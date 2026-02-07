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
:root {
    --bg-body: #f5f6fa;
    --bg-card: #ffffff;
    --bg-tile: #f8f9fa;
    --bg-input: #ffffff;
    --bg-weather: #f0f8ff;
    --bg-secondary-btn: #ecf0f1;
    --bg-secondary-btn-hover: #dfe6e9;
    --bg-active-tile: #e8f5e9;
    --bg-inactive-tile: #fbe9e7;
    --bg-toast: #2c3e50;
    --bg-modal-overlay: rgba(0,0,0,0.5);
    --bg-warning: #fff3cd;
    --bg-success-light: #d4edda;
    --bg-danger-light: #f8d7da;
    --text-primary: #2c3e50;
    --text-secondary: #666;
    --text-muted: #7f8c8d;
    --text-hint: #888;
    --text-disabled: #95a5a6;
    --text-placeholder: #999;
    --text-warning: #856404;
    --text-success-dark: #155724;
    --text-danger-dark: #721c24;
    --border-light: #eee;
    --border-input: #ddd;
    --border-card: #bdc3c7;
    --border-active: #a5d6a7;
    --border-hover: #bbb;
    --border-row: #f0f0f0;
    --color-primary: #1a7a4c;
    --color-primary-hover: #15603c;
    --color-accent: #2ecc71;
    --color-success: #27ae60;
    --color-danger: #e74c3c;
    --color-danger-hover: #c0392b;
    --color-warning: #f39c12;
    --color-link: #3498db;
    --header-gradient: linear-gradient(135deg, #1a7a4c, #2ecc71);
    --shadow-card: 0 1px 4px rgba(0,0,0,0.08);
    --shadow-header: 0 2px 8px rgba(0,0,0,0.15);
    --shadow-toast: 0 4px 12px rgba(0,0,0,0.2);
}
body.dark-mode {
    --bg-body: #1a1a2e;
    --bg-card: #16213e;
    --bg-tile: #1a1a2e;
    --bg-input: #1a1a2e;
    --bg-weather: #16213e;
    --bg-secondary-btn: #253555;
    --bg-secondary-btn-hover: #2d4068;
    --bg-active-tile: #1b3a2a;
    --bg-inactive-tile: #3a2020;
    --bg-toast: #0f3460;
    --bg-modal-overlay: rgba(0,0,0,0.7);
    --bg-warning: #3a3020;
    --bg-success-light: #1b3a2a;
    --bg-danger-light: #3a2020;
    --text-primary: #e0e0e0;
    --text-secondary: #b0b0b0;
    --text-muted: #8a9bb0;
    --text-hint: #7a8a9a;
    --text-disabled: #607080;
    --text-placeholder: #607080;
    --text-warning: #d4a843;
    --text-success-dark: #6fcf97;
    --text-danger-dark: #e07a7a;
    --border-light: #253555;
    --border-input: #304060;
    --border-card: #304060;
    --border-active: #2d7a4a;
    --border-hover: #405575;
    --border-row: #253555;
    --color-primary: #2ecc71;
    --color-primary-hover: #27ae60;
    --color-accent: #2ecc71;
    --color-success: #2ecc71;
    --color-danger: #e74c3c;
    --color-danger-hover: #c0392b;
    --color-warning: #f39c12;
    --color-link: #5dade2;
    --header-gradient: linear-gradient(135deg, #0f3460, #16213e);
    --shadow-card: 0 1px 4px rgba(0,0,0,0.3);
    --shadow-header: 0 2px 8px rgba(0,0,0,0.4);
    --shadow-toast: 0 4px 12px rgba(0,0,0,0.4);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-body); color: var(--text-primary); }
.header { background: var(--header-gradient); color: white; padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; box-shadow: var(--shadow-header); }
.header-left { display: flex; align-items: center; gap: 14px; }
.header-logo { height: 44px; filter: brightness(0) invert(1); }
.header h1 { font-size: 20px; font-weight: 600; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.nav-tabs { display: flex; gap: 4px; }
.nav-tab { padding: 6px 14px; border-radius: 8px; font-size: 13px; font-weight: 500; text-decoration: none; color: white; transition: background 0.15s ease; }
.nav-tab:hover { background: rgba(255,255,255,0.15); }
.nav-tab.active { background: rgba(255,255,255,0.25); }
.dark-toggle { background: rgba(255,255,255,0.15); border: none; border-radius: 8px; cursor: pointer; font-size: 16px; padding: 4px 8px; transition: background 0.15s; line-height: 1; }
.dark-toggle:hover { background: rgba(255,255,255,0.25); }
.container { max-width: 1200px; margin: 0 auto; padding: 24px; }
.card { background: var(--bg-card); border-radius: 12px; box-shadow: var(--shadow-card); margin-bottom: 20px; overflow: hidden; }
.card-header { padding: 16px 20px; border-bottom: 1px solid var(--border-light); display: flex; justify-content: space-between; align-items: center; }
.card-header h2 { font-size: 16px; font-weight: 600; }
.card-body { padding: 20px; }
.btn { display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 8px; border: none; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s ease; }
.btn-primary { background: var(--color-primary); color: white; }
.btn-primary:hover { background: var(--color-primary-hover); }
.btn-danger { background: var(--color-danger); color: white; }
.btn-danger:hover { background: var(--color-danger-hover); }
.btn-secondary { background: var(--bg-secondary-btn); color: var(--text-primary); }
.btn-secondary:hover { background: var(--bg-secondary-btn-hover); }
.btn-sm { padding: 5px 10px; font-size: 12px; }
.btn-icon { padding: 6px 10px; }

/* Zone/Sensor Tiles */
.tile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.tile { background: var(--bg-tile); border-radius: 8px; padding: 14px; border: 1px solid var(--border-light); }
.tile.active { background: var(--bg-active-tile); border-color: var(--border-active); }
.tile-name { font-weight: 600; font-size: 14px; margin-bottom: 6px; }
.tile-state { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
.tile-state.on { color: var(--color-success); font-weight: 500; }
.tile-actions { display: flex; gap: 6px; }

/* Schedule (entity-based) */
.schedule-section { margin-bottom: 20px; }
.schedule-section-label { font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px; }
.days-row { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
.day-toggle { padding: 8px 14px; border-radius: 8px; border: 2px solid var(--border-input); cursor: pointer; font-size: 13px; font-weight: 600; text-align: center; min-width: 52px; transition: all 0.15s ease; background: var(--bg-tile); color: var(--text-muted); user-select: none; }
.day-toggle:hover { border-color: var(--border-hover); }
.day-toggle.active { background: var(--bg-active-tile); border-color: var(--color-success); color: var(--color-success); }
.start-times-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }
.zone-settings-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.zone-settings-table th { text-align: left; padding: 8px; border-bottom: 2px solid var(--border-light); font-size: 12px; color: var(--text-muted); text-transform: uppercase; }
.zone-settings-table td { padding: 8px; border-bottom: 1px solid var(--border-row); }
.system-controls-row { display: flex; gap: 12px; flex-wrap: wrap; }

/* Empty States */
.empty-state { text-align: center; padding: 40px 20px; color: var(--text-disabled); }
.empty-state h3 { font-size: 18px; margin-bottom: 8px; color: var(--text-muted); }
.empty-state p { font-size: 14px; }

/* Loading */
.loading { text-align: center; padding: 20px; color: var(--text-muted); font-size: 14px; }

/* Toast */
.toast-container { position: fixed; top: 20px; right: 20px; z-index: 1000; }
.toast { background: var(--bg-toast); color: white; padding: 12px 20px; border-radius: 8px; margin-bottom: 8px; font-size: 14px; animation: slideIn 0.3s ease; box-shadow: var(--shadow-toast); }
.toast.error { background: var(--color-danger); }
.toast.success { background: var(--color-success); }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

/* Dark mode form inputs */
body.dark-mode input, body.dark-mode select, body.dark-mode textarea {
    background: var(--bg-input); color: var(--text-primary); border-color: var(--border-input);
}

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
    .dark-toggle { font-size: 14px; padding: 3px 6px; }
}
</style>
</head>
<body>
<script>(function(){if(localStorage.getItem('flux_dark_mode_homeowner')==='true')document.body.classList.add('dark-mode');})()</script>

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
        <button class="dark-toggle" onclick="toggleDarkMode()" title="Toggle dark mode">🌙</button>
        <button class="dark-toggle" onclick="showHelp()" title="Help">❓</button>
        <button class="btn btn-secondary btn-sm" onclick="switchToManagement()">Management</button>
    </div>
</div>

<div class="container">
    <div class="detail-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <div>
            <h2 id="dashTitle" style="font-size:22px;font-weight:600;">My Irrigation System</h2>
            <div id="dashAddress" style="font-size:14px;color:var(--text-disabled);margin-top:4px;display:none;"></div>
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
                <span id="weatherMultBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-success-light);color:var(--text-success-dark);">1.0x</span>
            </div>
        </div>
        <div class="card-body" id="weatherCardBody">
            <div class="loading">Loading weather...</div>
        </div>
    </div>

    <!-- Moisture Probes Card -->
    <div class="card" id="moistureCard" style="display:none;">
        <div class="card-header">
            <h2>Moisture Probes</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <span id="moistureStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-success-light);color:var(--text-success-dark);">—</span>
            </div>
        </div>
        <div class="card-body" id="moistureCardBody">
            <div class="loading">Loading moisture data...</div>
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
                <select id="historyRange" onchange="loadHistory()" style="padding:4px 8px;border:1px solid var(--border-input);border-radius:6px;font-size:12px;">
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

<!-- Help Modal -->
<div id="helpModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:999;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:640px;max-height:80vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">Homeowner Dashboard Help</h3>
            <button onclick="closeHelpModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div id="helpContent" style="padding:16px 24px 24px 24px;overflow-y:auto;font-size:14px;color:var(--text-secondary);line-height:1.6;"></div>
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
    loadMoisture();
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
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load status: ' + esc(e.message) + '</div>';
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
                    <span style="cursor:pointer;font-size:11px;color:var(--color-primary);margin-left:6px;"
                          onclick="event.stopPropagation();renameZone(\\'${z.entity_id}\\')">&#9998;</span>
                </div>
                <div class="tile-state ${isOn ? 'on' : ''}">${isOn ? 'Running' : 'Off'}</div>
                <div class="tile-actions" style="flex-wrap:wrap;">
                    ${isOn
                        ? '<button class="btn btn-danger btn-sm" onclick="stopZone(\\'' + zId + '\\')">Stop</button>'
                        : '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + zId + '\\', null)">Start</button>' +
                          '<span style="display:flex;align-items:center;gap:4px;margin-top:4px;"><input type="number" id="dur_' + zId + '" min="1" max="480" placeholder="min" style="width:60px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;">' +
                          '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + zId + '\\', document.getElementById(\\'dur_' + zId + '\\').value)">Timed</button></span>'
                    }
                </div>
            </div>`;
        }).join('') + '</div>';
    } catch (e) {
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load zones: ' + esc(e.message) + '</div>';
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
    if (val >= -50)      { label = 'Great'; color = 'var(--color-success)'; }
    else if (val >= -60) { label = 'Good';  color = 'var(--color-success)'; }
    else if (val >= -70) { label = 'Poor';  color = 'var(--color-warning)'; }
    else                 { label = 'Bad';   color = 'var(--color-danger)'; }
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
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load sensors: ' + esc(e.message) + '</div>';
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
                html += '<div style="margin-bottom:16px;"><div style="font-size:13px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">' + esc(label) + '</div>';
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
        controlsEl.innerHTML = '<div style="color:var(--color-danger);">Failed to load controls: ' + esc(e.message) + '</div>';
        scheduleEl.innerHTML = '<div style="color:var(--color-danger);">Failed to load schedule: ' + esc(e.message) + '</div>';
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
            'padding:12px 16px;border-radius:8px;background:' + (isOn ? 'var(--bg-active-tile)' : 'var(--bg-inactive-tile)') + ';">' +
            '<div><div style="font-size:15px;font-weight:600;color:' + (isOn ? 'var(--color-success)' : 'var(--color-danger)') + ';">' +
            'Schedule ' + (isOn ? 'Enabled' : 'Disabled') + '</div>' +
            '<div style="font-size:12px;color:var(--text-muted);">Master schedule on/off</div></div>' +
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
                '<input type="text" id="' + inputId + '" value="' + esc(st.state) + '" placeholder="HH:MM" style="width:100px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;">' +
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
                    html += '<td><select id="' + selId + '" style="padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;" ' +
                        'onchange="setEntityValue(\\'' + modeEid +
                        '\\',\\'select\\',{option:document.getElementById(\\'' + selId + '\\').value})">' +
                        optionsHtml + '</select></td>';
                } else {
                    html += '<td style="color:var(--text-disabled);">-</td>';
                }
            }
            if (enable) {
                const isOn = enable.state === 'on';
                html += '<td><button class="btn ' + (isOn ? 'btn-primary' : 'btn-secondary') + ' btn-sm" ' +
                    'onclick="setEntityValue(\\'' + enable.entity_id + '\\',\\'switch\\',' +
                    '{state:\\'' + (isOn ? 'off' : 'on') + '\\'})">' +
                    (isOn ? 'Enabled' : 'Disabled') + '</button></td>';
            } else {
                html += '<td style="color:var(--text-disabled);">-</td>';
            }
            if (isPumpOrMaster) {
                html += '<td style="color:var(--text-disabled);font-style:italic;">Firmware controlled</td>';
            } else if (duration) {
                const attrs = duration.attributes || {};
                const unit = attrs.unit_of_measurement || 'min';
                const eid = duration.entity_id;
                const inputId = 'dur_sched_' + eid.replace(/[^a-zA-Z0-9]/g, '_');
                html += '<td><input type="number" id="' + inputId + '" value="' + esc(duration.state) + '" ' +
                    'min="' + (attrs.min || 0) + '" max="' + (attrs.max || 999) + '" step="' + (attrs.step || 1) + '" ' +
                    'style="width:70px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;"> ' +
                    esc(unit) + ' ' +
                    '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid +
                    '\\',\\'number\\',{value:parseFloat(document.getElementById(\\'' + inputId + '\\').value)})">Set</button></td>';
            } else {
                html += '<td style="color:var(--text-disabled);">-</td>';
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
                '<input type="number" id="num_' + eid + '" value="' + esc(state) + '" min="' + min + '" max="' + max + '" step="' + step + '" style="width:80px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;">' +
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
                '<select id="sel_' + eid + '" style="padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;">' + optionsHtml + '</select>' +
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
                '<input type="text" id="txt_' + eid + '" value="' + esc(state) + '" style="width:120px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid + '\\',\\'text\\',{value:document.getElementById(\\'txt_' + eid + '\\').value})">Set</button>' +
            '</div></div>';
    }

    return '<div class="tile">' +
        '<div class="tile-name">' + name + '</div>' +
        '<div class="tile-state">' + esc(state) + '</div>' +
        '<div style="font-size:11px;color:var(--text-disabled);margin-top:4px;">' + esc(domain) + '</div>' +
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
        const hoursRaw = document.getElementById('historyRange') ? document.getElementById('historyRange').value : '24';
        const hours = parseInt(hoursRaw, 10) || 24;
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
            const multColor = mult === 1.0 ? 'var(--text-success-dark)' : mult < 1 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
            const multBg = mult === 1.0 ? 'var(--bg-success-light)' : mult < 1 ? 'var(--bg-warning)' : 'var(--bg-danger-light)';
            weatherSummary = '<div style="margin-bottom:12px;padding:8px 12px;background:var(--bg-weather);border-radius:8px;font-size:12px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">' +
                '<span>' + wIcon + ' <strong>' + esc(cw.condition) + '</strong></span>' +
                (cw.temperature != null ? '<span>🌡️ ' + cw.temperature + '°</span>' : '') +
                (cw.humidity != null ? '<span>💧 ' + cw.humidity + '%</span>' : '') +
                (cw.wind_speed != null ? '<span>💨 ' + cw.wind_speed + ' mph</span>' : '') +
                '<span style="background:' + multBg + ';color:' + multColor + ';padding:2px 8px;border-radius:10px;font-weight:600;">' + mult + 'x</span>' +
                '</div>';
        }

        el.innerHTML = weatherSummary +
            '<table style="width:100%;font-size:13px;border-collapse:collapse;"><thead><tr style="text-align:left;border-bottom:2px solid var(--border-light);"><th style="padding:6px;">Zone</th><th style="padding:6px;">State</th><th style="padding:6px;">Time</th><th style="padding:6px;">Duration</th><th style="padding:6px;">Weather</th></tr></thead><tbody>' +
            events.slice(0, 100).map(e => {
                const wx = e.weather || {};
                let wxCell = '-';
                if (wx.condition) {
                    const ci = {'sunny':'☀️','clear-night':'🌙','partlycloudy':'⛅','cloudy':'☁️','rainy':'🌧️','pouring':'🌧️','snowy':'❄️','windy':'💨','fog':'🌫️','lightning':'⚡','lightning-rainy':'⛈️','hail':'🧊'};
                    const wi = ci[wx.condition] || '🌡️';
                    const wm = wx.watering_multiplier != null ? wx.watering_multiplier : '';
                    const wmColor = wm === 1.0 ? 'var(--color-success)' : wm < 1 ? 'var(--color-warning)' : wm > 1 ? 'var(--color-danger)' : 'var(--text-placeholder)';
                    wxCell = wi + ' ' + (wx.temperature != null ? wx.temperature + '° ' : '') +
                        (wm ? '<span style="color:' + wmColor + ';font-weight:600;">' + wm + 'x</span>' : '');
                    const rules = wx.active_adjustments || wx.rules_triggered || [];
                    if (rules.length > 0) {
                        wxCell += '<div style="font-size:10px;color:var(--text-warning);margin-top:2px;">' + rules.map(r => r.replace(/_/g, ' ')).join(', ') + '</div>';
                    }
                }
                const srcLabel = e.source ? '<div style="font-size:10px;color:var(--text-placeholder);">' + esc(e.source) + '</div>' : '';
                return `<tr style="border-bottom:1px solid var(--border-row);">
                <td style="padding:6px;">${esc(resolveZoneName(e.entity_id, e.zone_name))}${srcLabel}</td>
                <td style="padding:6px;">${e.state === 'on' || e.state === 'open' ? '<span style="color:var(--color-success);">ON</span>' : '<span style="color:var(--text-disabled);">OFF</span>'}</td>
                <td style="padding:6px;">${formatTime(e.timestamp)}</td>
                <td style="padding:6px;">${e.duration_seconds ? Math.round(e.duration_seconds / 60) + ' min' : '-'}</td>
                <td style="padding:6px;font-size:12px;">${wxCell}</td>
            </tr>`;
            }).join('') + '</tbody></table>';
    } catch (e) {
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load history: ' + esc(e.message) + '</div>';
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
            body.innerHTML = '<div style="color:var(--text-placeholder);text-align:center;padding:12px;">' + esc(w.error) + '</div>';
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
        badge.style.background = mult === 1.0 ? 'var(--bg-success-light)' : mult < 1 ? 'var(--bg-warning)' : 'var(--bg-danger-light)';
        badge.style.color = mult === 1.0 ? 'var(--text-success-dark)' : mult < 1 ? 'var(--text-warning)' : 'var(--text-danger-dark)';

        let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;">';
        html += '<div style="background:var(--bg-weather);border-radius:8px;padding:10px;text-align:center;">';
        html += '<div style="font-size:24px;">' + icon + '</div>';
        html += '<div style="font-weight:600;text-transform:capitalize;font-size:13px;">' + esc(w.condition || 'unknown') + '</div>';
        html += '</div>';
        html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
        html += '<div style="color:var(--text-placeholder);font-size:11px;">Temperature</div>';
        html += '<div style="font-weight:600;font-size:16px;">' + (w.temperature != null ? w.temperature + (w.temperature_unit || '°F') : 'N/A') + '</div>';
        html += '</div>';
        html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
        html += '<div style="color:var(--text-placeholder);font-size:11px;">Humidity</div>';
        html += '<div style="font-weight:600;font-size:16px;">' + (w.humidity != null ? w.humidity + '%' : 'N/A') + '</div>';
        html += '</div>';
        html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
        html += '<div style="color:var(--text-placeholder);font-size:11px;">Wind</div>';
        html += '<div style="font-weight:600;font-size:16px;">' + (w.wind_speed != null ? w.wind_speed + ' ' + (w.wind_speed_unit || 'mph') : 'N/A') + '</div>';
        html += '</div>';
        html += '</div>';

        // 3-day forecast
        const forecast = w.forecast || [];
        if (forecast.length > 0) {
            html += '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;margin-bottom:8px;">Forecast</div>';
            html += '<div style="display:flex;gap:8px;overflow-x:auto;">';
            for (let i = 0; i < Math.min(forecast.length, 5); i++) {
                const f = forecast[i];
                const dt = f.datetime ? new Date(f.datetime) : null;
                const dayLabel = dt ? dt.toLocaleDateString('en-US', { weekday: 'short' }) : '';
                const fIcon = condIcons[f.condition] || '🌡️';
                const precip = f.precipitation_probability || 0;
                html += '<div style="flex:0 0 auto;background:var(--bg-tile);border-radius:8px;padding:8px 12px;text-align:center;min-width:70px;">';
                html += '<div style="font-size:11px;color:var(--text-placeholder);">' + esc(dayLabel) + '</div>';
                html += '<div style="font-size:18px;">' + fIcon + '</div>';
                html += '<div style="font-size:12px;font-weight:600;">' + (f.temperature != null ? f.temperature + '°' : '') + '</div>';
                if (precip > 0) {
                    html += '<div style="font-size:10px;color:var(--color-link);">💧 ' + precip + '%</div>';
                }
                html += '</div>';
            }
            html += '</div></div>';
        }

        // Active adjustments
        const adjustments = data.active_adjustments || [];
        if (adjustments.length > 0) {
            html += '<div style="margin-top:12px;padding:10px;background:var(--bg-warning);border-radius:8px;font-size:12px;">';
            html += '<strong style="color:var(--text-warning);">Active Weather Adjustments:</strong>';
            html += '<ul style="margin:4px 0 0 16px;color:var(--text-warning);">';
            for (const adj of adjustments) {
                html += '<li>' + esc(adj.reason || adj.rule) + '</li>';
            }
            html += '</ul></div>';
        }

        // --- Weather Rules Editor ---
        html += '<div style="margin-top:16px;border-top:1px solid var(--border-light);padding-top:16px;">';
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
                '<span style="font-size:11px;color:var(--text-placeholder);width:28px;">' + monthNames[i-1] + '</span>' +
                '<input type="number" id="seasonal_month_' + i + '" value="' + val + '" min="0" max="2" step="0.1" ' +
                'style="width:55px;padding:2px 4px;border:1px solid var(--border-input);border-radius:4px;font-size:11px;"></div>';
        }
        html += '<div style="background:var(--bg-tile);border:1px solid var(--border-light);border-radius:8px;padding:10px;margin-bottom:4px;">';
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">';
        html += '<div><div style="font-weight:600;font-size:13px;">Seasonal Adjustment</div>';
        html += '<div style="font-size:11px;color:var(--text-placeholder);">Monthly watering multiplier (0=off, 1=normal)</div></div>';
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
        container.innerHTML = '<div style="color:var(--color-danger);">Failed to load weather rules: ' + esc(e.message) + '</div>';
    }
}

function buildRuleRow(ruleId, name, description, enabled, fields) {
    let html = '<div style="background:var(--bg-tile);border:1px solid var(--border-light);border-radius:8px;padding:10px;">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
    html += '<div><div style="font-weight:600;font-size:13px;">' + esc(name) + '</div>';
    html += '<div style="font-size:11px;color:var(--text-placeholder);">' + esc(description) + '</div></div>';
    html += '<label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;">';
    html += '<input type="checkbox" id="rule_' + ruleId + '" ' + (enabled ? 'checked' : '') + '> Enabled</label>';
    html += '</div>';
    if (fields && fields.length > 0) {
        html += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:6px;">';
        for (const f of fields) {
            html += '<div style="display:flex;align-items:center;gap:4px;">';
            html += '<span style="font-size:11px;color:var(--text-placeholder);">' + esc(f.label) + '</span>';
            html += '<input type="' + f.type + '" id="' + f.id + '" value="' + f.value + '" ';
            if (f.min != null) html += 'min="' + f.min + '" ';
            if (f.max != null) html += 'max="' + f.max + '" ';
            if (f.step != null) html += 'step="' + f.step + '" ';
            html += 'style="width:60px;padding:2px 4px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;">';
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
    const hoursRaw = document.getElementById('historyRange') ? document.getElementById('historyRange').value : '24';
    const hours = parseInt(hoursRaw, 10) || 24;
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

// --- Moisture Probes ---
let _moistureExpanded = { settings: false, management: false, durations: false };

async function loadMoisture() {
    const card = document.getElementById('moistureCard');
    const body = document.getElementById('moistureCardBody');
    const badge = document.getElementById('moistureStatusBadge');
    try {
        const data = await mapi('/probes');
        const settings = await mapi('/settings');

        if (!settings.enabled && Object.keys(data.probes || {}).length === 0) {
            card.style.display = 'none';
            return;
        }
        card.style.display = 'block';

        const probes = data.probes || {};
        const probeCount = Object.keys(probes).length;
        badge.textContent = settings.enabled ? probeCount + ' probe(s)' : 'Disabled';
        badge.style.background = settings.enabled ? 'var(--bg-success-light)' : 'var(--bg-tile)';
        badge.style.color = settings.enabled ? 'var(--text-success-dark)' : 'var(--text-muted)';

        let html = '';

        // Probe tiles
        if (probeCount > 0) {
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;">';
            for (const [pid, probe] of Object.entries(probes)) {
                const sensors = probe.sensors_live || {};
                html += '<div style="background:var(--bg-tile);border-radius:10px;padding:12px;border:1px solid var(--border-light);">';
                html += '<div style="font-weight:600;font-size:14px;margin-bottom:8px;">' + esc(probe.display_name || pid) + '</div>';

                // Depth readings as horizontal bars
                for (const depth of ['shallow', 'mid', 'deep']) {
                    const s = sensors[depth];
                    if (!s) continue;
                    const val = s.value != null ? s.value : null;
                    const stale = s.stale;
                    const pct = val != null ? Math.min(val, 100) : 0;
                    const color = val == null ? '#bbb' : stale ? '#999' : val > 70 ? '#3498db' : val > 40 ? '#2ecc71' : '#e67e22';
                    html += '<div style="margin-bottom:6px;">';
                    html += '<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-bottom:2px;">';
                    html += '<span>' + depth.charAt(0).toUpperCase() + depth.slice(1) + '</span>';
                    html += '<span>' + (val != null ? val.toFixed(0) + '%' : '—') + (stale ? ' ⏳' : '') + '</span>';
                    html += '</div>';
                    html += '<div style="height:6px;background:var(--border-light);border-radius:3px;overflow:hidden;">';
                    html += '<div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:3px;transition:width 0.3s;"></div>';
                    html += '</div></div>';
                }

                // Mapped zones
                const zones = probe.zone_mappings || [];
                if (zones.length > 0) {
                    html += '<div style="margin-top:6px;font-size:11px;color:var(--text-muted);">Zones: ';
                    html += zones.map(z => '<span style="background:var(--bg-secondary-btn);padding:1px 6px;border-radius:4px;font-size:10px;">' + esc(z.split('.').pop()) + '</span>').join(' ');
                    html += '</div>';
                }
                html += '</div>';
            }
            html += '</div>';
        } else {
            html += '<div style="text-align:center;padding:16px;color:var(--text-muted);">No moisture probes configured. Click <strong>Manage Probes</strong> below to discover and add probes.</div>';
        }

        // Zone multiplier summary
        if (probeCount > 0 && settings.enabled) {
            try {
                const config = await api('/zones');
                if (config && config.length > 0) {
                    html += '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;margin-bottom:8px;">Zone Multipliers</div>';
                    html += '<div style="display:flex;flex-wrap:wrap;gap:6px;">';
                    for (const zone of config) {
                        try {
                            const mult = await mapi('/zones/' + encodeURIComponent(zone.entity_id) + '/multiplier', 'POST');
                            const m = mult.combined_multiplier != null ? mult.combined_multiplier : 1.0;
                            const mColor = m === 0 ? 'var(--color-danger)' : m < 1 ? 'var(--text-warning)' : m > 1 ? 'var(--text-danger-dark)' : 'var(--text-success-dark)';
                            const mBg = m === 0 ? 'var(--bg-danger-light)' : m < 1 ? 'var(--bg-warning)' : m > 1 ? 'var(--bg-danger-light)' : 'var(--bg-success-light)';
                            const label = mult.moisture_skip ? 'SKIP' : m.toFixed(2) + 'x';
                            const alias = (window._currentZoneAliases || {})[zone.entity_id] || zone.friendly_name || zone.name;
                            html += '<div style="background:' + mBg + ';color:' + mColor + ';padding:4px 10px;border-radius:12px;font-size:12px;font-weight:600;">';
                            html += esc(alias) + ': ' + label + '</div>';
                        } catch (e) { /* skip zone */ }
                    }
                    html += '</div></div>';
                }
            } catch (e) { /* no zones */ }
        }

        // Duration status
        try {
            const dur = await mapi('/durations');
            const base = dur.base_durations || {};
            const adjusted = dur.adjusted_durations || {};
            if (Object.keys(base).length > 0) {
                html += '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;margin-bottom:8px;">Duration Status' + (dur.duration_adjustment_active ? ' <span style="color:var(--color-warning);">(Active)</span>' : '') + '</div>';
                html += '<div style="overflow-x:auto;"><table style="width:100%;font-size:12px;border-collapse:collapse;">';
                html += '<tr style="border-bottom:1px solid var(--border-light);"><th style="text-align:left;padding:4px 8px;color:var(--text-muted);">Entity</th><th style="text-align:right;padding:4px 8px;color:var(--text-muted);">Base</th><th style="text-align:right;padding:4px 8px;color:var(--text-muted);">Adjusted</th><th style="text-align:right;padding:4px 8px;color:var(--text-muted);">Multiplier</th></tr>';
                for (const [eid, b] of Object.entries(base)) {
                    const adj = adjusted[eid];
                    const adjVal = adj ? adj.adjusted : b.base_value;
                    const mult = adj ? adj.combined_multiplier : 1.0;
                    const name = b.friendly_name || eid.split('.').pop();
                    html += '<tr style="border-bottom:1px solid var(--border-row);">';
                    html += '<td style="padding:4px 8px;">' + esc(name) + '</td>';
                    html += '<td style="text-align:right;padding:4px 8px;">' + b.base_value + ' min</td>';
                    html += '<td style="text-align:right;padding:4px 8px;font-weight:600;color:' + (adjVal !== b.base_value ? 'var(--color-warning)' : 'var(--text-primary)') + ';">' + adjVal + ' min</td>';
                    html += '<td style="text-align:right;padding:4px 8px;">' + (mult != null ? mult.toFixed(2) + 'x' : '—') + '</td>';
                    html += '</tr>';
                }
                html += '</table></div></div>';
            }
        } catch (e) { /* no durations */ }

        // Expandable sections
        // Settings
        html += '<div style="margin-top:16px;border-top:1px solid var(--border-light);padding-top:12px;">';
        html += '<div style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;" onclick="toggleMoistureSection(\'settings\')">';
        html += '<span style="font-size:13px;font-weight:600;">Settings</span>';
        html += '<span id="moistureSettingsChevron" style="font-size:12px;color:var(--text-muted);">' + (_moistureExpanded.settings ? '▼' : '▶') + '</span>';
        html += '</div>';
        html += '<div id="moistureSettingsBody" style="display:' + (_moistureExpanded.settings ? 'block' : 'none') + ';margin-top:10px;">';
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px;">';
        html += '<label style="display:flex;align-items:center;gap:8px;"><input type="checkbox" id="moistureEnabled" ' + (settings.enabled ? 'checked' : '') + ' onchange="saveMoistureSettings()"> Enable Moisture Control</label>';
        html += '<div><label style="font-size:11px;color:var(--text-muted);">Stale Threshold (min)</label><input type="number" id="moistureStaleMin" value="' + (settings.stale_reading_threshold_minutes || 120) + '" min="5" max="1440" style="width:80px;padding:4px;border:1px solid var(--border-input);border-radius:4px;background:var(--bg-input);color:var(--text-primary);"></div>';
        html += '</div>';
        const dw = settings.depth_weights || {shallow: 0.2, mid: 0.5, deep: 0.3};
        html += '<div style="margin-top:8px;font-size:12px;color:var(--text-muted);">Depth Weights</div>';
        html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:4px;">';
        for (const d of ['shallow', 'mid', 'deep']) {
            html += '<div><label style="font-size:11px;color:var(--text-muted);">' + d.charAt(0).toUpperCase() + d.slice(1) + '</label>';
            html += '<input type="number" id="moistureWeight_' + d + '" value="' + (dw[d] || 0.33) + '" min="0" max="1" step="0.05" style="width:60px;padding:4px;border:1px solid var(--border-input);border-radius:4px;background:var(--bg-input);color:var(--text-primary);"></div>';
        }
        html += '</div>';
        const dt = settings.default_thresholds || {};
        html += '<div style="margin-top:8px;font-size:12px;color:var(--text-muted);">Default Thresholds (%)</div>';
        html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px;margin-top:4px;">';
        for (const [key, label] of [['skip_threshold','Skip'], ['scale_wet','Wet'], ['scale_dry','Dry'], ['max_increase_percent','Max Increase'], ['max_decrease_percent','Max Decrease']]) {
            html += '<div><label style="font-size:11px;color:var(--text-muted);">' + label + '</label>';
            html += '<input type="number" id="moistureThresh_' + key + '" value="' + (dt[key] != null ? dt[key] : '') + '" min="0" max="100" style="width:70px;padding:4px;border:1px solid var(--border-input);border-radius:4px;background:var(--bg-input);color:var(--text-primary);"></div>';
        }
        html += '</div>';
        html += '<button class="btn btn-primary btn-sm" style="margin-top:8px;" onclick="saveMoistureSettings()">Save Settings</button>';
        html += '</div></div>';

        // Probe Management
        html += '<div style="margin-top:12px;border-top:1px solid var(--border-light);padding-top:12px;">';
        html += '<div style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;" onclick="toggleMoistureSection(\'management\')">';
        html += '<span style="font-size:13px;font-weight:600;">Manage Probes</span>';
        html += '<span id="moistureManagementChevron" style="font-size:12px;color:var(--text-muted);">' + (_moistureExpanded.management ? '▼' : '▶') + '</span>';
        html += '</div>';
        html += '<div id="moistureManagementBody" style="display:' + (_moistureExpanded.management ? 'block' : 'none') + ';margin-top:10px;">';
        html += '<button class="btn btn-secondary btn-sm" onclick="discoverMoistureProbes()">Discover Probes</button>';
        html += '<div id="moistureDiscoverResults" style="margin-top:8px;"></div>';
        html += '<div id="moistureProbeList" style="margin-top:8px;">';
        // Existing probes with edit/delete
        for (const [pid, probe] of Object.entries(probes)) {
            html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;margin-bottom:8px;border:1px solid var(--border-light);">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
            html += '<strong>' + esc(probe.display_name || pid) + '</strong>';
            html += '<button class="btn btn-danger btn-sm" onclick="deleteMoistureProbe(\'' + esc(pid) + '\')">Remove</button>';
            html += '</div>';
            html += '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">ID: ' + esc(pid) + '</div>';
            const ss = probe.sensors || {};
            html += '<div style="font-size:11px;margin-top:4px;">Sensors: ' + Object.entries(ss).map(([d,e]) => d + '=' + e).join(', ') + '</div>';
            html += '<div style="font-size:11px;">Zones: ' + (probe.zone_mappings || []).join(', ') + '</div>';
            html += '</div>';
        }
        html += '</div></div></div>';

        // Duration Controls
        html += '<div style="margin-top:12px;border-top:1px solid var(--border-light);padding-top:12px;">';
        html += '<div style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;" onclick="toggleMoistureSection(\'durations\')">';
        html += '<span style="font-size:13px;font-weight:600;">Duration Controls</span>';
        html += '<span id="moistureDurationsChevron" style="font-size:12px;color:var(--text-muted);">' + (_moistureExpanded.durations ? '▼' : '▶') + '</span>';
        html += '</div>';
        html += '<div id="moistureDurationsBody" style="display:' + (_moistureExpanded.durations ? 'block' : 'none') + ';margin-top:10px;">';
        html += '<div style="display:flex;gap:8px;flex-wrap:wrap;">';
        html += '<button class="btn btn-secondary btn-sm" onclick="captureMoistureDurations()">Capture Base Durations</button>';
        html += '<button class="btn btn-primary btn-sm" onclick="applyMoistureDurations()">Apply Adjusted</button>';
        html += '<button class="btn btn-secondary btn-sm" onclick="restoreMoistureDurations()">Restore Originals</button>';
        html += '</div>';
        html += '<div style="margin-top:6px;font-size:11px;color:var(--text-muted);">Capture saves current run durations as your baseline. Apply writes adjusted values (base × weather × moisture). Restore returns to baseline.</div>';
        html += '</div></div>';

        body.innerHTML = html;
    } catch (e) {
        card.style.display = 'none';
    }
}

// Moisture API helper (uses homeowner moisture prefix)
async function mapi(path, method = 'GET', bodyData = null) {
    const opts = { method, headers: {} };
    if (bodyData) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(bodyData);
    }
    const res = await fetch(BASE + '/moisture' + path, opts);
    return await res.json();
}

function toggleMoistureSection(section) {
    _moistureExpanded[section] = !_moistureExpanded[section];
    const body = document.getElementById('moisture' + section.charAt(0).toUpperCase() + section.slice(1) + 'Body');
    const chevron = document.getElementById('moisture' + section.charAt(0).toUpperCase() + section.slice(1) + 'Chevron');
    if (body) body.style.display = _moistureExpanded[section] ? 'block' : 'none';
    if (chevron) chevron.textContent = _moistureExpanded[section] ? '▼' : '▶';
}

async function saveMoistureSettings() {
    try {
        const payload = {
            enabled: document.getElementById('moistureEnabled').checked,
            stale_reading_threshold_minutes: parseInt(document.getElementById('moistureStaleMin').value) || 120,
            depth_weights: {
                shallow: parseFloat(document.getElementById('moistureWeight_shallow').value) || 0.2,
                mid: parseFloat(document.getElementById('moistureWeight_mid').value) || 0.5,
                deep: parseFloat(document.getElementById('moistureWeight_deep').value) || 0.3,
            },
            default_thresholds: {
                skip_threshold: parseInt(document.getElementById('moistureThresh_skip_threshold').value) || 80,
                scale_wet: parseInt(document.getElementById('moistureThresh_scale_wet').value) || 70,
                scale_dry: parseInt(document.getElementById('moistureThresh_scale_dry').value) || 30,
                max_increase_percent: parseInt(document.getElementById('moistureThresh_max_increase_percent').value) || 50,
                max_decrease_percent: parseInt(document.getElementById('moistureThresh_max_decrease_percent').value) || 50,
            },
        };
        const result = await mapi('/settings', 'PUT', payload);
        showToast(result.message || 'Settings saved');
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

async function discoverMoistureProbes() {
    const container = document.getElementById('moistureDiscoverResults');
    container.innerHTML = '<div class="loading">Scanning sensors...</div>';
    try {
        const data = await mapi('/probes/discover');
        const candidates = data.candidates || [];
        if (candidates.length === 0) {
            container.innerHTML = '<div style="font-size:12px;color:var(--text-muted);padding:8px;">No moisture probe sensors found. Ensure your Gophr probe is connected and reporting to Home Assistant.</div>';
            return;
        }
        let html = '<div style="font-size:12px;font-weight:600;margin-bottom:6px;">' + candidates.length + ' sensor(s) found:</div>';
        html += '<div style="max-height:200px;overflow-y:auto;">';
        for (const c of candidates) {
            html += '<div style="background:var(--bg-tile);border-radius:6px;padding:6px 10px;margin-bottom:4px;font-size:12px;border:1px solid var(--border-light);">';
            html += '<strong>' + esc(c.friendly_name) + '</strong>';
            html += '<div style="color:var(--text-muted);">' + esc(c.entity_id) + ' — ' + (c.state || '?') + (c.unit_of_measurement ? ' ' + c.unit_of_measurement : '') + '</div>';
            html += '</div>';
        }
        html += '</div>';
        html += '<div style="margin-top:8px;font-size:11px;color:var(--text-muted);">To add a probe, group 3 sensors (shallow/mid/deep) using the form below.</div>';
        // Quick add form
        html += '<div style="margin-top:10px;background:var(--bg-tile);border-radius:8px;padding:12px;border:1px solid var(--border-light);">';
        html += '<div style="font-size:13px;font-weight:600;margin-bottom:8px;">Add New Probe</div>';
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
        html += '<div><label style="font-size:11px;">Probe ID</label><input type="text" id="newProbeId" placeholder="e.g. gophr_backyard" style="width:100%;padding:4px;border:1px solid var(--border-input);border-radius:4px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;"></div>';
        html += '<div><label style="font-size:11px;">Display Name</label><input type="text" id="newProbeName" placeholder="e.g. Backyard Probe" style="width:100%;padding:4px;border:1px solid var(--border-input);border-radius:4px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;"></div>';
        html += '</div>';
        // Sensor dropdowns from discovered candidates
        const sensorOpts = candidates.map(c => '<option value="' + esc(c.entity_id) + '">' + esc(c.friendly_name || c.entity_id) + '</option>').join('');
        html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:8px;">';
        for (const depth of ['shallow', 'mid', 'deep']) {
            html += '<div><label style="font-size:11px;">' + depth.charAt(0).toUpperCase() + depth.slice(1) + '</label>';
            html += '<select id="newProbeSensor_' + depth + '" style="width:100%;padding:4px;border:1px solid var(--border-input);border-radius:4px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;">';
            html += '<option value="">— none —</option>' + sensorOpts;
            html += '</select></div>';
        }
        html += '</div>';
        // Zone multi-select
        html += '<div style="margin-top:8px;"><label style="font-size:11px;">Map to Zones (comma-separated entity_ids)</label>';
        html += '<input type="text" id="newProbeZones" placeholder="switch.zone_1, switch.zone_2" style="width:100%;padding:4px;border:1px solid var(--border-input);border-radius:4px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;"></div>';
        html += '<button class="btn btn-primary btn-sm" style="margin-top:8px;" onclick="addMoistureProbe()">Add Probe</button>';
        html += '</div>';
        container.innerHTML = html;
    } catch (e) { container.innerHTML = '<div style="color:var(--color-danger);font-size:12px;">' + esc(e.message) + '</div>'; }
}

async function addMoistureProbe() {
    const probeId = document.getElementById('newProbeId').value.trim();
    const name = document.getElementById('newProbeName').value.trim();
    if (!probeId) { showToast('Probe ID is required', 'error'); return; }
    const sensors = {};
    for (const d of ['shallow', 'mid', 'deep']) {
        const v = document.getElementById('newProbeSensor_' + d).value;
        if (v) sensors[d] = v;
    }
    const zonesStr = document.getElementById('newProbeZones').value.trim();
    const zones = zonesStr ? zonesStr.split(',').map(z => z.trim()).filter(z => z) : [];
    try {
        const result = await mapi('/probes', 'POST', {
            probe_id: probeId,
            display_name: name || probeId,
            sensors: sensors,
            zone_mappings: zones,
        });
        showToast('Probe added: ' + (result.probe?.display_name || probeId));
        loadMoisture();
    } catch (e) { showToast(e.message || 'Failed to add probe', 'error'); }
}

async function deleteMoistureProbe(probeId) {
    if (!confirm('Remove probe "' + probeId + '"?')) return;
    try {
        await mapi('/probes/' + encodeURIComponent(probeId), 'DELETE');
        showToast('Probe removed');
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

async function captureMoistureDurations() {
    try {
        const result = await mapi('/durations/capture', 'POST');
        showToast('Captured base durations for ' + result.captured + ' entities');
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

async function applyMoistureDurations() {
    try {
        const result = await mapi('/durations/apply', 'POST');
        showToast('Applied adjusted durations to ' + result.applied + ' zone(s)');
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

async function restoreMoistureDurations() {
    try {
        const result = await mapi('/durations/restore', 'POST');
        showToast('Restored base durations for ' + result.restored + ' entities');
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Dark Mode ---
function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('flux_dark_mode_homeowner', isDark);
    document.querySelector('.dark-toggle').textContent = isDark ? '☀️' : '🌙';
}
(function initDarkToggleIcon() {
    const btn = document.querySelector('.dark-toggle');
    if (btn && document.body.classList.contains('dark-mode')) btn.textContent = '☀️';
})();

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

// --- Help Modal ---
const HELP_CONTENT = `
<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:0 0 8px 0;">Dashboard Overview</h4>
<p style="margin-bottom:10px;">This is your irrigation control center. From here you can monitor and control every aspect of your irrigation system — zones, sensors, schedules, weather rules, and run history.</p>
<p style="margin-bottom:10px;">The dashboard auto-refreshes every 30 seconds to keep everything up to date.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Zone Control</h4>
<p style="margin-bottom:10px;">Each zone tile shows the current state (running or off). You can:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Start</strong> — Turn a zone on immediately with no time limit</li><li style="margin-bottom:4px;"><strong>Timed Start</strong> — Enter a duration in minutes and click <strong>Timed</strong> to run the zone for a set period, then auto-shutoff</li><li style="margin-bottom:4px;"><strong>Stop</strong> — Turn off a running zone immediately</li><li style="margin-bottom:4px;"><strong>Emergency Stop All</strong> — Instantly stops every active zone on the system</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Green-highlighted tiles indicate zones that are currently running.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Sensors</h4>
<p style="margin-bottom:10px;">The sensors card shows real-time readings from your irrigation controller — soil moisture, temperature, Wi-Fi signal strength, and any other sensors exposed by your device. Wi-Fi signal includes a quality badge (Great/Good/Poor/Bad) based on signal strength in dBm.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Schedule Management</h4>
<p style="margin-bottom:10px;">Your irrigation schedule is configured through your Flux Open Home controller and managed via its ESPHome entities:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Schedule Enable/Disable</strong> — Master toggle to turn the entire schedule on or off</li><li style="margin-bottom:4px;"><strong>Days of Week</strong> — Click day buttons to toggle which days the schedule runs</li><li style="margin-bottom:4px;"><strong>Start Times</strong> — Set when each schedule program begins (HH:MM format)</li><li style="margin-bottom:4px;"><strong>Zone Settings</strong> — Enable/disable individual zones and set run durations for each</li><li style="margin-bottom:4px;"><strong>Zone Modes</strong> — Some zones may have special modes (Pump Start Relay, Master Valve) that are firmware-controlled</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Schedule changes take effect immediately on your controller — no restart needed.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Weather-Based Control</h4>
<p style="margin-bottom:10px;">When weather is enabled (configured on the Configuration page), the dashboard shows current conditions and a <strong>watering multiplier</strong>:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>1.0x</strong> (green) — Normal watering, no adjustments active</li><li style="margin-bottom:4px;"><strong>Below 1.0x</strong> (yellow) — Reduced watering due to cool temps, humidity, etc.</li><li style="margin-bottom:4px;"><strong>Above 1.0x</strong> (red) — Increased watering due to hot temperatures</li><li style="margin-bottom:4px;"><strong>Skip/Pause</strong> — Watering paused entirely due to rain, freezing, or high wind</li></ul>
<p style="margin-bottom:10px;">Configure weather rules by expanding the <strong>Weather Rules</strong> section. Each rule can be individually enabled/disabled. Click <strong>Test Rules Now</strong> to see which rules would trigger under current conditions.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Moisture Probes (Gophr)</h4>
<p style="margin-bottom:10px;">When Gophr moisture probes are connected to Home Assistant, the moisture card shows live soil moisture readings at three depths (shallow, mid, deep). Probes are mapped to irrigation zones for intelligent watering adjustments:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Probe tiles</strong> — Color-coded bars showing moisture level at each depth, with stale-data indicators</li><li style="margin-bottom:4px;"><strong>Zone multipliers</strong> — Combined weather &times; moisture multiplier for each mapped zone</li><li style="margin-bottom:4px;"><strong>Duration status</strong> — Table showing base vs. adjusted run durations</li><li style="margin-bottom:4px;"><strong>Settings</strong> — Enable/disable, stale threshold, depth weights, and moisture thresholds (skip, wet, dry, max increase/decrease)</li><li style="margin-bottom:4px;"><strong>Manage Probes</strong> — Discover probes from HA sensors, add/remove probes, assign to zones</li><li style="margin-bottom:4px;"><strong>Duration Controls</strong> — Capture base durations, apply adjusted durations (for ESPHome schedules), or restore originals</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Moisture probes adjust both timed API/dashboard runs and ESPHome scheduled runs. Base durations are temporarily modified on the controller and restored after runs complete.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Run History</h4>
<p style="margin-bottom:10px;">The run history table shows every zone on/off event with:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Zone name</strong> and source (API, schedule, weather pause, etc.)</li><li style="margin-bottom:4px;"><strong>State</strong> — ON (green) or OFF</li><li style="margin-bottom:4px;"><strong>Time</strong> and <strong>duration</strong> of each run</li><li style="margin-bottom:4px;"><strong>Weather conditions</strong> at the time of the event</li></ul>
<p style="margin-bottom:10px;">Use the time range dropdown to view the last 24 hours, 7 days, 30 days, 90 days, or full year. Click <strong>Export CSV</strong> to download history as a spreadsheet.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">System Pause / Resume</h4>
<p style="margin-bottom:10px;"><strong>Pause System</strong> immediately stops all active zones and prevents any new zones from starting — including ESPHome schedule programs. While paused, any zone that tries to turn on will be automatically shut off.</p>
<p style="margin-bottom:10px;"><strong>Resume System</strong> lifts the pause and allows normal operation. Weather-triggered pauses auto-resume when conditions clear; manual pauses require clicking Resume.</p>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Use <strong>Emergency Stop All</strong> for a quick one-time stop. Use <strong>Pause System</strong> when you need to keep everything off until you manually resume.</div>
`;

function showHelp() {
    document.getElementById('helpContent').innerHTML = HELP_CONTENT;
    document.getElementById('helpModal').style.display = 'flex';
}
function closeHelpModal() {
    document.getElementById('helpModal').style.display = 'none';
}
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('helpModal').style.display === 'flex') {
        closeHelpModal();
    }
});
document.getElementById('helpModal').addEventListener('click', function(e) {
    if (e.target === this) closeHelpModal();
});
</script>
</body>
</html>
"""
