"""Script de inyección manual de mutaciones para auditar la suite de pytest.

Ejecuta una batería de 23 mutantes sobre `gestores.py` y `modelos.py` sin dependencias
externas: por cada mutante reemplaza la línea objetivo, corre `pytest -x -q --tb=no`,
restaura SIEMPRE el archivo original mediante un bloque `try / finally` e imprime la
tabla auditable de resultados con fecha y hora de ejecución.
"""

from dataclasses import dataclass
from datetime import datetime
import os
import re
import subprocess
import sys
from typing import List, Tuple


@dataclass(frozen=True)
class Mutante:
    """Definición de un mutante por reemplazo exacto de línea."""

    id_mutante: str
    archivo: str
    descripcion: str
    original: str
    mutado: str


MUTANTES: Tuple[Mutante, ...] = (
    Mutante(
        "M-01",
        "gestores.py",
        "RL-01: dt_venc <= dt_actual -> dt_venc < dt_actual",
        "            if dt_venc <= dt_actual:",
        "            if dt_venc < dt_actual:",
    ),
    Mutante(
        "M-02",
        "gestores.py",
        "RL-03: temp_val < 2.0 -> temp_val <= 2.0",
        "            if temp_val < 2.0 or temp_val > 8.0:",
        "            if temp_val <= 2.0 or temp_val > 8.0:",
    ),
    Mutante(
        "M-03",
        "gestores.py",
        "RL-03: temp_val > 8.0 -> temp_val >= 8.0",
        "            if temp_val < 2.0 or temp_val > 8.0:",
        "            if temp_val < 2.0 or temp_val >= 8.0:",
    ),
    Mutante(
        "M-04",
        "gestores.py",
        "RL-04: diferencia_relativa > 0.03 -> >= 0.03",
        "                if diferencia_relativa > 0.03:",
        "                if diferencia_relativa >= 0.03:",
    ),
    Mutante(
        "M-05",
        "gestores.py",
        "RL-04: p_teo <= 0 -> p_teo < 0",
        "            if p_teo <= 0:",
        "            if p_teo < 0:",
    ),
    Mutante(
        "M-06",
        "gestores.py",
        'RL-05: sin verificacion de estado "PENDIENTE"',
        '    if certificado == "PENDIENTE" or certificado == "AUSENTE":',
        '    if certificado == "AUSENTE":',
    ),
    Mutante(
        "M-07",
        "gestores.py",
        "Lote: omite chequeo de duplicado dentro del mismo lote",
        "                    if id_ped in ids_vistos or self.buscar_pedido(id_ped) is not None:",
        "                    if self.buscar_pedido(id_ped) is not None:",
    ),
    Mutante(
        "M-08",
        "gestores.py",
        "Guard TypeError desactivado en crear_cliente",
        "        if not isinstance(cliente, Cliente):",
        "        if False:",
    ),
    Mutante(
        "M-09",
        "gestores.py",
        "Guard TypeError desactivado en crear_ruta",
        "        if not isinstance(ruta, Ruta):",
        "        if False:",
    ),
    Mutante(
        "M-10",
        "gestores.py",
        "Guard TypeError desactivado en crear_pedido",
        "        if not isinstance(pedido, Pedido):",
        "        if False:",
    ),
    Mutante(
        "M-11",
        "gestores.py",
        "RL-01: operador logico and -> or en guardia de fecha",
        '    if fecha_vencimiento != "" and fecha_vencimiento is not None:',
        '    if fecha_vencimiento != "" or fecha_vencimiento is not None:',
    ),
    Mutante(
        "M-12",
        "gestores.py",
        "RL-02: operador logico and -> or en regex de lote",
        "    if codigo_lote and not REGEX_CODIGO_LOTE.match(codigo_lote):",
        "    if codigo_lote or not REGEX_CODIGO_LOTE.match(codigo_lote):",
    ),
    Mutante(
        "M-13",
        "gestores.py",
        "RL-03: operador logico or -> and en rango termico",
        "            if temp_val < 2.0 or temp_val > 8.0:",
        "            if temp_val < 2.0 and temp_val > 8.0:",
    ),
    Mutante(
        "M-14",
        "gestores.py",
        "RL-04: operador logico and -> or en guardia de peso",
        '        and str(peso_real).strip() != ""',
        '        or str(peso_real).strip() != ""',
    ),
    Mutante(
        "M-15",
        "gestores.py",
        "RL-05: operador logico or -> and en certificado",
        '    if certificado == "PENDIENTE" or certificado == "AUSENTE":',
        '    if certificado == "PENDIENTE" and certificado == "AUSENTE":',
    ),
    Mutante(
        "M-16",
        "modelos.py",
        "Transiciones: Registrado permite salto directo a En Ruta",
        '    "Registrado": {"En Validación", "Cancelado"},',
        '    "Registrado": {"En Validación", "Cancelado", "En Ruta"},',
    ),
    Mutante(
        "M-17",
        "modelos.py",
        "Transiciones: En Validación permite salto a En Preparación",
        '    "En Validación": {"Aprobado", "Cancelado"},',
        '    "En Validación": {"Aprobado", "Cancelado", "En Preparación"},',
    ),
    Mutante(
        "M-18",
        "modelos.py",
        "Transiciones: En Preparación permite pasar a Cancelado",
        '    "En Preparación": {"En Ruta"},',
        '    "En Preparación": {"En Ruta", "Cancelado"},',
    ),
    Mutante(
        "M-19",
        "modelos.py",
        "Transiciones: En Ruta permite pasar a Cancelado",
        '    "En Ruta": {"Entregado"},',
        '    "En Ruta": {"Entregado", "Cancelado"},',
    ),
    Mutante(
        "M-20",
        "modelos.py",
        "Transiciones: Entregado permite retroceder a En Ruta",
        '    "Entregado": set(),',
        '    "Entregado": {"En Ruta"},',
    ),
    Mutante(
        "M-21",
        "modelos.py",
        "Transiciones: Cancelado permite reabrir a Registrado",
        '    "Cancelado": set(),',
        '    "Cancelado": {"Registrado"},',
    ),
    Mutante(
        "M-22",
        "gestores.py",
        "FK: desactiva ErrorIntegridadReferencial en eliminar_cliente",
        "            if gestor_ped.listar_pedidos_por_cliente(id_cliente):",
        "            if False:",
    ),
    Mutante(
        "M-23",
        "gestores.py",
        "FK: desactiva ErrorIntegridadReferencial en eliminar_ruta",
        "            if any(p.id_ruta == id_ruta for p in gestor_ped.pedidos):",
        "            if False:",
    ),
)


