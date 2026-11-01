"""Pruebas de máquina de estados, valores límite (RL-01, RL-03, RL-04) y simulación de mutaciones.

========================================================================================
DOCUMENTACIÓN DE VERIFICACIÓN DE MUTACIONES (MUTATION TESTING) SOBRE REGLAS RL:
----------------------------------------------------------------------------------------
1. Mutante M1 en RL-01 (Caducidad):
   - Código original: `if dt_venc <= dt_actual: raise FilaLoteInvalidaError("RL-01", ...)`
   - Mutación inyectada: Cambiar el operador relacional `<=` por `<` (`dt_venc < dt_actual`).
   - Detección: La prueba `test_limite_exacto_rl01_caducidad` con `fecha_vencimiento == "2026-10-18"`
     (igual a `fecha_actual`) FALLA inmediatamente con el mutante M1, matando al mutante.

2. Mutantes M2 y M3 en RL-03 (Red de Frío):
   - Código original: `if temp_val < 2.0 or temp_val > 8.0: raise FilaLoteInvalidaError("RL-03", ...)`
   - Mutación M2: Cambiar `< 2.0` por `<= 2.0`.
   - Mutación M3: Cambiar `> 8.0` por `>= 8.0`.
   - Detección: La prueba `test_limite_exacto_rl03_red_de_frio` evalúa exactamente `2.0 °C` y `8.0 °C`
     como umbrales válidos y `1.99 °C` / `8.01 °C` como rechazos, matando a M2 y M3.

3. Mutante M4 en RL-04 (Tolerancia de Peso del 3%):
   - Código original: `if diferencia_relativa > 0.03: raise FilaLoteInvalidaError("RL-04", ...)`
   - Mutación M4: Cambiar `> 0.03` por `>= 0.03`.
   - Detección: La prueba `test_limite_exacto_rl04_tolerancia_peso_3_por_ciento` evalúa una diferencia
     exacta del 3.0% (`103.0` y `97.0` respecto a `100.0`), la cual debe ser aceptada, y `3.01%`
     (`103.01` y `96.99`), la cual debe rechazarse, matando al mutante M4.
========================================================================================
"""

import pytest

from gestores import FilaLoteInvalidaError, GestorPedidos, validar_insumo_lote
from modelos import ErrorTransicionEstado, Pedido


FILA_LOTE_BASE = {
    "codigo_lote": "LT-12345-MX",
    "fecha_vencimiento": "2027-05-01",
    "temperatura_c": "5.0",
    "peso_real": "100.0",
    "peso_teorico": "100.0",
    "certificado_calidad": "OK",
}


def test_etapa2_c01_transicion_valida_de_estado(gestor_pedidos: GestorPedidos) -> None:
    """C-01 (Etapa 2): Pedido En Validación con cliente y stock OK pasa a Aprobado."""
    pedido = Pedido(
        "PED-E01", "CLI-01", "Vacunas", 100, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01"
    )
    gestor_pedidos.crear_pedido(pedido)
    gestor_pedidos.cambiar_estado_pedido("PED-E01", "En Validación")
    gestor_pedidos.cambiar_estado_pedido("PED-E01", "Aprobado")
    assert gestor_pedidos.buscar_pedido("PED-E01").estado == "Aprobado"


def test_etapa2_c02_bloqueo_transicion_invalida(gestor_pedidos: GestorPedidos) -> None:
    """C-02 (Etapa 2): Intento de pasar de Registrado directamente a En Ruta es rechazado."""
    pedido = Pedido(
        "PED-E02", "CLI-01", "Vacunas", 100, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01"
    )
    gestor_pedidos.crear_pedido(pedido)
    with pytest.raises(ErrorTransicionEstado):
        gestor_pedidos.cambiar_estado_pedido("PED-E02", "En Ruta")
    assert gestor_pedidos.buscar_pedido("PED-E02").estado == "Registrado"


def test_etapa2_c03_cancelacion_extemporanea_en_ruta(gestor_pedidos: GestorPedidos) -> None:
    """C-03 (Etapa 2): Intento de cancelar un pedido que ya está En Ruta es bloqueado."""
    pedido = Pedido(
        "PED-E03", "CLI-01", "Vacunas", 100, "León", "Irapuato", "2026-10-18", "Registrado", "RUT-01"
    )
    gestor_pedidos.crear_pedido(pedido)
    for estado in ("En Validación", "Aprobado", "En Preparación", "En Ruta"):
        gestor_pedidos.cambiar_estado_pedido("PED-E03", estado)
    with pytest.raises(ErrorTransicionEstado):
        gestor_pedidos.cambiar_estado_pedido("PED-E03", "Cancelado")


@pytest.mark.parametrize(
    "fecha_vencimiento,debe_rechazar",
    [
        pytest.param("2026-10-17", True, id="vencido_ayer_rechaza"),
        pytest.param("2026-10-18", True, id="limite_exacto_igual_a_fecha_actual_rechaza"),
        pytest.param("2026-10-19", False, id="limite_un_dia_despues_acepta"),
    ],
)
def test_limite_exacto_rl01_caducidad(fecha_vencimiento: str, debe_rechazar: bool) -> None:
    """Prueba de valor límite para RL-01 (Fecha_Vencimiento <= Fecha_Actual).

    Verifica el límite exacto donde Fecha_Vencimiento == Fecha_Actual (2026-10-18).
    Mata al mutante M1 si se reemplaza `<=` por `<`.
    """
    fila = {**FILA_LOTE_BASE, "fecha_vencimiento": fecha_vencimiento}
    if debe_rechazar:
        with pytest.raises(FilaLoteInvalidaError) as exc_info:
            validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert exc_info.value.regla == "RL-01"
    else:
        resultado = validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert resultado["fecha_vencimiento"] == fecha_vencimiento


