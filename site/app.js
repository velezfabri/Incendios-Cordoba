const format = new Intl.NumberFormat('es-AR');
const state = {annual: 'affected_ha', ranking: 'affected_ha', months: 'affected_ha'};
const labels = {affected_ha: 'Hectáreas afectadas', reported_fires: 'Incendios reportados'};

function barChart(id, rows, metric, nameKey, highlight, maxHeight = 245) {
  const element = document.getElementById(id);
  const maximum = Math.max(...rows.map(row => row[metric]));
  element.innerHTML = '';
  element.setAttribute('aria-label', `${labels[metric]}. ${rows.map(row => `${row[nameKey]}: ${format.format(row[metric])}`).join('; ')}`);
  rows.forEach(row => {
    const col = document.createElement('div'); col.className = 'bar-col';
    const value = document.createElement('span'); value.className = 'bar-value'; value.textContent = format.format(row[metric]);
    const bar = document.createElement('div'); bar.className = `bar ${row[nameKey] === highlight ? 'highlight' : ''}`;
    bar.style.height = `${Math.max(2, (row[metric] / maximum) * maxHeight)}px`;
    bar.title = `${row[nameKey]}: ${format.format(row[metric])} ${metric === 'affected_ha' ? 'ha' : 'incendios/eventos'}`;
    const name = document.createElement('span'); name.className = 'bar-name'; name.textContent = row[nameKey];
    col.append(value, bar, name); element.append(col);
  });
}

function ranking(rows, metric) {
  const root = document.getElementById('ranking-chart'); root.innerHTML = '';
  const sorted = rows.filter(r => r.status === 'reportado' && r.jurisdiction !== 'Parques Nacionales')
    .sort((a,b) => b[metric] - a[metric]).slice(0,8);
  const maximum = sorted[0][metric];
  sorted.forEach(row => {
    const line = document.createElement('div'); line.className = 'rank-row';
    const label = document.createElement('span'); label.className = 'rank-label'; label.textContent = row.jurisdiction; label.title = row.jurisdiction;
    const track = document.createElement('span'); track.className = 'rank-track';
    const fill = document.createElement('span'); fill.className = `rank-fill ${row.jurisdiction === 'Córdoba' ? 'highlight' : ''}`;
    fill.style.display = 'block'; fill.style.width = `${row[metric]/maximum*100}%`; track.append(fill);
    const value = document.createElement('span'); value.className = 'rank-value'; value.textContent = `${format.format(row[metric])}${metric === 'affected_ha' ? ' ha' : ''}`;
    line.append(label, track, value); root.append(line);
  });
}

function switcher(name, callback) {
  document.querySelectorAll(`[data-${name}]`).forEach(button => button.addEventListener('click', () => {
    state[name] = button.dataset[name];
    document.querySelectorAll(`[data-${name}]`).forEach(item => {
      const active = item === button; item.classList.toggle('active', active); item.setAttribute('aria-pressed', String(active));
    });
    callback();
  }));
}

fetch('data/analysis.json').then(response => {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}).then(data => {
  const annual = () => {
    document.getElementById('annual-title').textContent = state.annual === 'affected_ha' ? 'Superficie afectada por año' : 'Incendios reportados por año';
    barChart('annual-chart', data.nationalYears.map(r => ({...r, name: String(r.year)})), state.annual, 'name', '2024');
  };
  const province = () => {
    document.getElementById('ranking-title').textContent = state.ranking === 'affected_ha' ? 'Superficie afectada' : 'Incendios reportados';
    ranking(data.jurisdictions2024, state.ranking);
  };
  const monthly = () => {
    document.getElementById('months-title').textContent = state.months === 'affected_ha' ? 'Hectáreas afectadas por mes' : 'Eventos registrados por mes';
    barChart('months-chart', data.cordobaMonths, state.months, 'month_name', 'Septiembre');
  };
  annual(); province(); monthly();
  switcher('annual', annual); switcher('ranking', province); switcher('months', monthly);
}).catch(error => {
  for (const id of ['annual-chart', 'ranking-chart', 'months-chart']) {
    document.getElementById(id).textContent = `No se pudieron cargar los datos (${error.message}). Revisá la ruta site/data/analysis.json.`;
  }
});

