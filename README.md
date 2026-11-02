# Rutas del Bajío — Sistema Logístico Backend (Parcial 2)

Backend logístico en Python para la gestión de clientes, rutas de distribución, ciclo de vida de pedidos mediante máquina de estados determinista y procesamiento masivo de lotes con reglas de limpieza e inocuidad (`RL-01` a `RL-05`). Desarrollado para la materia **Análisis de Procesos de la Industria** (Ingeniería en Software y Sistemas Computacionales, Universidad De La Salle Bajío).

---

## 1. Requisitos e Instalación

* **Python:** `3.10+` (verificado en Python `3.12.16`).
* **Dependencias de ejecución:** únicamente librería estándar de Python (`csv`, `dataclasses`, `datetime`, `os`, `re`, `tempfile`, `typing`).
* **Dependencias de pruebas y cobertura (`requirements-dev.txt`):** `pytest>=7.0` y `pytest-cov>=4.0`.

```bash
# Crear y activar entorno virtual (opcional pero recomendado)
python -m venv .venv
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Linux / macOS:
source .venv/bin/activate

# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt
```

---

## 2. Cómo Ejecutar el Sistema, la Suite de Pruebas y las Mutaciones

### 2.1 Flujo de demostración y generación de ejemplos (`main.py`)

Ejecuta el alta de entidades, las transiciones de la máquina de estados y el procesamiento del lote [`examples/lote_ejemplo.csv`](examples/lote_ejemplo.csv) generando [`examples/rechazos_ejemplo.csv`](examples/rechazos_ejemplo.csv):

```bash
python main.py
```

### 2.2 Suite de pruebas automatizadas (`pytest`)

```bash
# Ejecución completa detallada (138 ítems en 32 criterios C-01..C-32)
pytest -v -ra

# Ejecución filtrada por marcador de nivel
pytest -m unitaria
pytest -m integracion
pytest -m aceptacion

# Reporte de cobertura por línea con líneas faltantes
pytest --cov=. --cov-report=term-missing
```

### 2.3 Script de pruebas de mutación manual (`scripts/mutar.py`)

Inyecta secuencialmente los **23 mutantes** (`M-01` a `M-23`) en `gestores.py` y `modelos.py`, ejecuta `pytest -x -q` por cada mutante y restaura siempre el archivo original mediante bloques `try / finally`:

```bash
python scripts/mutar.py
```

---

## 3. Árbol Real de Archivos del Repositorio

```text
rutas_del_bajio/
├── errores.py                  # Excepciones de dominio y constantes oficiales de subestados de rechazo
├── modelos.py                  # Entidades (Cliente, Ruta, Pedido) y máquina de 7 estados oficiales
├── gestores.py                 # Gestores CRUD, persistencia CSV atómica y validación de lotes (RL-01..RL-05)
├── main.py                     # Flujo de demostración reproducible y generación de examples/
├── pytest.ini                  # Configuración de pytest y marcadores estrictos (unitaria, integracion, aceptacion)
├── requirements-dev.txt        # Dependencias de pruebas (pytest, pytest-cov)
├── NOTAS_MUTACIONES.md         # Registro auditable de los 23 mutantes evaluados (100% Mutation Score)
├── README.md                   # Guía de instalación, ejecución, arquitectura y enlaces a docs/
├── examples/
│   ├── lote_ejemplo.csv        # Lote CSV de entrada con casos válidos y violaciones a RL-01..RL-05
│   └── rechazos_ejemplo.csv    # Bitácora CSV de rechazos generada por GestorPedidos.cargar_lote()
├── scripts/
│   └── mutar.py                # Motor de inyección manual de mutantes sin dependencias externas
├── tests/
│   ├── conftest.py             # Fixtures compartidas aisladas con tmp_path
│   ├── test_modelos.py         # Pruebas unitarias de entidades y matriz 7x7 de transiciones
│   ├── test_gestores.py        # Pruebas CRUD, integridad referencial, atomicidad y main.py
│   └── test_pedidos_lote.py    # Pruebas de estados en gestor, valores límite RL-01..RL-05 y lotes
└── docs/
    ├── catalogo_operaciones.md # Inventario de clases, métodos, retornos y excepciones
    ├── checklist_entrega.md    # Lista de verificación de la sección 9 de la guía Proyecto_P2
    ├── defectos.md             # Bitácora de los 11 defectos reales detectados y corregidos
    ├── diagramas.md            # Diagramas Mermaid (Figura 1: Clases/ER; Figura 2: Máquina de Estados)
    ├── diccionario_datos.md    # Esquema de columnas, tipos, reglas y excepciones por archivo CSV
    ├── limites.md              # Límites honestos del alcance actual de pruebas y arquitectura
    ├── matriz_criterios.md     # Matriz unificada de los 32 criterios de prueba (C-01 a C-32)
    ├── pendientes_humano.md    # Decisiones abiertas de dominio para acuerdo del equipo
    ├── plan_vs_implementado.md # Comparativa entre la Tabla 4 de Act03_P2 y el árbol real de tests/
    └── tabla_transiciones.md   # Tabla de transiciones permitidas/prohibidas y matriz 7x7
```