@pytest.mark.parametrize(
    "temperatura_c,debe_rechazar",
    [
        pytest.param("1.99", True, id="bajo_umbral_inferior_1_99C_rechaza"),
        pytest.param("2.0", False, id="umbral_exacto_inferior_2_0C_acepta"),
        pytest.param("8.0", False, id="umbral_exacto_superior_8_0C_acepta"),
        pytest.param("8.01", True, id="sobre_umbral_superior_8_01C_rechaza"),
    ],
)
def test_limite_exacto_rl03_red_de_frio(temperatura_c: str, debe_rechazar: bool) -> None:
    """Prueba de valores límite para RL-03 (umbrales térmicos exactos de 2°C y 8°C).

    Mata a los mutantes M2 (`<= 2.0`) y M3 (`>= 8.0`).
    """
    fila = {**FILA_LOTE_BASE, "temperatura_c": temperatura_c}
    if debe_rechazar:
        with pytest.raises(FilaLoteInvalidaError) as exc_info:
            validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert exc_info.value.regla == "RL-03"
    else:
        resultado = validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert resultado["temperatura_c"] == temperatura_c


@pytest.mark.parametrize(
    "peso_real,peso_teorico,debe_rechazar",
    [
        pytest.param("103.0", "100.0", False, id="diferencia_exacta_mas_3_por_ciento_acepta"),
        pytest.param("97.0", "100.0", False, id="diferencia_exacta_menos_3_por_ciento_acepta"),
        pytest.param("103.01", "100.0", True, id="diferencia_mas_3_01_por_ciento_rechaza"),
        pytest.param("96.99", "100.0", True, id="diferencia_menos_3_01_por_ciento_rechaza"),
    ],
)
def test_limite_exacto_rl04_tolerancia_peso_3_por_ciento(
    peso_real: str, peso_teorico: str, debe_rechazar: bool
) -> None:
    """Prueba de valores límite para RL-04 (diferencia exacta del 3% entre peso real y teórico).

    Mata al mutante M4 si se altera `> 0.03` por `>= 0.03`.
    """
    fila = {**FILA_LOTE_BASE, "peso_real": peso_real, "peso_teorico": peso_teorico}
    if debe_rechazar:
        with pytest.raises(FilaLoteInvalidaError) as exc_info:
            validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert exc_info.value.regla == "RL-04"
    else:
        resultado = validar_insumo_lote(fila, fecha_actual="2026-10-18")
        assert resultado["peso_real"] == peso_real


def test_etapa2_c04_a_c08_depuracion_lotes_reglas_rl01_a_rl05(
    tmp_path, gestor_pedidos: GestorPedidos
) -> None:
    """C-04 a C-08 (Etapa 2): Verifica las reglas de rechazo RL-01 a RL-05 en carga por lote."""
    archivo_lote = tmp_path / "lote_insumos.csv"
    archivo_rechazos = tmp_path / "rechazos.csv"

    archivo_lote.write_text(
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta,"
        "codigo_lote,fecha_vencimiento,temperatura_c,peso_real,peso_teorico,certificado_calidad\n"
        # Fila válida (en umbrales exactos: 2.0 °C y +3% de peso)
        "PED-L01,CLI-01,Suero,25,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12345-MX,2027-05-01,2.0,103.0,100.0,OK\n"
        # C-04 / RL-01: Caducidad en límite exacto (2026-10-18 <= 2026-10-18)
        "PED-L02,CLI-01,Lácteo,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12346-MX,2026-10-18,4.0,50.0,50.0,OK\n"
        # C-05 / RL-02: Formato de código de lote inválido (LOT-ABC-123)
        "PED-L03,CLI-01,Reactivo,15,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LOT-ABC-123,2027-05-01,5.0,30.0,30.0,OK\n"
        # C-06 / RL-03: Cadena de frío rota (10.5 °C > 8 °C)
        "PED-L04,CLI-01,Biológico,12,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12348-MX,2027-05-01,10.5,20.0,20.0,OK\n"
        # C-07 / RL-04: Tolerancia de pesaje (+4.5% > 3%)
        "PED-L05,CLI-01,Grano,40,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12349-MX,2027-05-01,5.0,104.5,100.0,OK\n"
        # C-08 / RL-05: Certificado de calidad AUSENTE
        "PED-L06,CLI-01,Químico,30,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12350-MX,2027-05-01,5.0,80.0,80.0,AUSENTE\n",
        encoding="utf-8",
    )

    reporte = gestor_pedidos.cargar_lote(
        str(archivo_lote), ruta_rechazos=str(archivo_rechazos), fecha_actual="2026-10-18"
    )

    assert reporte.leidas == 6
    assert reporte.aceptadas == 1
    assert len(reporte.rechazadas) == 5

    reglas_detectadas = [r.regla for r in reporte.rechazadas]
    assert reglas_detectadas == ["RL-01", "RL-02", "RL-03", "RL-04", "RL-05"]
    assert archivo_rechazos.exists()