def _extraer_prueba_fallida(salida: str) -> str:
    """Extrae el identificador completo de la primera prueba que falló en pytest."""
    for linea in salida.splitlines():
        if linea.startswith("FAILED "):
            resto = linea[len("FAILED ") :].strip()
            return resto.split(" - ")[0].strip()
    coincidencia = re.search(r"(tests/[^\s]+::test_[^\n]+)", salida)
    if coincidencia:
        return coincidencia.group(1).split(" - ")[0].strip()
    return "Fallo detectado"


def ejecutar_mutaciones() -> int:
    """Ejecuta todos los mutantes definidos e imprime el reporte tabular."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"=== Ejecución de Pruebas de Mutación Manual — Fecha: {ahora} ===")
    print(
        f"{'ID':<5} | {'Archivo':<12} | {'Línea':<5} | {'Mutación':<56} | {'Resultado':<9} | {'Prueba que falló'}"
    )
    print("-" * 145)

    eliminados = 0
    sobrevivientes: List[str] = []

    for m in MUTANTES:
        ruta_archivo = os.path.join(raiz, m.archivo)
        with open(ruta_archivo, mode="r", encoding="utf-8") as f_in:
            contenido_original = f_in.read()

        lineas = contenido_original.splitlines()
        num_linea = -1
        for idx, texto_linea in enumerate(lineas, start=1):
            if texto_linea == m.original:
                num_linea = idx
                break

        if num_linea == -1:
            raise RuntimeError(
                f"No se encontró la línea original del mutante {m.id_mutante} en {m.archivo}: {m.original!r}"
            )

        contenido_mutado = contenido_original.replace(m.original, m.mutado, 1)
        try:
            with open(ruta_archivo, mode="w", encoding="utf-8", newline="\n") as f_out:
                f_out.write(contenido_mutado)

            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests/test_modelos.py",
                    "tests/test_pedidos_lote.py",
                    "tests/test_gestores.py",
                    "-x",
                    "-q",
                    "--tb=no",
                    "-o",
                    "addopts=-ra",
                ],
                cwd=raiz,
                capture_output=True,
                text=True,
                check=False,
            )
            salida = (proc.stdout or "") + "\n" + (proc.stderr or "")
            if proc.returncode != 0:
                resultado = "Killed"
                eliminados += 1
                prueba_fallida = _extraer_prueba_fallida(salida)
            else:
                resultado = "Survived"
                sobrevivientes.append(m.id_mutante)
                prueba_fallida = "NINGUNA (Sobrevivió)"

            print(
                f"{m.id_mutante:<5} | {m.archivo:<12} | {num_linea:<5} | "
                f"{m.descripcion:<56} | {resultado:<9} | {prueba_fallida}"
            )
        finally:
            with open(ruta_archivo, mode="w", encoding="utf-8", newline="\n") as f_restore:
                f_restore.write(contenido_original)

    total = len(MUTANTES)
    print("-" * 145)
    print(
        f"Resumen final: {eliminados} de {total} mutantes eliminados "
        f"({(eliminados / total) * 100:.1f}% Mutation Score)."
    )
    return 0 if not sobrevivientes else 1


if __name__ == "__main__":
    raise SystemExit(ejecutar_mutaciones())
