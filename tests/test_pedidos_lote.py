"""Pruebas de máquina de estados y depuración de lotes (Etapa 2: C-01 a C-08 y RL-01 a RL-05)."""

import pytest

from gestores import GestorPedidos
from modelos import ErrorTransicionEstado, Pedido


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
        "PED-E03", "CLI-01", "Vacunas", 100, "León", "Irapuato", "2026-10-18", "En Ruta", "RUT-01"
    )
    gestor_pedidos.crear_pedido(pedido)
    with pytest.raises(ErrorTransicionEstado):
        gestor_pedidos.cambiar_estado_pedido("PED-E03", "Cancelado")


def test_etapa2_c04_a_c08_depuracion_lotes_reglas_rl01_a_rl05(
    tmp_path, gestor_pedidos: GestorPedidos
) -> None:
    """C-04 a C-08 (Etapa 2): Verifica las reglas de rechazo y cuarentena RL-01 a RL-05 en carga por lote."""
    archivo_lote = tmp_path / "lote_insumos.csv"
    archivo_rechazos = tmp_path / "rechazos.csv"

    archivo_lote.write_text(
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta,"
        "codigo_lote,fecha_vencimiento,temperatura_c,peso_real,peso_teorico,certificado_calidad\n"
        # Fila válida
        "PED-L01,CLI-01,Suero,25,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12345-MX,2027-05-01,4.5,100.0,100.0,OK\n"
        # C-04 / RL-01: Caducidad vencida -> Cuarentena
        "PED-L02,CLI-01,Lácteo,10,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12346-MX,2026-10-01,4.0,50.0,50.0,OK\n"
        # C-05 / RL-02: Formato de código de lote inválido (LOT-ABC-123)
        "PED-L03,CLI-01,Reactivo,15,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LOT-ABC-123,2027-05-01,5.0,30.0,30.0,OK\n"
        # C-06 / RL-03: Cadena de frío rota (10.5 °C > 8 °C)
        "PED-L04,CLI-01,Biológico,12,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12348-MX,2027-05-01,10.5,20.0,20.0,OK\n"
        # C-07 / RL-04: Tolerancia de pesaje (+4.5% > 3%)
        "PED-L05,CLI-01,Grano,40,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12349-MX,2027-05-01,5.0,104.5,100.0,OK\n"
        # C-08 / RL-05: Certificado de calidad AUSENTE -> Cuarentena
        "PED-L06,CLI-01,Químico,30,León,Irapuato,2026-10-18,Registrado,RUT-01,"
        "LT-12350-MX,2027-05-01,5.0,80.0,80.0,AUSENTE\n",
        encoding="utf-8",
    )

    reporte = gestor_pedidos.cargar_lote(
        str(archivo_lote), ruta_rechazos=str(archivo_rechazos), fecha_actual="2026-10-18"
    )

    assert reporte.leidas == 6
    assert reporte.aceptadas == 1
    assert reporte.cuarentena == 2
    assert len(reporte.rechazadas) == 5

    reglas_detectadas = [r.regla for r in reporte.rechazadas]
    assert reglas_detectadas == ["RL-01", "RL-02", "RL-03", "RL-04", "RL-05"]
    assert archivo_rechazos.exists()
