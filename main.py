"""Módulo principal de ejecución y generación de archivos de ejemplo para Rutas del Bajío.

Ejecuta el flujo integral de clientes, rutas, pedidos, transiciones de la máquina de estados
y procesamiento de un lote CSV real con filas válidas e inválidas de cada regla (RL-01 a RL-05,
RL-EST, RL-FK, RL-DUP, RL-CAMPO), generando `examples/lote_ejemplo.csv` y
`examples/rechazos_ejemplo.csv`.
"""

import os
import tempfile
from datetime import date, timedelta
from typing import Optional

from gestores import GestorClientes, GestorPedidos, GestorRutas, ReporteLote
from modelos import Cliente, Pedido, Ruta


def ejecutar_flujo_demostracion(
    directorio_ejemplos: Optional[str] = None,
    fecha_actual: Optional[str] = None,
) -> ReporteLote:
    """Ejecuta el flujo demostrativo completo y genera lote_ejemplo.csv y rechazos_ejemplo.csv."""
    fecha_ref_str = (fecha_actual or date.today().isoformat()).strip()
    fecha_ref_dt = date.fromisoformat(fecha_ref_str)
    fecha_futura = (fecha_ref_dt + timedelta(days=180)).isoformat()
    fecha_pasada = (fecha_ref_dt - timedelta(days=10)).isoformat()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    carpeta_ejemplos = directorio_ejemplos or os.path.join(base_dir, "examples")
    os.makedirs(carpeta_ejemplos, exist_ok=True)

    ruta_lote_ejemplo = os.path.join(carpeta_ejemplos, "lote_ejemplo.csv")
    ruta_rechazos_ejemplo = os.path.join(carpeta_ejemplos, "rechazos_ejemplo.csv")

    filas_lote = [
        "id_pedido,id_cliente,producto,cantidad,origen,destino,fecha_pedido,estado,id_ruta,"
        "codigo_lote,fecha_vencimiento,temperatura_c,peso_real,peso_teorico,certificado_calidad",
        # 1. Fila válida en umbral inferior térmico (2.0 °C) y +3.0% peso exacto
        f"PED-L01,CLI-01,Suero Fisiológico,25,León,Irapuato,{fecha_ref_str},Registrado,RUT-01,"
        f"LT-10001-MX,{fecha_futura},2.0,103.0,100.0,OK",
        # 2. Fila válida en umbral superior térmico (8.0 °C) y estado vacío (se limpia a Registrado)
        f"PED-L02,CLI-01,Insulina NPH,40,León,Celaya,{fecha_ref_str},,RUT-02,"
        f"lt-10002-mx,{fecha_futura},8.0,97.0,100.0,ok",
        # 3. Rechazo RL-01: Caducidad en límite exacto (Fecha_Vencimiento == Fecha_Actual)
        f"PED-L03,CLI-01,Lácteo Pasteurizado,10,León,Irapuato,{fecha_ref_str},Registrado,RUT-01,"
        f"LT-10003-MX,{fecha_ref_str},4.0,50.0,50.0,OK",
        # 4. Rechazo RL-02: Formato de código de lote inválido
        f"PED-L04,CLI-01,Reactivo Diagnóstico,15,León,Irapuato,{fecha_ref_str},Registrado,RUT-01,"
        f"LOT-ABC-123,{fecha_futura},5.0,30.0,30.0,OK",
        # 5. Rechazo RL-03: Ruptura de cadena de frío (10.5 °C > 8.0 °C)
        f"PED-L05,CLI-01,Vacuna Triple Viral,12,León,Irapuato,{fecha_ref_str},Registrado,RUT-01,"
        f"LT-10005-MX,{fecha_futura},10.5,20.0,20.0,OK",
        # 6. Rechazo RL-04: Tolerancia de pesaje superada (+4.5% > 3.0%)
        f"PED-L06,CLI-01,Grano Farmacéutico,40,León,Irapuato,{fecha_ref_str},Registrado,RUT-01,"
        f"LT-10006-MX,{fecha_futura},5.0,104.5,100.0,OK",
        # 7. Rechazo RL-05: Certificado de calidad vacío/ausente (tratado como AUSENTE)
        f"PED-L07,CLI-01,Químico Industrial,30,León,Irapuato,{fecha_ref_str},Registrado,RUT-01,"
        f"LT-10007-MX,{fecha_futura},5.0,80.0,80.0,",
        # 8. Rechazo múltiple RL-01;RL-03;RL-05 (caducado + frío roto + certificado PENDIENTE)
        f"PED-L08,CLI-01,Plasma Congelado,18,León,Irapuato,{fecha_ref_str},Registrado,RUT-01,"
        f"LT-10008-MX,{fecha_pasada},1.5,60.0,60.0,PENDIENTE",
        # 9. Rechazo RL-EST: Estado inicial en lote distinto de Registrado
        f"PED-L09,CLI-01,Antibiótico,20,León,Irapuato,{fecha_ref_str},En Ruta,RUT-01,"
        f"LT-10009-MX,{fecha_futura},4.5,50.0,50.0,OK",
        # 10. Rechazo RL-FK: Cliente inexistente
        f"PED-L10,CLI-99,Analgésico,10,León,Irapuato,{fecha_ref_str},Registrado,RUT-01,"
        f"LT-10010-MX,{fecha_futura},4.5,50.0,50.0,OK",
    ]
    with open(ruta_lote_ejemplo, mode="w", encoding="utf-8", newline="") as f_lote:
        f_lote.write("\n".join(filas_lote) + "\n")

    with tempfile.TemporaryDirectory() as tmp_dir:
        ruta_clientes = os.path.join(tmp_dir, "clientes.csv")
        ruta_rutas = os.path.join(tmp_dir, "rutas.csv")
        ruta_pedidos = os.path.join(tmp_dir, "pedidos.csv")

        gestor_clientes = GestorClientes(ruta_clientes)
        gestor_rutas = GestorRutas(ruta_rutas)
        gestor_pedidos = GestorPedidos(ruta_pedidos, gestor_clientes, gestor_rutas)

        gestor_clientes.crear_cliente(
            Cliente("CLI-01", "Comercializadora del Bajío", "Irapuato", "4621234567")
        )
        gestor_rutas.crear_ruta(Ruta("RUT-01", "León", "Irapuato", 68.5, 1.2, "Carlos Mendoza"))
        gestor_rutas.crear_ruta(Ruta("RUT-02", "León", "Celaya", 125.0, 1.8, "Laura Gómez"))

        pedido = Pedido(
            id_pedido="PED-001",
            id_cliente="CLI-01",
            producto="Lote Lácteos Refrigerados",
            cantidad=50,
            origen="León",
            destino="Irapuato",
            fecha_pedido=fecha_ref_str,
            estado="Registrado",
            id_ruta="RUT-01",
        )
        gestor_pedidos.crear_pedido(pedido)

        for estado in ["En Validación", "Aprobado", "En Preparación", "En Ruta", "Entregado"]:
            gestor_pedidos.cambiar_estado_pedido("PED-001", estado)

        reporte = gestor_pedidos.cargar_lote(
            ruta_lote_ejemplo,
            ruta_rechazos=ruta_rechazos_ejemplo,
            fecha_actual=fecha_ref_str,
        )

        print("=== Sistema Logístico Rutas del Bajío ===")
        print(f"Clientes registrados: {len(gestor_clientes.listar_clientes())}")
        print(f"Rutas activas: {len(gestor_rutas.listar_rutas())}")
        print(f"Pedido individual procesado: {gestor_pedidos.buscar_pedido('PED-001')}")
        print(
            f"Lote procesado -> Leídas: {reporte.leidas}, "
            f"Aceptadas: {reporte.aceptadas}, "
            f"Rechazadas: {len(reporte.rechazadas)}, "
            f"Por subestado: {reporte.por_subestado}"
        )
        return reporte


if __name__ == "__main__":
    ejecutar_flujo_demostracion()
