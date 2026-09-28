# Incendios en Argentina · Córdoba 2024

Proyecto de ciencia de datos y sitio narrativo en español. La serie nacional del **Anuario de Estadística Forestal, edición 2025 (incendios 2024)** cubre 2018–2024. El análisis detallado de Córdoba 2024 usa por separado el **Informe anual de áreas afectadas** de DirGR e IDECOR (febrero 2025). El sitio funciona como página estática, sin cuenta, claves ni API en tiempo de ejecución.

## Qué cuenta cada dato

| Dato | Unidad de una fila | Interpretación |
| --- | --- | --- |
| Serie nacional | Año calendario | Total de incendios **reportados por jurisdicciones con información** y superficie reportada; el total incluye Parques Nacionales como fila propia. |
| Jurisdicciones 2024 | Provincia / CABA / Parques Nacionales | `sin_informacion` no es cero. Parques Nacionales no se suman otra vez a cada provincia. |
| Córdoba mensual | Mes calendario de 2024 | Incendios y hectáreas del mapeo provincial, con una delimitación territorial que excluye parte del noreste de Córdoba. |
| Córdoba departamental | Departamento | Un incendio que cruza departamentos se cuenta en cada uno: la suma es 606 registros departamentales, frente a 586 eventos provinciales. Las hectáreas sí se distribuyen entre departamentos. |
| Imagen | Producto satelital publicado por CONAE | Documenta **El Durazno al 3/9/2024**. Su superficie publicada ese día (10.500 ha) es una estimación temporal del evento; el informe posterior provincial consigna 10.644 ha para el incendio iniciado el 2/9. No representa el total de Córdoba. |
| Detección FIRMS | Centro de píxel con anomalía térmica | No es necesariamente un incendio único ni un polígono de área quemada. El visor muestra observaciones reales solamente después del cruce validado con polígonos IDECOR y fechas. |

## Resultados trazables

- Anuario nacional 2024: **5.175 incendios**, **392.277 ha**, con **5 de 24 jurisdicciones provinciales/CABA sin información**. Córdoba: **582 incendios y 103.325 ha**; Formosa tiene más incendios reportados (**1.028**), Córdoba la mayor superficie **entre jurisdicciones que informaron**. Los totales nacionales agregan **104 incendios y 40.784 ha de Parques Nacionales**.
- Informe provincial Córdoba 2024: **586 eventos y 103.327 ha**. Septiembre: **177 eventos y 78.298 ha**, aproximadamente 75,8 % de la superficie del informe. El resumen inicial del PDF imprime `103.237` ha, pero el cuerpo y las tablas suman `103.327`; documentamos la discrepancia tipográfica y usamos la tabla mensual verificada.
- Las cifras provinciales y nacionales de Córdoba difieren **4 eventos y 2 ha**; sus coberturas y procesos de elaboración difieren. No se suman ni se sustituyen entre sí.

Los archivos en [`data/source/`](data/source/) son **transcripciones manuales** de tablas y gráfico publicados en PDF, con páginas exactas en [`data/sources.json`](data/sources.json). La captura está separada de la transformación para poder corregir un error sin tocar el diseño. La serie 2018–2024 no implica cobertura geográfica idéntica: el proyecto **solo auditó fila por fila el año 2024** y no publica una matriz provincial anterior como si ya estuviera validada.

## Ejecutar

```bash
python3 scripts/build_data.py
python3 -m http.server 8000 --directory site
```

Abrir `http://localhost:8000`. No hace falta instalar paquetes. `build_data.py` valida claves, duplicados, cifras publicadas, 24 jurisdicciones, 5 ausencias, suma mensual y suma departamental. Genera `site/data/analysis.json` y tres CSV descargables. Se incluyen archivos generados para que GitHub Pages, Manus y cualquier hosting estático funcionen inmediatamente después de clonar o subir el ZIP. Ejecutar `python3 -m unittest discover -s tests` para comprobar las relaciones entre fuentes y las agregaciones.

## Estructura

```text
data/source/       Transcripciones y metadatos de dos eventos, con evidencia de páginas
data/sources.json  Inventario de fuentes, acceso, imágenes y limitaciones
scripts/           Normalización, descarga NASA y cruce espacial sin dependencias externas
site/              Página estática, gráficos SVG interactivos y CSV públicos
tests/             Controles de agregación y valores de referencia
MANUS.md           Instrucciones para conectar el repositorio con Manus
```

## Auditoría y límites

La matriz `year × jurisdiction` exportada distingue `reportado`, `sin_informacion` y `no_auditado`. Para 2018–2023 contiene `no_auditado`: solo es segura la serie de totales publicada en el anuario, no el supuesto de que todas las provincias hayan informado. En 2024 `s/i` del anuario significa sin información; `—` dentro de una fila informada denota ausencia en esa subcategoría, **no se aplica a jurisdicciones enteras**. El anuario divide los totales por vegetación; la página evita atribuir causas de incendio a una anomalía térmica.

El informe IDECOR estudia un área amplia pero **excluye parte del noreste provincial** (bañados del Río Dulce y norte de Mar de Ansenuza, p. 10). Los criterios de mapeo mejoraron durante el proyecto (unidad mínima de 2 ha en 2024). Hay discordancias menores dentro del PDF (resumen `103.237` frente a tabla y cuerpo `103.327`; algunos renglones de su tabla de los diez mayores indican 2023 dentro de la sección 2024), por lo que el MVP no reproduce esa tabla completa. El mapa de IDECOR se enlaza como fuente de polígonos, sin reproducirlos como si se hubieran procesado aquí.

