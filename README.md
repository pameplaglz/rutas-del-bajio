# Rutas del Bajío — Sistema Logístico (Parcial 2)

Backend logístico desarrollado para la materia **Análisis de Procesos de la Industria** (Ingeniería en Software y Sistemas Computacionales, Universidad De La Salle Bajío).

## Integrantes del Equipo y Roles
- **Arquitecto:** André David Ramírez Sánchez (`modelos.py` — Entidades y Máquina de Estados)
- **Desarrollador CRUD:** Ricardo Rivas Rivas (`gestores.py`, `main.py` — CRUD, Persistencia CSV y Reglas de Lote)
- **Encargada de Pruebas:** Pamela Aguirre López (`tests/`, `pytest.ini` — Suite Pytest, Valores Límite y Mutaciones)
- **Documentador:** Raúl Barba Llaguno (`README.md`, `NOTAS_MUTACIONES.md` — Documentación e Integración)

## Catálogo Oficial de Estados del Pedido
Los únicos estados operativos válidos en el ciclo de vida de un `Pedido` son estrictamente:
1. `"Registrado"` *(estado inicial)*
2. `"En Validación"`
3. `"Aprobado"`
4. `"En Preparación"`
5. `"En Ruta"`
6. `"Entregado"` *(estado final)*
7. `"Cancelado"` *(estado final)*

## Estructura del Proyecto
```text
rutas_del_bajio/
├── modelos.py              # Entidades del dominio (Cliente, Ruta, Pedido) y máquina de estados oficial
├── gestores.py             # Gestores CRUD, persistencia CSV y depuración de lotes (RL-01 a RL-05)
├── main.py                 # Punto de entrada y flujo de demostración
├── pytest.ini              # Configuración de descubrimiento y marcadores de pytest
├── NOTAS_MUTACIONES.md     # Registro de pruebas de mutación sobre operadores relacionales (RL-01 a RL-04)
├── README.md               # Documentación general del repositorio
└── tests/                  # Suite de pruebas automatizadas con pytest
    ├── conftest.py         # Fixtures centralizadas con aislamiento mediante tmp_path
    ├── test_modelos.py     # Pruebas unitarias de entidades y catálogo estricto de estados
    ├── test_gestores.py    # Pruebas de persistencia CSV, llaves foráneas y CRUD (C-01 a C-12)
    └── test_pedidos_lote.py# Pruebas de máquina de estados, valores límite exactos y mutaciones
```
