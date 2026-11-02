# Comparativa: Planificación de Pruebas (`Act03_P2` Tabla 4) vs. Implementación Real (`tests/`)

## 1. Distribución Planificada en `Act03_P2` (Tabla 4 — Etapa 2)

En el acta de planificación de la Etapa 2 (`Act03_P2_ESTADOS_LOTES`, página 7, Tabla 4), se proyectó dividir la suite en 4 archivos nominales por integrante para cubrir los 8 criterios originales de la Etapa 2 (`C-01` a `C-08`, renumerados en la matriz unificada como `C-13` a `C-20`):

| Integrante | Rol | Bloque Planificado en `Act03_P2` | Archivo Planificado en `Act03_P2` | Criterios Equivalentes en Matriz Unificada (`C-01`..`C-32`) |
| :--- | :--- | :--- | :--- | :--- |
| **André David Ramírez Sánchez** | Arquitecto | `C-01`, `C-02`, `C-03` *(Estados y transiciones)* | `test_pedidos_estados.py` | `C-13`, `C-14`, `C-15` (más `C-21`, `C-22`, `C-24`, `C-31`) |
| **Ricardo Rivas Rivas** | Desarrollador CRUD | `C-04`, `C-05` *(Reglas de limpieza y validaciones)* | `test_pedidos_limpieza.py` | `C-16` (`RL-01`), `C-17` (`RL-02`) (más `C-23`, `C-25`, `C-30`) |
| **Pamela Aguirre López** | Encargada de Pruebas | `C-06`, `C-07` *(Cotejo de lotes, reportes y relaciones)* | `test_pedidos_lote.py` | `C-18` (`RL-03`), `C-19` (`RL-04`) (más `C-26`, `C-28`, `C-29`) |
| **Raúl Barba Llaguno** | Documentador | `C-08` *(Persistencia y revisión final del acta)* | `test_pedidos_persistencia.py` | `C-20` (`RL-05`) (más `C-27`, `C-32`) |

---

## 2. Árbol Real Implementado en `tests/`

En la implementación final del repositorio, la suite se consolidó por **capa arquitectónica** en 3 módulos de prueba más 1 módulo de fixtures compartidas (`conftest.py`), integrando tanto los criterios de la Etapa 1 (`C-01` a `C-12`) como los de la Etapa 2 (`C-13` a `C-20`) y los criterios de endurecimiento y regresión (`C-21` a `C-32`):

| Archivo Real en `tests/` | Responsabilidad Técnica Real | Criterios Cubiertos (`C-01`..`C-32`) | Ítems Ejecutados en `pytest` |
| :--- | :--- | :--- | :--- |
| [`tests/conftest.py`](../tests/conftest.py) | Fixtures reutilizables aisladas con `tmp_path` (`entorno_gestores`, `entorno_poblado`). | Soporte transversal para `C-01`..`C-32` | — |
| [`tests/test_modelos.py`](../tests/test_modelos.py) | Pruebas unitarias de entidades (`Cliente`, `Ruta`, `Pedido`), serialización, validaciones de dominio, inmutabilidad de `estado` y matriz $7 \times 7$ de transiciones. | `C-02`, `C-05`, `C-10`, `C-21`, `C-22`, `C-24`, `C-31` | 87 ítems |
| [`tests/test_gestores.py`](../tests/test_gestores.py) | Pruebas unitarias, de integración y de aceptación sobre `GestorClientes`, `GestorRutas`, `GestorPedidos`, integridad referencial, atomicidad y flujo `main.py`. | `C-01`, `C-03`, `C-04`, `C-06`, `C-07`, `C-08`, `C-09`, `C-11`, `C-12`, `C-23`, `C-25`, `C-30`, `C-32` | 13 ítems |
| [`tests/test_pedidos_lote.py`](../tests/test_pedidos_lote.py) | Pruebas de máquina de estados desde `GestorPedidos` (`C-13`..`C-15`), valores límite de `RL-01`..`RL-05` (`C-16`..`C-20`) y reglas estructurales/multi-regla de `cargar_lote` (`C-26`..`C-29`). | `C-13`, `C-14`, `C-15`, `C-16`, `C-17`, `C-18`, `C-19`, `C-20`, `C-26`, `C-27`, `C-28`, `C-29` | 38 ítems |
| **Total** | **3 módulos de prueba + `conftest.py`** | **32 criterios (`C-01` a `C-32`)** | **138 ítems (`138 passed`)** |

---

## 3. Justificación Técnica del Cambio (Plan vs. Implementado)

1. **Unificación de Etapa 1 y Etapa 2 sin colisión de nombres ni duplicación de fixtures:**
   * En `Act03_P2` solo se listaron archivos para la Etapa 2 (`test_pedidos_*.py`), omitiendo dónde residían las pruebas de la Etapa 1 (`C-01` a `C-12` de modelos y gestores CRUD). Organizar `tests/` en `test_modelos.py`, `test_gestores.py` y `test_pedidos_lote.py` permitió mantener una correspondencia directa con los módulos del sistema (`modelos.py` $\leftrightarrow$ `test_modelos.py`; `gestores.py` CRUD $\leftrightarrow$ `test_gestores.py`; `gestores.py` estados y lotes $\leftrightarrow$ `test_pedidos_lote.py`).
2. **Cohesión de parametrización en `test_pedidos_lote.py`:**
   * Las pruebas de transiciones operativas (`C-13`..`C-15`) y depuración de lotes (`C-16`..`C-20`, `C-26`..`C-29`) comparten la misma fixture `entorno_poblado` y el mismo flujo de `GestorPedidos.cargar_lote()`. Concentrarlas en `test_pedidos_lote.py` evitó duplicar funciones auxiliares de escritura de lotes CSV en cuatro archivos pequeños.
