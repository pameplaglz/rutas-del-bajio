"""Pruebas dedicadas por criterio para máquina de estados y depuración de lotes (C-13 a C-20, C-26 a C-29)."""

import csv

import pytest

from errores import (
    SUBESTADO_CUARENTENA,
    SUBESTADO_DATOS_INVALIDOS,
    SUBESTADO_DESCARTE,
    SUBESTADO_ESTADO_INVALIDO,
    SUBESTADO_FORMATO_INVALIDO,
    SUBESTADO_PESAJE,
    SUBESTADO_RED_FRIO,
    ErrorArchivoLote,
    ErrorTransicionEstado,
    FilaLoteInvalidaError,
)
from gestores import GestorClientes, GestorPedidos, GestorRutas, validar_insumo_lote
from modelos import Pedido


FILA_LOTE_BASE = {
    "codigo_lote": "LT-12345-MX",
    "fecha_vencimiento": "2027-05-01",
    "temperatura_c": "5.0",
    "peso_real": "100.0",
    "peso_teorico": "100.0",
    "certificado_calidad": "OK",
}


@pytest.mark.unitaria
def test_c13_transicion_valida_de_estado(gestor_pedidos: GestorPedidos) -> None:
    """C-13: Pedido En Validación con cliente y stock OK pasa a estado Aprobado."""
    pedido = Pedido(
        "PED-C13", "CLI-01", "Vacunas", 100, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01"
    )
    gestor_pedidos.crear_pedido(pedido)
    gestor_pedidos.cambiar_estado_pedido("PED-C13", "En Validación")
    gestor_pedidos.cambiar_estado_pedido("PED-C13", "Aprobado")
    assert gestor_pedidos.buscar_pedido("PED-C13").estado == "Aprobado"


@pytest.mark.unitaria
def test_c14_bloqueo_transicion_invalida(gestor_pedidos: GestorPedidos) -> None:
    """C-14: Intento de pasar de Registrado directamente a En Ruta es bloqueado con ErrorTransicionEstado."""
    pedido = Pedido(
        "PED-C14", "CLI-01", "Vacunas", 100, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01"
    )
    gestor_pedidos.crear_pedido(pedido)
    with pytest.raises(ErrorTransicionEstado):
        gestor_pedidos.cambiar_estado_pedido("PED-C14", "En Ruta")
    assert gestor_pedidos.buscar_pedido("PED-C14").estado == "Registrado"


