# Llevar el proyecto a Manus

1. Crear **un repositorio nuevo** de GitHub llamado `incendios-argentina` y subir **el contenido de esta carpeta a la raíz**. Mantener intacto el proyecto anterior sobre Chile.
2. Conectar ese repositorio desde Manus. Pedirle que **importe y conserve** los archivos `data/source/`, `scripts/`, `data/sources.json` y `site/data/`, y que use el sitio existente como punto de partida. La página inicial está en `site/index.html`.
3. Para previsualizar o servir el proyecto, configurar raíz pública `site/`. Si Manus requiere un comando: `python3 -m http.server 8000 --directory site`; no hay comando de compilación ni secretos.
4. Si Manus rehace la interfaz, darle esta instrucción:

> Diseñá una página de historia de datos en español llamada “Incendios en Argentina · foco Córdoba 2024”. Usá `site/data/analysis.json` y los CSV del repositorio para cifras oficiales. Para detecciones NASA, usá `site/data/thermal_matches.json` **solo si** `status` vale `validated_polygon_and_time_match`; si dice `not_available`, mantené la explicación pendiente y el enlace al mapa IDECOR. Preservá las notas de cobertura, los `null` por falta de información, las diferencias entre anuario e informe IDECOR, los créditos de CONAE y la distinción entre observación térmica, episodio y hectáreas. No inventes puntos, escenas, mapas de riesgo, modelos de IA ni datos para 2018–2023 por provincia. Conservá descargas, fuentes y accesibilidad. Mostrame una vista previa para revisar.

5. Comprobar que la imagen remota de CONAE carga, que los selectores de gráficos funcionan, que las tablas CSV descargan y que en celular los gráficos no se cortan. Mantener `site/data/analysis.json` y `site/data/thermal_matches.json` versionados: Manus no necesita correr Python para mostrar el sitio. **No ingresar la clave FIRMS en Manus ni incluirla en variables públicas del frontend.**

Si Manus exige React, puede adaptar la interfaz desde `site/`, pero debe conservar el contrato de datos y sus advertencias. **No subir claves FIRMS, CSV brutos sin revisar ni descargas privadas de CONAE.** La conexión y publicación de Manus las realizás desde tu propia cuenta.
