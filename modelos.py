"""Módulo de modelos de dominio para el sistema logístico Rutas del Bajío.

Define las entidades principales (Cliente, Ruta, Pedido) junto con sus reglas
de validación de atributos, máquina de estados inviolable y serialización CSV.

Criterios de limpieza vs. rechazo en modelos:
- Se LIMPIA:
  1. Espacios en blanco extremos (`strip()`) en cadenas de texto.
  2. Normalización ortográfica de la ciudad `"Leon"` -> `"León"`.
  3. Estado vacío (`""`) al construir o reconstruir un Pedido -> `"Registrado"`.
- Se RECHAZA (lanza `ValueError` o `ErrorTransicionEstado`):
  1. Campos obligatorios vacíos.
  2. `Ruta.origen` distinto de `"León"`, o `Ruta.destino` fuera del catálogo del Bajío
     (`Irapuato`, `Celaya`, `Salamanca`, `Guanajuato`).
  3. `Pedido.origen` o `Pedido.destino` fuera del catálogo del Bajío, o `origen == destino`.
  4. `distancia_km <= 0`, `tiempo_estimado <= 0`, o `cantidad <= 0` / no entera.
  5. `fecha_pedido` que no cumpla el formato estricto `YYYY-MM-DD`.
  6. `estado` fuera de los 7 estados oficiales (`ESTADOS_VALIDOS`), o creación directa de
     un `Pedido` nuevo en un estado distinto de `"Registrado"` sin bandera de restauración.
"""

from datetime import datetime
from typing import Any, Dict, Set, Tuple

from errores import ErrorTransicionEstado


CIUDADES_BAJIO: Tuple[str, ...] = (
    "León",
    "Irapuato",
    "Celaya",
    "Salamanca",
    "Guanajuato",
)

DESTINOS_PERMITIDOS: Set[str] = set(CIUDADES_BAJIO)

# Catálogo único y estricto de 7 estados operativos oficiales del pedido
ESTADOS_VALIDOS: Tuple[str, ...] = (
    "Registrado",
    "En Validación",
    "Aprobado",
    "En Preparación",
    "En Ruta",
    "Entregado",
    "Cancelado",
)

TRANSICIONES_PERMITIDAS: Dict[str, Set[str]] = {
    "Registrado": {"En Validación", "Cancelado"},
    "En Validación": {"Aprobado", "Cancelado"},
    "Aprobado": {"En Preparación", "Cancelado"},
    "En Preparación": {"En Ruta"},
    "En Ruta": {"Entregado"},
    "Entregado": set(),
    "Cancelado": set(),
}


def normalizar_ciudad(nombre_ciudad: str) -> str:
    """Limpia espacios extremos y normaliza 'Leon' a 'León' con tilde."""
    limpia = str(nombre_ciudad).strip()
    if limpia == "Leon":
        return "León"
    return limpia


