"""Pruebas unitarias para los modelos de dominio (Cliente, Ruta, Pedido) y estados oficiales."""

import pytest

from modelos import (
    ESTADOS_VALIDOS,
    TRANSICIONES_PERMITIDAS,
    Cliente,
    ErrorTransicionEstado,
    Pedido,
    Ruta,
)


def test_catalogo_unico_estados_oficiales() -> None:
    """Verifica que los únicos estados operativos válidos sean estrictamente los 7 oficiales."""
    estados_esperados = (
        "Registrado",
        "En Validación",
        "Aprobado",
        "En Preparación",
        "En Ruta",
        "Entregado",
        "Cancelado",
    )
    assert ESTADOS_VALIDOS == estados_esperados
    assert set(TRANSICIONES_PERMITIDAS.keys()) == set(estados_esperados)


@pytest.mark.parametrize(
    "estado_obsoleto",
    ["pendiente", "en_transito", "entregado", "cancelado", "Cuarentena", "Bloqueado", "Rechazado"],
)
def test_rechazo_estados_obsoletos_o_no_oficiales(estado_obsoleto: str) -> None:
    """Verifica que estados obsoletos o subestados fuera del catálogo principal sean rechazados."""
    with pytest.raises(ValueError):
        Pedido("PED-01", "CLI-01", "Insumo", 10, "León", "Irapuato", "2026-10-18", estado_obsoleto)


def test_c02_serializacion_correcta_a_diccionario(cliente_base: Cliente) -> None:
    """C-02: Verifica que to_dict() y from_dict() conserven exactamente los campos."""
    diccionario = cliente_base.to_dict()
    assert diccionario == {
        "id_cliente": "CLI-01",
        "nombre": "Distribuidora Bajío",
        "ciudad": "Irapuato",
        "telefono": "4621002000",
    }
    reconstruido = Cliente.from_dict(diccionario)
    assert reconstruido.to_dict() == diccionario


@pytest.mark.parametrize(
    "origen,destino,distancia,tiempo",
    [
        ("Querétaro", "Irapuato", 50.0, 1.0),
        ("León", "Monterrey", 50.0, 1.0),
        ("León", "Celaya", -10.0, 1.0),
        ("León", "Guanajuato", 40.0, 0.0),
    ],
)
def test_c05_validacion_valores_fuera_del_catalogo_ruta(
    origen: str, destino: str, distancia: float, tiempo: float
) -> None:
    """C-05: Verifica que valores fuera del catálogo o límites inválidos lancen ValueError."""
    with pytest.raises(ValueError):
        Ruta("RUT-ERR", origen, destino, distancia, tiempo, "Operador")


@pytest.mark.parametrize(
    "cantidad,fecha,estado",
    [
        (0, "2026-10-18", "Registrado"),
        (-5, "2026-10-18", "Registrado"),
        ("12.5", "2026-10-18", "Registrado"),
        (10, "18-10-2026", "Registrado"),
        (10, "2026-10-18", "estado_inexistente"),
    ],
)
def test_c05_validacion_atributos_pedido(cantidad, fecha: str, estado: str) -> None:
    """C-05: Verifica validación de cantidad entera positiva, fecha YYYY-MM-DD y catálogo de estados."""
    with pytest.raises(ValueError):
        Pedido("PED-01", "CLI-01", "Caja", cantidad, "León", "Celaya", fecha, estado)


def test_c10_formato_salida_legible_str(cliente_base: Cliente, ruta_base: Ruta) -> None:
    """C-10: Verifica que __str__ y __repr__ devuelvan representaciones legibles con datos clave."""
    pedido = Pedido("PED-01", "CLI-01", "Insumo Médico", 15, "León", "Irapuato", "2026-10-18")
    assert pedido.estado == "Registrado"
    assert "CLI-01" in str(cliente_base) and "Distribuidora Bajío" in str(cliente_base)
    assert "RUT-01" in str(ruta_base) and "Irapuato" in str(ruta_base)
    assert "PED-01" in str(pedido) and "Insumo Médico" in str(pedido)
    assert "Pedido(" in repr(pedido)
