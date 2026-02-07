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
<title>Flux Open Home - Management Dashboard</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin=""/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<style>
:root {
    --bg-body: #f5f6fa;
    --bg-card: #ffffff;
    --bg-tile: #f8f9fa;
    --bg-input: #ffffff;
    --bg-form: #f8f9fa;
    --bg-weather: #f0f8ff;
    --bg-secondary-btn: #ecf0f1;
    --bg-secondary-btn-hover: #dfe6e9;
    --bg-active-tile: #e8f5e9;
    --bg-inactive-tile: #fbe9e7;
    --bg-toast: #2c3e50;
    --bg-warning: #fff3cd;
    --bg-success-light: #d4edda;
    --bg-danger-light: #f8d7da;
    --bg-revoked-card: #fafafa;
    --bg-key-preview: #e8f5e9;
    --border-key-preview: #c8e6c9;

    --text-primary: #2c3e50;
    --text-secondary: #666;
    --text-secondary-alt: #555;
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
}
body.dark-mode {
    --bg-body: #1a1a2e;
    --bg-card: #16213e;
    --bg-tile: #1a1a2e;
    --bg-input: #1a1a2e;
    --bg-form: #1a1a2e;
    --bg-weather: #16213e;
    --bg-secondary-btn: #253555;
    --bg-secondary-btn-hover: #2d4068;
    --bg-active-tile: #1b3a2a;
    --bg-inactive-tile: #3a2020;
    --bg-toast: #0f3460;
    --bg-warning: #3a3020;
    --bg-success-light: #1b3a2a;
    --bg-danger-light: #3a2020;
    --bg-revoked-card: #1a1a2e;
    --bg-key-preview: #1b3a2a;
    --border-key-preview: #2d7a4a;

    --text-primary: #e0e0e0;
    --text-secondary: #b0b0b0;
    --text-secondary-alt: #b0b0b0;
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

    --header-gradient: linear-gradient(135deg, #0f3460, #16213e);
    --shadow-card: 0 1px 3px rgba(0,0,0,0.3);
    --shadow-header: 0 2px 8px rgba(0,0,0,0.4);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-body); color: var(--text-primary); }
body.dark-mode input, body.dark-mode select, body.dark-mode textarea { background: var(--bg-input); color: var(--text-primary); border-color: var(--border-input); }
.header { background: var(--header-gradient); color: white; padding: 20px 24px; display: flex; align-items: center; justify-content: space-between; box-shadow: var(--shadow-header); }
.header h1 { font-size: 20px; font-weight: 600; }
.header-actions { display: flex; gap: 10px; align-items: center; }
.mode-badge { background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; }
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
.dark-toggle { background: rgba(255,255,255,0.15); border: none; border-radius: 8px; cursor: pointer; font-size: 16px; padding: 4px 8px; transition: background 0.15s; line-height: 1; }
.dark-toggle:hover { background: rgba(255,255,255,0.25); }

