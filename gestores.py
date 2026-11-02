"""Módulo de gestores CRUD, persistencia CSV atómica y procesamiento por lotes para Rutas del Bajío.

Implementa GestorClientes, GestorRutas y GestorPedidos con integridad referencial estricta,
respaldo automático de filas descartadas, control de los 7 estados operativos oficiales y
depuración exhaustiva de lotes mediante las reglas RL-01 a RL-05.

Criterios de limpieza vs. rechazo en gestores y carga por lote:
- Se LIMPIA:
  1. Espacios extremos (`strip()`) en todos los campos leídos de CSV.
  2. Código de lote (`codigo_lote`) y estado de certificado (`certificado_calidad`) normalizados
     a mayúsculas (`upper()`).
  3. Ciudad `"Leon"` normalizada a `"León"`.
  4. Campo `estado` vacío (`""`) en archivo de lote interpretado como estado inicial `"Registrado"`.
- Se RECHAZA:
  1. Nivel archivo (`ErrorArchivoLote`): archivo de lote inexistente, sin encabezados, con
     encabezados en mayúsculas o sin las columnas obligatorias (`id_pedido`, `id_cliente`, `cantidad`),
     o archivos CSV de entidades cuyos encabezados no coincidan exactamente con `CAMPOS_CSV`.
  2. Nivel fila (`FilaLoteInvalidaError`): incumplimiento de cualquiera de las reglas `RL-01` a `RL-05`,
     identificador vacío (`RL-ID`), campos obligatorios vacíos (`RL-CAMPO`), estado inicial distinto
     de `"Registrado"` (`RL-EST`), ID duplicado (`RL-DUP`), llave foránea inexistente (`RL-FK`) o
     inconsistencia entre origen/destino del pedido y su ruta asignada.
"""

import csv
import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from errores import (
    SUBESTADO_CUARENTENA,
    SUBESTADO_DATOS_INVALIDOS,
    SUBESTADO_DESCARTE,
    SUBESTADO_ESTADO_INVALIDO,
    SUBESTADO_FORMATO_INVALIDO,
    SUBESTADO_PESAJE,
    SUBESTADO_RED_FRIO,
    ErrorArchivoLote,
    ErrorIntegridadReferencial,
    ErrorTransicionEstado,
    FilaLoteInvalidaError,
)
from modelos import Cliente, Pedido, Ruta, normalizar_ciudad


REGEX_CODIGO_LOTE = re.compile(r"^LT-[0-9]{5}-[A-Z]{2}$")
COLUMNAS_OBLIGATORIAS_LOTE: Tuple[str, ...] = ("id_pedido", "id_cliente", "cantidad")
CAMPOS_OBLIGATORIOS_FILA_PEDIDO: Tuple[str, ...] = (
    "id_cliente",
    "producto",
    "cantidad",
    "origen",
    "destino",
    "fecha_pedido",
)


def _guardar_csv_atomico(
    ruta_destino: str,
    encabezados: Sequence[str],
    filas: Sequence[Dict[str, Any]],
) -> None:
    """Escribe un archivo CSV de forma atómica usando un archivo temporal y os.replace."""
    directorio = os.path.dirname(os.path.abspath(ruta_destino)) or "."
    os.makedirs(directorio, exist_ok=True)
    fd, ruta_tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".csv", dir=directorio, text=True)
    try:
        with os.fdopen(fd, mode="w", encoding="utf-8", newline="") as f_tmp:
            escritor = csv.DictWriter(f_tmp, fieldnames=list(encabezados))
            escritor.writeheader()
            for fila in filas:
                escritor.writerow(fila)
        os.replace(ruta_tmp, ruta_destino)
    except Exception:
        if os.path.exists(ruta_tmp):
            os.remove(ruta_tmp)
        raise


@dataclass
class RegistroDescarte:
    """Representa una fila descartada durante GestorPedidos.cargar() con su motivo auditable."""

    linea: int
    id_pedido: str
    motivo: str
    datos_fila: Dict[str, Any] = field(default_factory=dict)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            return self.id_pedido == other
        if isinstance(other, RegistroDescarte):
            return (
                self.linea == other.linea
                and self.id_pedido == other.id_pedido
                and self.motivo == other.motivo
            )
        return NotImplemented


