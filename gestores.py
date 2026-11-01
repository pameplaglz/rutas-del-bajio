"""Módulo de gestores CRUD, persistencia CSV y procesamiento por lotes para Rutas del Bajío.

Implementa GestorClientes, GestorRutas y GestorPedidos con validación estricta de tipos,
integridad de llaves foráneas, control de los 7 estados operativos oficiales y depuración
de lotes mediante las reglas RL-01 a RL-05.
"""

import csv
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from modelos import Cliente, ErrorTransicionEstado, Pedido, Ruta


REGEX_CODIGO_LOTE = re.compile(r"^LT-[0-9]{5}-[A-Z]{2}$")


class FilaLoteInvalidaError(ValueError):
    """Excepción para rechazar una fila individual durante la carga por lote."""

    def __init__(self, regla: str, motivo: str, subestado_rechazo: str = "Rechazo: Descarte") -> None:
        super().__init__(f"[{regla}] {motivo}")
        self.regla: str = regla
        self.motivo: str = motivo
        self.subestado_rechazo: str = subestado_rechazo


@dataclass
class RegistroRechazo:
    """Representa una fila descartada durante la carga por lote con su subestado de rechazo."""

    linea: int
    identificador: str
    regla: str
    motivo: str
    subestado_rechazo: str = "Rechazo: Descarte"


@dataclass
class ReporteLote:
    """Resumen auditable de resultados tras procesar un archivo CSV de lote."""

    leidas: int = 0
    aceptadas: int = 0
    rechazadas: List[RegistroRechazo] = field(default_factory=list)


def validar_insumo_lote(fila: Dict[str, Any], fecha_actual: str = "2026-10-18") -> Dict[str, Any]:
    """Evalúa las reglas de limpieza y depuración RL-01 a RL-05 sobre una fila de lote.

    Reglas aplicadas:
    - RL-01 (Caducidad): Rechaza si Fecha_Vencimiento <= Fecha_Actual.
    - RL-02 (Formato de Lote): Rechaza si no cumple regex ^LT-[0-9]{5}-[A-Z]{2}$.
    - RL-03 (Red de Frío): Rechaza si Temp < 2.0 °C o Temp > 8.0 °C (2.0 y 8.0 son válidos).
    - RL-04 (Tolerancia de Peso): Rechaza si |Peso_Real - Peso_Teorico| / Peso_Teorico > 3% (0.03 exacto es válido).
    - RL-05 (Certificado de Calidad): Rechaza si el certificado está PENDIENTE o AUSENTE.
    """
    codigo_lote = str(fila.get("codigo_lote", "")).strip()
    fecha_vencimiento = str(fila.get("fecha_vencimiento", "")).strip()
    temperatura = fila.get("temperatura_c")
    peso_real = fila.get("peso_real")
    peso_teorico = fila.get("peso_teorico")
    certificado = str(fila.get("certificado_calidad", "OK")).strip().upper()

    # RL-02: Formato de Lote Inválido (^LT-[0-9]{5}-[A-Z]{2}$)
    if codigo_lote and not REGEX_CODIGO_LOTE.match(codigo_lote):
        raise FilaLoteInvalidaError(
            "RL-02",
            f"Formato de código de lote inválido: {codigo_lote}",
            subestado_rechazo="Rechazo: Formato Inválido",
        )

    # RL-01: Caducidad Vencida (Fecha_Vencimiento <= Fecha_Actual)
    if fecha_vencimiento:
        dt_venc = datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
        dt_actual = datetime.strptime(fecha_actual, "%Y-%m-%d")
        if dt_venc <= dt_actual:
            raise FilaLoteInvalidaError(
                "RL-01",
                f"Lote caducado ({fecha_vencimiento} <= {fecha_actual})",
                subestado_rechazo="Rechazo: Cuarentena",
            )

    # RL-03: Temperatura de Red de Frío (Temp < 2°C o Temp > 8°C)
    if temperatura is not None and str(temperatura).strip() != "":
        temp_val = float(temperatura)
        if temp_val < 2.0 or temp_val > 8.0:
            raise FilaLoteInvalidaError(
                "RL-03",
                f"Ruptura de cadena de frío: {temp_val} °C fuera del umbral [2.0 °C, 8.0 °C]",
                subestado_rechazo="Rechazo: Red de Frío",
            )

    # RL-04: Inconsistencia de Peso (|Peso_Real - Peso_Teorico| / Peso_Teorico > 3%)
    if (
        peso_real is not None
        and peso_teorico is not None
        and str(peso_real).strip() != ""
        and str(peso_teorico).strip() != ""
    ):
        p_real = float(peso_real)
        p_teo = float(peso_teorico)
        if p_teo <= 0:
            raise FilaLoteInvalidaError(
                "RL-04",
                "El peso teórico debe ser mayor que cero.",
                subestado_rechazo="Rechazo: Pesaje",
            )
        diferencia_relativa = round(abs(p_real - p_teo) / p_teo, 9)
        if diferencia_relativa > 0.03:
            raise FilaLoteInvalidaError(
                "RL-04",
                f"Diferencia de pesaje superior al 3% (real={p_real}, teórico={p_teo})",
                subestado_rechazo="Rechazo: Pesaje",
            )

    # RL-05: Certificado de Calidad Faltante (PENDIENTE o AUSENTE)
    if certificado in {"PENDIENTE", "AUSENTE", ""}:
        raise FilaLoteInvalidaError(
            "RL-05",
            f"Certificado de calidad en estado {certificado or 'AUSENTE'}",
            subestado_rechazo="Rechazo: Cuarentena",
        )

    return fila