La foto pública de CONAE se carga desde Argentina.gob.ar y puede depender de la disponibilidad del servidor; el enlace al artículo funciona como referencia alternativa. CONAE no especifica sensor, bandas ni licencia de reutilización de **esa imagen** en la nota; por eso no le atribuimos esos metadatos ni la guardamos dentro del repositorio. Para obtener una escena propia comparable antes/después: elegir el evento y extensión exacta, descargar bandas y metadatos originales con condiciones de uso explícitas (CONAE o Copernicus), controlar nubosidad, reproyectar y mantener la misma extensión, fechas y crédito. NASA Worldview permite explorar escenas MODIS históricas; FIRMS sirve para **detecciones**, no como reemplazo de imagen óptica de alta resolución.

## Incorporar detecciones NASA FIRMS

**Estado de esta entrega:** se cruzaron 6.697 observaciones NASA VIIRS NOAA-20 con los KML oficiales de IDECOR aportados para El Durazno y Capilla del Monte. El resultado contiene 256 y 1.099 detecciones dentro de cada polígono y de los primeros cinco días locales, respectivamente. La clave FIRMS **no está ni en el ZIP ni en los archivos del sitio**. Los CSV brutos y KML quedan excluidos del repositorio; el sitio incluye únicamente el resultado derivado y los contornos utilizados para poder auditarlo.

1. En tu computadora, definí `FIRMS_MAP_KEY` temporalmente en una terminal. En PowerShell: `$env:FIRMS_MAP_KEY = Read-Host 'Clave FIRMS'`; en Linux/macOS: `read -rs FIRMS_MAP_KEY; export FIRMS_MAP_KEY`. **No agregues su valor al repositorio ni a Manus.** La clave permite consultar puntos FIRMS, no descargar por sí sola imágenes ópticas.
2. Ejecutá `py scripts/fetch_firms.py` en Windows (`python3` en Linux/macOS). Consulta VIIRS NOAA-20 **Standard Processing** en un rectángulo exploratorio de Córdoba (`-66.0,-35.2,-61.5,-29.2`), para 2–7 y 19–24 de septiembre de 2024 (UTC). El CSV bruto se guarda en `data/raw_downloads/`, excluido por `.gitignore`.
3. Desde el [mapa oficial IDECOR 2024](https://mapascordoba.gob.ar/viewer/mapa/505), descargá ambos KML, verificando El Durazno (02/09; 10.644 ha) y Capilla del Monte (19/09; 42.046 ha). Copialos como `data/private/el_durazno.kml` y `data/private/capilla_del_monte.kml`. Ejecutá `py scripts/convert_idecor_kml.py --durazno data/private/el_durazno.kml --capilla data/private/capilla_del_monte.kml`. La conversión verifica sitio, fecha y área; conserva piezas y agujeros en WGS84.
4. Ejecutá `py scripts/match_firms.py --raw data/raw_downloads/firms_viirs_noaa20_sp_cordoba_2024_event_windows.csv --polygons data/private/idecor_eventos_2024.geojson`. Filtra cada punto por ubicación dentro del área oficial y por los cinco primeros días en hora de Córdoba (UTC−3). Genera `site/data/thermal_matches.json` y `site/data/detecciones_verificadas_2024.csv`.
5. Publicá únicamente el resultado derivado junto al sitio. Para incorporar esta versión, reemplazá los archivos del proyecto por los del ZIP actualizado y hacé un nuevo commit y push. El visor muestra los dos eventos, sus contornos, detecciones y CSV.

El polígono corresponde al **área final**, mientras que los puntos son observaciones de los **primeros cinco días**. El resultado indica coincidencia espacial y temporal compatible con el evento documentado, **no demuestra la causa de cada anomalía**. No sumar píxeles para obtener hectáreas ni sumar observaciones para contar incendios. Las nubes, la hora de paso del satélite y el umbral de detección también afectan cuántos puntos se ven. Un resultado sin puntos puede reflejar ausencia de observaciones, no ausencia de incendio. Se usa un sensor y producto para evitar duplicar detecciones de varias plataformas. El valor FRP (si viene en el CSV) se conserva como atributo de potencia radiativa, sin convertirlo en severidad del incendio.

## Cómo explicar el proyecto en una entrevista

> “Reuní una serie publicada para Argentina y audité por separado las jurisdicciones de 2024. Vi que el total nacional incluye Parques Nacionales y que cinco jurisdicciones aparecen sin información, así que evité comparar el total como si tuviera cobertura completa. Crucé la lectura con un informe provincial independiente para estudiar la distribución mensual y departamental de Córdoba. Dejo las transcripciones, el pipeline, las comprobaciones y los vínculos a las imágenes originales en GitHub.”

### Glosario

- **Incendio reportado:** episodio registrado por un organismo según su método.
- **Superficie afectada:** hectáreas informadas; no se calcula contando detecciones térmicas.
- **Anomalía térmica:** observación satelital de temperatura anómala en un píxel, potencialmente asociada a fuego.
- **s/i:** sin información enviada al anuario; no equivale a cero.

## Próximos pasos

Auditar las 24 jurisdicciones para cada año anterior antes de añadir rankings históricos provinciales. Exportar y verificar los polígonos de IDECOR; ejecutar el cruce NASA y revisar manualmente los resultados. Incorporar imágenes ópticas NASA o Sentinel con fecha, coordenadas, licencia, nubosidad y extensión común.

Autor: Fabricio Velez. Fuentes y enlaces completos: [`data/sources.json`](data/sources.json). Fecha de consulta: **2026-09-28**.
