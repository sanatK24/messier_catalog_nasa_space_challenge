// Messier Skymap Prototype
const DATA_PATH = 'messier_data.json';
const DZI_MANIFEST = 'messier_dzi/manifest.json';

let messier = [];
let dziMap = {};
let map, markers = [];

async function fetchJSON(path){
  const res = await fetch(path);
  return res.json();
}

function setQuadrantProgress(quadrant, progress) {
  const circle = document.querySelector(`.progress-ring-q${quadrant}`);
  const circumference = 2 * Math.PI * 90; // 2πr where r=90
  const offset = circumference - (progress / 25) * circumference;
  circle.style.strokeDashoffset = offset;
}

function activateQuadrant(quadrant) {
  // Remove active class from all quadrants
  document.querySelectorAll('.progress-ring circle').forEach(circle => {
    circle.classList.remove('active');
  });
  
  // Add active class to current quadrant
  const activeCircle = document.querySelector(`.progress-ring-q${quadrant}`);
  activeCircle.classList.add('active');
  activeCircle.style.opacity = '1';
}

async function updateLoadingProgress(progress, detail) {
  const progressText = document.querySelector('.status-progress');
  const detailsText = document.querySelector('.loading-details');
  const quadrantLabel = document.querySelector('.quadrant-label');
  
  // Calculate which quadrant we're in
  const quadrant = Math.floor(progress / 25) + 1;
  const quadrantProgress = progress % 25;
  
  // Update quadrant display
  quadrantLabel.textContent = `QUADRANT ${quadrant}/4`;
  activateQuadrant(quadrant);
  
  // Set progress for current and completed quadrants
  for (let i = 1; i < quadrant; i++) {
    setQuadrantProgress(i, 25); // Fill completed quadrants
    document.querySelector(`.progress-ring-q${i}`).style.opacity = '1';
  }
  setQuadrantProgress(quadrant, quadrantProgress);
  
  progressText.textContent = `${Math.floor(progress)}%`;
  if (detail) {
    detailsText.textContent = detail;
  }
}

function hideLoadingScreen() {
  const loadingScreen = document.getElementById('loadingScreen');
  loadingScreen.classList.add('hidden');
  setTimeout(() => {
    loadingScreen.style.display = 'none';
  }, 500);
}

async function init(){
  try {
    // Quadrant 1: Data Loading (0-25%)
    updateLoadingProgress(5, 'INITIALIZING CORE SYSTEMS');
    await new Promise(r => setTimeout(r, 500));
    updateLoadingProgress(15, 'Loading catalog data...');
    messier = await fetchJSON(DATA_PATH);
    updateLoadingProgress(25, 'QUADRANT 1 COMPLETE');
    await new Promise(r => setTimeout(r, 300));
    
    // Quadrant 2: Processing (25-50%)
    updateLoadingProgress(30, 'Loading image manifest...');
    const manifest = await fetchJSON(DZI_MANIFEST);
    manifest.forEach(item => dziMap[item.id] = item);
    updateLoadingProgress(40, 'Processing astronomical data...');
    await new Promise(r => setTimeout(r, 300));
    updateLoadingProgress(50, 'QUADRANT 2 COMPLETE');
    
    // Quadrant 3: Interface Setup (50-75%)
    updateLoadingProgress(55, 'Building object list...');
    buildList();
    updateLoadingProgress(65, 'Initializing sky map...');
    setupMap();
    updateLoadingProgress(75, 'QUADRANT 3 COMPLETE');
    
    // Quadrant 4: Final Systems (75-100%)
    updateLoadingProgress(80, 'Setting up interface...');
    setupSearch();
    setupFilters();
    updateLoadingProgress(90, 'Preparing skymap overlay...');
    setupSkymapOverlay();
    updateLoadingProgress(95, 'Calibrating final systems...');
    await new Promise(r => setTimeout(r, 300));
    updateLoadingProgress(100, 'ALL SYSTEMS ONLINE');
    
    // Hide loading screen after a brief delay
    setTimeout(hideLoadingScreen, 800);
  } catch (error) {
    console.error('Initialization error:', error);
    document.querySelector('.status-label').textContent = 'ERROR';
    document.querySelector('.loading-details').textContent = 'Failed to initialize. Please refresh.';
  }
}