@pytest.mark.unitaria
def test_c15_cancelacion_extemporanea_en_ruta(gestor_pedidos: GestorPedidos) -> None:
    """C-15: Intento de cancelar un pedido en estado En Ruta es bloqueado por el sistema."""
    pedido = Pedido(
        "PED-C15", "CLI-01", "Vacunas", 100, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01"
    )
    gestor_pedidos.crear_pedido(pedido)
    for estado in ("En Validación", "Aprobado", "En Preparación", "En Ruta"):
        gestor_pedidos.cambiar_estado_pedido("PED-C15", estado)
    with pytest.raises(ErrorTransicionEstado):
        gestor_pedidos.cambiar_estado_pedido("PED-C15", "Cancelado")
    assert gestor_pedidos.buscar_pedido("PED-C15").estado == "En Ruta"


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "fecha_vencimiento,debe_rechazar",
    [
        pytest.param("2026-10-17", True, id="vencido_ayer_rechaza"),
        pytest.param("2026-10-18", True, id="limite_exacto_igual_a_fecha_actual_rechaza"),
        pytest.param("2026-10-19", False, id="limite_un_dia_despues_acepta"),
        pytest.param("fecha-invalida", True, id="formato_fecha_invalido_rechaza"),
        pytest.param("", False, id="sin_fecha_vencimiento_opcional_no_dispara_rl01"),
    ],
)
def test_c16_depuracion_lote_caducado_rl01(fecha_vencimiento: str, debe_rechazar: bool) -> None:
    """C-16: Evalúa la regla RL-01 (Caducidad Vencida: Fecha_Vencimiento <= Fecha_Actual) con valores límite."""
    fila = {**FILA_LOTE_BASE, "fecha_vencimiento": fecha_vencimiento}
    if debe_rechazar:
        with pytest.raises(FilaLoteInvalidaError) as exc_info:
            validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert exc_info.value.regla == "RL-01"
        assert exc_info.value.subestado_rechazo == SUBESTADO_CUARENTENA
    else:
        resultado = validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert resultado["fecha_vencimiento"] == fecha_vencimiento


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "codigo_lote,debe_rechazar",
    [
        pytest.param("LOT-ABC-123", True, id="formato_erroneo_lot_abc_123"),
        pytest.param("LT-123-MX", True, id="menos_de_5_digitos"),
        pytest.param("LT-12345-M", True, id="una_sola_letra_final"),
        pytest.param("LT-12345-MX", False, id="formato_valido_estandar"),
        pytest.param("  lt-99999-ab ", False, id="formato_minusculas_se_limpia_a_mayusculas"),
        pytest.param("", False, id="sin_codigo_lote_opcional_no_dispara_rl02"),
    ],
)
def test_c17_validacion_codigo_lote_rl02(codigo_lote: str, debe_rechazar: bool) -> None:
    """C-17: Evalúa la regla RL-02 (Formato de código de lote ^LT-[0-9]{5}-[A-Z]{2}$)."""
    fila = {**FILA_LOTE_BASE, "codigo_lote": codigo_lote}
    if debe_rechazar:
        with pytest.raises(FilaLoteInvalidaError) as exc_info:
            validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert exc_info.value.regla == "RL-02"
        assert exc_info.value.subestado_rechazo == SUBESTADO_FORMATO_INVALIDO
    else:
        resultado = validar_insumo_lote(fila, fecha_actual="2026-10-18")
        if codigo_lote.strip():
            assert resultado["codigo_lote"] == codigo_lote.strip().upper()


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "temperatura_c,debe_rechazar",
    [
        pytest.param("1.99", True, id="bajo_umbral_inferior_1_99C_rechaza"),
        pytest.param("2.0", False, id="umbral_exacto_inferior_2_0C_acepta"),
        pytest.param("8.0", False, id="umbral_exacto_superior_8_0C_acepta"),
        pytest.param("8.01", True, id="sobre_umbral_superior_8_01C_rechaza"),
        pytest.param("10.5", True, id="ruptura_cadena_frio_10_5C_rechaza"),
        pytest.param("no-num", True, id="temperatura_no_numerica_rechaza"),
    ],
)
def test_c18_alerta_cadena_frio_rl03(temperatura_c: str, debe_rechazar: bool) -> None:
    """C-18: Evalúa la regla RL-03 (Temperatura de Red de Frío en rango [2.0 °C, 8.0 °C]) con valores límite."""
    fila = {**FILA_LOTE_BASE, "temperatura_c": temperatura_c}
    if debe_rechazar:
        with pytest.raises(FilaLoteInvalidaError) as exc_info:
            validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert exc_info.value.regla == "RL-03"
        assert exc_info.value.subestado_rechazo == SUBESTADO_RED_FRIO
    else:
        resultado = validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert resultado["temperatura_c"] == temperatura_c


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "peso_real,peso_teorico,debe_rechazar",
    [
        pytest.param("103.0", "100.0", False, id="diferencia_exacta_mas_3_por_ciento_acepta"),
        pytest.param("97.0", "100.0", False, id="diferencia_exacta_menos_3_por_ciento_acepta"),
        pytest.param("103.01", "100.0", True, id="diferencia_mas_3_01_por_ciento_rechaza"),
        pytest.param("96.99", "100.0", True, id="diferencia_menos_3_01_por_ciento_rechaza"),
        pytest.param("104.5", "100.0", True, id="diferencia_mas_4_5_por_ciento_rechaza"),
        pytest.param("100.0", "0.0", True, id="peso_teorico_cero_rechaza"),
        pytest.param("100.0", "-10.0", True, id="peso_teorico_negativo_rechaza"),
        pytest.param("abc", "100.0", True, id="peso_no_numerico_rechaza"),
        pytest.param("", "100.0", False, id="sin_peso_real_opcional_no_dispara_rl04"),
    ],
)
def test_c19_tolerancia_pesaje_rl04(
    peso_real: str, peso_teorico: str, debe_rechazar: bool
) -> None:
    """C-19: Evalúa la regla RL-04 (Tolerancia de pesaje del 3%) con valores límite exactos."""
    fila = {**FILA_LOTE_BASE, "peso_real": peso_real, "peso_teorico": peso_teorico}
    if debe_rechazar:
        with pytest.raises(FilaLoteInvalidaError) as exc_info:
            validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert exc_info.value.regla == "RL-04"
        assert exc_info.value.subestado_rechazo == SUBESTADO_PESAJE
    else:
        resultado = validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert resultado["peso_real"] == peso_real


