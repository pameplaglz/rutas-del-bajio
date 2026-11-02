"""Pruebas unitarias para los modelos de dominio (Cliente, Ruta, Pedido) y máquina de estados."""

from typing import List, Tuple

import pytest

from errores import ErrorTransicionEstado
from gestores import GestorClientes, GestorPedidos, GestorRutas
from modelos import (
    ESTADOS_VALIDOS,
    TRANSICIONES_PERMITIDAS,
    Cliente,
    Pedido,
    Ruta,
)


ESTADOS_OFICIALES_ESPERADOS: Tuple[str, ...] = (
    "Registrado",
    "En Validación",
    "Aprobado",
    "En Preparación",
    "En Ruta",
    "Entregado",
    "Cancelado",
)

ORACULO_TRANSICIONES_PERMITIDAS = {
    ("Registrado", "En Validación"),
    ("Registrado", "Cancelado"),
    ("En Validación", "Aprobado"),
    ("En Validación", "Cancelado"),
    ("Aprobado", "En Preparación"),
    ("Aprobado", "Cancelado"),
    ("En Preparación", "En Ruta"),
    ("En Ruta", "Entregado"),
}

PARES_TODOS_LOS_ESTADOS: List[Tuple[str, str, bool]] = [
    (origen, destino, (origen, destino) in ORACULO_TRANSICIONES_PERMITIDAS)
    for origen in ESTADOS_OFICIALES_ESPERADOS
    for destino in ESTADOS_OFICIALES_ESPERADOS
]


@pytest.mark.unitaria
def test_c02_serializacion_correcta_a_diccionario(cliente_base: Cliente, ruta_base: Ruta) -> None:
    """C-02: Verifica que to_dict() y from_dict() conserven exactamente los campos en las 3 entidades."""
    diccionario_cli = cliente_base.to_dict()
    assert diccionario_cli == {
        "id_cliente": "CLI-01",
        "nombre": "Distribuidora Bajío",
        "ciudad": "Irapuato",
        "telefono": "4621002000",
    }
    assert Cliente.from_dict(diccionario_cli).to_dict() == diccionario_cli
    assert Ruta.from_dict(ruta_base.to_dict()).to_dict() == ruta_base.to_dict()

    pedido = Pedido("PED-01", "CLI-01", "Insumo", 10, "León", "Irapuato", "2026-10-18")
    assert Pedido.from_dict(pedido.to_dict()).to_dict() == pedido.to_dict()


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "id_ruta,origen,destino,distancia,tiempo,transportista",
    [
        ("", "León", "Irapuato", 50.0, 1.0, "Operador"),
        ("RUT-ERR", "Querétaro", "Irapuato", 50.0, 1.0, "Operador"),
        ("RUT-ERR", "León", "Monterrey", 50.0, 1.0, "Operador"),
        ("RUT-ERR", "León", "León", 50.0, 1.0, "Operador"),
        ("RUT-ERR", "León", "Celaya", -10.0, 1.0, "Operador"),
        ("RUT-ERR", "León", "Guanajuato", 40.0, 0.0, "Operador"),
        ("RUT-ERR", "León", "Irapuato", True, 1.0, "Operador"),
        ("RUT-ERR", "León", "Irapuato", 50.0, False, "Operador"),
        ("RUT-ERR", "León", "Irapuato", 50.0, 1.0, "   "),
    ],
)
def test_c05_validacion_valores_fuera_del_catalogo_ruta(
    id_ruta: str,
    origen: str,
    destino: str,
    distancia: float,
    tiempo: float,
    transportista: str,
) -> None:
    """C-05: Verifica que valores fuera del catálogo o límites inválidos en Ruta lancen ValueError."""
    with pytest.raises(ValueError):
        Ruta(id_ruta, origen, destino, distancia, tiempo, transportista)


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "id_ped,id_cli,prod,cantidad,fecha,estado",
    [
        ("", "CLI-01", "Caja", 10, "2026-10-18", "Registrado"),
        ("PED-01", "", "Caja", 10, "2026-10-18", "Registrado"),
        ("PED-01", "CLI-01", "", 10, "2026-10-18", "Registrado"),
        ("PED-01", "CLI-01", "Caja", 0, "2026-10-18", "Registrado"),
        ("PED-01", "CLI-01", "Caja", -5, "2026-10-18", "Registrado"),
        ("PED-01", "CLI-01", "Caja", "12.5", "2026-10-18", "Registrado"),
        ("PED-01", "CLI-01", "Caja", 12.5, "2026-10-18", "Registrado"),
        ("PED-01", "CLI-01", "Caja", True, "2026-10-18", "Registrado"),
        ("PED-01", "CLI-01", "Caja", "abc", "2026-10-18", "Registrado"),
        ("PED-01", "CLI-01", "Caja", 10, "18-10-2026", "Registrado"),
        ("PED-01", "CLI-01", "Caja", 10, "2026-10-18", "estado_inexistente"),
        ("PED-01", "CLI-01", "Caja", 10, "2026-10-18", "pendiente"),
        ("PED-01", "CLI-01", "Caja", 10, "2026-10-18", "Rechazado"),
        ("PED-01", "CLI-01", "Caja", 10, "2026-10-18", "Cuarentena"),
    ],
)
def test_c05_validacion_atributos_pedido(
    id_ped: str, id_cli: str, prod: str, cantidad, fecha: str, estado: str
) -> None:
    """C-05: Verifica validación de campos obligatorios, cantidad entera, fecha y catálogo de estados."""
    with pytest.raises(ValueError):
        Pedido(id_ped, id_cli, prod, cantidad, "León", "Celaya", fecha, estado)


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "id_cli,nombre,ciudad,tel",
    [
        ("", "Ana", "León", "4771234567"),
        ("CLI-01", "", "León", "4771234567"),
        ("CLI-01", "Ana", "", "4771234567"),
        ("CLI-01", "Ana", "León", ""),
    ],
)
def test_c05_validacion_atributos_cliente(id_cli: str, nombre: str, ciudad: str, tel: str) -> None:
    """C-05: Verifica que campos vacíos al instanciar Cliente lancen ValueError."""
    with pytest.raises(ValueError):
        Cliente(id_cli, nombre, ciudad, tel)


