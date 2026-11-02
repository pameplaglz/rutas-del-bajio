# Catálogo de Operaciones del Sistema

Inventario completo de clases, métodos y funciones públicas/privadas en [`modelos.py`](../modelos.py), [`gestores.py`](../gestores.py) y [`main.py`](../main.py), con sus tipos de retorno (PEP 484) y excepciones reales.

---

## 1. Módulo `modelos.py`

| Entidad / Función | Método / Firma | Qué hace | Qué devuelve | Excepción que lanza y condición |
| :--- | :--- | :--- | :--- | :--- |
| Función de módulo | `normalizar_ciudad(nombre_ciudad: str)` | Aplica `strip()` y reemplaza `"Leon"` por `"León"`. | `str` | Ninguna |
| `Cliente` | `__init__(id_cliente: str, nombre: str, ciudad: str, telefono: str)` | Inicializa y valida un cliente aplicando `strip()` y `normalizar_ciudad()`. | `None` | `ValueError` si cualquiera de los 4 atributos queda vacío |
| `Cliente` | `to_dict()` | Serializa la instancia a diccionario con claves exactas de `CAMPOS_VALIDOS`. | `Dict[str, Any]` | Ninguna |
| `Cliente` | `from_dict(data: Dict[str, Any])` | Reconstruye un `Cliente` desde un diccionario con claves en minúsculas exactas. | `Cliente` | `KeyError` si falta una clave; `ValueError` si un valor es vacío |
| `Ruta` | `__init__(id_ruta: str, origen: str, destino: str, distancia_km: float, tiempo_estimado: float, transportista: str)` | Inicializa una ruta validando `origen == "León"`, `destino` en catálogo del Bajío (`!= "León"`), `distancia_km > 0` y `tiempo_estimado > 0`. | `None` | `ValueError` si `id_ruta` o `transportista` son vacíos, `origen != "León"`, `destino` inválido, o valores numéricos son `bool` o `<= 0` |
| `Ruta` | `to_dict()` | Serializa la instancia de `Ruta` a diccionario. | `Dict[str, Any]` | Ninguna |
| `Ruta` | `from_dict(data: Dict[str, Any])` | Reconstruye una `Ruta` desde un diccionario CSV con claves en minúsculas. | `Ruta` | `KeyError` si falta una clave; `ValueError` si falla conversión a `float` o validación de dominio |
| `Pedido` | `__init__(..., estado: str = "Registrado", id_ruta: str = "", *, _restaurar_estado: bool = False)` | Inicializa un pedido validando atributos, `cantidad` entera positiva (no `bool`), `origen`/`destino` en `CIUDADES_BAJIO` (`origen != destino`), fecha `YYYY-MM-DD` y estado inicial `"Registrado"` (salvo `_restaurar_estado=True`). | `None` | `ValueError` por campos vacíos, cantidad no entera/`<=0`, ciudades fuera del catálogo o iguales, fecha inválida o estado fuera de `ESTADOS_VALIDOS`; `ErrorTransicionEstado` si `_restaurar_estado=False` y `estado != "Registrado"` |
| `Pedido` | `estado` (`@property`) | Propiedad de solo lectura que expone `self._estado`. | `str` | `AttributeError` si se intenta asignar directamente (`pedido.estado = ...`) |
| `Pedido` | `puede_transicionar_a(nuevo_estado: str)` | Consulta en `TRANSICIONES_PERMITIDAS` si el cambio de `self._estado` a `nuevo_estado` es válido. | `bool` | Ninguna |
| `Pedido` | `transicionar_estado(nuevo_estado: str)` | Cambia `self._estado` a `nuevo_estado` si pertenece a `ESTADOS_VALIDOS` y la transición está permitida. | `None` | `ValueError` si `nuevo_estado` no está en `ESTADOS_VALIDOS`; `ErrorTransicionEstado` si la transición está prohibida |
| `Pedido` | `to_dict()` | Serializa el pedido a diccionario para persistencia CSV. | `Dict[str, Any]` | Ninguna |
| `Pedido` | `from_dict(data: Dict[str, Any], *, restaurar_estado: bool = True)` | Reconstruye un `Pedido` desde diccionario CSV; por defecto permite restaurar cualquier estado válido del catálogo. | `Pedido` | `KeyError`, `ValueError` o `ErrorTransicionEstado` |

---

## 2. Módulo `gestores.py`