---

## 4. Integrantes del Equipo y Roles

| Integrante | Rol | Responsabilidad Técnica y Documental |
| :--- | :--- | :--- |
| **André David Ramírez Sánchez** | Arquitecto | [`modelos.py`](modelos.py), modelo de entidades, composición, máquina de 7 estados oficiales y apoyo del Capítulo 1 ([`docs/diagramas.md`](docs/diagramas.md), [`docs/tabla_transiciones.md`](docs/tabla_transiciones.md)). |
| **Ricardo Rivas Rivas** | Desarrollador CRUD | [`gestores.py`](gestores.py), [`errores.py`](errores.py), [`main.py`](main.py), persistencia CSV atómica, integridad referencial, carga por lote (`RL-01`..`RL-05`) y apoyo del Capítulo 2 ([`docs/diccionario_datos.md`](docs/diccionario_datos.md), [`docs/catalogo_operaciones.md`](docs/catalogo_operaciones.md)). |
| **Pamela Aguirre López** | Encargada de Pruebas | [`tests/`](tests/), [`pytest.ini`](pytest.ini), [`scripts/mutar.py`](scripts/mutar.py), [`NOTAS_MUTACIONES.md`](NOTAS_MUTACIONES.md) y apoyo del Capítulo 3 ([`docs/matriz_criterios.md`](docs/matriz_criterios.md), [`docs/defectos.md`](docs/defectos.md), [`docs/limites.md`](docs/limites.md)). |
| **Raúl Barba Llaguno** | Documentador | [`README.md`](README.md), [`docs/checklist_entrega.md`](docs/checklist_entrega.md), [`docs/plan_vs_implementado.md`](docs/plan_vs_implementado.md), integración editorial del reporte técnico y consolidación de anexos. |

---

## 5. Índice de Documentación de Apoyo (`docs/`)

* **Arquitectura y Dominio (Cap. 1):**
  * [Diagramas de Clases, Entidad-Relación y Máquina de Estados (`docs/diagramas.md`)](docs/diagramas.md)
  * [Tabla de Transiciones y Matriz $7 \times 7$ (`docs/tabla_transiciones.md`)](docs/tabla_transiciones.md)
  * [Decisiones de Dominio Pendientes para el Equipo (`docs/pendientes_humano.md`)](docs/pendientes_humano.md)
* **Implementación CRUD, Persistencia y Lotes (Cap. 2):**
  * [Diccionario de Datos de Archivos CSV (`docs/diccionario_datos.md`)](docs/diccionario_datos.md)
  * [Catálogo de Operaciones por Clase y Gestor (`docs/catalogo_operaciones.md`)](docs/catalogo_operaciones.md)
* **Estrategia y Resultados de Pruebas (Cap. 3):**
  * [Matriz Unificada de 32 Criterios de Prueba `C-01`..`C-32` (`docs/matriz_criterios.md`)](docs/matriz_criterios.md)
  * [Bitácora de Defectos Detectados y Corregidos (`docs/defectos.md`)](docs/defectos.md)
  * [Límites del Alcance de Pruebas (`docs/limites.md`)](docs/limites.md)
  * [Notas y Resultados de Pruebas de Mutación (`NOTAS_MUTACIONES.md`)](NOTAS_MUTACIONES.md)
* **Gestión del Proyecto y Verificación de Entrega (Cap. 4):**
  * [Comparativa Plan (`Act03_P2` Tabla 4) vs. Implementado (`docs/plan_vs_implementado.md`)](docs/plan_vs_implementado.md)
  * [Lista de Verificación Final — Sección 9 de `Proyecto_P2` (`docs/checklist_entrega.md`)](docs/checklist_entrega.md)
