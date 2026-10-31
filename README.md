# Rutas del Bajío — Sistema Logístico (Parcial 2)

Backend logístico desarrollado para la materia **Análisis de Procesos de la Industria** (Ingeniería en Software y Sistemas Computacionales, Universidad De La Salle Bajío).

## Integrantes del Equipo
- **Arquitecto:** André David Ramírez Sánchez
- **Desarrollador CRUD:** Ricardo Rivas Rivas
- **Encargada de Pruebas:** Pamela Aguirre López
- **Documentador:** Raúl Barba Llaguno

## Estructura del Proyecto
```text
rutas_del_bajio/
├── modelos.py              # Entidades del dominio (Cliente, Ruta, Pedido) y máquina de estados
├── gestores.py             # Gestores CRUD, persistencia CSV y depuración de lotes (RL-01 a RL-05)
├── main.py                 # Punto de entrada y flujo de demostración
├── pytest.ini              # Configuración de descubrimiento y marcadores de pytest
└── tests/                  # Suite de pruebas automatizadas con pytest
    ├── conftest.py         # Fixtures centralizadas con aislamiento mediante tmp_path
    ├── test_modelos.py     # Pruebas unitarias de entidades y validaciones (C-02, C-05, C-10)
    ├── test_gestores.py    # Pruebas de persistencia CSV, llaves foráneas y CRUD (C-01 a C-12)
    └── test_pedidos_lote.py# Pruebas de máquina de estados y depuración de lotes (Etapa 2)
```