| Gestor / Función | Método / Firma | Qué hace | Qué devuelve | Excepción que lanza y condición |
| :--- | :--- | :--- | :--- | :--- |
| Función auxiliar | `_guardar_csv_atomico(ruta_destino, encabezados, filas)` | Escribe las filas en un archivo temporal en el mismo directorio (`tempfile.mkstemp`) y reemplaza el destino con `os.replace`. | `None` | `OSError` en caso de error de E/S (limpiando antes el archivo temporal) |
| Función de lote | `validar_insumo_lote(fila: Dict[str, Any], fecha_actual: Optional[str] = None)` | Evalúa las 5 reglas `RL-01`..`RL-05` en orden numérico y acumula todas las violaciones encontradas. | `Dict[str, Any]` | `FilaLoteInvalidaError` (con `regla`, `motivo`, `subestado_rechazo` y lista `reglas`) si se viola al menos una regla; `ValueError` si `fecha_actual` no tiene formato `YYYY-MM-DD` |
| `GestorClientes` | `__init__(archivo_csv: str = "clientes.csv")` | Inicializa la colección en memoria y ejecuta `cargar()`. | `None` | `ErrorArchivoLote` o `ValueError` propagados desde `cargar()` |
| `GestorClientes` | `registrar_gestor_pedidos(gestor_pedidos: GestorPedidos)` | Suscribe una instancia de `GestorPedidos` para verificar integridad referencial antes de eliminar clientes. | `None` | Ninguna |
| `GestorClientes` | `cargar()` | Lee `clientes.csv` si existe; valida que los encabezados sean exactamente `CAMPOS_CSV` e instancia cada `Cliente`. | `None` | `ErrorArchivoLote` si los encabezados no coinciden con `CAMPOS_CSV`; `ValueError` si una fila contiene datos inválidos |
| `GestorClientes` | `guardar()` | Persiste atómicamente `self.clientes` en `self.archivo_csv`. | `None` | `OSError` en caso de fallo de disco |
| `GestorClientes` | `buscar_cliente(id_cliente: str)` | Busca y devuelve el cliente con `id_cliente` coincidente. | `Optional[Cliente]` | Ninguna |
| `GestorClientes` | `crear_cliente(cliente: Cliente)` | Verifica tipo `Cliente` y unicidad de `id_cliente`, agrega a memoria y llama a `guardar()`. | `None` | `TypeError` si no es `Cliente`; `ValueError` si `id_cliente` ya existe |
| `GestorClientes` | `listar_clientes()` | Devuelve una copia superficial de la lista de clientes. | `List[Cliente]` | Ninguna |
| `GestorClientes` | `listar_clientes_por_ciudad(ciudad: str)` | Filtra clientes cuya ciudad coincide (insensible a mayúsculas y normalizando `"Leon"` $\rightarrow$ `"León"`). | `List[Cliente]` | Ninguna |
| `GestorClientes` | `actualizar_cliente(id_cliente: str, **cambios: Any)` | Valida que no haya claves desconocidas, construye el `Cliente` actualizado de forma atómica y persiste. | `bool` (`True` si existía y se actualizó, `False` si no existe) | `ValueError` si se pasan claves desconocidas/no modificables o valores inválidos |
| `GestorClientes` | `eliminar_cliente(id_cliente: str)` | Verifica que ningún `GestorPedidos` registrado tenga pedidos del cliente; si está libre, lo elimina y guarda. | `bool` (`True` si se eliminó, `False` si no existía) | `ErrorIntegridadReferencial` si el cliente tiene pedidos asociados |
| `GestorRutas` | `__init__(archivo_csv: str = "rutas.csv")` | Inicializa la colección de rutas y ejecuta `cargar()`. | `None` | `ErrorArchivoLote` o `ValueError` propagados desde `cargar()` |
| `GestorRutas` | `registrar_gestor_pedidos(gestor_pedidos: GestorPedidos)` | Suscribe una instancia de `GestorPedidos` para verificar integridad referencial antes de eliminar rutas. | `None` | Ninguna |
| `GestorRutas` | `cargar()` | Lee `rutas.csv` si existe; valida encabezados exactos `CAMPOS_CSV` e instancia cada `Ruta`. | `None` | `ErrorArchivoLote` si los encabezados no coinciden con `CAMPOS_CSV`; `ValueError` si una fila es inválida |
| `GestorRutas` | `guardar()` | Persiste atómicamente `self.rutas` en `self.archivo_csv`. | `None` | `OSError` en caso de fallo de disco |
| `GestorRutas` | `buscar_ruta(id_ruta: str)` | Busca y devuelve la ruta con `id_ruta` coincidente. | `Optional[Ruta]` | Ninguna |
| `GestorRutas` | `crear_ruta(ruta: Ruta)` | Verifica tipo `Ruta` y unicidad de `id_ruta`, agrega a memoria y llama a `guardar()`. | `None` | `TypeError` si no es `Ruta`; `ValueError` si `id_ruta` ya existe |
| `GestorRutas` | `listar_rutas()` | Devuelve una copia superficial de la lista de rutas. | `List[Ruta]` | Ninguna |
| `GestorRutas` | `listar_rutas_por_destino(destino: str)` | Filtra rutas cuyo destino coincide con la ciudad normalizada. | `List[Ruta]` | Ninguna |
| `GestorRutas` | `actualizar_ruta(id_ruta: str, **cambios: Any)` | Valida claves permitidas, construye la nueva `Ruta` de forma atómica y persiste en CSV. | `bool` (`True` si existía, `False` si no existe) | `ValueError` si se pasan claves desconocidas o atributos fuera del dominio |
| `GestorRutas` | `eliminar_ruta(id_ruta: str)` | Verifica que ningún `GestorPedidos` registrado tenga pedidos asignados a `id_ruta`; si está libre, la elimina y guarda. | `bool` (`True` si se eliminó, `False` si no existía) | `ErrorIntegridadReferencial` si la ruta tiene pedidos asociados |
| `GestorPedidos` | `__init__(archivo_csv="pedidos.csv", gestor_clientes=None, gestor_rutas=None)` | Se suscribe ante `gestor_clientes` y `gestor_rutas`, inicializa listas `pedidos` y `descartados`, y ejecuta `cargar()`. | `None` | `ErrorArchivoLote` si los encabezados de `pedidos.csv` son inválidos |
| `GestorPedidos` | `cargar()` | Lee `pedidos.csv`, restaura pedidos válidos y envía filas con FK rota o datos inválidos a `self.descartados`, respaldándolas en `<archivo>.descartados.csv`. | `None` | `ErrorArchivoLote` si los encabezados no coinciden con `CAMPOS_CSV` |
| `GestorPedidos` | `guardar()` | Garantiza que `self.descartados` esté respaldado en `<archivo>.descartados.csv` y guarda atómicamente `self.pedidos`. | `None` | `OSError` en caso de fallo de disco |
| `GestorPedidos` | `buscar_pedido(id_pedido: str)` | Busca y devuelve un pedido por `id_pedido`. | `Optional[Pedido]` | Ninguna |
| `GestorPedidos` | `crear_pedido(pedido: Pedido)` | Verifica tipo `Pedido`, estado inicial `"Registrado"`, unicidad de ID, existencia de `id_cliente`/`id_ruta` y coincidencia de trayecto; agrega y guarda. | `None` | `TypeError` si no es `Pedido`; `ErrorTransicionEstado` si `estado != "Registrado"`; `ValueError` si ID duplicado, FK inexistente o trayecto no coincide con la ruta |
| `GestorPedidos` | `listar_pedidos()` | Devuelve una copia superficial de todos los pedidos cargados. | `List[Pedido]` | Ninguna |
| `GestorPedidos` | `listar_pedidos_por_estado(estado: str)` | Devuelve los pedidos cuyo `estado` coincide con el filtro. | `List[Pedido]` | Ninguna |
| `GestorPedidos` | `listar_pedidos_por_cliente(id_cliente: str)` | Devuelve los pedidos asociados a `id_cliente`. | `List[Pedido]` | Ninguna |
| `GestorPedidos` | `cambiar_estado_pedido(id_pedido: str, nuevo_estado: str)` | Ejecuta `pedido.transicionar_estado(nuevo_estado)` y persiste el cambio en CSV. | `Pedido` | `ValueError` si `id_pedido` no existe o `nuevo_estado` no pertenece a `ESTADOS_VALIDOS`; `ErrorTransicionEstado` si la transición está prohibida |
| `GestorPedidos` | `actualizar_pedido(id_pedido: str, **cambios: Any)` | Valida claves permitidas, construye un objeto candidato, valida transición de estado (si incluye `estado`) y FKs/trayecto antes de mutar memoria o CSV. | `bool` (`True` si existía, `False` si no existe) | `ValueError` por clave desconocida, atributo inválido o FK/trayecto inválido; `ErrorTransicionEstado` si intenta una transición prohibida |
| `GestorPedidos` | `eliminar_pedido(id_pedido: str)` | Elimina el pedido de memoria y actualiza el CSV. | `bool` (`True` si se eliminó, `False` si no existía) | Ninguna |
| `GestorPedidos` | `cargar_lote(ruta_lote: str, ruta_rechazos: Optional[str] = None, fecha_actual: Optional[str] = None)` | Valida el archivo de lote, evalúa `RL-01`..`RL-05` y reglas estructurales (`RL-ID`, `RL-CAMPO`, `RL-EST`, `RL-DUP`, `RL-FK`) por fila, guarda pedidos aceptados, escribe `ruta_rechazos` si se indicó y devuelve el `ReporteLote`. | `ReporteLote` | `ErrorArchivoLote` si el archivo no existe, no tiene encabezados, tiene mayúsculas en encabezados o carece de `id_pedido`, `id_cliente` o `cantidad` |

---

## 3. Módulo `main.py`

| Función | Firma | Qué hace | Qué devuelve | Excepción que lanza y condición |
| :--- | :--- | :--- | :--- | :--- |
| Función auxiliar | `_escribir_lote_ejemplo(ruta_lote: str)` | Genera un archivo CSV de lote reproducible con 10 filas (2 válidas y 8 con violaciones a `RL-01`..`RL-05`, reglas estructurales y un caso multi-regla). | `None` | `OSError` si la ruta no es escribible |
| Flujo principal | `ejecutar_flujo_demostracion(directorio_base: Optional[str] = None, fecha_actual: Optional[str] = None)` | Inicializa gestores, registra clientes/rutas/pedidos, ejecuta transiciones válidas, procesa `lote_ejemplo.csv` y genera `rechazos_ejemplo.csv`. | `ReporteLote` | Propaga cualquier excepción no esperada de los gestores |
