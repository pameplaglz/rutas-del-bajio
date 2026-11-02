# Notas de Verificación de Mutaciones (`NOTAS_MUTACIONES.md`) — Rutas del Bajío

Este documento registra las pruebas de mutación ejecutadas mediante **inyección manual automatizada** con el script [`scripts/mutar.py`](file:///C:/Users/Pamela%20Aguirre/.gemini/antigravity/scratch/rutas_del_bajio/scripts/mutar.py) (sin utilizar herramientas externas como `mutmut`, reemplazando cada línea objetivo en una copia temporal y restaurando siempre el archivo original dentro de un bloque `try / finally`).

## Resumen de Resultados Reales
- **Total de mutantes inyectados:** `23`
- **Mutantes eliminados (corrida inicial):** `20 de 23` (`87.0%`)
- **Mutantes sobrevivientes iniciales detectados:** `3` (`M-17`, `M-20`, `M-21`)
- **Mutantes eliminados (corrida final tras corrección de pruebas):** **`23 de 23 mutantes eliminados` (`100.0% Mutation Score`)**

---

## Análisis de Sobrevivientes Iniciales y Pruebas Añadidas

Durante la primera corrida de `scripts/mutar.py` sobrevivieron **3 mutantes** sobre `TRANSICIONES_PERMITIDAS` en `modelos.py`:
1. **`M-17`** (`En Validación` $\rightarrow$ agrega transición prohibida a `En Preparación`).
2. **`M-20`** (`Entregado` $\rightarrow$ agrega transición prohibida de retroceso a `En Ruta`).
3. **`M-21`** (`Cancelado` $\rightarrow$ agrega transición prohibida de reapertura a `Registrado`).

- **Causa raíz descubierta:** En la primera versión de `test_c21_matriz_completa_49_transiciones_estados`, la lista parametrizada calculaba si una transición era válida consultando directamente `destino in TRANSICIONES_PERMITIDAS[origen]` del propio módulo `modelos.py` bajo prueba (oráculo tautológico). Al mutar `TRANSICIONES_PERMITIDAS` en `modelos.py`, la prueba adoptaba el diccionario mutado como verdad esperada.
- **Corrección aplicada en la suite:** Se definió en `tests/test_modelos.py` el conjunto independiente e inmutable `ORACULO_TRANSICIONES_PERMITIDAS` con las 8 únicas transiciones válidas del negocio para parametrizar `test_c21_matriz_completa_49_transiciones_estados`. Al volver a ejecutar `python scripts/mutar.py`, los mutantes `M-17`, `M-20` y `M-21` fueron eliminados inmediatamente.

Adicionalmente, en el diseño previo a la Fase 2 se habían identificado otros posibles huecos que motivaron casos específicos en la suite:
- **`M-05` (`p_teo <= 0` $\rightarrow$ `p_teo < 0`):** Eliminado por `test_c19_tolerancia_pesaje_rl04[peso_teorico_cero_rechaza]`.
- **`M-07` (Omisión de `id_ped in ids_vistos` dentro del mismo lote):** Eliminado por la fila duplicada intra-lote en `test_c29_lote_reglas_estructurales_id_campo_est_dup_fk`.
- **`M-11` y `M-14` (Inversión de `and` $\rightarrow$ `or` en guardias de campos opcionales):** Eliminados por los casos de cadena vacía en `test_c16_depuracion_lote_caducado_rl01[sin_fecha_vencimiento_opcional_no_dispara_rl01]` y `test_c19_tolerancia_pesaje_rl04[sin_peso_real_opcional_no_dispara_rl04]`.

---

## Tabla Completa de los 23 Mutantes Evaluados

| ID | Archivo | Línea | Mutación Inyectada | Resultado | Prueba que Detecta el Fallo (Mata al Mutante) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **M-01** | `gestores.py` | `169` | `RL-01: dt_venc <= dt_actual -> dt_venc < dt_actual` | **Killed** | `tests/test_pedidos_lote.py::test_c16_depuracion_lote_caducado_rl01[limite_exacto_igual_a_fecha_actual_rechaza]` |
| **M-02** | `gestores.py` | `200` | `RL-03: temp_val < 2.0 -> temp_val <= 2.0` | **Killed** | `tests/test_pedidos_lote.py::test_c18_alerta_cadena_frio_rl03[umbral_exacto_inferior_2_0C_acepta]` |
| **M-03** | `gestores.py` | `200` | `RL-03: temp_val > 8.0 -> temp_val >= 8.0` | **Killed** | `tests/test_pedidos_lote.py::test_c18_alerta_cadena_frio_rl03[umbral_exacto_superior_8_0C_acepta]` |
| **M-04** | `gestores.py` | `237` | `RL-04: diferencia_relativa > 0.03 -> >= 0.03` | **Killed** | `tests/test_pedidos_lote.py::test_c19_tolerancia_pesaje_rl04[diferencia_exacta_mas_3_por_ciento_acepta]` |
| **M-05** | `gestores.py` | `227` | `RL-04: p_teo <= 0 -> p_teo < 0` | **Killed** | `tests/test_pedidos_lote.py::test_c19_tolerancia_pesaje_rl04[peso_teorico_cero_rechaza]` |
| **M-06** | `gestores.py` | `255` | `RL-05: sin verificacion de estado "PENDIENTE"` | **Killed** | `tests/test_pedidos_lote.py::test_c20_cuarentena_falta_certificado_rl05[certificado_pendiente_rechaza]` |
| **M-07** | `gestores.py` | `780` | `Lote: omite chequeo de duplicado dentro del mismo lote` | **Killed** | `tests/test_pedidos_lote.py::test_c29_lote_reglas_estructurales_id_campo_est_dup_fk` |
| **M-08** | `gestores.py` | `331` | `Guard TypeError desactivado en crear_cliente` | **Killed** | `tests/test_gestores.py::test_c30_crud_completo_gestor_rutas_y_gestor_pedidos` |
| **M-09** | `gestores.py` | `438` | `Guard TypeError desactivado en crear_ruta` | **Killed** | `tests/test_gestores.py::test_c30_crud_completo_gestor_rutas_y_gestor_pedidos` |
| **M-10** | `gestores.py` | `624` | `Guard TypeError desactivado en crear_pedido` | **Killed** | `tests/test_gestores.py::test_c30_crud_completo_gestor_rutas_y_gestor_pedidos` |
| **M-11** | `gestores.py` | `166` | `RL-01: operador logico and -> or en guardia de fecha` | **Killed** | `tests/test_pedidos_lote.py::test_c16_depuracion_lote_caducado_rl01[sin_fecha_vencimiento_opcional_no_dispara_rl01]` |
| **M-12** | `gestores.py` | `187` | `RL-02: operador logico and -> or en regex de lote` | **Killed** | `tests/test_pedidos_lote.py::test_c16_depuracion_lote_caducado_rl01[limite_un_dia_despues_acepta]` |
| **M-13** | `gestores.py` | `200` | `RL-03: operador logico or -> and en rango termico` | **Killed** | `tests/test_pedidos_lote.py::test_c18_alerta_cadena_frio_rl03[bajo_umbral_inferior_1_99C_rechaza]` |
| **M-14** | `gestores.py` | `221` | `RL-04: operador logico and -> or en guardia de peso` | **Killed** | `tests/test_pedidos_lote.py::test_c19_tolerancia_pesaje_rl04[sin_peso_real_opcional_no_dispara_rl04]` |
| **M-15** | `gestores.py` | `255` | `RL-05: operador logico or -> and en certificado` | **Killed** | `tests/test_pedidos_lote.py::test_c20_cuarentena_falta_certificado_rl05[certificado_ausente_rechaza]` |
| **M-16** | `modelos.py` | `50` | `Transiciones: Registrado permite salto directo a En Ruta` | **Killed** | `tests/test_modelos.py::test_c21_matriz_completa_49_transiciones_estados[Registrado_a_En Ruta]` |
| **M-17** | `modelos.py` | `51` | `Transiciones: En Validación permite salto a En Preparación` | **Killed** | `tests/test_modelos.py::test_c21_matriz_completa_49_transiciones_estados[En Validación_a_En Preparación]` |
| **M-18** | `modelos.py` | `53` | `Transiciones: En Preparación permite pasar a Cancelado` | **Killed** | `tests/test_modelos.py::test_c21_matriz_completa_49_transiciones_estados[En Preparación_a_Cancelado]` |
| **M-19** | `modelos.py` | `54` | `Transiciones: En Ruta permite pasar a Cancelado` | **Killed** | `tests/test_modelos.py::test_c21_matriz_completa_49_transiciones_estados[En Ruta_a_Cancelado]` |
| **M-20** | `modelos.py` | `55` | `Transiciones: Entregado permite retroceder a En Ruta` | **Killed** | `tests/test_modelos.py::test_c21_matriz_completa_49_transiciones_estados[Entregado_a_En Ruta]` |
| **M-21** | `modelos.py` | `56` | `Transiciones: Cancelado permite reabrir a Registrado` | **Killed** | `tests/test_modelos.py::test_c21_matriz_completa_49_transiciones_estados[Cancelado_a_Registrado]` |
| **M-22** | `gestores.py` | `373` | `FK: desactiva ErrorIntegridadReferencial en eliminar_cliente` | **Killed** | `tests/test_gestores.py::test_c23_integridad_referencial_eliminar_cliente_y_ruta` |
| **M-23** | `gestores.py` | `480` | `FK: desactiva ErrorIntegridadReferencial en eliminar_ruta` | **Killed** | `tests/test_gestores.py::test_c23_integridad_referencial_eliminar_cliente_y_ruta` |
