# Diagramas de Arquitectura y Máquina de Estados (`Mermaid`)

## Figura 1 — Diagrama de Clases y Relaciones del Dominio y Gestores

Representación exacta de las clases implementadas en [`modelos.py`](../modelos.py), [`gestores.py`](../gestores.py) y [`errores.py`](../errores.py), incluyendo atributos tipados (PEP 484), métodos públicos y privados reales, y cardinalidades (`Cliente 1 ── 0..* Pedido` obligatoria; `Ruta 0..1 ── 0..* Pedido` opcional).

```mermaid
classDiagram
    direction TB

    class Cliente {
        +Tuple~str~ CAMPOS_VALIDOS$
        +str id_cliente
        +str nombre
        +str ciudad
        +str telefono
        +to_dict() Dict~str, Any~
        +from_dict(data: Dict~str, Any~)$ Cliente
        +__str__() str
        +__repr__() str
    }

    class Ruta {
        +Tuple~str~ CAMPOS_VALIDOS$
        +str id_ruta
        +str origen
        +str destino
        +float distancia_km
        +float tiempo_estimado
        +str transportista
        +to_dict() Dict~str, Any~
        +from_dict(data: Dict~str, Any~)$ Ruta
        +__str__() str
        +__repr__() str
    }

    class Pedido {
        +Tuple~str~ CAMPOS_VALIDOS$
        +str id_pedido
        +str id_cliente
        +str producto
        +int cantidad
        +str origen
        +str destino
        +str fecha_pedido
        -str _estado
        +str id_ruta
        +estado() str
        +puede_transicionar_a(nuevo_estado: str) bool
        +transicionar_estado(nuevo_estado: str) None
        +to_dict() Dict~str, Any~
        +from_dict(data: Dict~str, Any~, restaurar_estado: bool)$ Pedido
        +__str__() str
        +__repr__() str
    }

    class GestorClientes {
        +List~str~ CAMPOS_CSV$
        +str archivo_csv
        +List~Cliente~ clientes
        -List~GestorPedidos~ _gestores_pedidos
        +registrar_gestor_pedidos(gestor_pedidos: GestorPedidos) None
        +cargar() None
        +guardar() None
        +buscar_cliente(id_cliente: str) Optional~Cliente~
        +crear_cliente(cliente: Cliente) None
        +listar_clientes() List~Cliente~
        +listar_clientes_por_ciudad(ciudad: str) List~Cliente~
        +actualizar_cliente(id_cliente: str, **cambios: Any) bool
        +eliminar_cliente(id_cliente: str) bool
    }

    class GestorRutas {
        +List~str~ CAMPOS_CSV$
        +str archivo_csv
        +List~Ruta~ rutas
        -List~GestorPedidos~ _gestores_pedidos
        +registrar_gestor_pedidos(gestor_pedidos: GestorPedidos) None
        +cargar() None
        +guardar() None
        +buscar_ruta(id_ruta: str) Optional~Ruta~
        +crear_ruta(ruta: Ruta) None
        +listar_rutas() List~Ruta~
        +listar_rutas_por_destino(destino: str) List~Ruta~
        +actualizar_ruta(id_ruta: str, **cambios: Any) bool
        +eliminar_ruta(id_ruta: str) bool
    }

    class GestorPedidos {
        +List~str~ CAMPOS_CSV$
        +List~str~ CAMPOS_DESCARTADOS_CSV$
        +str archivo_csv
        +str archivo_descartados_csv
        +Optional~GestorClientes~ gestor_clientes
        +Optional~GestorRutas~ gestor_rutas
        +List~Pedido~ pedidos
        +List~RegistroDescarte~ descartados
        -_respaldar_descartados() None
        -_validar_referencias_y_ruta(id_cliente: str, id_ruta: str, origen: str, destino: str) None
        +cargar() None
        +guardar() None
        +buscar_pedido(id_pedido: str) Optional~Pedido~
        +crear_pedido(pedido: Pedido) None
        +listar_pedidos() List~Pedido~
        +listar_pedidos_por_estado(estado: str) List~Pedido~
        +listar_pedidos_por_cliente(id_cliente: str) List~Pedido~
        +cambiar_estado_pedido(id_pedido: str, nuevo_estado: str) Pedido
        +actualizar_pedido(id_pedido: str, **cambios: Any) bool
        +eliminar_pedido(id_pedido: str) bool
        +cargar_lote(ruta_lote: str, ruta_rechazos: Optional~str~, fecha_actual: Optional~str~) ReporteLote
    }

    class RegistroDescarte {
        +int linea
        +str id_pedido
        +str motivo
        +Dict~str, Any~ datos_fila
    }

    class RegistroRechazo {
        +int linea
        +str identificador
        +str regla
        +str motivo
        +str subestado_rechazo
        +str reglas
    }

    class ReporteLote {
        +int leidas
        +int aceptadas
        +List~RegistroRechazo~ rechazadas
        +Dict~str, int~ por_subestado
    }

    Cliente "1" <-- "0..*" Pedido : id_cliente (FK obligatoria)
    Ruta "0..1" <-- "0..*" Pedido : id_ruta (FK opcional)
    GestorClientes "1" o-- "0..*" Cliente : gestiona
    GestorRutas "1" o-- "0..*" Ruta : gestiona
    GestorPedidos "1" o-- "0..*" Pedido : gestiona
    GestorPedidos "1" *-- "0..*" RegistroDescarte : registra
    GestorPedidos ..> ReporteLote : genera en cargar_lote()
    ReporteLote "1" *-- "0..*" RegistroRechazo : contiene
    GestorPedidos "0..*" <--> "0..1" GestorClientes : integridad referencial
    GestorPedidos "0..*" <--> "0..1" GestorRutas : integridad referencial
```

