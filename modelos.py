"""Módulo de modelos de dominio para el sistema logístico Rutas del Bajío.

Define las entidades principales (Cliente, Ruta, Pedido) junto con sus reglas
de validación de atributos, máquina de estados y métodos de serialización CSV.
"""

from datetime import datetime
from typing import Any, Dict, Set


DESTINOS_PERMITIDOS: Set[str] = {"León", "Leon", "Irapuato", "Celaya", "Salamanca", "Guanajuato"}

ESTADOS_VALIDOS: Set[str] = {
    # Catálogo Etapa 1
    "pendiente",
    "en_transito",
    "entregado",
    "cancelado",
    # Catálogo Máquina de Estados Etapa 2
    "Registrado",
    "En Validación",
    "Aprobado",
    "Rechazado",
    "En Preparación",
    "En Ruta",
    "Entregado",
    "Cancelado",
}

TRANSICIONES_PERMITIDAS: Dict[str, Set[str]] = {
    # Etapa 1
    "pendiente": {"en_transito", "cancelado"},
    "en_transito": {"entregado"},
    "entregado": set(),
    "cancelado": set(),
    # Etapa 2
    "Registrado": {"En Validación", "Cancelado"},
    "En Validación": {"Aprobado", "Rechazado", "Cancelado"},
    "Aprobado": {"En Preparación", "Cancelado"},
    "Rechazado": set(),
    "En Preparación": {"En Ruta"},
    "En Ruta": {"Entregado"},
    "Entregado": set(),
    "Cancelado": set(),
}


class ErrorTransicionEstado(ValueError):
    """Excepción lanzada cuando se intenta realizar una transición de estado prohibida."""