@pytest.mark.unitaria
def test_c10_formato_salida_legible_str(cliente_base: Cliente, ruta_base: Ruta) -> None:
    """C-10: Verifica que __str__ y __repr__ devuelvan representaciones legibles con datos clave."""
    pedido = Pedido("PED-01", "CLI-01", "Insumo Médico", "15", "León", "Irapuato", "2026-10-18")
    assert pedido.estado == "Registrado"
    assert pedido.cantidad == 15
    assert "CLI-01" in str(cliente_base) and "Distribuidora Bajío" in str(cliente_base)
    assert "Cliente(" in repr(cliente_base)
    assert "RUT-01" in str(ruta_base) and "Irapuato" in str(ruta_base)
    assert "Ruta(" in repr(ruta_base)
    assert "PED-01" in str(pedido) and "Insumo Médico" in str(pedido)
    assert "Pedido(" in repr(pedido)


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "origen,destino,es_valida",
    PARES_TODOS_LOS_ESTADOS,
    ids=[f"{o}_a_{d}" for o, d, _ in PARES_TODOS_LOS_ESTADOS],
)
def test_c21_matriz_completa_49_transiciones_estados(
    origen: str, destino: str, es_valida: bool
) -> None:
    """C-21: Verifica los 49 pares (estado_origen, estado_destino) del catálogo de 7 estados."""
    datos = {
        "id_pedido": "PED-M21",
        "id_cliente": "CLI-01",
        "producto": "Caja",
        "cantidad": 10,
        "origen": "León",
        "destino": "Irapuato",
        "fecha_pedido": "2026-10-18",
        "estado": origen,
        "id_ruta": "RUT-01",
    }
    pedido = Pedido.from_dict(datos, restaurar_estado=True)
    assert pedido.estado == origen

    if es_valida:
        pedido.transicionar_estado(destino)
        assert pedido.estado == destino
    else:
        with pytest.raises(ErrorTransicionEstado):
            pedido.transicionar_estado(destino)
        assert pedido.estado == origen


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "estado_inicial,puede_cancelar",
    [
        ("Registrado", True),
        ("En Validación", True),
        ("Aprobado", True),
        ("En Preparación", False),
        ("En Ruta", False),
        ("Entregado", False),
        ("Cancelado", False),
    ],
)
def test_c22_reglas_cancelacion_por_estado(estado_inicial: str, puede_cancelar: bool) -> None:
    """C-22: Verifica que solo se pueda cancelar desde Registrado, En Validación y Aprobado."""
    pedido = Pedido.from_dict(
        {
            "id_pedido": "PED-C22",
            "id_cliente": "CLI-01",
            "producto": "Vacuna",
            "cantidad": 5,
            "origen": "León",
            "destino": "Celaya",
            "fecha_pedido": "2026-10-18",
            "estado": estado_inicial,
            "id_ruta": "",
        },
        restaurar_estado=True,
    )
    if puede_cancelar:
        pedido.transicionar_estado("Cancelado")
        assert pedido.estado == "Cancelado"
    else:
        with pytest.raises(ErrorTransicionEstado):
            pedido.transicionar_estado("Cancelado")
        assert pedido.estado == estado_inicial