@dataclass
class RegistroRechazo:
    """Representa una fila descartada durante la carga por lote con todas las reglas violadas."""

    linea: int
    identificador: str
    regla: str
    motivo: str
    subestado_rechazo: str = SUBESTADO_DESCARTE
    reglas: str = ""

    def __post_init__(self) -> None:
        if not self.reglas:
            self.reglas = self.regla


@dataclass
class ReporteLote:
    """Resumen auditable de resultados tras procesar un archivo CSV de lote."""

    leidas: int = 0
    aceptadas: int = 0
    rechazadas: List[RegistroRechazo] = field(default_factory=list)
    por_subestado: Dict[str, int] = field(default_factory=dict)


def validar_insumo_lote(
    fila: Dict[str, Any],
    fecha_actual: Optional[str] = None,
) -> Dict[str, Any]:
    """Evalúa TODAS las reglas RL-01 a RL-05 en estricto orden numérico sobre una fila de lote.

    Orden numérico de evaluación:
    1. RL-01 (Caducidad): Rechaza si Fecha_Vencimiento <= Fecha_Actual -> "Rechazo: Cuarentena".
    2. RL-02 (Formato de Lote): Rechaza si codigo_lote no cumple ^LT-[0-9]{5}-[A-Z]{2}$ -> "Rechazo: Formato Inválido".
    3. RL-03 (Red de Frío): Rechaza si Temp < 2.0 °C o Temp > 8.0 °C -> "Rechazo: Red de Frío".
    4. RL-04 (Tolerancia de Peso): Rechaza si |Peso_Real - Peso_Teorico| / Peso_Teorico > 3% -> "Rechazo: Pesaje".
    5. RL-05 (Certificado de Calidad): Rechaza si certificado_calidad está ausente, vacío, PENDIENTE o AUSENTE -> "Rechazo: Cuarentena".

    Si se violan múltiples reglas, registra todas en orden numérico (`reglas`), asignando a
    `regla` y `subestado_rechazo` la primera regla violada en dicho orden.
    """
    fecha_ref = (fecha_actual or date.today().isoformat()).strip()
    dt_actual = datetime.strptime(fecha_ref, "%Y-%m-%d")

    codigo_raw = fila.get("codigo_lote")
    codigo_lote = str(codigo_raw).strip().upper() if codigo_raw is not None else ""

    fecha_venc_raw = fila.get("fecha_vencimiento")
    fecha_vencimiento = str(fecha_venc_raw).strip() if fecha_venc_raw is not None else ""

    temperatura = fila.get("temperatura_c")
    peso_real = fila.get("peso_real")
    peso_teorico = fila.get("peso_teorico")

    cert_raw = fila.get("certificado_calidad")
    certificado = str(cert_raw).strip().upper() if cert_raw is not None else ""
    if not certificado:
        certificado = "AUSENTE"

    violaciones: List[Tuple[str, str, str]] = []

    # 1. RL-01: Caducidad Vencida (Fecha_Vencimiento <= Fecha_Actual)
    if fecha_vencimiento != "" and fecha_vencimiento is not None:
        try:
            dt_venc = datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
            if dt_venc <= dt_actual:
                violaciones.append(
                    (
                        "RL-01",
                        f"Lote caducado ({fecha_vencimiento} <= {fecha_ref})",
                        SUBESTADO_CUARENTENA,
                    )
                )
        except ValueError:
            violaciones.append(
                (
                    "RL-01",
                    f"Fecha de vencimiento con formato inválido: {fecha_vencimiento}",
                    SUBESTADO_CUARENTENA,
                )
            )

    # 2. RL-02: Formato de Lote Inválido (^LT-[0-9]{5}-[A-Z]{2}$)
    if codigo_lote and not REGEX_CODIGO_LOTE.match(codigo_lote):
        violaciones.append(
            (
                "RL-02",
                f"Formato de código de lote inválido: {codigo_lote}",
                SUBESTADO_FORMATO_INVALIDO,
            )
        )

    # 3. RL-03: Temperatura de Red de Frío (Temp < 2.0 °C o Temp > 8.0 °C)
    if temperatura is not None and str(temperatura).strip() != "":
        try:
            temp_val = float(temperatura)
            if temp_val < 2.0 or temp_val > 8.0:
                violaciones.append(
                    (
                        "RL-03",
                        f"Ruptura de cadena de frío: {temp_val} °C fuera del umbral [2.0 °C, 8.0 °C]",
                        SUBESTADO_RED_FRIO,
                    )
                )
        except ValueError:
            violaciones.append(
                (
                    "RL-03",
                    f"Temperatura no numérica: {temperatura}",
                    SUBESTADO_RED_FRIO,
                )
            )

    # 4. RL-04: Inconsistencia de Peso (|Peso_Real - Peso_Teorico| / Peso_Teorico > 3%)
    if (
        peso_real is not None
        and peso_teorico is not None
        and str(peso_real).strip() != ""
        and str(peso_teorico).strip() != ""
    ):
        try:
            p_real = float(peso_real)
            p_teo = float(peso_teorico)
            if p_teo <= 0:
                violaciones.append(
                    (
                        "RL-04",
                        "El peso teórico debe ser mayor que cero.",
                        SUBESTADO_PESAJE,
                    )
                )
            else:
                diferencia_relativa = round(abs(p_real - p_teo) / p_teo, 9)
                if diferencia_relativa > 0.03:
                    violaciones.append(
                        (
                            "RL-04",
                            f"Diferencia de pesaje superior al 3% (real={p_real}, teórico={p_teo})",
                            SUBESTADO_PESAJE,
                        )
                    )
        except ValueError:
            violaciones.append(
                (
                    "RL-04",
                    "Valores de peso no numéricos.",
                    SUBESTADO_PESAJE,
                )
            )

    # 5. RL-05: Certificado de Calidad Faltante (ausente, vacío, PENDIENTE o AUSENTE)
    if certificado == "PENDIENTE" or certificado == "AUSENTE":
        violaciones.append(
            (
                "RL-05",
                f"Certificado de calidad en estado {certificado}",
                SUBESTADO_CUARENTENA,
            )
        )

    if violaciones:
        regla_primaria, _, subestado_primario = violaciones[0]
        todas_reglas = [v[0] for v in violaciones]
        motivo_unido = "; ".join(v[1] for v in violaciones)
        raise FilaLoteInvalidaError(
            regla=regla_primaria,
            motivo=motivo_unido,
            subestado_rechazo=subestado_primario,
            reglas=todas_reglas,
        )

    fila_limpia = dict(fila)
    if codigo_lote:
        fila_limpia["codigo_lote"] = codigo_lote
    fila_limpia["certificado_calidad"] = certificado
    return fila_limpia


