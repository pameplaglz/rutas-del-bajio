# Diccionario de Datos de Archivos CSV

Especificación extraída directamente de [`modelos.py`](../modelos.py), [`gestores.py`](../gestores.py) y [`errores.py`](../errores.py).

---

## 1. `clientes.csv` (`GestorClientes.CAMPOS_CSV`)

* **Validación a nivel archivo:** Si los encabezados no coinciden exactamente en orden y minúsculas con `["id_cliente", "nombre", "ciudad", "telefono"]`, `GestorClientes.cargar()` lanza `ErrorArchivoLote`.

| Columna | Tipo en Python | Obligatoriedad | Regla de Limpieza y Validación | Excepción que Lanza |
| :--- | :--- | :--- | :--- | :--- |
| `id_cliente` | `str` | Obligatorio (`PK`) | Se aplica `strip()`. No vacío (`""`) y único dentro de `GestorClientes`. | `ValueError` (si vacío o duplicado) |
| `nombre` | `str` | Obligatorio | Se aplica `strip()`. No vacío (`""`). | `ValueError` |
| `ciudad` | `str` | Obligatorio | Se aplica `normalizar_ciudad()` (`strip()` y `"Leon"` $\rightarrow$ `"León"`). No vacío (`""`). | `ValueError` |
| `telefono` | `str` | Obligatorio | Se aplica `strip()`. No vacío (`""`). | `ValueError` |

---

## 2. `rutas.csv` (`GestorRutas.CAMPOS_CSV`)

* **Validación a nivel archivo:** Si los encabezados no coinciden exactamente con `["id_ruta", "origen", "destino", "distancia_km", "tiempo_estimado", "transportista"]`, `GestorRutas.cargar()` lanza `ErrorArchivoLote`.

| Columna | Tipo en Python | Obligatoriedad | Regla de Limpieza y Validación | Excepción que Lanza |
| :--- | :--- | :--- | :--- | :--- |
| `id_ruta` | `str` | Obligatorio (`PK`) | Se aplica `strip()`. No vacío (`""`) y único dentro de `GestorRutas`. | `ValueError` (si vacío o duplicado) |
| `origen` | `str` | Obligatorio | Se aplica `normalizar_ciudad()`. Debe ser estrictamente `"León"`. | `ValueError` |
| `destino` | `str` | Obligatorio | Se aplica `normalizar_ciudad()`. Debe pertenecer a `DESTINOS_PERMITIDOS` y ser distinto de `"León"` (`{"Irapuato", "Celaya", "Salamanca", "Guanajuato"}`). | `ValueError` |
| `distancia_km` | `float` | Obligatorio | Rechaza `bool`. Convertible a `float` y estrictamente `> 0.0`. | `ValueError` |
| `tiempo_estimado` | `float` | Obligatorio | Rechaza `bool`. Convertible a `float` y estrictamente `> 0.0`. | `ValueError` |
| `transportista` | `str` | Obligatorio | Se aplica `strip()`. No vacío (`""`). | `ValueError` |

---

## 3. `pedidos.csv` (`GestorPedidos.CAMPOS_CSV`) y `<archivo>.descartados.csv`

* **Validación a nivel archivo:** Si los encabezados de `pedidos.csv` no coinciden exactamente con `["id_pedido", "id_cliente", "producto", "cantidad", "origen", "destino", "fecha_pedido", "estado", "id_ruta"]`, `GestorPedidos.cargar()` lanza `ErrorArchivoLote`.
* **Comportamiento en `cargar()` ante errores de fila:** Si una fila tiene datos inválidos o FK inexistente, se descarta de `self.pedidos`, se registra en `self.descartados` (`RegistroDescarte`) y se respalda atómicamente en `<archivo>.descartados.csv` con las columnas `["linea", "id_pedido", "motivo", *CAMPOS_CSV]`.