class Cliente:
    """Representa un cliente registrado en Rutas del Bajío."""

    CAMPOS_VALIDOS: Tuple[str, ...] = ("id_cliente", "nombre", "ciudad", "telefono")

    def __init__(self, id_cliente: str, nombre: str, ciudad: str, telefono: str) -> None:
        id_limpio = str(id_cliente).strip() if id_cliente is not None else ""
        nombre_limpio = str(nombre).strip() if nombre is not None else ""
        ciudad_limpia = normalizar_ciudad(ciudad) if ciudad is not None else ""
        tel_limpio = str(telefono).strip() if telefono is not None else ""

        if not id_limpio:
            raise ValueError("El id_cliente no puede estar vacío.")
        if not nombre_limpio:
            raise ValueError("El nombre del cliente es obligatorio.")
        if not ciudad_limpia:
            raise ValueError("La ciudad del cliente es obligatoria.")
        if not tel_limpio:
            raise ValueError("El teléfono del cliente es obligatorio.")

        self.id_cliente: str = id_limpio
        self.nombre: str = nombre_limpio
        self.ciudad: str = ciudad_limpia
        self.telefono: str = tel_limpio

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia de Cliente en un diccionario para persistencia CSV."""
        return {
            "id_cliente": self.id_cliente,
            "nombre": self.nombre,
            "ciudad": self.ciudad,
            "telefono": self.telefono,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cliente":
        """Reconstruye una instancia de Cliente desde un diccionario con claves exactas en minúscula."""
        return cls(
            id_cliente=data["id_cliente"],
            nombre=data["nombre"],
            ciudad=data["ciudad"],
            telefono=data["telefono"],
        )

    def __str__(self) -> str:
        return f"Cliente({self.id_cliente}: {self.nombre}, {self.ciudad}, Tel: {self.telefono})"

    def __repr__(self) -> str:
        return (
            f"Cliente(id_cliente={self.id_cliente!r}, nombre={self.nombre!r}, "
            f"ciudad={self.ciudad!r}, telefono={self.telefono!r})"
        )


class Ruta:
    """Representa una ruta logística de transporte en la región del Bajío."""

    CAMPOS_VALIDOS: Tuple[str, ...] = (
        "id_ruta",
        "origen",
        "destino",
        "distancia_km",
        "tiempo_estimado",
        "transportista",
    )

    def __init__(
        self,
        id_ruta: str,
        origen: str,
        destino: str,
        distancia_km: float,
        tiempo_estimado: float,
        transportista: str,
    ) -> None:
        id_limpio = str(id_ruta).strip() if id_ruta is not None else ""
        if not id_limpio:
            raise ValueError("El id_ruta no puede estar vacío.")

        origen_limpio = normalizar_ciudad(origen) if origen is not None else ""
        destino_limpio = normalizar_ciudad(destino) if destino is not None else ""

        if origen_limpio != "León":
            raise ValueError("El punto de origen debe ser León.")
        if destino_limpio not in DESTINOS_PERMITIDOS or destino_limpio == "León":
            raise ValueError(
                f"Destino inválido: {destino_limpio!r}. Debe pertenecer al catálogo del Bajío."
            )

        if isinstance(distancia_km, bool):
            raise ValueError("La distancia en kilómetros debe ser numérica.")
        dist_float = float(distancia_km)
        if dist_float <= 0:
            raise ValueError("La distancia en kilómetros debe ser un número positivo.")

        if isinstance(tiempo_estimado, bool):
            raise ValueError("El tiempo estimado debe ser numérico.")
        tiempo_float = float(tiempo_estimado)
        if tiempo_float <= 0:
            raise ValueError("El tiempo estimado debe ser un número positivo.")

        transp_limpio = str(transportista).strip() if transportista is not None else ""
        if not transp_limpio:
            raise ValueError("El nombre del transportista es obligatorio.")

        self.id_ruta: str = id_limpio
        self.origen: str = origen_limpio
        self.destino: str = destino_limpio
        self.distancia_km: float = dist_float
        self.tiempo_estimado: float = tiempo_float
        self.transportista: str = transp_limpio

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia de Ruta en un diccionario para persistencia CSV."""
        return {
            "id_ruta": self.id_ruta,
            "origen": self.origen,
            "destino": self.destino,
            "distancia_km": self.distancia_km,
            "tiempo_estimado": self.tiempo_estimado,
            "transportista": self.transportista,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Ruta":
        """Reconstruye una instancia de Ruta desde un diccionario con claves exactas en minúscula."""
        return cls(
            id_ruta=data["id_ruta"],
            origen=data["origen"],
            destino=data["destino"],
            distancia_km=float(data["distancia_km"]),
            tiempo_estimado=float(data["tiempo_estimado"]),
            transportista=data["transportista"],
        )

    def __str__(self) -> str:
        return (
            f"Ruta({self.id_ruta}: {self.origen} -> {self.destino}, "
            f"{self.distancia_km} km, {self.tiempo_estimado} h, Op: {self.transportista})"
        )

    def __repr__(self) -> str:
        return (
            f"Ruta(id_ruta={self.id_ruta!r}, origen={self.origen!r}, destino={self.destino!r}, "
            f"distancia_km={self.distancia_km!r}, tiempo_estimado={self.tiempo_estimado!r}, "
            f"transportista={self.transportista!r})"
        )


class Pedido:
    """Representa una orden de pedido logístico y controla su máquina de estados inviolable."""

    CAMPOS_VALIDOS: Tuple[str, ...] = (
        "id_pedido",
        "id_cliente",
        "producto",
        "cantidad",
        "origen",
        "destino",
        "fecha_pedido",
        "estado",
        "id_ruta",
    )

    def __init__(
        self,
        id_pedido: str,
        id_cliente: str,
        producto: str,
        cantidad: int,
        origen: str,
        destino: str,
        fecha_pedido: str,
        estado: str = "Registrado",
        id_ruta: str = "",
        *,
        _restaurar_estado: bool = False,
    ) -> None:
        id_ped_limpio = str(id_pedido).strip() if id_pedido is not None else ""
        id_cli_limpio = str(id_cliente).strip() if id_cliente is not None else ""
        prod_limpio = str(producto).strip() if producto is not None else ""

        if not id_ped_limpio:
            raise ValueError("El id_pedido no puede estar vacío.")
        if not id_cli_limpio:
            raise ValueError("El id_cliente es obligatorio.")
        if not prod_limpio:
            raise ValueError("El producto es obligatorio.")

        if isinstance(cantidad, bool) or not isinstance(cantidad, int):
            try:
                if isinstance(cantidad, str) and "." in cantidad:
                    raise ValueError("La cantidad debe ser estrictamente entera.")
                cantidad_int = int(cantidad)
                if float(cantidad) != cantidad_int:
                    raise ValueError("La cantidad debe ser estrictamente entera.")
            except (ValueError, TypeError) as exc:
                raise ValueError("El campo cantidad de un pedido debe ser únicamente entero.") from exc
        else:
            cantidad_int = cantidad

        if cantidad_int <= 0:
            raise ValueError("La cantidad del pedido debe ser un entero positivo.")

        origen_limpio = normalizar_ciudad(origen) if origen is not None else ""
        destino_limpio = normalizar_ciudad(destino) if destino is not None else ""
        if origen_limpio not in DESTINOS_PERMITIDOS:
            raise ValueError(
                f"Origen inválido: {origen_limpio!r}. Debe pertenecer al catálogo del Bajío."
            )
        if destino_limpio not in DESTINOS_PERMITIDOS:
            raise ValueError(
                f"Destino inválido: {destino_limpio!r}. Debe pertenecer al catálogo del Bajío."
            )
        if origen_limpio == destino_limpio:
            raise ValueError("El origen y el destino del pedido no pueden ser la misma ciudad.")

        fecha_limpia = str(fecha_pedido).strip() if fecha_pedido is not None else ""
        try:
            datetime.strptime(fecha_limpia, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("La fecha debe registrarse en formato YYYY-MM-DD.") from exc

        estado_limpio = str(estado).strip() if estado else "Registrado"
        if estado_limpio not in ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado inválido: {estado_limpio!r}. Estados válidos: {ESTADOS_VALIDOS}."
            )
        if not _restaurar_estado and estado_limpio != "Registrado":
            raise ErrorTransicionEstado(
                f"Un pedido nuevo solo puede crearse en estado 'Registrado', no en '{estado_limpio}'."
            )

        self.id_pedido: str = id_ped_limpio
        self.id_cliente: str = id_cli_limpio
        self.producto: str = prod_limpio
        self.cantidad: int = cantidad_int
        self.origen: str = origen_limpio
        self.destino: str = destino_limpio
        self.fecha_pedido: str = fecha_limpia
        self._estado: str = estado_limpio
        self.id_ruta: str = str(id_ruta).strip() if id_ruta is not None else ""

    @property
    def estado(self) -> str:
        """Devuelve el estado actual del pedido (propiedad de solo lectura)."""
        return self._estado

    def puede_transicionar_a(self, nuevo_estado: str) -> bool:
        """Indica si la transición desde el estado actual hacia nuevo_estado es válida."""
        return nuevo_estado in TRANSICIONES_PERMITIDAS.get(self._estado, set())

    def transicionar_estado(self, nuevo_estado: str) -> None:
        """Ejecuta una transición en la máquina de estados validando las reglas del negocio."""
        if nuevo_estado not in ESTADOS_VALIDOS:
            raise ValueError(f"El estado '{nuevo_estado}' no pertenece al catálogo oficial.")
        if not self.puede_transicionar_a(nuevo_estado):
            raise ErrorTransicionEstado(
                f"Transición prohibida de '{self._estado}' a '{nuevo_estado}'."
            )
        self._estado = nuevo_estado

    def to_dict(self) -> Dict[str, Any]:
        """Convierte la instancia de Pedido en un diccionario para persistencia CSV."""
        return {
            "id_pedido": self.id_pedido,
            "id_cliente": self.id_cliente,
            "producto": self.producto,
            "cantidad": self.cantidad,
            "origen": self.origen,
            "destino": self.destino,
            "fecha_pedido": self.fecha_pedido,
            "estado": self._estado,
            "id_ruta": self.id_ruta,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], *, restaurar_estado: bool = True) -> "Pedido":
        """Reconstruye una instancia de Pedido desde un diccionario CSV con claves en minúscula.

        Args:
            data: Diccionario con los campos exactos del CSV de pedidos.
            restaurar_estado: Si es True (por defecto al leer de persistencia), permite
                restaurar cualquier estado válido del catálogo. Si es False, exige 'Registrado'.
        """
        return cls(
            id_pedido=data["id_pedido"],
            id_cliente=data["id_cliente"],
            producto=data["producto"],
            cantidad=int(data["cantidad"]),
            origen=data["origen"],
            destino=data["destino"],
            fecha_pedido=data["fecha_pedido"],
            estado=data.get("estado") or "Registrado",
            id_ruta=data.get("id_ruta", ""),
            _restaurar_estado=restaurar_estado,
        )

    def __str__(self) -> str:
        return (
            f"Pedido({self.id_pedido}: {self.producto} x{self.cantidad}, "
            f"Cliente: {self.id_cliente}, Estado: {self._estado}, Ruta: {self.id_ruta or 'Sin asignar'})"
        )

    def __repr__(self) -> str:
        return (
            f"Pedido(id_pedido={self.id_pedido!r}, id_cliente={self.id_cliente!r}, "
            f"producto={self.producto!r}, cantidad={self.cantidad!r}, origen={self.origen!r}, "
            f"destino={self.destino!r}, fecha_pedido={self.fecha_pedido!r}, "
            f"estado={self._estado!r}, id_ruta={self.id_ruta!r})"
        )