class GestorClientes:
    """Gestiona las operaciones CRUD y persistencia CSV atómica para la entidad Cliente."""

    CAMPOS_CSV: List[str] = ["id_cliente", "nombre", "ciudad", "telefono"]

    def __init__(self, archivo_csv: str = "clientes.csv") -> None:
        self.archivo_csv: str = archivo_csv
        self.clientes: List[Cliente] = []
        self._gestores_pedidos: List["GestorPedidos"] = []
        self.cargar()

    def registrar_gestor_pedidos(self, gestor_pedidos: "GestorPedidos") -> None:
        """Registra un GestorPedidos dependiente para proteger la integridad referencial."""
        if gestor_pedidos not in self._gestores_pedidos:
            self._gestores_pedidos.append(gestor_pedidos)

    def cargar(self) -> None:
        """Carga las instancias de Cliente desde el archivo CSV validando encabezados exactos."""
        self.clientes = []
        if not os.path.exists(self.archivo_csv):
            return
        with open(self.archivo_csv, mode="r", encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            if not lector.fieldnames:
                return
            if list(lector.fieldnames) != self.CAMPOS_CSV:
                raise ErrorArchivoLote(
                    f"Encabezados inválidos en '{self.archivo_csv}': "
                    f"se esperaba {self.CAMPOS_CSV}, se recibió {list(lector.fieldnames)}."
                )
            for fila in lector:
                if not any(fila.values()):
                    continue
                self.clientes.append(Cliente.from_dict(fila))

    def guardar(self) -> None:
        """Escribe de manera atómica el estado actual de la lista de clientes en el archivo CSV."""
        filas = [cliente.to_dict() for cliente in self.clientes]
        _guardar_csv_atomico(self.archivo_csv, self.CAMPOS_CSV, filas)

    def buscar_cliente(self, id_cliente: str) -> Optional[Cliente]:
        """Busca un cliente por su identificador único."""
        for cliente in self.clientes:
            if cliente.id_cliente == id_cliente:
                return cliente
        return None

    def crear_cliente(self, cliente: Cliente) -> None:
        """Registra un nuevo cliente verificando tipo e inexistencia de ID duplicado."""
        if not isinstance(cliente, Cliente):
            raise TypeError("Se esperaba una instancia de Cliente.")
        if self.buscar_cliente(cliente.id_cliente) is not None:
            raise ValueError(f"Ya existe un cliente con el ID '{cliente.id_cliente}'.")
        self.clientes.append(cliente)
        self.guardar()

    def listar_clientes(self) -> List[Cliente]:
        """Devuelve la lista completa de clientes registrados."""
        return list(self.clientes)

    def listar_clientes_por_ciudad(self, ciudad: str) -> List[Cliente]:
        """Filtra y devuelve los clientes pertenecientes a una ciudad específica."""
        ciudad_norm = normalizar_ciudad(ciudad).lower()
        return [c for c in self.clientes if c.ciudad.lower() == ciudad_norm]

    def actualizar_cliente(self, id_cliente: str, **cambios: Any) -> bool:
        """Actualiza los atributos de un cliente de forma atómica y rechaza claves desconocidas."""
        campos_permitidos = set(self.CAMPOS_CSV) - {"id_cliente"}
        claves_invalidas = set(cambios.keys()) - campos_permitidos
        if claves_invalidas:
            raise ValueError(
                f"Claves desconocidas o no modificables en actualizar_cliente: {sorted(claves_invalidas)}"
            )
        cliente = self.buscar_cliente(id_cliente)
        if cliente is None:
            return False
        datos = cliente.to_dict()
        datos.update(cambios)
        datos["id_cliente"] = id_cliente
        actualizado = Cliente.from_dict(datos)
        idx = self.clientes.index(cliente)
        self.clientes[idx] = actualizado
        self.guardar()
        return True

    def eliminar_cliente(self, id_cliente: str) -> bool:
        """Elimina un cliente por su ID si no tiene pedidos asociados en ningún GestorPedidos."""
        cliente = self.buscar_cliente(id_cliente)
        if cliente is None:
            return False
        for gestor_ped in self._gestores_pedidos:
            if gestor_ped.listar_pedidos_por_cliente(id_cliente):
                raise ErrorIntegridadReferencial(
                    f"No se puede eliminar el cliente '{id_cliente}' porque tiene pedidos asociados."
                )
        self.clientes.remove(cliente)
        self.guardar()
        return True


class GestorRutas:
    """Gestiona las operaciones CRUD y persistencia CSV atómica para la entidad Ruta."""

    CAMPOS_CSV: List[str] = [
        "id_ruta",
        "origen",
        "destino",
        "distancia_km",
        "tiempo_estimado",
        "transportista",
    ]

    def __init__(self, archivo_csv: str = "rutas.csv") -> None:
        self.archivo_csv: str = archivo_csv
        self.rutas: List[Ruta] = []
        self._gestores_pedidos: List["GestorPedidos"] = []
        self.cargar()

    def registrar_gestor_pedidos(self, gestor_pedidos: "GestorPedidos") -> None:
        """Registra un GestorPedidos dependiente para proteger la integridad referencial."""
        if gestor_pedidos not in self._gestores_pedidos:
            self._gestores_pedidos.append(gestor_pedidos)

    def cargar(self) -> None:
        """Carga las instancias de Ruta desde el archivo CSV validando encabezados exactos."""
        self.rutas = []
        if not os.path.exists(self.archivo_csv):
            return
        with open(self.archivo_csv, mode="r", encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            if not lector.fieldnames:
                return
            if list(lector.fieldnames) != self.CAMPOS_CSV:
                raise ErrorArchivoLote(
                    f"Encabezados inválidos en '{self.archivo_csv}': "
                    f"se esperaba {self.CAMPOS_CSV}, se recibió {list(lector.fieldnames)}."
                )
            for fila in lector:
                if not any(fila.values()):
                    continue
                self.rutas.append(Ruta.from_dict(fila))

    def guardar(self) -> None:
        """Escribe de manera atómica el estado actual de la lista de rutas en el archivo CSV."""
        filas = [ruta.to_dict() for ruta in self.rutas]
        _guardar_csv_atomico(self.archivo_csv, self.CAMPOS_CSV, filas)

    def buscar_ruta(self, id_ruta: str) -> Optional[Ruta]:
        """Busca una ruta por su identificador único."""
        for ruta in self.rutas:
            if ruta.id_ruta == id_ruta:
                return ruta
        return None

    def crear_ruta(self, ruta: Ruta) -> None:
        """Registra una nueva ruta verificando tipo e inexistencia de ID duplicado."""
        if not isinstance(ruta, Ruta):
            raise TypeError("Se esperaba una instancia de Ruta.")
        if self.buscar_ruta(ruta.id_ruta) is not None:
            raise ValueError(f"Ya existe una ruta con el ID '{ruta.id_ruta}'.")
        self.rutas.append(ruta)
        self.guardar()

    def listar_rutas(self) -> List[Ruta]:
        """Devuelve la lista completa de rutas registradas."""
        return list(self.rutas)

    def listar_rutas_por_destino(self, destino: str) -> List[Ruta]:
        """Filtra y devuelve las rutas que llegan a un destino específico."""
        destino_norm = normalizar_ciudad(destino).lower()
        return [r for r in self.rutas if r.destino.lower() == destino_norm]

    def actualizar_ruta(self, id_ruta: str, **cambios: Any) -> bool:
        """Actualiza los atributos de una ruta de forma atómica y rechaza claves desconocidas."""
        campos_permitidos = set(self.CAMPOS_CSV) - {"id_ruta"}
        claves_invalidas = set(cambios.keys()) - campos_permitidos
        if claves_invalidas:
            raise ValueError(
                f"Claves desconocidas o no modificables en actualizar_ruta: {sorted(claves_invalidas)}"
            )
        ruta = self.buscar_ruta(id_ruta)
        if ruta is None:
            return False
        datos = ruta.to_dict()
        datos.update(cambios)
        datos["id_ruta"] = id_ruta
        actualizada = Ruta.from_dict(datos)
        idx = self.rutas.index(ruta)
        self.rutas[idx] = actualizada
        self.guardar()
        return True

    def eliminar_ruta(self, id_ruta: str) -> bool:
        """Elimina una ruta por su ID si no tiene pedidos asociados en ningún GestorPedidos."""
        ruta = self.buscar_ruta(id_ruta)
        if ruta is None:
            return False
        for gestor_ped in self._gestores_pedidos:
            if any(p.id_ruta == id_ruta for p in gestor_ped.pedidos):
                raise ErrorIntegridadReferencial(
                    f"No se puede eliminar la ruta '{id_ruta}' porque tiene pedidos asociados."
                )
        self.rutas.remove(ruta)
        self.guardar()
        return True


class GestorPedidos:
    """Gestiona las operaciones CRUD, máquina de estados oficial y carga por lote de Pedidos."""

    CAMPOS_CSV: List[str] = [
        "id_pedido",
        "id_cliente",
        "producto",
        "cantidad",
        "origen",
        "destino",
        "fecha_pedido",
        "estado",
        "id_ruta",
    ]
    CAMPOS_DESCARTADOS_CSV: List[str] = [
        "linea",
        "id_pedido",
        "motivo",
        *CAMPOS_CSV,
    ]

    def __init__(
        self,
        archivo_csv: str = "pedidos.csv",
        gestor_clientes: Optional[GestorClientes] = None,
        gestor_rutas: Optional[GestorRutas] = None,
    ) -> None:
        self.archivo_csv: str = archivo_csv
        self.archivo_descartados_csv: str = f"{archivo_csv}.descartados.csv"
        self.gestor_clientes: Optional[GestorClientes] = gestor_clientes
        self.gestor_rutas: Optional[GestorRutas] = gestor_rutas
        if self.gestor_clientes is not None:
            self.gestor_clientes.registrar_gestor_pedidos(self)
        if self.gestor_rutas is not None:
            self.gestor_rutas.registrar_gestor_pedidos(self)

        self.pedidos: List[Pedido] = []
        self.descartados: List[RegistroDescarte] = []
        self.cargar()

    def _respaldar_descartados(self) -> None:
        """Escribe en <archivo>.descartados.csv todas las filas descartadas durante cargar()."""
        if not self.descartados:
            return
        filas_respaldo: List[Dict[str, Any]] = []
        for desc in self.descartados:
            fila_out = {campo: desc.datos_fila.get(campo, "") for campo in self.CAMPOS_CSV}
            fila_out["linea"] = desc.linea
            fila_out["id_pedido"] = desc.id_pedido
            fila_out["motivo"] = desc.motivo
            filas_respaldo.append(fila_out)
        _guardar_csv_atomico(
            self.archivo_descartados_csv,
            self.CAMPOS_DESCARTADOS_CSV,
            filas_respaldo,
        )

    def _validar_referencias_y_ruta(
        self,
        id_cliente: str,
        id_ruta: str,
        origen: str,
        destino: str,
    ) -> None:
        """Verifica existencia de id_cliente, id_ruta y coincidencia de origen/destino con la ruta."""
        if self.gestor_clientes is not None and self.gestor_clientes.buscar_cliente(id_cliente) is None:
            raise ValueError(f"El cliente '{id_cliente}' no está registrado.")
        if id_ruta:
            if self.gestor_rutas is not None:
                ruta_obj = self.gestor_rutas.buscar_ruta(id_ruta)
                if ruta_obj is None:
                    raise ValueError(f"La ruta '{id_ruta}' no está registrada.")
                if origen != ruta_obj.origen or destino != ruta_obj.destino:
                    raise ValueError(
                        f"El trayecto del pedido ({origen} -> {destino}) no coincide con "
                        f"la ruta '{id_ruta}' ({ruta_obj.origen} -> {ruta_obj.destino})."
                    )

    def cargar(self) -> None:
        """Carga los pedidos desde el CSV validando encabezados, llaves foráneas y respaldando descartes."""
        self.pedidos = []
        self.descartados = []
        if not os.path.exists(self.archivo_csv):
            return
        with open(self.archivo_csv, mode="r", encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            if not lector.fieldnames:
                return
            if list(lector.fieldnames) != self.CAMPOS_CSV:
                raise ErrorArchivoLote(
                    f"Encabezados inválidos en '{self.archivo_csv}': "
                    f"se esperaba {self.CAMPOS_CSV}, se recibió {list(lector.fieldnames)}."
                )
            for fila in lector:
                if not any(fila.values()):
                    continue
                id_ped = (fila.get("id_pedido") or "").strip()
                try:
                    pedido = Pedido.from_dict(fila, restaurar_estado=True)
                    self._validar_referencias_y_ruta(
                        pedido.id_cliente,
                        pedido.id_ruta,
                        pedido.origen,
                        pedido.destino,
                    )
                    self.pedidos.append(pedido)
                except (ValueError, KeyError) as err:
                    self.descartados.append(
                        RegistroDescarte(
                            linea=lector.line_num,
                            id_pedido=id_ped,
                            motivo=str(err),
                            datos_fila=dict(fila),
                        )
                    )

        if self.descartados:
            self._respaldar_descartados()

    def guardar(self) -> None:
        """Escribe de forma atómica los pedidos en el CSV asegurando el respaldo previo de descartados."""
        if self.descartados and not os.path.exists(self.archivo_descartados_csv):
            self._respaldar_descartados()
        filas = [pedido.to_dict() for pedido in self.pedidos]
        _guardar_csv_atomico(self.archivo_csv, self.CAMPOS_CSV, filas)

    def buscar_pedido(self, id_pedido: str) -> Optional[Pedido]:
        """Busca un pedido por su identificador único."""
        for pedido in self.pedidos:
            if pedido.id_pedido == id_pedido:
                return pedido
        return None

    def crear_pedido(self, pedido: Pedido) -> None:
        """Registra un nuevo pedido verificando estado inicial 'Registrado', unicidad y llaves foráneas."""
        if not isinstance(pedido, Pedido):
            raise TypeError("Se esperaba una instancia de Pedido.")
        if pedido.estado != "Registrado":
            raise ErrorTransicionEstado(
                f"Solo se pueden crear pedidos en estado inicial 'Registrado' (recibido: '{pedido.estado}')."
            )
        if self.buscar_pedido(pedido.id_pedido) is not None:
            raise ValueError(f"Ya existe un pedido con el ID '{pedido.id_pedido}'.")

        self._validar_referencias_y_ruta(
            pedido.id_cliente,
            pedido.id_ruta,
            pedido.origen,
            pedido.destino,
        )
        self.pedidos.append(pedido)
        self.guardar()

    def listar_pedidos(self) -> List[Pedido]:
        """Devuelve todos los pedidos cargados."""
        return list(self.pedidos)

    def listar_pedidos_por_estado(self, estado: str) -> List[Pedido]:
        """Filtra y devuelve los pedidos que se encuentran en un estado determinado."""
        return [p for p in self.pedidos if p.estado == estado]

    def listar_pedidos_por_cliente(self, id_cliente: str) -> List[Pedido]:
        """Devuelve todos los pedidos asociados a un id_cliente específico."""
        return [p for p in self.pedidos if p.id_cliente == id_cliente]

    def cambiar_estado_pedido(self, id_pedido: str, nuevo_estado: str) -> Pedido:
        """Aplica una transición de estado válida sobre un pedido y persiste el cambio."""
        pedido = self.buscar_pedido(id_pedido)
        if pedido is None:
            raise ValueError(f"No existe el pedido con ID '{id_pedido}'.")
        pedido.transicionar_estado(nuevo_estado)
        self.guardar()
        return pedido

    def actualizar_pedido(self, id_pedido: str, **cambios: Any) -> bool:
        """Actualiza campos permitidos de un pedido de forma atómica revalidando FKs y transiciones."""
        campos_permitidos = set(self.CAMPOS_CSV) - {"id_pedido"}
        claves_invalidas = set(cambios.keys()) - campos_permitidos
        if claves_invalidas:
            raise ValueError(
                f"Claves desconocidas o no modificables en actualizar_pedido: {sorted(claves_invalidas)}"
            )

        pedido = self.buscar_pedido(id_pedido)
        if pedido is None:
            return False

        # Construcción y validación en objeto candidato ANTES de mutar memoria o disco
        datos_candidato = pedido.to_dict()
        for clave, valor in cambios.items():
            if clave != "estado":
                datos_candidato[clave] = valor

        candidato = Pedido.from_dict(datos_candidato, restaurar_estado=True)

        if "estado" in cambios and cambios["estado"] != pedido.estado:
            candidato.transicionar_estado(cambios["estado"])

        self._validar_referencias_y_ruta(
            candidato.id_cliente,
            candidato.id_ruta,
            candidato.origen,
            candidato.destino,
        )

        idx = self.pedidos.index(pedido)
        self.pedidos[idx] = candidato
        self.guardar()
        return True

    def eliminar_pedido(self, id_pedido: str) -> bool:
        """Elimina un pedido existente y persiste los cambios en el archivo CSV."""
        pedido = self.buscar_pedido(id_pedido)
        if pedido is None:
            return False
        self.pedidos.remove(pedido)
        self.guardar()
        return True

    def cargar_lote(
        self,
        ruta_lote: str,
        ruta_rechazos: Optional[str] = None,
        fecha_actual: Optional[str] = None,
    ) -> ReporteLote:
        """Procesa un archivo CSV de lotes/pedidos aplicando RL-01..RL-05 y validaciones de fila."""
        if not os.path.exists(ruta_lote):
            raise ErrorArchivoLote(f"El archivo de lote no existe: '{ruta_lote}'.")

        fecha_ref = (fecha_actual or date.today().isoformat()).strip()
        reporte = ReporteLote()
        ids_vistos: set[str] = set()
        nuevos_pedidos: List[Pedido] = []

        with open(ruta_lote, mode="r", encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            if not lector.fieldnames:
                raise ErrorArchivoLote(f"El archivo de lote '{ruta_lote}' no contiene encabezados.")

            encabezados = list(lector.fieldnames)
            if any(h != h.strip().lower() for h in encabezados if h is not None):
                raise ErrorArchivoLote(
                    f"Los encabezados del lote deben estar en minúsculas exactas: {encabezados}"
                )

            faltantes = [c for c in COLUMNAS_OBLIGATORIAS_LOTE if c not in encabezados]
            if faltantes:
                raise ErrorArchivoLote(
                    f"Columnas obligatorias faltantes en el archivo de lote: {faltantes}"
                )

            for fila in lector:
                reporte.leidas += 1
                id_fila = (fila.get("id_pedido") or fila.get("codigo_lote") or "").strip()
                try:
                    # 1. Evaluación completa en orden numérico de RL-01 a RL-05
                    validar_insumo_lote(fila, fecha_actual=fecha_ref)

                    # 2. Validación de ID de pedido obligatorio
                    id_ped = (fila.get("id_pedido") or "").strip()
                    if not id_ped:
                        raise FilaLoteInvalidaError(
                            "RL-ID",
                            "Identificador id_pedido vacío.",
                            subestado_rechazo=SUBESTADO_DATOS_INVALIDOS,
                        )

                    # 3. Validación de campos obligatorios del pedido (sin defaults silenciosos)
                    campos_vacios = [
                        campo
                        for campo in CAMPOS_OBLIGATORIOS_FILA_PEDIDO
                        if not str(fila.get(campo) or "").strip()
                    ]
                    if campos_vacios:
                        raise FilaLoteInvalidaError(
                            "RL-CAMPO",
                            f"Campos obligatorios vacíos o ausentes: {campos_vacios}",
                            subestado_rechazo=SUBESTADO_DATOS_INVALIDOS,
                        )

                    # 4. Validación de estado inicial estricto ("Registrado" o vacío)
                    estado_raw = str(fila.get("estado") or "").strip()
                    estado_limpio = estado_raw if estado_raw else "Registrado"
                    if estado_limpio != "Registrado":
                        raise FilaLoteInvalidaError(
                            "RL-EST",
                            f"El estado inicial en lote debe ser 'Registrado', se recibió '{estado_limpio}'.",
                            subestado_rechazo=SUBESTADO_ESTADO_INVALIDO,
                        )

                    # 5. Validación de duplicados en lote o en gestor
                    if id_ped in ids_vistos or self.buscar_pedido(id_ped) is not None:
                        raise FilaLoteInvalidaError(
                            "RL-DUP",
                            f"ID de pedido duplicado: {id_ped}",
                            subestado_rechazo=SUBESTADO_DESCARTE,
                        )

                    # 6. Validación de llaves foráneas y ruta
                    id_cli = str(fila["id_cliente"]).strip()
                    id_rut = str(fila.get("id_ruta") or "").strip()
                    if self.gestor_clientes is not None and self.gestor_clientes.buscar_cliente(id_cli) is None:
                        raise FilaLoteInvalidaError(
                            "RL-FK",
                            f"Cliente inexistente: {id_cli}",
                            subestado_rechazo=SUBESTADO_DATOS_INVALIDOS,
                        )
                    if id_rut and self.gestor_rutas is not None and self.gestor_rutas.buscar_ruta(id_rut) is None:
                        raise FilaLoteInvalidaError(
                            "RL-FK",
                            f"Ruta inexistente: {id_rut}",
                            subestado_rechazo=SUBESTADO_DATOS_INVALIDOS,
                        )

                    pedido = Pedido(
                        id_pedido=id_ped,
                        id_cliente=id_cli,
                        producto=str(fila["producto"]).strip(),
                        cantidad=fila["cantidad"],
                        origen=str(fila["origen"]).strip(),
                        destino=str(fila["destino"]).strip(),
                        fecha_pedido=str(fila["fecha_pedido"]).strip(),
                        estado="Registrado",
                        id_ruta=id_rut,
                    )
                    self._validar_referencias_y_ruta(
                        pedido.id_cliente,
                        pedido.id_ruta,
                        pedido.origen,
                        pedido.destino,
                    )
                except FilaLoteInvalidaError as err:
                    reglas_str = ";".join(err.reglas)
                    reporte.rechazadas.append(
                        RegistroRechazo(
                            linea=lector.line_num,
                            identificador=id_fila,
                            regla=err.regla,
                            motivo=err.motivo,
                            subestado_rechazo=err.subestado_rechazo,
                            reglas=reglas_str,
                        )
                    )
                    reporte.por_subestado[err.subestado_rechazo] = (
                        reporte.por_subestado.get(err.subestado_rechazo, 0) + 1
                    )
                    continue
                except ValueError as err:
                    reporte.rechazadas.append(
                        RegistroRechazo(
                            linea=lector.line_num,
                            identificador=id_fila,
                            regla="RL-CAMPO",
                            motivo=str(err),
                            subestado_rechazo=SUBESTADO_DATOS_INVALIDOS,
                            reglas="RL-CAMPO",
                        )
                    )
                    reporte.por_subestado[SUBESTADO_DATOS_INVALIDOS] = (
                        reporte.por_subestado.get(SUBESTADO_DATOS_INVALIDOS, 0) + 1
                    )
                    continue

                ids_vistos.add(pedido.id_pedido)
                nuevos_pedidos.append(pedido)

        self.pedidos.extend(nuevos_pedidos)
        reporte.aceptadas = len(nuevos_pedidos)
        self.guardar()

        if ruta_rechazos is not None:
            filas_rechazo = [
                {
                    "linea": r.linea,
                    "identificador": r.identificador,
                    "regla": r.regla,
                    "reglas": r.reglas,
                    "motivo": r.motivo,
                    "subestado_rechazo": r.subestado_rechazo,
                }
                for r in reporte.rechazadas
            ]
            _guardar_csv_atomico(
                ruta_rechazos,
                ["linea", "identificador", "regla", "reglas", "motivo", "subestado_rechazo"],
                filas_rechazo,
            )

        return reporte
