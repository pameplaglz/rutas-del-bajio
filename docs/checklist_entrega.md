# Lista de Verificación Final (Sección 9 de la Guía `Proyecto_P2`)

> **Criterio de marcado (Directriz 4.2):** Únicamente se marcan con `[x]` los puntos verificables automáticamente mediante comandos reales sobre el repositorio. Los puntos que dependen del documento PDF/Word, capturas de pantalla, firmas o acciones en las cuentas de GitHub de cada integrante permanecen en `[ ]` para verificación humana antes de la entrega.

---

## A. Verificación Técnica Automatizada en el Repositorio (Comandos Reales)

- [x] **Suite de pruebas automatizadas 100% en verde:** `pytest -v -ra` ejecuta **138 ítems** distribuidos en **32 criterios únicos (`C-01` a `C-32`)** con resultado `138 passed` (`125 unitaria`, `10 integracion`, `3 aceptacion`).
- [x] **Cobertura de código superior a la meta ($\ge 90\%$):** `pytest --cov=. --cov-report=term-missing` reporta **99% de cobertura global** (`errores.py`: **100%**, `modelos.py`: **100%**, `gestores.py`: **97%**, `main.py`: **98%**).
- [x] **Pruebas de mutación verificadas sin sobrevivientes:** `python scripts/mutar.py` evalúa **23 mutantes (`M-01` a `M-23`)** con resultado **23 de 23 eliminados (`100.0% Mutation Score`)**.
- [x] **Archivos de ejemplo reales generados por el flujo:** `python main.py` genera [`examples/lote_ejemplo.csv`](../examples/lote_ejemplo.csv) (10 filas leídas: 2 aceptadas y 8 rechazadas) y [`examples/rechazos_ejemplo.csv`](../examples/rechazos_ejemplo.csv).
- [x] **Consistencia estricta de nombres en el repositorio:** los nombres de entidades (`Cliente`, `Ruta`, `Pedido`), los 7 estados oficiales (`Registrado`, `En Validación`, `Aprobado`, `En Preparación`, `En Ruta`, `Entregado`, `Cancelado`; 0 ocurrencias de `"En RUTA"`), columnas CSV (`CAMPOS_VALIDOS == CAMPOS_CSV`) e identificadores `C-01`..`C-32` son idénticos en código, `tests/`, `README.md` y `docs/`.

---

## B. Lista de Verificación Oficial — Sección 9 de `Proyecto_P2`

### 1. Uso ético de la IA
- [ ] El Anexo A tiene los seis apartados oficiales, en el orden indicado:
  1. Introducción
  2. Inventario de herramientas de IA utilizadas
  3. Descripción detallada de las fases del trabajo
  4. Registro detallado de prompts empleados
  5. Consideraciones éticas finales
  6. Declaración de originalidad
- [ ] Cada integrante registró sus prompts reales con captura legible y describió su validación humana con hechos concretos (qué se modificó, qué se descartó).
- [ ] No hay uso en rojo: ningún capítulo, conclusión o dato fue generado por una IA.

### 2. Profundidad técnica
- [ ] Cada capítulo explica decisiones con argumentos y alternativas descartadas, no solo describe (p. ej. completar la columna `Razón de Negocio` de [`docs/tabla_transiciones.md`](tabla_transiciones.md) y resolver las disyuntivas de [`docs/pendientes_humano.md`](pendientes_humano.md)).
- [ ] Las cifras de pruebas en el reporte escrito coinciden con las capturas con fecha visible del Anexo C (`138 passed`, `99%` cobertura, `23/23` mutantes eliminados).
- [ ] Los nombres de entidades, estados y criterios son iguales en los cuatro capítulos del Word/PDF y en los anexos (sustituir cualquier aparición residual de `"En RUTA"` o `"Rechazado"` como estado de `Pedido` en el documento Word).

### 3. Originalidad y formato
- [ ] Hay portada institucional (elementos del Anexo A.1 de la guía) y el formato visual es coherente en todo el documento.
- [ ] Cada rol incluye una propuesta de mejora fundamentada en las conclusiones, más una conclusión general.

### 4. Estructura y redacción
- [ ] Todo el texto del reporte está redactado en tercera persona o en voz impersonal (sin primera persona singular ni plural).
- [ ] Tablas y figuras están numeradas consecutivamente (`Tabla 1`, `Figura 1`), tituladas arriba, con fuente o nota abajo, y citadas en el texto antes de aparecer.
- [ ] Cada capítulo tiene nota inicial de redactor y revisor según el circuito de revisión cruzada (Sección 5.6 de la guía) y declaración de autoría firmada (Anexo A.3):
  * Capítulo 1 (Arquitecto) $\rightarrow$ revisa Documentador.
  * Capítulo 2 (Desarrollador CRUD) $\rightarrow$ revisa Arquitecto.
  * Capítulo 3 (Encargada de Pruebas) $\rightarrow$ revisa Desarrollador CRUD.
  * Capítulo 4 y conclusión general (Documentador) $\rightarrow$ revisa Encargada de Pruebas.
- [ ] Se revisó ortografía y gramática en todo el documento.

### 5. Fuentes
- [ ] Toda cita del texto aparece en la lista de referencias y viceversa, en formato APA 7.
- [ ] Cada integrante aportó al menos una fuente confiable que no es una IA, y cada herramienta de IA declarada tiene su referencia estructurada en APA 7.

### 6. Entrega
- [ ] El repositorio tiene el commit final exacto (`git commit --allow-empty -m "v-p2 - entrega final"`) y el historial muestra aportes reales de los integrantes (o, si alguna sesión se trabajó en conjunto desde una sola cuenta, se declara con transparencia en el Capítulo 4.5 y en el Anexo D).
- [ ] Cualquier integrante puede explicar cualquier sección del reporte y del código (defensa oral aleatoria).
