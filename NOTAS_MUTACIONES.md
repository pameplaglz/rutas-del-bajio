# Notas de Verificación de Mutaciones (Mutation Testing) — Rutas del Bajío

Este documento registra las pruebas de mutación ejecutadas sobre las reglas de depuración de lotes (`RL-01` a `RL-05`) en `gestores.py` para auditar la sensibilidad de la suite de `pytest` (`tests/test_pedidos_lote.py`).

## Tabla de Mutantes Evaluados

| ID Mutante | Regla | Línea Original en `gestores.py` | Mutación Inyectada (Operador Relacional) | Prueba que Detecta el Fallo (Mata al Mutante) | Estado del Mutante |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **M-01** | `RL-01` (Caducidad) | `if dt_venc <= dt_actual:` | `if dt_venc < dt_actual:` | `test_limite_exacto_rl01_caducidad[limite_exacto_igual_a_fecha_actual_rechaza]` | **Eliminado (Killed)** |
| **M-02** | `RL-03` (Red de Frío - Mín) | `if temp_val < 2.0 or temp_val > 8.0:` | `if temp_val <= 2.0 or temp_val > 8.0:` | `test_limite_exacto_rl03_red_de_frio[umbral_exacto_inferior_2_0C_acepta]` | **Eliminado (Killed)** |
| **M-03** | `RL-03` (Red de Frío - Máx) | `if temp_val < 2.0 or temp_val > 8.0:` | `if temp_val < 2.0 or temp_val >= 8.0:` | `test_limite_exacto_rl03_red_de_frio[umbral_exacto_superior_8_0C_acepta]` | **Eliminado (Killed)** |
| **M-04** | `RL-04` (Tolerancia Peso 3%) | `if diferencia_relativa > 0.03:` | `if diferencia_relativa >= 0.03:` | `test_limite_exacto_rl04_tolerancia_peso_3_por_ciento[diferencia_exacta_mas_3_por_ciento_acepta]` | **Eliminado (Killed)** |

## Conclusión de Calidad de la Suite
Al incorporar pruebas parametrizadas con valores límite exactos (`Fecha_Vencimiento == Fecha_Actual`, `2.0 °C`, `8.0 °C`, y `±3.0%` de diferencia de peso), el **100% de los mutantes de operadores relacionales** fueron detectados y eliminados por `pytest`.
