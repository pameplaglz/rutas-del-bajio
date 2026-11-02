# Límites del Entorno de Pruebas (`docs/limites.md`)

Este documento declara con transparencia los escenarios técnicos y operativos que **no** están cubiertos por la suite actual de `pytest`, explicando el motivo técnico y de alcance del curso.

1. **Concurrencia y acceso multi-proceso a archivos CSV:**
   - **Qué no se probó:** Escrituras simultáneas desde múltiples hilos o procesos sobre `clientes.csv`, `rutas.csv` o `pedidos.csv`.
   - **Por qué:** Aunque `_guardar_csv_atomico` utiliza archivos temporales y `os.replace` para evitar archivos truncados a mitad de escritura, el sistema no implementa bloqueos de archivo (`file locks`) ni transacciones ACID de base de datos, ya que el alcance del Parcial 2 se centra en persistencia plana monousuario.
2. **Volumen masivo de datos (pruebas de estrés y memoria):**
   - **Qué no se probó:** Carga de archivos CSV o lotes con cientos de miles o millones de filas.
   - **Por qué:** Los gestores mantienen la colección completa de objetos en memoria (`self.clientes`, `self.rutas`, `self.pedidos`) y reescriben el archivo completo en cada operación CRUD. La suite prioriza la rapidez de ejecución (`< 1 s`) para retroalimentación continua.
3. **Codificaciones de caracteres distintas de `UTF-8` (`latin-1`, `cp1252`, `UTF-16` con BOM):**
   - **Qué no se probó:** Ingesta de archivos CSV exportados por hojas de cálculo antiguas en codificación `Windows-1252` o `ISO-8859-1`.
   - **Por qué:** El sistema estandariza explícitamente `encoding="utf-8"` en todas las operaciones de lectura y escritura para preservar tildes y caracteres del español (`León`, `En Validación`, `En Preparación`).
4. **Fallas de permisos del sistema operativo o disco lleno (`PermissionError`, `OSError`):**
   - **Qué no se probó:** Simulación de errores de sistema de archivos de bajo nivel cuando el directorio de trabajo es de solo lectura o un proceso externo como Excel mantiene bloqueado el archivo destino en Windows.
   - **Por qué:** Su reproducción depende del sistema operativo anfitrión y requeriría *mocks* artificiales sobre `os.replace` y `open`, fuera del enfoque de pruebas con `tmp_path` reales.
5. **Validación criptográfica o documental de archivos PDF de certificados de calidad (`RL-05`):**
   - **Qué no se probó:** Verificación de existencia física o firma digital de un documento PDF externo para el certificado de calidad.
   - **Por qué:** En el diseño de ingesta CSV del proyecto, la regla `RL-05` se evalúa sobre el campo estructurado `certificado_calidad` (`OK` frente a `PENDIENTE` / `AUSENTE` / vacío) dentro de la fila del lote.