@pytest.mark.unitaria
def test_c24_inmutabilidad_estado_y_estado_inicial_registrado(
    gestor_pedidos: GestorPedidos,
) -> None:
    """C-24: Verifica que estado sea propiedad de solo lectura y crear_pedido solo acepte Registrado."""
    with pytest.raises(ErrorTransicionEstado):
        Pedido("PED-24A", "CLI-01", "Insumo", 10, "León", "Irapuato", "2026-10-18", "En Ruta")

    pedido = Pedido("PED-24B", "CLI-01", "Insumo", 10, "León", "Irapuato", "2026-10-18")
    with pytest.raises(AttributeError):
        pedido.estado = "Entregado"  # type: ignore[misc]

    with pytest.raises(ValueError, match="no pertenece al catálogo oficial"):
        pedido.transicionar_estado("Inexistente")

    pedido_restaurado = Pedido.from_dict(
        {
            "id_pedido": "PED-24C",
            "id_cliente": "CLI-01",
            "producto": "Insumo",
            "cantidad": 10,
            "origen": "León",
            "destino": "Irapuato",
            "fecha_pedido": "2026-10-18",
            "estado": "En Ruta",
            "id_ruta": "RUT-01",
        },
        restaurar_estado=True,
    )
    with pytest.raises(ErrorTransicionEstado, match="estado inicial 'Registrado'"):
        gestor_pedidos.crear_pedido(pedido_restaurado)


@pytest.mark.unitaria
def test_c31_validacion_origen_destino_y_coincidencia_con_ruta(
    tmp_path, gestor_clientes: GestorClientes, gestor_rutas: GestorRutas
) -> None:
    """C-31: Verifica validación de ciudades del Bajío, normalización Leon->León y coincidencia con ruta."""
    ruta_norm = Ruta("RUT-NORM", "Leon", "Salamanca", 45.0, 0.8, "Pedro")
    assert ruta_norm.origen == "León"

    ped_norm = Pedido("PED-31A", "CLI-01", "Caja", 5, "Leon", "Salamanca", "2026-10-18")
    assert ped_norm.origen == "León"

    with pytest.raises(ValueError, match="Origen inválido"):
        Pedido("PED-31B", "CLI-01", "Caja", 5, "Guadalajara", "Irapuato", "2026-10-18")

    with pytest.raises(ValueError, match="Destino inválido"):
        Pedido("PED-31C", "CLI-01", "Caja", 5, "León", "CDMX", "2026-10-18")

    with pytest.raises(ValueError, match="misma ciudad"):
        Pedido("PED-31D", "CLI-01", "Caja", 5, "León", "Leon", "2026-10-18")

    gestor_ped = GestorPedidos(str(tmp_path / "pedidos_c31.csv"), gestor_clientes, gestor_rutas)
    # RUT-01 es León -> Irapuato; un pedido León -> Celaya con RUT-01 debe ser rechazado
    ped_inconsistente = Pedido(
        "PED-31E", "CLI-01", "Caja", 5, "León", "Celaya", "2026-10-18", "Registrado", "RUT-01"
    )
    with pytest.raises(ValueError, match="no coincide con la ruta"):
        gestor_ped.crear_pedido(ped_inconsistente)
