"""Módulo principal de ejecución y demostración para el sistema Rutas del Bajío."""

import os
import tempfile

from gestores import GestorClientes, GestorPedidos, GestorRutas
from modelos import Cliente, Pedido, Ruta


def ejecutar_flujo_demostracion() -> None:
    """Ejecuta un flujo integral de demostración CRUD y máquina de estados en carpeta temporal."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ruta_clientes = os.path.join(tmp_dir, "clientes.csv")
        ruta_rutas = os.path.join(tmp_dir, "rutas.csv")
        ruta_pedidos = os.path.join(tmp_dir, "pedidos.csv")

        gestor_clientes = GestorClientes(ruta_clientes)
        gestor_rutas = GestorRutas(ruta_rutas)
        gestor_pedidos = GestorPedidos(ruta_pedidos, gestor_clientes, gestor_rutas)

        cliente = Cliente("CLI-01", "Comercializadora del Bajío", "Irapuato", "4621234567")
        ruta = Ruta("RUT-01", "León", "Irapuato", 68.5, 1.2, "Carlos Mendoza")
        gestor_clientes.crear_cliente(cliente)
        gestor_rutas.crear_ruta(ruta)

        pedido = Pedido(
            id_pedido="PED-001",
            id_cliente="CLI-01",
            producto="Lote Lácteos Refrigerados",
            cantidad=50,
            origen="León",
            destino="Irapuato",
            fecha_pedido="2026-10-18",
            estado="Registrado",
            id_ruta="RUT-01",
        )
        gestor_pedidos.crear_pedido(pedido)

        for estado in ["En Validación", "Aprobado", "En Preparación", "En Ruta", "Entregado"]:
            gestor_pedidos.cambiar_estado_pedido("PED-001", estado)

        print("=== Sistema Logístico Rutas del Bajío ===")
        print(f"Clientes registrados: {len(gestor_clientes.listar_clientes())}")
        print(f"Rutas activas: {len(gestor_rutas.listar_rutas())}")
        print(f"Pedido procesado: {gestor_pedidos.buscar_pedido('PED-001')}")


if __name__ == "__main__":
    ejecutar_flujo_demostracion()
