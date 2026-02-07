"""
Flux Open Home - Homeowner Dashboard UI
=========================================
HTML/CSS/JS for the homeowner control dashboard.
Served at GET /admin when mode is "homeowner" (default view).
"""

HOMEOWNER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flux Open Home - Homeowner Dashboard</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; color: #2c3e50; }
.header { background: linear-gradient(135deg, #1a7a4c, #2ecc71); color: white; padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
.header-left { display: flex; align-items: center; gap: 14px; }
.header-logo { height: 44px; filter: brightness(0) invert(1); }
.header h1 { font-size: 20px; font-weight: 600; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.nav-tabs { display: flex; gap: 4px; }
.nav-tab { padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 500; text-decoration: none; color: white; transition: background 0.15s ease; }
.nav-tab:hover { background: rgba(255,255,255,0.15); }
.nav-tab.active { background: rgba(255,255,255,0.25); }
.container { max-width: 1200px; margin: 0 auto; padding: 24px; }
.card { background: white; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); margin-bottom: 20px; overflow: hidden; }
.card-header { padding: 16px 20px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
.card-header h2 { font-size: 16px; font-weight: 600; }
.card-body { padding: 20px; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s ease; }
.btn-primary { background: #1a7a4c; color: white; }
.btn-primary:hover { background: #15603c; }
.btn-danger { background: #e74c3c; color: white; }
.btn-danger:hover { background: #c0392b; }
.btn-secondary { background: #ecf0f1; color: #2c3e50; }
.btn-secondary:hover { background: #dfe6e9; }
.btn-sm { padding: 5px 10px; font-size: 12px; }
.btn-icon { padding: 6px 10px; }

/* Zone/Sensor Tiles */
.tile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.tile { background: #f8f9fa; border-radius: 8px; padding: 14px; border: 1px solid #eee; }
.tile.active { background: #e8f5e9; border-color: #a5d6a7; }
.tile-name { font-weight: 600; font-size: 14px; margin-bottom: 6px; }
.tile-state { font-size: 13px; color: #7f8c8d; margin-bottom: 8px; }
.tile-state.on { color: #27ae60; font-weight: 500; }
.tile-actions { display: flex; gap: 6px; }

/* Schedule (entity-based) */
.schedule-section { margin-bottom: 20px; }
.schedule-section-label { font-size: 13px; font-weight: 600; color: #7f8c8d; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px; }
.days-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
.day-toggle { padding: 8px 14px; border-radius: 8px; border: 2px solid #ddd; cursor: pointer; font-size: 13px; font-weight: 600; text-align: center; min-width: 52px; transition: all 0.15s ease; background: #f8f9fa; color: #7f8c8d; user-select: none; }
.day-toggle:hover { border-color: #bbb; }
.day-toggle.active { background: #e8f5e9; border-color: #27ae60; color: #27ae60; }
.start-times-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.zone-settings-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.zone-settings-table th { text-align: left; padding: 8px; border-bottom: 2px solid #eee; font-size: 12px; color: #7f8c8d; text-transform: uppercase; }
.zone-settings-table td { padding: 8px; border-bottom: 1px solid #f0f0f0; }
.system-controls-row { display: flex; gap: 12px; flex-wrap: wrap; }

/* Empty States */
.empty-state { text-align: center; padding: 40px 20px; color: #95a5a6; }
.empty-state h3 { font-size: 18px; margin-bottom: 8px; color: #7f8c8d; }
.empty-state p { font-size: 14px; }

/* Loading */
.loading { text-align: center; padding: 20px; color: #7f8c8d; font-size: 14px; }

/* Toast */
.toast-container { position: fixed; top: 20px; right: 20px; z-index: 1000; }
.toast { background: #2c3e50; color: white; padding: 12px 20px; border-radius: 8px; margin-bottom: 8px; font-size: 14px; animation: slideIn 0.3s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.toast.error { background: #e74c3c; }
.toast.success { background: #27ae60; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

/* Responsive */
@media (max-width: 600px) {
    .tile-grid { grid-template-columns: 1fr; }
    .container { padding: 12px; }
    .header { flex-wrap: wrap; gap: 10px; padding: 14px 16px; }
    .header h1 { font-size: 16px; }
    .header-logo { height: 32px; }
    .header-actions { width: 100%; justify-content: flex-start; flex-wrap: wrap; gap: 6px; }
    .nav-tabs { gap: 2px; }
    .nav-tab { padding: 5px 10px; font-size: 12px; }
    .btn-sm { padding: 5px 8px; font-size: 11px; }
    .days-row { gap: 4px; }
    .day-toggle { padding: 6px 10px; font-size: 12px; min-width: 44px; }
    .start-times-grid { grid-template-columns: 1fr; }
    .system-controls-row { flex-direction: column; }
}
</style>
</head>
<body>

<div class="header">
    <div class="header-left">
        <img src="data:image/png;base64,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" alt="Flux Open Home" class="header-logo">
        <h1>Irrigation</h1>
    </div>
    <div class="header-actions">
        <div class="nav-tabs">
            <span class="nav-tab active">Homeowner</span>
            <a class="nav-tab" href="?view=config">Configuration</a>
        </div>
        <button class="btn btn-secondary btn-sm" onclick="switchToManagement()">Switch to Management</button>
    </div>
</div>

<div class="container">
    <div class="detail-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <div>
            <h2 id="dashTitle" style="font-size:22px;font-weight:600;">My Irrigation System</h2>
            <div id="dashAddress" style="font-size:14px;color:#95a5a6;margin-top:4px;display:none;"></div>
        </div>
        <div style="display:flex;gap:8px;">
            <button class="btn btn-secondary btn-sm" onclick="refreshDashboard()">Refresh</button>
            <button class="btn btn-danger btn-sm" onclick="stopAllZones()">Emergency Stop All</button>
        </div>
    </div>

    <!-- Location Map -->
    <div id="detailMap" style="height:200px;border-radius:12px;margin-bottom:20px;display:none;overflow:hidden;"></div>

    <!-- Status Card -->
    <div class="card">
        <div class="card-header">
            <h2>System Status</h2>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-secondary btn-sm" id="pauseResumeBtn" onclick="togglePauseResume()">Pause System</button>
            </div>
        </div>
        <div class="card-body" id="detailStatus">
            <div class="loading">Loading status...</div>
        </div>
    </div>

    <!-- Weather Card -->
    <div class="card" id="weatherCard" style="display:none;">
        <div class="card-header">
            <h2>Weather-Based Control</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <span id="weatherMultBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:#d4edda;color:#155724;">1.0x</span>
            </div>
        </div>
        <div class="card-body" id="weatherCardBody">
            <div class="loading">Loading weather...</div>
        </div>
    </div>

    <!-- Zones Card -->
    <div class="card">
        <div class="card-header"><h2>Zones</h2></div>
        <div class="card-body" id="detailZones">
            <div class="loading">Loading zones...</div>
        </div>
    </div>

    <!-- Sensors Card -->
    <div class="card">
        <div class="card-header"><h2>Sensors</h2></div>
        <div class="card-body" id="detailSensors">
            <div class="loading">Loading sensors...</div>
        </div>
    </div>

    <!-- Device Controls Card -->
    <div class="card">
        <div class="card-header"><h2>Device Controls</h2></div>
        <div class="card-body" id="detailControls">
            <div class="loading">Loading controls...</div>
        </div>
    </div>

    <!-- Schedule Card (entity-based) -->
    <div class="card">
        <div class="card-header">
            <h2>Schedule</h2>
        </div>
        <div class="card-body" id="detailSchedule">
            <div class="loading">Loading schedule...</div>
        </div>
    </div>

    <!-- History Card -->
    <div class="card">
        <div class="card-header">
            <h2>Run History</h2>
            <div style="display:flex;gap:6px;align-items:center;">
                <select id="historyRange" onchange="loadHistory()" style="padding:4px 8px;border:1px solid #ddd;border-radius:6px;font-size:12px;">
                    <option value="24">Last 24 hours</option>
                    <option value="168">Last 7 days</option>
                    <option value="720">Last 30 days</option>
                    <option value="2160">Last 90 days</option>
                    <option value="8760">Last year</option>
                </select>
                <button class="btn btn-secondary btn-sm" onclick="exportHistoryCSV()">Export CSV</button>
                <button class="btn btn-danger btn-sm" onclick="clearRunHistory()">Clear History</button>
            </div>
        </div>
        <div class="card-body" id="detailHistory">
            <div class="loading">Loading history...</div>
        </div>
    </div>
</div>

<div class="toast-container" id="toastContainer"></div>

<script>
// Homeowner API base — all calls go through /admin/api/homeowner/*
const HBASE = (window.location.pathname.replace(/\\/+$/, '')) + '/api/homeowner';
let refreshTimer = null;
let geocodeCache = {};
let leafletMap = null;

// --- Toast ---
function showToast(msg, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = 'toast ' + type;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// --- Mode Switch ---
async function switchToManagement() {
    if (!confirm('Switch to Management mode? The homeowner dashboard will no longer be available until you switch back.')) return;
    try {
        const BASE = window.location.pathname.replace(/\/+$/, '');
        await fetch(BASE + '/api/mode', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ mode: 'management' }),
        });
        showToast('Switching to management mode...');
        setTimeout(() => window.location.reload(), 1000);
    } catch(e) { showToast(e.message, 'error'); }
}

// --- API Helper ---
async function api(path, options = {}) {
    const res = await fetch(HBASE + path, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    });
    const data = await res.json();
    if (!res.ok) {
        const detail = data.detail || data.error || JSON.stringify(data);
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
    return data;
}

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// --- Unit Conversion Helpers ---
function fToC(f) { return Math.round((f - 32) * 5 / 9); }
function cToF(c) { return Math.round(c * 9 / 5 + 32); }
function mphToKmh(mph) { return Math.round(mph * 1.609); }
function kmhToMph(kmh) { return Math.round(kmh / 1.609); }

function syncUnitConversion(sourceId, targetId, convertFn) {
    const el = document.getElementById(sourceId);
    if (!el) return;
    el.addEventListener('input', function() {
        const target = document.getElementById(targetId);
        if (target) target.value = convertFn(parseFloat(this.value) || 0);
    });
}

function setupUnitConversions(prefix) {
    const p = prefix || '';
    // Freeze: F <-> C
    syncUnitConversion(p + 'temperature_freeze_f', p + 'temperature_freeze_c', fToC);
    syncUnitConversion(p + 'temperature_freeze_c', p + 'temperature_freeze_f', cToF);
    // Cool: F <-> C
    syncUnitConversion(p + 'temperature_cool_f', p + 'temperature_cool_c', fToC);
    syncUnitConversion(p + 'temperature_cool_c', p + 'temperature_cool_f', cToF);
    // Hot: F <-> C
    syncUnitConversion(p + 'temperature_hot_f', p + 'temperature_hot_c', fToC);
    syncUnitConversion(p + 'temperature_hot_c', p + 'temperature_hot_f', cToF);
    // Wind: mph <-> km/h
    syncUnitConversion(p + 'wind_speed_mph', p + 'wind_speed_kmh', mphToKmh);
    syncUnitConversion(p + 'wind_speed_kmh', p + 'wind_speed_mph', kmhToMph);
}

// --- Zone Display Name Helpers ---
function getZoneDisplayName(z) {
    const aliases = window._currentZoneAliases || {};
    if (aliases[z.entity_id]) return aliases[z.entity_id];
    const zoneNum = extractZoneNumber(z.entity_id, 'zone');
    if (zoneNum) {
        const modes = window._zoneModes || {};
        if (modes[zoneNum] && modes[zoneNum].state) {
            const modeVal = modes[zoneNum].state.toLowerCase();
            if (modeVal !== 'normal' && modeVal !== 'standard' && modeVal !== '' && modeVal !== 'unknown') {
                return modes[zoneNum].state;
            }
        }
    }
    return z.friendly_name || z.name || z.entity_id;
}

function resolveZoneName(entityId, fallbackName) {
    if (!entityId) return fallbackName || 'Unknown';
    const aliases = window._currentZoneAliases || {};
    if (aliases[entityId]) return aliases[entityId];
    const zoneNum = extractZoneNumber(entityId, 'zone');
    if (zoneNum) {
        const modes = window._zoneModes || {};
        if (modes[zoneNum] && modes[zoneNum].state) {
            const modeVal = modes[zoneNum].state.toLowerCase();
            if (modeVal !== 'normal' && modeVal !== 'standard' && modeVal !== '' && modeVal !== 'unknown') {
                return modes[zoneNum].state;
            }
        }
    }
    return fallbackName || entityId;
}

function getZoneLabel(zoneNum) {
    const aliases = window._currentZoneAliases || {};
    const modes = window._zoneModes || {};
    for (const [eid, alias] of Object.entries(aliases)) {
        const m = eid.match(/zone[_\\s]*(\\d+)/i);
        if (m && m[1] === String(zoneNum) && alias) return alias;
    }
    if (modes[zoneNum] && modes[zoneNum].state) {
        const modeVal = modes[zoneNum].state.toLowerCase();
        if (modeVal !== 'normal' && modeVal !== 'standard' && modeVal !== '' && modeVal !== 'unknown') {
            return modes[zoneNum].state;
        }
    }
    return 'Zone ' + zoneNum;
}

// --- Schedule entity classification ---
const SCHEDULE_PATTERNS = {
    schedule_enable: (eid, domain) =>
        domain === 'switch' && /schedule/.test(eid) && /enable/.test(eid) &&
        !/(monday|tuesday|wednesday|thursday|friday|saturday|sunday)/.test(eid) &&
        !/enable_zone/.test(eid),
    day_switches: (eid, domain) =>
        domain === 'switch' && /schedule/.test(eid) &&
        /(monday|tuesday|wednesday|thursday|friday|saturday|sunday)/.test(eid),
    start_times: (eid, domain) =>
        domain === 'text' && /start_time/.test(eid),
    run_durations: (eid, domain) =>
        domain === 'number' && /run_duration/.test(eid),
    repeat_cycles: (eid, domain) =>
        domain === 'number' && /repeat_cycle/.test(eid),
    zone_enables: (eid, domain) =>
        domain === 'switch' && /enable_zone/.test(eid),
    zone_modes: (eid, domain) =>
        domain === 'select' && /zone_\\d+_mode/.test(eid),
    system_controls: (eid, domain) =>
        domain === 'switch' && (/auto_advance/.test(eid) || /start_stop/.test(eid)),
};

function classifyScheduleEntity(entity) {
    const eid = (entity.entity_id || '').toLowerCase();
    const domain = entity.domain || '';
    for (const [category, matcher] of Object.entries(SCHEDULE_PATTERNS)) {
        if (matcher(eid, domain)) return category;
    }
    return null;
}

function extractStartTimeNumber(eid) {
    const match = eid.match(/start_time[_\\s]*(\\d+)/i);
    return match ? parseInt(match[1]) : 99;
}

function extractZoneNumber(eid, prefix) {
    const pattern = new RegExp(prefix + '[_\\\\s]*(\\\\d+)', 'i');
    const match = eid.match(pattern);
    return match ? match[1] : null;
}

function formatAddress(c) {
    const parts = [];
    if (c.address) parts.push(c.address);
    const cityStateZip = [];
    if (c.city) cityStateZip.push(c.city);
    if (c.state) cityStateZip.push(c.state);
    if (cityStateZip.length > 0) {
        let line = cityStateZip.join(', ');
        if (c.zip) line += ' ' + c.zip;
        parts.push(line);
    } else if (c.zip) {
        parts.push(c.zip);
    }
    return parts.join(', ');
}

// --- Location Map ---
async function initDetailMap(addrData) {
    const mapEl = document.getElementById('detailMap');
    const addr = formatAddress(addrData);
    if (!addr) { mapEl.style.display = 'none'; return; }
    if (geocodeCache[addr]) {
        showMap(geocodeCache[addr].lat, geocodeCache[addr].lon, addr);
        return;
    }
    try {
        const geo = await api('/geocode?q=' + encodeURIComponent(addr));
        if (geo.lat !== null && geo.lon !== null) {
            geocodeCache[addr] = { lat: geo.lat, lon: geo.lon };
            showMap(geo.lat, geo.lon, addr);
        } else {
            mapEl.style.display = 'none';
        }
    } catch (e) {
        console.warn('Geocoding failed:', e);
        mapEl.style.display = 'none';
    }
}

function showMap(lat, lon, label) {
    const mapEl = document.getElementById('detailMap');
    mapEl.style.display = 'block';
    if (leafletMap) { leafletMap.remove(); leafletMap = null; }
    leafletMap = L.map('detailMap').setView([lat, lon], 16);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
    }).addTo(leafletMap);
    L.marker([lat, lon]).addTo(leafletMap).bindPopup(esc(label)).openPopup();
    setTimeout(() => { if (leafletMap) leafletMap.invalidateSize(); }, 200);
}

// --- Dashboard Loading ---
async function loadDashboard() {
    loadStatus();
    loadWeather();
    loadZones();
    loadSensors();
    loadControls();
    loadHistory();
}

async function refreshDashboard() {
    loadDashboard();
}

// --- Status ---
let currentSystemPaused = false;

async function loadStatus() {
    const el = document.getElementById('detailStatus');
    try {
        const s = await api('/status');
        currentSystemPaused = !!s.system_paused;
        const btn = document.getElementById('pauseResumeBtn');
        if (s.system_paused) {
            btn.textContent = 'Resume System';
            btn.className = 'btn btn-primary btn-sm';
        } else {
            btn.textContent = 'Pause System';
            btn.className = 'btn btn-secondary btn-sm';
        }

        // Update address display from status (which includes config address)
        const addrEl = document.getElementById('dashAddress');
        const addr = formatAddress(s);
        if (addr) {
            addrEl.textContent = addr;
            addrEl.style.display = 'block';
        }

        el.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;">
            <div class="tile"><div class="tile-name">Connection</div><div class="tile-state ${s.ha_connected ? 'on' : ''}">${s.ha_connected ? 'Connected' : 'Disconnected'}</div></div>
            <div class="tile"><div class="tile-name">System</div><div class="tile-state ${s.system_paused ? '' : 'on'}">${s.system_paused ? 'Paused' : 'Active'}</div></div>
            <div class="tile"><div class="tile-name">Zones</div><div class="tile-state ${s.active_zones > 0 ? 'on' : ''}">${s.active_zones > 0 ? esc(resolveZoneName(s.active_zone_entity_id, s.active_zone_name)) + ' running' : 'Idle (' + (s.total_zones || 0) + ' zones)'}</div></div>
            <div class="tile"><div class="tile-name">Sensors</div><div class="tile-state">${s.total_sensors || 0} total</div></div>
            ${s.rain_delay_active ? '<div class="tile"><div class="tile-name">Rain Delay</div><div class="tile-state">Until ' + esc(s.rain_delay_until || 'unknown') + '</div></div>' : ''}
        </div>`;
    } catch (e) {
        el.innerHTML = '<div style="color:#e74c3c;">Failed to load status: ' + esc(e.message) + '</div>';
    }
}

async function togglePauseResume() {
    const action = currentSystemPaused ? 'resume' : 'pause';
    if (!currentSystemPaused && !confirm('Pause the irrigation system? All active zones will be stopped.')) return;
    try {
        await api('/system/' + action, { method: 'POST' });
        showToast('System ' + (action === 'pause' ? 'paused' : 'resumed'));
        setTimeout(() => loadStatus(), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Zones ---
async function loadZones() {
    const el = document.getElementById('detailZones');
    try {
        const data = await api('/zones');
        const zones = Array.isArray(data) ? data : (data.zones || []);
        if (zones.length === 0) { el.innerHTML = '<div class="empty-state"><p>No zones found</p></div>'; return; }
        el.innerHTML = '<div class="tile-grid">' + zones.map(z => {
            const zId = z.name || z.entity_id;
            const isOn = z.state === 'on';
            const displayName = getZoneDisplayName(z);
            return `
            <div class="tile ${isOn ? 'active' : ''}">
                <div class="tile-name">
                    ${esc(displayName)}
                    <span style="cursor:pointer;font-size:11px;color:#1a7a4c;margin-left:6px;"
                          onclick="event.stopPropagation();renameZone(\\'${z.entity_id}\\')">&#9998;</span>
                </div>
                <div class="tile-state ${isOn ? 'on' : ''}">${isOn ? 'Running' : 'Off'}</div>
                <div class="tile-actions" style="flex-wrap:wrap;">
                    ${isOn
                        ? '<button class="btn btn-danger btn-sm" onclick="stopZone(\\'' + zId + '\\')">Stop</button>'
                        : '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + zId + '\\', null)">Start</button>' +
                          '<span style="display:flex;align-items:center;gap:4px;margin-top:4px;"><input type="number" id="dur_' + zId + '" min="1" max="480" placeholder="min" style="width:60px;padding:3px 6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">' +
                          '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + zId + '\\', document.getElementById(\\'dur_' + zId + '\\').value)">Timed</button></span>'
                    }
                </div>
            </div>`;
        }).join('') + '</div>';
    } catch (e) {
        el.innerHTML = '<div style="color:#e74c3c;">Failed to load zones: ' + esc(e.message) + '</div>';
    }
}

async function startZone(zoneId, durationMinutes) {
    try {
        const body = {};
        if (durationMinutes && parseInt(durationMinutes) > 0) {
            body.duration_minutes = parseInt(durationMinutes);
        }
        await api('/zones/' + zoneId + '/start', { method: 'POST', body: JSON.stringify(body) });
        showToast('Zone started' + (body.duration_minutes ? ' for ' + body.duration_minutes + ' min' : ''));
        setTimeout(() => loadZones(), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

async function stopZone(zoneId) {
    try {
        await api('/zones/' + zoneId + '/stop', { method: 'POST' });
        showToast('Zone stopped');
        setTimeout(() => loadZones(), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

async function stopAllZones() {
    if (!confirm('Emergency stop ALL zones?')) return;
    try {
        await api('/zones/stop_all', { method: 'POST' });
        showToast('All zones stopped');
        setTimeout(() => loadZones(), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

async function renameZone(entityId) {
    const aliases = window._currentZoneAliases || {};
    const currentName = aliases[entityId] || entityId.split('.').pop().replace(/_/g, ' ');
    const newName = prompt('Enter alias for this zone (leave empty to clear):', currentName);
    if (newName === null) return;
    if (newName.trim() === '') {
        delete aliases[entityId];
    } else {
        aliases[entityId] = newName.trim();
    }
    window._currentZoneAliases = aliases;
    try {
        await api('/zone_aliases', {
            method: 'PUT',
            body: JSON.stringify({ zone_aliases: aliases }),
        });
        showToast('Zone renamed');
        loadZones();
        loadControls();
    } catch (e) { showToast(e.message, 'error'); }
}

// --- WiFi Signal Quality ---
function wifiSignalBadge(sensor) {
    const eid = (sensor.entity_id || '').toLowerCase();
    const name = (sensor.friendly_name || sensor.name || '').toLowerCase();
    const unit = (sensor.unit_of_measurement || '').toLowerCase();
    const isWifi = (eid.includes('wifi') || eid.includes('signal') || eid.includes('rssi')
        || name.includes('wi-fi') || name.includes('wifi') || name.includes('signal strength'))
        && (unit === 'dbm' || unit === 'db');
    if (!isWifi) return '';
    const val = parseFloat(sensor.state);
    if (isNaN(val)) return '';
    let label, color;
    if (val >= -50)      { label = 'Great'; color = '#1a7a1a'; }
    else if (val >= -60) { label = 'Good';  color = '#3a9a2a'; }
    else if (val >= -70) { label = 'Poor';  color = '#d4930a'; }
    else                 { label = 'Bad';   color = '#cc2222'; }
    return ' <span style="font-weight:600;color:' + color + ';">(' + label + ')</span>';
}

// --- Sensors ---
async function loadSensors() {
    const el = document.getElementById('detailSensors');
    try {
        const data = await api('/sensors');
        const sensors = Array.isArray(data) ? data : (data.sensors || []);
        if (sensors.length === 0) { el.innerHTML = '<div class="empty-state"><p>No sensors found</p></div>'; return; }
        el.innerHTML = '<div class="tile-grid">' + sensors.map(s => `
            <div class="tile">
                <div class="tile-name">${esc(s.friendly_name || s.name || s.entity_id)}</div>
                <div class="tile-state">${esc(s.state)}${s.unit_of_measurement ? ' ' + esc(s.unit_of_measurement) : ''}${wifiSignalBadge(s)}</div>
            </div>`).join('') + '</div>';
    } catch (e) {
        el.innerHTML = '<div style="color:#e74c3c;">Failed to load sensors: ' + esc(e.message) + '</div>';
    }
}

// --- Device Controls (also populates Schedule card) ---
async function loadControls() {
    const controlsEl = document.getElementById('detailControls');
    const scheduleEl = document.getElementById('detailSchedule');
    try {
        const data = await api('/entities');
        const allEntities = Array.isArray(data) ? data : (data.entities || []);

        const scheduleByCategory = {
            schedule_enable: [], day_switches: [], start_times: [],
            run_durations: [], repeat_cycles: [], zone_enables: [],
            zone_modes: [], system_controls: []
        };
        const controlEntities = [];

        for (const e of allEntities) {
            const cat = classifyScheduleEntity(e);
            if (cat) {
                scheduleByCategory[cat].push(e);
            } else {
                const eid = (e.entity_id || '').toLowerCase();
                if (/valve_\\d+/.test(eid)) continue;
                if (e.domain === 'number' && /repeat/.test(eid) && !/repeat_cycle/.test(eid)) continue;
                controlEntities.push(e);
            }
        }

        // Build zone mode map
        window._zoneModes = {};
        for (const zm of scheduleByCategory.zone_modes) {
            const num = extractZoneNumber(zm.entity_id, 'zone');
            if (num) window._zoneModes[num] = { state: zm.state, entity: zm };
        }

        // Render Device Controls
        if (controlEntities.length === 0) {
            controlsEl.innerHTML = '<div class="empty-state"><p>No device controls found</p></div>';
        } else {
            const groups = {};
            controlEntities.forEach(e => {
                const d = e.domain || 'unknown';
                if (!groups[d]) groups[d] = [];
                groups[d].push(e);
            });
            const domainLabels = {
                'switch': 'Switches', 'number': 'Run Times', 'select': 'Selects',
                'button': 'Buttons', 'text': 'Text Inputs', 'light': 'Lights'
            };
            const domainOrder = ['switch', 'number', 'select', 'text', 'button', 'light'];
            const sortedDomains = Object.keys(groups).sort((a, b) => {
                const ai = domainOrder.indexOf(a); const bi = domainOrder.indexOf(b);
                return (ai === -1 ? 99 : ai) - (bi === -1 ? 99 : bi);
            });
            let html = '';
            for (const domain of sortedDomains) {
                const label = domainLabels[domain] || domain.charAt(0).toUpperCase() + domain.slice(1);
                html += '<div style="margin-bottom:16px;"><div style="font-size:13px;font-weight:600;color:#7f8c8d;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">' + esc(label) + '</div>';
                html += '<div class="tile-grid">';
                for (const e of groups[domain]) {
                    html += renderControlTile(e);
                }
                html += '</div></div>';
            }
            controlsEl.innerHTML = html;
        }

        // Render Schedule card
        renderScheduleCard(scheduleByCategory);

    } catch (e) {
        controlsEl.innerHTML = '<div style="color:#e74c3c;">Failed to load controls: ' + esc(e.message) + '</div>';
        scheduleEl.innerHTML = '<div style="color:#e74c3c;">Failed to load schedule: ' + esc(e.message) + '</div>';
    }
}

function renderScheduleCard(sched) {
    const el = document.getElementById('detailSchedule');
    const { schedule_enable, day_switches, start_times, run_durations, repeat_cycles, zone_enables, zone_modes, system_controls } = sched;
    const total = schedule_enable.length + day_switches.length + start_times.length + run_durations.length +
        repeat_cycles.length + zone_enables.length + zone_modes.length + system_controls.length;

    if (total === 0) {
        el.innerHTML = '<div class="empty-state"><p>No schedule entities detected on this device.</p></div>';
        return;
    }

    let html = '';

    // --- Schedule Master Enable ---
    if (schedule_enable.length > 0) {
        const se = schedule_enable[0];
        const isOn = se.state === 'on';
        html += '<div class="schedule-section" style="margin-bottom:16px;">' +
            '<div style="display:flex;align-items:center;justify-content:space-between;' +
            'padding:12px 16px;border-radius:8px;background:' + (isOn ? '#e8f5e9' : '#fbe9e7') + ';">' +
            '<div><div style="font-size:15px;font-weight:600;color:' + (isOn ? '#27ae60' : '#e74c3c') + ';">' +
            'Schedule ' + (isOn ? 'Enabled' : 'Disabled') + '</div>' +
            '<div style="font-size:12px;color:#7f8c8d;">Master schedule on/off</div></div>' +
            '<button class="btn ' + (isOn ? 'btn-danger' : 'btn-primary') + '" ' +
            'onclick="setEntityValue(\\'' + se.entity_id + '\\',\\'switch\\',' +
            '{state:\\'' + (isOn ? 'off' : 'on') + '\\'})">' +
            (isOn ? 'Disable Schedule' : 'Enable Schedule') + '</button>' +
            '</div></div>';
    }

    // --- Days of Week ---
    if (day_switches.length > 0) {
        html += '<div class="schedule-section"><div class="schedule-section-label">Days of Week</div><div class="days-row">';
        const dayOrder = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday'];
        const dayLabels = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
        for (let i = 0; i < dayOrder.length; i++) {
            const dayEntity = day_switches.find(e => e.entity_id.toLowerCase().includes(dayOrder[i]));
            if (dayEntity) {
                const isOn = dayEntity.state === 'on';
                html += '<div class="day-toggle ' + (isOn ? 'active' : '') + '" ' +
                    'onclick="setEntityValue(\\'' + dayEntity.entity_id + '\\',\\'switch\\',' +
                    '{state:\\'' + (isOn ? 'off' : 'on') + '\\'})">' +
                    dayLabels[i] + '</div>';
            }
        }
        html += '</div></div>';
    }

    // --- Start Times ---
    if (start_times.length > 0) {
        const sorted = [...start_times].sort((a, b) => extractStartTimeNumber(a.entity_id) - extractStartTimeNumber(b.entity_id));
        html += '<div class="schedule-section"><div class="schedule-section-label">Start Times</div><div class="start-times-grid">';
        for (const st of sorted) {
            const num = extractStartTimeNumber(st.entity_id);
            const label = 'Start Time ' + (num < 99 ? num : '?');
            const eid = st.entity_id;
            const inputId = 'st_' + eid.replace(/[^a-zA-Z0-9]/g, '_');
            html += '<div class="tile">' +
                '<div class="tile-name">' + esc(label) + '</div>' +
                '<div class="tile-state">' + esc(st.state) + '</div>' +
                '<div class="tile-actions" style="flex-wrap:wrap;gap:4px;">' +
                '<input type="text" id="' + inputId + '" value="' + esc(st.state) + '" placeholder="HH:MM" style="width:100px;padding:3px 6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid +
                '\\',\\'text\\',{value:document.getElementById(\\'' + inputId + '\\').value})">Set</button>' +
                '</div></div>';
        }
        html += '</div></div>';
    }

    // --- Zone Settings ---
    if (zone_enables.length > 0 || run_durations.length > 0) {
        html += '<div class="schedule-section"><div class="schedule-section-label">Zone Settings</div>';
        const zoneMap = {};
        for (const ze of zone_enables) {
            const num = extractZoneNumber(ze.entity_id, 'enable_zone');
            if (num !== null) {
                if (!zoneMap[num]) zoneMap[num] = {};
                zoneMap[num].enable = ze;
            }
        }
        for (const rd of run_durations) {
            const num = extractZoneNumber(rd.entity_id, 'zone');
            if (num !== null) {
                if (!zoneMap[num]) zoneMap[num] = {};
                zoneMap[num].duration = rd;
            }
        }
        for (const zm of zone_modes) {
            const num = extractZoneNumber(zm.entity_id, 'zone');
            if (num !== null) {
                if (!zoneMap[num]) zoneMap[num] = {};
                zoneMap[num].mode = zm;
            }
        }
        const sortedZones = Object.keys(zoneMap).sort((a, b) => parseInt(a) - parseInt(b));
        const hasMode = sortedZones.some(zn => zoneMap[zn].mode);

        html += '<table class="zone-settings-table"><thead><tr>' +
            '<th>Zone</th>' + (hasMode ? '<th>Mode</th>' : '') +
            '<th>Schedule Enable</th><th>Run Duration</th></tr></thead><tbody>';
        for (const zn of sortedZones) {
            const { enable, duration, mode } = zoneMap[zn];
            const zoneLabel = getZoneLabel(zn);
            const modeVal = mode ? mode.state.toLowerCase() : '';
            const isPumpOrMaster = /pump|master|relay/.test(modeVal);
            html += '<tr><td><strong>' + esc(zoneLabel) + '</strong></td>';
            if (hasMode) {
                if (mode) {
                    const modeAttrs = mode.attributes || {};
                    const modeOptions = modeAttrs.options || [];
                    const modeEid = mode.entity_id;
                    const selId = 'mode_' + modeEid.replace(/[^a-zA-Z0-9]/g, '_');
                    const optionsHtml = modeOptions.map(o =>
                        '<option value="' + esc(o) + '"' + (o === mode.state ? ' selected' : '') + '>' + esc(o) + '</option>'
                    ).join('');
                    html += '<td><select id="' + selId + '" style="padding:3px 6px;border:1px solid #ddd;border-radius:4px;font-size:12px;" ' +
                        'onchange="setEntityValue(\\'' + modeEid +
                        '\\',\\'select\\',{option:document.getElementById(\\'' + selId + '\\').value})">' +
                        optionsHtml + '</select></td>';
                } else {
                    html += '<td style="color:#95a5a6;">-</td>';
                }
            }
            if (enable) {
                const isOn = enable.state === 'on';
                html += '<td><button class="btn ' + (isOn ? 'btn-primary' : 'btn-secondary') + ' btn-sm" ' +
                    'onclick="setEntityValue(\\'' + enable.entity_id + '\\',\\'switch\\',' +
                    '{state:\\'' + (isOn ? 'off' : 'on') + '\\'})">' +
                    (isOn ? 'Enabled' : 'Disabled') + '</button></td>';
            } else {
                html += '<td style="color:#95a5a6;">-</td>';
            }
            if (isPumpOrMaster) {
                html += '<td style="color:#95a5a6;font-style:italic;">Firmware controlled</td>';
            } else if (duration) {
                const attrs = duration.attributes || {};
                const unit = attrs.unit_of_measurement || 'min';
                const eid = duration.entity_id;
                const inputId = 'dur_sched_' + eid.replace(/[^a-zA-Z0-9]/g, '_');
                html += '<td><input type="number" id="' + inputId + '" value="' + esc(duration.state) + '" ' +
                    'min="' + (attrs.min || 0) + '" max="' + (attrs.max || 999) + '" step="' + (attrs.step || 1) + '" ' +
                    'style="width:70px;padding:3px 6px;border:1px solid #ddd;border-radius:4px;font-size:12px;"> ' +
                    esc(unit) + ' ' +
                    '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid +
                    '\\',\\'number\\',{value:parseFloat(document.getElementById(\\'' + inputId + '\\').value)})">Set</button></td>';
            } else {
                html += '<td style="color:#95a5a6;">-</td>';
            }
            html += '</tr>';
        }
        html += '</tbody></table></div>';
    }

    // --- System Controls ---
    if (system_controls.length > 0) {
        html += '<div class="schedule-section"><div class="schedule-section-label">System Controls</div><div class="system-controls-row">';
        for (const sc of system_controls) {
            html += renderControlTile(sc);
        }
        html += '</div></div>';
    }

    // --- Repeat Cycles ---
    if (repeat_cycles.length > 0) {
        html += '<div class="schedule-section"><div class="schedule-section-label">Repeat Cycles</div><div class="tile-grid">';
        for (const rc of repeat_cycles) {
            html += renderControlTile(rc);
        }
        html += '</div></div>';
    }

    el.innerHTML = html;
}

function renderControlTile(e) {
    const name = esc(e.friendly_name || e.name || e.entity_id);
    const eid = e.entity_id;
    const domain = e.domain;
    const state = e.state || 'unknown';
    const attrs = e.attributes || {};

    if (domain === 'switch' || domain === 'light') {
        const isOn = state === 'on';
        return '<div class="tile ' + (isOn ? 'active' : '') + '">' +
            '<div class="tile-name">' + name + '</div>' +
            '<div class="tile-state ' + (isOn ? 'on' : '') + '">' + (isOn ? 'On' : 'Off') + '</div>' +
            '<div class="tile-actions">' +
                (isOn
                    ? '<button class="btn btn-secondary btn-sm" onclick="setEntityValue(\\'' + eid + '\\',\\'' + domain + '\\',{state:\\'off\\'})">Turn Off</button>'
                    : '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid + '\\',\\'' + domain + '\\',{state:\\'on\\'})">Turn On</button>'
                ) +
            '</div></div>';
    }

    if (domain === 'number') {
        const min = attrs.min !== undefined ? attrs.min : '';
        const max = attrs.max !== undefined ? attrs.max : '';
        const step = attrs.step || 1;
        const unit = attrs.unit_of_measurement || '';
        return '<div class="tile">' +
            '<div class="tile-name">' + name + '</div>' +
            '<div class="tile-state">' + esc(state) + (unit ? ' ' + esc(unit) : '') + '</div>' +
            '<div class="tile-actions" style="flex-wrap:wrap;gap:4px;">' +
                '<input type="number" id="num_' + eid + '" value="' + esc(state) + '" min="' + min + '" max="' + max + '" step="' + step + '" style="width:80px;padding:3px 6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid + '\\',\\'number\\',{value:parseFloat(document.getElementById(\\'num_' + eid + '\\').value)})">Set</button>' +
            '</div></div>';
    }

    if (domain === 'select') {
        const options = attrs.options || [];
        const optionsHtml = options.map(o => '<option value="' + esc(o) + '"' + (o === state ? ' selected' : '') + '>' + esc(o) + '</option>').join('');
        return '<div class="tile">' +
            '<div class="tile-name">' + name + '</div>' +
            '<div class="tile-state">' + esc(state) + '</div>' +
            '<div class="tile-actions" style="flex-wrap:wrap;gap:4px;">' +
                '<select id="sel_' + eid + '" style="padding:3px 6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">' + optionsHtml + '</select>' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid + '\\',\\'select\\',{option:document.getElementById(\\'sel_' + eid + '\\').value})">Set</button>' +
            '</div></div>';
    }

    if (domain === 'button') {
        return '<div class="tile">' +
            '<div class="tile-name">' + name + '</div>' +
            '<div class="tile-state">' + esc(state) + '</div>' +
            '<div class="tile-actions">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid + '\\',\\'button\\',{})">Press</button>' +
            '</div></div>';
    }

    if (domain === 'text') {
        return '<div class="tile">' +
            '<div class="tile-name">' + name + '</div>' +
            '<div class="tile-state">' + esc(state) + '</div>' +
            '<div class="tile-actions" style="flex-wrap:wrap;gap:4px;">' +
                '<input type="text" id="txt_' + eid + '" value="' + esc(state) + '" style="width:120px;padding:3px 6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid + '\\',\\'text\\',{value:document.getElementById(\\'txt_' + eid + '\\').value})">Set</button>' +
            '</div></div>';
    }

    return '<div class="tile">' +
        '<div class="tile-name">' + name + '</div>' +
        '<div class="tile-state">' + esc(state) + '</div>' +
        '<div style="font-size:11px;color:#95a5a6;margin-top:4px;">' + esc(domain) + '</div>' +
        '</div>';
}

async function setEntityValue(entityId, domain, bodyObj) {
    try {
        await api('/entities/' + entityId + '/set', {
            method: 'POST',
            body: JSON.stringify(bodyObj),
        });
        showToast('Updated ' + entityId.split('.').pop());
        setTimeout(() => loadControls(), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- History ---
async function loadHistory() {
    const el = document.getElementById('detailHistory');
    try {
        const hours = document.getElementById('historyRange') ? document.getElementById('historyRange').value : '24';
        const data = await api('/history/runs?hours=' + hours);
        const events = data.events || [];
        if (events.length === 0) { el.innerHTML = '<div class="empty-state"><p>No run events in the selected time range</p></div>'; return; }

        // Show current weather context summary if available
        const cw = data.current_weather || {};
        let weatherSummary = '';
        if (cw.condition) {
            const condIcons = {'sunny':'☀️','clear-night':'🌙','partlycloudy':'⛅','cloudy':'☁️','rainy':'🌧️','pouring':'🌧️','snowy':'❄️','windy':'💨','fog':'🌫️','lightning':'⚡','lightning-rainy':'⛈️','hail':'🧊'};
            const wIcon = condIcons[cw.condition] || '🌡️';
            const mult = cw.watering_multiplier != null ? cw.watering_multiplier : 1.0;
            const multColor = mult === 1.0 ? '#155724' : mult < 1 ? '#856404' : '#721c24';
            const multBg = mult === 1.0 ? '#d4edda' : mult < 1 ? '#fff3cd' : '#f8d7da';
            weatherSummary = '<div style="margin-bottom:12px;padding:8px 12px;background:#f0f8ff;border-radius:8px;font-size:12px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">' +
                '<span>' + wIcon + ' <strong>' + esc(cw.condition) + '</strong></span>' +
                (cw.temperature != null ? '<span>🌡️ ' + cw.temperature + '°</span>' : '') +
                (cw.humidity != null ? '<span>💧 ' + cw.humidity + '%</span>' : '') +
                (cw.wind_speed != null ? '<span>💨 ' + cw.wind_speed + ' mph</span>' : '') +
                '<span style="background:' + multBg + ';color:' + multColor + ';padding:2px 8px;border-radius:10px;font-weight:600;">' + mult + 'x</span>' +
                '</div>';
        }

        el.innerHTML = weatherSummary +
            '<table style="width:100%;font-size:13px;border-collapse:collapse;"><thead><tr style="text-align:left;border-bottom:2px solid #eee;"><th style="padding:6px;">Zone</th><th style="padding:6px;">State</th><th style="padding:6px;">Time</th><th style="padding:6px;">Duration</th><th style="padding:6px;">Weather</th></tr></thead><tbody>' +
            events.slice(0, 100).map(e => {
                const wx = e.weather || {};
                let wxCell = '-';
                if (wx.condition) {
                    const ci = {'sunny':'☀️','clear-night':'🌙','partlycloudy':'⛅','cloudy':'☁️','rainy':'🌧️','pouring':'🌧️','snowy':'❄️','windy':'💨','fog':'🌫️','lightning':'⚡','lightning-rainy':'⛈️','hail':'🧊'};
                    const wi = ci[wx.condition] || '🌡️';
                    const wm = wx.watering_multiplier != null ? wx.watering_multiplier : '';
                    const wmColor = wm === 1.0 ? '#27ae60' : wm < 1 ? '#f39c12' : wm > 1 ? '#e74c3c' : '#999';
                    wxCell = wi + ' ' + (wx.temperature != null ? wx.temperature + '° ' : '') +
                        (wm ? '<span style="color:' + wmColor + ';font-weight:600;">' + wm + 'x</span>' : '');
                    const rules = wx.active_adjustments || wx.rules_triggered || [];
                    if (rules.length > 0) {
                        wxCell += '<div style="font-size:10px;color:#856404;margin-top:2px;">' + rules.map(r => r.replace(/_/g, ' ')).join(', ') + '</div>';
                    }
                }
                const srcLabel = e.source ? '<div style="font-size:10px;color:#999;">' + esc(e.source) + '</div>' : '';
                return `<tr style="border-bottom:1px solid #f0f0f0;">
                <td style="padding:6px;">${esc(resolveZoneName(e.entity_id, e.zone_name))}${srcLabel}</td>
                <td style="padding:6px;">${e.state === 'on' || e.state === 'open' ? '<span style="color:#27ae60;">ON</span>' : '<span style="color:#95a5a6;">OFF</span>'}</td>
                <td style="padding:6px;">${formatTime(e.timestamp)}</td>
                <td style="padding:6px;">${e.duration_seconds ? Math.round(e.duration_seconds / 60) + ' min' : '-'}</td>
                <td style="padding:6px;font-size:12px;">${wxCell}</td>
            </tr>`;
            }).join('') + '</tbody></table>';
    } catch (e) {
        el.innerHTML = '<div style="color:#e74c3c;">Failed to load history: ' + esc(e.message) + '</div>';
    }
}

function formatTime(ts) {
    if (!ts) return '-';
    try {
        const d = new Date(ts);
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch { return ts; }
}

// --- Weather ---
const WBASE = (window.location.pathname.replace(/\\/+$/, '')) + '/api';

async function wapi(path, options = {}) {
    const res = await fetch(WBASE + path, {
        headers: { 'Content-Type': 'application/json', ...options.headers },
        ...options,
    });
    const data = await res.json();
    if (!res.ok) {
        const detail = data.detail || data.error || JSON.stringify(data);
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
    return data;
}

async function loadWeather() {
    const card = document.getElementById('weatherCard');
    const body = document.getElementById('weatherCardBody');
    const badge = document.getElementById('weatherMultBadge');
    try {
        const data = await api('/weather');
        if (!data.weather_enabled) {
            card.style.display = 'none';
            return;
        }
        card.style.display = 'block';
        const w = data.weather || {};
        if (w.error) {
            body.innerHTML = '<div style="color:#999;text-align:center;padding:12px;">' + esc(w.error) + '</div>';
            return;
        }

        const condIcons = {
            'sunny': '☀️', 'clear-night': '🌙', 'partlycloudy': '⛅',
            'cloudy': '☁️', 'rainy': '🌧️', 'pouring': '🌧️',
            'snowy': '❄️', 'windy': '💨', 'fog': '🌫️',
            'lightning': '⚡', 'lightning-rainy': '⛈️', 'hail': '🧊',
        };
        const icon = condIcons[w.condition] || '🌡️';
        const mult = data.watering_multiplier != null ? data.watering_multiplier : 1.0;
        badge.textContent = mult + 'x';
        badge.style.background = mult === 1.0 ? '#d4edda' : mult < 1 ? '#fff3cd' : '#f8d7da';
        badge.style.color = mult === 1.0 ? '#155724' : mult < 1 ? '#856404' : '#721c24';

        let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;">';
        html += '<div style="background:#f0f8ff;border-radius:8px;padding:10px;text-align:center;">';
        html += '<div style="font-size:24px;">' + icon + '</div>';
        html += '<div style="font-weight:600;text-transform:capitalize;font-size:13px;">' + esc(w.condition || 'unknown') + '</div>';
        html += '</div>';
        html += '<div style="background:#f8f9fa;border-radius:8px;padding:10px;">';
        html += '<div style="color:#999;font-size:11px;">Temperature</div>';
        html += '<div style="font-weight:600;font-size:16px;">' + (w.temperature != null ? w.temperature + (w.temperature_unit || '°F') : 'N/A') + '</div>';
        html += '</div>';
        html += '<div style="background:#f8f9fa;border-radius:8px;padding:10px;">';
        html += '<div style="color:#999;font-size:11px;">Humidity</div>';
        html += '<div style="font-weight:600;font-size:16px;">' + (w.humidity != null ? w.humidity + '%' : 'N/A') + '</div>';
        html += '</div>';
        html += '<div style="background:#f8f9fa;border-radius:8px;padding:10px;">';
        html += '<div style="color:#999;font-size:11px;">Wind</div>';
        html += '<div style="font-weight:600;font-size:16px;">' + (w.wind_speed != null ? w.wind_speed + ' ' + (w.wind_speed_unit || 'mph') : 'N/A') + '</div>';
        html += '</div>';
        html += '</div>';

        // 3-day forecast
        const forecast = w.forecast || [];
        if (forecast.length > 0) {
            html += '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;color:#7f8c8d;text-transform:uppercase;margin-bottom:8px;">Forecast</div>';
            html += '<div style="display:flex;gap:8px;overflow-x:auto;">';
            for (let i = 0; i < Math.min(forecast.length, 5); i++) {
                const f = forecast[i];
                const dt = f.datetime ? new Date(f.datetime) : null;
                const dayLabel = dt ? dt.toLocaleDateString('en-US', { weekday: 'short' }) : '';
                const fIcon = condIcons[f.condition] || '🌡️';
                const precip = f.precipitation_probability || 0;
                html += '<div style="flex:0 0 auto;background:#f8f9fa;border-radius:8px;padding:8px 12px;text-align:center;min-width:70px;">';
                html += '<div style="font-size:11px;color:#999;">' + esc(dayLabel) + '</div>';
                html += '<div style="font-size:18px;">' + fIcon + '</div>';
                html += '<div style="font-size:12px;font-weight:600;">' + (f.temperature != null ? f.temperature + '°' : '') + '</div>';
                if (precip > 0) {
                    html += '<div style="font-size:10px;color:#3498db;">💧 ' + precip + '%</div>';
                }
                html += '</div>';
            }
            html += '</div></div>';
        }

        // Active adjustments
        const adjustments = data.active_adjustments || [];
        if (adjustments.length > 0) {
            html += '<div style="margin-top:12px;padding:10px;background:#fff3cd;border-radius:8px;font-size:12px;">';
            html += '<strong style="color:#856404;">Active Weather Adjustments:</strong>';
            html += '<ul style="margin:4px 0 0 16px;color:#856404;">';
            for (const adj of adjustments) {
                html += '<li>' + esc(adj.reason || adj.rule) + '</li>';
            }
            html += '</ul></div>';
        }

        // --- Weather Rules Editor ---
        html += '<div style="margin-top:16px;border-top:1px solid #eee;padding-top:16px;">';
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">';
        html += '<div style="font-size:14px;font-weight:600;">Weather Rules</div>';
        html += '<div style="display:flex;gap:6px;">';
        html += '<button class="btn btn-secondary btn-sm" onclick="evaluateWeatherNow()">Test Rules Now</button>';
        html += '<button class="btn btn-secondary btn-sm" onclick="exportWeatherLogCSV()">Export Log</button>';
        html += '<button class="btn btn-danger btn-sm" onclick="clearWeatherLog()">Clear Log</button>';
        html += '</div>';
        html += '</div>';
        html += '<div id="weatherRulesContainer"><div class="loading">Loading rules...</div></div>';
        html += '</div>';

        body.innerHTML = html;

        // Load rules into the container
        loadWeatherRules();
    } catch (e) {
        card.style.display = 'none';
    }
}

async function loadWeatherRules() {
    const container = document.getElementById('weatherRulesContainer');
    if (!container) return;
    try {
        const data = await wapi('/weather/rules');
        const rules = data.rules || {};
        let html = '<div style="display:flex;flex-direction:column;gap:8px;">';

        // Rule 1: Rain Detection
        const r1 = rules.rain_detection || {};
        html += buildRuleRow('rain_detection', 'Rain Detection', 'Pause when currently raining', r1.enabled, [
            { id: 'rain_detection_resume_delay_hours', label: 'Resume delay (hours)', value: r1.resume_delay_hours || 2, type: 'number', min: 0, max: 24, step: 1 }
        ]);

        // Rule 2: Rain Forecast
        const r2 = rules.rain_forecast || {};
        html += buildRuleRow('rain_forecast', 'Rain Forecast', 'Skip when rain probability exceeds threshold', r2.enabled, [
            { id: 'rain_forecast_probability_threshold', label: 'Probability %', value: r2.probability_threshold || 60, type: 'number', min: 10, max: 100, step: 5 }
        ]);

        // Rule 3: Precipitation Threshold
        const r3 = rules.precipitation_threshold || {};
        html += buildRuleRow('precipitation_threshold', 'Precipitation Amount', 'Skip when expected rainfall exceeds threshold', r3.enabled, [
            { id: 'precipitation_threshold_mm', label: 'Threshold (mm)', value: r3.skip_if_rain_above_mm || 6, type: 'number', min: 1, max: 50, step: 1 }
        ]);

        // Rule 4: Freeze Protection
        const r4 = rules.temperature_freeze || {};
        html += buildRuleRow('temperature_freeze', 'Freeze Protection', 'Skip when temperature is at or below freezing', r4.enabled, [
            { id: 'temperature_freeze_f', label: 'Threshold (°F)', value: r4.freeze_threshold_f || 35, type: 'number', min: 20, max: 45, step: 1 },
            { id: 'temperature_freeze_c', label: 'Threshold (°C)', value: r4.freeze_threshold_c || 2, type: 'number', min: -5, max: 7, step: 1 }
        ]);

        // Rule 5: Cool Temperature
        const r5 = rules.temperature_cool || {};
        html += buildRuleRow('temperature_cool', 'Cool Temperature', 'Reduce watering in cool weather', r5.enabled, [
            { id: 'temperature_cool_f', label: 'Below (°F)', value: r5.cool_threshold_f || 60, type: 'number', min: 40, max: 75, step: 1 },
            { id: 'temperature_cool_c', label: 'Below (°C)', value: r5.cool_threshold_c || 15, type: 'number', min: 5, max: 25, step: 1 },
            { id: 'temperature_cool_reduction', label: 'Reduce %', value: r5.reduction_percent || 25, type: 'number', min: 5, max: 75, step: 5 }
        ]);

        // Rule 6: Hot Temperature
        const r6 = rules.temperature_hot || {};
        html += buildRuleRow('temperature_hot', 'Hot Temperature', 'Increase watering in hot weather', r6.enabled, [
            { id: 'temperature_hot_f', label: 'Above (°F)', value: r6.hot_threshold_f || 95, type: 'number', min: 80, max: 120, step: 1 },
            { id: 'temperature_hot_c', label: 'Above (°C)', value: r6.hot_threshold_c || 35, type: 'number', min: 25, max: 50, step: 1 },
            { id: 'temperature_hot_increase', label: 'Increase %', value: r6.increase_percent || 25, type: 'number', min: 5, max: 75, step: 5 }
        ]);

        // Rule 7: Wind Speed
        const r7 = rules.wind_speed || {};
        html += buildRuleRow('wind_speed', 'High Wind', 'Skip when wind exceeds threshold', r7.enabled, [
            { id: 'wind_speed_mph', label: 'Max (mph)', value: r7.max_wind_speed_mph || 20, type: 'number', min: 5, max: 60, step: 1 },
            { id: 'wind_speed_kmh', label: 'Max (km/h)', value: r7.max_wind_speed_kmh || 32, type: 'number', min: 8, max: 100, step: 1 }
        ]);

        // Rule 8: Humidity
        const r8 = rules.humidity || {};
        html += buildRuleRow('humidity', 'High Humidity', 'Reduce watering when humidity is high', r8.enabled, [
            { id: 'humidity_threshold', label: 'Above %', value: r8.high_humidity_threshold || 80, type: 'number', min: 50, max: 100, step: 5 },
            { id: 'humidity_reduction', label: 'Reduce %', value: r8.reduction_percent || 20, type: 'number', min: 5, max: 75, step: 5 }
        ]);

        // Rule 9: Seasonal Adjustment
        const r9 = rules.seasonal_adjustment || {};
        const months = r9.monthly_multipliers || {};
        const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
        let seasonInputs = '';
        for (let i = 1; i <= 12; i++) {
            const val = months[String(i)] != null ? months[String(i)] : (i >= 3 && i <= 11 ? 1.0 : 0.0);
            seasonInputs += '<div style="display:flex;align-items:center;gap:4px;">' +
                '<span style="font-size:11px;color:#999;width:28px;">' + monthNames[i-1] + '</span>' +
                '<input type="number" id="seasonal_month_' + i + '" value="' + val + '" min="0" max="2" step="0.1" ' +
                'style="width:55px;padding:2px 4px;border:1px solid #ddd;border-radius:4px;font-size:11px;"></div>';
        }
        html += '<div style="background:#f8f9fa;border:1px solid #eee;border-radius:8px;padding:10px;margin-bottom:4px;">';
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">';
        html += '<div><div style="font-weight:600;font-size:13px;">Seasonal Adjustment</div>';
        html += '<div style="font-size:11px;color:#999;">Monthly watering multiplier (0=off, 1=normal)</div></div>';
        html += '<label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;">';
        html += '<input type="checkbox" id="rule_seasonal_adjustment" ' + (r9.enabled ? 'checked' : '') + '> Enabled</label>';
        html += '</div>';
        html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(95px,1fr));gap:4px;">' + seasonInputs + '</div>';
        html += '</div>';

        html += '</div>';

        // Save button
        html += '<div style="margin-top:12px;display:flex;gap:8px;">';
        html += '<button class="btn btn-primary" onclick="saveWeatherRules()">Save Weather Rules</button>';
        html += '</div>';

        container.innerHTML = html;
        setupUnitConversions('');
    } catch (e) {
        container.innerHTML = '<div style="color:#e74c3c;">Failed to load weather rules: ' + esc(e.message) + '</div>';
    }
}

function buildRuleRow(ruleId, name, description, enabled, fields) {
    let html = '<div style="background:#f8f9fa;border:1px solid #eee;border-radius:8px;padding:10px;">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
    html += '<div><div style="font-weight:600;font-size:13px;">' + esc(name) + '</div>';
    html += '<div style="font-size:11px;color:#999;">' + esc(description) + '</div></div>';
    html += '<label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;">';
    html += '<input type="checkbox" id="rule_' + ruleId + '" ' + (enabled ? 'checked' : '') + '> Enabled</label>';
    html += '</div>';
    if (fields && fields.length > 0) {
        html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;">';
        for (const f of fields) {
            html += '<div style="display:flex;align-items:center;gap:4px;">';
            html += '<span style="font-size:11px;color:#999;">' + esc(f.label) + '</span>';
            html += '<input type="' + f.type + '" id="' + f.id + '" value="' + f.value + '" ';
            if (f.min != null) html += 'min="' + f.min + '" ';
            if (f.max != null) html += 'max="' + f.max + '" ';
            if (f.step != null) html += 'step="' + f.step + '" ';
            html += 'style="width:60px;padding:2px 4px;border:1px solid #ddd;border-radius:4px;font-size:12px;">';
            html += '</div>';
        }
        html += '</div>';
    }
    html += '</div>';
    return html;
}

async function saveWeatherRules() {
    try {
        const rules = {
            rain_detection: {
                enabled: document.getElementById('rule_rain_detection').checked,
                resume_delay_hours: parseFloat(document.getElementById('rain_detection_resume_delay_hours').value) || 2,
            },
            rain_forecast: {
                enabled: document.getElementById('rule_rain_forecast').checked,
                probability_threshold: parseInt(document.getElementById('rain_forecast_probability_threshold').value) || 60,
                lookahead_hours: 24,
            },
            precipitation_threshold: {
                enabled: document.getElementById('rule_precipitation_threshold').checked,
                skip_if_rain_above_mm: parseFloat(document.getElementById('precipitation_threshold_mm').value) || 6,
            },
            temperature_freeze: {
                enabled: document.getElementById('rule_temperature_freeze').checked,
                freeze_threshold_f: parseInt(document.getElementById('temperature_freeze_f').value) || 35,
                freeze_threshold_c: parseInt(document.getElementById('temperature_freeze_c').value) || 2,
            },
            temperature_cool: {
                enabled: document.getElementById('rule_temperature_cool').checked,
                cool_threshold_f: parseInt(document.getElementById('temperature_cool_f').value) || 60,
                cool_threshold_c: parseInt(document.getElementById('temperature_cool_c').value) || 15,
                reduction_percent: parseInt(document.getElementById('temperature_cool_reduction').value) || 25,
            },
            temperature_hot: {
                enabled: document.getElementById('rule_temperature_hot').checked,
                hot_threshold_f: parseInt(document.getElementById('temperature_hot_f').value) || 95,
                hot_threshold_c: parseInt(document.getElementById('temperature_hot_c').value) || 35,
                increase_percent: parseInt(document.getElementById('temperature_hot_increase').value) || 25,
            },
            wind_speed: {
                enabled: document.getElementById('rule_wind_speed').checked,
                max_wind_speed_mph: parseInt(document.getElementById('wind_speed_mph').value) || 20,
                max_wind_speed_kmh: parseInt(document.getElementById('wind_speed_kmh').value) || 32,
            },
            humidity: {
                enabled: document.getElementById('rule_humidity').checked,
                high_humidity_threshold: parseInt(document.getElementById('humidity_threshold').value) || 80,
                reduction_percent: parseInt(document.getElementById('humidity_reduction').value) || 20,
            },
            seasonal_adjustment: {
                enabled: document.getElementById('rule_seasonal_adjustment').checked,
                monthly_multipliers: {},
            },
        };
        for (let i = 1; i <= 12; i++) {
            rules.seasonal_adjustment.monthly_multipliers[String(i)] = parseFloat(document.getElementById('seasonal_month_' + i).value) || 0;
        }
        await wapi('/weather/rules', {
            method: 'PUT',
            body: JSON.stringify({ rules }),
        });
        showToast('Weather rules saved');
    } catch (e) {
        showToast('Failed to save weather rules: ' + e.message, 'error');
    }
}

async function evaluateWeatherNow() {
    try {
        showToast('Evaluating weather rules...');
        const result = await wapi('/weather/evaluate', { method: 'POST' });
        if (result.skipped) {
            showToast(result.reason || 'Evaluation skipped', 'error');
            return;
        }
        const triggered = result.triggered_rules || [];
        if (triggered.length === 0) {
            showToast('No rules triggered — conditions are normal');
        } else {
            const names = triggered.map(t => t.rule.replace(/_/g, ' ')).join(', ');
            showToast('Triggered: ' + names + ' | Multiplier: ' + result.watering_multiplier + 'x');
        }
        // Refresh the weather card to show updated state
        setTimeout(() => loadWeather(), 1000);
    } catch (e) {
        showToast('Evaluation failed: ' + e.message, 'error');
    }
}

// --- CSV Export ---
function exportHistoryCSV() {
    const hours = document.getElementById('historyRange') ? document.getElementById('historyRange').value : '24';
    const url = HBASE + '/history/runs/csv?hours=' + hours;
    window.open(url, '_blank');
}

function exportWeatherLogCSV() {
    const url = HBASE + '/weather/log/csv';
    window.open(url, '_blank');
}

// --- Clear Logs ---
async function clearRunHistory() {
    if (!confirm('Clear all run history? This cannot be undone.')) return;
    try {
        const result = await api('/history/runs', { method: 'DELETE' });
        if (result.success) {
            showToast(result.message || 'Run history cleared');
            setTimeout(() => loadHistory(), 1000);
        } else {
            showToast(result.error || 'Failed to clear history', 'error');
        }
    } catch (e) { showToast(e.message, 'error'); }
}

async function clearWeatherLog() {
    if (!confirm('Clear all weather log entries? This cannot be undone.')) return;
    try {
        const result = await api('/weather/log', { method: 'DELETE' });
        if (result.success) {
            showToast(result.message || 'Weather log cleared');
            setTimeout(() => loadWeather(), 1000);
        } else {
            showToast(result.error || 'Failed to clear weather log', 'error');
        }
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Init ---
document.addEventListener('DOMContentLoaded', async () => {
    // Load zone aliases
    try {
        window._currentZoneAliases = await api('/zone_aliases');
    } catch (e) {
        window._currentZoneAliases = {};
    }
    window._zoneModes = {};

    // Load dashboard
    loadDashboard();

    // Init map from status (address comes from config)
    try {
        const status = await api('/status');
        if (status.address || status.city || status.state || status.zip) {
            initDetailMap(status);
        }
    } catch (e) {
        console.warn('Could not load address for map:', e);
    }

    // Auto-refresh every 30 seconds
    refreshTimer = setInterval(loadDashboard, 30000);
});
</script>
</body>
</html>
"""