@pytest.mark.unitaria
@pytest.mark.parametrize(
    "certificado,debe_rechazar",
    [
        pytest.param("OK", False, id="certificado_ok_acepta"),
        pytest.param("  ok ", False, id="certificado_ok_minusculas_se_limpia"),
        pytest.param("AUSENTE", True, id="certificado_ausente_rechaza"),
        pytest.param("PENDIENTE", True, id="certificado_pendiente_rechaza"),
        pytest.param("", True, id="certificado_vacio_se_trata_como_ausente"),
    ],
)
def test_c20_cuarentena_falta_certificado_rl05(certificado: str, debe_rechazar: bool) -> None:
    """C-20: Evalúa la regla RL-05 (Certificado de calidad faltante, PENDIENTE o AUSENTE)."""
    fila = {**FILA_LOTE_BASE, "certificado_calidad": certificado}
    if debe_rechazar:
        with pytest.raises(FilaLoteInvalidaError) as exc_info:
            validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert exc_info.value.regla == "RL-05"
        assert exc_info.value.subestado_rechazo == SUBESTADO_CUARENTENA
    else:
        resultado = validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert resultado["certificado_calidad"] == "OK"


@pytest.mark.integracion
def test_c26_lote_multiples_reglas_violadas_reporta_todas(
    tmp_path, gestor_pedidos: GestorPedidos
) -> None:
    """C-26: Una fila que viola RL-01..RL-05 reporta la primera en regla y todas en reglas en orden numérico."""
    archivo_lote = tmp_path / "lote_multiregla.csv"
    archivo_rechazos = tmp_path / "rechazos_multiregla.csv"
    archivo_lote.write_text(
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta,"
        "codigo_lote,fecha_vencimiento,temperatura_c,peso_real,peso_teorico,certificado_calidad\n"
        "PED-M01,CLI-01,Plasma,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "CODIGO-MALO,2026-10-01,12.0,120.0,100.0,PENDIENTE\n",
        encoding="utf-8",
    )
    reporte = gestor_pedidos.cargar_lote(
        str(archivo_lote), ruta_rechazos=str(archivo_rechazos), fecha_actual="2026-10-18"
    )
    assert len(reporte.rechazadas) == 1
    rechazo = reporte.rechazadas[0]
    assert rechazo.regla == "RL-01"
    assert rechazo.reglas == "RL-01;RL-02;RL-03;RL-04;RL-05"
    assert rechazo.subestado_rechazo == SUBESTADO_CUARENTENA


@pytest.mark.integracion
def test_c27_lote_certificado_ausente_o_vacio_dispara_rl05(
    tmp_path, gestor_pedidos: GestorPedidos
) -> None:
    """C-27: Si la columna certificado_calidad no existe en el CSV o viene vacía, se rechaza con RL-05."""
    archivo_sin_col = tmp_path / "lote_sin_col_cert.csv"
    archivo_sin_col.write_text(
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta,"
        "codigo_lote,fecha_vencimiento,temperatura_c,peso_real,peso_teorico\n"
        "PED-SC01,CLI-01,Suero,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12345-MX,2027-05-01,4.0,100.0,100.0\n",
        encoding="utf-8",
    )
    reporte = gestor_pedidos.cargar_lote(str(archivo_sin_col), fecha_actual="2026-10-18")
    assert reporte.aceptadas == 0
    assert len(reporte.rechazadas) == 1
    assert reporte.rechazadas[0].regla == "RL-05"


@pytest.mark.integracion
def test_c28_lote_errores_de_archivo_y_encabezados(
    tmp_path, gestor_pedidos: GestorPedidos
) -> None:
    """C-28: Archivo inexistente, vacío, con encabezados en mayúscula o incompletos lanza ErrorArchivoLote."""
    with pytest.raises(ErrorArchivoLote, match="no existe"):
        gestor_pedidos.cargar_lote(str(tmp_path / "inexistente.csv"))

    vacio = tmp_path / "vacio.csv"
    vacio.write_text("", encoding="utf-8")
    with pytest.raises(ErrorArchivoLote, match="no contiene encabezados"):
        gestor_pedidos.cargar_lote(str(vacio))

    mayus = tmp_path / "mayus.csv"
    mayus.write_text("Id_Pedido,id_cliente,cantidad\n", encoding="utf-8")
    with pytest.raises(ErrorArchivoLote, match="minúsculas exactas"):
        gestor_pedidos.cargar_lote(str(mayus))

    incompleto = tmp_path / "incompleto.csv"
    incompleto.write_text("id_pedido,producto\nPED-01,Caja\n", encoding="utf-8")
    with pytest.raises(ErrorArchivoLote, match="Columnas obligatorias faltantes"):
        gestor_pedidos.cargar_lote(str(incompleto))

    # También en cargar() de los tres gestores cuando los encabezados no coinciden con CAMPOS_CSV
    cli_mal = tmp_path / "cli_mal.csv"
    cli_mal.write_text("id_cliente,Nombre,Ciudad,telefono\n", encoding="utf-8")
    with pytest.raises(ErrorArchivoLote, match="Encabezados inválidos"):
        GestorClientes(str(cli_mal))

    rut_mal = tmp_path / "rut_mal.csv"
    rut_mal.write_text("id_ruta,origen,destino\n", encoding="utf-8")
    with pytest.raises(ErrorArchivoLote, match="Encabezados inválidos"):
        GestorRutas(str(rut_mal))

    ped_mal = tmp_path / "ped_mal.csv"
    ped_mal.write_text("id_pedido,id_cliente,Producto\n", encoding="utf-8")
    with pytest.raises(ErrorArchivoLote, match="Encabezados inválidos"):
        GestorPedidos(str(ped_mal))


