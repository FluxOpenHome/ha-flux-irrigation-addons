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

/* Schedule */
.schedule-program { background: #f8f9fa; border-radius: 8px; padding: 14px; border: 1px solid #eee; margin-bottom: 10px; }
.schedule-program-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.schedule-program-name { font-weight: 600; font-size: 14px; }
.schedule-program-enabled { font-size: 12px; padding: 2px 8px; border-radius: 10px; }
.schedule-program-enabled.yes { background: #e8f5e9; color: #27ae60; }
.schedule-program-enabled.no { background: #fde8e8; color: #e74c3c; }
.schedule-details { font-size: 13px; color: #555; }

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

        <!-- Schedule & Rain Delay Card -->
        <div class="card">
            <div class="card-header">
                <h2>Schedule</h2>
            </div>
            <div class="card-body" id="detailSchedule">
                <div class="loading">Loading schedule...</div>
            </div>
        </div>

        <!-- Rain Delay Card -->
        <div class="card">
            <div class="card-header"><h2>Rain Delay</h2></div>
            <div class="card-body" id="detailRainDelay">
                <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
                    <label style="font-size:13px;font-weight:500;color:#555;">Set rain delay:</label>
                    <input type="number" id="rainDelayHours" min="1" max="168" value="24" style="width:80px;padding:6px 10px;border:1px solid #ddd;border-radius:6px;font-size:14px;">
                    <span style="font-size:13px;color:#666;">hours</span>
                    <button class="btn btn-primary btn-sm" onclick="setRainDelay()">Set Delay</button>
                    <button class="btn btn-danger btn-sm" onclick="cancelRainDelay()">Cancel Delay</button>
                </div>
                <div id="rainDelayStatus" style="margin-top:10px;font-size:13px;color:#666;"></div>
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
        renderCustomerGrid(data.customers || []);
    } catch (e) {
        document.getElementById('customerGrid').innerHTML =
            '<div class="empty-state"><h3>Error loading properties</h3><p>' + e.message + '</p></div>';
    }
}

function renderCustomerGrid(customers) {
    const grid = document.getElementById('customerGrid');
    if (customers.length === 0) {
        grid.innerHTML = '<div class="empty-state"><h3>No properties connected</h3><p>Click "+ Add Property" to connect a homeowner\\'s irrigation system.</p></div>';
        return;
    }
    grid.innerHTML = customers.map(c => {
        const status = getCustomerStatus(c);
        const stats = getQuickStats(c);
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
                ${c.notes ? '<div style="font-size:13px;color:#7f8c8d;margin-bottom:6px;">' + esc(c.notes) + '</div>' : ''}
                <div class="customer-stats">
                    ${stats}
                </div>
                <div class="customer-actions" onclick="event.stopPropagation()">
                    <button class="btn btn-secondary btn-sm" onclick="checkCustomer('${c.id}')">Test Connection</button>
                    <button class="btn btn-danger btn-sm" onclick="removeCustomer('${c.id}', '${esc(c.name)}')">Remove</button>
                </div>
            </div>
        </div>`;
    }).join('');
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
    if (s.active_zones !== undefined && s.active_zones > 0) parts.push(`<span class="customer-stat"><strong>${s.active_zones}</strong> active</span>`);
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
        content.innerHTML = `URL: <strong>${esc(decoded.url)}</strong>` +
            (decoded.label ? `<br>Label: <strong>${esc(decoded.label)}</strong>` : '');
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
    } catch (e) {
        document.getElementById('detailName').textContent = 'Unknown Property';
    }

    loadDetailData(id);
    detailRefreshTimer = setInterval(() => loadDetailData(id), 15000);
}

function backToList() {
    currentCustomerId = null;
    document.getElementById('detailView').classList.remove('visible');
    document.getElementById('listView').style.display = 'block';
    if (detailRefreshTimer) { clearInterval(detailRefreshTimer); detailRefreshTimer = null; }
    loadCustomers();
    listRefreshTimer = setInterval(loadCustomers, 60000);
}

async function refreshDetail() {
    if (currentCustomerId) loadDetailData(currentCustomerId);
}

async function loadDetailData(id) {
    loadDetailStatus(id);  // also updates rain delay status and pause/resume button
    loadDetailZones(id);
    loadDetailSensors(id);
    loadDetailSchedule(id);
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
        // Update rain delay status
        const rdEl = document.getElementById('rainDelayStatus');
        if (s.rain_delay_active) {
            rdEl.innerHTML = '<span style="color:#f39c12;font-weight:500;">Rain delay active until ' + esc(s.rain_delay_until || 'unknown') + '</span>';
        } else {
            rdEl.innerHTML = '<span style="color:#95a5a6;">No rain delay active</span>';
        }
        el.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;">
            <div class="tile"><div class="tile-name">Connection</div><div class="tile-state ${s.ha_connected ? 'on' : ''}">${s.ha_connected ? 'Connected' : 'Disconnected'}</div></div>
            <div class="tile"><div class="tile-name">System</div><div class="tile-state ${s.system_paused ? '' : 'on'}">${s.system_paused ? 'Paused' : 'Active'}</div></div>
            <div class="tile"><div class="tile-name">Zones</div><div class="tile-state">${s.active_zones || 0} / ${s.total_zones || 0} active</div></div>
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
async function loadDetailZones(id) {
    const el = document.getElementById('detailZones');
    try {
        const data = await api('/customers/' + id + '/zones');
        const zones = data.zones || [];
        if (zones.length === 0) { el.innerHTML = '<div class="empty-state"><p>No zones found</p></div>'; return; }
        el.innerHTML = '<div class="tile-grid">' + zones.map(z => {
            const zId = z.name || z.entity_id;
            const isOn = z.state === 'on';
            return `
            <div class="tile ${isOn ? 'active' : ''}">
                <div class="tile-name">${esc(z.friendly_name || z.name || z.entity_id)}</div>
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

// --- Detail: Sensors ---
async function loadDetailSensors(id) {
    const el = document.getElementById('detailSensors');
    try {
        const data = await api('/customers/' + id + '/sensors');
        const sensors = data.sensors || [];
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

// --- Detail: Schedule ---
async function loadDetailSchedule(id) {
    const el = document.getElementById('detailSchedule');
    try {
        const data = await api('/customers/' + id + '/schedule');
        const programs = data.programs || [];
        if (programs.length === 0) { el.innerHTML = '<div class="empty-state"><p>No schedules configured</p></div>'; return; }
        el.innerHTML = programs.map(p => `
            <div class="schedule-program">
                <div class="schedule-program-header">
                    <span class="schedule-program-name">${esc(p.name || p.program_id)}</span>
                    <div style="display:flex;gap:6px;align-items:center;">
                        <span class="schedule-program-enabled ${p.enabled ? 'yes' : 'no'}">${p.enabled ? 'Enabled' : 'Disabled'}</span>
                        <button class="btn btn-danger btn-sm" onclick="deleteProgram('${id}','${esc(p.program_id)}','${esc(p.name || p.program_id)}')">Delete</button>
                    </div>
                </div>
                <div class="schedule-details">
                    ${p.days ? 'Days: ' + esc(p.days.join(', ')) : ''}
                    ${p.start_time ? ' &middot; Start: ' + esc(p.start_time) : ''}
                    ${p.zones ? ' &middot; ' + p.zones.length + ' zone(s): ' + p.zones.map(z => esc(z.zone_id) + ' (' + z.duration_minutes + 'min)').join(', ') : ''}
                </div>
            </div>`).join('');
    } catch (e) {
        el.innerHTML = '<div style="color:#e74c3c;">Failed to load schedule: ' + esc(e.message) + '</div>';
    }
}

async function deleteProgram(custId, programId, programName) {
    if (!confirm('Delete schedule program "' + programName + '"?')) return;
    try {
        await api('/customers/' + custId + '/schedule/program/' + programId, { method: 'DELETE' });
        showToast('Program deleted');
        setTimeout(() => loadDetailSchedule(custId), 500);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Detail: Rain Delay ---
async function setRainDelay() {
    if (!currentCustomerId) return;
    const hours = parseInt(document.getElementById('rainDelayHours').value);
    if (!hours || hours < 1 || hours > 168) { showToast('Enter hours between 1 and 168', 'error'); return; }
    try {
        await api('/customers/' + currentCustomerId + '/schedule/rain_delay', {
            method: 'POST',
            body: JSON.stringify({ hours }),
        });
        showToast('Rain delay set for ' + hours + ' hours');
        setTimeout(() => loadDetailStatus(currentCustomerId), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

async function cancelRainDelay() {
    if (!currentCustomerId) return;
    try {
        await api('/customers/' + currentCustomerId + '/schedule/rain_delay', { method: 'DELETE' });
        showToast('Rain delay cancelled');
        setTimeout(() => loadDetailStatus(currentCustomerId), 1000);
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
                <td style="padding:6px;">${esc(e.zone_name || e.entity_id)}</td>
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