### Figura 1b — Diagrama Entidad-Relación (`erDiagram`) de Persistencia CSV

```mermaid
erDiagram
    CLIENTES ||--o{ PEDIDOS : "id_cliente (FK obligatoria)"
    RUTAS |o--o{ PEDIDOS : "id_ruta (FK opcional)"

    CLIENTES {
        str id_cliente PK
        str nombre
        str ciudad
        str telefono
    }

    RUTAS {
        str id_ruta PK
        str origen
        str destino
        float distancia_km
        float tiempo_estimado
        str transportista
    }

    PEDIDOS {
        str id_pedido PK
        str id_cliente FK
        str producto
        int cantidad
        str origen
        str destino
        str fecha_pedido
        str estado
        str id_ruta FK
    }
```

---

## Figura 2 — Máquina de Estados de `Pedido` (7 Estados Oficiales)

Representación exacta de `ESTADOS_VALIDOS` y `TRANSICIONES_PERMITIDAS` definidos en [`modelos.py`](../modelos.py) (líneas 39–57).
* **Nota técnica:** Las reglas de limpieza de lote (`RL-01` a `RL-05`) se evalúan en la ingesta (`validar_insumo_lote` / `cargar_lote`) **antes** de instanciar `Pedido`; por tanto, no forman parte de las transiciones de `Pedido`. Tampoco existen pseudo-acciones `entry/` o `exit/` en el código.

```mermaid
stateDiagram-v2
    direction TB

    state "Registrado" as Registrado
    state "En Validación" as EnValidacion
    state "Aprobado" as Aprobado
    state "En Preparación" as EnPreparacion
    state "En Ruta" as EnRuta
    state "Entregado" as Entregado
    state "Cancelado" as Cancelado

    [*] --> Registrado : Pedido() / crear_pedido() / cargar_lote()

    Registrado --> EnValidacion : transicionar_estado("En Validación")
    Registrado --> Cancelado : transicionar_estado("Cancelado")

    EnValidacion --> Aprobado : transicionar_estado("Aprobado")
    EnValidacion --> Cancelado : transicionar_estado("Cancelado")

    Aprobado --> EnPreparacion : transicionar_estado("En Preparación")
    Aprobado --> Cancelado : transicionar_estado("Cancelado")

    EnPreparacion --> EnRuta : transicionar_estado("En Ruta")

    EnRuta --> Entregado : transicionar_estado("Entregado")

    Entregado --> [*]
    Cancelado --> [*]
```
