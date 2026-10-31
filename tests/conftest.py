"""Fixtures centralizadas con pytest y aislamiento mediante tmp_path."""

import pytest

from gestores import GestorClientes, GestorPedidos, GestorRutas
from modelos import Cliente, Pedido, Ruta


@pytest.fixture
def cliente_base() -> Cliente:
    """Proporciona una instancia válida de Cliente para pruebas."""
    return Cliente("CLI-01", "Distribuidora Bajío", "Irapuato", "4621002000")


@pytest.fixture
def ruta_base() -> Ruta:
    """Proporciona una instancia válida de Ruta para pruebas."""
    return Ruta("RUT-01", "León", "Irapuato", 65.0, 1.1, "Juan Pérez")


@pytest.fixture
def gestor_clientes(tmp_path, cliente_base: Cliente) -> GestorClientes:
    """GestorClientes inicializado en un archivo temporal con un cliente base."""
    gestor = GestorClientes(str(tmp_path / "clientes.csv"))
    gestor.crear_cliente(cliente_base)
    return gestor


@pytest.fixture
def gestor_rutas(tmp_path, ruta_base: Ruta) -> GestorRutas:
    """GestorRutas inicializado en un archivo temporal con una ruta base."""
    gestor = GestorRutas(str(tmp_path / "rutas.csv"))
    gestor.crear_ruta(ruta_base)
    return gestor


@pytest.fixture
def gestor_pedidos(tmp_path, gestor_clientes: GestorClientes, gestor_rutas: GestorRutas) -> GestorPedidos:
    """GestorPedidos aislado en carpeta temporal con gestores de clientes y rutas inyectados."""
    return GestorPedidos(
        str(tmp_path / "pedidos.csv"),
        gestor_clientes=gestor_clientes,
        gestor_rutas=gestor_rutas,
    )
