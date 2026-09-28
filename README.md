# Incendios en Argentina · Córdoba 2024

Historia de datos sobre incendios reportados en Argentina entre 2018 y 2024, con un análisis de Córdoba en 2024 y un cruce espacial y temporal entre áreas afectadas publicadas por IDECOR y detecciones térmicas de NASA FIRMS. [Sitio estático](site/) listo para publicar desde este repositorio en Vercel.

## Hallazgos

- El Anuario de Estadística Forestal registra **5.175 incendios y 392.277 ha** en 2024. Cinco de las 24 jurisdicciones provinciales/CABA figuran **sin información**; los totales incluyen una fila adicional de Parques Nacionales. Córdoba figura con **582 incendios y 103.325 ha** en esa fuente.
- El informe provincial IDECOR registra **586 eventos y 103.327 ha** en su área de estudio de Córdoba. Septiembre concentra **177 eventos y 78.298 ha**, equivalentes al 75,8 % de la superficie anual del informe. Los dos recuentos de Córdoba provienen de procesos y coberturas distintos; no se suman.
- Entre los dos eventos analizados, el cruce identifica **256 detecciones térmicas en El Durazno** y **1.099 en Capilla del Monte** durante los primeros cinco días locales de cada evento y dentro del polígono final de IDECOR. Son observaciones satelitales coincidentes, **no 1.355 incendios** ni una medida directa de intensidad, daño o hectáreas quemadas.

## Fuentes y procedencia