function drawEvent(root, event) {
  root.innerHTML = '';
  const header = document.createElement('div'); header.className = 'thermal-header';
  const title = document.createElement('h3'); title.textContent = event.site;
  const description = document.createElement('p');
  description.textContent = `${event.start_local} a ${event.end_local} · ${format.format(event.detections.length)} observaciones dentro del polígono en esos cinco días. Superficie final IDECOR: ${format.format(event.affected_ha_official)} ha.`;
  header.append(title, description); root.append(header);
  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg'); svg.setAttribute('viewBox', '0 0 800 430');
  svg.setAttribute('role', 'img');
  svg.setAttribute('aria-label', `${event.site}: ${event.detections.length} observaciones satelitales dentro del contorno final`);
  const polygons = [];
  for (const geometry of event.geometries) {
    for (const polygon of geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates) polygons.push(polygon);
  }
  const positions = polygons.flat(2);
  const xs = positions.map(p => p[0]), ys = positions.map(p => p[1]);
  const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
  const scale = Math.min(700 / Math.max(.001, maxX - minX), 350 / Math.max(.001, maxY - minY));
  const project = p => [400 + (p[0] - (minX + maxX) / 2) * scale, 215 - (p[1] - (minY + maxY) / 2) * scale];
  for (const polygon of polygons) {
    const path = document.createElementNS(ns, 'path');
    path.setAttribute('d', polygon.map(ring => ring.map((point, i) => {
      const [x, y] = project(point); return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
    }).join(' ') + ' Z').join(' '));
    path.setAttribute('fill', '#d9eb97'); path.setAttribute('fill-opacity', '.17');
    path.setAttribute('stroke', '#d9eb97'); path.setAttribute('stroke-width', '2');
    path.setAttribute('fill-rule', 'evenodd'); svg.append(path);
  }
  for (const point of event.detections) {
    const circle = document.createElementNS(ns, 'circle'); const [x, y] = project([point.lon, point.lat]);
    circle.setAttribute('cx', x); circle.setAttribute('cy', y); circle.setAttribute('r', '4.5');
    circle.setAttribute('fill', '#ef8c65'); circle.setAttribute('fill-opacity', '.85');
    const tooltip = document.createElementNS(ns, 'title');
    tooltip.textContent = `${point.date_local} · ${point.time_utc} UTC · VIIRS NOAA-20 · confianza ${point.confidence}`;
    circle.append(tooltip); svg.append(circle);
  }
  root.append(svg);
  const legend = document.createElement('p'); legend.className = 'thermal-legend';
  legend.textContent = 'Contorno: área final de IDECOR · puntos: detecciones NASA de los primeros cinco días. Vista esquemática sin base cartográfica; cada punto no representa hectáreas.';
  root.append(legend);
}

fetch('data/thermal_matches.json').then(response => response.json()).then(data => {
  const root = document.getElementById('thermal-explorer');
  if (data.status !== 'validated_polygon_and_time_match' || !data.events?.length) {
    root.innerHTML = '<h3>Detecciones pendientes de verificación</h3><p>Esta entrega todavía no contiene un CSV NASA descargado ni polígonos IDECOR exportados y comprobados. No mostramos coordenadas o recuentos supuestos. El repositorio incluye los scripts para hacer el cruce y activar este visor cuando estén los datos validados.</p>';
    return;
  }
  root.innerHTML = '';
  const controls = document.createElement('div'); controls.className = 'thermal-controls';
  const display = document.createElement('div');
  data.events.forEach((event, index) => {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = event.site;
    button.setAttribute('aria-pressed', String(index === 0));
    button.addEventListener('click', () => {
      controls.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      drawEvent(display, event);
    }); controls.append(button);
  });
  root.append(controls, display); drawEvent(display, data.events[0]);
  const link = document.createElement('a'); link.href = 'data/detecciones_verificadas_2024.csv';
  link.download = 'detecciones_verificadas_2024.csv'; link.textContent = 'Descargar puntos y atributos CSV ↗'; root.append(link);
}).catch(() => {
  document.getElementById('thermal-explorer').textContent = 'El conjunto de observaciones todavía no está disponible.';
});