class Cliente:
    """Representa un cliente registrado en Rutas del Bajío."""

    def __init__(self, id_cliente: str, nombre: str, ciudad: str, telefono: str) -> None:
        if not str(id_cliente).strip():
            raise ValueError("El id_cliente no puede estar vacío.")
        if not str(nombre).strip():
            raise ValueError("El nombre del cliente es obligatorio.")
        if not str(ciudad).strip():
            raise ValueError("La ciudad del cliente es obligatoria.")
        if not str(telefono).strip():
            raise ValueError("El teléfono del cliente es obligatorio.")

        self.id_cliente: str = str(id_cliente).strip()
        self.nombre: str = str(nombre).strip()
        self.ciudad: str = str(ciudad).strip()
        self.telefono: str = str(telefono).strip()

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
        """Reconstruye una instancia de Cliente a partir de una fila leída con csv.DictReader."""
        return cls(
            id_cliente=data["id_cliente"],
            nombre=data["nombre"],
            ciudad=data.get("ciudad") or data.get("Ciudad", ""),
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

    def __init__(
        self,
        id_ruta: str,
        origen: str,
        destino: str,
        distancia_km: float,
        tiempo_estimado: float,
        transportista: str,
    ) -> None:
        if not str(id_ruta).strip():
            raise ValueError("El id_ruta no puede estar vacío.")
        origen_limpio = str(origen).strip()
        destino_limpio = str(destino).strip()
        if origen_limpio not in {"León", "Leon"}:
            raise ValueError("El punto de origen debe ser León.")
        if destino_limpio not in DESTINOS_PERMITIDOS or destino_limpio in {"León", "Leon"}:
            raise ValueError(f"Destino inválido: {destino_limpio}. Debe pertenecer al catálogo del Bajío.")
        if float(distancia_km) <= 0:
            raise ValueError("La distancia en kilómetros debe ser un número positivo.")
        if float(tiempo_estimado) <= 0:
            raise ValueError("El tiempo estimado debe ser un número positivo.")
        if not str(transportista).strip():
            raise ValueError("El nombre del transportista es obligatorio.")

        self.id_ruta: str = str(id_ruta).strip()
        self.origen: str = origen_limpio
        self.destino: str = destino_limpio
        self.distancia_km: float = float(distancia_km)
        self.tiempo_estimado: float = float(tiempo_estimado)
        self.transportista: str = str(transportista).strip()

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
        """Reconstruye una instancia de Ruta a partir de una fila leída con csv.DictReader."""
        return cls(
            id_ruta=data["id_ruta"],
            origen=data["origen"],
            destino=data["destino"],
            distancia_km=float(data["distancia_km"]),
            tiempo_estimado=float(data["tiempo_estimado"]),
            transportista=data.get("transportista") or data.get("Transportista", ""),
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
    """Representa una orden de pedido logístico y controla su máquina de estados."""

    def __init__(
        self,
        id_pedido: str,
        id_cliente: str,
        producto: str,
        cantidad: int,
        origen: str,
        destino: str,
        fecha_pedido: str,
        estado: str = "pendiente",
        id_ruta: str = "",
    ) -> None:
        if not str(id_pedido).strip():
            raise ValueError("El id_pedido no puede estar vacío.")
        if not str(id_cliente).strip():
            raise ValueError("El id_cliente es obligatorio.")
        if not str(producto).strip():
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

        fecha_limpia = str(fecha_pedido).strip()
        try:
            datetime.strptime(fecha_limpia, "%Y-%m-%d")
        except ValueError as exc:
            raise ValueError("La fecha debe registrarse en formato YYYY-MM-DD.") from exc

        estado_limpio = str(estado).strip() if estado else "pendiente"
        if estado_limpio not in ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido: {estado_limpio}.")

        self.id_pedido: str = str(id_pedido).strip()
        self.id_cliente: str = str(id_cliente).strip()
        self.producto: str = str(producto).strip()
        self.cantidad: int = cantidad_int
        self.origen: str = str(origen).strip()
        self.destino: str = str(destino).strip()
        self.fecha_pedido: str = fecha_limpia
        self.estado: str = estado_limpio
        self.id_ruta: str = str(id_ruta).strip() if id_ruta is not None else ""

    def transicionar_estado(self, nuevo_estado: str) -> None:
        """Ejecuta una transición en la máquina de estados validando las reglas del negocio."""
        if nuevo_estado not in ESTADOS_VALIDOS:
            raise ValueError(f"El estado '{nuevo_estado}' no pertenece al catálogo válido.")
        permitidos = TRANSICIONES_PERMITIDAS.get(self.estado, set())
        if nuevo_estado not in permitidos:
            raise ErrorTransicionEstado(
                f"Transición prohibida de '{self.estado}' a '{nuevo_estado}'."
            )
        self.estado = nuevo_estado

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
            "estado": self.estado,
            "id_ruta": self.id_ruta,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pedido":
        """Reconstruye una instancia de Pedido a partir de una fila leída con csv.DictReader."""
        return cls(
            id_pedido=data["id_pedido"],
            id_cliente=data["id_cliente"],
            producto=data.get("producto") or data.get("Producto", ""),
            cantidad=int(data["cantidad"]),
            origen=data.get("origen") or data.get("Origen", ""),
            destino=data.get("destino") or data.get("Destino", ""),
            fecha_pedido=data["fecha_pedido"],
            estado=data.get("estado", "pendiente"),
            id_ruta=data.get("id_ruta", ""),
        )

    def __str__(self) -> str:
        return (
            f"Pedido({self.id_pedido}: {self.producto} x{self.cantidad}, "
            f"Cliente: {self.id_cliente}, Estado: {self.estado}, Ruta: {self.id_ruta or 'Sin asignar'})"
        )

    def __repr__(self) -> str:
        return (
            f"Pedido(id_pedido={self.id_pedido!r}, id_cliente={self.id_cliente!r}, "
            f"producto={self.producto!r}, cantidad={self.cantidad!r}, origen={self.origen!r}, "
            f"destino={self.destino!r}, fecha_pedido={self.fecha_pedido!r}, "
            f"estado={self.estado!r}, id_ruta={self.id_ruta!r})"
        )
