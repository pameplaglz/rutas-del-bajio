# Decisiones de Dominio Pendientes para Definición del Equipo Humano

> **Importante (Directriz 3.5):** Este documento expone las 5 disyuntivas de diseño detectadas entre las actas preliminares (`Act03_P2`, borradores de tablas) y la implementación final del sistema. **Ninguna de estas decisiones ha sido alterada arbitrariamente**; el equipo humano debe acordar qué postura documentar en los capítulos narrativos del reporte técnico.

---

## (a) Modelado de un pedido inviable por falta de stock o crédito (sin el estado `"Rechazado"` en `Pedido`)

* **Contexto en artefactos previos:** En la Tabla 1 de `Act03_P2` aparecía la transición `En Validación -> Rechazado` cuando un pedido carecía de inventario o excedía el límite de crédito.
* **Estado actual en código (`modelos.py`):** Conforme a la unificación estricta del catálogo en **7 estados oficiales** (`Registrado`, `En Validación`, `Aprobado`, `En Preparación`, `En Ruta`, `Entregado`, `Cancelado`), `"Rechazado"` no existe como estado de `Pedido`. Hoy, un pedido en `En Validación` que no aprueba solvencia o stock solo puede transicionar a `Cancelado`.
* **Pregunta para decisión del equipo:**
  * *Opción 1:* Documentar en el reporte que el estado final `Cancelado` absorbe tanto la cancelación a solicitud del cliente como la cancelación operativa por falta de stock/crédito durante las fases previas a `En Preparación`.
  * *Opción 2:* Documentar esta restricción como una limitación conocida del catálogo unificado de 7 estados y proponer en trabajo futuro un atributo de motivo de cancelación (`motivo_cancelacion`).

---

## (b) Nomenclatura del subestado `"Rechazo: Cuarentena"` en las reglas `RL-01` y `RL-05`

* **Contexto operativo:** En logística e inocuidad industrial (ISO/HACCP), una **cuarentena** es una retención temporal de lote para inspección o aclaración documental (como indica la Tabla 2 de `Act03_P2` para `RL-05`: *"Bloqueo temporal del lote en cuarentena hasta aclaración"*), mientras que un **rechazo** implica el descarte definitivo en recepción. Además, `RL-01` (lote caducado) y `RL-05` (certificado pendiente/ausente) comparten actualmente la misma constante `SUBESTADO_CUARENTENA = "Rechazo: Cuarentena"`.
* **Estado actual en código (`errores.py`):** Se conserva el texto literal `"Rechazo: Cuarentena"` para no romper compatibilidad con las pruebas existentes.
* **Pregunta para decisión del equipo:**
  * *Opción 1:* Mantener `"Rechazo: Cuarentena"` aclarando en el reporte que, a efectos de la ingesta automatizada (`cargar_lote`), toda fila que no ingresa a `pedidos.csv` se clasifica bajo el prefijo `"Rechazo: ..."` indicando el destino físico del insumo no admitido (almacén de cuarentena).
  * *Opción 2:* Acordar si en una versión futura `RL-01` (caducado) debería mapear a `"Rechazo: Descarte"` y `RL-05` (sin certificado) a `"Retención: Cuarentena"`.

---

## (c) Pertenencia de `Salamanca` al catálogo de destinos válidos (`CIUDADES_BAJIO`)

* **Contexto en artefactos previos:** En algunos enunciados de la Etapa 1 se mencionaban ejemplos con Irapuato, Celaya y Guanajuato, mientras que el diccionario de datos del reporte técnico (Sección 1.2 y 2.2) incluye explícitamente a `Salamanca`.
* **Estado actual en código (`modelos.py`):** `CIUDADES_BAJIO = ("León", "Irapuato", "Celaya", "Salamanca", "Guanajuato")`, por lo que `Salamanca` es un destino válido tanto en `Ruta` como en `Pedido`.
* **Pregunta para decisión del equipo:**
  * Confirmar que en todas las tablas del reporte escrito se liste de forma uniforme el catálogo completo de 5 ciudades (`León` como origen fijo de ruta, y `Irapuato`, `Celaya`, `Salamanca`, `Guanajuato` como destinos).

---

## (d) Alcance de `"log de error"` en `C-17` (`RL-02`) y `"notificación a QA"` en `C-18` (`RL-03`)

* **Contexto en artefactos previos:** En la Tabla 3 de `Act03_P2`, el resultado esperado de `C-05` (hoy `C-17`, `RL-02`) mencionaba *"emite log de error"* y el de `C-06` (hoy `C-18`, `RL-03`) mencionaba *"notificación a QA"*.
* **Estado actual en código (`gestores.py` y `docs/matriz_criterios.md`):** El sistema registra cada rechazo de forma estructurada en `ReporteLote.rechazadas` (`RegistroRechazo`) y en el archivo auditable `rechazos.csv` (`linea`, `identificador`, `regla`, `reglas`, `motivo`, `subestado_rechazo`), sin invocar al módulo `logging` de Python ni enviar notificaciones externas a un sistema de QA. En `docs/matriz_criterios.md`, los resultados esperados de `C-17` y `C-18` ya están alineados con el comportamiento real del código.
* **Pregunta para decisión del equipo:**
  * *Opción 1:* Actualizar la redacción de la tabla en el documento Word del reporte para que coincida con `docs/matriz_criterios.md` (registro en `ReporteLote.rechazadas` y `rechazos.csv`, dejando las alertas externas a QA como alcance excluido según `docs/limites.md`).
  * *Opción 2:* Solicitar la adición explícita de llamadas a `logging.warning(...)` / `logging.error(...)` dentro de `cargar_lote()` si el equipo desea evidenciar salida en el logger estándar.

---

## (e) Criterio `C-20` (`RL-05`): validación de la columna `certificado_calidad` vs. existencia de un archivo PDF

* **Contexto en artefactos previos:** En la Tabla 2 de `Act03_P2` la condición de `RL-05` se definió como *"Documento en estado PENDIENTE o AUSENTE"*, pero en la Tabla 3 (`C-08`, hoy `C-20`) el escenario de entrada decía *"Recepción de lote sin archivo PDF de certificado adjunto"*.
* **Estado actual en código (`gestores.py`):** `validar_insumo_lote()` evalúa el valor de la columna `certificado_calidad` del CSV de lote (rechazando cuando la columna está ausente, vacía `""`, `"PENDIENTE"` o `"AUSENTE"`, y aceptando `"OK"`), sin verificar archivos `.pdf` en el sistema de archivos.
* **Pregunta para decisión del equipo:**
  * Unificar la redacción de `C-20` en el reporte técnico para que refiera a la columna `certificado_calidad` del CSV de lote (en concordancia con la Tabla 2 de `Act03_P2` y con `docs/matriz_criterios.md`), evitando afirmar que el backend inspecciona archivos PDF físicos.
