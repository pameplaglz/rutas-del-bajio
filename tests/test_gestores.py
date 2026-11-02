"""Pruebas unitarias, de integración y de aceptación para GestorClientes, GestorRutas y GestorPedidos."""

import os

import pytest

from errores import ErrorIntegridadReferencial, ErrorTransicionEstado
from gestores import GestorClientes, GestorPedidos, GestorRutas, RegistroDescarte
from main import ejecutar_flujo_demostracion
from modelos import Cliente, Pedido, Ruta


@pytest.mark.unitaria
def test_c01_gestor_arranca_vacio_si_archivo_no_existe(tmp_path) -> None:
    """C-01: Si la ruta del archivo CSV no existe, el gestor inicia con colección vacía sin errores."""
    g_cli = GestorClientes(str(tmp_path / "no_existe_cli.csv"))
    g_rut = GestorRutas(str(tmp_path / "no_existe_rut.csv"))
    g_ped = GestorPedidos(str(tmp_path / "no_existe_ped.csv"), g_cli, g_rut)
    assert g_cli.listar_clientes() == []
    assert g_rut.listar_rutas() == []
    assert g_ped.listar_pedidos() == []


@pytest.mark.integracion
def test_c03_rechazo_identificadores_duplicados(
    gestor_clientes: GestorClientes,
    gestor_rutas: GestorRutas,
    gestor_pedidos: GestorPedidos,
    cliente_base: Cliente,
    ruta_base: Ruta,
) -> None:
    """C-03: Insertar dos elementos con el mismo ID lanza ValueError y mantiene el archivo intacto."""
    contenido_antes = open(gestor_clientes.archivo_csv, encoding="utf-8").read()
    with pytest.raises(ValueError, match="Ya existe un cliente"):
        gestor_clientes.crear_cliente(cliente_base)
    contenido_despues = open(gestor_clientes.archivo_csv, encoding="utf-8").read()
    assert contenido_antes == contenido_despues

    with pytest.raises(ValueError, match="Ya existe una ruta"):
        gestor_rutas.crear_ruta(ruta_base)

    ped = Pedido("PED-DUP", "CLI-01", "Caja", 5, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01")
    gestor_pedidos.crear_pedido(ped)
    with pytest.raises(ValueError, match="Ya existe un pedido"):
        gestor_pedidos.crear_pedido(ped)


@pytest.mark.integracion
def test_c04_llave_foranea_inexistente_descarta_fila_y_registra(
    tmp_path, gestor_clientes: GestorClientes, gestor_rutas: GestorRutas
) -> None:
    """C-04: Una fila de pedido con FK rota se descarta, se registra en descartados y se respalda en disco."""
    archivo_pedidos = tmp_path / "pedidos_corruptos.csv"
    archivo_pedidos.write_text(
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta\n"
        "PED-99,CLI-NO-EXISTE,Cajas,10,León,Irapuato,2026-10-18,Registrado,RUT-01\n"
        "PED-98,CLI-01,Cajas,10,León,Irapuato,2026-10-18,Registrado,RUT-NO-EXISTE\n",
        encoding="utf-8",
    )
    gestor = GestorPedidos(str(archivo_pedidos), gestor_clientes, gestor_rutas)
    assert gestor.listar_pedidos() == []
    assert "PED-99" in gestor.descartados
    assert "PED-98" in gestor.descartados
    assert isinstance(gestor.descartados[0], RegistroDescarte)
    assert "CLI-NO-EXISTE" in gestor.descartados[0].motivo
    assert os.path.exists(gestor.archivo_descartados_csv)


@pytest.mark.unitaria
def test_c06_eliminar_id_inexistente_retorna_falso(
    gestor_clientes: GestorClientes,
    gestor_rutas: GestorRutas,
    gestor_pedidos: GestorPedidos,
) -> None:
    """C-06: Intentar eliminar un ID que no existe retorna False sin alterar los datos."""
    assert gestor_clientes.eliminar_cliente("CLI-999") is False
    assert gestor_rutas.eliminar_ruta("RUT-999") is False
    assert gestor_pedidos.eliminar_pedido("PED-999") is False
    assert len(gestor_clientes.listar_clientes()) == 1


@pytest.mark.integracion
def test_c07_persistencia_de_la_eliminacion(gestor_clientes: GestorClientes) -> None:
    """C-07: Al eliminar un registro y recargar el gestor desde el CSV, el registro ya no aparece."""
    assert gestor_clientes.eliminar_cliente("CLI-01") is True
    recargado = GestorClientes(gestor_clientes.archivo_csv)
    assert recargado.buscar_cliente("CLI-01") is None


@pytest.mark.unitaria
def test_c08_filtrado_correcto_por_id(
    gestor_clientes: GestorClientes,
    gestor_rutas: GestorRutas,
    gestor_pedidos: GestorPedidos,
) -> None:
    """C-08: Buscar un ID existente retorna el objeto exacto asociado, y uno inexistente retorna None."""
    pedido = Pedido("PED-10", "CLI-01", "Componentes", 20, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01")
    gestor_pedidos.crear_pedido(pedido)
    encontrado = gestor_pedidos.buscar_pedido("PED-10")
    assert encontrado is not None
    assert encontrado.producto == "Componentes"
    assert gestor_pedidos.buscar_pedido("PED-NO") is None
    assert gestor_clientes.buscar_cliente("CLI-NO") is None
    assert gestor_rutas.buscar_ruta("RUT-NO") is None


@pytest.mark.integracion
def test_c09_consulta_elementos_asociados_por_relacion(gestor_pedidos: GestorPedidos) -> None:
    """C-09: Consultar dependencias por cliente o por estado devuelve la lista filtrada correcta."""
    p1 = Pedido("PED-01", "CLI-01", "Prod A", 5, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01")
    p2 = Pedido("PED-02", "CLI-01", "Prod B", 8, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01")
    gestor_pedidos.crear_pedido(p1)
    gestor_pedidos.crear_pedido(p2)
    for estado in ("En Validación", "Aprobado", "En Preparación", "En Ruta"):
        gestor_pedidos.cambiar_estado_pedido("PED-02", estado)

    assert len(gestor_pedidos.listar_pedidos_por_cliente("CLI-01")) == 2
    assert len(gestor_pedidos.listar_pedidos_por_estado("En Ruta")) == 1


@pytest.mark.unitaria
def test_c11_manejo_archivo_csv_solo_con_cabeceras(tmp_path) -> None:
    """C-11: Un archivo CSV que solo contiene cabeceras o filas en blanco se carga como lista vacía."""
    csv_cli = tmp_path / "solo_cabeceras_cli.csv"
    csv_cli.write_text("id_cliente,nombre,ciudad,telefono\n,,,\n", encoding="utf-8")
    csv_rut = tmp_path / "solo_cabeceras_rut.csv"
    csv_rut.write_text("id_ruta,origen,destino,distancia_km,tiempo_estimado,transportista\n,,,,,", encoding="utf-8")
    csv_ped = tmp_path / "solo_cabeceras_ped.csv"
    csv_ped.write_text(
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta\n,,,,,,,,\n",
        encoding="utf-8",
    )
    g_cli = GestorClientes(str(csv_cli))
    g_rut = GestorRutas(str(csv_rut))
    g_ped = GestorPedidos(str(csv_ped), g_cli, g_rut)
    assert g_cli.listar_clientes() == []
    assert g_rut.listar_rutas() == []
    assert g_ped.listar_pedidos() == []


@pytest.mark.aceptacion
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


@pytest.mark.integracion
def test_c23_integridad_referencial_eliminar_cliente_y_ruta(
    tmp_path,
    gestor_clientes: GestorClientes,
    gestor_rutas: GestorRutas,
    gestor_pedidos: GestorPedidos,
) -> None:
    """C-23: Eliminar cliente o ruta con pedidos falla con ErrorIntegridadReferencial; sin pedidos funciona."""
    ped = Pedido("PED-23", "CLI-01", "Caja", 10, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01")
    gestor_pedidos.crear_pedido(ped)

    with pytest.raises(ErrorIntegridadReferencial, match="tiene pedidos asociados"):
        gestor_clientes.eliminar_cliente("CLI-01")

    with pytest.raises(ErrorIntegridadReferencial, match="tiene pedidos asociados"):
        gestor_rutas.eliminar_ruta("RUT-01")

    # Al eliminar primero el pedido, ya es posible eliminar el cliente y la ruta
    assert gestor_pedidos.eliminar_pedido("PED-23") is True
    assert gestor_clientes.eliminar_cliente("CLI-01") is True
    assert gestor_rutas.eliminar_ruta("RUT-01") is True

    # Verificar que si un CSV tiene una fila descartada y una válida, guardar() respalda la descartada
    g_cli2 = GestorClientes(str(tmp_path / "cli2.csv"))
    g_cli2.crear_cliente(Cliente("CLI-OK", "Cliente Válido", "León", "4770001122"))
    csv_mixto = tmp_path / "pedidos_mixto.csv"
    csv_mixto.write_text(
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta\n"
        "PED-OK,CLI-OK,Insumo,5,León,Irapuato,2026-10-18,Registrado,\n"
        "PED-HUERFANO,CLI-BORRADO,Insumo,5,León,Irapuato,2026-10-18,Registrado,\n",
        encoding="utf-8",
    )
    g_ped2 = GestorPedidos(str(csv_mixto), g_cli2)
    assert len(g_ped2.listar_pedidos()) == 1
    assert "PED-HUERFANO" in g_ped2.descartados
    # Incluso si se borra el respaldo manualmente antes de guardar(), guardar() lo recrea
    os.remove(g_ped2.archivo_descartados_csv)
    g_ped2.guardar()
    assert os.path.exists(g_ped2.archivo_descartados_csv)
    respaldo_txt = open(g_ped2.archivo_descartados_csv, encoding="utf-8").read()
    assert "PED-HUERFANO" in respaldo_txt


@pytest.mark.integracion
def test_c25_actualizar_pedido_atomico_fks_y_claves_desconocidas(
    gestor_clientes: GestorClientes,
    gestor_rutas: GestorRutas,
    gestor_pedidos: GestorPedidos,
) -> None:
    """C-25: actualizar_pedido valida FKs, transiciones y claves desconocidas sin mutar estado si falla."""
    ped = Pedido("PED-25", "CLI-01", "Caja", 10, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01")
    gestor_pedidos.crear_pedido(ped)
    csv_original = open(gestor_pedidos.archivo_csv, encoding="utf-8").read()

    # Claves desconocidas en los tres gestores
    with pytest.raises(ValueError, match="Claves desconocidas"):
        gestor_pedidos.actualizar_pedido("PED-25", campo_falso="x")
    with pytest.raises(ValueError, match="Claves desconocidas"):
        gestor_clientes.actualizar_cliente("CLI-01", campo_falso="x")
    with pytest.raises(ValueError, match="Claves desconocidas"):
        gestor_rutas.actualizar_ruta("RUT-01", campo_falso="x")

    # FK de cliente inexistente combinada con transición válida: NO debe mutar el estado en memoria ni CSV
    with pytest.raises(ValueError, match="no está registrado"):
        gestor_pedidos.actualizar_pedido(
            "PED-25", estado="En Validación", id_cliente="CLI-INEXISTENTE"
        )
    assert gestor_pedidos.buscar_pedido("PED-25").estado == "Registrado"
    assert open(gestor_pedidos.archivo_csv, encoding="utf-8").read() == csv_original

    # FK de ruta inexistente
    with pytest.raises(ValueError, match="no está registrada"):
        gestor_pedidos.actualizar_pedido("PED-25", id_ruta="RUT-INEXISTENTE")

    # Transición prohibida en actualizar_pedido
    with pytest.raises(ErrorTransicionEstado):
        gestor_pedidos.actualizar_pedido("PED-25", estado="Entregado")

    # Actualización válida y pedido inexistente
    assert gestor_pedidos.actualizar_pedido("PED-25", cantidad=25, estado="En Validación") is True
    assert gestor_pedidos.buscar_pedido("PED-25").cantidad == 25
    assert gestor_pedidos.buscar_pedido("PED-25").estado == "En Validación"
    assert gestor_pedidos.actualizar_pedido("PED-NO-EXISTE", cantidad=10) is False


@pytest.mark.integracion
def test_c30_crud_completo_gestor_rutas_y_gestor_pedidos(
    gestor_clientes: GestorClientes,
    gestor_rutas: GestorRutas,
    gestor_pedidos: GestorPedidos,
) -> None:
    """C-30: Verifica CRUD completo de GestorRutas, GestorPedidos, GestorClientes y guards de TypeError."""
    # Guards de TypeError
    with pytest.raises(TypeError, match="instancia de Cliente"):
        gestor_clientes.crear_cliente("no_es_cliente")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="instancia de Ruta"):
        gestor_rutas.crear_ruta("no_es_ruta")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="instancia de Pedido"):
        gestor_pedidos.crear_pedido("no_es_pedido")  # type: ignore[arg-type]

    # GestorClientes: listar_clientes_por_ciudad y actualizar_cliente
    gestor_clientes.crear_cliente(Cliente("CLI-02", "Farmacia León", "León", "4779990000"))
    assert len(gestor_clientes.listar_clientes_por_ciudad("Irapuato")) == 1
    assert len(gestor_clientes.listar_clientes_por_ciudad("Leon")) == 1
    assert gestor_clientes.actualizar_cliente("CLI-02", nombre="Farmacia Central") is True
    assert gestor_clientes.buscar_cliente("CLI-02").nombre == "Farmacia Central"
    assert gestor_clientes.actualizar_cliente("CLI-INEXISTENTE", nombre="X") is False

    # GestorRutas: listar_rutas_por_destino y actualizar_ruta
    gestor_rutas.crear_ruta(Ruta("RUT-02", "León", "Celaya", 120.0, 1.7, "Mario"))
    assert len(gestor_rutas.listar_rutas()) == 2
    assert len(gestor_rutas.listar_rutas_por_destino("Celaya")) == 1
    assert gestor_rutas.actualizar_ruta("RUT-02", transportista="Mario Ruiz", distancia_km=122.5) is True
    assert gestor_rutas.buscar_ruta("RUT-02").transportista == "Mario Ruiz"
    assert gestor_rutas.actualizar_ruta("RUT-INEXISTENTE", transportista="X") is False

    # GestorPedidos: cambiar_estado_pedido de ID inexistente
    with pytest.raises(ValueError, match="No existe el pedido"):
        gestor_pedidos.cambiar_estado_pedido("PED-INEXISTENTE", "En Validación")


@pytest.mark.aceptacion
def test_c32_ejecutar_flujo_demostracion_main(tmp_path) -> None:
    """C-32: Ejecuta ejecutar_flujo_demostracion() en carpeta temporal verificando lote y rechazos."""
    reporte = ejecutar_flujo_demostracion(
        directorio_ejemplos=str(tmp_path),
        fecha_actual="2026-10-18",
    )
    assert reporte.leidas == 10
    assert reporte.aceptadas == 2
    assert len(reporte.rechazadas) == 8
    assert (tmp_path / "lote_ejemplo.csv").exists()
    assert (tmp_path / "rechazos_ejemplo.csv").exists()
