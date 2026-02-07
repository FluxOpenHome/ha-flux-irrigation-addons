"""
Flux Open Home - Management Dashboard UI
==========================================
HTML/CSS/JS for the management company dashboard.
Served at GET /admin when mode is "management".
"""

MANAGEMENT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Flux Irrigation - Management Dashboard</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f6fa; color: #2c3e50; }
.header { background: linear-gradient(135deg, #1a7a4c, #2ecc71); color: white; padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
.header h1 { font-size: 20px; font-weight: 600; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.mode-badge { background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
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

/* Customer Grid */
.customer-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.customer-card { background: white; border-radius: 12px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); border-left: 4px solid #bdc3c7; transition: all 0.2s ease; cursor: pointer; }
.customer-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.12); transform: translateY(-1px); }
.customer-card.online { border-left-color: #2ecc71; }
.customer-card.offline { border-left-color: #e74c3c; }
.customer-card.unknown { border-left-color: #f39c12; }
.customer-card-body { padding: 16px; }
.customer-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.customer-name { font-size: 16px; font-weight: 600; color: #2c3e50; }
.customer-status { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #7f8c8d; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.status-dot.online { background: #2ecc71; }
.status-dot.offline { background: #e74c3c; }
.status-dot.unknown { background: #f39c12; }
.customer-stats { display: flex; gap: 16px; font-size: 13px; color: #7f8c8d; margin-top: 8px; }
.customer-stat { display: flex; align-items: center; gap: 4px; }
.customer-stat strong { color: #2c3e50; }
.customer-actions { display: flex; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #eee; }

/* Add Customer Form */
.add-form { background: #f8f9fa; border-radius: 8px; padding: 16px; margin-bottom: 20px; display: none; }
.add-form.visible { display: block; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 13px; font-weight: 500; color: #555; margin-bottom: 4px; }
.form-group input, .form-group textarea { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; font-family: inherit; }
.form-group textarea { min-height: 80px; resize: vertical; font-family: monospace; }
.form-group .hint { font-size: 11px; color: #999; margin-top: 2px; }
.form-actions { display: flex; gap: 8px; margin-top: 12px; }
.key-preview { background: #e8f5e9; border: 1px solid #c8e6c9; border-radius: 6px; padding: 12px; margin-top: 12px; font-size: 13px; display: none; }
.key-preview.visible { display: block; }
.key-preview .label { font-weight: 600; color: #1a7a4c; margin-bottom: 4px; }

/* Detail View */
.detail-view { display: none; }
.detail-view.visible { display: block; }
.detail-back { display: flex; align-items: center; gap: 8px; color: #1a7a4c; font-size: 14px; font-weight: 500; cursor: pointer; margin-bottom: 16px; border: none; background: none; }
.detail-back:hover { text-decoration: underline; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.detail-header h2 { font-size: 22px; font-weight: 600; }

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

/* Search/Filter Bar */
.search-bar { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
.search-bar input { flex: 1; min-width: 200px; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
.search-bar input:focus { outline: none; border-color: #1a7a4c; }
.search-bar select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; background: white; }
.customer-address { font-size: 12px; color: #95a5a6; margin-bottom: 4px; }
.customer-meta { display: flex; gap: 12px; font-size: 12px; color: #7f8c8d; flex-wrap: wrap; }

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
    .customer-grid { grid-template-columns: 1fr; }
    .tile-grid { grid-template-columns: 1fr; }
    .container { padding: 12px; }
    .header h1 { font-size: 16px; }
}
</style>
</head>
<body>

<div class="header">
    <h1>Flux Irrigation Management</h1>
    <div class="header-actions">
        <span class="mode-badge">Management Mode</span>
        <button class="btn btn-secondary btn-sm" onclick="switchToHomeowner()">Switch to Homeowner</button>
    </div>
</div>

<div class="container">
    <!-- Customer List View -->
    <div id="listView">
        <div class="card">
            <div class="card-header">
                <h2>Properties</h2>
                <div style="display:flex;gap:8px;">
                    <button class="btn btn-secondary btn-sm" onclick="refreshAll()">Refresh All</button>
                    <button class="btn btn-primary btn-sm" onclick="toggleAddForm()">+ Add Property</button>
                </div>
            </div>
            <div class="card-body">
                <!-- Add Customer Form -->
                <div id="addForm" class="add-form">
                    <div class="form-group">
                        <label>Connection Key</label>
                        <textarea id="addKey" placeholder="Paste the connection key from the homeowner..." oninput="previewKey()"></textarea>
                        <p class="hint">The homeowner generates this key from their Flux Irrigation add-on.</p>
                    </div>
                    <div id="keyPreview" class="key-preview">
                        <div class="label">Key decoded:</div>
                        <div id="keyPreviewContent"></div>
                    </div>
                    <div class="form-group">
                        <label>Display Name (optional)</label>
                        <input type="text" id="addName" placeholder="e.g., Smith Residence - 123 Main St">
                    </div>
                    <div class="form-group">
                        <label>Notes (optional)</label>
                        <input type="text" id="addNotes" placeholder="e.g., Residential lawn, 6 zones">
                    </div>
                    <div class="form-actions">
                        <button class="btn btn-primary" onclick="addCustomer()">Connect</button>
                        <button class="btn btn-secondary" onclick="toggleAddForm()">Cancel</button>
                    </div>
                </div>

                <div class="search-bar" id="searchBar" style="display:none;">
                    <input type="text" id="searchInput" placeholder="Search by name, address, city, state, or ZIP..." oninput="filterCustomers()">
                    <select id="filterState" onchange="filterCustomers()">
                        <option value="">All States</option>
                    </select>
                    <select id="filterStatus" onchange="filterCustomers()">
                        <option value="">All Statuses</option>
                        <option value="online">Online</option>
                        <option value="offline">Offline</option>
                        <option value="unknown">Unknown</option>
                    </select>
                </div>

                <div id="customerGrid" class="customer-grid">
                    <div class="loading">Loading properties...</div>
                </div>
            </div>
        </div>
    </div>

    <!-- Customer Detail View -->
    <div id="detailView" class="detail-view">
        <button class="detail-back" onclick="backToList()">&larr; Back to Properties</button>
        <div class="detail-header">
            <div>
                <h2 id="detailName"></h2>
                <div id="detailAddress" class="customer-address" style="font-size:14px;margin-top:4px;"></div>
            </div>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-secondary btn-sm" onclick="refreshDetail()">Refresh</button>
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
                <h2>Recent Run History</h2>
                <span style="font-size:12px;color:#999;">Last 24 hours</span>
            </div>
            <div class="card-body" id="detailHistory">
                <div class="loading">Loading history...</div>
            </div>
        </div>
    </div>
</div>

<div class="toast-container" id="toastContainer"></div>

<script>
const BASE = (window.location.pathname.replace(/\\/+$/, '')) + '/api';
let currentCustomerId = null;
let detailRefreshTimer = null;
let listRefreshTimer = null;
let allCustomers = [];
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

// --- API Helper ---
async function api(path, options = {}) {
    const res = await fetch(BASE + path, {
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

// --- Customer List ---
async function loadCustomers() {
    try {
        const data = await api('/customers');
        allCustomers = data.customers || [];
        populateStateFilter(allCustomers);
        if (allCustomers.length > 2) {
            document.getElementById('searchBar').style.display = 'flex';
        } else {
            document.getElementById('searchBar').style.display = 'none';
        }
        filterCustomers();
    } catch (e) {
        document.getElementById('customerGrid').innerHTML =
            '<div class="empty-state"><h3>Error loading properties</h3><p>' + e.message + '</p></div>';
    }
}

function renderCustomerGrid(customers) {
    const grid = document.getElementById('customerGrid');
    if (customers.length === 0) {
        const isFiltered = document.getElementById('searchInput').value || document.getElementById('filterState').value || document.getElementById('filterStatus').value;
        grid.innerHTML = isFiltered
            ? '<div class="empty-state"><h3>No matching properties</h3><p>Try adjusting your search or filters.</p></div>'
            : '<div class="empty-state"><h3>No properties connected</h3><p>Click "+ Add Property" to connect a homeowner\\'s irrigation system.</p></div>';
        return;
    }
    grid.innerHTML = customers.map(c => {
        const status = getCustomerStatus(c);
        const stats = getQuickStats(c);
        const addr = formatAddress(c);
        const zoneInfo = c.zone_count ? '<span class="customer-stat"><strong>' + c.zone_count + '</strong> zones</span>' : '';
        return `
        <div class="customer-card ${status}" onclick="viewCustomer('${c.id}')">
            <div class="customer-card-body">
                <div class="customer-card-header">
                    <span class="customer-name">${esc(c.name)}</span>
                    <span class="customer-status">
                        <span class="status-dot ${status}"></span>
                        ${status === 'online' ? 'Online' : status === 'offline' ? 'Offline' : 'Unknown'}
                    </span>
                </div>
                ${addr ? '<div class="customer-address">' + esc(addr) + '</div>' : ''}
                ${c.notes ? '<div style="font-size:13px;color:#7f8c8d;margin-bottom:6px;">' + esc(c.notes) + '</div>' : ''}
                <div class="customer-stats">
                    ${zoneInfo}${stats}
                </div>
                <div class="customer-actions" onclick="event.stopPropagation()">
                    <button class="btn btn-secondary btn-sm" onclick="checkCustomer('${c.id}')">Test Connection</button>
                    <button class="btn btn-danger btn-sm" onclick="removeCustomer('${c.id}', '${esc(c.name)}')">Remove</button>
                </div>
            </div>
        </div>`;
    }).join('');
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

function populateStateFilter(customers) {
    const select = document.getElementById('filterState');
    const currentVal = select.value;
    const states = [...new Set(customers.map(c => c.state).filter(Boolean))].sort();
    select.innerHTML = '<option value="">All States</option>' + states.map(s => '<option value="' + esc(s) + '">' + esc(s) + '</option>').join('');
    select.value = currentVal;
}

function filterCustomers() {
    const search = (document.getElementById('searchInput').value || '').toLowerCase().trim();
    const stateFilter = document.getElementById('filterState').value;
    const statusFilter = document.getElementById('filterStatus').value;
    let filtered = allCustomers;
    if (search) {
        filtered = filtered.filter(c => {
            const haystack = [c.name, c.address, c.city, c.state, c.zip, c.notes].filter(Boolean).join(' ').toLowerCase();
            return haystack.includes(search);
        });
    }
    if (stateFilter) {
        filtered = filtered.filter(c => c.state === stateFilter);
    }
    if (statusFilter) {
        filtered = filtered.filter(c => getCustomerStatus(c) === statusFilter);
    }
    renderCustomerGrid(filtered);
}

function getCustomerStatus(c) {
    if (!c.last_status) return 'unknown';
    if (c.last_status.reachable && c.last_status.authenticated) return 'online';
    return 'offline';
}

function getQuickStats(c) {
    if (!c.last_status || !c.last_status.system_status) return '<span class="customer-stat">No data yet</span>';
    const s = c.last_status.system_status;
    let parts = [];
    if (s.total_zones !== undefined) parts.push(`<span class="customer-stat"><strong>${s.total_zones}</strong> zones</span>`);
    if (s.active_zones > 0 && s.active_zone_name) {
        const custAliases = c.zone_aliases || {};
        const aName = custAliases[s.active_zone_entity_id] || s.active_zone_name;
        parts.push(`<span class="customer-stat" style="color:#27ae60;"><strong>${esc(aName)}</strong> running</span>`);
    }
    if (s.total_sensors !== undefined) parts.push(`<span class="customer-stat"><strong>${s.total_sensors}</strong> sensors</span>`);
    if (s.system_paused) parts.push('<span class="customer-stat" style="color:#e74c3c;">Paused</span>');
    return parts.join('') || '<span class="customer-stat">Connected</span>';
}

function esc(str) {
    if (!str) return '';
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// --- Add Customer ---
function toggleAddForm() {
    const form = document.getElementById('addForm');
    form.classList.toggle('visible');
    if (!form.classList.contains('visible')) {
        document.getElementById('addKey').value = '';
        document.getElementById('addName').value = '';
        document.getElementById('addNotes').value = '';
        document.getElementById('keyPreview').classList.remove('visible');
    }
}

function previewKey() {
    const key = document.getElementById('addKey').value.trim();
    const preview = document.getElementById('keyPreview');
    const content = document.getElementById('keyPreviewContent');
    if (key.length < 10) { preview.classList.remove('visible'); return; }
    try {
        const decoded = JSON.parse(atob(key.replace(/-/g, '+').replace(/_/g, '/')));
        const connMode = decoded.mode === 'nabu_casa' ? 'Nabu Casa' : 'Direct';
        let html = 'URL: <strong>' + esc(decoded.url) + '</strong>';
        html += '<br>Mode: <strong>' + connMode + '</strong>';
        if (decoded.label) html += '<br>Label: <strong>' + esc(decoded.label) + '</strong>';
        const addrParts = [];
        if (decoded.address) addrParts.push(decoded.address);
        if (decoded.city) addrParts.push(decoded.city);
        if (decoded.state) addrParts.push(decoded.state);
        if (decoded.zip) addrParts.push(decoded.zip);
        if (addrParts.length > 0) html += '<br>Address: <strong>' + esc(addrParts.join(', ')) + '</strong>';
        if (decoded.zone_count) html += '<br>Zones: <strong>' + decoded.zone_count + '</strong>';
        content.innerHTML = html;
        preview.classList.add('visible');
    } catch (e) {
        content.innerHTML = '<span style="color:#e74c3c;">Invalid key format</span>';
        preview.classList.add('visible');
    }
}

async function addCustomer() {
    const key = document.getElementById('addKey').value.trim();
    const name = document.getElementById('addName').value.trim();
    const notes = document.getElementById('addNotes').value.trim();
    if (!key) { showToast('Paste a connection key', 'error'); return; }
    try {
        const data = await api('/customers', {
            method: 'POST',
            body: JSON.stringify({ connection_key: key, name: name || null, notes }),
        });
        showToast('Property connected: ' + data.customer.name);
        toggleAddForm();
        loadCustomers();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function removeCustomer(id, name) {
    if (!confirm('Remove "' + name + '"? This cannot be undone.')) return;
    try {
        await api('/customers/' + id, { method: 'DELETE' });
        showToast('Property removed');
        loadCustomers();
    } catch (e) { showToast(e.message, 'error'); }
}

async function checkCustomer(id) {
    try {
        showToast('Testing connection...');
        const data = await api('/customers/' + id + '/check', { method: 'POST' });
        if (data.reachable && data.authenticated) {
            showToast(data.customer_name + ': Connected successfully');
        } else if (data.reachable) {
            showToast(data.customer_name + ': Reachable but auth failed - ' + (data.error || ''), 'error');
        } else {
            showToast(data.customer_name + ': Unreachable - ' + (data.error || ''), 'error');
        }
        loadCustomers();
    } catch (e) { showToast(e.message, 'error'); }
}

async function refreshAll() {
    const data = await api('/customers').catch(() => ({ customers: [] }));
    const customers = data.customers || [];
    for (const c of customers) {
        api('/customers/' + c.id + '/check', { method: 'POST' }).catch(() => {});
    }
    showToast('Refreshing all connections...');
    setTimeout(loadCustomers, 3000);
}

// --- Detail View ---
async function viewCustomer(id) {
    currentCustomerId = id;
    document.getElementById('listView').style.display = 'none';
    document.getElementById('detailView').classList.add('visible');
    if (listRefreshTimer) { clearInterval(listRefreshTimer); listRefreshTimer = null; }

    try {
        const customer = await api('/customers/' + id);
        document.getElementById('detailName').textContent = customer.name;
        window._currentZoneAliases = customer.zone_aliases || {};
        const addr = formatAddress(customer);
        const addrEl = document.getElementById('detailAddress');
        if (addr) {
            addrEl.textContent = addr;
            addrEl.style.display = 'block';
        } else {
            addrEl.style.display = 'none';
        }
        initDetailMap(customer);
    } catch (e) {
        document.getElementById('detailName').textContent = 'Unknown Property';
        document.getElementById('detailAddress').style.display = 'none';
        document.getElementById('detailMap').style.display = 'none';
    }

    loadDetailData(id);
    detailRefreshTimer = setInterval(() => loadDetailData(id), 15000);
}

function backToList() {
    currentCustomerId = null;
    document.getElementById('detailView').classList.remove('visible');
    document.getElementById('listView').style.display = 'block';
    if (detailRefreshTimer) { clearInterval(detailRefreshTimer); detailRefreshTimer = null; }
    if (leafletMap) { leafletMap.remove(); leafletMap = null; }
    document.getElementById('detailMap').style.display = 'none';
    window._currentZoneAliases = {};
    window._zoneModes = {};
    loadCustomers();
    listRefreshTimer = setInterval(loadCustomers, 60000);
}

async function refreshDetail() {
    if (currentCustomerId) loadDetailData(currentCustomerId);
}

// --- Location Map ---
async function initDetailMap(customer) {
    const mapEl = document.getElementById('detailMap');
    const addr = formatAddress(customer);
    if (!addr) { mapEl.style.display = 'none'; return; }
    if (geocodeCache[addr]) {
        showMap(geocodeCache[addr].lat, geocodeCache[addr].lon, addr);
        return;
    }
    try {
        const res = await fetch(
            'https://nominatim.openstreetmap.org/search?format=json&limit=1&q=' +
            encodeURIComponent(addr),
            { headers: { 'User-Agent': 'FluxIrrigationDashboard/1.1.6' } }
        );
        const results = await res.json();
        if (results && results.length > 0) {
            const lat = parseFloat(results[0].lat);
            const lon = parseFloat(results[0].lon);
            geocodeCache[addr] = { lat, lon };
            showMap(lat, lon, addr);
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

async function loadDetailData(id) {
    loadDetailStatus(id);
    loadDetailZones(id);
    loadDetailSensors(id);
    loadDetailControls(id);  // Also renders the Schedule card from entities
    loadDetailHistory(id);
}

// --- Detail: Status ---
let currentSystemPaused = false;

async function loadDetailStatus(id) {
    const el = document.getElementById('detailStatus');
    try {
        const s = await api('/customers/' + id + '/status');
        currentSystemPaused = !!s.system_paused;
        const btn = document.getElementById('pauseResumeBtn');
        if (s.system_paused) {
            btn.textContent = 'Resume System';
            btn.className = 'btn btn-primary btn-sm';
        } else {
            btn.textContent = 'Pause System';
            btn.className = 'btn btn-secondary btn-sm';
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
    if (!currentCustomerId) return;
    const action = currentSystemPaused ? 'resume' : 'pause';
    if (!currentSystemPaused && !confirm('Pause the irrigation system? All active zones will be stopped.')) return;
    try {
        await api('/customers/' + currentCustomerId + '/system/' + action, { method: 'POST' });
        showToast('System ' + (action === 'pause' ? 'paused' : 'resumed'));
        setTimeout(() => loadDetailStatus(currentCustomerId), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Detail: Zones ---
function getZoneDisplayName(z) {
    // Check alias first, then zone mode, then friendly_name/name/entity_id
    const aliases = window._currentZoneAliases || {};
    if (aliases[z.entity_id]) return aliases[z.entity_id];
    // Try to extract zone number and check mode
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
    // Resolve display name for any entity_id: check alias, then zone mode, then fallback
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

async function loadDetailZones(id) {
    const el = document.getElementById('detailZones');
    try {
        const data = await api('/customers/' + id + '/zones');
        // /api/zones returns a bare list [...], not {zones: [...]}
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
                        ? '<button class="btn btn-danger btn-sm" onclick="stopZone(\\'' + id + '\\',\\'' + zId + '\\')">Stop</button>'
                        : '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + id + '\\',\\'' + zId + '\\', null)">Start</button>' +
                          '<span style="display:flex;align-items:center;gap:4px;margin-top:4px;"><input type="number" id="dur_' + zId + '" min="1" max="480" placeholder="min" style="width:60px;padding:3px 6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">' +
                          '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + id + '\\',\\'' + zId + '\\', document.getElementById(\\'dur_' + zId + '\\').value)">Timed</button></span>'
                    }
                </div>
            </div>`;
        }).join('') + '</div>';
    } catch (e) {
        el.innerHTML = '<div style="color:#e74c3c;">Failed to load zones: ' + esc(e.message) + '</div>';
    }
}

async function startZone(custId, zoneId, durationMinutes) {
    try {
        const body = {};
        if (durationMinutes && parseInt(durationMinutes) > 0) {
            body.duration_minutes = parseInt(durationMinutes);
        }
        await api('/customers/' + custId + '/zones/' + zoneId + '/start', { method: 'POST', body: JSON.stringify(body) });
        showToast('Zone started' + (body.duration_minutes ? ' for ' + body.duration_minutes + ' min' : ''));
        setTimeout(() => loadDetailZones(custId), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

async function stopZone(custId, zoneId) {
    try {
        await api('/customers/' + custId + '/zones/' + zoneId + '/stop', { method: 'POST' });
        showToast('Zone stopped');
        setTimeout(() => loadDetailZones(custId), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

async function stopAllZones() {
    if (!currentCustomerId) return;
    if (!confirm('Emergency stop ALL zones for this property?')) return;
    try {
        await api('/customers/' + currentCustomerId + '/zones/stop_all', { method: 'POST' });
        showToast('All zones stopped');
        setTimeout(() => loadDetailZones(currentCustomerId), 1000);
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
        await api('/customers/' + currentCustomerId + '/zone_aliases', {
            method: 'PUT',
            body: JSON.stringify({ zone_aliases: aliases }),
        });
        showToast('Zone renamed');
        loadDetailZones(currentCustomerId);
        loadDetailControls(currentCustomerId);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Detail: Sensors ---
async function loadDetailSensors(id) {
    const el = document.getElementById('detailSensors');
    try {
        const data = await api('/customers/' + id + '/sensors');
        // /api/sensors returns {sensors: [...], ...} but handle bare list too
        const sensors = Array.isArray(data) ? data : (data.sensors || []);
        if (sensors.length === 0) { el.innerHTML = '<div class="empty-state"><p>No sensors found</p></div>'; return; }
        el.innerHTML = '<div class="tile-grid">' + sensors.map(s => `
            <div class="tile">
                <div class="tile-name">${esc(s.friendly_name || s.name || s.entity_id)}</div>
                <div class="tile-state">${esc(s.state)}${s.unit_of_measurement ? ' ' + esc(s.unit_of_measurement) : ''}</div>
            </div>`).join('') + '</div>';
    } catch (e) {
        el.innerHTML = '<div style="color:#e74c3c;">Failed to load sensors: ' + esc(e.message) + '</div>';
    }
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
        domain === 'number' && /repeat/.test(eid),
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

// --- Detail: Device Controls (also populates Schedule card) ---
async function loadDetailControls(id) {
    const controlsEl = document.getElementById('detailControls');
    const scheduleEl = document.getElementById('detailSchedule');
    try {
        const data = await api('/customers/' + id + '/entities');
        const allEntities = Array.isArray(data) ? data : (data.entities || []);

        // Split entities into schedule vs. controls
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
                // Filter out redundant valve_N entities (duplicates of zone entities)
                const eid = (e.entity_id || '').toLowerCase();
                if (/valve_\\d+/.test(eid)) continue;
                controlEntities.push(e);
            }
        }

        // Build zone mode map for dynamic labels (Pump Start Relay, Master Valve, etc.)
        window._zoneModes = {};
        for (const zm of scheduleByCategory.zone_modes) {
            const num = extractZoneNumber(zm.entity_id, 'zone');
            if (num) window._zoneModes[num] = { state: zm.state, entity: zm };
        }

        // Render Device Controls (non-schedule entities only)
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
                    html += renderControlTile(id, e);
                }
                html += '</div></div>';
            }
            controlsEl.innerHTML = html;
        }

        // Render Schedule card from classified entities
        renderScheduleCard(id, scheduleByCategory);

    } catch (e) {
        controlsEl.innerHTML = '<div style="color:#e74c3c;">Failed to load controls: ' + esc(e.message) + '</div>';
        scheduleEl.innerHTML = '<div style="color:#e74c3c;">Failed to load schedule: ' + esc(e.message) + '</div>';
    }
}

function getZoneLabel(zoneNum) {
    // Check zone aliases first, then zone modes, then default
    const aliases = window._currentZoneAliases || {};
    const modes = window._zoneModes || {};
    // Try to find alias by matching zone number in any entity_id key
    for (const [eid, alias] of Object.entries(aliases)) {
        const m = eid.match(/zone[_\\s]*(\\d+)/i);
        if (m && m[1] === String(zoneNum) && alias) return alias;
    }
    // Check if zone has a special mode (Pump Start Relay, Master Valve, etc.)
    if (modes[zoneNum] && modes[zoneNum].state) {
        const modeVal = modes[zoneNum].state.toLowerCase();
        if (modeVal !== 'normal' && modeVal !== 'standard' && modeVal !== '' && modeVal !== 'unknown') {
            return modes[zoneNum].state;
        }
    }
    return 'Zone ' + zoneNum;
}

function renderScheduleCard(custId, sched) {
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
            'onclick="setEntityValue(\\'' + custId + '\\',\\'' + se.entity_id + '\\',\\'switch\\',' +
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
                    'onclick="setEntityValue(\\'' + custId + '\\',\\'' + dayEntity.entity_id + '\\',\\'switch\\',' +
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
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid +
                '\\',\\'text\\',{value:document.getElementById(\\'' + inputId + '\\').value})">Set</button>' +
                '</div></div>';
        }
        html += '</div></div>';
    }

    // --- Zone Settings (Enable + Run Duration + Mode paired by zone number) ---
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
        // Add zone modes to the map
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
            '<th>Enabled</th><th>Run Duration</th></tr></thead><tbody>';
        for (const zn of sortedZones) {
            const { enable, duration, mode } = zoneMap[zn];
            const zoneLabel = getZoneLabel(zn);
            // Check if this zone is a Pump Start Relay or Master Valve (no run duration)
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
                        'onchange="setEntityValue(\\'' + custId + '\\',\\'' + modeEid +
                        '\\',\\'select\\',{option:document.getElementById(\\'' + selId + '\\').value})">' +
                        optionsHtml + '</select></td>';
                } else {
                    html += '<td style="color:#95a5a6;">-</td>';
                }
            }
            if (enable) {
                const isOn = enable.state === 'on';
                html += '<td><button class="btn ' + (isOn ? 'btn-primary' : 'btn-secondary') + ' btn-sm" ' +
                    'onclick="setEntityValue(\\'' + custId + '\\',\\'' + enable.entity_id + '\\',\\'switch\\',' +
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
                    '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid +
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
            html += renderControlTile(custId, sc);
        }
        html += '</div></div>';
    }

    // --- Repeat Cycles ---
    if (repeat_cycles.length > 0) {
        html += '<div class="schedule-section"><div class="schedule-section-label">Repeat Cycles</div><div class="tile-grid">';
        for (const rc of repeat_cycles) {
            html += renderControlTile(custId, rc);
        }
        html += '</div></div>';
    }

    el.innerHTML = html;
}

function renderControlTile(custId, e) {
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
                    ? '<button class="btn btn-secondary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid + '\\',\\'' + domain + '\\',{state:\\'off\\'})">Turn Off</button>'
                    : '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid + '\\',\\'' + domain + '\\',{state:\\'on\\'})">Turn On</button>'
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
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid + '\\',\\'number\\',{value:parseFloat(document.getElementById(\\'num_' + eid + '\\').value)})">Set</button>' +
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
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid + '\\',\\'select\\',{option:document.getElementById(\\'sel_' + eid + '\\').value})">Set</button>' +
            '</div></div>';
    }

    if (domain === 'button') {
        return '<div class="tile">' +
            '<div class="tile-name">' + name + '</div>' +
            '<div class="tile-state">' + esc(state) + '</div>' +
            '<div class="tile-actions">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid + '\\',\\'button\\',{})">Press</button>' +
            '</div></div>';
    }

    if (domain === 'text') {
        return '<div class="tile">' +
            '<div class="tile-name">' + name + '</div>' +
            '<div class="tile-state">' + esc(state) + '</div>' +
            '<div class="tile-actions" style="flex-wrap:wrap;gap:4px;">' +
                '<input type="text" id="txt_' + eid + '" value="' + esc(state) + '" style="width:120px;padding:3px 6px;border:1px solid #ddd;border-radius:4px;font-size:12px;">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid + '\\',\\'text\\',{value:document.getElementById(\\'txt_' + eid + '\\').value})">Set</button>' +
            '</div></div>';
    }

    // Fallback for unknown domains — read-only display
    return '<div class="tile">' +
        '<div class="tile-name">' + name + '</div>' +
        '<div class="tile-state">' + esc(state) + '</div>' +
        '<div style="font-size:11px;color:#95a5a6;margin-top:4px;">' + esc(domain) + '</div>' +
        '</div>';
}

async function setEntityValue(custId, entityId, domain, bodyObj) {
    try {
        await api('/customers/' + custId + '/entities/' + entityId + '/set', {
            method: 'POST',
            body: JSON.stringify(bodyObj),
        });
        showToast('Updated ' + entityId.split('.').pop());
        setTimeout(() => loadDetailControls(custId), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Detail: History ---
async function loadDetailHistory(id) {
    const el = document.getElementById('detailHistory');
    try {
        const data = await api('/customers/' + id + '/history/runs?hours=24');
        const events = data.events || [];
        if (events.length === 0) { el.innerHTML = '<div class="empty-state"><p>No run events in the last 24 hours</p></div>'; return; }
        el.innerHTML = '<table style="width:100%;font-size:13px;border-collapse:collapse;"><thead><tr style="text-align:left;border-bottom:2px solid #eee;"><th style="padding:6px;">Zone</th><th style="padding:6px;">State</th><th style="padding:6px;">Time</th><th style="padding:6px;">Duration</th></tr></thead><tbody>' +
            events.slice(0, 50).map(e => `<tr style="border-bottom:1px solid #f0f0f0;">
                <td style="padding:6px;">${esc(resolveZoneName(e.entity_id, e.zone_name))}</td>
                <td style="padding:6px;">${e.state === 'on' ? '<span style="color:#27ae60;">ON</span>' : '<span style="color:#95a5a6;">OFF</span>'}</td>
                <td style="padding:6px;">${formatTime(e.timestamp)}</td>
                <td style="padding:6px;">${e.duration_seconds ? Math.round(e.duration_seconds / 60) + ' min' : '-'}</td>
            </tr>`).join('') + '</tbody></table>';
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

// --- Mode Switch ---
async function switchToHomeowner() {
    if (!confirm('Switch to Homeowner mode? The management dashboard will no longer be available until you switch back.')) return;
    try {
        await api('/mode', { method: 'PUT', body: JSON.stringify({ mode: 'homeowner' }) });
        showToast('Switching to homeowner mode...');
        setTimeout(() => window.location.reload(), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    loadCustomers();
    listRefreshTimer = setInterval(loadCustomers, 60000);
});
</script>
</body>
</html>
"""
