# Tabla de Transiciones de la Máquina de Estados (`Pedido`)

## 1. Tabla de Transiciones por Estado Origen

> **Nota para el equipo:** La columna **`Razón de Negocio`** se entrega intencionalmente vacía conforme a la directriz 3.2 para que el Arquitecto / Documentador la redacte con sus propias palabras en el reporte técnico.

| Estado Origen | Estados Destino Permitidos (`TRANSICIONES_PERMITIDAS`) | Estados Destino Prohibidos Más Dañinos | Excepción Lanzada al Intentar Prohibidos | Razón de Negocio |
| :--- | :--- | :--- | :--- | :--- |
| `Registrado` | `En Validación`, `Cancelado` | `Aprobado`, `En Preparación`, `En Ruta`, `Entregado` (salto de validación y surtido); `Registrado` (auto-transición) | `ErrorTransicionEstado` | |
| `En Validación` | `Aprobado`, `Cancelado` | `En Preparación`, `En Ruta`, `Entregado` (despacho sin aprobación); `Registrado` (regresión al inicio) | `ErrorTransicionEstado` | |
| `Aprobado` | `En Preparación`, `Cancelado` | `En Ruta`, `Entregado` (salida de unidad sin orden de preparación en almacén); `Registrado`, `En Validación` (regresión) | `ErrorTransicionEstado` | |
| `En Preparación` | `En Ruta` | `Cancelado` (cancelación tardía con mercancía ya surtida); `Entregado` (cierre sin traslado); `Registrado`, `En Validación`, `Aprobado` | `ErrorTransicionEstado` | |
| `En Ruta` | `Entregado` | `Cancelado` (cancelación extemporánea con unidad en tránsito); `Registrado`, `En Validación`, `Aprobado`, `En Preparación` | `ErrorTransicionEstado` | |
| `Entregado` | *(Ninguno — estado terminal)* | `Registrado`, `En Validación`, `Aprobado`, `En Preparación`, `En Ruta`, `Cancelado` (reapertura o alteración de pedido cerrado) | `ErrorTransicionEstado` | |
| `Cancelado` | *(Ninguno — estado terminal)* | `Registrado`, `En Validación`, `Aprobado`, `En Preparación`, `En Ruta`, `Entregado` (reactivación de orden anulada) | `ErrorTransicionEstado` | |

---

## 2. Matriz Exhaustiva $7 \times 7$ de Pares `(origen, destino)` (49 Combinaciones Verificadas en `C-21`)

| Origen \ Destino | `Registrado` | `En Validación` | `Aprobado` | `En Preparación` | `En Ruta` | `Entregado` | `Cancelado` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Registrado`** | Prohibida | **Permitida** | Prohibida | Prohibida | Prohibida | Prohibida | **Permitida** |
| **`En Validación`** | Prohibida | Prohibida | **Permitida** | Prohibida | Prohibida | Prohibida | **Permitida** |
| **`Aprobado`** | Prohibida | Prohibida | Prohibida | **Permitida** | Prohibida | Prohibida | **Permitida** |
| **`En Preparación`** | Prohibida | Prohibida | Prohibida | Prohibida | **Permitida** | Prohibida | Prohibida |
| **`En Ruta`** | Prohibida | Prohibida | Prohibida | Prohibida | Prohibida | **Permitida** | Prohibida |
| **`Entregado`** | Prohibida | Prohibida | Prohibida | Prohibida | Prohibida | Prohibida | Prohibida |
| **`Cancelado`** | Prohibida | Prohibida | Prohibida | Prohibida | Prohibida | Prohibida | Prohibida |

* **Total de pares evaluados en `test_c21_matriz_completa_49_transiciones_estados`:** $7 \times 7 = 49$.
* **Transiciones permitidas:** $8$.
* **Transiciones prohibidas (lanzan `ErrorTransicionEstado`):** $41$.