| Columna | Tipo en Python | Obligatoriedad | Regla de Limpieza y Validación | Excepción que Lanza (en creación/actualización) |
| :--- | :--- | :--- | :--- | :--- |
| `id_pedido` | `str` | Obligatorio (`PK`) | Se aplica `strip()`. No vacío (`""`) y único dentro de `GestorPedidos`. | `ValueError` |
| `id_cliente` | `str` | Obligatorio (`FK`) | Se aplica `strip()`. No vacío (`""`) y debe existir en `GestorClientes`. | `ValueError` |
| `producto` | `str` | Obligatorio | Se aplica `strip()`. No vacío (`""`). | `ValueError` |
| `cantidad` | `int` | Obligatorio | Rechaza `bool` y cadenas con punto decimal (`"."`). Entero estricto `> 0`. | `ValueError` |
| `origen` | `str` | Obligatorio | Se aplica `normalizar_ciudad()`. Debe pertenecer a `CIUDADES_BAJIO` (`{"León", "Irapuato", "Celaya", "Salamanca", "Guanajuato"}`), `origen != destino`, y si hay `id_ruta`, debe coincidir con `ruta.origen`. | `ValueError` |
| `destino` | `str` | Obligatorio | Se aplica `normalizar_ciudad()`. Debe pertenecer a `CIUDADES_BAJIO`, `origen != destino`, y si hay `id_ruta`, debe coincidir con `ruta.destino`. | `ValueError` |
| `fecha_pedido` | `str` | Obligatorio | Se aplica `strip()`. Formato ISO estricto `YYYY-MM-DD` (`datetime.strptime`). | `ValueError` |
| `estado` | `str` | Obligatorio | Propiedad de solo lectura (`pedido.estado`). En creación (`Pedido()`, `crear_pedido()`) solo acepta `"Registrado"` (o `""` $\rightarrow$ `"Registrado"`). En reconstrucción (`from_dict(..., restaurar_estado=True)`) acepta cualquiera de los 7 estados de `ESTADOS_VALIDOS`. | `ValueError` (fuera de catálogo) / `ErrorTransicionEstado` (creación en estado distinto de `"Registrado"` o transición prohibida) |
| `id_ruta` | `str` | Opcional (`FK`) | Se aplica `strip()`. Si no está vacío (`""`), debe existir en `GestorRutas` y coincidir en `origen` y `destino` con el pedido. | `ValueError` |

---

## 4. Archivo CSV de Lote de Entrada (p. ej. `examples/lote_ejemplo.csv`)

* **Validación a nivel archivo (`GestorPedidos.cargar_lote`):**
  1. Archivo inexistente $\rightarrow$ lanza `ErrorArchivoLote`.
  2. Archivo vacío o sin fila de encabezados $\rightarrow$ lanza `ErrorArchivoLote`.
  3. Cualquier encabezado con letras mayúsculas o espacios extremos (`h != h.strip().lower()`) $\rightarrow$ lanza `ErrorArchivoLote`.
  4. Falta cualquiera de las columnas mínimas `COLUMNAS_OBLIGATORIAS_LOTE = ("id_pedido", "id_cliente", "cantidad")` $\rightarrow$ lanza `ErrorArchivoLote`.
* **Validación a nivel fila:** Las reglas `RL-01`..`RL-05` se evalúan en orden numérico en `validar_insumo_lote()` seguidas de las validaciones estructurales (`RL-ID`, `RL-CAMPO`, `RL-EST`, `RL-DUP`, `RL-FK`). Los campos de inspección de lote (`codigo_lote`..`certificado_calidad`) no se almacenan como atributos de `Pedido`.