let skymapLayer = null;
let hotspotFeatures = [];
async function setupSkymapOverlay(){
  const btn = document.getElementById('toggleSkymap');
  const tilesUrl = 'output/tiles/{z}/{x}/{y}.png';
  btn.onclick = async ()=>{
    if(skymapLayer){
      map.removeLayer(skymapLayer);
      skymapLayer = null;
      return;
    }
    // add tile layer
    skymapLayer = L.tileLayer(tilesUrl, {maxZoom:6, minZoom:0, attribution: 'Messier Skymap'}).addTo(map);
    // load hotspots
    try{
      const hs = await fetch('output/messier_skymap_8k_hotspots.json').then(r=>r.json());
      hotspotFeatures = hs;
      // create invisible rectangles on map using image coordinates conversion
      // We assume equirectangular: lon = ra-180 => x axis mapping used earlier; but we also stored bbox_norm
      hs.forEach(h=>{
        const bbox = h.bbox_norm; // [x0,y0,x1,y1]
        // convert normalized to latlng: lat = (1 - (y*2 -1))? We'll map using same conversion as ra/dec used for markers
        // For simplicity, compute center RA/Dec by converting center_px back to ra/dec by inverse mapping (assume 8192x4096)
        const w = 8192, hgt = 4096;
        const cx = h.center_px[0], cy = h.center_px[1];
        const ra = (cx / w) * 360.0;
        const dec = 90.0 - (cy / hgt) * 180.0;
        const lat = dec;
        const lng = ra - 180;
        const marker = L.circleMarker([lat, lng], {radius:8, color:'#ffddb3', weight:1, fillOpacity:0}).addTo(map);
        marker.on('click', ()=>{
          const found = messier.find(m=>m.id===h.id);
          if(found) openDetail(found);
        });
      });
    }catch(e){ console.warn('No hotspots found or failed to load:', e); }
  };
}

function buildList(){
  const ul = document.getElementById('objectList');
  const countEl = document.getElementById('objectCount');
  
  messier.forEach(o=>{
    const li = document.createElement('li');
    li.textContent = `${o.id} — ${o.name}`;
    li.onclick = ()=> gotoObject(o);
    ul.appendChild(li);
  });

  countEl.textContent = `${messier.length} objects`;
}

let currentView = 'sky'; // 'sky' or 'grid'

function setupMap(){
  // We'll map RA/DEC onto a plate carrée projection: x = ra_decimal, y = dec_decimal
  map = L.map('map', {worldCopyJump:false, zoomControl:true, minZoom:1, maxZoom:12}).setView([0,180],2);
  
  // Update coordinates display on mouse move
  map.on('mousemove', (e) => {
    const lat = e.latlng.lat.toFixed(2);
    const lng = (e.latlng.lng + 180).toFixed(2); // Convert back to RA
    document.getElementById('ra').textContent = `${lng}°`;
    document.getElementById('dec').textContent = `${lat}°`;
  });
  
  // Create a dark background
  const darkLayer = L.tileLayer('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==', {
    maxZoom: 12
  }).addTo(map);
  
  // Add skymap tiles immediately
  skymapLayer = L.tileLayer('output/tiles/{z}/{x}/{y}.png', {maxZoom:6, minZoom:0, attribution: 'Messier Skymap'}).addTo(map);

  // Convert RA (0-360) and Dec (-90..+90) to lat/lng for Leaflet: lat = dec, lng = ra-180
  messier.forEach(o=>{
    const lat = o.dec_decimal;
    const lng = o.ra_decimal - 180;
    const marker = L.circleMarker([lat,lng],{radius:6,fillColor:'#7dd3fc',color:'#66bfbf',weight:1,fillOpacity:0.9}).addTo(map);
    marker.on('click', ()=> openDetail(o));
    marker.bindTooltip(`${o.id} — ${o.name}`, {direction:'top',offset:[0,-8]});
    markers.push({id:o.id, marker});
  });

  // add simple tooltip clustering for crowded regions (lightweight)
  map.on('moveend',()=>{/* noop for now */});
}