| Conjunto | Organismo y documento | Uso en el proyecto |
| --- | --- | --- |
| Totales nacionales 2018–2024 y jurisdicciones 2024 | [Anuario de Estadística Forestal, edición 2025, cap. 4](https://www.argentina.gob.ar/sites/default/files/anuario_2024_edicion_2025.pdf) | Serie anual, ranking entre jurisdicciones que informaron y cobertura de 2024. |
| Eventos, meses, departamentos y superficies de Córdoba | [Informe anual de áreas afectadas por incendios 2024, DirGR e IDECOR](https://obs-idecor-mapas-docs.obs.sa-argentina-1.myhuaweicloud.com/m505/informe_anual_de_areas_afectadas_por_incendios_forestales_2024.pdf) | Desagregación provincial, ventanas de eventos y superficies finales. |
| Geometrías de El Durazno y Capilla del Monte | [Mapa IDECOR de áreas afectadas 2024](https://mapascordoba.gob.ar/viewer/mapa/505), KML de cada evento | Áreas oficiales para comprobar la pertenencia espacial de las observaciones FIRMS. |
| Detecciones históricas VIIRS NOAA-20 Standard Processing | [NASA FIRMS](https://firms.modaps.eosdis.nasa.gov/api/area/) | Coordenadas, fechas UTC, hora, confianza y potencia radiativa del producto `VIIRS_NOAA20_SP`. |
| Imagen del área afectada de El Durazno | [Nota de CONAE](https://www.argentina.gob.ar/noticias/los-incendios-forestales-en-cordoba-vistos-desde-el-espacio) | Imagen vinculada desde el sitio oficial: estimación de 10.500 ha al 3/9/2024, frente a las 10.644 ha finales del informe IDECOR. |

Las páginas de los PDF, diferencias de cobertura y enlaces están registrados en [`data/sources.json`](data/sources.json). Los archivos en [`data/source/`](data/source/) son transcripciones manuales de tablas y un gráfico publicados; no se mezclan las dos fuentes oficiales como si usaran una única metodología. El informe provincial excluye parte del noreste de Córdoba. Su resumen imprime `103.237 ha`, mientras que el cuerpo y las tablas suman `103.327 ha`: se usa el valor respaldado por las tablas.

## Cómo se hizo el cruce NASA–IDECOR

1. [`scripts/fetch_firms.py`](scripts/fetch_firms.py) consulta la API de área de FIRMS con el producto `VIIRS_NOAA20_SP`, usando la ventana rectangular exploratoria `-66.0,-35.2,-61.5,-29.2` en **longitud, latitud**. Descarga registros para los períodos **2–7 y 19–24 de septiembre de 2024 en UTC**. Las fechas UTC extra permiten cubrir los últimos días locales de cada ventana.
2. Se exportaron desde el mapa oficial de IDECOR los KML individuales de **El Durazno (02/09/2024; 10.644 ha)** y **Capilla del Monte (19/09/2024; 42.046 ha)**. [`scripts/convert_idecor_kml.py`](scripts/convert_idecor_kml.py) verifica en sus atributos el sitio, la fecha y la superficie; transforma todos sus polígonos y eventuales agujeros a GeoJSON WGS84. No aproxima las áreas mediante círculos o cajas.
3. [`scripts/match_firms.py`](scripts/match_firms.py) convierte cada fecha y hora de detección desde UTC a **UTC−3** y retiene únicamente observaciones dentro del polígono respectivo y entre **2–6/09** (El Durazno) o **19–23/09** (Capilla del Monte), ambas fechas incluidas. Elimina filas duplicadas por evento, fecha/hora UTC, coordenadas y satélite. El recuento resultante es 256 + 1.099; el CSV bruto de la consulta rectangular tenía 6.697 filas, muchas fuera de las áreas analizadas.
4. El resultado versionado está en [`site/data/thermal_matches.json`](site/data/thermal_matches.json) y [`site/data/detecciones_verificadas_2024.csv`](site/data/detecciones_verificadas_2024.csv). El JSON incluye los contornos usados y las detecciones para que la visualización pueda mostrar ambos sin consultar servicios externos ni revelar una clave. Los KML originales, el CSV bruto y la clave API se mantienen fuera de Git.

El polígono representa el **área final mapeada** y las detecciones corresponden a los **primeros cinco días**, por decisión analítica. Estar dentro del polígono y la ventana temporal permite asociar la observación con el área documentada; no demuestra qué causó cada anomalía ni mide cuánto ardió en ese instante. Nubes, hora de paso del satélite y umbral de detección influyen en el número de observaciones. `frp_mw` se conserva como atributo de potencia radiativa del píxel y **no se interpreta como severidad total del incendio**. Una observación no equivale a un incendio distinto. La imagen de CONAE es un recurso diferente de estos puntos VIIRS; el sitio la enlaza desde su origen.

## Reproducir el análisis

Se requiere Python 3.10+ de la biblioteca estándar para los scripts; la página publicada no ejecuta Python. En Windows, ejecutar desde la raíz del repositorio:

```powershell
$env:FIRMS_MAP_KEY = Read-Host 'Clave FIRMS'
py scripts/fetch_firms.py
```

Guardar los KML exportados del mapa IDECOR en `data/private/el_durazno.kml` y `data/private/capilla_del_monte.kml`. A continuación:

```powershell
py scripts/convert_idecor_kml.py --durazno data/private/el_durazno.kml --capilla data/private/capilla_del_monte.kml
py scripts/match_firms.py --raw data/raw_downloads/firms_viirs_noaa20_sp_cordoba_2024_event_windows.csv --polygons data/private/idecor_eventos_2024.geojson
py scripts/build_data.py
py -m unittest discover -s tests
py -m http.server 8000 --directory site
```

Abrir `http://localhost:8000`. En Linux/macOS se puede utilizar `python3` en lugar de `py`. La variable `FIRMS_MAP_KEY` se usa solo para obtener los datos; no se incorpora al navegador ni a Vercel. La API puede actualizar registros históricos; una descarga posterior debe auditarse antes de reemplazar los resultados publicados. `data/private/` y `data/raw_downloads/` figuran en `.gitignore`.

## Publicación en Vercel

[`vercel.json`](vercel.json) indica a Vercel que sirva exclusivamente la carpeta `site/`, con preset **Other** y sin compilación. `index.html`, CSS, JavaScript y JSON/CSV generados ya están versionados. No se necesitan Node, Python, variables de entorno, servicios de pago ni un paso de construcción para publicar esta página.

1. En [Vercel](https://vercel.com/new), ingresar con GitHub y elegir **Add New → Project** e importar `velezfabri/Incendios-Cordoba`.
2. Seleccionar la cuenta personal **Hobby** (uso personal gratuito). Confirmar **Root Directory: `./`** (raíz del repositorio); **Framework Preset: Other**, **Build Command: vacío**, **Output Directory: `site`**. El archivo `vercel.json` trae ya estas opciones; si el formulario muestra otra cosa, ajustarlo antes de pulsar **Deploy**.
3. Abrir el enlace `.vercel.app` que devuelve el despliegue y comprobar el gráfico, el visor con ambos eventos y las descargas CSV. Los futuros `git push` a `main` actualizarán el sitio automáticamente. Agregar la URL definitiva al campo **Website** del apartado *About* en GitHub y, si se desea, a este README.

No se necesita Manus para importar ni publicar este sitio. Si se usa Manus para proponer un rediseño, debe preservar el contrato de datos de `site/data/`, la separación entre fuentes, la clave FIRMS fuera del frontend y la configuración del despliegue en Vercel. Vercel Hobby está destinado a proyectos personales no comerciales y tiene límites de uso.

## Estructura y controles

```text
data/source/             Transcripciones de tablas y metadatos de los dos eventos
data/sources.json         Referencias, páginas, cobertura y decisiones editoriales
scripts/                 Transformación, descarga FIRMS y cruce espacial
site/                    Página estática y resultados derivados publicados
tests/                   Pruebas de agregaciones, cobertura y coincidencia espacial
vercel.json              Configuración de Vercel desde la raíz del repositorio
```

`build_data.py` verifica consistencia de la serie y de las jurisdicciones, sumas mensuales y registros departamentales. Los eventos que cruzan departamentos pueden contarse más de una vez en la tabla departamental: 606 registros frente a 586 eventos provinciales. En la matriz `year × jurisdiction`, 2024 distingue `reportado` de `sin_informacion`; los años 2018–2023 permanecen como `no_auditado` a nivel jurisdicción, sin inventar ausencias ni ceros. El visor del sitio dibuja una representación esquemática de los contornos; no es una cartografía base para medir distancias.

Proyecto y análisis: Fabricio Velez. Fuentes consultadas: 28/09/2026.