| Columna | Tipo Esperado | Obligatoriedad en Fila | Regla de Limpieza y Validación | Excepción / Código de Regla en Fila |
| :--- | :--- | :--- | :--- | :--- |
| `id_pedido` | `str` | Obligatorio (encabezado y valor) | `strip()`. No vacío, no duplicado en el mismo lote ni en `GestorPedidos`. | `FilaLoteInvalidaError`: `RL-ID` (`Rechazo: Datos Inválidos`) si vacío; `RL-DUP` (`Rechazo: Descarte`) si duplicado |
| `id_cliente` | `str` | Obligatorio (encabezado y valor) | `strip()`. No vacío y debe existir en `GestorClientes`. | `FilaLoteInvalidaError`: `RL-CAMPO` si vacío; `RL-FK` (`Rechazo: Datos Inválidos`) si no existe |
| `producto` | `str` | Obligatorio (valor) | `strip()`. Sin valores por defecto silenciosos; no vacío. | `FilaLoteInvalidaError`: `RL-CAMPO` (`Rechazo: Datos Inválidos`) |
| `cantidad` | `int` | Obligatorio (encabezado y valor) | `strip()`. Entero estricto `> 0`. | `FilaLoteInvalidaError`: `RL-CAMPO` (`Rechazo: Datos Inválidos`) |
| `origen` | `str` | Obligatorio (valor) | `normalizar_ciudad()`. En `CIUDADES_BAJIO`, `origen != destino`, y coincidente con `ruta.origen` si hay `id_ruta`. | `FilaLoteInvalidaError`: `RL-CAMPO` (`Rechazo: Datos Inválidos`) |
| `destino` | `str` | Obligatorio (valor) | `normalizar_ciudad()`. En `CIUDADES_BAJIO`, `origen != destino`, y coincidente con `ruta.destino` si hay `id_ruta`. | `FilaLoteInvalidaError`: `RL-CAMPO` (`Rechazo: Datos Inválidos`) |
| `fecha_pedido` | `str` | Obligatorio (valor) | `strip()`. Formato `YYYY-MM-DD`. | `FilaLoteInvalidaError`: `RL-CAMPO` (`Rechazo: Datos Inválidos`) |
| `estado` | `str` | Opcional (valor) | `strip()`. Vacío (`""`) se limpia a `"Registrado"`. Cualquier valor distinto de `"Registrado"` se rechaza. | `FilaLoteInvalidaError`: `RL-EST` (`Rechazo: Estado Inválido`) |
| `id_ruta` | `str` | Opcional (valor) | `strip()`. Si se informa, debe existir en `GestorRutas` y coincidir en trayecto. | `FilaLoteInvalidaError`: `RL-FK` / `RL-CAMPO` (`Rechazo: Datos Inválidos`) |
| `codigo_lote` | `str` | Opcional (insumo) | `strip().upper()`. Si no está vacío, debe cumplir `^LT-[0-9]{5}-[A-Z]{2}$`. | `FilaLoteInvalidaError`: `RL-02` (`Rechazo: Formato Inválido`) |
| `fecha_vencimiento` | `str` | Opcional (insumo) | `strip()`. Si no está vacío, debe ser fecha `YYYY-MM-DD` estrictamente `> fecha_actual`. Si `<= fecha_actual` o formato inválido, se rechaza. | `FilaLoteInvalidaError`: `RL-01` (`Rechazo: Cuarentena`) |
| `temperatura_c` | `float` | Opcional (insumo) | `strip()`. Si no está vacío, debe ser `float` dentro del intervalo cerrado `[2.0, 8.0]`. | `FilaLoteInvalidaError`: `RL-03` (`Rechazo: Red de Frío`) |
| `peso_real` | `float` | Opcional (insumo) | `strip()`. Si `peso_real` y `peso_teorico` están presentes, `round(abs(p_real - p_teo) / p_teo, 9) <= 0.03`. | `FilaLoteInvalidaError`: `RL-04` (`Rechazo: Pesaje`) |
| `peso_teorico` | `float` | Opcional (insumo) | `strip()`. Si se evalúa pesaje, debe ser `float > 0`. | `FilaLoteInvalidaError`: `RL-04` (`Rechazo: Pesaje`) |
| `certificado_calidad` | `str` | Obligatorio en evaluación `RL-05` | `strip().upper()`. Columna ausente o vacía (`""`) se normaliza a `"AUSENTE"`. Si es `"PENDIENTE"` o `"AUSENTE"`, se rechaza. | `FilaLoteInvalidaError`: `RL-05` (`Rechazo: Cuarentena`) |

---

## 5. Archivo CSV de Rechazos de Lote (p. ej. `examples/rechazos_ejemplo.csv`)

Generado de forma atómica cuando se invoca `cargar_lote(..., ruta_rechazos=...)`.

| Columna | Tipo en Python | Obligatoriedad | Descripción y Regla de Generación | Excepción que Lanza |
| :--- | :--- | :--- | :--- | :--- |
| `linea` | `int` | Obligatorio | Número de línea en el CSV de lote (`lector.line_num`, contando cabecera como línea 1). | N/A (archivo de salida) |
| `identificador` | `str` | Obligatorio | `id_pedido` limpio; si está vacío, usa `codigo_lote` o `""`. | N/A (archivo de salida) |
| `regla` | `str` | Obligatorio | Primera regla violada en orden de evaluación (`RL-01`..`RL-05`, `RL-ID`, `RL-CAMPO`, `RL-EST`, `RL-DUP`, `RL-FK`). | N/A (archivo de salida) |
| `reglas` | `str` | Obligatorio | Todas las reglas violadas por la fila concatenadas con `";"` en orden numérico (p. ej. `"RL-01;RL-02;RL-03;RL-04;RL-05"`). | N/A (archivo de salida) |
| `motivo` | `str` | Obligatorio | Mensajes descriptivos de todas las violaciones detectadas en la fila separados por `"; "`. | N/A (archivo de salida) |
| `subestado_rechazo` | `str` | Obligatorio | Constante oficial asociada a la regla primaria (`Rechazo: Cuarentena`, `Rechazo: Formato Inválido`, `Rechazo: Red de Frío`, `Rechazo: Pesaje`, `Rechazo: Datos Inválidos`, `Rechazo: Estado Inválido`, `Rechazo: Descarte`). | N/A (archivo de salida) |