function setupFilters(){
  const sel = document.getElementById('typeFilter');
  if(!sel) return;
  sel.onchange = ()=>{
    const val = sel.value;
    filterByType(val);
  };
}

function filterByType(type){
  markers.forEach(({id,marker})=>{
    const obj = messier.find(o=>o.id===id);
    if(!obj) return;
    const ok = (type==='all') || (obj.type && obj.type.includes(type));
    if(ok) marker.setStyle({opacity:1,fillOpacity:0.9,radius:6});
    else marker.setStyle({opacity:0.15,fillOpacity:0.1,radius:4});
  });
  // also filter list
  const lis = document.querySelectorAll('#objectList li');
  lis.forEach(li=>{
    const text = li.textContent;
    const oid = text.split(' — ')[0];
    const obj = messier.find(o=>o.id===oid);
    if(!obj) return;
    const show = (type==='all') || (obj.type && obj.type.includes(type));
    li.style.display = show ? 'block' : 'none';
  });
}

function gotoObject(o){
  const lat = o.dec_decimal;
  const lng = o.ra_decimal - 180;
  map.setView([lat,lng],6, {animate:true});
  openDetail(o);
}

function setupSearch(){
  const input = document.getElementById('search');
  const btn = document.getElementById('searchBtn');
  btn.onclick = ()=>{
    const q = input.value.trim().toLowerCase();
    if(!q) return;
    const found = messier.find(o=> o.id.toLowerCase()===q || o.name.toLowerCase().includes(q));
    if(found) gotoObject(found);
    else alert('Not found. Try M31 or Andromeda.');
  };
}

function openDetail(o){
  const modal = document.getElementById('detailModal');
  document.getElementById('objTitle').textContent = `${o.id} — ${o.name}`;
  document.getElementById('objType').textContent = `Type: ${o.type}`;
  document.getElementById('objCoords').textContent = `RA ${o.ra}  DEC ${o.dec}`;
  document.getElementById('objConst').textContent = `Constellation: ${o.constellation}`;
  document.getElementById('objMag').textContent = `Magnitude: ${o.magnitude}`;
  document.getElementById('objHistory').textContent = `Historical notes: ${generateHistory(o)}`;

  // thumbnail or DZI
  const entry = dziMap[o.id] || dziMap[o.id.replace('-02','')];
  const thumb = document.getElementById('thumb');
  const osdWrap = document.getElementById('osdViewer');
  const thumbWrap = document.getElementById('thumbWrap');
  osdWrap.classList.add('hidden');
  thumbWrap.classList.remove('hidden');

  if(entry){
    thumb.src = `messier_dzi/${entry.thumbnail}`;
    // prepare OpenSeadragon on demand
    setTimeout(()=>{
      osdWrap.classList.remove('hidden');
      thumbWrap.classList.add('hidden');
      openDZI(entry.dzi);
    }, 800);
  } else {
    thumb.src = 'output.jpg'; // fallback
  }
  // add external links (placeholders to NASA/Hubble)
  const links = document.getElementById('objLinks');
  links.innerHTML = '';
  const nasa = document.createElement('a');
  nasa.href = `https://images.nasa.gov/search-results?q=${encodeURIComponent(o.name)}`;
  nasa.target = '_blank';
  nasa.textContent = 'Search NASA images';
  links.appendChild(nasa);

  links.appendChild(document.createTextNode(' • '));
  const hubble = document.createElement('a');
  hubble.href = `https://hubblesite.org/search?search=${encodeURIComponent(o.name)}`;
  hubble.target = '_blank';
  hubble.textContent = 'Hubble site';
  links.appendChild(hubble);

  // observational placeholders
  document.getElementById('bestSeason').textContent = estimateSeason(o.dec_decimal);
  document.getElementById('appSize').textContent = o.apparent_size || '—';

  modal.classList.remove('hidden');
}