class GestorClientes:
    """Gestiona las operaciones CRUD y persistencia CSV para la entidad Cliente."""

    CAMPOS_CSV: List[str] = ["id_cliente", "nombre", "ciudad", "telefono"]

    def __init__(self, archivo_csv: str = "clientes.csv") -> None:
        self.archivo_csv: str = archivo_csv
        self.clientes: List[Cliente] = []
        self.cargar()

    def cargar(self) -> None:
        """Carga las instancias de Cliente desde el archivo CSV hacia la memoria."""
        self.clientes = []
        if not os.path.exists(self.archivo_csv):
            return
        with open(self.archivo_csv, mode="r", encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            if not lector.fieldnames:
                return
            for fila in lector:
                if not any(fila.values()):
                    continue
                self.clientes.append(Cliente.from_dict(fila))

    def guardar(self) -> None:
        """Escribe el estado actual de la lista de clientes en el archivo CSV."""
        with open(self.archivo_csv, mode="w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=self.CAMPOS_CSV)
            escritor.writeheader()
            for cliente in self.clientes:
                escritor.writerow(cliente.to_dict())

    def buscar_cliente(self, id_cliente: str) -> Optional[Cliente]:
        """Busca un cliente por su identificador único."""
        for cliente in self.clientes:
            if cliente.id_cliente == id_cliente:
                return cliente
        return None

    def crear_cliente(self, cliente: Cliente) -> None:
        """Registra un nuevo cliente verificando que su ID no esté duplicado."""
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
        return [c for c in self.clientes if c.ciudad.lower() == ciudad.strip().lower()]

    def actualizar_cliente(self, id_cliente: str, **cambios: Any) -> bool:
        """Actualiza los atributos de un cliente existente y persiste en disco."""
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
        """Elimina un cliente por su ID y actualiza el archivo CSV."""
        cliente = self.buscar_cliente(id_cliente)
        if cliente is None:
            return False
        self.clientes.remove(cliente)
        self.guardar()
        return True


class GestorRutas:
    """Gestiona las operaciones CRUD y persistencia CSV para la entidad Ruta."""

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
        self.cargar()

    def cargar(self) -> None:
        """Carga las instancias de Ruta desde el archivo CSV hacia la memoria."""
        self.rutas = []
        if not os.path.exists(self.archivo_csv):
            return
        with open(self.archivo_csv, mode="r", encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            if not lector.fieldnames:
                return
            for fila in lector:
                if not any(fila.values()):
                    continue
                self.rutas.append(Ruta.from_dict(fila))

    def guardar(self) -> None:
        """Escribe el estado actual de la lista de rutas en el archivo CSV."""
        with open(self.archivo_csv, mode="w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=self.CAMPOS_CSV)
            escritor.writeheader()
            for ruta in self.rutas:
                escritor.writerow(ruta.to_dict())

    def buscar_ruta(self, id_ruta: str) -> Optional[Ruta]:
        """Busca una ruta por su identificador único."""
        for ruta in self.rutas:
            if ruta.id_ruta == id_ruta:
                return ruta
        return None

    def crear_ruta(self, ruta: Ruta) -> None:
        """Registra una nueva ruta verificando que su ID no esté duplicado."""
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
        return [r for r in self.rutas if r.destino.lower() == destino.strip().lower()]

    def actualizar_ruta(self, id_ruta: str, **cambios: Any) -> bool:
        """Actualiza los atributos de una ruta existente y persiste en disco."""
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
        """Elimina una ruta por su ID y actualiza el archivo CSV."""
        ruta = self.buscar_ruta(id_ruta)
        if ruta is None:
            return False
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

    def __init__(
        self,
        archivo_csv: str = "pedidos.csv",
        gestor_clientes: Optional[GestorClientes] = None,
        gestor_rutas: Optional[GestorRutas] = None,
    ) -> None:
        self.archivo_csv: str = archivo_csv
        self.gestor_clientes: Optional[GestorClientes] = gestor_clientes
        self.gestor_rutas: Optional[GestorRutas] = gestor_rutas
        self.pedidos: List[Pedido] = []
        self.descartados: List[str] = []
        self.cargar()

    def cargar(self) -> None:
        """Carga los pedidos desde el CSV validando llaves foráneas y registrando filas descartadas."""
        self.pedidos = []
        self.descartados = []
        if not os.path.exists(self.archivo_csv):
            return
        with open(self.archivo_csv, mode="r", encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            if not lector.fieldnames:
                return
            for fila in lector:
                if not any(fila.values()):
                    continue
                id_ped = (fila.get("id_pedido") or "").strip()
                id_cli = (fila.get("id_cliente") or "").strip()
                id_rut = (fila.get("id_ruta") or "").strip()

                if self.gestor_clientes is not None and self.gestor_clientes.buscar_cliente(id_cli) is None:
                    self.descartados.append(id_ped)
                    continue

                if id_rut and self.gestor_rutas is not None and self.gestor_rutas.buscar_ruta(id_rut) is None:
                    self.descartados.append(id_ped)
                    continue

                try:
                    self.pedidos.append(Pedido.from_dict(fila))
                except (ValueError, KeyError):
                    self.descartados.append(id_ped)

    def guardar(self) -> None:
        """Escribe el estado actual de los pedidos en el archivo CSV."""
        with open(self.archivo_csv, mode="w", encoding="utf-8", newline="") as f:
            escritor = csv.DictWriter(f, fieldnames=self.CAMPOS_CSV)
            escritor.writeheader()
            for pedido in self.pedidos:
                escritor.writerow(pedido.to_dict())

    def buscar_pedido(self, id_pedido: str) -> Optional[Pedido]:
        """Busca un pedido por su identificador único."""
        for pedido in self.pedidos:
            if pedido.id_pedido == id_pedido:
                return pedido
        return None

    def crear_pedido(self, pedido: Pedido) -> None:
        """Registra un nuevo pedido verificando unicidad de ID y existencia de llaves foráneas."""
        if not isinstance(pedido, Pedido):
            raise TypeError("Se esperaba una instancia de Pedido.")
        if self.buscar_pedido(pedido.id_pedido) is not None:
            raise ValueError(f"Ya existe un pedido con el ID '{pedido.id_pedido}'.")
        if self.gestor_clientes is not None and self.gestor_clientes.buscar_cliente(pedido.id_cliente) is None:
            raise ValueError(f"El cliente '{pedido.id_cliente}' no está registrado.")
        if (
            pedido.id_ruta
            and self.gestor_rutas is not None
            and self.gestor_rutas.buscar_ruta(pedido.id_ruta) is None
        ):
            raise ValueError(f"La ruta '{pedido.id_ruta}' no está registrada.")
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
        """Actualiza campos permitidos de un pedido respetando la máquina de estados."""
        pedido = self.buscar_pedido(id_pedido)
        if pedido is None:
            return False

        if "estado" in cambios and cambios["estado"] != pedido.estado:
            pedido.transicionar_estado(cambios["estado"])

        datos = pedido.to_dict()
        for clave, valor in cambios.items():
            if clave not in {"id_pedido", "estado"}:
                datos[clave] = valor
        datos["estado"] = pedido.estado

        actualizado = Pedido.from_dict(datos)
        idx = self.pedidos.index(pedido)
        self.pedidos[idx] = actualizado
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
        fecha_actual: str = "2026-10-18",
    ) -> ReporteLote:
        """Procesa un archivo CSV de lotes/pedidos aplicando las reglas RL-01 a RL-05."""
        reporte = ReporteLote()
        ids_vistos: set[str] = set()
        nuevos_pedidos: List[Pedido] = []

        with open(ruta_lote, mode="r", encoding="utf-8", newline="") as f:
            lector = csv.DictReader(f)
            if not lector.fieldnames:
                return reporte

            for fila in lector:
                reporte.leidas += 1
                id_fila = (fila.get("id_pedido") or fila.get("codigo_lote") or "").strip()
                try:
                    validar_insumo_lote(fila, fecha_actual=fecha_actual)

                    id_ped = (fila.get("id_pedido") or id_fila).strip()
                    if not id_ped:
                        raise FilaLoteInvalidaError("RL-ID", "Identificador de pedido vacío")
                    if id_ped in ids_vistos or self.buscar_pedido(id_ped) is not None:
                        raise FilaLoteInvalidaError("RL-DUP", f"ID duplicado en lote: {id_ped}")

                    id_cli = (fila.get("id_cliente") or "CLI-01").strip()
                    if self.gestor_clientes is not None and self.gestor_clientes.buscar_cliente(id_cli) is None:
                        raise FilaLoteInvalidaError("RL-FK", f"Cliente inexistente: {id_cli}")

                    pedido = Pedido(
                        id_pedido=id_ped,
                        id_cliente=id_cli,
                        producto=(fila.get("producto") or "Insumo Lote").strip(),
                        cantidad=int(fila.get("cantidad", 1)),
                        origen=(fila.get("origen") or "León").strip(),
                        destino=(fila.get("destino") or "Irapuato").strip(),
                        fecha_pedido=(fila.get("fecha_pedido") or fecha_actual).strip(),
                        estado=(fila.get("estado") or "Registrado").strip(),
                        id_ruta=(fila.get("id_ruta") or "").strip(),
                    )
                except FilaLoteInvalidaError as err:
                    reporte.rechazadas.append(
                        RegistroRechazo(
                            linea=lector.line_num,
                            identificador=id_fila,
                            regla=err.regla,
                            motivo=err.motivo,
                            subestado_rechazo=err.subestado_rechazo,
                        )
                    )
                    continue
                except ValueError as err:
                    reporte.rechazadas.append(
                        RegistroRechazo(
                            linea=lector.line_num,
                            identificador=id_fila,
                            regla="VALIDACION",
                            motivo=str(err),
                            subestado_rechazo="Rechazo: Datos Inválidos",
                        )
                    )
                    continue

                ids_vistos.add(pedido.id_pedido)
                nuevos_pedidos.append(pedido)

        self.pedidos.extend(nuevos_pedidos)
        reporte.aceptadas = len(nuevos_pedidos)
        self.guardar()

        if ruta_rechazos is not None:
            with open(ruta_rechazos, mode="w", encoding="utf-8", newline="") as f_out:
                escritor = csv.DictWriter(
                    f_out,
                    fieldnames=["linea", "identificador", "regla", "motivo", "subestado_rechazo"],
                )
                escritor.writeheader()
                for r in reporte.rechazadas:
                    escritor.writerow(
                        {
                            "linea": r.linea,
                            "identificador": r.identificador,
                            "regla": r.regla,
                            "motivo": r.motivo,
                            "subestado_rechazo": r.subestado_rechazo,
                        }
                    )

        return reporte