@pytest.mark.aceptacion
def test_c29_lote_reglas_estructurales_id_campo_est_dup_fk(
    tmp_path, gestor_pedidos: GestorPedidos
) -> None:
    """C-29: Verifica RL-ID, RL-CAMPO, RL-EST, RL-DUP, RL-FK, rechazos.csv campo por campo y por_subestado."""
    # Pre-registrar un pedido en el gestor para probar RL-DUP contra el gestor además de dentro del lote
    gestor_pedidos.crear_pedido(
        Pedido("PED-EXISTENTE", "CLI-01", "Base", 5, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01")
    )

    archivo_lote = tmp_path / "lote_estructural.csv"
    archivo_rechazos = tmp_path / "rechazos_estructural.csv"
    archivo_lote.write_text(
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta,"
        "codigo_lote,fecha_vencimiento,temperatura_c,peso_real,peso_teorico,certificado_calidad\n"
        # Línea 2: Válida
        "PED-OK1,CLI-01,Suero,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-11111-MX,2027-05-01,4.0,100.0,100.0,OK\n"
        # Línea 3: RL-DUP dentro del mismo lote (repite PED-OK1)
        "PED-OK1,CLI-01,Suero,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-11112-MX,2027-05-01,4.0,100.0,100.0,OK\n"
        # Línea 4: RL-DUP contra pedido ya existente en el gestor (PED-EXISTENTE)
        "PED-EXISTENTE,CLI-01,Suero,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-11113-MX,2027-05-01,4.0,100.0,100.0,OK\n"
        # Línea 5: RL-ID (id_pedido vacío)
        ",CLI-01,Suero,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-11114-MX,2027-05-01,4.0,100.0,100.0,OK\n"
        # Línea 6: RL-CAMPO (producto vacío, sin default silencioso)
        "PED-SIN-PROD,CLI-01,,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-11115-MX,2027-05-01,4.0,100.0,100.0,OK\n"
        # Línea 7: RL-EST (estado inicial distinto de Registrado)
        "PED-MAL-EST,CLI-01,Suero,10,León,Irapuato,2026-10-18,Aprobado,RUT-01,"
        "LT-11116-MX,2027-05-01,4.0,100.0,100.0,OK\n"
        # Línea 8: RL-FK (cliente inexistente)
        "PED-MAL-CLI,CLI-999,Suero,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-11117-MX,2027-05-01,4.0,100.0,100.0,OK\n"
        # Línea 9: RL-FK (ruta inexistente)
        "PED-MAL-RUT,CLI-01,Suero,10,León,Irapuato,2026-10-18,Registrado,RUT-999,"
        "LT-11118-MX,2027-05-01,4.0,100.0,100.0,OK\n"
        # Línea 10: RL-CAMPO por cantidad inválida en Pedido
        "PED-MAL-CANT,CLI-01,Suero,-5,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-11119-MX,2027-05-01,4.0,100.0,100.0,OK\n",
        encoding="utf-8",
    )

    reporte = gestor_pedidos.cargar_lote(
        str(archivo_lote), ruta_rechazos=str(archivo_rechazos), fecha_actual="2026-10-18"
    )

    assert reporte.leidas == 9
    assert reporte.aceptadas == 1
    assert len(reporte.rechazadas) == 8
    assert reporte.leidas == reporte.aceptadas + len(reporte.rechazadas)

    assert reporte.por_subestado == {
        SUBESTADO_DESCARTE: 2,
        SUBESTADO_DATOS_INVALIDOS: 5,
        SUBESTADO_ESTADO_INVALIDO: 1,
    }

    with open(archivo_rechazos, mode="r", encoding="utf-8", newline="") as f_csv:
        filas_csv = list(csv.DictReader(f_csv))

    assert len(filas_csv) == 8
    assert [f["regla"] for f in filas_csv] == [
        "RL-DUP",
        "RL-DUP",
        "RL-ID",
        "RL-CAMPO",
        "RL-EST",
        "RL-FK",
        "RL-FK",
        "RL-CAMPO",
    ]
    assert filas_csv[0]["linea"] == "3"
    assert filas_csv[0]["identificador"] == "PED-OK1"
    assert filas_csv[0]["reglas"] == "RL-DUP"
    assert filas_csv[0]["subestado_rechazo"] == SUBESTADO_DESCARTE