function generateHistory(o){
  return `${o.name} (${o.id}) is a ${o.type} in ${o.constellation}. RA ${o.ra}, Dec ${o.dec}. Magnitude ${o.magnitude}.`;
}

function estimateSeason(dec){
  // rough rule: northern objects (dec>0) best in northern hemisphere spring/summer depending on RA
  if(dec > 20) return 'Spring - Summer (N hemisphere)';
  if(dec > -20) return 'Spring - Autumn (N hemisphere)';
  return 'Summer - Autumn (S hemisphere)';
}

let osdViewer = null;
function openDZI(dziPath){
  const osdWrap = document.getElementById('osdViewer');
  if(osdViewer){
    try{ osdViewer.open(`messier_dzi/${dziPath}`); return; }catch(e){console.warn(e)}
  }
  osdViewer = OpenSeadragon({
    id: 'osdViewer',
    prefixUrl: 'https://cdn.jsdelivr.net/npm/openseadragon@4.0.0/build/openseadragon/images/',
    tileSources: `messier_dzi/${dziPath}`,
    showNavigator:true
  });
}

// modal close
document.addEventListener('click', (e)=>{
  if(e.target && e.target.id==='closeModal'){ document.getElementById('detailModal').classList.add('hidden'); }
});

// Map control functions
function toggleMapView() {
  currentView = currentView === 'sky' ? 'grid' : 'sky';
  if (currentView === 'grid') {
    if (skymapLayer) map.removeLayer(skymapLayer);
    // Add grid lines (simplified for demo)
    L.grid().addTo(map);
  } else {
    map.eachLayer((layer) => {
      if (layer instanceof L.Grid) map.removeLayer(layer);
    });
    if (!skymapLayer) {
      skymapLayer = L.tileLayer('output/tiles/{z}/{x}/{y}.png', {
        maxZoom: 6,
        minZoom: 0,
        attribution: 'Messier Skymap'
      }).addTo(map);
    }
  }
}

function zoomToFit() {
  map.setView([0, 180], 2, { animate: true });
}

function toggleGrid() {
  map.eachLayer((layer) => {
    if (layer instanceof L.Grid) {
      map.removeLayer(layer);
      return;
    }
  });
  L.grid().addTo(map);
}

// Add custom Grid control to Leaflet
L.Grid = L.LayerGroup.extend({
  initialize: function(options) {
    L.LayerGroup.prototype.initialize.call(this);
    this.options = L.extend({}, {
      xticks: 24,
      yticks: 18
    }, options);
  },

  onAdd: function(map) {
    this._map = map;
    this._draw();
    return this;
  },

  _draw: function() {
    let raLines = [], decLines = [];
    
    // RA lines (verticals)
    for (let i = -180; i <= 180; i += 30) {
      const line = L.polyline([[-90, i], [90, i]], {
        color: 'rgba(64, 205, 255, 0.2)',
        weight: 1
      });
      this.addLayer(line);
      
      // Labels
      const ra = ((i + 180) % 360).toFixed(0);
      const label = L.marker([90, i], {
        icon: L.divIcon({
          className: 'grid-label',
          html: `${ra}°`,
          iconSize: [40, 20]
        })
      });
      this.addLayer(label);
    }
    
    // Dec lines (horizontals)
    for (let i = -75; i <= 75; i += 15) {
      const line = L.polyline([[i, -180], [i, 180]], {
        color: 'rgba(64, 205, 255, 0.2)',
        weight: 1
      });
      this.addLayer(line);
      
      // Labels
      const label = L.marker([i, -180], {
        icon: L.divIcon({
          className: 'grid-label',
          html: `${i}°`,
          iconSize: [30, 20]
        })
      });
      this.addLayer(label);
    }
  }
});

L.grid = function(options) {
  return new L.Grid(options);
};

window.addEventListener('load', init);
