/* Interactive map for the smart-city project.
   258 taxi zones on their real coordinates, sized by PageRank and coloured by
   the community Louvain found, with the 299 heaviest edges between them. The
   removal simulation is the point: stepping through it shows the network go
   from one connected component to sixteen the moment JFK is taken out. */
(function () {
  'use strict';

  var host = document.getElementById('sc-map');
  if (!host || typeof L === 'undefined') return;

  var COMMUNITY = ['#69f6b9', '#8f9fe8', '#e8c33f'];   // matches the static figure
  var DIM = '#3a494a';

  var state = { data: null, step: 0, edgeLayer: null, nodeLayer: null, markers: {} };

  var map = L.map(host, { scrollWheelZoom: false, zoomControl: true, attributionControl: true });
  // Esri's Dark Gray Canvas: dark enough for this page and free without an API
  // key. CARTO's dark basemap now stamps "API KEY REQUIRED" across every tile,
  // and OpenStreetMap's own servers block generic clients under their usage
  // policy. Note the {z}/{y}/{x} order — Esri puts y before x.
  L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 16,
    minZoom: 9
  }).addTo(map);

  function fmt(n) { return n.toLocaleString('en-US'); }

  function radius(node) {
    // PageRank spans two orders of magnitude; sqrt keeps the small zones visible
    // without letting Upper East Side North swallow the map.
    return 3 + Math.sqrt(node.pagerank_norm) * 14;
  }

  function removedIds() {
    return state.data.simulation.slice(0, state.step).map(function (s) { return s.removed_id; });
  }

  function draw() {
    var d = state.data;
    var gone = removedIds();

    if (state.edgeLayer) map.removeLayer(state.edgeLayer);
    if (state.nodeLayer) map.removeLayer(state.nodeLayer);

    var showEdges = document.getElementById('sc-edges').checked;
    var edges = [];
    if (showEdges) {
      d.edges.forEach(function (e) {
        edges.push(L.polyline([e.s, e.d], {
          color: '#00f5ff',
          weight: 0.6 + e.w * 2.4,
          opacity: 0.10 + e.w * 0.4,
          interactive: false
        }));
      });
    }
    state.edgeLayer = L.layerGroup(edges).addTo(map);

    var nodes = [];
    state.markers = {};
    d.nodes.forEach(function (n) {
      var dead = gone.indexOf(n.id) !== -1;
      var m = L.circleMarker([n.lat, n.lon], {
        radius: radius(n),
        color: dead ? '#ffb4ab' : COMMUNITY[n.community] || DIM,
        weight: dead ? 2 : 1,
        fillColor: dead ? '#93000a' : COMMUNITY[n.community] || DIM,
        fillOpacity: dead ? 0.25 : 0.55,
        dashArray: dead ? '3 3' : null
      });
      m.bindPopup(
        '<div style="font-family:Geist,system-ui,sans-serif;min-width:210px">' +
        '<div style="font-size:14px;font-weight:600;margin-bottom:2px">' + n.name + '</div>' +
        '<div style="font-family:JetBrains Mono,monospace;font-size:11px;color:#8f909d;margin-bottom:8px">' +
        'RANK #' + n.rank + ' · ' + n.zone_type.toUpperCase() + ' · COMMUNITY ' + n.community + '</div>' +
        '<table style="font-family:JetBrains Mono,monospace;font-size:11px;border-collapse:collapse">' +
        '<tr><td style="color:#8f909d;padding-right:10px">PageRank</td><td>' + n.pagerank.toFixed(5) + '</td></tr>' +
        '<tr><td style="color:#8f909d">Betweenness</td><td>' + n.betweenness.toFixed(5) + '</td></tr>' +
        '<tr><td style="color:#8f909d">Trips in</td><td>' + fmt(n.in_flow) + '</td></tr>' +
        '<tr><td style="color:#8f909d">Trips out</td><td>' + fmt(n.out_flow) + '</td></tr>' +
        (dead ? '<tr><td colspan="2" style="color:#ffb4ab;padding-top:6px">REMOVED IN THIS STEP</td></tr>' : '') +
        '</table></div>'
      );
      state.markers[n.id] = m;
      nodes.push(m);
    });
    state.nodeLayer = L.layerGroup(nodes).addTo(map);
  }

  function readout() {
    var d = state.data;
    var s = state.step === 0 ? null : d.simulation[state.step - 1];
    var flow = s ? s.remaining_flow_pct : 100;
    var comps = s ? s.num_components : d.stats.initial_components;
    var removed = s ? s.removed_name : null;

    document.getElementById('sc-flow').textContent = flow.toFixed(1) + '%';
    document.getElementById('sc-components').textContent = comps;
    document.getElementById('sc-components').className =
      'font-label-code-md text-label-code-md ' + (comps > 1 ? 'text-error' : 'text-tertiary-fixed-dim');
    document.getElementById('sc-step').textContent = state.step + ' / ' + d.simulation.length;
    document.getElementById('sc-removed').textContent = removed
      ? 'Just removed: ' + removed
      : 'Nothing removed — the network as it stands.';

    document.getElementById('sc-back').disabled = state.step === 0;
    document.getElementById('sc-next').disabled = state.step === d.simulation.length;
  }

  function go(delta) {
    state.step = Math.max(0, Math.min(state.data.simulation.length, state.step + delta));
    draw();
    readout();
    var last = state.step > 0 ? state.data.simulation[state.step - 1].removed_id : null;
    if (last && state.markers[last]) map.panTo(state.markers[last].getLatLng(), { animate: true });
  }

  fetch('/assets/data/smartcity-map.json')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      state.data = d;
      map.setView([d.city.center_lat, d.city.center_lon], d.city.zoom);
      draw();
      readout();
      document.getElementById('sc-loading').hidden = true;
      document.getElementById('sc-controls').hidden = false;
    })
    .catch(function () {
      document.getElementById('sc-loading').textContent =
        'The map data could not be loaded. The figures below carry the same findings.';
    });

  document.getElementById('sc-next').addEventListener('click', function () { go(1); });
  document.getElementById('sc-back').addEventListener('click', function () { go(-1); });
  document.getElementById('sc-reset').addEventListener('click', function () {
    state.step = 0; draw(); readout();
    map.setView([state.data.city.center_lat, state.data.city.center_lon], state.data.city.zoom);
  });
  document.getElementById('sc-edges').addEventListener('change', draw);

  // Scroll-wheel zoom is off so the page still scrolls over the map; a click
  // inside it opts in, and leaving the map opts back out.
  map.on('click', function () { map.scrollWheelZoom.enable(); });
  map.on('mouseout', function () { map.scrollWheelZoom.disable(); });
})();
