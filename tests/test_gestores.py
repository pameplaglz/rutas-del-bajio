"""Pruebas unitarias y de integración para GestorClientes, GestorRutas y GestorPedidos."""

import pytest

from gestores import GestorClientes, GestorPedidos, GestorRutas
from modelos import Cliente, Pedido, Ruta


def test_c01_gestor_arranca_vacio_si_archivo_no_existe(tmp_path) -> None:
    """C-01: Si la ruta del archivo CSV no existe, el gestor inicia con colección vacía sin errores."""
    gestor = GestorClientes(str(tmp_path / "no_existe.csv"))
    assert gestor.listar_clientes() == []


def test_c03_rechazo_identificadores_duplicados(gestor_clientes: GestorClientes, cliente_base: Cliente) -> None:
    """C-03: Insertar dos elementos con el mismo ID lanza ValueError y mantiene el archivo intacto."""
    contenido_antes = open(gestor_clientes.archivo_csv, encoding="utf-8").read()
    with pytest.raises(ValueError):
        gestor_clientes.crear_cliente(cliente_base)
    contenido_despues = open(gestor_clientes.archivo_csv, encoding="utf-8").read()
    assert contenido_antes == contenido_despues


def test_c04_llave_foranea_inexistente_descarta_fila_y_registra(
    tmp_path, gestor_clientes: GestorClientes, gestor_rutas: GestorRutas
) -> None:
    """C-04: Una fila de pedido con id_cliente inexistente se descarta y se registra en descartados."""
    archivo_pedidos = tmp_path / "pedidos_corruptos.csv"
    archivo_pedidos.write_text(
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta\n"
        "PED-99,CLI-NO-EXISTE,Cajas,10,León,Irapuato,2026-10-18,Registrado,RUT-01\n",
        encoding="utf-8",
    )
    gestor = GestorPedidos(str(archivo_pedidos), gestor_clientes, gestor_rutas)
    assert gestor.listar_pedidos() == []
    assert "PED-99" in gestor.descartados


def test_c06_eliminar_id_inexistente_retorna_falso(gestor_clientes: GestorClientes) -> None:
    """C-06: Intentar eliminar un ID que no existe retorna False sin alterar los datos."""
    assert gestor_clientes.eliminar_cliente("CLI-999") is False
    assert len(gestor_clientes.listar_clientes()) == 1


def test_c07_persistencia_de_la_eliminacion(tmp_path, gestor_clientes: GestorClientes) -> None:
    """C-07: Al eliminar un registro y recargar el gestor desde el CSV, el registro ya no aparece."""
    assert gestor_clientes.eliminar_cliente("CLI-01") is True
    recargado = GestorClientes(gestor_clientes.archivo_csv)
    assert recargado.buscar_cliente("CLI-01") is None


def test_c08_filtrado_correcto_por_id(gestor_pedidos: GestorPedidos) -> None:
    """C-08: Buscar un ID existente retorna el objeto exacto asociado."""
    pedido = Pedido("PED-10", "CLI-01", "Componentes", 20, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01")
    gestor_pedidos.crear_pedido(pedido)
    encontrado = gestor_pedidos.buscar_pedido("PED-10")
    assert encontrado is not None
    assert encontrado.producto == "Componentes"


def test_c09_consulta_elementos_asociados_por_relacion(gestor_pedidos: GestorPedidos) -> None:
    """C-09: Consultar dependencias por cliente o por estado devuelve la lista filtrada correcta."""
    p1 = Pedido("PED-01", "CLI-01", "Prod A", 5, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01")
    p2 = Pedido("PED-02", "CLI-01", "Prod B", 8, "León", "Irapuato", "2026-10-18", "En Ruta", "RUT-01")
    gestor_pedidos.crear_pedido(p1)
    gestor_pedidos.crear_pedido(p2)

    assert len(gestor_pedidos.listar_pedidos_por_cliente("CLI-01")) == 2
    assert len(gestor_pedidos.listar_pedidos_por_estado("En Ruta")) == 1


def test_c11_manejo_archivo_csv_solo_con_cabeceras(tmp_path) -> None:
    """C-11: Un archivo CSV que solo contiene la fila de cabeceras se carga como lista vacía sin errores."""
    csv_vacio = tmp_path / "solo_cabeceras.csv"
    csv_vacio.write_text("id_cliente,nombre,ciudad,telefono\n", encoding="utf-8")
    gestor = GestorClientes(str(csv_vacio))
    assert gestor.listar_clientes() == []


@pytest.mark.integracion
def test_c12_flujo_integral_dependencias(tmp_path) -> None:
    """C-12: Alta, guardado, transición de estados oficiales, recarga desde disco y consulta cruzada."""
    g_cli = GestorClientes(str(tmp_path / "clientes.csv"))
    g_rut = GestorRutas(str(tmp_path / "rutas.csv"))
    g_cli.crear_cliente(Cliente("CLI-100", "AgroBajío", "Celaya", "4619998877"))
    g_rut.crear_ruta(Ruta("RUT-100", "León", "Celaya", 125.0, 1.8, "Laura Gómez"))

    g_ped = GestorPedidos(str(tmp_path / "pedidos.csv"), g_cli, g_rut)
    g_ped.crear_pedido(
        Pedido("PED-100", "CLI-100", "Fertilizante", 40, "León", "Celaya", "2026-10-18", "Registrado", "RUT-100")
    )
    g_ped.cambiar_estado_pedido("PED-100", "En Validación")
    g_ped.cambiar_estado_pedido("PED-100", "Aprobado")
    g_ped.cambiar_estado_pedido("PED-100", "En Preparación")
    g_ped.cambiar_estado_pedido("PED-100", "En Ruta")

    g_ped_recargado = GestorPedidos(str(tmp_path / "pedidos.csv"), g_cli, g_rut)
    ped = g_ped_recargado.buscar_pedido("PED-100")
    assert ped is not None
    assert ped.estado == "En Ruta"
    assert ped.id_cliente == "CLI-100"