/* Customer Grid */
.customer-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.customer-card { background: var(--bg-card); border-radius: 12px; box-shadow: var(--shadow-card); border-left: 4px solid var(--border-card); transition: all 0.2s ease; cursor: pointer; }
.customer-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.12); transform: translateY(-1px); }
.customer-card.online { border-left-color: #2ecc71; }
.customer-card.offline { border-left-color: #e74c3c; }
.customer-card.revoked { border-left-color: var(--text-disabled); background: var(--bg-revoked-card); }
.customer-card.unknown { border-left-color: var(--color-warning); }
.customer-card-body { padding: 16px; }
.customer-card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
.customer-name { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.customer-status { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--text-muted); }
.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.status-dot.online { background: #2ecc71; }
.status-dot.offline { background: #e74c3c; }
.status-dot.revoked { background: #95a5a6; }
.status-dot.unknown { background: #f39c12; }
.customer-stats { display: flex; gap: 16px; font-size: 13px; color: var(--text-muted); margin-top: 8px; }
.customer-stat { display: flex; align-items: center; gap: 4px; }
.customer-stat strong { color: var(--text-primary); }
.customer-actions { display: flex; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border-light); }

/* Add Customer Form */
.add-form { background: var(--bg-form); border-radius: 8px; padding: 16px; margin-bottom: 20px; display: none; }
.add-form.visible { display: block; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 13px; font-weight: 500; color: var(--text-secondary-alt); margin-bottom: 4px; }
.form-group input, .form-group textarea { width: 100%; padding: 8px 12px; border: 1px solid var(--border-input); border-radius: 6px; font-size: 14px; font-family: inherit; background: var(--bg-input); color: var(--text-primary); }
.form-group textarea { min-height: 80px; resize: vertical; font-family: monospace; }
.form-group .hint { font-size: 11px; color: var(--text-placeholder); margin-top: 2px; }
.form-actions { display: flex; gap: 8px; margin-top: 12px; }
.key-preview { background: var(--bg-key-preview); border: 1px solid var(--border-key-preview); border-radius: 6px; padding: 12px; margin-top: 12px; font-size: 13px; display: none; }
.key-preview.visible { display: block; }
.key-preview .label { font-weight: 600; color: var(--color-primary); margin-bottom: 4px; }

/* Detail View */
.detail-view { display: none; }
.detail-view.visible { display: block; }
.detail-back { display: flex; align-items: center; gap: 8px; color: var(--color-primary); font-size: 14px; font-weight: 500; cursor: pointer; margin-bottom: 16px; border: none; background: none; }
.detail-back:hover { text-decoration: underline; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.detail-header h2 { font-size: 22px; font-weight: 600; }

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

/* Search/Filter Bar */
.search-bar { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
.search-bar input { flex: 1; min-width: 180px; padding: 8px 12px; border: 1px solid var(--border-input); border-radius: 6px; font-size: 14px; background: var(--bg-input); color: var(--text-primary); }
.search-bar input:focus { outline: none; border-color: var(--color-primary); }
.search-bar select { padding: 8px 10px; border: 1px solid var(--border-input); border-radius: 6px; font-size: 12px; background: var(--bg-card); color: var(--text-primary); cursor: pointer; }
.search-bar select:focus { outline: none; border-color: var(--color-primary); }
.filter-count { font-size: 12px; color: var(--text-muted); white-space: nowrap; }
.filter-count strong { color: var(--text-primary); }
.search-bar .filter-row { display: contents; }
.customer-address { font-size: 12px; color: var(--text-disabled); margin-bottom: 4px; }
.customer-meta { display: flex; gap: 12px; font-size: 12px; color: var(--text-muted); flex-wrap: wrap; }

/* Empty States */
.empty-state { text-align: center; padding: 40px 20px; color: var(--text-disabled); }
.empty-state h3 { font-size: 18px; margin-bottom: 8px; color: var(--text-muted); }
.empty-state p { font-size: 14px; }

/* Loading */
.loading { text-align: center; padding: 20px; color: var(--text-muted); font-size: 14px; }

/* Toast */
.toast-container { position: fixed; top: 20px; right: 20px; z-index: 1000; }
.toast { background: var(--bg-toast); color: white; padding: 12px 20px; border-radius: 8px; margin-bottom: 8px; font-size: 14px; animation: slideIn 0.3s ease; box-shadow: 0 4px 12px rgba(0,0,0,0.2); }
.toast.error { background: var(--color-danger); }
.toast.success { background: var(--color-success); }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }

/* Responsive */
@media (max-width: 600px) {
    .customer-grid { grid-template-columns: 1fr; }
    .tile-grid { grid-template-columns: 1fr; }
    .container { padding: 12px; }
    .header { flex-wrap: wrap; gap: 10px; padding: 14px 16px; }
    .header h1 { font-size: 16px; }
    .header-left img { height: 32px; }
    .header-actions { width: 100%; justify-content: flex-start; flex-wrap: wrap; gap: 6px; }
    .mode-badge { font-size: 11px; padding: 3px 8px; }
    .btn-sm { padding: 5px 8px; font-size: 11px; }
    .dark-toggle { font-size: 14px; padding: 3px 6px; }
    .search-bar { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
    .search-bar input { grid-column: 1 / -1; min-width: auto; font-size: 13px; padding: 7px 10px; }
    .search-bar select { font-size: 11px; padding: 6px 6px; }
    .search-bar .filter-row { display: contents; }
    .search-bar .filter-count { grid-column: 1 / -1; text-align: center; font-size: 11px; }
    .search-bar #clearFiltersBtn { grid-column: 1 / -1; }
    .days-row { gap: 4px; }
    .day-toggle { padding: 6px 10px; font-size: 12px; min-width: 44px; }
    .start-times-grid { grid-template-columns: 1fr; }
    .system-controls-row { flex-direction: column; }
    .detail-header { flex-direction: column; gap: 8px; align-items: flex-start; }
    .customer-card-body { padding: 12px; }
    .customer-actions { flex-wrap: wrap; }
}
</style>
</head>
<body>
<script>(function(){if(localStorage.getItem('flux_dark_mode_management')==='true')document.body.classList.add('dark-mode');})()</script>

<div class="header">
    <div class="header-left" style="display:flex;align-items:center;gap:14px;">
        <img src="data:image/png;base64,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" alt="Flux Open Home" style="height:44px;filter:brightness(0) invert(1);">
        <h1>Irrigation</h1>
    </div>
    <div class="header-actions">
        <span class="mode-badge">Management Mode</span>
        <button class="btn btn-secondary btn-sm" onclick="switchToHomeowner()">Homeowner</button>
        <button class="dark-toggle" onclick="toggleDarkMode()" title="Toggle dark mode">🌙</button>
        <button class="dark-toggle" onclick="showHelp()" title="Help">❓</button>
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
                        <p class="hint">The homeowner generates this key from their Flux Open Home Irrigation Control add-on.</p>
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
                    <input type="text" id="searchInput" placeholder="Search name, address, phone, notes..." oninput="filterCustomers()">
                    <div class="filter-row">
                        <select id="filterState" onchange="filterCustomers()">
                            <option value="">All States</option>
                        </select>
                        <select id="filterCity" onchange="filterCustomers()">
                            <option value="">All Cities</option>
                        </select>
                        <select id="filterZones" onchange="filterCustomers()">
                            <option value="">All Zones</option>
                            <option value="1-4">1–4 zones</option>
                            <option value="5-8">5–8 zones</option>
                            <option value="9-12">9–12 zones</option>
                            <option value="13+">13+ zones</option>
                        </select>
                        <select id="filterStatus" onchange="filterCustomers()">
                            <option value="">All Statuses</option>
                            <option value="online">Online</option>
                            <option value="offline">Offline</option>
                            <option value="revoked">Revoked</option>
                            <option value="unknown">Unknown</option>
                        </select>
                        <select id="filterSystemStatus" onchange="filterCustomers()">
                            <option value="">System State</option>
                            <option value="running">Running</option>
                            <option value="idle">Idle</option>
                            <option value="paused">Paused</option>
                        </select>
                        <select id="sortBy" onchange="filterCustomers()">
                            <option value="name">Sort: Name</option>
                            <option value="city">Sort: City</option>
                            <option value="state">Sort: State</option>
                            <option value="zones">Sort: Zones</option>
                            <option value="status">Sort: Status</option>
                            <option value="recent">Sort: Last Seen</option>
                        </select>
                    </div>
                    <span id="filterCount" class="filter-count"></span>
                    <button id="clearFiltersBtn" class="btn btn-secondary btn-sm" onclick="clearAllFilters()" style="display:none;">Clear Filters</button>
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
                <div id="detailContact" style="font-size:14px;color:var(--text-secondary-alt);margin-top:2px;display:none;">&#128100; <span id="detailContactName"></span></div>
                <div id="detailPhone" style="font-size:13px;color:var(--text-muted);margin-top:2px;display:none;">&#128222; <a id="detailPhoneLink" href="" style="color:var(--color-link);text-decoration:none;"></a></div>
            </div>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-secondary btn-sm" onclick="refreshDetail()">Refresh</button>
                <button class="btn btn-danger btn-sm" onclick="stopAllZones()">Emergency Stop All</button>
            </div>
        </div>

        <!-- Notes -->
        <div id="detailNotesSection" style="margin-bottom:16px;display:none;">
            <div id="detailNotesDisplay" style="display:flex;align-items:flex-start;gap:8px;">
                <div style="flex:1;">
                    <span style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;">Notes</span>
                    <div id="detailNotesText" style="font-size:14px;color:var(--text-secondary-alt);margin-top:2px;white-space:pre-wrap;"></div>
                </div>
                <button class="btn btn-secondary btn-sm" onclick="editDetailNotes()">Edit</button>
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
        <div class="card" id="detailWeatherCard" style="display:none;">
            <div class="card-header">
                <h2>Weather-Based Control</h2>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span id="detailWeatherBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-success-light);color:var(--text-success-dark);">1.0x</span>
                </div>
            </div>
            <div class="card-body" id="detailWeatherBody">
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
                    <select id="mgmtHistoryRange" onchange="loadDetailHistory(currentCustomerId)" style="padding:4px 8px;border:1px solid var(--border-input);border-radius:6px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">
                        <option value="24">Last 24 hours</option>
                        <option value="168">Last 7 days</option>
                        <option value="720">Last 30 days</option>
                        <option value="2160">Last 90 days</option>
                        <option value="8760">Last year</option>
                    </select>
                    <button class="btn btn-secondary btn-sm" onclick="mgmtExportHistoryCSV()">Export CSV</button>
                    <button class="btn btn-danger btn-sm" onclick="mgmtClearRunHistory()">Clear History</button>
                </div>
            </div>
            <div class="card-body" id="detailHistory">
                <div class="loading">Loading history...</div>
            </div>
        </div>
    </div>

    <!-- API Docs -->
    <div class="card" id="apiDocsCard" style="margin-top:24px;">
        <div class="card-body" style="text-align:center;padding:20px;">
            <p style="margin-bottom:10px;font-size:13px;color:var(--text-muted);">Interactive API documentation for this add-on:</p>
            <a id="docsLink" href="/api/docs" target="_blank" class="btn btn-secondary btn-sm">Open API Docs</a>
        </div>
    </div>
</div>

<!-- Notes Modal -->
<div id="notesModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:999;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:24px;width:90%;max-width:480px;box-shadow:0 8px 32px rgba(0,0,0,0.2);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <h3 style="font-size:16px;font-weight:600;margin:0;color:var(--text-primary);" id="notesModalTitle">Edit Notes</h3>
            <button onclick="closeNotesModal()" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <textarea id="notesModalInput" style="width:100%;min-height:120px;padding:10px 12px;border:1px solid var(--border-input);border-radius:8px;font-size:14px;font-family:inherit;resize:vertical;background:var(--bg-input);color:var(--text-primary);" placeholder="Add notes about this property..."></textarea>
        <div style="display:flex;gap:8px;margin-top:14px;justify-content:flex-end;">
            <button class="btn btn-secondary" onclick="closeNotesModal()">Cancel</button>
            <button class="btn btn-primary" onclick="saveModalNotes()">Save Notes</button>
        </div>
    </div>
</div>

<!-- Update Connection Key Modal -->
<div id="keyModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:999;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:24px;width:90%;max-width:520px;box-shadow:0 8px 32px rgba(0,0,0,0.2);">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
            <h3 style="font-size:16px;font-weight:600;margin:0;color:var(--text-primary);" id="keyModalTitle">&#128273; Update Connection Key</h3>
            <button onclick="closeKeyModal()" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <p style="font-size:13px;color:var(--text-muted);margin-bottom:12px;">Paste the new connection key from the homeowner. This will update the connection credentials while keeping your notes and zone aliases.</p>
        <textarea id="keyModalInput" style="width:100%;min-height:80px;padding:10px 12px;border:1px solid var(--border-input);border-radius:8px;font-size:13px;font-family:monospace;resize:vertical;background:var(--bg-input);color:var(--text-primary);" placeholder="Paste the new connection key here..."></textarea>
        <div id="keyModalPreview" style="margin-top:10px;font-size:12px;color:var(--text-secondary-alt);display:none;"></div>
        <div style="display:flex;gap:8px;margin-top:14px;justify-content:flex-end;">
            <button class="btn btn-secondary" onclick="closeKeyModal()">Cancel</button>
            <button class="btn btn-primary" onclick="saveModalKey()">&#128273; Update Key</button>
        </div>
    </div>
</div>

<!-- Help Modal -->
<div id="helpModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:999;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:640px;max-height:80vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">Management Dashboard Help</h3>
            <button onclick="closeHelpModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div id="helpContent" style="padding:16px 24px 24px 24px;overflow-y:auto;font-size:14px;color:var(--text-secondary);line-height:1.6;"></div>
    </div>
</div>

<div class="toast-container" id="toastContainer"></div>

<script>
function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('flux_dark_mode_management', isDark);
    document.querySelector('.dark-toggle').textContent = isDark ? '☀️' : '🌙';
}
(function initDarkToggleIcon() {
    const btn = document.querySelector('.dark-toggle');
    if (btn && document.body.classList.contains('dark-mode')) btn.textContent = '☀️';
})();

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
        populateCityFilter(allCustomers);
        document.getElementById('searchBar').style.display = allCustomers.length > 0 ? 'flex' : 'none';
        filterCustomers();
    } catch (e) {
        document.getElementById('customerGrid').innerHTML =
            '<div class="empty-state"><h3>Error loading properties</h3><p>' + e.message + '</p></div>';
    }
}

function renderCustomerGrid(customers) {
    const grid = document.getElementById('customerGrid');
    if (customers.length === 0) {
        const isFiltered = document.getElementById('searchInput').value || document.getElementById('filterState').value || document.getElementById('filterCity').value || document.getElementById('filterZones').value || document.getElementById('filterStatus').value || document.getElementById('filterSystemStatus').value;
        grid.innerHTML = isFiltered
            ? '<div class="empty-state"><h3>No matching properties</h3><p>Try adjusting your search or filters.</p></div>'
            : '<div class="empty-state"><h3>No properties connected</h3><p>Click "+ Add Property" to connect a homeowner\\'s irrigation system.</p></div>';
        return;
    }
    grid.innerHTML = customers.map(c => {
        const status = getCustomerStatus(c);
        const stats = getQuickStats(c);
        const addr = formatAddress(c);
        const contactName = [c.first_name, c.last_name].filter(Boolean).join(' ');
        const zoneInfo = c.zone_count ? '<span class="customer-stat"><strong>' + c.zone_count + '</strong> zones</span>' : '';
        return `
        <div class="customer-card ${status}" onclick="viewCustomer('${c.id}')">
            <div class="customer-card-body">
                <div class="customer-card-header">
                    <span class="customer-name">${esc(c.name)}</span>
                    <span class="customer-status">
                        <span class="status-dot ${status}"></span>
                        ${status === 'online' ? 'Online' : status === 'revoked' ? '<span style="color:var(--text-disabled);">Access Revoked</span>' : status === 'offline' ? 'Offline' : 'Unknown'}
                    </span>
                </div>
                ${contactName ? '<div style="font-size:13px;color:var(--text-secondary-alt);margin-bottom:2px;">&#128100; ' + esc(contactName) + '</div>' : ''}
                ${addr ? '<div class="customer-address">' + esc(addr) + '</div>' : ''}
                ${c.phone ? '<div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">&#128222; <a href="tel:' + esc(c.phone) + '" style="color:var(--color-link);text-decoration:none;" onclick="event.stopPropagation();">' + esc(c.phone) + '</a></div>' : ''}
                ${c.notes ? '<div style="font-size:13px;color:var(--text-muted);margin-bottom:6px;">' + esc(c.notes) + '</div>' : ''}
                <div class="customer-stats">
                    ${zoneInfo}${stats}
                </div>
                <div class="customer-actions" onclick="event.stopPropagation()">
                    <button class="btn btn-secondary btn-sm" onclick="editCardNotes('${c.id}', event)">Notes</button>
                    <button class="btn btn-secondary btn-sm" onclick="updateCardKey('${c.id}', event)" title="Update Connection Key">&#128273; Update Key</button>
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

function populateCityFilter(customers, stateFilter) {
    const select = document.getElementById('filterCity');
    const currentVal = select.value;
    let pool = customers;
    if (stateFilter) pool = customers.filter(c => c.state === stateFilter);
    const cities = [...new Set(pool.map(c => c.city).filter(Boolean))].sort();
    select.innerHTML = '<option value="">All Cities</option>' + cities.map(c => '<option value="' + esc(c) + '">' + esc(c) + '</option>').join('');
    // Keep selection if still valid, otherwise reset
    if (cities.includes(currentVal)) { select.value = currentVal; } else { select.value = ''; }
}

function getSystemStatus(c) {
    if (!c.last_status || !c.last_status.system_status) return '';
    const s = c.last_status.system_status;
    if (s.system_paused) return 'paused';
    if (s.active_zones > 0) return 'running';
    return 'idle';
}

function filterCustomers() {
    const search = (document.getElementById('searchInput').value || '').toLowerCase().trim();
    const stateFilter = document.getElementById('filterState').value;
    // Re-populate cities based on selected state
    populateCityFilter(allCustomers, stateFilter);
    const cityFilter = document.getElementById('filterCity').value;
    const zonesFilter = document.getElementById('filterZones').value;
    const statusFilter = document.getElementById('filterStatus').value;
    const systemStatusFilter = document.getElementById('filterSystemStatus').value;
    const sortBy = document.getElementById('sortBy').value;

    let filtered = allCustomers;
    if (search) {
        filtered = filtered.filter(c => {
            const haystack = [c.name, c.first_name, c.last_name, c.address, c.city, c.state, c.zip, c.phone, c.notes].filter(Boolean).join(' ').toLowerCase();
            return haystack.includes(search);
        });
    }
    if (stateFilter) {
        filtered = filtered.filter(c => c.state === stateFilter);
    }
    if (cityFilter) {
        filtered = filtered.filter(c => c.city === cityFilter);
    }
    if (zonesFilter) {
        filtered = filtered.filter(c => {
            const z = c.zone_count || 0;
            if (zonesFilter === '1-4') return z >= 1 && z <= 4;
            if (zonesFilter === '5-8') return z >= 5 && z <= 8;
            if (zonesFilter === '9-12') return z >= 9 && z <= 12;
            if (zonesFilter === '13+') return z >= 13;
            return true;
        });
    }
    if (statusFilter) {
        filtered = filtered.filter(c => getCustomerStatus(c) === statusFilter);
    }
    if (systemStatusFilter) {
        filtered = filtered.filter(c => getSystemStatus(c) === systemStatusFilter);
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
        if (sortBy === 'name') return (a.name || '').localeCompare(b.name || '');
        if (sortBy === 'city') return (a.city || '').localeCompare(b.city || '');
        if (sortBy === 'state') {
            const sc = (a.state || '').localeCompare(b.state || '');
            return sc !== 0 ? sc : (a.city || '').localeCompare(b.city || '');
        }
        if (sortBy === 'zones') return (b.zone_count || 0) - (a.zone_count || 0);
        if (sortBy === 'status') {
            const order = { online: 0, offline: 1, revoked: 2, unknown: 3 };
            return (order[getCustomerStatus(a)] || 2) - (order[getCustomerStatus(b)] || 2);
        }
        if (sortBy === 'recent') {
            return (b.last_seen_online || '').localeCompare(a.last_seen_online || '');
        }
        return 0;
    });

    // Update filter count and clear button
    const hasFilters = search || stateFilter || cityFilter || zonesFilter || statusFilter || systemStatusFilter;
    const countEl = document.getElementById('filterCount');
    const clearBtn = document.getElementById('clearFiltersBtn');
    if (hasFilters) {
        countEl.innerHTML = '<strong>' + filtered.length + '</strong> of ' + allCustomers.length + ' properties';
        clearBtn.style.display = '';
    } else {
        countEl.innerHTML = allCustomers.length + ' properties';
        clearBtn.style.display = 'none';
    }

    renderCustomerGrid(filtered);
}

function clearAllFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('filterState').value = '';
    document.getElementById('filterCity').value = '';
    document.getElementById('filterZones').value = '';
    document.getElementById('filterStatus').value = '';
    document.getElementById('filterSystemStatus').value = '';
    document.getElementById('sortBy').value = 'name';
    filterCustomers();
}

function getCustomerStatus(c) {
    if (!c.last_status) return 'unknown';
    if (c.last_status.revoked) return 'revoked';
    if (c.last_status.reachable && c.last_status.authenticated) return 'online';
    return 'offline';
}

function getQuickStats(c) {
    if (getCustomerStatus(c) === 'revoked') return '<span class="customer-stat" style="color:var(--text-disabled);"><strong>Homeowner revoked access</strong></span>';
    if (!c.last_status || !c.last_status.system_status) {
        if (c.last_status && c.last_status.error) return '<span class="customer-stat" style="color:var(--color-warning);">' + esc(c.last_status.error) + '</span>';
        return '<span class="customer-stat">No data yet</span>';
    }
    const s = c.last_status.system_status;
    let parts = [];
    if (s.system_paused) {
        parts.push('<span class="customer-stat" style="color:var(--color-danger);"><strong>Paused</strong></span>');
    } else if (s.active_zones > 0 && s.active_zone_name) {
        const custAliases = c.zone_aliases || {};
        const aName = custAliases[s.active_zone_entity_id] || s.active_zone_name;
        parts.push(`<span class="customer-stat" style="color:var(--color-success);"><strong>${esc(aName)}</strong> running</span>`);
    } else {
        parts.push('<span class="customer-stat"><strong>Idle</strong></span>');
    }
    if (s.total_sensors !== undefined) parts.push(`<span class="customer-stat"><strong>${s.total_sensors}</strong> sensors</span>`);
    return parts.join('') || '<span class="customer-stat">Connected</span>';
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
        content.innerHTML = '<span style="color:var(--color-danger);">Invalid key format</span>';
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
        } else if (data.revoked) {
            showToast(data.customer_name + ': Access Revoked — the homeowner has revoked management access', 'error');
        } else if (data.reachable && !data.authenticated) {
            showToast(data.customer_name + ': ' + (data.error || 'Authentication failed'), 'error');
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

// --- Notes Editing ---
let notesModalCustomerId = null;
let notesModalSource = null; // 'card' or 'detail'

function editCardNotes(id, event) {
    event.stopPropagation();
    const c = allCustomers.find(c => c.id === id);
    openNotesModal(id, c ? c.name : 'Property', c ? (c.notes || '') : '', 'card');
}

function openNotesModal(id, name, notes, source) {
    notesModalCustomerId = id;
    notesModalSource = source;
    document.getElementById('notesModalTitle').textContent = 'Notes — ' + name;
    document.getElementById('notesModalInput').value = notes;
    const modal = document.getElementById('notesModal');
    modal.style.display = 'flex';
    setTimeout(() => document.getElementById('notesModalInput').focus(), 50);
}

function closeNotesModal() {
    document.getElementById('notesModal').style.display = 'none';
    notesModalCustomerId = null;
    notesModalSource = null;
}


async function saveModalNotes() {
    if (!notesModalCustomerId) return;
    const id = notesModalCustomerId;
    const source = notesModalSource;
    const notes = document.getElementById('notesModalInput').value.trim();
    try {
        await api('/customers/' + id, {
            method: 'PUT',
            body: JSON.stringify({ notes }),
        });
        showToast('Notes saved');
        closeNotesModal();
        // Update detail view if viewing this customer
        if (source === 'detail' || currentCustomerId === id) {
            window._currentCustomerNotes = notes;
            const notesText = document.getElementById('detailNotesText');
            if (notesText) {
                notesText.textContent = notes || 'No notes yet — click Edit to add.';
                notesText.style.fontStyle = notes ? 'normal' : 'italic';
                notesText.style.color = notes ? 'var(--text-secondary-alt)' : 'var(--text-disabled)';
            }
        }
        loadCustomers();
    } catch (e) { showToast(e.message, 'error'); }
}

function editDetailNotes() {
    if (!currentCustomerId) return;
    const c = allCustomers.find(c => c.id === currentCustomerId);
    const name = c ? c.name : (document.getElementById('detailName').textContent || 'Property');
    openNotesModal(currentCustomerId, name, window._currentCustomerNotes || '', 'detail');
}

// --- Update Connection Key Modal ---
let keyModalCustomerId = null;

function updateCardKey(id, event) {
    event.stopPropagation();
    const c = allCustomers.find(c => c.id === id);
    openKeyModal(id, c ? c.name : 'Property');
}

function openKeyModal(id, name) {
    keyModalCustomerId = id;
    document.getElementById('keyModalTitle').innerHTML = '&#128273; Update Key — ' + esc(name);
    document.getElementById('keyModalInput').value = '';
    document.getElementById('keyModalPreview').style.display = 'none';
    const modal = document.getElementById('keyModal');
    modal.style.display = 'flex';
    setTimeout(() => document.getElementById('keyModalInput').focus(), 50);
}

function closeKeyModal() {
    document.getElementById('keyModal').style.display = 'none';
    keyModalCustomerId = null;
}

async function saveModalKey() {
    if (!keyModalCustomerId) return;
    const id = keyModalCustomerId;
    const key = document.getElementById('keyModalInput').value.trim();
    if (!key) { showToast('Paste a connection key', 'error'); return; }
    try {
        const data = await api('/customers/' + id + '/connection-key', {
            method: 'PUT',
            body: JSON.stringify({ connection_key: key }),
        });
        if (data.connectivity && data.connectivity.reachable && data.connectivity.authenticated) {
            showToast('Connection key updated — connected successfully!');
        } else {
            showToast('Connection key updated — ' + (data.connectivity ? (data.connectivity.error || 'checking connection...') : 'will check connection shortly'), 'error');
        }
        closeKeyModal();
        loadCustomers();
        if (currentCustomerId === id) refreshDetail();
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Detail View ---
async function viewCustomer(id) {
    currentCustomerId = id;
    document.getElementById('listView').style.display = 'none';
    document.getElementById('apiDocsCard').style.display = 'none';
    document.getElementById('detailView').classList.add('visible');
    if (listRefreshTimer) { clearInterval(listRefreshTimer); listRefreshTimer = null; }

    try {
        const customer = await api('/customers/' + id);
        document.getElementById('detailName').textContent = customer.name;
        window._currentZoneAliases = customer.zone_aliases || {};
        window._currentCustomerNotes = customer.notes || '';
        const addr = formatAddress(customer);
        const addrEl = document.getElementById('detailAddress');
        if (addr) {
            addrEl.textContent = addr;
            addrEl.style.display = 'block';
        } else {
            addrEl.style.display = 'none';
        }
        // Show contact name
        const contactEl = document.getElementById('detailContact');
        const contactName = [customer.first_name, customer.last_name].filter(Boolean).join(' ');
        if (contactName) {
            document.getElementById('detailContactName').textContent = contactName;
            contactEl.style.display = 'block';
        } else {
            contactEl.style.display = 'none';
        }
        // Show phone
        const phoneEl = document.getElementById('detailPhone');
        if (customer.phone) {
            document.getElementById('detailPhoneLink').textContent = customer.phone;
            document.getElementById('detailPhoneLink').href = 'tel:' + customer.phone;
            phoneEl.style.display = 'block';
        } else {
            phoneEl.style.display = 'none';
        }
        // Show notes section
        const notesSection = document.getElementById('detailNotesSection');
        const notesText = document.getElementById('detailNotesText');
        notesSection.style.display = 'block';
        notesText.textContent = customer.notes || 'No notes yet — click Edit to add.';
        notesText.style.fontStyle = customer.notes ? 'normal' : 'italic';
        notesText.style.color = customer.notes ? 'var(--text-secondary-alt)' : 'var(--text-disabled)';
        initDetailMap(customer);
    } catch (e) {
        document.getElementById('detailName').textContent = 'Unknown Property';
        document.getElementById('detailAddress').style.display = 'none';
        document.getElementById('detailContact').style.display = 'none';
        document.getElementById('detailPhone').style.display = 'none';
        document.getElementById('detailMap').style.display = 'none';
        document.getElementById('detailNotesSection').style.display = 'none';
    }

    loadDetailData(id);
    detailRefreshTimer = setInterval(() => loadDetailData(id), 15000);
}

function backToList() {
    currentCustomerId = null;
    document.getElementById('detailView').classList.remove('visible');
    document.getElementById('listView').style.display = 'block';
    document.getElementById('apiDocsCard').style.display = 'block';
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

let mapCenter = null;

function showMap(lat, lon, label) {
    const mapEl = document.getElementById('detailMap');
    mapEl.style.display = 'block';
    if (leafletMap) { leafletMap.remove(); leafletMap = null; }
    mapCenter = { lat, lon };
    leafletMap = L.map('detailMap').setView([lat, lon], 16);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
    }).addTo(leafletMap);
    L.marker([lat, lon]).addTo(leafletMap).bindPopup(esc(label)).openPopup();
    // Recenter button
    const RecenterControl = L.Control.extend({
        options: { position: 'topleft' },
        onAdd: function() {
            const btn = L.DomUtil.create('div', 'leaflet-bar');
            btn.innerHTML = '<a href="#" title="Recenter map" style="display:flex;align-items:center;justify-content:center;width:30px;height:30px;font-size:16px;text-decoration:none;color:#333;background:#fff;">⌖</a>';
            btn.style.cursor = 'pointer';
            L.DomEvent.on(btn, 'click', function(e) {
                L.DomEvent.stop(e);
                if (leafletMap && mapCenter) leafletMap.setView([mapCenter.lat, mapCenter.lon], 16);
            });
            return btn;
        }
    });
    leafletMap.addControl(new RecenterControl());
    setTimeout(() => { if (leafletMap) leafletMap.invalidateSize(); }, 200);
}

async function loadDetailData(id) {
    loadDetailStatus(id);
    loadDetailWeather(id);
    loadDetailZones(id);
    loadDetailSensors(id);
    loadDetailControls(id);  // Also renders the Schedule card from entities
    loadDetailHistory(id);
}

// --- Detail: Weather ---
async function loadDetailWeather(id) {
    const card = document.getElementById('detailWeatherCard');
    const body = document.getElementById('detailWeatherBody');
    const badge = document.getElementById('detailWeatherBadge');
    try {
        const data = await api('/customers/' + id + '/weather');
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
        html += '<div style="font-weight:600;text-transform:capitalize;font-size:13px;color:var(--text-primary);">' + esc(w.condition || 'unknown') + '</div>';
        html += '</div>';
        html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
        html += '<div style="color:var(--text-placeholder);font-size:11px;">Temperature</div>';
        html += '<div style="font-weight:600;font-size:16px;color:var(--text-primary);">' + (w.temperature != null ? w.temperature + (w.temperature_unit || '°F') : 'N/A') + '</div>';
        html += '</div>';
        html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
        html += '<div style="color:var(--text-placeholder);font-size:11px;">Humidity</div>';
        html += '<div style="font-weight:600;font-size:16px;color:var(--text-primary);">' + (w.humidity != null ? w.humidity + '%' : 'N/A') + '</div>';
        html += '</div>';
        html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
        html += '<div style="color:var(--text-placeholder);font-size:11px;">Wind</div>';
        html += '<div style="font-weight:600;font-size:16px;color:var(--text-primary);">' + (w.wind_speed != null ? w.wind_speed + ' ' + (w.wind_speed_unit || 'mph') : 'N/A') + '</div>';
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
        html += '<button class="btn btn-secondary btn-sm" onclick="mgmtEvaluateWeather()">Test Rules Now</button>';
        html += '<button class="btn btn-secondary btn-sm" onclick="mgmtExportWeatherLogCSV()">Export Log</button>';
        html += '<button class="btn btn-danger btn-sm" onclick="mgmtClearWeatherLog()">Clear Log</button>';
        html += '</div>';
        html += '</div>';
        html += '<div id="mgmtWeatherRulesContainer"><div class="loading">Loading rules...</div></div>';
        html += '</div>';

        body.innerHTML = html;

        // Load rules into the container
        loadMgmtWeatherRules(id);
    } catch (e) {
        card.style.display = 'none';
    }
}

async function loadMgmtWeatherRules(custId) {
    const container = document.getElementById('mgmtWeatherRulesContainer');
    if (!container) return;
    try {
        const data = await api('/customers/' + custId + '/weather/rules');
        const rules = data.rules || {};
        let html = '<div style="display:flex;flex-direction:column;gap:8px;">';

        // Rule 1: Rain Detection
        const r1 = rules.rain_detection || {};
        html += mgmtBuildRuleRow('rain_detection', 'Rain Detection', 'Pause when currently raining', r1.enabled, [
            { id: 'mgmt_rain_detection_resume_delay_hours', label: 'Resume delay (hours)', value: r1.resume_delay_hours || 2, type: 'number', min: 0, max: 24, step: 1 }
        ]);

        // Rule 2: Rain Forecast
        const r2 = rules.rain_forecast || {};
        html += mgmtBuildRuleRow('rain_forecast', 'Rain Forecast', 'Skip when rain probability exceeds threshold', r2.enabled, [
            { id: 'mgmt_rain_forecast_probability_threshold', label: 'Probability %', value: r2.probability_threshold || 60, type: 'number', min: 10, max: 100, step: 5 }
        ]);

        // Rule 3: Precipitation Threshold
        const r3 = rules.precipitation_threshold || {};
        html += mgmtBuildRuleRow('precipitation_threshold', 'Precipitation Amount', 'Skip when expected rainfall exceeds threshold', r3.enabled, [
            { id: 'mgmt_precipitation_threshold_mm', label: 'Threshold (mm)', value: r3.skip_if_rain_above_mm || 6, type: 'number', min: 1, max: 50, step: 1 }
        ]);

        // Rule 4: Freeze Protection
        const r4 = rules.temperature_freeze || {};
        html += mgmtBuildRuleRow('temperature_freeze', 'Freeze Protection', 'Skip when temperature is at or below freezing', r4.enabled, [
            { id: 'mgmt_temperature_freeze_f', label: 'Threshold (°F)', value: r4.freeze_threshold_f || 35, type: 'number', min: 20, max: 45, step: 1 },
            { id: 'mgmt_temperature_freeze_c', label: 'Threshold (°C)', value: r4.freeze_threshold_c || 2, type: 'number', min: -5, max: 7, step: 1 }
        ]);

        // Rule 5: Cool Temperature
        const r5 = rules.temperature_cool || {};
        html += mgmtBuildRuleRow('temperature_cool', 'Cool Temperature', 'Reduce watering in cool weather', r5.enabled, [
            { id: 'mgmt_temperature_cool_f', label: 'Below (°F)', value: r5.cool_threshold_f || 60, type: 'number', min: 40, max: 75, step: 1 },
            { id: 'mgmt_temperature_cool_c', label: 'Below (°C)', value: r5.cool_threshold_c || 15, type: 'number', min: 5, max: 25, step: 1 },
            { id: 'mgmt_temperature_cool_reduction', label: 'Reduce %', value: r5.reduction_percent || 25, type: 'number', min: 5, max: 75, step: 5 }
        ]);

        // Rule 6: Hot Temperature
        const r6 = rules.temperature_hot || {};
        html += mgmtBuildRuleRow('temperature_hot', 'Hot Temperature', 'Increase watering in hot weather', r6.enabled, [
            { id: 'mgmt_temperature_hot_f', label: 'Above (°F)', value: r6.hot_threshold_f || 95, type: 'number', min: 80, max: 120, step: 1 },
            { id: 'mgmt_temperature_hot_c', label: 'Above (°C)', value: r6.hot_threshold_c || 35, type: 'number', min: 25, max: 50, step: 1 },
            { id: 'mgmt_temperature_hot_increase', label: 'Increase %', value: r6.increase_percent || 25, type: 'number', min: 5, max: 75, step: 5 }
        ]);

        // Rule 7: Wind Speed
        const r7 = rules.wind_speed || {};
        html += mgmtBuildRuleRow('wind_speed', 'High Wind', 'Skip when wind exceeds threshold', r7.enabled, [
            { id: 'mgmt_wind_speed_mph', label: 'Max (mph)', value: r7.max_wind_speed_mph || 20, type: 'number', min: 5, max: 60, step: 1 },
            { id: 'mgmt_wind_speed_kmh', label: 'Max (km/h)', value: r7.max_wind_speed_kmh || 32, type: 'number', min: 8, max: 100, step: 1 }
        ]);

        // Rule 8: Humidity
        const r8 = rules.humidity || {};
        html += mgmtBuildRuleRow('humidity', 'High Humidity', 'Reduce watering when humidity is high', r8.enabled, [
            { id: 'mgmt_humidity_threshold', label: 'Above %', value: r8.high_humidity_threshold || 80, type: 'number', min: 50, max: 100, step: 5 },
            { id: 'mgmt_humidity_reduction', label: 'Reduce %', value: r8.reduction_percent || 20, type: 'number', min: 5, max: 75, step: 5 }
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
                '<input type="number" id="mgmt_seasonal_month_' + i + '" value="' + val + '" min="0" max="2" step="0.1" ' +
                'style="width:55px;padding:2px 4px;border:1px solid var(--border-input);border-radius:4px;font-size:11px;background:var(--bg-input);color:var(--text-primary);"></div>';
        }
        html += '<div style="background:var(--bg-tile);border:1px solid var(--border-light);border-radius:8px;padding:10px;margin-bottom:4px;">';
        html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">';
        html += '<div><div style="font-weight:600;font-size:13px;color:var(--text-primary);">Seasonal Adjustment</div>';
        html += '<div style="font-size:11px;color:var(--text-placeholder);">Monthly watering multiplier (0=off, 1=normal)</div></div>';
        html += '<label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;">';
        html += '<input type="checkbox" id="mgmt_rule_seasonal_adjustment" ' + (r9.enabled ? 'checked' : '') + '> Enabled</label>';
        html += '</div>';
        html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(95px,1fr));gap:4px;">' + seasonInputs + '</div>';
        html += '</div>';

        html += '</div>';

        // Save button
        html += '<div style="margin-top:12px;display:flex;gap:8px;">';
        html += '<button class="btn btn-primary" onclick="mgmtSaveWeatherRules()">Save Weather Rules</button>';
        html += '</div>';

        container.innerHTML = html;
        setupUnitConversions('mgmt_');
    } catch (e) {
        container.innerHTML = '<div style="color:var(--color-danger);">Failed to load weather rules: ' + esc(e.message) + '</div>';
    }
}

function mgmtBuildRuleRow(ruleId, name, description, enabled, fields) {
    let html = '<div style="background:var(--bg-tile);border:1px solid var(--border-light);border-radius:8px;padding:10px;">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
    html += '<div><div style="font-weight:600;font-size:13px;color:var(--text-primary);">' + esc(name) + '</div>';
    html += '<div style="font-size:11px;color:var(--text-placeholder);">' + esc(description) + '</div></div>';
    html += '<label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;">';
    html += '<input type="checkbox" id="mgmt_rule_' + ruleId + '" ' + (enabled ? 'checked' : '') + '> Enabled</label>';
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
            html += 'style="width:60px;padding:2px 4px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">';
            html += '</div>';
        }
        html += '</div>';
    }
    html += '</div>';
    return html;
}

async function mgmtSaveWeatherRules() {
    if (!currentCustomerId) return;
    try {
        const rules = {
            rain_detection: {
                enabled: document.getElementById('mgmt_rule_rain_detection').checked,
                resume_delay_hours: parseFloat(document.getElementById('mgmt_rain_detection_resume_delay_hours').value) || 2,
            },
            rain_forecast: {
                enabled: document.getElementById('mgmt_rule_rain_forecast').checked,
                probability_threshold: parseInt(document.getElementById('mgmt_rain_forecast_probability_threshold').value) || 60,
                lookahead_hours: 24,
            },
            precipitation_threshold: {
                enabled: document.getElementById('mgmt_rule_precipitation_threshold').checked,
                skip_if_rain_above_mm: parseFloat(document.getElementById('mgmt_precipitation_threshold_mm').value) || 6,
            },
            temperature_freeze: {
                enabled: document.getElementById('mgmt_rule_temperature_freeze').checked,
                freeze_threshold_f: parseInt(document.getElementById('mgmt_temperature_freeze_f').value) || 35,
                freeze_threshold_c: parseInt(document.getElementById('mgmt_temperature_freeze_c').value) || 2,
            },
            temperature_cool: {
                enabled: document.getElementById('mgmt_rule_temperature_cool').checked,
                cool_threshold_f: parseInt(document.getElementById('mgmt_temperature_cool_f').value) || 60,
                cool_threshold_c: parseInt(document.getElementById('mgmt_temperature_cool_c').value) || 15,
                reduction_percent: parseInt(document.getElementById('mgmt_temperature_cool_reduction').value) || 25,
            },
            temperature_hot: {
                enabled: document.getElementById('mgmt_rule_temperature_hot').checked,
                hot_threshold_f: parseInt(document.getElementById('mgmt_temperature_hot_f').value) || 95,
                hot_threshold_c: parseInt(document.getElementById('mgmt_temperature_hot_c').value) || 35,
                increase_percent: parseInt(document.getElementById('mgmt_temperature_hot_increase').value) || 25,
            },
            wind_speed: {
                enabled: document.getElementById('mgmt_rule_wind_speed').checked,
                max_wind_speed_mph: parseInt(document.getElementById('mgmt_wind_speed_mph').value) || 20,
                max_wind_speed_kmh: parseInt(document.getElementById('mgmt_wind_speed_kmh').value) || 32,
            },
            humidity: {
                enabled: document.getElementById('mgmt_rule_humidity').checked,
                high_humidity_threshold: parseInt(document.getElementById('mgmt_humidity_threshold').value) || 80,
                reduction_percent: parseInt(document.getElementById('mgmt_humidity_reduction').value) || 20,
            },
            seasonal_adjustment: {
                enabled: document.getElementById('mgmt_rule_seasonal_adjustment').checked,
                monthly_multipliers: {},
            },
        };
        for (let i = 1; i <= 12; i++) {
            rules.seasonal_adjustment.monthly_multipliers[String(i)] = parseFloat(document.getElementById('mgmt_seasonal_month_' + i).value) || 0;
        }
        await api('/customers/' + currentCustomerId + '/weather/rules', {
            method: 'PUT',
            body: JSON.stringify({ rules }),
        });
        showToast('Weather rules saved');
    } catch (e) {
        showToast('Failed to save weather rules: ' + e.message, 'error');
    }
}

async function mgmtEvaluateWeather() {
    if (!currentCustomerId) return;
    try {
        showToast('Evaluating weather rules...');
        const result = await api('/customers/' + currentCustomerId + '/weather/evaluate', { method: 'POST' });
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
        setTimeout(() => loadDetailWeather(currentCustomerId), 1000);
    } catch (e) {
        showToast('Evaluation failed: ' + e.message, 'error');
    }
}

// --- CSV Export ---
function mgmtExportHistoryCSV() {
    if (!currentCustomerId) return;
    const hours = document.getElementById('mgmtHistoryRange') ? document.getElementById('mgmtHistoryRange').value : '24';
    const url = BASE + '/customers/' + currentCustomerId + '/history/runs/csv?hours=' + hours;
    window.open(url, '_blank');
}

function mgmtExportWeatherLogCSV() {
    if (!currentCustomerId) return;
    const url = BASE + '/customers/' + currentCustomerId + '/weather/log/csv';
    window.open(url, '_blank');
}

async function mgmtClearWeatherLog() {
    if (!currentCustomerId) return;
    if (!confirm('Clear all weather log entries for this customer? This cannot be undone.')) return;
    try {
        const result = await api('/customers/' + currentCustomerId + '/weather/log', { method: 'DELETE' });
        if (result.success) {
            showToast(result.message || 'Weather log cleared');
            setTimeout(() => loadDetailWeather(currentCustomerId), 1000);
        } else {
            showToast(result.error || 'Failed to clear weather log', 'error');
        }
    } catch (e) { showToast(e.message, 'error'); }
}

async function mgmtClearRunHistory() {
    if (!currentCustomerId) return;
    if (!confirm('Clear all run history for this customer? This cannot be undone.')) return;
    try {
        const result = await api('/customers/' + currentCustomerId + '/history/runs', { method: 'DELETE' });
        if (result.success) {
            showToast(result.message || 'Run history cleared');
            setTimeout(() => loadDetailHistory(currentCustomerId), 1000);
        } else {
            showToast(result.error || 'Failed to clear run history', 'error');
        }
    } catch (e) { showToast(e.message, 'error'); }
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
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load status: ' + esc(e.message) + '</div>';
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
                    <span style="cursor:pointer;font-size:11px;color:var(--color-primary);margin-left:6px;"
                          onclick="event.stopPropagation();renameZone(\\'${z.entity_id}\\')">&#9998;</span>
                </div>
                <div class="tile-state ${isOn ? 'on' : ''}">${isOn ? 'Running' : 'Off'}</div>
                <div class="tile-actions" style="flex-wrap:wrap;">
                    ${isOn
                        ? '<button class="btn btn-danger btn-sm" onclick="stopZone(\\'' + id + '\\',\\'' + zId + '\\')">Stop</button>'
                        : '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + id + '\\',\\'' + zId + '\\', null)">Start</button>' +
                          '<span style="display:flex;align-items:center;gap:4px;margin-top:4px;"><input type="number" id="dur_' + zId + '" min="1" max="480" placeholder="min" style="width:60px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">' +
                          '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + id + '\\',\\'' + zId + '\\', document.getElementById(\\'dur_' + zId + '\\').value)">Timed</button></span>'
                    }
                </div>
            </div>`;
        }).join('') + '</div>';
    } catch (e) {
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load zones: ' + esc(e.message) + '</div>';
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
                <div class="tile-state">${esc(s.state)}${s.unit_of_measurement ? ' ' + esc(s.unit_of_measurement) : ''}${wifiSignalBadge(s)}</div>
            </div>`).join('') + '</div>';
    } catch (e) {
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load sensors: ' + esc(e.message) + '</div>';
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
                // Filter out redundant entities (valve_N duplicates, generic repeat)
                const eid = (e.entity_id || '').toLowerCase();
                if (/valve_\\d+/.test(eid)) continue;
                if (e.domain === 'number' && /repeat/.test(eid) && !/repeat_cycle/.test(eid)) continue;
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
                html += '<div style="margin-bottom:16px;"><div style="font-size:13px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">' + esc(label) + '</div>';
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
        controlsEl.innerHTML = '<div style="color:var(--color-danger);">Failed to load controls: ' + esc(e.message) + '</div>';
        scheduleEl.innerHTML = '<div style="color:var(--color-danger);">Failed to load schedule: ' + esc(e.message) + '</div>';
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
            'padding:12px 16px;border-radius:8px;background:' + (isOn ? 'var(--bg-active-tile)' : 'var(--bg-inactive-tile)') + ';">' +
            '<div><div style="font-size:15px;font-weight:600;color:' + (isOn ? 'var(--color-success)' : 'var(--color-danger)') + ';">' +
            'Schedule ' + (isOn ? 'Enabled' : 'Disabled') + '</div>' +
            '<div style="font-size:12px;color:var(--text-muted);">Master schedule on/off</div></div>' +
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
                '<input type="text" id="' + inputId + '" value="' + esc(st.state) + '" placeholder="HH:MM" style="width:100px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">' +
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
            '<th>Schedule Enable</th><th>Run Duration</th></tr></thead><tbody>';
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
                    html += '<td><select id="' + selId + '" style="padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);" ' +
                        'onchange="setEntityValue(\\'' + custId + '\\',\\'' + modeEid +
                        '\\',\\'select\\',{option:document.getElementById(\\'' + selId + '\\').value})">' +
                        optionsHtml + '</select></td>';
                } else {
                    html += '<td style="color:var(--text-disabled);">-</td>';
                }
            }
            if (enable) {
                const isOn = enable.state === 'on';
                html += '<td><button class="btn ' + (isOn ? 'btn-primary' : 'btn-secondary') + ' btn-sm" ' +
                    'onclick="setEntityValue(\\'' + custId + '\\',\\'' + enable.entity_id + '\\',\\'switch\\',' +
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
                    'style="width:70px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);"> ' +
                    esc(unit) + ' ' +
                    '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid +
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
                '<input type="number" id="num_' + eid + '" value="' + esc(state) + '" min="' + min + '" max="' + max + '" step="' + step + '" style="width:80px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">' +
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
                '<select id="sel_' + eid + '" style="padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">' + optionsHtml + '</select>' +
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
                '<input type="text" id="txt_' + eid + '" value="' + esc(state) + '" style="width:120px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid + '\\',\\'text\\',{value:document.getElementById(\\'txt_' + eid + '\\').value})">Set</button>' +
            '</div></div>';
    }

    // Fallback for unknown domains — read-only display
    return '<div class="tile">' +
        '<div class="tile-name">' + name + '</div>' +
        '<div class="tile-state">' + esc(state) + '</div>' +
        '<div style="font-size:11px;color:var(--text-disabled);margin-top:4px;">' + esc(domain) + '</div>' +
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
        const hours = document.getElementById('mgmtHistoryRange') ? document.getElementById('mgmtHistoryRange').value : '24';
        const data = await api('/customers/' + id + '/history/runs?hours=' + hours);
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
            '<table style="width:100%;font-size:13px;border-collapse:collapse;"><thead><tr style="text-align:left;border-bottom:2px solid var(--border-light);color:var(--text-muted);"><th style="padding:6px;">Zone</th><th style="padding:6px;">State</th><th style="padding:6px;">Time</th><th style="padding:6px;">Duration</th><th style="padding:6px;">Weather</th></tr></thead><tbody>' +
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

// --- Mode Switch ---
async function switchToHomeowner() {
    if (!confirm('Switch to Homeowner mode? The management dashboard will no longer be available until you switch back.')) return;
    try {
        await api('/mode', { method: 'PUT', body: JSON.stringify({ mode: 'homeowner' }) });
        showToast('Switching to homeowner mode...');
        setTimeout(() => window.location.reload(), 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Help Modal ---
const HELP_CONTENT = `
<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:0 0 8px 0;">Dashboard Overview</h4>
<p style="margin-bottom:10px;">The Management Dashboard lets you monitor and control irrigation systems across multiple properties from a single interface. Each property is a homeowner who has shared their connection key with you.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Adding Properties</h4>
<p style="margin-bottom:10px;">To add a property, click <strong>+ Add Property</strong> and paste the connection key provided by the homeowner. The key is generated from their Flux Open Home Irrigation Control add-on's Configuration page.</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;">The key is automatically decoded to preview the property name, address, and connection type</li>
<li style="margin-bottom:4px;">You can optionally set a custom display name and notes</li>
<li style="margin-bottom:4px;">Click <strong>Connect</strong> to add the property to your dashboard</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Connection keys contain the URL, API key, and property details. You don't need to configure anything else.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Property Cards</h4>
<p style="margin-bottom:10px;">Each property is displayed as a card showing its current status:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>🟢 Online</strong> — System is reachable and responding</li>
<li style="margin-bottom:4px;"><strong>🔴 Offline</strong> — System is unreachable (check network or Home Assistant)</li>
<li style="margin-bottom:4px;"><strong>🟡 Revoked</strong> — Homeowner has revoked your access</li>
<li style="margin-bottom:4px;"><strong>Zone count</strong> — Number of irrigation zones configured</li>
<li style="margin-bottom:4px;"><strong>Running / Idle / Paused</strong> — Current system state</li>
<li style="margin-bottom:4px;"><strong>WiFi signal</strong> — Connection quality indicator (if available)</li>
</ul>
<p style="margin-bottom:10px;">Click any property card to open the detail view for full control.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Search &amp; Filtering</h4>
<p style="margin-bottom:10px;">Use the search bar and filters to quickly find properties:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Search</strong> — Filter by name, address, phone number, or notes</li>
<li style="margin-bottom:4px;"><strong>State / City</strong> — Filter by location</li>
<li style="margin-bottom:4px;"><strong>Zone count</strong> — Filter by number of zones</li>
<li style="margin-bottom:4px;"><strong>Status</strong> — Filter by online/offline/revoked</li>
<li style="margin-bottom:4px;"><strong>System State</strong> — Filter by running/idle/paused</li>
<li style="margin-bottom:4px;"><strong>Sort</strong> — Order by name, city, state, zones, status, or last seen</li>
</ul>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Property Detail View</h4>
<p style="margin-bottom:10px;">Click a property card to see its full details including zone controls, sensors, schedule, weather, and run history. Use the <strong>← Back</strong> button to return to the property list.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Remote Zone Control</h4>
<p style="margin-bottom:10px;">From the detail view, you can remotely control any irrigation zone:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Start</strong> — Turn on a zone (optionally set a timed run in minutes)</li>
<li style="margin-bottom:4px;"><strong>Stop</strong> — Turn off a specific zone</li>
<li style="margin-bottom:4px;"><strong>🛑 Stop All Zones</strong> — Emergency stop for all zones at once</li>
<li style="margin-bottom:4px;"><strong>⏸ Pause / ▶ Resume</strong> — Pause or resume the entire irrigation system</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 When the system is paused, any zone that turns on (even from an ESPHome schedule) will be immediately shut off.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Schedule Management</h4>
<p style="margin-bottom:10px;">View and manage watering schedules for each property:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Days</strong> — Select which days of the week to water</li>
<li style="margin-bottom:4px;"><strong>Start Times</strong> — Set one or more daily start times</li>
<li style="margin-bottom:4px;"><strong>Zone Durations</strong> — Configure how long each zone runs (in minutes)</li>
<li style="margin-bottom:4px;"><strong>Enable/Disable</strong> — Toggle the schedule on or off without deleting it</li>
</ul>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Weather Rules</h4>
<p style="margin-bottom:10px;">If the homeowner has configured weather integration, you can view and manage weather-based watering adjustments:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Rain Skip</strong> — Skip watering when rain is detected or forecasted</li>
<li style="margin-bottom:4px;"><strong>Wind Delay</strong> — Delay watering during high winds</li>
<li style="margin-bottom:4px;"><strong>Temperature Adjustments</strong> — Increase or decrease watering based on temperature</li>
<li style="margin-bottom:4px;"><strong>Watering Multiplier</strong> — See the current weather-adjusted multiplier applied to run times</li>
</ul>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Run History</h4>
<p style="margin-bottom:10px;">View a detailed log of all irrigation activity for each property:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;">Each entry shows the zone, start/stop time, duration, and source (API, schedule, manual, etc.)</li>
<li style="margin-bottom:4px;">Weather conditions at the time of each run are captured</li>
<li style="margin-bottom:4px;"><strong>CSV Export</strong> — Download the run history as a spreadsheet</li>
<li style="margin-bottom:4px;"><strong>Clear History</strong> — Remove old entries (this cannot be undone)</li>
</ul>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Notes &amp; Zone Aliases</h4>
<p style="margin-bottom:10px;">Customize how properties and zones appear in your dashboard:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Notes</strong> — Add private notes to any property (e.g., "new sod in backyard", "drip system needs repair")</li>
<li style="margin-bottom:4px;"><strong>Zone Aliases</strong> — Rename zones to friendly names (e.g., "Front Lawn", "Garden Beds") that override the default hardware names</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Notes and zone aliases are stored locally in your management add-on — the homeowner won't see them.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Updating Connection Keys</h4>
<p style="margin-bottom:10px;">If a homeowner regenerates their connection key (e.g., after revoking access or changing their setup), you'll need to update the key for that property:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;">Click the <strong>🔑 Update Key</strong> button in the property detail view</li>
<li style="margin-bottom:4px;">Paste the new connection key from the homeowner</li>
<li style="margin-bottom:4px;">Your notes and zone aliases are preserved when updating a key</li>
</ul>
`;

function showHelp() {
    document.getElementById('helpContent').innerHTML = HELP_CONTENT;
    document.getElementById('helpModal').style.display = 'flex';
}
function closeHelpModal() {
    document.getElementById('helpModal').style.display = 'none';
}
document.getElementById('helpModal').addEventListener('click', function(e) {
    if (e.target === this) closeHelpModal();
});

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    // Fix docs link for ingress — page is served at /admin, strip it to get ingress base
    const ingressBase = window.location.pathname.replace(/\\/admin\\/?$/, '');
    document.getElementById('docsLink').href = ingressBase + '/api/docs';
    loadCustomers();
    listRefreshTimer = setInterval(loadCustomers, 60000);
    // Close modals on backdrop click or Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (document.getElementById('helpModal').style.display === 'flex') closeHelpModal();
            else if (document.getElementById('keyModal').style.display === 'flex') closeKeyModal();
            else if (document.getElementById('notesModal').style.display === 'flex') closeNotesModal();
        }
    });
    document.getElementById('notesModal').addEventListener('click', function(e) {
        if (e.target === this) closeNotesModal();
    });
    document.getElementById('keyModal').addEventListener('click', function(e) {
        if (e.target === this) closeKeyModal();
    });
});
</script>
</body>
</html>
"""
