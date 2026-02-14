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
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js" crossorigin=""></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js" crossorigin=""></script>
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
    --bg-hover: #f5f6f8;
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
    --color-info: #2196F3;
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
    --bg-hover: #1e2a45;
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
    --color-info: #5dade2;
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
.card-body > *:last-child { margin-bottom: 0; }
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
.tile-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; }
.tile { background: var(--bg-tile); border-radius: 8px; padding: 14px; border: 1px solid var(--border-light); min-height: 130px; position: relative; display:flex; flex-direction:column; }
#cardBody_status .tile { min-height: auto; flex-direction:row; align-items:center; gap:12px; }
#cardBody_status .tile .status-tile-text { flex:1; min-width:0; }
#cardBody_status .tile .status-tile-text .tile-name { padding-right:0; margin-bottom:2px; }
#cardBody_status .tile .status-tile-text .tile-state { margin-bottom:0; }
.status-tile-icon { flex-shrink:0; color:var(--text-muted); opacity:0.4; }
.status-tile-icon.icon-on { color:var(--color-success); opacity:0.75; }
.status-tile-icon.icon-warn { color:var(--color-warning,#f39c12); opacity:0.75; }
.status-tile-icon.icon-off { color:var(--color-danger); opacity:0.7; }
.tile.active { background: var(--bg-active-tile); border-color: var(--border-active); }
.tile-name { font-weight: 600; font-size: 14px; margin-bottom: 6px; padding-right: 70px; }
.tile-state { font-size: 13px; color: var(--text-muted); margin-bottom: 8px; }
.tile-state.on { color: var(--color-success); font-weight: 500; }
.tile-actions { display: flex; gap: 6px; margin-top:auto; }
.tile-sprinkler-icon { position:absolute; bottom:14px; right:6px; display:flex; align-items:flex-end; gap:3px; color:var(--text-muted); pointer-events:none; }
.tile-sprinkler-icon svg { opacity:0.45; transition:opacity 0.3s ease; }
.tile.active .tile-sprinkler-icon svg { color:var(--color-success); opacity:0.85; animation:sprinklerPulse 2s ease-in-out infinite; }
@keyframes sprinklerPulse { 0%,100%{ opacity:0.5; transform:scale(1); } 50%{ opacity:1; transform:scale(1.1); } }
.tile-sprinkler-icon.pump-valve svg { opacity:0.45; }
.tile.active .tile-sprinkler-icon.pump-valve svg { color:var(--color-info); opacity:0.85; animation:pumpPulse 2s ease-in-out infinite; }
@keyframes pumpPulse { 0%,100%{ opacity:0.5; transform:scale(1); } 50%{ opacity:1; transform:scale(1.1); } }

/* Card Row — side-by-side cards */
.card-row { display: flex; gap: 20px; margin-bottom: 20px; align-items: stretch; }
.card-row > .card { flex: 1; min-width: 0; margin-bottom: 0; }
.card-row > .card.card-collapsed { align-self: flex-start; }
@media (max-width: 768px) { .card-row { flex-direction: column; } .card-row > .card { margin-bottom: 20px; width: 100%; } }

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

/* Water-themed spinner */
.water-spinner {
    width: 44px; height: 44px; border-radius: 50%;
    border: 3px solid rgba(59, 130, 246, 0.15);
    border-top: 3px solid rgba(59, 130, 246, 0.8);
    border-right: 3px solid rgba(59, 130, 246, 0.4);
    animation: waterSpin 1s cubic-bezier(0.4, 0, 0.2, 1) infinite;
    box-shadow: 0 0 16px rgba(59, 130, 246, 0.15), inset 0 0 10px rgba(59, 130, 246, 0.05);
}
@keyframes waterSpin { to { transform: rotate(360deg); } }

/* Dark mode form inputs */
body.dark-mode input, body.dark-mode select, body.dark-mode textarea {
    background: var(--bg-input); color: var(--text-primary); border-color: var(--border-input);
}

/* Settings gear & notification bell */
.notif-bell-btn { position: relative; }
.notif-bell-btn .notif-badge {
    position: absolute; top: -4px; right: -4px;
    background: #e74c3c; color: white;
    font-size: 10px; font-weight: 700;
    min-width: 16px; height: 16px;
    border-radius: 8px; display: flex;
    align-items: center; justify-content: center;
    padding: 0 4px; line-height: 1;
}
/* Notification event list */
.notif-item { padding: 12px 20px; border-bottom: 1px solid var(--border-light); }
.notif-item.unread { background: rgba(26,122,76,0.06); padding: 12px 20px; }
/* Toggle switch */
.toggle-switch { position: relative; display: inline-block; width: 40px; height: 22px; flex-shrink: 0; }
.toggle-switch input { opacity: 0; width: 0; height: 0; }
.toggle-slider {
    position: absolute; inset: 0; background: var(--border-light);
    border-radius: 22px; cursor: pointer; transition: 0.2s;
}
.toggle-slider::before {
    content: ''; position: absolute; height: 16px; width: 16px;
    left: 3px; bottom: 3px; background: white;
    border-radius: 50%; transition: 0.2s;
}
.toggle-switch input:checked + .toggle-slider { background: var(--color-primary); }
.toggle-switch input:checked + .toggle-slider::before { transform: translateX(18px); }

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
    .zone-settings-table { table-layout: fixed; }
    .zone-settings-table th, .zone-settings-table td { padding: 6px 4px; font-size: 12px; }
    .zone-settings-table td[style*="white-space"] { white-space: normal !important; }
    .zone-settings-table input[type="number"] { width: 50px !important; padding: 3px 2px !important; font-size: 11px !important; }
}
.leaflet-tile-pane.dark-tiles { filter: brightness(0.6) invert(1) contrast(3) hue-rotate(200deg) saturate(0.3) brightness(0.7); }
.map-lock-btn { position:absolute; top:10px; right:10px; z-index:1000; background:#fff; border:none; border-radius:4px; box-shadow:0 1px 4px rgba(0,0,0,.3); cursor:pointer; width:30px; height:30px; display:flex; align-items:center; justify-content:center; font-size:14px; }
.map-lock-btn:hover { background:#f5f5f5; }

/* === DATA NERD VIEW === */
#dataNerdOverlay { position:fixed;inset:0;z-index:10000;display:flex;flex-direction:column;background:rgba(245,246,250,0.97);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);transition:opacity 0.3s ease; }
body.dark-mode #dataNerdOverlay { background:rgba(18,18,35,0.97); }
#dnToolbar { display:flex;align-items:center;gap:10px;padding:10px 16px;background:rgba(255,255,255,0.95);border-bottom:1px solid rgba(0,0,0,0.08);flex-shrink:0; }
body.dark-mode #dnToolbar { background:rgba(15,25,50,0.95);border-bottom:1px solid rgba(46,204,113,0.15); }
#dnContent { flex:1;overflow-y:auto;padding:16px; }
#dnGrid { display:grid;grid-template-columns:repeat(2,1fr);gap:16px;max-width:1600px;margin:0 auto; }
@media(max-width:1024px){ #dnGrid { grid-template-columns:1fr; } }
@media(min-width:1400px){ #dnGrid { grid-template-columns:repeat(3,1fr); } #dnGrid .dn-wide { grid-column:span 2; } }
.dn-full { grid-column:1/-1; }
.dn-panel { background:rgba(255,255,255,0.9);border:1px solid rgba(0,0,0,0.08);border-radius:12px;padding:16px;backdrop-filter:blur(10px);transition:box-shadow 0.3s ease; }
.dn-panel:hover { box-shadow:0 0 20px rgba(46,204,113,0.1); }
body.dark-mode .dn-panel { background:rgba(22,33,62,0.8);border-color:rgba(46,204,113,0.15); }
body.dark-mode .dn-panel:hover { box-shadow:0 0 24px rgba(46,204,113,0.15); }
.dn-panel-title { font-size:13px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center; }
.dn-chart-wrap { position:relative;width:100%;height:280px; }
.dn-chart-wrap canvas { width:100%!important;height:100%!important; }
.dn-range-group { display:flex;border-radius:6px;overflow:hidden;border:1px solid rgba(0,0,0,0.12); }
body.dark-mode .dn-range-group { border-color:rgba(255,255,255,0.15); }
.dn-range-btn { padding:5px 14px;background:rgba(0,0,0,0.04);border:none;color:var(--text-secondary);font-size:12px;font-weight:600;cursor:pointer;transition:all 0.15s; }
body.dark-mode .dn-range-btn { background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.7); }
.dn-range-btn.active { background:rgba(46,204,113,0.2);color:#1a7a4c; }
body.dark-mode .dn-range-btn.active { background:rgba(46,204,113,0.3);color:#2ecc71; }
.dn-range-btn:hover:not(.active) { background:rgba(0,0,0,0.08); }
body.dark-mode .dn-range-btn:hover:not(.active) { background:rgba(255,255,255,0.12); }
.dn-toolbar-btn { padding:6px 14px;border-radius:6px;border:1px solid rgba(0,0,0,0.12);background:rgba(0,0,0,0.03);color:var(--text-secondary);font-size:12px;font-weight:600;cursor:pointer;transition:all 0.15s; }
body.dark-mode .dn-toolbar-btn { border-color:rgba(255,255,255,0.15);background:rgba(255,255,255,0.06);color:rgba(255,255,255,0.7); }
.dn-toolbar-btn:hover { background:rgba(0,0,0,0.08); }
body.dark-mode .dn-toolbar-btn:hover { background:rgba(255,255,255,0.12); }
.dn-summary-row { display:grid;grid-template-columns:repeat(4,1fr);gap:12px; }
@media(max-width:768px){ .dn-summary-row { grid-template-columns:repeat(2,1fr); } }
.dn-stat-card { background:linear-gradient(135deg,rgba(46,204,113,0.08),rgba(52,152,219,0.08));border:1px solid rgba(46,204,113,0.15);border-radius:10px;padding:14px;text-align:center;backdrop-filter:blur(8px); }
body.dark-mode .dn-stat-card { background:linear-gradient(135deg,rgba(46,204,113,0.12),rgba(52,152,219,0.12));border-color:rgba(46,204,113,0.2); }
.dn-stat-val { font-size:28px;font-weight:700;color:var(--color-primary);line-height:1.2; }
body.dark-mode .dn-stat-val { color:#2ecc71; }
.dn-stat-label { font-size:11px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-top:2px; }
.dn-stat-sub { font-size:11px;color:var(--text-hint);margin-top:4px; }
.dn-heatmap { display:flex;flex-direction:column;gap:2px; }
.dn-heatmap-row { display:flex;align-items:center;gap:2px; }
.dn-heatmap-label { width:36px;font-size:10px;font-weight:600;color:var(--text-muted);text-align:right;padding-right:4px;flex-shrink:0; }
.dn-heatmap-cell { flex:1;height:22px;border-radius:3px;cursor:default;transition:transform 0.15s;min-width:0; }
.dn-heatmap-cell:hover { transform:scale(1.3);z-index:1; }
.dn-heatmap-hours { display:flex;gap:2px;margin-left:40px; }
.dn-heatmap-hours span { flex:1;font-size:9px;color:var(--text-hint);text-align:center; }
.dn-loading { display:flex;align-items:center;justify-content:center;height:200px;color:var(--text-muted);font-size:14px; }
.dn-tab-group { display:flex;gap:4px; }
.dn-tab-btn { padding:3px 10px;border-radius:4px;border:1px solid transparent;background:none;color:var(--text-muted);font-size:11px;font-weight:600;cursor:pointer; }
.dn-tab-btn.active { background:rgba(46,204,113,0.15);color:var(--color-primary);border-color:rgba(46,204,113,0.3); }
body.dark-mode .dn-tab-btn.active { color:#2ecc71; }
.dn-pill { display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600;margin:2px; }
.dn-nerd-btn { padding:6px 14px;border-radius:6px;border:1px solid rgba(46,204,113,0.3);background:linear-gradient(135deg,rgba(46,204,113,0.1),rgba(52,152,219,0.1));color:var(--color-primary);font-size:13px;font-weight:700;cursor:pointer;transition:all 0.2s;letter-spacing:0.3px; }
body.dark-mode .dn-nerd-btn { color:#2ecc71;border-color:rgba(46,204,113,0.4);background:linear-gradient(135deg,rgba(46,204,113,0.15),rgba(52,152,219,0.15)); }
.dn-nerd-btn:hover { background:linear-gradient(135deg,rgba(46,204,113,0.2),rgba(52,152,219,0.2));box-shadow:0 0 12px rgba(46,204,113,0.15); }
</style>
</head>
<body>
<script>(function(){if(localStorage.getItem('flux_dark_mode_homeowner')==='true')document.body.classList.add('dark-mode');})()</script>

<div class="header">
    <div class="header-left">
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAARYAAABaCAYAAAB9oHnsAAAACXBIWXMAAC4jAAAuIwF4pT92AAAQnklEQVR4nO2d0XHjOBKGf1xdqaQnOwNrI7AuAnMjsDYCcyIYTQSjiWA8EZiOYDURDB3ByhGcnIH9JJVe+h7QvKEpgARIAgRlfFUslymKhEjgJ9BodAsiQiQSifTJv4cuwEdgMp1dAkgBXALIjof9btACKeAyrvjf/HjY5wMWJ6JACLEAsOR/dwA2RPQ6XIn0CFWPhStZBuDWc3l+AlgfD/tt3UGT6SwFsMbvhrqqO35oJtPZFsA1//sGIGn6jT7h570FcFXa/dfxsN+0PN8cUkhz3rULUUzHghBC1x7fAKyIKPNdpib+pdmfwb+ogK9ZW5kn09kCwANkI7gA8HkynQUrLJPpLMFvUQFkmZfqowdjgfeiAkhhaMscwFcAv3jb8nMLnsl0lk6mMypt+ZDlYVHJoW6PFwAehBCh1SetsAwhKgXVCl7l0nBfpBt93tMLAHno4jKZzpaQL62QuMf7F5OKjIdJwaATliF5GboAEScELS5crmzocpQRQmQA7gwOvQCQhyQuoQnLM8IbJkTs2UI+yyoXADK26QQDi0oOWb4qgxhHLUSl4AKy5xLEvbWZFXoEsDoe9kFaoSPhcDzsX9nAnuO0sV5D9lySEOpSg6g8o5utqRUNovIGvc3lGrLnkgw9W2TaY3k7HvZpCBUhMg541iuBbAhVCnEZ9O1qICrexc9AVBIiWgJ40hxzjQCGdKbCEszUaGQ8hCwuIxaVoi0uoR5uAsAtn2swQrOxRM6MEMUlUFFZo96mkpZEBTzUSaC+rwBwJ4QYzA0jCkvEOQbikvkqC4tYjrBEJYX0+9HxiYhO/LsMxOU7n9s7UVgiXmBxSTUf306ms8x1GRpE5Q2AdzsiN/w635lPdZ613ItJar7/IISo+9wJUVgi3uAlAp80H9+5FJeSqKiczQZZZtFVVApYXHT3FQA2vn1corBEvHI87DN4FpdzFpUCPvaL5uPCgc6bLSsKS8Q7PsXlI4hKARHdQ/qbqfAqLlFYIoNgIC7rrtcYqah86bJamYhS6MXlGr9XnDslCktkMFhcvmk+/sreu60IVFQWkIsKdTxyr6MrK+h9XK59+LhEYYkMyvGwX0P/hn3oIC51q4KXA4lKDvWMFCBFJe3jWqVpaJ243Akh+hAwLVFYIoNzPOxT9CgubKPROZt98h0dz6eoFLC4LKH3cfns0sclCkskCPoSFwNRyWzL1oUhRKWAiHaod6B7cCUuUVgiwWAgLrUhNaKonMI+LnXXuHfh4xKFJRIULC4/NR9nukBRUVT08HIA3QyckyBRUVgiIZJCHyjqJApdgKJSt3QAAJ59iUoBT2HrZuAuIL1ze/NxicISCQ5er5NALy7/lANeY2Sigvq1Pc4gojX0Q80r9OhAF4UlEiQN4mLCjwFFRTfN/QwZU2WwgGncU3IeJMo0NOXCcRqEzHcliIQPh7hMUN9YVTz6zjU1BlEpsYS+rLdCiKzrUM1UWC4A3HS5UAM3k+lsG1ISr0gYlMSlmlBNxyMbgL0xMlEBEb1yKAXdPb0TQux46NSKkIZCMTp/RAkPi3aGh2fuSnLK2ESlwMCB7msXH5eQhKVVOs9IZCgMROUFAYpKgcsgUSEIywuk9T4OgyJjo2490huAZaiiUuAqSJSpjeXpeNgntiePRPqAbSymNr57HzmLLCPqBw0RZUIIQB3O4f8OdLxEwIgQeiyRiBZ2hrMZJjsPzn1OolLADnR1QaKsHOiisESCpSFNRx3OgnOfo6gU9BkkKgpLJEgaROUF0smr2FT0Hj/3nEWlgMWlc5CoKCyR4DBIKLY4HvZJscFD/NyPIColEtQHicqaThCFJRIUbbIUug7ObZulcOwY+LjcNfm4RGFxj2p2wmuOFwMSxT7vDaVL6lMDcWkVipGnWq2zFI6drkGiorA4RuOfM/ddjgZU1n6v/hcc/HoDfZbCxilkFhddbp3PLePn1nmEt0rTMRa4F1b3+x90Pi6mfiyRbrzg/ZqM68l0duk7nWcNiWKftx5LKaK+at2KkagUHA/7e+75qIYuD5PpDJYLXnea/UaiMkR6Uwc8Qj8U3EDxoozC4gfVYq8lPK9rUTGZzuZQe496ERYXaTqOh306mc6AHsSFncdWlfI1iooQoni+tlPlY+NKCDGvOs/FoZAfVGPw1HchNKSKfc/Hw37n+sIuc//0GfmfiBYA/oKMwPaHoaj8jfMXlYKToXQUFj+ohOWGXdUHgxu2Km5J5unaORwmFOtZXDZEtDZ0a3easycw3lQzYlFYPMD2AVUFX3suSpUV1G/VzOVFfWYpbBCXwh7TG2zMNIkbcy6sVTujsPhjrdh3M5nOvEY6K+AGpbr2owejcg6/qU91KUeVwbk70ltA6sB5g8wzreydReOtJ46H/W4ynams698n01nuM2wE9xgynPZW3qAWmz6vnUEfaiB1cR8aQlwW4uIjl/MT5DAplNnAtrw2OQRGYfHLCnI2qNqgfVXssr+IqnGvXfZWDNJ0OHM0C0BcnogocXTu4IhDIY9wo00VH7nokp9Qsm2oYps8HQ97Z0bHEHL/GKQVcfkMPpJBNwqLb/it/EPxUZEvx8lQhBvMFnrbhrOYwyGISoGBuGxYgPtm7MMfK6KwDACnptDNVHyfTGd5X1PRk+nscjKdrQH8gx48W1tcP0MgolLAv1W3yO4KsufyUYywTjgXYUmGLoAtDdOgNwB+scC06klMprM5C8oO+kV0rmZhijJkCExUCtgBMIFaXK7xgcRFCLEUQrwKIUgIsesjj/O5GG9vJtNZOrakZ+x6/grgs+aQG8jf9gJpG9kA2Oq8YrmXs4B8GzfFiHUtKmvoReWL7bPi35Z0KpSaHMCtYn8hLs7j5w6JEGIO6SVccAXN+h+r8xLRyU7Oh1smmGDaXMF+aT5+gXn+mb54hZxNad1AuVeSwd4F/BnSb8LWIesJwNLh8CeFOjAz0CKhWEPPxzU/j4e9ca+x5M5f5T8hxmzhRZKq9vQnEeVtz3suPZaCKwzj9ThHhxgrx8N+w8bVe6jfnjps0o4C7KfioWeXava3ERXdSmVf2A6HlPUgRFFxybnYWIbGtoGfcDzsd/xm/BP6OK5teYNcQDcfcLjYNvXph7BznBs6YalW7JDGmCGVpeClrxMdD/uch51/QE5Ldzn3T8ioavPjYe/U+a2B1vmUj4d9Dn38VR+EWN+CRzcUWkF2y28gRSb1VaAmjof9djKdfYIsXwjL0l/gwAeEDbQrACseDiSQ3ew5b9UhX/EyyCH9VfIBhaRwBptD2p+yjudLIOug795LzsIWsURpvI1EIu3gwNsn0/tEJPyXphlXxttoY4lEIr0ThSUSifROa2Fhx5rIByM+94gJRsIihLgUQqyEEFt2+yUA/y25AGem0ciFEElxDoNtJ4TIhRD3Jgmp+VjTc+u2pHLOdeXzzOR3lr7/7vw231Wcq1qW3PB7J/fc4poJP9/XynMnvt+pxbmqz8f4u5XzGN+HHuqD9twRPY3Cwg1tB+A71P4aV5AOTL9MBcCCK8iZqc8AdlyhhvZruDuTlA618MtkA2nYu4N6Bu4GMrdM2/Ul65bFS1t+L+KJWmHhN8ovmE/rfgaQO2r8F5DWdlfntyEb+PpO4fubw9wL+AryuaSWl7qyFWl2mf9IMWVHiVZY+AHq1nvUcQ23De8a6qj3PrniacVzJYe9N/EFgPsWPRfb+DODxAiO2KF0kOM3Vqb46I33byGHRwmkc1i1Et4KIVKL9JN/1ny2hOz6lntNN0KIxGCe/RH2Ime6puOrECIzTAcxGlgwVaLyBF5dDen4luB0Dc8FpHNcYnHJW6FIeKUp2xzNq7ab+AK7ZGzR87YNRHSyQb4VqLJtASw0x2eK43eaY5PqsarjKt9ZQD7g8vc2iuPyyjHrpnMbXHut+G3Flht83+q3Wpal8fq291xxnwnAyuK5EICl5vjq8ym2e8PfcW/7HBTHJl3rRJv64vKaHct7Ujf6uE+6oZDKRX1JmhWaRJTidH3RVUuDnur8W5zGDE36OHdHbnjIeBbwb6na036QJsUD6ZOG296T1KBslybHRcJAJyzV7uYjNXdV14p9fQYmziv/h7BOCACyAIzJfaF6XrVBoEkOR6sLJeeW170wMPyqRC8SKKYOco3GUq5g1VWoc8vy1BFKPIvqb7zA8BkNXfFk8EIBTsWnzQulySgbjbYjwlRYTBu1S0OX09QYFmwgwxGU+dzXsG9gksr/ueH3qvWjTc/iWjf1zPs7x7zxhKoeDBn2YRBOhEXVQAzfWq6pvrF6i4HSghVOgzBnA5Tj3Egt94eIalj84WaWVNPNXewFTm4gj7+rzlomviyJhb9JZiqgRLTj834v7b4WQqx0hk5HzA1/39xxOdryhPf2vDshxLr8HNh+VZ3W/gm7EJ5lUlOnPCJat7zGmNhp9neyG/Yd83aLFg+8oXGo/GQAs8xyNzD3e8hhEYibiO5Z8MplWwshNh57eFfQp/YYAzlOg1aleG+zqvZUn9CynjE28XPXjUeMHH5Jqj5aoIMjaijBtG0bx7eAhmflIDmFg9jZTEF7YI33Ht4rvG/QaeX4DOH2wCLMGOOxPIbSReWZsGq61NuPsEixRzZ4b6/6/9Qz/y33Zl7I3Js7MiB991jmPZ+vzBukJ62NDeMJ5jMbO9sCMWucLjnIhBALInJttHuBmdF4jmFTaGgholcORVFO2raC/F1p5fCsh0s+wn/uqQ9HKMKiS3ex421LRG3Ge7nr3g03jBXed+evcNqld8HO5PdxDypIYWHu8V5Yrrm3UrWPZT1cK6MOsVwjZpwICxHlVWOO6SKxthBR4urcPiCiTNEQvtoGhfqosAGxOkNUXVlv4v0dCQRTG8vc8LhzcW1vQ6rYl3kuQ1eqjm6J4ffmPVy7aYib9XCNiCdMhSVtOoAd66rTwjvL8owWfpt+q+zuusTfN1Wb0MJwHVRa+d86kyMPdXVOj88jH77Mhy6ADlce46aZEO8MKphqLcfOukTj5h7DegR3ReWaX7tGh+03VQFta7TW9Vp8Oh264KptfF8PrDX7d11OqjPebnBaWTZCiKVqpoNvWtU4+Dbyt4w1bMhNoU4ANQZyyNm38gzXSgihNJ5z4CVVo2/rWJXhvTczIOtR1vJ8Q5BD3VN94PuVeyxLHXPInqauV513OblOWDJIJXsXtQ3AVghxj99eqgkXTuUFue5SsLHCxu8uLueDwcK4wfuXxAWAv4UQPyCfew7plZlA9maqCw5b+5rw9R8r1291rgHJoHf4/FrzWUiYrmrXUxNZShVFznTb2kSs6jEaVt6hzMrIWTiNCLY2KMcc6shqnX6roiy54feM7zmkAV5Z9jb3r+H5nNxLvn5S2i673Ice6oPRPa5cM+vhukNu2mdoummNtyQd0R51n9fwjDCiuw0Gq/164GK0guRQN8Hp6m0TPlHH4S8RvRJRXtrGuDJ4hfGGSvjW9RkCDbNCJENOfoJ5JXuCVLsxVoZeYWEeZeUiGXJyAfPyvwH4i8ZlC3FGSZzH9vy/UE8OpY3TzVxZFpC9F53APEO+raKovGe0Uc+IaEdEC8gXi66BvECulZpTO8/os4V7XsX9C3mm8A2ybf9BPYb8EDwmNP+CnPcuTz1vo5icP+xuUPZ52FH0hDWGZ4Tmw5bihFfSBMjvirWwRCKRSBP/A3Jkqd9jS9KSAAAAAElFTkSuQmCC" alt="Flux Open Home" class="header-logo">
        <h1>Irrigation</h1>
    </div>
    <div class="header-actions">
        <div class="nav-tabs">
            <a class="nav-tab" href="?view=config">Configuration</a>
        </div>
        <button class="dark-toggle" onclick="toggleDarkMode()" title="Toggle dark mode">🌙</button>
        <button class="dark-toggle" onclick="showChangelog()" title="Change Log">📋</button>
        <button class="dark-toggle" onclick="showHelp()" title="Help">&#10067;</button>
        <button class="dark-toggle" onclick="showReportIssue()" title="Report Issue">&#9888;&#65039;</button>
        <button class="dark-toggle notif-bell-btn" onclick="openNotificationsPanel()" title="Notifications">&#128276;<span class="notif-badge" id="notifBellBadge" style="display:none;">0</span></button>
    </div>
</div>

<div class="container">
    <div class="detail-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <div>
            <h2 id="dashTitle" style="font-size:22px;font-weight:600;">My Irrigation System</h2>
            <div id="dashAddress" onclick="openAddressInMaps()" style="font-size:14px;color:var(--color-link);margin-top:4px;display:none;cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;" title="Open in Maps"></div>
            <div id="dashTimezone" style="font-size:12px;color:var(--text-muted);margin-top:2px;"></div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
            <button class="btn btn-secondary btn-sm" onclick="cloneToDashboard()" title="Create a native HA dashboard from current config">Clone to HA Dashboard</button>
            <button class="btn btn-secondary btn-sm" onclick="refreshDashboard()">Refresh</button>
            <button class="btn btn-danger btn-sm" onclick="stopAllZones()">Emergency Stop All</button>
        </div>
    </div>

    <!-- Upcoming Service Banner -->
    <div id="upcomingServiceBanner" onclick="addServiceToCalendar()" style="display:none;background:linear-gradient(135deg,#1abc9c,#16a085);color:white;border-radius:12px;padding:16px 20px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,0.1);cursor:pointer;transition:transform 0.15s,box-shadow 0.15s;" onmouseover="this.style.transform='translateY(-1px)';this.style.boxShadow='0 4px 12px rgba(0,0,0,0.15)';" onmouseout="this.style.transform='';this.style.boxShadow='0 2px 8px rgba(0,0,0,0.1)';">
        <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:20px;">&#128295;</span>
            <div style="flex:1;">
                <div style="font-weight:600;font-size:15px;" id="upcomingServiceDate"></div>
                <div style="font-size:13px;opacity:0.9;margin-top:2px;" id="upcomingServiceNote"></div>
            </div>
            <span style="font-size:18px;opacity:0.8;" title="Add to Calendar">&#128197;</span>
        </div>
        <div style="font-size:11px;opacity:0.7;margin-top:6px;text-align:center;">Tap to add to calendar</div>
    </div>

    <!-- Active Issues Summary -->
    <div id="activeIssuesBanner" style="display:none;margin-bottom:16px;"></div>

    <!-- Location Map -->
    <div id="detailMap" style="height:200px;border-radius:12px;margin-bottom:20px;display:none;overflow:hidden;"></div>

    <!-- Status Card -->
    <div class="card">
        <div class="card-header" onclick="toggleCard('status')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_status" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> System Status</h2>
            <div style="display:flex;gap:8px;align-items:center;">
                <a href="#" onclick="lockCard('status',event)" id="cardLock_status" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
                <button class="btn btn-secondary btn-sm" id="pauseResumeBtn" onclick="event.stopPropagation();togglePauseResume()">Pause System</button>
            </div>
        </div>
        <div class="card-body" id="cardBody_status">
            <div class="loading">Loading status...</div>
        </div>
    </div>

    <!-- Gallons + Pump Row (side-by-side when pump detected, full-width otherwise) -->
    <div class="card-row" id="gallonsPumpRow" style="display:block;">
        <!-- Estimated Gallons Card -->
        <div class="card" id="estGallonsCard" style="display:none;">
            <div class="card-header" onclick="toggleCard('gallons')" style="cursor:pointer;user-select:none;">
                <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_gallons" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> &#128167; Water Monitor</h2>
                <div style="display:flex;gap:6px;align-items:center;">
                    <a href="#" onclick="lockCard('gallons',event)" id="cardLock_gallons" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
                    <select id="gallonsRange" onclick="event.stopPropagation()" onchange="loadEstGallons()" style="padding:4px 8px;border:1px solid var(--border-input);border-radius:6px;font-size:12px;background:var(--bg-input,var(--bg-tile));color:var(--text-primary);">
                        <option value="24">Last 24 hours</option>
                        <option value="168">Last 7 days</option>
                        <option value="720">Last 30 days</option>
                        <option value="2160">Last 90 days</option>
                        <option value="8760">Last year</option>
                    </select>
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();showWaterSettingsModal()" title="Water source settings">&#9881;&#65039;</button>
                </div>
            </div>
            <div class="card-body" id="cardBody_gallons">
                <div class="loading">Loading...</div>
            </div>
        </div>

        <!-- Pump Monitor Card -->
        <div class="card" id="pumpMonitorCard" style="display:none;">
            <div class="card-header" onclick="toggleCard('pump')" style="cursor:pointer;user-select:none;">
                <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_pump" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> &#9889; Pump Monitor</h2>
                <div style="display:flex;gap:6px;align-items:center;">
                    <a href="#" onclick="lockCard('pump',event)" id="cardLock_pump" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
                    <select id="pumpRange" onclick="event.stopPropagation()" onchange="loadPumpMonitor()" style="padding:4px 8px;border:1px solid var(--border-input);border-radius:6px;font-size:12px;background:var(--bg-input,var(--bg-tile));color:var(--text-primary);">
                        <option value="24">Last 24 hours</option>
                        <option value="720" selected>Last 30 days</option>
                        <option value="2160">Last 90 days</option>
                        <option value="8760">Last year</option>
                    </select>
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();showPumpSettingsModal()" title="Pump settings">&#9881;&#65039;</button>
                </div>
            </div>
            <div class="card-body" id="cardBody_pump">
                <div class="loading">Loading...</div>
            </div>
        </div>
    </div>

    <!-- Rain Sensor Card -->
    <div class="card" id="rainSensorCard" style="display:none;">
        <div class="card-header" onclick="toggleCard('rain')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_rain" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> &#127783;&#65039; Rain Sensor</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <a href="#" onclick="lockCard('rain',event)" id="cardLock_rain" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
                <span id="rainStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-tile);color:var(--text-muted);">&#8212;</span>
            </div>
        </div>
        <div class="card-body" id="cardBody_rain">
            <div class="loading">Loading rain sensor...</div>
        </div>
    </div>

    <!-- Weather Card -->
    <div class="card" id="weatherCard" style="display:none;">
        <div class="card-header" onclick="toggleCard('weather')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_weather" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> Weather-Based Control</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <a href="#" onclick="lockCard('weather',event)" id="cardLock_weather" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
                <span id="weatherMultBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-success-light);color:var(--text-success-dark);">1.0x</span>
            </div>
        </div>
        <div class="card-body" id="cardBody_weather">
            <div class="loading">Loading weather...</div>
        </div>
    </div>

    <!-- Moisture Probes Card -->
    <div class="card" id="moistureCard" style="display:none;">
        <div class="card-header" onclick="toggleCard('moisture')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_moisture" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> <svg xmlns="http://www.w3.org/2000/svg" viewBox="155 170 745 295" style="height:28px;width:auto;"><path fill="var(--text-primary)" fill-rule="evenodd" d="M322.416931,281.625397 C323.073517,288.667053 324.062378,295.290680 324.095001,301.918976 C324.240021,331.407532 324.573761,360.907135 323.953278,390.384125 C323.315430,420.685608 305.951965,442.817230 276.750000,451.004150 C252.045670,457.930115 227.631088,457.462616 204.859512,444.061829 C193.733704,437.514404 185.529037,427.904022 179.913101,416.206268 C179.426056,415.191742 179.182327,414.060425 178.732849,412.703430 C192.772842,404.558502 206.657608,396.503632 221.095810,388.127686 C222.548920,398.588440 227.417007,406.291168 236.306213,411.228241 C242.295563,414.554749 248.872574,415.283630 255.195541,413.607391 C269.094299,409.922882 279.602142,400.331543 276.985321,375.408997 C268.292480,376.997406 259.625824,379.362396 250.827682,380.053528 C212.511551,383.063599 177.112976,355.681854 170.128632,318.134705 C162.288498,275.986908 187.834488,236.765533 229.805115,227.777832 C248.650925,223.742157 267.514679,224.860764 285.481567,232.988800 C306.417999,242.460220 318.099121,258.975830 322.416931,281.625397 M216.907806,286.065979 C225.295822,272.331604 237.176926,265.403442 252.929047,267.162231 C267.323669,268.769440 277.405518,277.037170 282.681366,290.504517 C288.739105,305.967712 282.622986,322.699615 267.827820,332.537079 C254.597519,341.334045 236.860046,339.821564 225.031052,328.887756 C212.268768,317.091309 209.342514,302.099945 216.907806,286.065979z"/><path fill="var(--text-primary)" fill-rule="evenodd" d="M440.778076,230.141632 C466.800079,239.483002 484.434601,256.637787 491.839233,283.105133 C500.007050,312.300537 489.084961,342.278625 464.074921,361.493744 C431.640076,386.413300 382.445770,383.545990 353.656403,355.057953 C318.682434,320.450043 324.759583,264.850739 366.581024,238.762604 C389.708984,224.335434 414.506042,222.091354 440.778076,230.141632 M419.079773,266.764740 C437.440765,270.748535 450.546936,286.287720 449.715515,302.670624 C448.781708,321.070160 434.135437,336.279297 415.803497,337.885803 C397.935547,339.451660 380.905334,327.358856 376.509705,309.984161 C370.390747,285.797394 393.025116,262.545013 419.079773,266.764740z"/><path fill="var(--text-primary)" fill-rule="evenodd" d="M505.651459,275.706696 C519.676758,244.101715 544.491516,227.960754 577.827881,226.121109 C611.160156,224.281693 638.083069,237.473114 655.040100,266.968140 C676.296448,303.941376 659.723389,352.082367 620.168030,369.955170 C596.583435,380.611755 572.628662,381.200958 548.535156,371.444641 C547.794678,371.144745 546.983826,371.018707 545.645447,370.662506 C545.645447,390.059296 545.645447,409.111145 545.645447,428.497070 C530.607544,428.497070 516.074341,428.497070 500.996918,428.497070 C500.996918,426.395355 500.996918,424.628113 500.996918,422.860901 C500.996948,382.885895 500.731262,342.907776 501.200592,302.938263 C501.306030,293.961548 503.980682,285.014954 505.651459,275.706696 M598.115479,334.281433 C575.892517,344.478851 553.161804,330.843811 547.077026,312.404572 C542.453613,298.393616 547.708435,283.178833 560.344666,273.573029 C572.626587,264.236572 589.550232,263.566986 602.341309,271.911499 C626.866516,287.910980 624.857971,320.051117 598.115479,334.281433z"/><path fill="var(--text-primary)" d="M670.825439,182.155045 C670.825439,180.187927 670.825439,178.699997 670.825439,176.849915 C685.635620,176.849915 700.198181,176.849915 715.259155,176.849915 C715.259155,197.175491 715.259155,217.587784 715.259155,238.510025 C716.406799,238.089737 717.045288,238.015717 717.473022,237.676285 C735.466553,223.398956 755.376953,222.532013 775.856384,230.443253 C790.949036,236.273605 798.483093,249.035553 801.756714,264.225281 C803.287109,271.326416 804.004150,278.725677 804.067200,285.998688 C804.319702,315.143738 804.171570,344.292236 804.171570,373.721710 C789.407043,373.721710 774.836182,373.721710 759.827942,373.721710 C759.827942,371.711731 759.835571,369.768616 759.826843,367.825562 C759.706604,341.165588 760.090210,314.490112 759.275696,287.851318 C758.772949,271.407867 746.863953,263.163330 731.353210,266.883484 C722.925842,268.904694 717.127258,275.714691 716.057434,285.099060 C715.681213,288.399445 715.542114,291.742798 715.536499,295.066956 C715.495117,319.566559 715.514954,344.066254 715.515503,368.565918 C715.515503,370.204803 715.515503,371.843689 715.515503,373.824829 C700.566040,373.824829 685.988281,373.824829 670.825439,373.824829 C670.825439,310.162415 670.825439,246.398331 670.825439,182.155045z"/><path fill="var(--text-primary)" d="M855.839355,323.000092 C855.839355,340.127289 855.839355,356.754486 855.839355,373.695129 C840.823486,373.695129 826.114746,373.695129 810.997253,373.695129 C810.997253,371.683563 810.994263,369.731567 810.997681,367.779572 C811.046997,339.965515 810.786316,312.145172 811.345886,284.341370 C811.503601,276.506470 813.144958,268.402985 815.701904,260.971832 C822.865173,240.153290 839.259949,230.438156 859.952881,227.148788 C867.723389,225.913574 875.715454,226.072052 883.918213,225.576279 C883.918213,240.530334 883.918213,254.247711 883.918213,268.202820 C883.009399,267.944122 882.380005,267.791504 881.768005,267.586914 C867.262085,262.736725 856.693237,269.680603 856.083313,285.032410 C855.587708,297.505157 855.890564,310.009644 855.839355,323.000092z"/><path fill="#6DAC39" d="M397.000000,391.998138 C428.473236,391.998138 459.446503,391.998138 490.792969,391.998138 C490.792969,404.699890 490.792969,417.072754 490.792969,429.726562 C438.290070,429.726562 385.895660,429.726562 333.244019,429.726562 C333.244019,417.257721 333.244019,404.991150 333.244019,391.998138 C354.328308,391.998138 375.414154,391.998138 397.000000,391.998138z"/></svg> Moisture Probes</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <a href="#" onclick="lockCard('moisture',event)" id="cardLock_moisture" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
                <span id="moistureStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-success-light);color:var(--text-success-dark);">—</span>
            </div>
        </div>
        <div class="card-body" id="cardBody_moisture">
            <div class="loading">Loading moisture data...</div>
        </div>
    </div>

    <!-- Zones Card -->
    <div class="card">
        <div class="card-header" onclick="toggleCard('zones')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_zones" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> Zones</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <a href="#" onclick="lockCard('zones',event)" id="cardLock_zones" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
                <div id="autoAdvanceToggle" onclick="event.stopPropagation()" style="display:none;"></div>
            </div>
        </div>
        <div class="card-body" id="cardBody_zones">
            <div class="loading">Loading zones...</div>
        </div>
    </div>

    <!-- Schedule Card (entity-based) -->
    <div class="card">
        <div class="card-header" onclick="toggleCard('schedule')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_schedule" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> Schedule</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <a href="#" onclick="lockCard('schedule',event)" id="cardLock_schedule" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
            </div>
        </div>
        <div class="card-body" id="cardBody_schedule">
            <div class="loading">Loading schedule...</div>
        </div>
    </div>

    <!-- Sensors Card -->
    <div class="card">
        <div class="card-header" onclick="toggleCard('sensors')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_sensors" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> Sensors</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <a href="#" onclick="lockCard('sensors',event)" id="cardLock_sensors" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
            </div>
        </div>
        <div class="card-body" id="cardBody_sensors">
            <div class="loading">Loading sensors...</div>
        </div>
    </div>

    <!-- Device Controls Card (collapsible, collapsed by default) -->
    <div class="card">
        <div class="card-header" onclick="toggleCard('controls')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_controls" style="font-size:12px;transition:transform 0.2s;display:inline-block;">&#9654;</span> Device Controls</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <a href="#" onclick="lockCard('controls',event)" id="cardLock_controls" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
            </div>
        </div>
        <div class="card-body" id="cardBody_controls" style="display:none;">
            <div class="loading">Loading controls...</div>
        </div>
    </div>

    <!-- Expansion Boards Card (collapsible, collapsed by default) -->
    <div class="card" id="expansionCard" style="display:none;">
        <div class="card-header" onclick="toggleCard('expansion')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_expansion" style="font-size:12px;transition:transform 0.2s;display:inline-block;">&#9654;</span> &#128268; Expansion Boards</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <a href="#" onclick="lockCard('expansion',event)" id="cardLock_expansion" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
                <span id="expansionStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-tile);color:var(--text-muted);">&#8212;</span>
            </div>
        </div>
        <div class="card-body" id="cardBody_expansion" style="display:none;">
            <div class="loading">Loading expansion data...</div>
        </div>
    </div>

    <!-- History Card -->
    <div class="card">
        <div class="card-header" onclick="toggleCard('history')" style="cursor:pointer;user-select:none;">
            <h2 style="display:flex;align-items:center;gap:8px;"><span id="cardChevron_history" style="font-size:12px;transition:transform 0.2s;display:inline-block;transform:rotate(90deg);">&#9654;</span> Run History</h2>
            <div style="display:flex;gap:6px;align-items:center;">
                <a href="#" onclick="lockCard('history',event)" id="cardLock_history" style="text-decoration:none;display:inline-flex;align-items:center;color:var(--text-muted);" title="Lock open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="currentColor"><rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/><rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/><path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/></svg></a>
                <select id="historyZoneFilter" onclick="event.stopPropagation()" onchange="loadHistory()" style="padding:4px 8px;border:1px solid var(--border-input);border-radius:6px;font-size:12px;background:var(--bg-input,var(--bg-tile));color:var(--text-primary);max-width:130px;">
                    <option value="">All Zones</option>
                </select>
                <select id="historyRange" onclick="event.stopPropagation()" onchange="loadHistory()" style="padding:4px 8px;border:1px solid var(--border-input);border-radius:6px;font-size:12px;background:var(--bg-input,var(--bg-tile));color:var(--text-primary);">
                    <option value="24">Last 24 hours</option>
                    <option value="168">Last 7 days</option>
                    <option value="720">Last 30 days</option>
                    <option value="2160">Last 90 days</option>
                    <option value="8760">Last year</option>
                </select>
                <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();exportHistoryCSV()">Export CSV</button>
                <button class="btn btn-danger btn-sm" onclick="event.stopPropagation();clearRunHistory()">Clear History</button>
            </div>
        </div>
        <div class="card-body" id="cardBody_history">
            <div class="loading">Loading history...</div>
        </div>
    </div>
</div>

<!-- Change Log Modal -->
<div id="changelogModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:780px;max-height:85vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">Configuration Change Log</h3>
            <div style="display:flex;gap:6px;align-items:center;">
                <button class="btn btn-secondary btn-sm" onclick="exportChangelogCSV()">Export CSV</button>
                <button onclick="closeChangelogModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
            </div>
        </div>
        <div id="changelogFilters" style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;padding:12px 24px;border-bottom:1px solid var(--border-light);background:var(--bg-tile);">
            <select id="clFilterActor" onchange="applyChangelogFilters()" style="padding:4px 8px;border-radius:6px;border:1px solid var(--border-light);background:var(--bg-input);color:var(--text-primary);font-size:12px;cursor:pointer;">
                <option value="all">All Users</option>
                <option value="Homeowner">Homeowner</option>
                <option value="Management">Management</option>
            </select>
            <select id="clFilterTime" onchange="applyChangelogFilters()" style="padding:4px 8px;border-radius:6px;border:1px solid var(--border-light);background:var(--bg-input);color:var(--text-primary);font-size:12px;cursor:pointer;">
                <option value="7">Last 7 Days</option>
                <option value="30" selected>Last 30 Days</option>
                <option value="90">Last 90 Days</option>
                <option value="365">Last 1 Year</option>
                <option value="730">Last 2 Years</option>
            </select>
            <select id="clFilterCategory" onchange="applyChangelogFilters()" style="padding:4px 8px;border-radius:6px;border:1px solid var(--border-light);background:var(--bg-input);color:var(--text-primary);font-size:12px;cursor:pointer;">
                <option value="all">All Categories</option>
            </select>
            <span id="clFilterCount" style="font-size:11px;color:var(--text-muted);margin-left:auto;"></span>
        </div>
        <div id="changelogContent" style="padding:16px 24px 24px 24px;overflow-y:auto;font-size:13px;color:var(--text-secondary);line-height:1.5;">
            Loading...
        </div>
    </div>
</div>

<!-- Help Modal -->
<div id="helpModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:640px;max-height:80vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">Homeowner Dashboard Help</h3>
            <button onclick="closeHelpModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div id="helpContent" style="padding:16px 24px 24px 24px;overflow-y:auto;font-size:14px;color:var(--text-secondary);line-height:1.6;"></div>
    </div>
</div>

<!-- Report Issue Modal -->
<div id="reportIssueModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:500px;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">&#9888;&#65039; Report an Issue</h3>
            <button onclick="closeReportIssue()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div style="padding:20px 24px 24px 24px;">
            <label style="font-size:13px;font-weight:600;color:var(--text-secondary);display:block;margin-bottom:8px;">Severity</label>
            <div style="display:flex;gap:8px;margin-bottom:16px;" id="severityBtns">
                <button type="button" class="severity-btn" data-sev="clarification" onclick="selectSeverity(\'clarification\')" style="flex:1;padding:10px 8px;border-radius:8px;border:2px solid #3498db;cursor:pointer;font-size:13px;font-weight:600;background:var(--bg-tile);color:#3498db;transition:all 0.15s ease;">Clarification</button>
                <button type="button" class="severity-btn" data-sev="annoyance" onclick="selectSeverity(\'annoyance\')" style="flex:1;padding:10px 8px;border-radius:8px;border:2px solid #f39c12;cursor:pointer;font-size:13px;font-weight:600;background:var(--bg-tile);color:#f39c12;transition:all 0.15s ease;">Annoyance</button>
                <button type="button" class="severity-btn" data-sev="severe" onclick="selectSeverity(\'severe\')" style="flex:1;padding:10px 8px;border-radius:8px;border:2px solid #e74c3c;cursor:pointer;font-size:13px;font-weight:600;background:var(--bg-tile);color:#e74c3c;transition:all 0.15s ease;">Severe Issue</button>
            </div>
            <label style="font-size:13px;font-weight:600;color:var(--text-secondary);display:block;margin-bottom:8px;">Describe the Issue</label>
            <textarea id="issueDescription" maxlength="1000" placeholder="Please describe the issue you are experiencing..." style="width:100%;min-height:100px;padding:10px 12px;border-radius:8px;border:1px solid var(--border-light);background:var(--bg-tile);color:var(--text-primary);font-size:14px;font-family:inherit;resize:vertical;box-sizing:border-box;"></textarea>
            <div style="text-align:right;font-size:11px;color:var(--text-muted);margin-top:4px;"><span id="issueCharCount">0</span>/1000</div>
            <div style="display:flex;gap:8px;margin-top:16px;justify-content:flex-end;">
                <button class="btn btn-secondary btn-sm" onclick="closeReportIssue()">Cancel</button>
                <button class="btn btn-danger btn-sm" id="submitIssueBtn" onclick="submitIssue()">Submit Issue</button>
            </div>
        </div>
    </div>
</div>

<!-- Return Issue Modal -->
<div id="returnIssueModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;" onclick="if(event.target===this)closeReturnModal()">
    <div style="background:var(--bg-card);border-radius:16px;width:90%;max-width:420px;box-shadow:0 8px 32px rgba(0,0,0,0.2);overflow:hidden;">
        <div style="padding:20px 24px 0 24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:18px;font-weight:600;color:var(--text-primary);">Issue Not Resolved</span>
                <button onclick="closeReturnModal()" style="background:none;border:none;font-size:24px;color:var(--text-muted);cursor:pointer;">&times;</button>
            </div>
            <p style="font-size:13px;color:var(--text-secondary);margin:8px 0 0 0;">Please explain why this issue is not resolved. Management will review your note.</p>
        </div>
        <div style="padding:16px 24px 24px 24px;">
            <textarea id="returnReasonText" rows="4" maxlength="1000" placeholder="Describe why the issue is not resolved..." style="width:100%;border:1px solid var(--border-light);border-radius:8px;padding:10px;font-size:14px;resize:vertical;background:var(--bg-tile);color:var(--text-primary);box-sizing:border-box;font-family:inherit;"></textarea>
            <div style="display:flex;gap:8px;margin-top:12px;">
                <button onclick="closeReturnModal()" class="btn btn-secondary" style="flex:1;">Cancel</button>
                <button id="returnSubmitBtn" onclick="submitReturnIssue()" class="btn" style="flex:1;background:#e74c3c;color:#fff;border:none;">Submit</button>
            </div>
        </div>
    </div>
</div>

<div class="toast-container" id="toastContainer"></div>

<!-- Generic Dynamic Modal -->
<div id="dynamicModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;" onclick="if(event.target===this)closeDynamicModal()">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:400px;max-height:80vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px 10px 20px;border-bottom:1px solid var(--border-light);">
            <h3 id="dynamicModalTitle" style="font-size:15px;font-weight:600;margin:0;color:var(--text-primary);"></h3>
            <button onclick="closeDynamicModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div id="dynamicModalBody" style="padding:12px 20px 20px 20px;overflow-y:auto;"></div>
    </div>
</div>

<!-- Gallons Zone Detail Modal -->
<div id="gallonsDetailModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10001;align-items:center;justify-content:center;" onclick="if(event.target===this)closeGallonsDetailModal()">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:92%;max-width:520px;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;max-height:80vh;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);flex-shrink:0;">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">&#128167; Zone Water Usage</h3>
            <button onclick="closeGallonsDetailModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div id="gallonsDetailBody" style="overflow-y:auto;flex:1;min-height:0;padding:16px 24px 24px 24px;"></div>
    </div>
</div>

<!-- Notifications Panel Modal (with settings inside) -->
<div id="notifPanelModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10001;align-items:center;justify-content:center;" onclick="if(event.target===this)closeNotificationsPanel()">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:92%;max-width:500px;max-height:85vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px 12px 20px;border-bottom:1px solid var(--border-light);flex-shrink:0;">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">&#128276; Notifications</h3>
            <div style="display:flex;align-items:center;gap:6px;">
                <button onclick="showNotifSettingsView()" title="Notification Settings" style="background:none;border:none;font-size:18px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&#9881;&#65039;</button>
                <button class="btn btn-secondary btn-sm" id="notifMarkAllBtn" onclick="markAllNotificationsRead()" style="font-size:11px;display:none;">Mark all read</button>
                <button class="btn btn-secondary btn-sm" id="notifClearAllBtn" onclick="clearAllNotifications()" style="font-size:11px;display:none;">Clear</button>
                <button onclick="closeNotificationsPanel()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
            </div>
        </div>
        <div id="notifPanelBody" style="overflow-y:auto;flex:1;min-height:0;padding:0;">
            <div style="color:var(--text-muted);text-align:center;padding:40px;">Loading...</div>
        </div>
    </div>
</div>

<!-- Calendar Picker Modal (iOS) -->
<div id="calendarPickerModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:flex-end;justify-content:center;" onclick="if(event.target===this)closeCalendarPicker()">
    <div style="background:var(--bg-card);border-radius:16px 16px 0 0;padding:0;width:100%;max-width:500px;box-shadow:0 -4px 24px rgba(0,0,0,0.2);animation:slideUp 0.25s ease-out;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:18px 20px 10px 20px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:16px;font-weight:600;margin:0;color:var(--text-primary);">Add to Calendar</h3>
            <button onclick="closeCalendarPicker()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div style="padding:12px 20px 24px 20px;display:flex;flex-direction:column;gap:10px;" id="calendarPickerOptions"></div>
    </div>
</div>
<style>@keyframes slideUp{from{transform:translateY(100%)}to{transform:translateY(0)}}</style>

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

// --- Probe Wake Conflict Warning ---
var _pendingForceEntity = null;
var _pendingForceSleep = null;

function _buildConflictModalHtml(conflicts) {
    var html = '<div style="margin-bottom:12px;color:var(--text-secondary);">' +
        'This change will prevent the following probe(s) from waking before their ' +
        'mapped zone(s) on the next watering cycle:</div><div style="margin-bottom:16px;">';
    for (var i = 0; i < conflicts.length; i++) {
        var c = conflicts[i];
        html += '<div style="padding:8px;margin-bottom:6px;background:var(--bg-hover);border-radius:6px;border-left:3px solid var(--color-warning);">' +
            '<strong>' + esc(c.probe_name) + '</strong> cannot wake before ' +
            '<strong>Zone ' + c.zone_num + '</strong> at <strong>' + esc(c.zone_start_time) + '</strong>' +
            '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">Prep needed by ' +
            esc(c.prep_trigger_time) + ' (already past)</div></div>';
    }
    html += '</div>';
    return html;
}

function _forceEntitySet() {
    if (!_pendingForceEntity) return;
    var p = _pendingForceEntity;
    _pendingForceEntity = null;
    closeDynamicModal();
    setEntityValue(p.entityId, p.domain, p.bodyObj, true);
}

function _forceSleepSet() {
    if (!_pendingForceSleep) return;
    var p = _pendingForceSleep;
    _pendingForceSleep = null;
    closeDynamicModal();
    _doSetSleepDuration(p.probeId, p.minutes, true);
}

// --- Sprinkler Type Icons ---
var _sprinklerCategoryMap = {
    'pop_up_spray':'spray','rotary_nozzle':'spray','fixed_spray':'spray','strip_spray':'spray',
    'gear_rotor':'rotor','impact_rotor':'rotor',
    'drip_emitter':'drip','drip_line':'drip',
    'micro_spray':'micro','bubbler':'micro'
};
function getSprinklerCategories(heads) {
    if (!heads || heads.length === 0) return null;
    var counts = {};
    for (var i = 0; i < heads.length; i++) {
        var cat = _sprinklerCategoryMap[heads[i].nozzle_type];
        if (cat) counts[cat] = (counts[cat] || 0) + 1;
    }
    var sorted = Object.keys(counts).sort(function(a, b) {
        if (counts[b] !== counts[a]) return counts[b] - counts[a];
        return a.localeCompare(b);
    });
    if (sorted.length === 0) return null;
    if (sorted.length === 1) return { categories: [sorted[0]], single: true };
    if (counts[sorted[0]] === counts[sorted[1]]) {
        return { categories: [sorted[0], sorted[1]], single: false };
    }
    return { categories: [sorted[0]], single: true };
}
function getSprinklerSvg(category, size) {
    var s = size || 36;
    var svgs = {
        'spray': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor"><rect x="10" y="15" width="4" height="7" rx="1"/><path d="M12 13 Q4 5 3 2.5 Q3 2 3.5 2 L20.5 2 Q21 2 21 2.5 Q20 5 12 13Z" opacity="0.65"/><circle cx="12" cy="14" r="2.5"/></svg>',
        'rotor': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor"><rect x="10" y="13" width="4" height="9" rx="1"/><circle cx="12" cy="11" r="3"/><path d="M14.5 8.5 Q17 4 19 2.5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.6"/><path d="M15.5 9.5 Q19 6 21 5" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.4"/></svg>',
        'drip': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor"><path d="M12 2 C12 2 6 10 6 15 C6 18.3 8.7 21 12 21 C15.3 21 18 18.3 18 15 C18 10 12 2 12 2Z"/></svg>',
        'micro': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor"><rect x="10.5" y="15" width="3" height="7" rx="1"/><circle cx="7" cy="6" r="1.5" opacity="0.5"/><circle cx="12" cy="4" r="1.5" opacity="0.5"/><circle cx="17" cy="6" r="1.5" opacity="0.5"/><circle cx="9" cy="9.5" r="1.3" opacity="0.4"/><circle cx="15" cy="9.5" r="1.3" opacity="0.4"/><circle cx="12" cy="12" r="1.8" opacity="0.65"/></svg>',
        'pump': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor"><circle cx="10" cy="14" r="6" opacity="0.55"/><circle cx="10" cy="14" r="3.5"/><rect x="14" y="12" width="8" height="4" rx="1" opacity="0.7"/><rect x="1" y="12.5" width="4" height="3" rx="0.5" opacity="0.5"/><rect x="7" y="6" width="6" height="3" rx="1" opacity="0.4"/><rect x="9" y="3" width="2" height="3" rx="0.5" opacity="0.35"/></svg>',
        'valve': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor"><rect x="1" y="13" width="22" height="5" rx="1.5" opacity="0.5"/><rect x="8" y="11" width="8" height="9" rx="2"/><rect x="11" y="4" width="2" height="7" rx="0.5"/><circle cx="12" cy="4" r="3" opacity="0.6"/><circle cx="12" cy="4" r="1.5"/></svg>'
    };
    return svgs[category] || '';
}

function getStatusTileSvg(key, size) {
    var s = size || 32;
    var svgs = {
        'connection': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor">'
            + '<path d="M12 18.5 C12.8 18.5 13.5 19.2 13.5 20 C13.5 20.8 12.8 21.5 12 21.5 C11.2 21.5 10.5 20.8 10.5 20 C10.5 19.2 11.2 18.5 12 18.5Z"/>'
            + '<path d="M8.5 15.5 Q12 12.5 15.5 15.5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.7"/>'
            + '<path d="M5.5 12 Q12 7 18.5 12" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.5"/>'
            + '<path d="M2.5 8.5 Q12 2 21.5 8.5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.35"/>'
            + '</svg>',
        'system': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor">'
            + '<circle cx="12" cy="12" r="10" opacity="0.15"/>'
            + '<circle cx="12" cy="12" r="7" opacity="0.25"/>'
            + '<path d="M12 5 L12 12" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" opacity="0.8"/>'
            + '<path d="M8 6.5 Q6 8 5.5 10.5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.5"/>'
            + '<path d="M16 6.5 Q18 8 18.5 10.5" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.5"/>'
            + '</svg>',
        'zones': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor">'
            + '<rect x="2" y="2" width="8.5" height="8.5" rx="2" opacity="0.6"/>'
            + '<rect x="13.5" y="2" width="8.5" height="8.5" rx="2" opacity="0.4"/>'
            + '<rect x="2" y="13.5" width="8.5" height="8.5" rx="2" opacity="0.4"/>'
            + '<rect x="13.5" y="13.5" width="8.5" height="8.5" rx="2" opacity="0.25"/>'
            + '</svg>',
        'sensors': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor">'
            + '<rect x="10" y="3" width="4" height="15" rx="2" opacity="0.3"/>'
            + '<rect x="10.5" y="10" width="3" height="7.5" rx="1.5" opacity="0.65"/>'
            + '<circle cx="12" cy="18.5" r="3.5" opacity="0.6"/>'
            + '<circle cx="12" cy="18.5" r="2"/>'
            + '<path d="M6 10 L9.5 10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity="0.4"/>'
            + '<path d="M6 13 L9.5 13" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity="0.4"/>'
            + '<path d="M6 7 L9.5 7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" opacity="0.4"/>'
            + '</svg>',
        'rain': '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor">'
            + '<path d="M19 11 Q21 11 21 13 Q21 15 19 15 L6 15 Q3 15 3 12.5 Q3 10 6 10 Q6 6 10 5 Q14 4 16 7 Q19 7 19 11Z" opacity="0.45"/>'
            + '<path d="M7.5 17.5 L6 21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>'
            + '<path d="M11.5 17.5 L10 21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>'
            + '<path d="M15.5 17.5 L14 21" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.6"/>'
            + '</svg>'
    };
    return svgs[key] || '';
}

function getLockSvg(locked, size) {
    var s = size || 22;
    if (locked) {
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor">'
            + '<rect x="4" y="11" width="16" height="11" rx="2" opacity="0.75"/>'
            + '<rect x="9" y="14" width="6" height="5" rx="1"/>'
            + '<path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 11" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.9"/>'
            + '</svg>';
    } else {
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="currentColor">'
            + '<rect x="4" y="11" width="16" height="11" rx="2" opacity="0.5"/>'
            + '<rect x="9" y="14" width="6" height="5" rx="1" opacity="0.65"/>'
            + '<path d="M8 11 L8 7 Q8 2 12 2 Q16 2 16 7 L16 8" stroke="currentColor" stroke-width="2.5" fill="none" stroke-linecap="round" opacity="0.6"/>'
            + '</svg>';
    }
}

// --- Collapsible Cards ---
var _cardLocks = {};
try { _cardLocks = JSON.parse(localStorage.getItem('flux_card_locks_ho') || '{}'); } catch(e) { _cardLocks = {}; }
function _saveCardLocks() { try { localStorage.setItem('flux_card_locks_ho', JSON.stringify(_cardLocks)); } catch(e) {} }

function toggleCard(key) {
    if (_cardLocks[key]) return; // locked open — ignore click
    var body = document.getElementById('cardBody_' + key);
    var chevron = document.getElementById('cardChevron_' + key);
    if (!body) return;
    var isHidden = body.style.display === 'none';
    body.style.display = isHidden ? 'block' : 'none';
    if (chevron) chevron.style.transform = isHidden ? 'rotate(90deg)' : 'rotate(0deg)';
    // Toggle border on the card-header when collapsed
    var header = body.previousElementSibling;
    if (header && header.classList.contains('card-header')) {
        header.style.borderBottom = isHidden ? '' : 'none';
    }
    // Toggle card-collapsed class on parent .card for flexbox sizing
    var card = body.closest('.card');
    if (card) { if (isHidden) { card.classList.remove('card-collapsed'); } else { card.classList.add('card-collapsed'); } }
}

function lockCard(key, evt) {
    if (evt) { evt.stopPropagation(); evt.preventDefault(); }
    var body = document.getElementById('cardBody_' + key);
    var lockIcon = document.getElementById('cardLock_' + key);
    if (_cardLocks[key]) {
        // Unlock
        delete _cardLocks[key];
        if (lockIcon) { lockIcon.innerHTML = getLockSvg(false, 22); lockIcon.title = 'Lock open'; }
    } else {
        // Lock open — ensure expanded
        _cardLocks[key] = true;
        if (body) body.style.display = 'block';
        var chevron = document.getElementById('cardChevron_' + key);
        if (chevron) chevron.style.transform = 'rotate(90deg)';
        if (lockIcon) { lockIcon.innerHTML = getLockSvg(true, 22); lockIcon.title = 'Unlock (allow collapse)'; }
        // Restore header border + remove collapsed class
        if (body) {
            var header = body.previousElementSibling;
            if (header && header.classList.contains('card-header')) header.style.borderBottom = '';
            var card = body.closest('.card');
            if (card) card.classList.remove('card-collapsed');
        }
    }
    _saveCardLocks();
}

function initCardState(key, defaultCollapsed) {
    var body = document.getElementById('cardBody_' + key);
    var chevron = document.getElementById('cardChevron_' + key);
    var lockIcon = document.getElementById('cardLock_' + key);
    if (!body) return;
    var header = body.previousElementSibling;
    var card = body.closest('.card');
    if (_cardLocks[key]) {
        // Locked open
        body.style.display = 'block';
        if (chevron) chevron.style.transform = 'rotate(90deg)';
        if (lockIcon) { lockIcon.innerHTML = getLockSvg(true, 22); lockIcon.title = 'Unlock (allow collapse)'; }
        if (header && header.classList.contains('card-header')) header.style.borderBottom = '';
        if (card) card.classList.remove('card-collapsed');
    } else if (defaultCollapsed) {
        body.style.display = 'none';
        if (chevron) chevron.style.transform = 'rotate(0deg)';
        if (lockIcon) { lockIcon.innerHTML = getLockSvg(false, 22); lockIcon.title = 'Lock open'; }
        if (header && header.classList.contains('card-header')) header.style.borderBottom = 'none';
        if (card) card.classList.add('card-collapsed');
    } else {
        body.style.display = 'block';
        if (chevron) chevron.style.transform = 'rotate(90deg)';
        if (lockIcon) { lockIcon.innerHTML = getLockSvg(false, 22); lockIcon.title = 'Lock open'; }
        if (header && header.classList.contains('card-header')) header.style.borderBottom = '';
        if (card) card.classList.remove('card-collapsed');
    }
}

// --- Report Issue ---
let selectedSeverity = null;
const ISSUE_BASE = HBASE.replace('/api/homeowner', '/api/homeowner/issues');

function showReportIssue() {
    selectedSeverity = null;
    document.getElementById('issueDescription').value = '';
    document.getElementById('issueCharCount').textContent = '0';
    document.querySelectorAll('#severityBtns .severity-btn').forEach(function(b) {
        b.style.background = 'var(--bg-tile)';
        const sev = b.getAttribute('data-sev');
        b.style.color = sev === 'clarification' ? '#3498db' : sev === 'annoyance' ? '#f39c12' : '#e74c3c';
    });
    document.getElementById('reportIssueModal').style.display = 'flex';
}

function closeReportIssue() {
    document.getElementById('reportIssueModal').style.display = 'none';
}

function selectSeverity(sev) {
    selectedSeverity = sev;
    const colors = {clarification: '#3498db', annoyance: '#f39c12', severe: '#e74c3c'};
    document.querySelectorAll('#severityBtns .severity-btn').forEach(function(b) {
        const bSev = b.getAttribute('data-sev');
        if (bSev === sev) {
            b.style.background = colors[sev];
            b.style.color = 'white';
        } else {
            b.style.background = 'var(--bg-tile)';
            b.style.color = colors[bSev];
        }
    });
}

document.getElementById('issueDescription').addEventListener('input', function() {
    document.getElementById('issueCharCount').textContent = this.value.length;
});

async function submitIssue() {
    if (!selectedSeverity) { showToast('Please select a severity level', 'error'); return; }
    const desc = document.getElementById('issueDescription').value.trim();
    if (!desc) { showToast('Please describe the issue', 'error'); return; }
    if (desc.length > 1000) { showToast('Description must be under 1000 characters', 'error'); return; }
    const btn = document.getElementById('submitIssueBtn');
    btn.disabled = true;
    btn.textContent = 'Submitting...';
    try {
        const resp = await fetch(ISSUE_BASE + '/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({severity: selectedSeverity, description: desc}),
        });
        if (!resp.ok) throw new Error('Failed to submit issue');
        showToast('Issue reported successfully');
        closeReportIssue();
        loadActiveIssues();
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Submit Issue';
    }
}

// Escape + backdrop for report issue modal + gallons detail modal
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('gallonsDetailModal').style.display === 'flex') {
        closeGallonsDetailModal();
    }
    if (e.key === 'Escape' && document.getElementById('reportIssueModal').style.display === 'flex') {
        closeReportIssue();
    }
    if (e.key === 'Escape' && document.getElementById('returnIssueModal').style.display === 'flex') {
        closeReturnModal();
    }
});
document.getElementById('reportIssueModal').addEventListener('click', function(e) {
    if (e.target === this) closeReportIssue();
});

// --- Active Issues & Upcoming Service ---
async function loadActiveIssues() {
    try {
        const resp = await fetch(ISSUE_BASE + '/visible');
        if (!resp.ok) { hideIssueBanners(); return; }
        const data = await resp.json();
        const issues = data.issues || [];
        renderUpcomingService(issues.filter(function(i) { return i.status !== 'resolved'; }));
        renderActiveIssuesBanner(issues);
    } catch (e) {
        hideIssueBanners();
    }
}

function hideIssueBanners() {
    document.getElementById('upcomingServiceBanner').style.display = 'none';
    document.getElementById('activeIssuesBanner').style.display = 'none';
}

let _upcomingServiceData = null;

function renderUpcomingService(issues) {
    const banner = document.getElementById('upcomingServiceBanner');
    const scheduled = issues.filter(function(i) { return i.service_date; });
    if (scheduled.length === 0) { banner.style.display = 'none'; _upcomingServiceData = null; return; }
    scheduled.sort(function(a, b) { return a.service_date.localeCompare(b.service_date); });
    const next = scheduled[0];
    _upcomingServiceData = next;
    const dt = new Date(next.service_date + 'T12:00:00');
    const dateStr = dt.toLocaleDateString(undefined, {weekday: 'long', month: 'long', day: 'numeric', year: 'numeric'});
    var dateLabel = 'Upcoming Service: ' + dateStr;
    if (next.service_date_updated_at) {
        dateLabel += ' (Updated)';
    }
    document.getElementById('upcomingServiceDate').textContent = dateLabel;
    const noteEl = document.getElementById('upcomingServiceNote');
    if (next.management_note) {
        noteEl.textContent = next.management_note;
        noteEl.style.display = 'block';
    } else {
        noteEl.style.display = 'none';
    }
    banner.style.display = 'block';
}

// --- Add to Calendar ---
function _calEventData() {
    const svcDate = _upcomingServiceData.service_date.replace(/-/g, '');
    const d = new Date(_upcomingServiceData.service_date + 'T12:00:00');
    d.setDate(d.getDate() + 1);
    const endDate = d.toISOString().slice(0, 10).replace(/-/g, '');
    const label = document.getElementById('dashTitle').textContent || '';
    const title = 'Irrigation Service' + (label ? ' - ' + label : '');
    const loc = document.getElementById('dashAddress').textContent || '';
    let details = 'Irrigation service visit scheduled by your management company.';
    if (_upcomingServiceData.management_note) {
        details += '\\nNote: ' + _upcomingServiceData.management_note;
    }
    return { svcDate: svcDate, endDate: endDate, title: title, location: loc, details: details, isoEnd: d.toISOString().slice(0, 10) };
}

function addServiceToCalendar() {
    if (!_upcomingServiceData || !_upcomingServiceData.service_date) return;
    var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);

    if (isIOS) {
        _showCalendarPicker();
        return;
    }

    // Android/Desktop: try blob download, fall back to picker
    var icsUrl = ISSUE_BASE + '/' + _upcomingServiceData.id + '/calendar.ics';
    fetch(icsUrl).then(function(resp) {
        if (!resp.ok) throw new Error('err');
        return resp.blob();
    }).then(function(blob) {
        var file = new File([blob], 'irrigation-service.ics', { type: 'text/calendar' });
        if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
            return navigator.share({ files: [file], title: 'Irrigation Service' });
        }
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = 'irrigation-service.ics';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function() { URL.revokeObjectURL(url); }, 5000);
    }).catch(function() {
        _showCalendarPicker();
    });
}

function _showCalendarPicker() {
    var ev = _calEventData();

    var googleUrl = 'https://calendar.google.com/calendar/render?action=TEMPLATE'
        + '&text=' + encodeURIComponent(ev.title)
        + '&dates=' + ev.svcDate + '/' + ev.endDate
        + '&details=' + encodeURIComponent(ev.details)
        + '&location=' + encodeURIComponent(ev.location);

    var outlookUrl = 'https://outlook.live.com/calendar/0/action/compose?'
        + 'subject=' + encodeURIComponent(ev.title)
        + '&startdt=' + _upcomingServiceData.service_date
        + '&enddt=' + ev.isoEnd
        + '&body=' + encodeURIComponent(ev.details)
        + '&location=' + encodeURIComponent(ev.location)
        + '&allday=true';

    var opts = document.getElementById('calendarPickerOptions');
    opts.innerHTML = '';

    // Build real <a> tags (not buttons) so the user physically taps the link.
    // HA companion app intercepts <a target="_blank"> the same way
    // openAddressInMaps() works via window.open.
    var items = [
        { label: 'Google Calendar', url: googleUrl },
        { label: 'Outlook / Hotmail', url: outlookUrl }
    ];
    items.forEach(function(item) {
        var a = document.createElement('a');
        a.href = item.url;
        a.target = '_blank';
        a.rel = 'noopener';
        a.textContent = item.label;
        a.style.cssText = 'display:block;width:100%;padding:14px 16px;border-radius:10px;border:1px solid var(--border-light);background:var(--bg-tile);color:var(--text-primary);font-size:15px;font-weight:500;cursor:pointer;text-align:left;text-decoration:none;box-sizing:border-box;';
        a.onclick = function() { setTimeout(closeCalendarPicker, 300); };
        opts.appendChild(a);
    });

    // Copy link fallback — guaranteed to work in any webview
    var copyBtn = document.createElement('button');
    copyBtn.textContent = 'Copy Calendar Link';
    copyBtn.style.cssText = 'width:100%;padding:14px 16px;border-radius:10px;border:1px dashed var(--border-light);background:transparent;color:var(--text-secondary);font-size:14px;cursor:pointer;text-align:left;';
    copyBtn.onclick = function() {
        navigator.clipboard.writeText(googleUrl).then(function() {
            showToast('Calendar link copied! Paste in Safari to add event.');
            closeCalendarPicker();
        }).catch(function() {
            // clipboard failed — select-all fallback
            var inp = document.createElement('input');
            inp.value = googleUrl;
            document.body.appendChild(inp);
            inp.select();
            document.execCommand('copy');
            document.body.removeChild(inp);
            showToast('Calendar link copied! Paste in Safari to add event.');
            closeCalendarPicker();
        });
    };
    opts.appendChild(copyBtn);

    document.getElementById('calendarPickerModal').style.display = 'flex';
}

function closeCalendarPicker() {
    document.getElementById('calendarPickerModal').style.display = 'none';
}

// --- Open Address in Maps ---
function openAddressInMaps() {
    const addr = document.getElementById('dashAddress').textContent;
    if (!addr) return;
    const encoded = encodeURIComponent(addr);
    // Detect iOS/macOS for Apple Maps, otherwise Google Maps
    const isApple = /iPad|iPhone|iPod|Macintosh/.test(navigator.userAgent);
    if (isApple) {
        window.open('https://maps.apple.com/?q=' + encoded, '_blank');
    } else {
        window.open('https://www.google.com/maps/search/?api=1&query=' + encoded, '_blank');
    }
}

function renderActiveIssuesBanner(issues) {
    const container = document.getElementById('activeIssuesBanner');
    if (issues.length === 0) { container.style.display = 'none'; return; }
    const sevColors = {severe: '#e74c3c', annoyance: '#f39c12', clarification: '#3498db'};
    const sevLabels = {severe: 'Severe Issue', annoyance: 'Annoyance', clarification: 'Clarification'};
    const statusLabels = {open: 'Submitted', acknowledged: 'Acknowledged', scheduled: 'Service Scheduled', resolved: 'Resolved', returned: 'Returned - Under Review'};
    let html = '<div style="background:var(--bg-card);border-radius:12px;padding:16px 20px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">';
    html += '<div style="font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:10px;">Your Reported Issues</div>';
    issues.forEach(function(issue) {
        const color = sevColors[issue.severity] || '#999';
        const isResolved = issue.status === 'resolved';
        const isReturned = issue.status === 'returned';
        const dt = new Date(issue.created_at);
        const _isMon = dt.toLocaleDateString('en-US', {month:'short'});
        const _isDay = dt.getDate();
        const _isYr = String(dt.getFullYear()).slice(-2);
        const _isTime = dt.toLocaleTimeString(undefined, {hour:'numeric', minute:'2-digit'});
        const timeStr = _isMon + ' ' + _isDay + '-' + _isYr + ' ' + _isTime;
        html += '<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-light);' + (isResolved ? 'opacity:0.85;' : '') + '">';
        if (isResolved) {
            html += '<span style="display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;background:#27ae6022;color:#27ae60;white-space:nowrap;">&#10003; Resolved</span>';
        } else if (isReturned) {
            html += '<span style="display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;background:#e74c3c22;color:#e74c3c;white-space:nowrap;">&#8635; Returned</span>';
        } else {
            html += '<span style="display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;background:' + color + '22;color:' + color + ';white-space:nowrap;">' + esc(sevLabels[issue.severity] || issue.severity) + '</span>';
        }
        html += '<div style="flex:1;min-width:0;">';
        html += '<div style="font-size:13px;color:var(--text-primary);word-break:break-word;">' + esc(issue.description) + '</div>';
        html += '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">' + esc(timeStr) + ' &middot; ' + esc(statusLabels[issue.status] || issue.status) + '</div>';
        if (issue.management_note) {
            html += '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;padding:6px 10px;background:var(--bg-tile);border-radius:6px;border-left:3px solid var(--color-primary);">&#128172; <strong>Management:</strong> ' + esc(issue.management_note) + '</div>';
        }
        if (issue.return_reason) {
            html += '<div style="font-size:12px;color:#e74c3c;margin-top:4px;padding:6px 10px;background:#e74c3c11;border-radius:6px;border-left:3px solid #e74c3c;">&#9888;&#65039; <strong>Your note:</strong> ' + esc(issue.return_reason) + '</div>';
        }
        if (isResolved) {
            html += '<div style="margin-top:6px;display:flex;gap:6px;">';
            html += '<button onclick="dismissIssue(\\''+issue.id+'\\')" class="btn btn-secondary btn-sm" style="font-size:11px;padding:3px 10px;">Dismiss</button>';
            html += '<button onclick="openReturnModal(\\''+issue.id+'\\')" class="btn btn-sm" style="font-size:11px;padding:3px 10px;background:#e74c3c22;color:#e74c3c;border:1px solid #e74c3c44;">Not Resolved</button>';
            html += '</div>';
        }
        html += '</div></div>';
    });
    html += '</div>';
    container.innerHTML = html;
    container.style.display = 'block';
}

async function dismissIssue(issueId) {
    try {
        const resp = await fetch(ISSUE_BASE + '/' + issueId + '/dismiss', { method: 'PUT' });
        if (!resp.ok) throw new Error('Failed to dismiss');
        showToast('Issue dismissed');
        loadActiveIssues();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// --- Return Issue (Not Resolved) ---
let _returnIssueId = null;

function openReturnModal(issueId) {
    _returnIssueId = issueId;
    document.getElementById('returnReasonText').value = '';
    document.getElementById('returnIssueModal').style.display = 'flex';
}

function closeReturnModal() {
    document.getElementById('returnIssueModal').style.display = 'none';
    _returnIssueId = null;
}

async function submitReturnIssue() {
    if (!_returnIssueId) return;
    var reason = document.getElementById('returnReasonText').value.trim();
    if (!reason) { showToast('Please provide a reason', 'error'); return; }
    var btn = document.getElementById('returnSubmitBtn');
    btn.disabled = true;
    btn.textContent = 'Submitting...';
    try {
        var resp = await fetch(ISSUE_BASE + '/' + _returnIssueId + '/return', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ return_reason: reason }),
        });
        if (!resp.ok) throw new Error('Failed to return issue');
        showToast('Issue returned to management for review');
        closeReturnModal();
        loadActiveIssues();
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Submit';
    }
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
        return 'Zone ' + zoneNum;
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
        return 'Zone ' + zoneNum;
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
            return 'Zone ' + zoneNum + ' - ' + modes[zoneNum].state;
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
        domain === 'number' && (/run_duration/.test(eid) || (/zone_?\\d/.test(eid) && !/repeat|cycle|mode/.test(eid)) || /duration.*zone/.test(eid)),
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

// --- Rain sensor entity classification ---
function isRainEntity(eid) {
    const e = (eid || '').toLowerCase();
    return /rain_sensor$/.test(e) || /rain_sensor_enabled/.test(e) ||
           /rain_delay_enabled/.test(e) || /rain_delay_hours/.test(e) ||
           /rain_sensor_type/.test(e) || /rain_delay_active/.test(e);
}

// --- Expansion board entity classification ---
function isExpansionEntity(eid) {
    const e = (eid || '').toLowerCase();
    return /detected_zones/.test(e) || /rescan_expansion/.test(e);
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

let mapLocked = true;
let mapCenter = null;

function _applyDarkTiles() {
    if (!leafletMap) return;
    var pane = leafletMap.getPane('tilePane');
    if (!pane) return;
    if (document.body.classList.contains('dark-mode')) {
        pane.classList.add('dark-tiles');
    } else {
        pane.classList.remove('dark-tiles');
    }
}

function showMap(lat, lon, label) {
    if (typeof L === 'undefined') {
        if (!showMap._retries) showMap._retries = 0;
        if (++showMap._retries > 25) { document.getElementById('detailMap').style.display = 'none'; return; }
        setTimeout(function() { showMap(lat, lon, label); }, 200);
        return;
    }
    showMap._retries = 0;
    const mapEl = document.getElementById('detailMap');
    mapEl.style.display = 'block';
    mapEl.innerHTML = '';
    mapCenter = { lat, lon };
    mapLocked = true;
    requestAnimationFrame(() => {
        leafletMap = L.map(mapEl, {
            center: [lat, lon],
            zoom: 16,
            dragging: false,
            scrollWheelZoom: false,
            doubleClickZoom: false,
            boxZoom: false,
            keyboard: false,
            zoomControl: false,
            touchZoom: false,
            attributionControl: true,
        });
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap',
            maxZoom: 19,
        }).addTo(leafletMap);
        L.marker([lat, lon]).addTo(leafletMap);
        _applyDarkTiles();
        // Lock/unlock button
        var lockBtn = document.createElement('button');
        lockBtn.id = 'mapLockBtn';
        lockBtn.className = 'map-lock-btn';
        lockBtn.innerHTML = getLockSvg(true, 16);
        lockBtn.title = 'Unlock map interaction';
        lockBtn.addEventListener('click', function(e) { e.stopPropagation(); toggleMapLock(); });
        mapEl.appendChild(lockBtn);
    });
}

function toggleMapLock() {
    if (!leafletMap) return;
    mapLocked = !mapLocked;
    if (mapLocked) {
        leafletMap.dragging.disable();
        leafletMap.scrollWheelZoom.disable();
        leafletMap.doubleClickZoom.disable();
        leafletMap.boxZoom.disable();
        leafletMap.keyboard.disable();
        leafletMap.touchZoom.disable();
        leafletMap.removeControl(leafletMap.zoomControl || {});
    } else {
        leafletMap.dragging.enable();
        leafletMap.scrollWheelZoom.enable();
        leafletMap.doubleClickZoom.enable();
        leafletMap.boxZoom.enable();
        leafletMap.keyboard.enable();
        leafletMap.touchZoom.enable();
        if (!leafletMap._zoomCtrl) {
            leafletMap._zoomCtrl = L.control.zoom({ position: 'topleft' }).addTo(leafletMap);
        }
    }
    var btn = document.getElementById('mapLockBtn');
    if (btn) {
        btn.innerHTML = getLockSvg(mapLocked, 16);
        btn.title = mapLocked ? 'Unlock map interaction' : 'Lock map interaction';
    }
}

// --- Dashboard Loading ---
let _initialLoadDone = false;
async function loadDashboard() {
    loadStatus();
    loadWeather();
    loadMoisture();
    await loadSensors();   // Must complete before loadControls — sets _expansionSensors / _detectedZoneCount
    await loadControls();  // Must complete before loadZones — sets _zoneModes for pump/valve detection
    loadZones();
    if (!_initialLoadDone) _initialLoadDone = true;
    loadHistory();
    loadEstGallons();
    loadPumpMonitor();
    loadActiveIssues();
    pollNotificationBadge();
}

async function refreshDashboard() {
    loadDashboard();
}

function generateReport() {
    var hours = document.getElementById('reportHours').value || '720';
    window.open(HBASE + '/report/pdf?hours=' + hours + '&t=' + Date.now(), '_blank');
}

async function cloneToDashboard() {
    if (!confirm('Create (or update) a native Home Assistant dashboard called "Flux Irrigation" from your current system configuration?')) return;
    try {
        const resp = await fetch(HBASE + '/dashboard/clone-to-ha', { method: 'POST' });
        const result = await resp.json();
        if (resp.ok && result.success) {
            showToast(result.message);
        } else {
            showToast('Failed: ' + (result.detail || result.error || 'Unknown error'), 'error');
        }
    } catch (e) {
        showToast('Error: ' + e.message, 'error');
    }
}

// --- Status ---
let currentSystemPaused = false;

async function loadStatus() {
    const el = document.getElementById('cardBody_status');
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
            <div class="tile">
                <div class="status-tile-icon ${s.ha_connected ? 'icon-on' : 'icon-off'}">${getStatusTileSvg('connection', 32)}</div>
                <div class="status-tile-text"><div class="tile-name">Connection</div><div class="tile-state ${s.ha_connected ? 'on' : ''}">${s.ha_connected ? 'Connected' : 'Disconnected'}</div></div>
            </div>
            <div class="tile">
                <div class="status-tile-icon ${s.system_paused ? 'icon-warn' : 'icon-on'}">${getStatusTileSvg('system', 32)}</div>
                <div class="status-tile-text"><div class="tile-name">System</div><div class="tile-state ${s.system_paused ? '' : 'on'}">${s.system_paused ? 'Paused' : 'Active'}</div></div>
            </div>
            <div class="tile">
                <div class="status-tile-icon ${s.active_zones > 0 ? 'icon-on' : ''}">${getStatusTileSvg('zones', 32)}</div>
                <div class="status-tile-text"><div class="tile-name">Zones</div><div class="tile-state ${s.active_zones > 0 ? 'on' : ''}">${s.active_zones > 0 ? esc(resolveZoneName(s.active_zone_entity_id, s.active_zone_name)) + ' running' : 'Idle (' + (s.total_zones || 0) + ' zones)'}</div></div>
            </div>
            <div class="tile">
                <div class="status-tile-icon">${getStatusTileSvg('sensors', 32)}</div>
                <div class="status-tile-text"><div class="tile-name">Sensors</div><div class="tile-state">${s.total_sensors || 0} total</div></div>
            </div>
            ${s.rain_delay_active ? '<div class="tile"><div class="status-tile-icon icon-warn">' + getStatusTileSvg('rain', 32) + '</div><div class="status-tile-text"><div class="tile-name">Rain Delay</div><div class="tile-state">Until ' + esc(s.rain_delay_until || 'unknown') + '</div></div></div>' : ''}
        </div>`;
        // Report mini-card — below status tiles
        el.innerHTML += `
        <div style="margin-top:12px;padding:10px 14px;background:var(--bg-tile,var(--card-bg));border-radius:8px;border:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:16px;">&#128196;</span>
                <span style="font-size:13px;font-weight:600;color:var(--text);">PDF System Report</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <select id="reportHours" style="padding:4px 8px;border-radius:6px;border:1px solid var(--border);background:var(--card-bg);color:var(--text);font-size:12px;">
                    <option value="24">24 Hours</option>
                    <option value="168">7 Days</option>
                    <option value="720" selected>30 Days</option>
                    <option value="2160">90 Days</option>
                    <option value="8760">1 Year</option>
                </select>
                <button class="btn btn-primary btn-sm" onclick="generateReport()">Generate</button>
            </div>
        </div>`;
        // Data Nerd View mini-card — below PDF report
        el.innerHTML += `
        <div style="margin-top:8px;padding:10px 14px;background:var(--bg-tile,var(--card-bg));border-radius:8px;border:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:16px;">&#128202;</span>
                <span style="font-size:13px;font-weight:600;color:var(--text);">Data Nerd View</span>
                <span style="font-size:10px;color:var(--text-muted);">Charts, trends &amp; deep analysis</span>
            </div>
            <button class="btn btn-primary btn-sm" onclick="dnOpen()">Open</button>
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
    const el = document.getElementById('cardBody_zones');
    try {
        // Fetch zone head GPM data in parallel with zones
        try {
            var allHeads = await api('/zone_heads?t=' + Date.now());
            window._hoZoneGpmMap = {};
            window._hoZoneGpmShow = {};
            window._hoZoneHeadCountShow = {};
            window._hoZoneHeadCount = {};
            for (var eid in allHeads) {
                if (allHeads[eid].total_gpm > 0) window._hoZoneGpmMap[eid] = allHeads[eid].total_gpm;
                if (allHeads[eid].show_gpm_on_card) window._hoZoneGpmShow[eid] = true;
                if (allHeads[eid].show_head_count_on_card) window._hoZoneHeadCountShow[eid] = true;
                if (allHeads[eid].heads && allHeads[eid].heads.length > 0) window._hoZoneHeadCount[eid] = allHeads[eid].heads.length;
            }
            window._hoZoneSprinklerCat = {};
            for (var eid2 in allHeads) {
                var catResult = getSprinklerCategories(allHeads[eid2].heads);
                if (catResult) window._hoZoneSprinklerCat[eid2] = catResult;
            }
        } catch(e) { window._hoZoneGpmMap = {}; window._hoZoneGpmShow = {}; window._hoZoneHeadCountShow = {}; window._hoZoneHeadCount = {}; window._hoZoneSprinklerCat = {}; }
        const data = await api('/zones');
        let zones = Array.isArray(data) ? data : (data.zones || []);
        // Filter by detected zone count (server already filters, but belt-and-suspenders)
        const maxZ = window._detectedZoneCount || 0;
        if (maxZ > 0) {
            zones = zones.filter(function(z) {
                const m = z.entity_id.match(/zone[_]?(\\d+)/i);
                return !m || parseInt(m[1]) <= maxZ;
            });
        }
        if (zones.length === 0) { el.innerHTML = '<div class="empty-state"><p>No zones found</p></div>'; return; }
        // Sort: normal zones first (by zone number), then Pump Start Relay / Master Valve at the end
        zones.sort(function(a, b) {
            var modes = window._zoneModes || {};
            var aNum = extractZoneNumber(a.entity_id, 'zone') || '0';
            var bNum = extractZoneNumber(b.entity_id, 'zone') || '0';
            var aMode = (modes[aNum] && modes[aNum].state || '').toLowerCase();
            var bMode = (modes[bNum] && modes[bNum].state || '').toLowerCase();
            var aSpecial = /pump|master|relay/.test(aMode) ? 1 : 0;
            var bSpecial = /pump|master|relay/.test(bMode) ? 1 : 0;
            if (aSpecial !== bSpecial) return aSpecial - bSpecial;
            return parseInt(aNum) - parseInt(bNum);
        });
        el.innerHTML = '<div class="tile-grid">' + zones.map(z => {
            const zId = z.name || z.entity_id;
            const isOn = z.state === 'on';
            const displayName = getZoneDisplayName(z);
            return `
            <div class="tile ${isOn ? 'active' : ''}">
                ${(function() {
                    var badges = '';
                    var hasGpm = window._hoZoneGpmShow && window._hoZoneGpmShow[z.entity_id] && window._hoZoneGpmMap && window._hoZoneGpmMap[z.entity_id];
                    var hasHeads = window._hoZoneHeadCountShow && window._hoZoneHeadCountShow[z.entity_id] && window._hoZoneHeadCount && window._hoZoneHeadCount[z.entity_id];
                    if (hasGpm || hasHeads) {
                        badges += '<div style="position:absolute;top:8px;right:10px;text-align:right;line-height:1.2;">';
                        if (hasGpm) {
                            badges += '<div><span style="font-size:14px;font-weight:700;color:var(--text-primary);">' + window._hoZoneGpmMap[z.entity_id].toFixed(1) + '</span><span style="font-size:10px;color:var(--text-secondary);margin-left:1px;">GPM</span></div>';
                        }
                        if (hasHeads) {
                            badges += '<div><span style="font-size:14px;font-weight:700;color:var(--text-primary);">' + window._hoZoneHeadCount[z.entity_id] + '</span><span style="font-size:10px;color:var(--text-secondary);margin-left:1px;">' + (window._hoZoneHeadCount[z.entity_id] === 1 ? 'head' : 'heads') + '</span></div>';
                        }
                        badges += '</div>';
                    }
                    return badges;
                })()}
                <div class="tile-name">
                    ${esc(displayName)}
                    <span style="cursor:pointer;font-size:20px;color:var(--color-primary);margin-left:6px;"
                          onclick="event.stopPropagation();renameZone(\\'${z.entity_id}\\')">&#9998;</span>
                    ${(function() {
                        var zn = extractZoneNumber(z.entity_id, 'zone');
                        var modes = window._zoneModes || {};
                        var mv = (zn && modes[zn]) ? (modes[zn].state || '').toLowerCase() : '';
                        if (/pump|relay/.test(mv)) {
                            return '<span style="cursor:pointer;font-size:20px;color:var(--color-info);margin-left:4px;" onclick="event.stopPropagation();showPumpSettingsModal()" title="Pump settings">&#9432;</span>';
                        }
                        if (/master|valve/.test(mv)) {
                            return '<span style="cursor:pointer;font-size:20px;color:var(--color-info);margin-left:4px;" onclick="event.stopPropagation();showWaterSettingsModal()" title="Water source settings">&#9432;</span>';
                        }
                        return '<span style="cursor:pointer;font-size:20px;color:var(--color-info);margin-left:4px;" onclick="event.stopPropagation();hoShowZoneDetailsModal(\\'' + z.entity_id + '\\', decodeURIComponent(\\'' + encodeURIComponent(displayName) + '\\'))" title="Zone head details">&#9432;</span>';
                    })()}
                </div>
                <div class="tile-state ${isOn ? 'on' : ''}">${isOn ? 'Running' : 'Off'}</div>
                <div class="tile-actions" style="flex-wrap:wrap;">
                    ${isOn
                        ? '<button class="btn btn-danger btn-sm" onclick="stopZone(\\'' + zId + '\\')">Stop</button>' +
                          '<span data-elapsed-since="' + (z.last_changed || '') + '" style="font-weight:700;color:var(--text-primary);font-size:13px;margin-left:6px;">' + _formatElapsed(z.last_changed) + '</span>'
                        : '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + zId + '\\', null)">Start</button>' +
                          '<span style="display:flex;align-items:center;gap:4px;margin-top:4px;"><input type="number" id="dur_' + zId + '" min="1" max="480" placeholder="min" style="width:60px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;">' +
                          '<button class="btn btn-primary btn-sm" onclick="startZone(\\'' + zId + '\\', document.getElementById(\\'dur_' + zId + '\\').value)">Timed</button></span>'
                    }
                </div>
                ${(function() {
                    var zoneNum = extractZoneNumber(z.entity_id, 'zone');
                    var modes = window._zoneModes || {};
                    if (zoneNum && modes[zoneNum]) {
                        var modeVal = (modes[zoneNum].state || '').toLowerCase();
                        if (/pump|relay/.test(modeVal)) {
                            return '<div class="tile-sprinkler-icon pump-valve">' + getSprinklerSvg('pump', 44) + '</div>';
                        }
                        if (/master|valve/.test(modeVal)) {
                            return '<div class="tile-sprinkler-icon pump-valve">' + getSprinklerSvg('valve', 44) + '</div>';
                        }
                    }
                    var catData = window._hoZoneSprinklerCat && window._hoZoneSprinklerCat[z.entity_id];
                    if (!catData) return '';
                    if (catData.single) {
                        return '<div class="tile-sprinkler-icon">' + getSprinklerSvg(catData.categories[0], 44) + '</div>';
                    } else {
                        return '<div class="tile-sprinkler-icon">' + getSprinklerSvg(catData.categories[0], 30) + getSprinklerSvg(catData.categories[1], 30) + '</div>';
                    }
                })()}
            </div>`;
        }).join('') + '</div>';
    } catch (e) {
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load zones: ' + esc(e.message) + '</div>';
    }
}

function _formatElapsed(isoDate) {
    if (!isoDate) return '';
    try {
        var diff = Math.max(0, Math.floor((Date.now() - new Date(isoDate).getTime()) / 1000));
        var h = Math.floor(diff / 3600);
        var m = Math.floor((diff % 3600) / 60);
        var s = diff % 60;
        if (h > 0) return h + 'h ' + m + 'm ' + s + 's';
        if (m > 0) return m + 'm ' + s + 's';
        return s + 's';
    } catch(e) { return ''; }
}
setInterval(function() {
    document.querySelectorAll('[data-elapsed-since]').forEach(function(el) {
        var since = el.getAttribute('data-elapsed-since');
        if (since) el.textContent = _formatElapsed(since);
    });
}, 1000);

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

// --- Uptime Formatting ---
function isUptimeSensor(sensor) {
    const eid = (sensor.entity_id || '').toLowerCase();
    const name = (sensor.friendly_name || sensor.name || '').toLowerCase();
    const dc = (sensor.device_class || '').toLowerCase();
    return (eid.includes('uptime') || name.includes('uptime'))
        && (dc === 'duration' || dc === 'timestamp' || ['s','d','h','min'].includes((sensor.unit_of_measurement || '').toLowerCase()));
}

function formatUptime(sensor) {
    if (!isUptimeSensor(sensor)) return null;
    let totalSec = 0;
    const dc = (sensor.device_class || '').toLowerCase();
    const unit = (sensor.unit_of_measurement || '').toLowerCase();
    if (dc === 'timestamp') {
        // State is an ISO timestamp of when the device started
        const started = new Date(sensor.state);
        if (isNaN(started.getTime())) return null;
        totalSec = Math.floor((Date.now() - started.getTime()) / 1000);
    } else {
        const raw = parseFloat(sensor.state);
        if (isNaN(raw)) return null;
        // Convert to seconds based on unit
        if (unit === 'd')        totalSec = Math.floor(raw * 86400);
        else if (unit === 'h')   totalSec = Math.floor(raw * 3600);
        else if (unit === 'min') totalSec = Math.floor(raw * 60);
        else                     totalSec = Math.floor(raw);
    }
    if (totalSec < 0) return null;

    const years = Math.floor(totalSec / 31536000); totalSec %= 31536000;
    const months = Math.floor(totalSec / 2592000); totalSec %= 2592000;
    const weeks = Math.floor(totalSec / 604800); totalSec %= 604800;
    const days = Math.floor(totalSec / 86400); totalSec %= 86400;
    const hours = Math.floor(totalSec / 3600); totalSec %= 3600;
    const mins = Math.floor(totalSec / 60);

    // Build parts, skipping leading zeros
    const parts = [];
    if (years)  parts.push({ val: years,  unit: 'y', label: years === 1 ? 'yr' : 'yrs' });
    if (months) parts.push({ val: months, unit: 'mo', label: months === 1 ? 'mo' : 'mos' });
    if (weeks)  parts.push({ val: weeks,  unit: 'w', label: weeks === 1 ? 'wk' : 'wks' });
    if (days)   parts.push({ val: days,   unit: 'd', label: days === 1 ? 'day' : 'days' });
    // Always show h/m once we have at least one part or if that's all there is
    parts.push({ val: hours, unit: 'h', label: 'hrs' });
    parts.push({ val: mins,  unit: 'm', label: 'min' });

    // Render as a compact segmented display
    let html = '<div style="display:flex;flex-wrap:wrap;gap:4px;align-items:baseline;">';
    for (const p of parts) {
        html += '<div style="text-align:center;">';
        html += '<span style="font-weight:700;font-size:15px;color:var(--text-primary);">' + p.val + '</span>';
        html += '<span style="font-size:10px;color:var(--text-muted);margin-left:1px;">' + p.label + '</span>';
        html += '</div>';
    }
    html += '</div>';
    return html;
}

function cleanSensorName(sensor) {
    let name = cleanEntityName(sensor.friendly_name || sensor.name, sensor.entity_id);
    // Strip leading device name prefix for uptime sensors
    // e.g. "Irrigation System Irrigation Controller Uptime" → "Irrigation Controller Uptime"
    if (isUptimeSensor(sensor)) {
        name = name.replace(/^Irrigation System\\s+/i, '');
    }
    return name;
}

function renderSensorValue(sensor) {
    const uptimeHtml = formatUptime(sensor);
    if (uptimeHtml) return uptimeHtml;
    return '<div class="tile-state">' + esc(sensor.state) + (sensor.unit_of_measurement ? ' ' + esc(sensor.unit_of_measurement) : '') + wifiSignalBadge(sensor) + '</div>';
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
    return ' <span style="font-weight:600;color:' + color + ';display:inline-flex;align-items:center;gap:2px;"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h.01"/><path d="M8.5 16.5a5 5 0 0 1 7 0"/><path d="M5 12.5a10 10 0 0 1 14 0"/><path d="M1.5 8.5a14 14 0 0 1 21 0"/></svg> ' + label + '</span>';
}

// --- Sensors ---
let _sensorGridBuilt = false;
async function loadSensors() {
    const el = document.getElementById('cardBody_sensors');
    try {
        const data = await api('/sensors');
        const allSensors = Array.isArray(data) ? data : (data.sensors || []);

        // Extract rain and expansion sensor entities into their own cards
        window._rainSensors = allSensors.filter(s => isRainEntity(s.entity_id));
        window._expansionSensors = allSensors.filter(s => isExpansionEntity(s.entity_id));
        renderRainSensorCard();
        renderExpansionCard();

        // Regular sensors (exclude rain + expansion)
        const sensors = allSensors.filter(s => !isRainEntity(s.entity_id) && !isExpansionEntity(s.entity_id));
        if (sensors.length === 0) { el.innerHTML = '<div class="empty-state"><p>No sensors found</p></div>'; _sensorGridBuilt = false; return; }

        // Build the tile grid once, then only update values
        const eids = sensors.map(s => s.entity_id).sort().join(',');
        const gridExists = _sensorGridBuilt && el.querySelector('.tile-grid');
        if (!gridExists || el.getAttribute('data-eids') !== eids) {
            // First load or sensor list changed — full build
            el.innerHTML = '<div class="tile-grid">' + sensors.map(s => {
                const eid = esc(s.entity_id);
                return '<div class="tile" data-eid="' + eid + '">' +
                    '<div class="tile-name">' + esc(cleanSensorName(s)) + '</div>' +
                    '<div class="tile-value">' + renderSensorValue(s) + '</div>' +
                '</div>';
            }).join('') + '</div>';
            el.setAttribute('data-eids', eids);
            _sensorGridBuilt = true;
        } else {
            // Targeted update — only change the value content of each tile
            for (const s of sensors) {
                const tile = el.querySelector('[data-eid="' + s.entity_id + '"]');
                if (!tile) continue;
                const valEl = tile.querySelector('.tile-value');
                if (!valEl) continue;
                const newHtml = renderSensorValue(s);
                if (valEl.innerHTML !== newHtml) {
                    valEl.innerHTML = newHtml;
                }
            }
        }
    } catch (e) {
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load sensors: ' + esc(e.message) + '</div>';
        _sensorGridBuilt = false;
    }
}

// --- Device Controls (also populates Schedule card) ---
async function loadControls() {
    const controlsEl = document.getElementById('cardBody_controls');
    const scheduleEl = document.getElementById('cardBody_schedule');
    try {
        const _cb = '?t=' + Date.now();
        const [data, durData, multData] = await Promise.all([
            api('/entities' + _cb),
            mapi('/durations' + _cb).catch(() => ({})),
            mapi('/multiplier' + _cb).catch(() => ({ combined_multiplier: 1.0, weather_multiplier: 1.0, moisture_multiplier: 1.0 })),
        ]);
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

        // Detect pump start relay zone and master valve zone
        window._pumpZoneEntity = null;
        window._masterValveEntity = null;
        for (const num in window._zoneModes) {
            const mode = (window._zoneModes[num].state || '').toLowerCase();
            if (/pump.*relay|pump\\s*start/i.test(mode)) {
                // Derive switch entity from mode entity:
                // select.irrigation_xxx_zone_N_mode -> switch.irrigation_xxx_zone_N
                const modeEid = window._zoneModes[num].entity.entity_id;
                window._pumpZoneEntity = modeEid.replace('select.', 'switch.').replace(/_mode$/, '');
            } else if (/master.*valve|valve.*master/i.test(mode)) {
                const modeEid = window._zoneModes[num].entity.entity_id;
                window._masterValveEntity = modeEid.replace('select.', 'switch.').replace(/_mode$/, '');
            }
        }
        // Auto-default to well water if pump relay detected and no water source set
        if (window._pumpZoneEntity) {
            try {
                var ws = await api('/water_settings?t=' + Date.now());
                if (!ws.water_source) {
                    ws.water_source = 'well';
                    ws.cost_per_1000_gal = 0;
                    await api('/water_settings', { method: 'PUT', body: JSON.stringify(ws) });
                }
            } catch(e) {}
        }
        // Always cache water settings (even if Est Gallons card is hidden)
        if (!window._cachedWaterSettings) {
            try {
                var wsC = await api('/water_settings?t=' + Date.now());
                if (wsC) window._cachedWaterSettings = wsC;
            } catch(e) {}
        }
        loadPumpMonitor();

        // Extract rain and expansion control entities into their own cards
        const rainControls = controlEntities.filter(e => isRainEntity(e.entity_id));
        const expansionControls = controlEntities.filter(e => isExpansionEntity(e.entity_id));
        const regularControls = controlEntities.filter(e => !isRainEntity(e.entity_id) && !isExpansionEntity(e.entity_id));
        window._rainControls = rainControls;
        window._expansionControls = expansionControls;
        renderRainSensorCard();
        renderExpansionCard();

        // Detect zone count from expansion sensor for zone filtering
        window._detectedZoneCount = 0;
        const expansionSensors = (window._expansionSensors || []);
        for (const es of expansionSensors) {
            if (/detected_zones/i.test(es.entity_id) && es.state) {
                const czm = es.state.match(/(\\d+)\\s*zones?/i);
                if (czm) window._detectedZoneCount = parseInt(czm[1]);
            }
        }

        // Extract auto_advance from system_controls and render in zone card header
        var autoAdvanceEntity = null;
        var filteredSystemControls = [];
        for (var sci = 0; sci < scheduleByCategory.system_controls.length; sci++) {
            var sc = scheduleByCategory.system_controls[sci];
            if (/auto_advance/i.test(sc.entity_id)) {
                autoAdvanceEntity = sc;
            } else {
                filteredSystemControls.push(sc);
            }
        }
        scheduleByCategory.system_controls = filteredSystemControls;
        var aaEl = document.getElementById('autoAdvanceToggle');
        if (autoAdvanceEntity && aaEl) {
            var aaOn = autoAdvanceEntity.state === 'on';
            aaEl.style.display = '';
            aaEl.innerHTML = '<div style="display:flex;align-items:center;gap:8px;">' +
                '<span style="font-size:13px;color:var(--text-secondary);">Auto Advance</span>' +
                '<button class="btn ' + (aaOn ? 'btn-primary' : 'btn-secondary') + ' btn-sm" ' +
                'onclick="setEntityValue(\\'' + autoAdvanceEntity.entity_id + '\\',\\'switch\\',' +
                '{state:\\'' + (aaOn ? 'off' : 'on') + '\\'});setTimeout(loadControls,500)">' +
                (aaOn ? 'On' : 'Off') + '</button></div>';
        } else if (aaEl) {
            aaEl.style.display = 'none';
        }

        // Render Schedule card (also populates window._pumpMasterZones)
        renderScheduleCard(scheduleByCategory, durData, multData);

        // Render Device Controls (excluding rain + expansion)
        {
            let html = '';
            // Zone Mode section at top (populated by renderScheduleCard — always includes highest zone)
            const pmZones = window._pumpMasterZones || [];
            if (pmZones.length > 0) {
                html += '<div style="margin-bottom:16px;"><div style="font-size:13px;font-weight:600;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">Zone Mode</div>';
                html += '<div class="tile-grid">';
                for (const pm of pmZones) {
                    const mode = pm.mode;
                    const modeVal = mode ? mode.state : '';
                    const modeEid = mode ? mode.entity_id : '';
                    const zNum = mode ? (modeEid.match(/zone[_]?(\\d+)/i) || [])[1] || '?' : '?';
                    const label = 'Zone ' + zNum;
                    const modeAttrs = mode ? (mode.attributes || {}) : {};
                    const modeOptions = modeAttrs.options || [];
                    const selId = 'pmmode_' + modeEid.replace(/[^a-zA-Z0-9]/g, '_');
                    const optionsHtml = modeOptions.map(o =>
                        '<option value="' + esc(o) + '"' + (o === modeVal ? ' selected' : '') + '>' + esc(o) + '</option>'
                    ).join('');
                    html += '<div class="tile">' +
                        '<div class="tile-name">' + esc(label) + '</div>' +
                        '<div class="tile-state" style="font-size:12px;color:var(--text-secondary);">' + esc(modeVal) + '</div>' +
                        '<div class="tile-actions">' +
                        '<select id="' + selId + '" style="padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;" ' +
                        'onchange="hoZoneModeChanged(\\'' + modeEid +
                        '\\',document.getElementById(\\'' + selId + '\\').value)">' +
                        optionsHtml + '</select>' +
                        '</div></div>';
                }
                html += '</div></div>';
            }
            if (regularControls.length === 0 && pmZones.length === 0) {
                controlsEl.innerHTML = '<div class="empty-state"><p>No device controls found</p></div>';
            } else {
                const groups = {};
                regularControls.forEach(e => {
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
        }

    } catch (e) {
        controlsEl.innerHTML = '<div style="color:var(--color-danger);">Failed to load controls: ' + esc(e.message) + '</div>';
        scheduleEl.innerHTML = '<div style="color:var(--color-danger);">Failed to load schedule: ' + esc(e.message) + '</div>';
    }
}

// --- Rain Sensor Card ---
function renderRainSensorCard() {
    const card = document.getElementById('rainSensorCard');
    const body = document.getElementById('cardBody_rain');
    const badge = document.getElementById('rainStatusBadge');
    const sensors = window._rainSensors || [];
    const controls = window._rainControls || [];
    const all = [...sensors, ...controls];
    if (all.length === 0) { card.style.display = 'none'; return; }
    card.style.display = 'block';

    // Find specific entities by pattern
    const findEntity = (list, pattern) => list.find(e => pattern.test((e.entity_id || '').toLowerCase()));
    const sensorEntity = findEntity(sensors, /rain_sensor$/) || findEntity(sensors, /rain_sensor[^_]/);
    const enabledEntity = findEntity(controls, /rain_sensor_enabled/);
    const typeEntity = findEntity(controls, /rain_sensor_type/);
    const delayEnabledEntity = findEntity(controls, /rain_delay_enabled/);
    const delayHoursEntity = findEntity(controls, /rain_delay_hours/);
    const delayActiveEntity = findEntity(sensors, /rain_delay_active/);

    // Status badge
    const isEnabled = enabledEntity && enabledEntity.state === 'on';
    const isRaining = sensorEntity && sensorEntity.state === 'on';
    const delayActive = delayActiveEntity && delayActiveEntity.state === 'on';
    if (!isEnabled) {
        badge.textContent = 'Disabled';
        badge.style.background = 'var(--bg-tile)';
        badge.style.color = 'var(--text-muted)';
    } else if (isRaining) {
        badge.textContent = 'Rain Detected';
        badge.style.background = 'var(--bg-danger-light)';
        badge.style.color = 'var(--text-danger-dark)';
    } else if (delayActive) {
        badge.textContent = 'Rain Delay';
        badge.style.background = 'var(--bg-warning)';
        badge.style.color = 'var(--text-warning)';
    } else {
        badge.textContent = 'Dry';
        badge.style.background = 'var(--bg-success-light)';
        badge.style.color = 'var(--text-success-dark)';
    }

    let html = '';

    // Rain sensor status banner
    if (sensorEntity) {
        const stateColor = isRaining ? 'var(--color-danger)' : 'var(--color-success)';
        const stateText = isRaining ? 'Rain Detected' : 'Dry';
        const bgColor = isRaining ? 'var(--bg-danger-light)' : 'var(--bg-success-light)';
        html += '<div style="display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:8px;margin-bottom:16px;background:' + bgColor + ';">' +
            '<div style="font-size:24px;">' + (isRaining ? '&#127783;&#65039;' : '&#9728;&#65039;') + '</div>' +
            '<div><div style="font-size:15px;font-weight:600;color:' + stateColor + ';">' + stateText + '</div>' +
            '<div style="font-size:12px;color:var(--text-muted);">Hardware rain sensor state</div></div></div>';
    }

    html += '<div class="tile-grid">';

    // Rain Sensor Enabled toggle
    if (enabledEntity) {
        const isOn = enabledEntity.state === 'on';
        html += '<div class="tile ' + (isOn ? 'active' : '') + '">' +
            '<div class="tile-name">Rain Sensor</div>' +
            '<div class="tile-state ' + (isOn ? 'on' : '') + '">' + (isOn ? 'Enabled' : 'Disabled') + '</div>' +
            '<div class="tile-actions">' +
            '<button class="btn ' + (isOn ? 'btn-danger' : 'btn-primary') + ' btn-sm" ' +
            'onclick="setEntityValue(\\'' + enabledEntity.entity_id + '\\',\\'switch\\',' +
            '{state:\\'' + (isOn ? 'off' : 'on') + '\\'})">' + (isOn ? 'Disable' : 'Enable') + '</button>' +
            '</div></div>';
    }

    // Rain Sensor Type selector
    if (typeEntity) {
        const options = (typeEntity.attributes && typeEntity.attributes.options) || [];
        const optionsHtml = options.map(o => '<option value="' + esc(o) + '"' + (o === typeEntity.state ? ' selected' : '') + '>' + esc(o) + '</option>').join('');
        html += '<div class="tile">' +
            '<div class="tile-name">Sensor Type</div>' +
            '<div class="tile-state">' + esc(typeEntity.state) + '</div>' +
            '<div class="tile-actions" style="flex-wrap:wrap;gap:4px;">' +
            '<select id="sel_rain_type" style="padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">' + optionsHtml + '</select>' +
            '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + typeEntity.entity_id + '\\',\\'select\\',{option:document.getElementById(\\'sel_rain_type\\').value})">Set</button>' +
            '</div></div>';
    }

    // Rain Delay Enabled toggle
    if (delayEnabledEntity) {
        const isOn = delayEnabledEntity.state === 'on';
        html += '<div class="tile ' + (isOn ? 'active' : '') + '">' +
            '<div class="tile-name">Rain Delay</div>' +
            '<div class="tile-state ' + (isOn ? 'on' : '') + '">' + (isOn ? 'Enabled' : 'Disabled') + '</div>' +
            '<div class="tile-actions">' +
            '<button class="btn ' + (isOn ? 'btn-danger' : 'btn-primary') + ' btn-sm" ' +
            'onclick="setEntityValue(\\'' + delayEnabledEntity.entity_id + '\\',\\'switch\\',' +
            '{state:\\'' + (isOn ? 'off' : 'on') + '\\'})">' + (isOn ? 'Disable' : 'Enable') + '</button>' +
            '</div></div>';
    }

    // Rain Delay Hours
    if (delayHoursEntity) {
        const attrs = delayHoursEntity.attributes || {};
        const min = attrs.min !== undefined ? attrs.min : 1;
        const max = attrs.max !== undefined ? attrs.max : 72;
        const step = attrs.step || 1;
        const unit = attrs.unit_of_measurement || 'h';
        html += '<div class="tile">' +
            '<div class="tile-name">Delay Duration</div>' +
            '<div class="tile-state">' + esc(delayHoursEntity.state) + ' ' + esc(unit) + '</div>' +
            '<div class="tile-actions" style="flex-wrap:wrap;gap:4px;">' +
            '<input type="number" id="num_rain_delay" value="' + esc(delayHoursEntity.state) + '" min="' + min + '" max="' + max + '" step="' + step + '" style="width:60px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">' +
            '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + delayHoursEntity.entity_id + '\\',\\'number\\',{value:parseFloat(document.getElementById(\\'num_rain_delay\\').value)})">Set</button>' +
            '</div></div>';
    }

    // Rain Delay Active status
    if (delayActiveEntity) {
        const isActive = delayActiveEntity.state === 'on';
        html += '<div class="tile ' + (isActive ? 'active' : '') + '">' +
            '<div class="tile-name">Rain Delay Active</div>' +
            '<div class="tile-state ' + (isActive ? 'on' : '') + '">' + (isActive ? 'Active' : 'Inactive') + '</div>' +
            '</div>';
    }

    html += '</div>';
    body.innerHTML = html;
}

// --- Expansion Board Card ---
function renderExpansionCard() {
    const card = document.getElementById('expansionCard');
    const body = document.getElementById('cardBody_expansion');
    const badge = document.getElementById('expansionStatusBadge');
    const sensors = window._expansionSensors || [];
    const controls = window._expansionControls || [];
    const all = [...sensors, ...controls];
    if (all.length === 0) { card.style.display = 'none'; return; }
    card.style.display = 'block';

    // Find specific entities
    const findEntity = (list, pattern) => list.find(e => pattern.test((e.entity_id || '').toLowerCase()));
    const detectedEntity = findEntity(sensors, /detected_zones/);
    const rescanEntity = findEntity(controls, /rescan_expansion/);

    // Parse detected zones text: "16 zones (0x20, 0x21)" or "8 zones (no expansion boards)"
    let zoneCount = 0;
    let boards = [];
    let noBoards = true;
    if (detectedEntity && detectedEntity.state) {
        const text = detectedEntity.state;
        const countMatch = text.match(/(\\d+)\\s*zones?/i);
        if (countMatch) zoneCount = parseInt(countMatch[1]);
        noBoards = /no expansion/i.test(text);
        if (!noBoards) {
            const addrMatch = text.match(/\\(([^)]+)\\)/);
            if (addrMatch) {
                boards = addrMatch[1].split(',').map(s => s.trim()).filter(s => s);
            }
        }
    }

    // Status badge
    if (noBoards) {
        badge.textContent = 'Main Board Only';
        badge.style.background = 'var(--bg-tile)';
        badge.style.color = 'var(--text-muted)';
    } else {
        badge.textContent = boards.length + ' Board' + (boards.length !== 1 ? 's' : '');
        badge.style.background = 'var(--bg-success-light)';
        badge.style.color = 'var(--text-success-dark)';
    }

    let html = '';

    // Zone count banner
    html += '<div style="display:flex;align-items:center;gap:10px;padding:12px 16px;border-radius:8px;margin-bottom:16px;background:var(--bg-tile);">' +
        '<div style="font-size:24px;">&#128268;</div>' +
        '<div><div style="font-size:15px;font-weight:600;color:var(--text-primary);">' + zoneCount + ' Zones Detected</div>' +
        '<div style="font-size:12px;color:var(--text-muted);">' + (noBoards ? 'No expansion boards connected' : boards.length + ' expansion board' + (boards.length !== 1 ? 's' : '') + ' connected') + '</div></div></div>';

    // Board tiles (if any)
    if (!noBoards && boards.length > 0) {
        html += '<div class="tile-grid">';
        boards.forEach((addr, i) => {
            const boardNum = i + 1;
            const startZone = 8 + (i * 8) + 1;
            const endZone = startZone + 7;
            html += '<div class="tile active">' +
                '<div class="tile-name">Expansion Board ' + boardNum + '</div>' +
                '<div class="tile-state on">' + esc(addr) + '</div>' +
                '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">Zones ' + startZone + '-' + endZone + '</div>' +
                '</div>';
        });
        html += '</div>';
    }

    // Rescan button
    if (rescanEntity) {
        html += '<div style="margin-top:12px;text-align:center;">' +
            '<button class="btn btn-secondary btn-sm" onclick="setEntityValue(\\'' + rescanEntity.entity_id + '\\',\\'button\\',{})">&#128260; Rescan Expansion Boards</button>' +
            '</div>';
    }

    body.innerHTML = html;
}

function renderScheduleCard(sched, durData, multData) {
    const el = document.getElementById('cardBody_schedule');
    // Skip full rebuild if user is actively editing an input inside the schedule card
    // (prevents cursor being kicked out mid-typing on the 30s refresh cycle)
    if (el.contains(document.activeElement) && (document.activeElement.tagName === 'INPUT' || document.activeElement.tagName === 'SELECT')) {
        return;
    }
    const { schedule_enable, day_switches, start_times, run_durations, repeat_cycles, zone_enables, zone_modes, system_controls } = sched;
    const adjDurations = (durData && durData.adjusted_durations) || {};
    const baseDurations = (durData && durData.base_durations) || {};
    const factorsActive = durData && durData.duration_adjustment_active;
    const liveWeatherMult = (multData && multData.weather_multiplier != null) ? multData.weather_multiplier : 1.0;
    const perZoneMult = (multData && multData.per_zone) || {};
    const moistureEnabled = multData && multData.moisture_enabled;
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

    // --- Apply Factors Toggle (rendered inline from durData, no separate API call) ---
    const afOn = durData && durData.duration_adjustment_active;
    var factorSummary = 'Automatically adjust run durations by weather and moisture factors';
    const perZoneKeys = Object.keys(perZoneMult);
    const anySkip = perZoneKeys.some(function(k) { return perZoneMult[k].skip; });
    if (liveWeatherMult !== 1.0 || perZoneKeys.length > 0) {
        var parts = [];
        if (liveWeatherMult !== 1.0) parts.push('Weather: ' + liveWeatherMult.toFixed(2) + 'x');
        if (perZoneKeys.length > 0) parts.push('Moisture: per-zone');
        if (anySkip) parts.push('Skip active on ' + perZoneKeys.filter(function(k) { return perZoneMult[k].skip; }).length + ' zone(s)');
        factorSummary = parts.join(' · ');
    }
    html += '<div style="display:flex;align-items:center;justify-content:space-between;' +
        'padding:12px 16px;border-radius:8px;margin-bottom:16px;background:' + (afOn ? 'var(--bg-active-tile)' : 'var(--bg-inactive-tile)') + ';">' +
        '<div><div style="font-size:14px;font-weight:600;color:' + (afOn ? 'var(--color-success)' : 'var(--text-secondary)') + ';">' +
        'Apply Factors to Schedule</div>' +
        '<div style="font-size:12px;color:var(--text-muted);">' + factorSummary + '</div></div>' +
        '<button class="btn ' + (afOn ? 'btn-danger' : 'btn-primary') + ' btn-sm" ' +
        'onclick="toggleApplyFactors(' + !afOn + ')">' +
        (afOn ? 'Disable' : 'Enable') + '</button></div>';

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
        var sortedZones = Object.keys(zoneMap).sort(function(a, b) {
            return parseInt(a) - parseInt(b);
        });
        // Filter by detected zone count (expansion board limit)
        const maxZones = window._detectedZoneCount || 0;
        if (maxZones > 0) {
            sortedZones = sortedZones.filter(function(zn) { return parseInt(zn) <= maxZones; });
        }
        // Separate pump/master valve zones — they go in Device Controls, not schedule
        // Always include the highest zone (6 or 8) since it's the configurable pump/valve zone
        var highestZone = sortedZones.length > 0 ? sortedZones[sortedZones.length - 1] : null;
        var pumpMasterZones = [];
        sortedZones = sortedZones.filter(function(zn) {
            var m = (zoneMap[zn].mode && zoneMap[zn].mode.state || '').toLowerCase();
            var isPumpValve = /pump|master|relay/.test(m);
            var isHighest = (zn === highestZone);
            if (isPumpValve || (isHighest && zoneMap[zn].mode)) {
                pumpMasterZones.push(zn);
                return false;
            }
            return true;
        });
        // Store for Device Controls card rendering
        window._pumpMasterZones = pumpMasterZones.map(function(zn) { return zoneMap[zn]; });
        const hasMode = sortedZones.some(zn => zoneMap[zn].mode);

        html += '<table class="zone-settings-table"><thead><tr>' +
            '<th>Zone</th>' + (hasMode ? '<th>Mode</th>' : '') +
            '<th>Schedule Enable</th><th>Run Duration</th></tr></thead><tbody>';
        for (const zn of sortedZones) {
            const { enable, duration, mode } = zoneMap[zn];
            const zoneLabel = getZoneLabel(zn);
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
                        'onchange="hoZoneModeChanged(\\'' + modeEid +
                        '\\',document.getElementById(\\'' + selId + '\\').value)">' +
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
            if (duration) {
                const attrs = duration.attributes || {};
                const unit = attrs.unit_of_measurement || 'min';
                const eid = duration.entity_id;
                const inputId = 'dur_sched_' + eid.replace(/[^a-zA-Z0-9]/g, '_');
                const adj = factorsActive ? adjDurations[eid] : null;
                const baseVal = adj ? String(adj.original) : duration.state;
                // Look up per-zone moisture multiplier for this zone number
                var zoneMoistMult = 1.0;
                var zoneSkip = false;
                var zoneCombined = liveWeatherMult;
                var zoneHasMoisture = false;
                for (var pzKey in perZoneMult) {
                    var pzMatch = pzKey.match(/zone[_]?(\\d+)/i);
                    if (pzMatch && pzMatch[1] === String(zn)) {
                        zoneMoistMult = perZoneMult[pzKey].moisture_multiplier || 1.0;
                        zoneSkip = perZoneMult[pzKey].skip || false;
                        zoneCombined = perZoneMult[pzKey].combined || liveWeatherMult;
                        zoneHasMoisture = true;
                        break;
                    }
                }
                if (!zoneHasMoisture) zoneCombined = liveWeatherMult;
                // Compute projected adjusted duration using per-zone multiplier
                var factorBadge = '';
                if ((adj && adj.skip) || zoneSkip) {
                    // Skip triggered — from applied factors or live moisture data
                    factorBadge = ' <span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;' +
                        'background:var(--bg-danger-light);color:var(--color-danger);">Skip Watering</span>';
                } else if (adj) {
                    // Factors are actively applied — show applied adjusted value
                    factorBadge = ' <span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;' +
                        'background:var(--bg-active-tile);color:' + (Math.abs(adj.combined_multiplier - 1.0) < 0.005 ? 'var(--color-success)' : 'var(--color-warning)') + ';">' +
                        adj.adjusted + ' ' + esc(unit) + ' (' + adj.combined_multiplier.toFixed(2) + 'x)</span>';
                } else if (zoneSkip) {
                    // Factors not applied but skip would trigger for THIS zone
                    factorBadge = ' <span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;' +
                        'background:var(--bg-tile);color:var(--color-danger);opacity:0.8;" title="Watering would be skipped if Apply Factors is enabled">Skip Watering</span>';
                } else if (Math.abs(zoneCombined - 1.0) >= 0.005) {
                    // Factors not applied but multiplier differs from 1.0 — show preview
                    var curVal = parseFloat(duration.state) || 0;
                    var projVal = Math.max(1, Math.round(curVal * zoneCombined));
                    var tooltipParts = 'W:' + liveWeatherMult.toFixed(2);
                    if (zoneHasMoisture) tooltipParts += ' × M:' + zoneMoistMult.toFixed(2);
                    factorBadge = ' <span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;' +
                        'background:var(--bg-tile);color:var(--color-warning);opacity:0.8;" title="Projected duration if Apply Factors is enabled (' +
                        tooltipParts + ')">' +
                        projVal + ' ' + esc(unit) + ' (' + zoneCombined.toFixed(2) + 'x)</span>';
                } else if (zoneHasMoisture) {
                    // Zone has moisture probe but multiplier is 1.0 — show probe-monitored indicator
                    factorBadge = ' <span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;' +
                        'background:var(--bg-tile);color:var(--text-muted);border:1px solid var(--border-light);" title="Moisture probe monitoring this zone (M:' + zoneMoistMult.toFixed(2) + 'x)">' +
                        zoneMoistMult.toFixed(2) + 'x 💧</span>';
                }
                html += '<td style="white-space:nowrap;"><input type="number" id="' + inputId + '" value="' + esc(baseVal) + '" ' +
                    'min="' + (attrs.min || 0) + '" max="' + (attrs.max || 999) + '" step="' + (attrs.step || 1) + '" ' +
                    'style="width:70px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;"> ' +
                    esc(unit) + ' ' +
                    '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid +
                    '\\',\\'number\\',{value:parseFloat(document.getElementById(\\'' + inputId + '\\').value)})">Set</button>' +
                    factorBadge + '</td>';
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

function cleanEntityName(friendlyName, entityId) {
    // HA often appends the device name to entity friendly names, e.g.
    // "Irrigation System Restart irrigation_controller" — strip it
    if (!friendlyName) return entityId || 'Unknown';
    var name = friendlyName;
    // Strip "Irrigation Controller XX:XX:XX:XX:XX:XX " prefix (device name with MAC)
    name = name.replace(/^Irrigation Controller\\s+[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}\\s+/i, '');
    const parts = name.split(' ');
    const last = parts[parts.length - 1];
    if (parts.length > 1 && last.includes('_') && entityId && entityId.includes(last)) {
        return parts.slice(0, -1).join(' ');
    }
    return name;
}

function renderControlTile(e) {
    const name = esc(cleanEntityName(e.friendly_name || e.name, e.entity_id));
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
            '<div class="tile-actions">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid + '\\',\\'button\\',{})">PRESS</button>' +
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

async function setEntityValue(entityId, domain, bodyObj, force) {
    try {
        var url = '/entities/' + entityId + '/set';
        if (force) url += '?force=true';
        var result = await api(url, {
            method: 'POST',
            body: JSON.stringify(bodyObj),
        });
        if (result && result.status === 'conflict' && result.conflicts && result.conflicts.length > 0) {
            _pendingForceEntity = { entityId: entityId, domain: domain, bodyObj: bodyObj };
            var html = _buildConflictModalHtml(result.conflicts);
            html += '<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px;">' +
                '<button class="btn btn-secondary" onclick="closeDynamicModal()">Cancel</button>' +
                '<button class="btn btn-primary" onclick="_forceEntitySet()">Apply Anyway</button></div>';
            showModal('Probe Wake Conflict', html, '480px');
            return;
        }
        showToast('Updated ' + entityId.split('.').pop());
        setTimeout(() => { loadControls(); loadSensors(); }, 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

async function hoZoneModeChanged(modeEntityId, newMode) {
    // Clear alias for this zone so mode name shows through
    var zoneEid = modeEntityId.replace('select.', 'switch.').replace(/_mode$/, '');
    var aliases = window._currentZoneAliases || {};
    if (aliases[zoneEid]) {
        delete aliases[zoneEid];
        window._currentZoneAliases = aliases;
        try {
            await api('/zone_aliases', {
                method: 'PUT',
                body: JSON.stringify({ zone_aliases: aliases }),
            });
        } catch(e) {}
    }
    setEntityValue(modeEntityId, 'select', {option: newMode});
}

// --- History ---
async function loadHistory() {
    const el = document.getElementById('cardBody_history');
    try {
        const hoursRaw = document.getElementById('historyRange') ? document.getElementById('historyRange').value : '24';
        const hours = parseInt(hoursRaw, 10) || 24;
        // Fetch run history and current probe names in parallel
        const [data, probeNameMap] = await Promise.all([
            api('/history/runs?hours=' + hours),
            mapi('/probes').then(pd => {
                const m = {};
                for (const [pid, p] of Object.entries(pd.probes || {})) {
                    m[pid] = p.display_name || pid;
                }
                return m;
            }).catch(() => ({})),
        ]);
        // Filter out bare OFF/closed events and probe events (shown in Probe History)
        const zoneFilter = (document.getElementById('historyZoneFilter') || {}).value || '';
        const allEvents = (data.events || []).filter(e => {
            // Exclude probe events — they go in Probe History section
            if (e.source === 'moisture_probe') return false;
            if ((e.state === 'off' || e.state === 'closed') && !e.duration_seconds
                && (!e.source || e.source === 'schedule' || e.source === 'unknown')) return false;
            return true;
        });
        // Populate zone filter dropdown
        const zoneSelect = document.getElementById('historyZoneFilter');
        if (zoneSelect) {
            const zoneSet = new Set();
            allEvents.forEach(e => { if (e.entity_id) zoneSet.add(e.entity_id); });
            const zones = Array.from(zoneSet).sort((a, b) => {
                const na = parseInt((a.match(/zone[_]?(\\d+)/i) || [])[1]) || 999;
                const nb = parseInt((b.match(/zone[_]?(\\d+)/i) || [])[1]) || 999;
                return na - nb;
            });
            const prev = zoneSelect.value;
            zoneSelect.innerHTML = '<option value="">All Zones</option>' + zones.map(z => {
                const num = (z.match(/zone[_]?(\\d+)/i) || [])[1] || z;
                return '<option value="' + esc(z) + '"' + (z === prev ? ' selected' : '') + '>Zone ' + num + '</option>';
            }).join('');
        }
        // Apply zone filter
        const events = zoneFilter ? allEvents.filter(e => e.entity_id === zoneFilter) : allEvents;
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

        // Determine if any event has probe (moisture) data — show columns only if so
        const hasProbeData = events.some(e => e.moisture && e.moisture.moisture_multiplier != null);
        const hasSoilReadings = events.some(e => e.moisture && e.moisture.sensor_readings && (e.moisture.sensor_readings.T != null || e.moisture.sensor_readings.M != null || e.moisture.sensor_readings.B != null));

        // Determine if any event's zone has GPM data configured
        const gpmMap = window._hoZoneGpmMap || {};
        const hasGpmData = events.some(e => gpmMap[e.entity_id] > 0);
        // Check if any event has water savings data
        const hasWaterSaved = events.some(e => e.water_saved_gallons > 0 || e.water_saved_minutes > 0);

        el.innerHTML = weatherSummary +
            '<table style="width:100%;font-size:13px;border-collapse:collapse;"><thead><tr style="text-align:left;border-bottom:2px solid var(--border-light);"><th style="padding:6px;">Zone</th><th style="padding:6px;">State</th><th style="padding:6px;">Time</th><th style="padding:6px;">Duration</th>' +
            (hasGpmData ? '<th style="padding:6px;">GPM</th><th style="padding:6px;">Est. Gallons</th>' : '') +
            (hasWaterSaved ? '<th style="padding:6px;color:var(--color-success);">Water Saved</th>' : '') +
            '<th style="padding:6px;">Moisture Factor</th>' +
            (hasSoilReadings ? '<th style="padding:6px;">Soil Moisture</th>' : '') +
            '<th style="padding:6px;">Weather</th></tr></thead><tbody>' +
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
                // Moisture Factor column — show for any event that has moisture data
                let mFactorCell = '<span style="color:var(--text-disabled);">—</span>';
                {
                    const mo = e.moisture || {};
                    const mMult = mo.moisture_multiplier != null ? mo.moisture_multiplier : null;
                    if (e.state === 'skip') {
                        mFactorCell = '<span style="color:var(--color-danger);font-weight:600;">Skip</span>';
                    } else if (mMult != null) {
                        if (mMult === 0) {
                            mFactorCell = '<span style="color:var(--color-danger);font-weight:600;">Skip</span>';
                        } else {
                            const fc = mMult === 1.0 ? 'var(--color-success)' : mMult < 1 ? 'var(--color-warning)' : 'var(--color-danger)';
                            mFactorCell = '<span style="color:' + fc + ';font-weight:600;">' + mMult + 'x</span>';
                        }
                    }
                }
                // Soil Moisture column — show T/M/B sensor readings
                let soilCell = '<span style="color:var(--text-disabled);">—</span>';
                {
                    const mo = e.moisture || {};
                    const sr = mo.sensor_readings || {};
                    const lines = [];
                    if (sr.T != null) lines.push('<span style="color:var(--text-muted);">T:</span> ' + sr.T + '%');
                    if (sr.M != null) lines.push('<span style="color:var(--text-muted);">M:</span> ' + sr.M + '%');
                    if (sr.B != null) lines.push('<span style="color:var(--text-muted);">B:</span> ' + sr.B + '%');
                    if (lines.length > 0) {
                        soilCell = '<div style="font-size:12px;line-height:1.4;">' + lines.join('<br>') + '</div>';
                    }
                }
                const srcLabel = e.source && e.source !== 'schedule' && e.source !== 'moisture_probe' ? '<div style="font-size:10px;color:var(--text-placeholder);">' + esc(e.source) + '</div>' : '';
                // State display: handle skip, probe wake, and moisture skip events
                let stateCell;
                let isProbeEvent = e.source === 'moisture_probe';
                if (e.state === 'scheduled_wake') {
                    stateCell = '<span style="color:var(--color-warning);font-weight:600;">Scheduled Wake</span>';
                } else if (e.state === 'probe_wake') {
                    stateCell = '<span style="color:var(--color-link);font-weight:600;">Awake</span>';
                } else if (e.state === 'moisture_skip') {
                    stateCell = '<span style="color:var(--color-danger);font-weight:600;">Skipped</span>';
                    if (e.mid_sensor_pct != null) {
                        stateCell += '<div style="font-size:10px;color:var(--text-muted);">Mid: ' + e.mid_sensor_pct + '%</div>';
                    }
                } else if (e.state === 'skip') {
                    stateCell = '<span style="color:var(--color-danger);font-weight:600;">Skipped</span><br><span style="color:var(--text-disabled);font-size:11px;">OFF</span>';
                } else if (e.state === 'on' || e.state === 'open') {
                    stateCell = '<span style="color:var(--color-success);">ON</span>';
                } else {
                    stateCell = '<span style="color:var(--text-disabled);">OFF</span>';
                }
                // Water Saved cell — shows gallons saved, or time saved if no GPM
                let waterSavedCell = '<span style="color:var(--text-disabled);">—</span>';
                if (e.water_saved_gallons > 0) {
                    var saveSrc = e.water_saved_source === 'moisture_skip' || e.water_saved_source === 'moisture_cutoff' ? 'Moisture' : e.water_saved_source === 'weather_pause' || e.water_saved_source === 'pause_enforced' ? 'Weather' : '';
                    waterSavedCell = '<span style="color:var(--color-success);font-weight:600;">&#x1F4A7; ' + e.water_saved_gallons.toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits:1}) + ' gal</span>';
                    if (saveSrc) waterSavedCell += '<div style="font-size:10px;color:var(--text-muted);">' + saveSrc + '</div>';
                } else if (e.water_saved_minutes > 0 && e.water_saved_no_gpm) {
                    waterSavedCell = '<span style="color:var(--color-warning);">' + e.water_saved_minutes.toFixed(1) + ' min</span><div style="font-size:10px;color:var(--text-muted);">No GPM set</div>';
                } else if (e.water_saved_minutes > 0) {
                    waterSavedCell = '<span style="color:var(--color-success);font-weight:600;">' + e.water_saved_minutes.toFixed(1) + ' min saved</span>';
                }
                // Zone name display — probe events resolve current probe name
                let zoneDisplay;
                if (isProbeEvent) {
                    // Use current probe display_name from probeNameMap, falling back to stored name
                    const currentName = (e.probe_id && probeNameMap[e.probe_id]) || e.probe_name || e.probe_id || '';
                    // Replace "Probe N" prefix in zone_name with the current display name
                    let text = e.zone_name || e.skip_text || currentName;
                    if (e.probe_id && probeNameMap[e.probe_id]) {
                        text = text.replace(/^Probe\\s*\\d+/i, probeNameMap[e.probe_id]);
                    }
                    zoneDisplay = esc(text);
                } else {
                    zoneDisplay = esc(resolveZoneName(e.entity_id, e.zone_name));
                }
                // GPM and Estimated Gallons cells
                let gpmCell = '-';
                let estGalCell = '-';
                if (hasGpmData && !isProbeEvent) {
                    const zGpm = gpmMap[e.entity_id];
                    if (zGpm > 0) {
                        gpmCell = zGpm.toFixed(1);
                        // duration_seconds is set on OFF events (calculated from ON→OFF span)
                        if (e.duration_seconds > 0) {
                            const gal = (e.duration_seconds / 60) * zGpm;
                            estGalCell = '<span style="font-weight:600;">' + gal.toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits:1}) + '</span>';
                        }
                    }
                }
                return `<tr style="border-bottom:1px solid var(--border-row);${e.state === 'skip' || e.state === 'moisture_skip' ? 'opacity:0.7;' : ''}${isProbeEvent ? 'background:var(--bg-tile);' : ''}">
                <td style="padding:6px;">${zoneDisplay}${srcLabel}</td>
                <td style="padding:6px;">${stateCell}</td>
                <td style="padding:6px;">${formatTime(e.timestamp)}</td>
                <td style="padding:6px;">${e.duration_seconds ? Math.round(e.duration_seconds / 60) + ' min' : '-'}</td>
                ${hasGpmData ? '<td style="padding:6px;">' + gpmCell + '</td><td style="padding:6px;">' + estGalCell + '</td>' : ''}
                ${hasWaterSaved ? '<td style="padding:6px;">' + waterSavedCell + '</td>' : ''}
                <td style="padding:6px;font-size:12px;">${mFactorCell}</td>
                ${hasSoilReadings ? '<td style="padding:6px;font-size:12px;">' + soilCell + '</td>' : ''}
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
        const mon = d.toLocaleDateString('en-US', {month:'short'});
        const day = d.getDate();
        const yr = String(d.getFullYear()).slice(-2);
        const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        return mon + ' ' + day + '-' + yr + ' ' + time;
    } catch { return ts; }
}

// --- Estimated Gallons Card ---
async function loadEstGallons() {
    const card = document.getElementById('estGallonsCard');
    const el = document.getElementById('cardBody_gallons');
    const gpmMap = window._hoZoneGpmMap || {};
    // Hide card if no zones have GPM data
    if (Object.keys(gpmMap).length === 0) { card.style.display = 'none'; return; }
    try {
        const hoursRaw = document.getElementById('gallonsRange') ? document.getElementById('gallonsRange').value : '24';
        const hours = parseInt(hoursRaw, 10) || 24;
        const data = await api('/history/runs?hours=' + hours);
        const events = data.events || [];
        // Filter to events with duration and GPM (duration_seconds is set on OFF events)
        const relevant = events.filter(e => e.duration_seconds > 0 && gpmMap[e.entity_id]);
        // Also collect water_saved_gallons from all events
        const savingsEvents = events.filter(e => e.water_saved_gallons > 0);
        const hasAnyData = relevant.length > 0 || savingsEvents.length > 0;
        if (!hasAnyData) {
            card.style.display = '';
            el.innerHTML = '<div class="empty-state"><p>No water usage data for the selected period</p></div>';
            return;
        }
        // Aggregate per zone
        const zoneGallons = {};
        const zoneMinutes = {};
        const zoneNames = {};
        relevant.forEach(e => {
            const gpm = gpmMap[e.entity_id] || 0;
            const mins = e.duration_seconds / 60;
            const gal = mins * gpm;
            if (!zoneGallons[e.entity_id]) zoneGallons[e.entity_id] = 0;
            if (!zoneMinutes[e.entity_id]) zoneMinutes[e.entity_id] = 0;
            zoneGallons[e.entity_id] += gal;
            zoneMinutes[e.entity_id] += mins;
            if (!zoneNames[e.entity_id]) zoneNames[e.entity_id] = resolveZoneName(e.entity_id, e.zone_name);
        });
        const totalGal = Object.values(zoneGallons).reduce((a, b) => a + b, 0);
        // Aggregate savings per zone
        const zoneSaved = {};
        var totalSaved = 0;
        savingsEvents.forEach(e => {
            if (!zoneSaved[e.entity_id]) zoneSaved[e.entity_id] = 0;
            zoneSaved[e.entity_id] += e.water_saved_gallons;
            totalSaved += e.water_saved_gallons;
            if (!zoneNames[e.entity_id]) zoneNames[e.entity_id] = resolveZoneName(e.entity_id, e.zone_name);
        });
        // Sort zones by gallons desc
        const allZoneIds = [...new Set([...Object.keys(zoneGallons), ...Object.keys(zoneSaved)])];
        const sorted = allZoneIds.sort((a, b) => (zoneGallons[b] || 0) - (zoneGallons[a] || 0));
        // Fetch water settings for cost display
        var waterSettings = null;
        try { waterSettings = await api('/water_settings?t=' + Date.now()); } catch(e) {}
        if (waterSettings) window._cachedWaterSettings = waterSettings;
        const hasCost = waterSettings && waterSettings.cost_per_1000_gal > 0 &&
            (waterSettings.water_source === 'city' || waterSettings.water_source === 'reclaimed');
        const costPer1000 = hasCost ? waterSettings.cost_per_1000_gal : 0;
        // Build summary-only HTML — centered layout
        let html = '<div style="display:flex;flex-direction:column;align-items:center;padding:8px 0;">';
        html += '<div style="display:flex;gap:16px;flex-wrap:wrap;justify-content:center;margin-bottom:12px;">';
        // --- Used column ---
        html += '<div style="text-align:center;flex:1;min-width:120px;">' +
            '<div style="font-size:32px;font-weight:700;color:var(--text-primary);">' + totalGal.toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits:1}) + '</div>' +
            '<div style="font-size:13px;color:var(--text-muted);">est. gallons used</div>';
        if (hasCost) {
            var waterCost = (totalGal / 1000) * costPer1000;
            html += '<div style="font-size:15px;color:var(--text-secondary);font-weight:600;margin-top:4px;">$' +
                waterCost.toFixed(2) + ' est. cost</div>';
        }
        html += '</div>';
        // --- Saved column ---
        html += '<div style="text-align:center;flex:1;min-width:120px;">' +
            '<div style="font-size:32px;font-weight:700;color:var(--color-success);">' + (totalSaved > 0 ? totalSaved.toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits:1}) : '-') + '</div>' +
            '<div style="font-size:13px;color:var(--color-success);">&#x1F4A7; est. gallons saved</div>';
        if (hasCost && totalSaved > 0) {
            var savedCost = (totalSaved / 1000) * costPer1000;
            html += '<div style="font-size:15px;color:var(--color-success);font-weight:600;margin-top:4px;">$' +
                savedCost.toFixed(2) + ' est. savings</div>';
        }
        html += '</div>';
        html += '</div>';
        // Water source badge + pressure
        var infoLine = [];
        if (waterSettings && waterSettings.water_source) {
            var waterSrcLabel = {city:'City Water', reclaimed:'Reclaimed Water', well:'Well Water'}[waterSettings.water_source] || '';
            if (waterSrcLabel) infoLine.push(esc(waterSrcLabel));
        }
        if (waterSettings && waterSettings.pressure_psi && !window._pumpZoneEntity) {
            var wBar = (waterSettings.pressure_psi * 0.0689476).toFixed(1);
            infoLine.push(waterSettings.pressure_psi + ' PSI (' + wBar + ' bar)');
        }
        if (infoLine.length > 0) {
            html += '<div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">' + infoLine.join(' &bull; ') + '</div>';
        }
        // View Zone Details button
        html += '<div style="margin-top:8px;"><button class="btn btn-secondary btn-sm" onclick="openGallonsDetailModal()">View Zone Details</button></div>';
        html += '</div>';  // close outer centering wrapper
        // Store zone data for the modal
        window._gallonsModalData = { sorted: sorted, zoneNames: zoneNames, zoneMinutes: zoneMinutes, zoneGallons: zoneGallons, zoneSaved: zoneSaved, gpmMap: gpmMap, totalGal: totalGal, totalSaved: totalSaved, costPer1000: costPer1000, hasCost: hasCost };
        card.style.display = '';
        el.innerHTML = html;
    } catch (e) {
        card.style.display = '';
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load water usage: ' + esc(e.message) + '</div>';
    }
}

function openGallonsDetailModal() {
    const d = window._gallonsModalData;
    if (!d) return;
    // Summary header — side by side for used and saved
    let html = '<div style="display:flex;gap:16px;flex-wrap:wrap;justify-content:center;margin-bottom:16px;">';
    html += '<div style="text-align:center;flex:1;min-width:100px;">' +
        '<div style="font-size:28px;font-weight:700;color:var(--text-primary);">' + d.totalGal.toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits:1}) + '</div>' +
        '<div style="font-size:13px;color:var(--text-muted);">est. gallons used</div>';
    if (d.hasCost) {
        html += '<div style="font-size:14px;color:var(--text-secondary);font-weight:600;margin-top:2px;">$' + ((d.totalGal / 1000) * d.costPer1000).toFixed(2) + '</div>';
    }
    html += '</div>';
    html += '<div style="text-align:center;flex:1;min-width:100px;">' +
        '<div style="font-size:28px;font-weight:700;color:var(--color-success);">' + (d.totalSaved > 0 ? d.totalSaved.toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits:1}) : '-') + '</div>' +
        '<div style="font-size:13px;color:var(--color-success);">&#x1F4A7; est. gallons saved</div>';
    if (d.hasCost && d.totalSaved > 0) {
        html += '<div style="font-size:14px;color:var(--color-success);font-weight:600;margin-top:2px;">$' + ((d.totalSaved / 1000) * d.costPer1000).toFixed(2) + ' saved</div>';
    }
    html += '</div>';
    html += '</div>';
    // Zone breakdown table — always show Saved column
    html += '<table style="width:100%;font-size:13px;border-collapse:collapse;">' +
        '<thead><tr style="text-align:left;border-bottom:2px solid var(--border-light);">' +
        '<th style="padding:6px 8px;">Zone</th>' +
        '<th style="padding:6px 8px;text-align:right;">Time</th>' +
        '<th style="padding:6px 8px;text-align:right;">Gallons</th>' +
        '<th style="padding:6px 8px;text-align:right;color:var(--color-success);">Saved</th>' +
        '<th style="padding:6px 8px;text-align:right;">GPM</th></tr></thead><tbody>';
    d.sorted.forEach(function(eid) {
        const totalMins = Math.round(d.zoneMinutes[eid] || 0);
        const used = d.zoneGallons[eid] || 0;
        const saved = (d.zoneSaved && d.zoneSaved[eid]) || 0;
        html += '<tr style="border-bottom:1px solid var(--border-row);">' +
            '<td style="padding:6px 8px;">' + esc(d.zoneNames[eid] || eid) + '</td>' +
            '<td style="padding:6px 8px;text-align:right;">' + totalMins + ' min</td>' +
            '<td style="padding:6px 8px;text-align:right;font-weight:600;">' + used.toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits:1}) + '</td>' +
            '<td style="padding:6px 8px;text-align:right;color:var(--color-success);font-weight:600;">' + (saved > 0 ? saved.toLocaleString(undefined, {minimumFractionDigits:1, maximumFractionDigits:1}) : '-') + '</td>' +
            '<td style="padding:6px 8px;text-align:right;color:var(--text-muted);">' + (d.gpmMap[eid] || 0).toFixed(1) + '</td>' +
            '</tr>';
    });
    // Cost totals row
    if (d.hasCost) {
        const usedCost = (d.totalGal / 1000) * d.costPer1000;
        const savedCost = (d.totalSaved / 1000) * d.costPer1000;
        html += '<tr style="border-top:2px solid var(--border-light);font-weight:700;">' +
            '<td style="padding:8px 8px;">Total</td>' +
            '<td></td>' +
            '<td style="padding:8px 8px;text-align:right;">$' + usedCost.toFixed(2) + '</td>' +
            '<td style="padding:8px 8px;text-align:right;color:var(--color-success);">$' + (d.totalSaved > 0 ? savedCost.toFixed(2) : '-') + '</td>' +
            '<td></td></tr>';
    }
    html += '</tbody></table>';
    document.getElementById('gallonsDetailBody').innerHTML = html;
    document.getElementById('gallonsDetailModal').style.display = 'flex';
}

function closeGallonsDetailModal() {
    document.getElementById('gallonsDetailModal').style.display = 'none';
}

// --- Pump Monitor ---

function _pumpStatTile(label, value, unit) {
    return '<div style="text-align:center;background:var(--bg-tile);border-radius:8px;padding:12px 8px;">' +
        '<div style="font-size:22px;font-weight:700;color:var(--text-primary);">' + value +
        (unit ? '<span style="font-size:13px;font-weight:400;color:var(--text-muted);"> ' + unit + '</span>' : '') +
        '</div>' +
        '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">' + label + '</div></div>';
}

async function loadPumpMonitor() {
    var card = document.getElementById('pumpMonitorCard');
    var row = document.getElementById('gallonsPumpRow');
    if (!card || !row) return;
    if (!window._pumpZoneEntity) {
        card.style.display = 'none';
        row.style.display = 'block';
        return;
    }
    card.style.display = '';
    row.style.display = 'flex';

    // Auto-save pump entity if not yet configured
    try {
        var settings = await api('/pump_settings?t=' + Date.now());
        if (!settings.pump_entity_id || settings.pump_entity_id !== window._pumpZoneEntity) {
            settings.pump_entity_id = window._pumpZoneEntity;
            await api('/pump_settings', { method: 'PUT', body: JSON.stringify(settings) });
        }
    } catch(e) {}

    var el = document.getElementById('cardBody_pump');
    if (!el) return;
    try {
        var hours = document.getElementById('pumpRange') ? document.getElementById('pumpRange').value : '720';
        var stats = await api('/pump_stats?hours=' + hours + '&t=' + Date.now());
        var pSettings = await api('/pump_settings?t=' + Date.now());

        // Cache pump settings for head pressure propagation
        window._cachedPumpSettings = pSettings;

        var html = '';
        // 2x2 stat grid
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px;">';
        html += _pumpStatTile('Total Cycles', stats.cycles || 0, '');
        html += _pumpStatTile('Run Hours', (stats.run_hours || 0).toFixed(1), 'hrs');
        html += _pumpStatTile('Power Used', (stats.total_kwh || 0).toFixed(1), 'kWh');
        html += _pumpStatTile('Est. Cost', '$' + (stats.estimated_cost || 0).toFixed(2), '');
        html += '</div>';

        // Pump info line
        var brand = pSettings.brand || 'Unknown';
        var pModel = pSettings.model || '';
        var brandModel = pModel ? brand + ' ' + pModel : brand;
        var hp = pSettings.hp ? pSettings.hp + ' HP' : (pSettings.kw ? pSettings.kw + ' kW' : 'Not configured');
        html += '<div style="font-size:12px;color:var(--text-muted);text-align:center;">';
        html += esc(brandModel) + ' &bull; ' + esc(String(hp)) + ' &bull; ' + (pSettings.voltage || 240) + 'V';
        if (pSettings.pressure_psi) {
            var pBar = (pSettings.pressure_psi * 0.0689476).toFixed(1);
            html += ' &bull; ' + pSettings.pressure_psi + ' PSI (' + pBar + ' bar)';
        }
        if (pSettings.year_installed) {
            var pumpAge = new Date().getFullYear() - parseInt(pSettings.year_installed);
            if (pumpAge >= 0) html += ' &bull; ' + pumpAge + (pumpAge === 1 ? ' year old' : ' years old');
        }
        html += '</div>';

        el.innerHTML = html;
    } catch(e) {
        el.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:20px;">Configure pump settings with the \\u2699\\ufe0f button</div>';
    }
}

var PUMP_DATABASE = [
    {brand:'Berkeley',models:[
        {model:'LTHH',display:'LTHH 1.5HP Centrifugal',pump_type:'above_ground',hp:1.5,kw:1.12,voltage:230,pressure_psi:35,max_gpm:64,max_head_ft:80},
        {model:'LTH-5',display:'LTH-5 5HP Centrifugal',pump_type:'above_ground',hp:5.0,kw:3.73,voltage:230,pressure_psi:50,max_gpm:162,max_head_ft:115},
        {model:'B1.5TPMS',display:'B-Series 10HP Commercial',pump_type:'above_ground',hp:10.0,kw:7.46,voltage:230,pressure_psi:65,max_gpm:202,max_head_ft:150}
    ]},
    {brand:'Davey',models:[
        {model:'XJ25P',display:'XJ25P Centrifugal 0.6HP',pump_type:'above_ground',hp:0.6,kw:0.45,voltage:230,pressure_psi:42,max_gpm:15,max_head_ft:97},
        {model:'XJ35P',display:'XJ35P Centrifugal 0.75HP',pump_type:'above_ground',hp:0.75,kw:0.56,voltage:230,pressure_psi:50,max_gpm:18,max_head_ft:115},
        {model:'XJ50P',display:'XJ50P Centrifugal 1.0HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:230,pressure_psi:56,max_gpm:22,max_head_ft:130},
        {model:'Torrium2',display:'Torrium2 Variable Speed',pump_type:'above_ground',hp:0.75,kw:0.55,voltage:230,pressure_psi:60,max_gpm:18,max_head_ft:138}
    ]},
    {brand:'Flotec',models:[
        {model:'FP4012',display:'FP4012 Shallow Well 0.5HP',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:55,max_gpm:8,max_head_ft:130},
        {model:'FP4112',display:'FP4112 Cast Iron Shallow 0.5HP',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:56,max_gpm:9,max_head_ft:129},
        {model:'FP4212',display:'FP4212 Convertible 0.5HP',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:60,max_gpm:8,max_head_ft:162},
        {model:'FP5172',display:'FP5172 Submersible 0.75HP',pump_type:'submersible',hp:0.75,kw:0.56,voltage:230,pressure_psi:60,max_gpm:10,max_head_ft:147}
    ]},
    {brand:'Franklin Electric',models:[
        {model:'SubDrive-10',display:'SubDrive 0.75HP 10GPM',pump_type:'submersible',hp:0.75,kw:0.56,voltage:230,pressure_psi:60,max_gpm:10,max_head_ft:200},
        {model:'SubDrive-25',display:'SubDrive 1.5HP 25GPM',pump_type:'submersible',hp:1.5,kw:1.12,voltage:230,pressure_psi:80,max_gpm:25,max_head_ft:300},
        {model:'SubDrive-35',display:'SubDrive 1.5HP 35GPM',pump_type:'submersible',hp:1.5,kw:1.12,voltage:230,pressure_psi:65,max_gpm:35,max_head_ft:250},
        {model:'FPS-4400-10',display:'FPS 4400 1HP 10GPM Sub',pump_type:'submersible',hp:1.0,kw:0.75,voltage:230,pressure_psi:65,max_gpm:10,max_head_ft:250},
        {model:'FPS-4400-20',display:'FPS 4400 1.5HP 20GPM Sub',pump_type:'submersible',hp:1.5,kw:1.12,voltage:230,pressure_psi:70,max_gpm:20,max_head_ft:300},
        {model:'FPS-4400-35',display:'FPS 4400 3HP 35GPM Sub',pump_type:'submersible',hp:3.0,kw:2.24,voltage:230,pressure_psi:85,max_gpm:35,max_head_ft:400},
        {model:'BT4-10S4',display:'BT4 Inline Booster 1HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:230,pressure_psi:100,max_gpm:7,max_head_ft:410}
    ]},
    {brand:'Goulds',models:[
        {model:'J5S',display:'J5S Shallow Well 0.5HP',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:50,max_gpm:15,max_head_ft:110},
        {model:'J7S',display:'J7S Shallow Well 0.75HP',pump_type:'above_ground',hp:0.75,kw:0.56,voltage:115,pressure_psi:55,max_gpm:20,max_head_ft:130},
        {model:'J10S',display:'J10S Shallow Well 1.0HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:230,pressure_psi:63,max_gpm:23,max_head_ft:145},
        {model:'J15S',display:'J15S Shallow Well 1.5HP',pump_type:'above_ground',hp:1.5,kw:1.12,voltage:230,pressure_psi:70,max_gpm:29,max_head_ft:165},
        {model:'J5',display:'J5 Convertible 0.5HP',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:50,max_gpm:12,max_head_ft:150},
        {model:'10GS05',display:'10GS05 Sub 0.5HP 10GPM',pump_type:'submersible',hp:0.5,kw:0.37,voltage:230,pressure_psi:40,max_gpm:10,max_head_ft:90},
        {model:'10GS10',display:'10GS10 Sub 1HP 10GPM',pump_type:'submersible',hp:1.0,kw:0.75,voltage:230,pressure_psi:80,max_gpm:10,max_head_ft:185},
        {model:'10GS15',display:'10GS15 Sub 1.5HP 10GPM',pump_type:'submersible',hp:1.5,kw:1.12,voltage:230,pressure_psi:120,max_gpm:10,max_head_ft:280},
        {model:'18GS10',display:'18GS10 Sub 1HP 18GPM',pump_type:'submersible',hp:1.0,kw:0.75,voltage:230,pressure_psi:50,max_gpm:18,max_head_ft:115},
        {model:'25GS10',display:'25GS10 Sub 1HP 25GPM',pump_type:'submersible',hp:1.0,kw:0.75,voltage:230,pressure_psi:38,max_gpm:25,max_head_ft:88}
    ]},
    {brand:'Grundfos',models:[
        {model:'SCALA2',display:'SCALA2 3-45 Booster 0.75HP',pump_type:'above_ground',hp:0.75,kw:0.55,voltage:115,pressure_psi:64,max_gpm:20,max_head_ft:148},
        {model:'CMBE-1-44',display:'CMBE 1-44 Booster 0.75HP',pump_type:'above_ground',hp:0.75,kw:0.56,voltage:115,pressure_psi:64,max_gpm:15,max_head_ft:168},
        {model:'CMBE-3-51',display:'CMBE 3-51 Booster 1HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:115,pressure_psi:60,max_gpm:26,max_head_ft:170},
        {model:'CMBE-1-75',display:'CMBE 1-75 Hi-Head 1HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:230,pressure_psi:115,max_gpm:15,max_head_ft:265},
        {model:'MQ3-45',display:'MQ3-45 Booster 1HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:115,pressure_psi:60,max_gpm:20,max_head_ft:92},
        {model:'SQFlex-11',display:'SQFlex 11 Solar Sub 1.4HP',pump_type:'submersible',hp:1.4,kw:1.05,voltage:230,pressure_psi:73,max_gpm:11,max_head_ft:525}
    ]},
    {brand:'Myers',models:[
        {model:'HR50S',display:'HR50S Shallow Well 0.5HP',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:50,max_gpm:15,max_head_ft:115},
        {model:'HJ75S',display:'HJ75S Shallow Well 0.75HP',pump_type:'above_ground',hp:0.75,kw:0.56,voltage:115,pressure_psi:69,max_gpm:25,max_head_ft:159},
        {model:'HJ100S',display:'HJ100S Shallow Well 1HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:115,pressure_psi:67,max_gpm:29,max_head_ft:154}
    ]},
    {brand:'Pentair',models:[
        {model:'Enviromax-E135',display:'Enviromax E135 Centrifugal',pump_type:'above_ground',hp:1.5,kw:1.12,voltage:230,pressure_psi:45,max_gpm:100,max_head_ft:80},
        {model:'Enviromax-E150',display:'Enviromax E150 Centrifugal',pump_type:'above_ground',hp:2.0,kw:1.49,voltage:230,pressure_psi:50,max_gpm:120,max_head_ft:95},
        {model:'Enviromax-E170',display:'Enviromax E170 Centrifugal',pump_type:'above_ground',hp:3.0,kw:2.24,voltage:230,pressure_psi:55,max_gpm:150,max_head_ft:110}
    ]},
    {brand:'Rain Bird',models:[
        {model:'BPUMP1HP',display:'BPUMP 1HP Booster',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:115,pressure_psi:45,max_gpm:66,max_head_ft:104},
        {model:'BPUMP1.5HP',display:'BPUMP 1.5HP Booster',pump_type:'above_ground',hp:1.5,kw:1.12,voltage:115,pressure_psi:50,max_gpm:66,max_head_ft:115},
        {model:'BPUMP2HP',display:'BPUMP 2HP Booster',pump_type:'above_ground',hp:2.0,kw:1.49,voltage:115,pressure_psi:55,max_gpm:70,max_head_ft:127}
    ]},
    {brand:'Red Lion',models:[
        {model:'RJS-50',display:'RJS-50 Shallow Well 0.5HP',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:50,max_gpm:13,max_head_ft:150},
        {model:'RJS-75',display:'RJS-75 Shallow Well 0.75HP',pump_type:'above_ground',hp:0.75,kw:0.56,voltage:115,pressure_psi:50,max_gpm:17,max_head_ft:150},
        {model:'RJS-100',display:'RJS-100 Shallow Well 1HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:115,pressure_psi:50,max_gpm:23,max_head_ft:150},
        {model:'RJC-50',display:'RJC-50 Convertible 0.5HP',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:50,max_gpm:11,max_head_ft:176},
        {model:'RJC-100',display:'RJC-100 Convertible 1HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:230,pressure_psi:50,max_gpm:20,max_head_ft:207},
        {model:'RL-SWJ50',display:'RL-SWJ50 Sub 0.5HP',pump_type:'submersible',hp:0.5,kw:0.37,voltage:230,pressure_psi:45,max_gpm:12,max_head_ft:100}
    ]},
    {brand:'Sta-Rite',models:[
        {model:'DuraJet-50',display:'DuraJet 0.5HP Shallow',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:50,max_gpm:12,max_head_ft:115},
        {model:'DuraJet-75',display:'DuraJet 0.75HP Shallow',pump_type:'above_ground',hp:0.75,kw:0.56,voltage:115,pressure_psi:55,max_gpm:18,max_head_ft:130},
        {model:'DuraJet-100',display:'DuraJet 1HP Shallow',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:230,pressure_psi:63,max_gpm:23,max_head_ft:145},
        {model:'DuraJet-150',display:'DuraJet 1.5HP Shallow',pump_type:'above_ground',hp:1.5,kw:1.12,voltage:230,pressure_psi:70,max_gpm:28,max_head_ft:162},
        {model:'DuraJet-200',display:'DuraJet 2HP Shallow',pump_type:'above_ground',hp:2.0,kw:1.49,voltage:230,pressure_psi:75,max_gpm:33,max_head_ft:173},
        {model:'Dominator-50',display:'Dominator 0.5HP Deep Well',pump_type:'submersible',hp:0.5,kw:0.37,voltage:230,pressure_psi:50,max_gpm:10,max_head_ft:120},
        {model:'Dominator-75',display:'Dominator 0.75HP Deep Well',pump_type:'submersible',hp:0.75,kw:0.56,voltage:230,pressure_psi:60,max_gpm:12,max_head_ft:170},
        {model:'Dominator-100',display:'Dominator 1HP Deep Well',pump_type:'submersible',hp:1.0,kw:0.75,voltage:230,pressure_psi:70,max_gpm:15,max_head_ft:230}
    ]},
    {brand:'Wayne',models:[
        {model:'SWS50',display:'SWS50 Shallow Well 0.5HP',pump_type:'above_ground',hp:0.5,kw:0.37,voltage:115,pressure_psi:50,max_gpm:12,max_head_ft:115},
        {model:'SWS75',display:'SWS75 Shallow Well 0.75HP',pump_type:'above_ground',hp:0.75,kw:0.56,voltage:115,pressure_psi:50,max_gpm:13,max_head_ft:115},
        {model:'SWS100',display:'SWS100 Shallow Well 1HP',pump_type:'above_ground',hp:1.0,kw:0.75,voltage:115,pressure_psi:50,max_gpm:18,max_head_ft:115}
    ]}
];

function _pumpDbPopulateModels(prefix, filterType) {
    var brandSel = document.getElementById(prefix + 'PumpBrandSel');
    var modelSel = document.getElementById(prefix + 'PumpModelSel');
    if (!brandSel || !modelSel) return;
    var brand = brandSel.value;
    modelSel.innerHTML = '<option value="">-- Select Model --</option>';
    if (!brand || brand === '__custom__') {
        modelSel.innerHTML += '<option value="__custom__">Custom / Other</option>';
        if (brand === '__custom__') modelSel.value = '__custom__';
        // Show custom row immediately
        var cr = document.getElementById(prefix + 'PumpCustomRow');
        if (cr) cr.style.display = (brand === '__custom__') ? '' : 'none';
        return;
    }
    var entry = PUMP_DATABASE.find(function(e) { return e.brand === brand; });
    if (!entry) return;
    entry.models.forEach(function(m) {
        if (filterType && m.pump_type !== filterType) return;
        modelSel.innerHTML += '<option value="' + m.model + '">' + m.display + '</option>';
    });
    modelSel.innerHTML += '<option value="__custom__">Custom / Other</option>';
}

function _pumpDbAutoFill(prefix) {
    var brandSel = document.getElementById(prefix + 'PumpBrandSel');
    var modelSel = document.getElementById(prefix + 'PumpModelSel');
    if (!brandSel || !modelSel) return;
    var brand = brandSel.value;
    var modelKey = modelSel.value;
    // Toggle custom fields
    var customRow = document.getElementById(prefix + 'PumpCustomRow');
    if (customRow) customRow.style.display = (brand === '__custom__' || modelKey === '__custom__') ? '' : 'none';
    if (!brand || brand === '__custom__' || !modelKey || modelKey === '__custom__') return;
    var entry = PUMP_DATABASE.find(function(e) { return e.brand === brand; });
    if (!entry) return;
    var m = entry.models.find(function(mm) { return mm.model === modelKey; });
    if (!m) return;
    // Auto-fill fields
    var s = function(id, v) { var el = document.getElementById(prefix + id); if (el && v !== undefined) el.value = v; };
    s('PumpHP', m.hp || '');
    s('PumpKW', m.kw || '');
    s('PumpVoltage', m.voltage || 240);
    s('PumpPressure', m.pressure_psi || '');
    s('PumpMaxGpm', m.max_gpm || '');
    s('PumpMaxHead', m.max_head_ft || '');
    // Update bar from PSI
    var barEl = document.getElementById(prefix + 'PumpPressureBar');
    if (barEl && m.pressure_psi) barEl.value = (m.pressure_psi * 0.0689476).toFixed(2);
    // Set pump type radio
    var typeEls = document.querySelectorAll('input[name="' + prefix + 'PumpType"]');
    for (var ti = 0; ti < typeEls.length; ti++) { typeEls[ti].checked = (typeEls[ti].value === m.pump_type); }
}

function _pumpDbInit(prefix, pSettings) {
    var brandSel = document.getElementById(prefix + 'PumpBrandSel');
    var modelSel = document.getElementById(prefix + 'PumpModelSel');
    if (!brandSel || !modelSel) return;
    var savedBrand = pSettings.brand || '';
    var savedModel = pSettings.model || '';
    // Try to match saved brand
    var matchedBrand = PUMP_DATABASE.find(function(e) { return e.brand === savedBrand; });
    if (matchedBrand) {
        brandSel.value = savedBrand;
        _pumpDbPopulateModels(prefix, '');
        // Try to match saved model
        var matchedModel = matchedBrand.models.find(function(m) { return m.model === savedModel; });
        if (matchedModel) {
            modelSel.value = savedModel;
        } else if (savedModel) {
            modelSel.value = '__custom__';
        }
    } else if (savedBrand) {
        brandSel.value = '__custom__';
    }
    // Show/hide custom row
    var customRow = document.getElementById(prefix + 'PumpCustomRow');
    if (customRow) {
        customRow.style.display = (brandSel.value === '__custom__' || modelSel.value === '__custom__' || (!matchedBrand && savedBrand)) ? '' : 'none';
    }
}

async function showPumpSettingsModal() {
    var pSettings = {};
    try { pSettings = await api('/pump_settings?t=' + Date.now()); } catch(e) {}
    var P = 'ho'; // prefix for element IDs

    var body = '<div style="display:flex;flex-direction:column;gap:12px;">';

    // Pump Type
    var pt = pSettings.pump_type || '';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Pump Type</label>';
    body += '<div style="display:flex;gap:16px;">';
    body += '<label style="font-size:13px;cursor:pointer;display:flex;align-items:center;gap:4px;"><input type="radio" name="hoPumpType" value="above_ground"' + (pt === 'above_ground' ? ' checked' : '') + ' onchange="_pumpDbPopulateModels(\\'ho\\',this.value)"> Above Ground</label>';
    body += '<label style="font-size:13px;cursor:pointer;display:flex;align-items:center;gap:4px;"><input type="radio" name="hoPumpType" value="submersible"' + (pt === 'submersible' ? ' checked' : '') + ' onchange="_pumpDbPopulateModels(\\'ho\\',this.value)"> Submersible</label>';
    body += '<label style="font-size:13px;cursor:pointer;display:flex;align-items:center;gap:4px;"><input type="radio" name="hoPumpType" value=""' + (!pt ? ' checked' : '') + ' onchange="_pumpDbPopulateModels(\\'ho\\',\\'\\')"> All Types</label>';
    body += '</div></div>';

    // Brand + Model dropdowns
    body += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Brand</label>' +
        '<select id="hoPumpBrandSel" onchange="_pumpDbPopulateModels(\\'ho\\',\\'\\');_pumpDbAutoFill(\\'ho\\')" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;">' +
        '<option value="">-- Select Brand --</option>';
    for (var dbi = 0; dbi < PUMP_DATABASE.length; dbi++) {
        body += '<option value="' + PUMP_DATABASE[dbi].brand + '">' + PUMP_DATABASE[dbi].brand + '</option>';
    }
    body += '<option value="__custom__">Custom / Other</option></select></div>';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Model</label>' +
        '<select id="hoPumpModelSel" onchange="_pumpDbAutoFill(\\'ho\\')" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;">' +
        '<option value="">-- Select Model --</option></select></div>';
    body += '</div>';

    // Custom brand/model text inputs (hidden by default)
    body += '<div id="hoPumpCustomRow" style="display:none;"><div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Custom Brand</label>' +
        '<input type="text" id="hoPumpBrand" value="' + esc(pSettings.brand || '') + '" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. Acme Pumps"></div>';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Custom Model</label>' +
        '<input type="text" id="hoPumpModel" value="' + esc(pSettings.model || '') + '" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. Turbo 3000"></div>';
    body += '</div></div>';

    body += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Horsepower (HP)</label>' +
        '<input type="number" id="hoPumpHP" value="' + (pSettings.hp || '') + '" step="0.25" min="0" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. 1.5" oninput="var v=parseFloat(this.value)||0;document.getElementById(\\'hoPumpKW\\').value=v>0?(v*0.7457).toFixed(4):\\'\\'"></div>';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Kilowatts (kW)</label>' +
        '<input type="number" id="hoPumpKW" value="' + (pSettings.kw || '') + '" step="0.01" min="0" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. 1.12" oninput="var v=parseFloat(this.value)||0;document.getElementById(\\'hoPumpHP\\').value=v>0?(v/0.7457).toFixed(4):\\'\\'"></div>';
    body += '</div>';

    body += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Voltage</label>' +
        '<input type="number" id="hoPumpVoltage" value="' + (pSettings.voltage || 240) + '" step="1" min="0" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="240"></div>';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Year Installed</label>' +
        '<input type="text" id="hoPumpYear" value="' + esc(pSettings.year_installed || '') + '" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. 2020"></div>';
    body += '</div>';

    body += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;">';
    var hoPsi = pSettings.pressure_psi || '';
    var hoBar = hoPsi ? (parseFloat(hoPsi) * 0.0689476).toFixed(2) : '';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Pressure (PSI)</label>' +
        '<input type="number" id="hoPumpPressure" value="' + hoPsi + '" step="1" min="0" ' +
        'oninput="var b=document.getElementById(\\'hoPumpPressureBar\\');if(b)b.value=this.value?(this.value*0.0689476).toFixed(2):\\'\\';" ' +
        'style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. 60"></div>';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Pressure (bar)</label>' +
        '<input type="number" id="hoPumpPressureBar" value="' + hoBar + '" step="0.01" min="0" ' +
        'oninput="var p=document.getElementById(\\'hoPumpPressure\\');if(p)p.value=this.value?Math.round(this.value/0.0689476):\\'\\';" ' +
        'style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. 4.14"></div>';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Max GPM</label>' +
        '<input type="number" id="hoPumpMaxGpm" value="' + (pSettings.max_gpm || '') + '" step="0.1" min="0" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. 25"></div>';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Max Head / TDH (ft)</label>' +
        '<input type="number" id="hoPumpMaxHead" value="' + (pSettings.max_head_ft || '') + '" step="1" min="0" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. 120"></div>';
    body += '</div>';

    body += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Electricity Cost ($/kWh)</label>' +
        '<input type="number" id="hoPumpCostKwh" value="' + (pSettings.cost_per_kwh || 0.12) + '" step="0.01" min="0" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="0.12"></div>';
    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Peak Rate ($/kWh)</label>' +
        '<input type="number" id="hoPumpPeakRate" value="' + (pSettings.peak_rate_per_kwh || 0) + '" step="0.01" min="0" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="0.00"></div>';
    body += '</div>';

    body += '<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;">' +
        '<button class="btn btn-secondary" onclick="closeDynamicModal()">Cancel</button>' +
        '<button class="btn btn-primary" onclick="savePumpSettings()">Save</button>' +
        '</div>';

    body += '</div>';

    showModal('\\u26a1 Pump Settings', body, '520px');
    // Initialize dropdowns after modal renders
    setTimeout(function() { _pumpDbInit('ho', pSettings); }, 50);
}

async function savePumpSettings() {
    // Determine brand/model from dropdown or custom input
    var brandSel = document.getElementById('hoPumpBrandSel');
    var modelSel = document.getElementById('hoPumpModelSel');
    var brand = '', model = '';
    if (brandSel && brandSel.value && brandSel.value !== '__custom__') {
        brand = brandSel.value;
        if (modelSel && modelSel.value && modelSel.value !== '__custom__') model = modelSel.value;
        else model = (document.getElementById('hoPumpModel') || {value:''}).value.trim();
    } else {
        brand = (document.getElementById('hoPumpBrand') || {value:''}).value.trim();
        model = (document.getElementById('hoPumpModel') || {value:''}).value.trim();
    }
    // Get pump type from radio
    var pumpType = '';
    var typeEls = document.querySelectorAll('input[name="hoPumpType"]');
    for (var ti = 0; ti < typeEls.length; ti++) { if (typeEls[ti].checked) { pumpType = typeEls[ti].value; break; } }
    var payload = {
        pump_entity_id: window._pumpZoneEntity || '',
        pump_type: pumpType,
        brand: brand,
        model: model,
        hp: parseFloat(document.getElementById('hoPumpHP').value) || 0,
        kw: parseFloat(document.getElementById('hoPumpKW').value) || 0,
        voltage: parseFloat(document.getElementById('hoPumpVoltage').value) || 240,
        year_installed: document.getElementById('hoPumpYear').value.trim(),
        cost_per_kwh: parseFloat(document.getElementById('hoPumpCostKwh').value) || 0.12,
        peak_rate_per_kwh: parseFloat(document.getElementById('hoPumpPeakRate').value) || 0,
        pressure_psi: parseFloat(document.getElementById('hoPumpPressure').value) || 0,
        max_gpm: parseFloat(document.getElementById('hoPumpMaxGpm').value) || 0,
        max_head_ft: parseFloat(document.getElementById('hoPumpMaxHead').value) || 0
    };
    try {
        await api('/pump_settings', { method: 'PUT', body: JSON.stringify(payload) });
        closeDynamicModal();
        showToast('Pump settings saved');
        loadPumpMonitor();
    } catch(e) {
        showToast('Failed to save: ' + e.message, true);
    }
}

// --- Water Source Settings ---

async function showWaterSettingsModal() {
    var ws = {};
    try { ws = await api('/water_settings?t=' + Date.now()); } catch(e) {}

    var body = '<div style="display:flex;flex-direction:column;gap:12px;">';

    body += '<div><label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Water Source</label>' +
        '<select id="waterSourceType" onchange="toggleWaterCostField()" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;">' +
        '<option value="">-- Select --</option>' +
        '<option value="city"' + (ws.water_source==='city' ? ' selected' : '') + '>City Water</option>' +
        '<option value="reclaimed"' + (ws.water_source==='reclaimed' ? ' selected' : '') + '>Reclaimed Water</option>' +
        '<option value="well"' + (ws.water_source==='well' ? ' selected' : '') + '>Well Water</option>' +
        '</select></div>';

    var showCost = (ws.water_source === 'city' || ws.water_source === 'reclaimed');
    body += '<div id="waterCostRow" style="' + (showCost ? '' : 'display:none;') + '">' +
        '<label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Cost per 1,000 Gallons ($)</label>' +
        '<input type="number" id="waterCostPer1000" value="' + (ws.cost_per_1000_gal || '') + '" step="0.01" min="0" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="e.g. 5.50">' +
        '</div>';

    body += '<div id="wellWaterNote" style="' + (ws.water_source==='well' ? '' : 'display:none;') +
        'background:var(--bg-tile);border-radius:6px;padding:8px 12px;font-size:13px;color:var(--text-muted);">' +
        'Well water has no utility cost. Pump electricity costs are tracked in the Pump Monitor card.</div>';

    // Water Pressure (PSI + bar)
    var wsPsi = ws.pressure_psi || 50;
    var wsBar = (wsPsi * 0.0689476).toFixed(2);
    body += '<div style="margin-top:4px;">' +
        '<label style="font-size:13px;font-weight:600;display:block;margin-bottom:4px;">Water Pressure</label>' +
        '<div style="display:flex;gap:8px;align-items:center;">' +
        '<div style="flex:1;"><input type="number" id="waterPressurePsi" value="' + wsPsi + '" step="1" min="0" ' +
        'oninput="var b=document.getElementById(\\'waterPressureBar\\');if(b)b.value=(this.value*0.0689476).toFixed(2);" ' +
        'style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="50">' +
        '<span style="font-size:10px;color:var(--text-muted);">PSI</span></div>' +
        '<div style="flex:1;"><input type="number" id="waterPressureBar" value="' + wsBar + '" step="0.01" min="0" ' +
        'oninput="var p=document.getElementById(\\'waterPressurePsi\\');if(p)p.value=Math.round(this.value/0.0689476);" ' +
        'style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;" placeholder="3.45">' +
        '<span style="font-size:10px;color:var(--text-muted);">bar</span></div>' +
        '</div>' +
        '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">System water pressure (used when no pump is configured)</div>' +
        '</div>';

    body += '<div style="display:flex;gap:10px;justify-content:flex-end;margin-top:8px;">' +
        '<button class="btn btn-secondary" onclick="closeDynamicModal()">Cancel</button>' +
        '<button class="btn btn-primary" onclick="saveWaterSettings()">Save</button>' +
        '</div>';
    body += '</div>';

    showModal('\\u{1F4A7} Water Monitor Settings', body, '420px');
}

function toggleWaterCostField() {
    var src = document.getElementById('waterSourceType').value;
    document.getElementById('waterCostRow').style.display = (src === 'city' || src === 'reclaimed') ? '' : 'none';
    document.getElementById('wellWaterNote').style.display = (src === 'well') ? '' : 'none';
}

async function saveWaterSettings() {
    var payload = {
        water_source: document.getElementById('waterSourceType').value,
        cost_per_1000_gal: parseFloat(document.getElementById('waterCostPer1000').value) || 0,
        pressure_psi: parseFloat(document.getElementById('waterPressurePsi').value) || 50
    };
    try {
        await api('/water_settings', { method: 'PUT', body: JSON.stringify(payload) });
        closeDynamicModal();
        showToast('Water settings saved');
        loadEstGallons();
    } catch(e) {
        showToast('Failed to save: ' + e.message, true);
    }
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

let _weatherDataCache = null;
let _weatherRulesCache = null;
let _moistureDataCache = null;
// User-typed sleep duration values — NOT tied to the entity.
// Survives DOM rebuilds.  Cleared only when value is applied to the device.
const _userSleepDurValues = {};  // probe_id -> user-typed value (string)
let _weatherCardBuilt = false;

const _condIcons = {
    'sunny': '☀️', 'clear-night': '🌙', 'partlycloudy': '⛅',
    'cloudy': '☁️', 'rainy': '🌧️', 'pouring': '🌧️',
    'snowy': '❄️', 'windy': '💨', 'fog': '🌫️',
    'lightning': '⚡', 'lightning-rainy': '⛈️', 'hail': '🧊',
};

function _buildWeatherCardShell() {
    // Build the weather card DOM structure once with data-id attributes for targeted updates
    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;">';
    html += '<div style="background:var(--bg-weather);border-radius:8px;padding:10px;text-align:center;">';
    html += '<div data-id="wIcon" style="font-size:24px;"></div>';
    html += '<div data-id="wCondition" style="font-weight:600;text-transform:capitalize;font-size:13px;"></div>';
    html += '</div>';
    html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
    html += '<div style="color:var(--text-placeholder);font-size:11px;">Temperature</div>';
    html += '<div data-id="wTemp" style="font-weight:600;font-size:16px;"></div>';
    html += '</div>';
    html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
    html += '<div style="color:var(--text-placeholder);font-size:11px;">Humidity</div>';
    html += '<div data-id="wHumidity" style="font-weight:600;font-size:16px;"></div>';
    html += '</div>';
    html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
    html += '<div style="color:var(--text-placeholder);font-size:11px;">Wind</div>';
    html += '<div data-id="wWind" style="font-weight:600;font-size:16px;"></div>';
    html += '</div>';
    html += '</div>';
    html += '<div data-id="wForecast"></div>';
    html += '<div data-id="wAdjustments"></div>';
    // Weather Rules Editor — collapsible section, collapsed by default
    html += '<div style="margin-top:16px;border-top:1px solid var(--border-light);padding-top:16px;">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0;cursor:pointer;" onclick="toggleWeatherRules()">';
    html += '<div style="display:flex;align-items:center;gap:8px;">';
    html += '<span id="weatherRulesChevron" style="font-size:12px;transition:transform 0.2s;">&#9654;</span>';
    html += '<div style="font-size:14px;font-weight:600;">Weather Rules</div>';
    html += '</div>';
    html += '<div style="display:flex;gap:6px;">';
    html += '<button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();evaluateWeatherNow()">Test Rules Now</button>';
    html += '<button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();exportWeatherLogCSV()">Export Log</button>';
    html += '<button class="btn btn-danger btn-sm" onclick="event.stopPropagation();clearWeatherLog()">Clear Log</button>';
    html += '</div>';
    html += '</div>';
    html += '<div id="weatherRulesContainer" style="display:none;margin-top:12px;"><div class="loading">Loading rules...</div></div>';
    html += '</div>';
    return html;
}

function _getVisibleWeatherKey(data) {
    // Build a cache key using ONLY the values the user can see — not timestamps
    const w = data.weather || {};
    const parts = [
        w.condition, w.temperature, w.humidity, w.wind_speed,
        data.watering_multiplier,
        JSON.stringify((data.active_adjustments || []).map(a => a.reason || a.rule)),
    ];
    // Include forecast visible fields only
    const fc = (w.forecast || []).slice(0, 10);
    for (const f of fc) {
        parts.push(f.condition, f.temperature, f.precipitation_probability);
    }
    return parts.join('|');
}

async function loadWeather() {
    const card = document.getElementById('weatherCard');
    const body = document.getElementById('cardBody_weather');
    const badge = document.getElementById('weatherMultBadge');
    try {
        const data = await api('/weather');
        if (!data.weather_enabled) {
            card.style.display = 'none';
            _weatherDataCache = null;
            _weatherCardBuilt = false;
            return;
        }

        // Build the card shell once, then only update data values
        if (!_weatherCardBuilt) {
            body.innerHTML = _buildWeatherCardShell();
            _weatherCardBuilt = true;
            _weatherDataCache = null; // force data fill on first build
            loadWeatherRules();
        }

        // Skip updates if visible data hasn't changed
        const visibleKey = _getVisibleWeatherKey(data);
        if (_weatherDataCache === visibleKey) return;
        _weatherDataCache = visibleKey;

        card.style.display = 'block';
        const w = data.weather || {};
        if (w.error) {
            body.innerHTML = '<div style="color:var(--text-placeholder);text-align:center;padding:12px;">' + esc(w.error) + '</div>';
            _weatherCardBuilt = false;
            return;
        }

        // --- Targeted updates: only change text/styles, no DOM rebuild ---
        const icon = _condIcons[w.condition] || '🌡️';
        const mult = data.watering_multiplier != null ? data.watering_multiplier : 1.0;

        // Badge — show skip message if a pause/skip adjustment is active
        const adjustments = data.active_adjustments || [];
        const skipAdj = adjustments.find(a => a.action === 'pause' || a.action === 'skip');
        if (skipAdj) {
            let skipText = 'Skipping Watering';
            if (skipAdj.expires_at) {
                try {
                    const expiresMs = new Date(skipAdj.expires_at).getTime() - Date.now();
                    if (expiresMs > 0) {
                        const hrs = Math.round(expiresMs / 3600000 * 10) / 10;
                        skipText = 'Skipping Watering for ' + hrs + ' hr' + (hrs !== 1 ? 's' : '');
                    }
                } catch(_) {}
            }
            badge.textContent = skipText;
            badge.style.background = 'var(--bg-danger-light)';
            badge.style.color = 'var(--text-danger-dark)';
        } else {
            badge.textContent = mult + 'x';
            badge.style.background = mult === 1.0 ? 'var(--bg-success-light)' : mult < 1 ? 'var(--bg-warning)' : 'var(--bg-danger-light)';
            badge.style.color = mult === 1.0 ? 'var(--text-success-dark)' : mult < 1 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
        }

        // Current conditions — update text only
        const el = (id) => body.querySelector('[data-id=\"' + id + '\"]');
        el('wIcon').textContent = icon;
        el('wCondition').textContent = w.condition || 'unknown';
        el('wTemp').textContent = w.temperature != null ? w.temperature + (w.temperature_unit || '°F') : 'N/A';
        el('wHumidity').textContent = w.humidity != null ? w.humidity + '%' : 'N/A';
        el('wWind').textContent = w.wind_speed != null ? w.wind_speed + ' ' + (w.wind_speed_unit || 'mph') : 'N/A';

        // Forecast — rebuild only the forecast strip (lightweight)
        const forecastEl = el('wForecast');
        const rawForecast = w.forecast || [];
        // Deduplicate forecast by date — NWS returns day+night periods
        // Keep one entry per calendar day (merge high/low temps, max precip)
        var forecast = [];
        var seenDays = {};
        for (var fi = 0; fi < rawForecast.length; fi++) {
            var ff = rawForecast[fi];
            var fdt = ff.datetime ? new Date(ff.datetime) : null;
            var dayKey = fdt ? fdt.toLocaleDateString('en-US') : ('idx' + fi);
            if (seenDays[dayKey]) {
                // Merge: use higher temp as high, lower as low, max precip
                var existing = seenDays[dayKey];
                if (ff.temperature != null && existing.temperature != null) {
                    if (ff.temperature > existing.temperature) {
                        existing.templow = existing.temperature;
                        existing.temperature = ff.temperature;
                        existing.condition = ff.condition || existing.condition;
                    } else {
                        existing.templow = ff.temperature;
                    }
                }
                var ep = existing.precipitation_probability || 0;
                var fp = ff.precipitation_probability || 0;
                if (fp > ep) existing.precipitation_probability = fp;
                continue;
            }
            var entry = Object.assign({}, ff);
            seenDays[dayKey] = entry;
            forecast.push(entry);
        }
        if (forecast.length > 0) {
            let fh = '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;margin-bottom:8px;">Forecast</div>';
            fh += '<div style="display:flex;gap:6px;overflow-x:auto;padding-bottom:4px;">';
            for (let i = 0; i < Math.min(forecast.length, 5); i++) {
                const f = forecast[i];
                const dt = f.datetime ? new Date(f.datetime) : null;
                var dayLabel = dt ? dt.toLocaleDateString('en-US', { weekday: 'short' }) : '';
                const fIcon = _condIcons[f.condition] || '🌡️';
                const precip = f.precipitation_probability || 0;
                fh += '<div style="flex:0 0 auto;background:var(--bg-tile);border-radius:8px;padding:8px 10px;text-align:center;min-width:64px;">';
                fh += '<div style="font-size:10px;color:var(--text-placeholder);white-space:nowrap;">' + esc(dayLabel) + '</div>';
                fh += '<div style="font-size:18px;">' + fIcon + '</div>';
                fh += '<div style="font-size:12px;font-weight:600;">' + (f.temperature != null ? f.temperature + '°' : '') + '</div>';
                if (f.templow != null) {
                    fh += '<div style="font-size:11px;color:var(--text-muted);">' + f.templow + '°</div>';
                }
                if (precip > 0) {
                    fh += '<div style="font-size:10px;color:var(--color-link);">💧 ' + precip + '%</div>';
                }
                fh += '</div>';
            }
            fh += '</div></div>';
            forecastEl.innerHTML = fh;
        } else {
            forecastEl.innerHTML = '';
        }

        // Active adjustments — rebuild only the adjustments box
        const adjEl = el('wAdjustments');
        if (adjustments.length > 0) {
            let ah = '<div style="margin-top:12px;padding:10px;background:var(--bg-warning);border-radius:8px;font-size:12px;">';
            ah += '<strong style="color:var(--text-warning);">Active Weather Adjustments:</strong>';
            ah += '<ul style="margin:4px 0 0 16px;color:var(--text-warning);">';
            for (const adj of adjustments) {
                ah += '<li>' + esc(adj.reason || adj.rule) + '</li>';
            }
            ah += '</ul></div>';
            adjEl.innerHTML = ah;
        } else {
            adjEl.innerHTML = '';
        }
    } catch (e) {
        card.style.display = 'none';
    }
}

async function loadWeatherRules() {
    const container = document.getElementById('weatherRulesContainer');
    if (!container) return;
    try {
        const data = await wapi('/weather/rules');
        // Skip DOM rebuild if rules haven't changed
        const rulesKey = JSON.stringify(data);
        if (_weatherRulesCache === rulesKey) return;
        _weatherRulesCache = rulesKey;
        const rules = data.rules || {};
        let html = '<div style="display:flex;flex-direction:column;gap:8px;">';

        // Rule 1: Rain Detection
        const r1 = rules.rain_detection || {};
        html += buildRuleRow('rain_detection', 'Rain Detection', 'Pause when currently raining', r1.enabled, [
            { id: 'rain_detection_resume_delay_hours', label: 'Resume delay (hours)', value: r1.resume_delay_hours || 2, type: 'number', min: 0, max: 24, step: 1 }
        ]);

        // Rule 2: Rain Forecast
        const r2 = rules.rain_forecast || {};
        html += buildRuleRow('rain_forecast', 'Rain Forecast', 'Skip when rain probability exceeds threshold within lookahead window', r2.enabled, [
            { id: 'rain_forecast_probability_threshold', label: 'Probability %', value: r2.probability_threshold || 60, type: 'number', min: 10, max: 100, step: 5 },
            { id: 'rain_forecast_lookahead_hours', label: 'Lookahead (hours)', value: r2.lookahead_hours || 48, type: 'number', min: 6, max: 168, step: 6 }
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
                lookahead_hours: parseInt(document.getElementById('rain_forecast_lookahead_hours').value) || 48,
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
        const result = await wapi('/weather/rules', {
            method: 'PUT',
            body: JSON.stringify({ rules }),
        });
        const mult = result.watering_multiplier;
        showToast('Weather rules saved' + (mult != null ? ' — multiplier: ' + mult + 'x' : ''));
        // Clear cache to pick up new multiplier; card structure stays intact
        _weatherDataCache = null;
        _weatherRulesCache = null;
        // Force re-apply adjusted durations in case the backend chain had a silent failure
        try { await mapi('/durations/apply', 'POST'); } catch(e2) { /* non-critical */ }
        loadWeather();
        loadStatus();
        // Delay schedule refresh slightly to let HA entity states settle after writes
        setTimeout(() => loadControls(), 1500);
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
        // Refresh weather data (card structure stays intact)
        _weatherDataCache = null;
        // Force re-apply adjusted durations in case the backend chain had a silent failure
        try { await mapi('/durations/apply', 'POST'); } catch(e2) { /* non-critical */ }
        loadWeather();
        loadStatus();
        // Delay schedule refresh slightly to let HA entity states settle after writes
        setTimeout(() => loadControls(), 1500);
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

function toggleWeatherRules() {
    const container = document.getElementById('weatherRulesContainer');
    const chevron = document.getElementById('weatherRulesChevron');
    if (!container) return;
    const isHidden = container.style.display === 'none';
    container.style.display = isHidden ? 'block' : 'none';
    if (chevron) chevron.style.transform = isHidden ? 'rotate(90deg)' : 'rotate(0deg)';
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
        } else {
            showToast(result.error || 'Failed to clear weather log', 'error');
        }
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Moisture Probes ---
let _moistureExpanded = { settings: false, management: false };
let _lastMultiplierKey = null;  // Track multiplier changes to auto-refresh schedule

async function loadMoisture() {
    const card = document.getElementById('moistureCard');
    const body = document.getElementById('cardBody_moisture');
    const badge = document.getElementById('moistureStatusBadge');
    try {
        const _mcb = '?t=' + Date.now();
        const [data, settings, cellularData] = await Promise.all([
            mapi('/probes' + _mcb),
            mapi('/settings' + _mcb),
            mapi('/probes/cellular' + _mcb).catch(() => ({ probes: {} })),
        ]);
        let multData = {};
        try { multData = await mapi('/multiplier' + _mcb); } catch (_) {}
        let timelineData = {};
        try { timelineData = await mapi('/schedule-timeline' + _mcb); } catch (_) {}

        const wifiProbes = data.probes || {};
        const cellularProbes = (cellularData && cellularData.probes) || {};
        const wifiCount = Object.keys(wifiProbes).length;
        const cellularCount = Object.keys(cellularProbes).length;
        const probeCount = wifiCount + cellularCount;

        // Check if moisture multipliers changed → auto-refresh schedule card
        const multKey = JSON.stringify(multData.per_zone || {});
        if (_lastMultiplierKey !== null && _lastMultiplierKey !== multKey) {
            console.log('[MOISTURE] Factors changed, refreshing schedule card');
            loadControls();
        }
        _lastMultiplierKey = multKey;

        // Hide the card on the dashboard if no probes are configured
        // (probes are added via the Configuration page)
        if (!settings.enabled && probeCount === 0) {
            card.style.display = 'none';
            _moistureDataCache = null;
            return;
        }
        // Skip DOM rebuild if data hasn't changed (prevents flickering on refresh)
        const moistureKey = JSON.stringify(data) + '|' + JSON.stringify(settings) + '|' + JSON.stringify(multData) + '|' + JSON.stringify(timelineData) + '|' + JSON.stringify(cellularData);
        if (_moistureDataCache === moistureKey) return;
        _moistureDataCache = moistureKey;
        card.style.display = 'block';

        badge.textContent = settings.enabled ? probeCount + ' probe(s)' + (cellularCount > 0 ? ' (' + cellularCount + ' cellular)' : '') : 'Disabled';
        badge.style.background = settings.enabled ? 'var(--bg-success-light)' : 'var(--bg-tile)';
        badge.style.color = settings.enabled ? 'var(--text-success-dark)' : 'var(--text-muted)';

        const perZone = (multData && multData.per_zone) || {};

        let html = '';

        // WiFi Probe tiles
        if (wifiCount > 0) {
            html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">';
            html += '<span style="font-size:13px;font-weight:600;display:inline-flex;align-items:center;gap:4px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="flex-shrink:0;"><path d="M12 20h.01"/><path d="M8.5 16.5a5 5 0 0 1 7 0"/><path d="M5 12.5a10 10 0 0 1 14 0"/><path d="M1.5 8.5a14 14 0 0 1 21 0"/></svg> WiFi Probes</span>';
            html += '</div>';
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;">';
            for (const [pid, probe] of Object.entries(wifiProbes)) {
                const sensors = probe.sensors_live || {};
                const devSensors = probe.device_sensors || {};
                const es = probe.extra_sensors || {};
                html += '<div style="background:var(--bg-tile);border-radius:10px;padding:12px;border:1px solid var(--border-light);">';
                // Probe header with per-zone skip/multiplier badges
                var probeZones = probe.zone_mappings || [];
                var probeSkipBadges = '';
                for (var pzi = 0; pzi < probeZones.length; pzi++) {
                    var pzEid = probeZones[pzi];
                    var pzInfo = perZone[pzEid];
                    var pzNum = (pzEid.match(/zone[_]?(\\d+)/i) || [])[1] || '?';
                    if (pzInfo && pzInfo.skip) {
                        probeSkipBadges += ' <span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:var(--bg-danger-light);color:var(--color-danger);">Z' + pzNum + ' Skip</span>';
                    } else if (pzInfo && pzInfo.moisture_multiplier != null && pzInfo.moisture_multiplier !== 1.0) {
                        probeSkipBadges += ' <span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:var(--bg-warning);color:var(--text-warning);">Z' + pzNum + ' ' + pzInfo.moisture_multiplier.toFixed(2) + 'x</span>';
                    } else {
                        // Zone mapped but multiplier is 1.0 or no data yet — show neutral badge
                        var mmVal = pzInfo ? (pzInfo.moisture_multiplier != null ? pzInfo.moisture_multiplier.toFixed(2) : '1.00') : '1.00';
                        probeSkipBadges += ' <span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:var(--bg-tile);color:var(--text-muted);border:1px solid var(--border-light);">Z' + pzNum + ' ' + mmVal + 'x</span>';
                    }
                }
                html += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:' + (probeSkipBadges ? '2' : '10') + 'px;">';
                html += '<span style="font-weight:600;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + esc(probe.display_name || pid) + '</span>';
                html += '<a href="#" onclick="renameProbe(\\'' + esc(pid) + '\\');return false;" title="Rename probe" style="font-size:12px;color:var(--text-muted);text-decoration:none;flex-shrink:0;">&#9998;</a>';
                html += '</div>';
                if (probeSkipBadges) {
                    html += '<div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px;">' + probeSkipBadges + '</div>';
                }

                // Depth readings as horizontal bars
                for (const depth of ['shallow', 'mid', 'deep']) {
                    const s = sensors[depth];
                    if (!s) continue;
                    const val = s.value != null ? s.value : null;
                    const stale = s.stale;
                    const isCached = s.cached === true;
                    const pct = val != null ? Math.min(val, 100) : 0;
                    const color = val == null ? '#bbb' : stale ? '#999' : val > 70 ? '#3498db' : val > 40 ? '#2ecc71' : '#e67e22';
                    html += '<div style="margin-bottom:6px;">';
                    html += '<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-bottom:2px;">';
                    html += '<span>' + depth.charAt(0).toUpperCase() + depth.slice(1) + (isCached ? ' <span style="font-size:9px;opacity:0.7;" title="Last reading before device went to sleep">(retained)</span>' : '') + '</span>';
                    html += '<span>' + (val != null ? val.toFixed(0) + '%' : '—') + (stale ? ' ⏳' : '') + '</span>';
                    html += '</div>';
                    html += '<div style="height:6px;background:var(--border-light);border-radius:3px;overflow:hidden;">';
                    html += '<div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:3px;transition:width 0.3s;"></div>';
                    html += '</div></div>';
                }

                // --- Section 3: Device Info (read-only telemetry) ---
                const hasDeviceTelemetry = devSensors.wifi || devSensors.battery || devSensors.solar_charging;
                if (hasDeviceTelemetry) {
                    html += '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;padding-top:8px;border-top:1px solid var(--border-light);font-size:11px;color:var(--text-muted);">';
                    if (devSensors.wifi) {
                        const wv = devSensors.wifi.value;
                        const wLabel = wv == null ? '—' : wv > -50 ? 'Great' : wv > -60 ? 'Good' : wv > -70 ? 'Fair' : 'Poor';
                        const wColor = wv == null ? 'var(--text-muted)' : wv > -50 ? 'var(--text-success-dark)' : wv > -60 ? 'var(--text-success-dark)' : wv > -70 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
                        html += '<span style="color:' + wColor + ';display:inline-flex;align-items:center;gap:2px;" title="WiFi Signal: ' + (wv != null ? wv.toFixed(0) + ' dBm' : 'unknown') + '"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h.01"/><path d="M8.5 16.5a5 5 0 0 1 7 0"/><path d="M5 12.5a10 10 0 0 1 14 0"/><path d="M1.5 8.5a14 14 0 0 1 21 0"/></svg> ' + wLabel + '</span>';
                    }
                    if (devSensors.battery) {
                        const bv = devSensors.battery.value;
                        const bIcon = bv == null ? '🔋' : bv > 50 ? '🔋' : bv > 20 ? '🪫' : '🪫';
                        const bColor = bv == null ? 'var(--text-muted)' : bv > 50 ? 'var(--text-success-dark)' : bv > 20 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
                        html += '<span style="color:' + bColor + ';" title="Battery">' + bIcon + ' ' + (bv != null ? bv.toFixed(0) + '%' : '—') + '</span>';
                    }
                    if (devSensors.solar_charging) {
                        const scLive = (devSensors.solar_charging.live_raw_state || '').toLowerCase();
                        const scCached = (devSensors.solar_charging.value || '').toLowerCase();
                        const scVal = (scLive && scLive !== 'unavailable' && scLive !== 'unknown') ? scLive : scCached;
                        const isCharging = scVal === 'on';
                        const scRetained = (scLive === 'unavailable' || scLive === 'unknown') && scCached;
                        html += '<span style="color:' + (isCharging ? 'var(--color-warning)' : 'var(--text-muted)') + ';" title="Solar Charging: ' + (isCharging ? 'Active' : 'Inactive') + (scRetained ? ' (retained)' : '') + '">' + (isCharging ? '☀️ Charging' : '🌙 No Solar') + (scRetained ? ' <span style="font-size:9px;opacity:0.7;">(retained)</span>' : '') + '</span>';
                    }
                    html += '</div>';
                }

                // --- Section 4: Sleep & Status ---
                const hasSleepInfo = devSensors.sleep_duration || devSensors.sleep_disabled;
                if (hasSleepInfo) {
                    html += '<div style="margin-top:8px;padding-top:8px;border-top:1px solid var(--border-light);font-size:11px;color:var(--text-muted);">';
                    // Row 4a: Awake/Sleeping status + schedule prep
                    if (devSensors.sleep_duration) {
                        html += '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">';
                        const isAwake = probe.is_awake === true;
                        var sleepLabel = '😴 Sleeping';
                        if (!isAwake && devSensors.status_led && devSensors.status_led.last_changed && devSensors.sleep_duration.value) {
                            try {
                                var sleepStart = new Date(devSensors.status_led.last_changed);
                                var durMin = parseFloat(devSensors.sleep_duration.value);
                                if (!isNaN(sleepStart.getTime()) && durMin > 0) {
                                    var wakeAt = new Date(sleepStart.getTime() + durMin * 60000);
                                    var now = new Date();
                                    if (wakeAt > now) {
                                        var diffMs = wakeAt - now;
                                        var diffMin = Math.round(diffMs / 60000);
                                        var timeStr = wakeAt.toLocaleTimeString([], {hour:'numeric', minute:'2-digit'});
                                        if (diffMin < 1) {
                                            sleepLabel = '😴 Waking soon';
                                        } else if (diffMin <= 60) {
                                            sleepLabel = '😴 Wake in ' + diffMin + ' min';
                                        } else {
                                            sleepLabel = '😴 Wake at ' + timeStr;
                                        }
                                    } else {
                                        sleepLabel = '😴 Waking soon';
                                    }
                                }
                            } catch(e) {}
                        }
                        html += '<span style="font-weight:600;color:' + (isAwake ? 'var(--color-success)' : 'var(--text-muted)') + ';">' +
                            (isAwake ? '☀️ Awake' : sleepLabel) + '</span>';
                        var probePrep = (timelineData.probe_prep || {})[pid];
                        if (probePrep && probePrep.state !== 'idle') {
                            var prepState = probePrep.state;
                            if (prepState === 'prep_pending') {
                                html += '<span style="font-size:10px;color:var(--color-warning);" title="Probe sleep adjusted to wake before zone">⏰ Waking for Z' + (probePrep.active_zone_num || '?') + '</span>';
                            } else if (prepState === 'monitoring') {
                                html += '<span style="font-size:10px;color:var(--color-success);" title="Probe is awake and monitoring zone moisture">🔍 Monitoring Z' + (probePrep.active_zone_num || '?') + '</span>';
                            } else if (prepState === 'sleeping_between') {
                                html += '<span style="font-size:10px;color:var(--text-muted);" title="Sleeping between mapped zones">💤 Between zones</span>';
                            }
                        }
                        html += '</div>';
                    }
                    // Row 4b: Sleep disabled toggle + pending
                    if (devSensors.sleep_disabled) {
                        const sdVal = devSensors.sleep_disabled.value || '';
                        const isSleepDisabled = sdVal === 'on';
                        const pendingSD = probe.pending_sleep_disabled;
                        const showDisabled = pendingSD != null ? pendingSD : isSleepDisabled;
                        const btnLabel = showDisabled ? 'Enable Sleep' : 'Disable Sleep';
                        const btnColor = showDisabled ? 'var(--color-success)' : 'var(--color-warning)';
                        html += '<div style="display:flex;align-items:center;gap:8px;margin-top:6px;">';
                        html += '<button onclick="hoToggleSleepDisabled(\\'' + esc(pid) + '\\',' + (showDisabled ? 'false' : 'true') + ')" style="padding:2px 8px;font-size:10px;border:1px solid ' + btnColor + ';border-radius:4px;cursor:pointer;background:transparent;color:' + btnColor + ';">' + btnLabel + '</button>';
                        html += '<span id="sleepDisPending_' + esc(pid) + '" style="color:var(--color-warning);font-size:10px;' + (pendingSD != null ? '' : 'display:none;') + '">' + (pendingSD != null ? '⏳ Pending — applies on wake' : '') + '</span>';
                        html += '</div>';
                    }
                    // Row 4c: Sleep duration control + pending
                    if (devSensors.sleep_duration) {
                        const sv = devSensors.sleep_duration.value;
                        const deviceMin = sv != null ? Math.round(sv) : null;
                        const pendingSleep = probe.pending_sleep_duration;
                        const userVal = _userSleepDurValues[pid];
                        const inputVal = userVal != null ? userVal : (pendingSleep != null ? pendingSleep : (deviceMin || ''));
                        const hasPendingOrUser = userVal != null || pendingSleep != null;
                        html += '<div style="margin-top:6px;">';
                        html += '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">';
                        html += '<span style="font-size:11px;" title="Current value on device">💤 ' + (deviceMin != null ? deviceMin + ' min' : '—') + '</span>';
                        html += '<input type="number" id="sleepDur_' + esc(pid) + '" value="' + inputVal + '" min="0.5" max="120" step="0.5" placeholder="min" oninput="_userSleepDurValues[\\'' + esc(pid) + '\\']=this.value" style="width:50px;padding:1px 4px;border:1px solid ' + (hasPendingOrUser ? 'var(--color-warning)' : 'var(--border-light)') + ';border-radius:4px;font-size:11px;background:var(--bg-card);color:var(--text-primary);">';
                        html += '<span style="font-size:10px;">min</span>';
                        html += '<button onclick="hoSetSleepDuration(\\'' + esc(pid) + '\\')" style="padding:2px 8px;font-size:10px;border:1px solid var(--border-light);border-radius:4px;cursor:pointer;background:var(--bg-tile);color:var(--text-secondary);">Set</button>';
                        html += '</div>';
                        html += '<div id="sleepDurPending_' + esc(pid) + '" style="color:var(--color-warning);font-size:10px;margin-top:2px;' + (pendingSleep != null ? '' : 'display:none;') + '" title="Pending: will apply when probe wakes">' + (pendingSleep != null ? '⏳ Pending: ' + pendingSleep + ' min — applies on wake' : '') + '</div>';
                        html += '</div>';
                    }
                    // Row 4d: Sleep Now
                    if (es.sleep_now) {
                        html += '<div style="margin-top:6px;">';
                        html += '<button onclick="hoPressSleepNow(\\'' + esc(pid) + '\\')" style="padding:2px 8px;font-size:10px;border:1px solid var(--color-info);border-radius:4px;cursor:pointer;background:transparent;color:var(--color-info);" title="Force probe to sleep now (starts the sleep duration countdown immediately)">Sleep Now</button>';
                        html += '</div>';
                    }
                    html += '</div>';
                }

                // --- Section 5: Actions (Calibrate + Wake Schedule) ---
                var _ppWake = (timelineData.probe_prep || {})[pid];
                var _hasZones = (probe.zone_mappings || []).length > 0;
                if (_hasZones) {
                    var _zoneSkipMap = {};
                    for (var _zsi = 0; _zsi < probeZones.length; _zsi++) {
                        var _zsEid = probeZones[_zsi];
                        var _zsInfo = perZone[_zsEid];
                        _zoneSkipMap[_zsEid] = _zsInfo ? !!_zsInfo.skip : false;
                    }
                    window['_wakePrep_' + pid] = _ppWake;
                    window['_wakeSkip_' + pid] = _zoneSkipMap;
                    window['_wakeScheduleDisabled_' + pid] = !!(probe.wake_schedule_disabled);
                }
                const _hasCalibrate = es.calibrate_dry && es.calibrate_dry.length > 0;
                if (_hasZones || _hasCalibrate) {
                    html += '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;padding-top:8px;border-top:1px solid var(--border-light);">';
                    if (_hasCalibrate) {
                        html += '<button onclick="hoShowCalibrationModal(\\'' + esc(pid) + '\\')" style="padding:2px 8px;font-size:10px;border:1px solid var(--color-warning);border-radius:4px;cursor:pointer;background:transparent;color:var(--color-warning);" title="Calibrate moisture sensors">Calibrate</button>';
                    }
                    if (_hasZones) {
                        var _wsDisabled = window['_wakeScheduleDisabled_' + pid] || false;
                        var _wsColor = _wsDisabled ? 'var(--text-muted, #666)' : 'var(--color-success, #2ecc71)';
                        var _wsBorder = _wsDisabled ? 'var(--border-light)' : 'var(--color-success, #2ecc71)';
                        var _wsBg = _wsDisabled ? 'var(--bg-tile)' : 'transparent';
                        html += '<button id="hoWakeSchedBtn_' + esc(pid) + '" onclick="hoShowWakeSchedule(\\'' + esc(pid) + '\\')" style="padding:2px 8px;font-size:10px;border:1px solid ' + _wsBorder + ';border-radius:4px;cursor:pointer;background:' + _wsBg + ';color:' + _wsColor + ';" title="View probe wake schedule">Wake Schedule</button>';
                    }
                    html += '</div>';
                }

                // Zone summary + edit toggle
                const zones = probe.zone_mappings || [];
                html += '<div style="margin-top:8px;display:flex;justify-content:space-between;align-items:center;">';
                if (zones.length > 0) {
                    html += '<span style="font-size:11px;color:var(--text-secondary-alt);"><strong>' + zones.length + '</strong> zone' + (zones.length !== 1 ? 's' : '') + ' mapped</span>';
                } else {
                    html += '<span style="font-size:11px;color:var(--text-muted);font-style:italic;">No zones mapped</span>';
                }
                html += '<a href="#" onclick="hoToggleProbeZones(\\'' + esc(pid) + '\\');return false;" style="font-size:11px;">Edit Zones</a>';
                html += '</div>';
                // Collapsible zone assignment
                html += '<div id="hoProbeZones_' + esc(pid) + '" style="display:none;margin-top:8px;border-top:1px solid var(--border-light);padding-top:8px;">';
                html += '<div style="display:flex;gap:6px;margin-bottom:6px;">';
                html += '<button class="btn btn-secondary btn-sm" onclick="hoProbeZonesSelectAll(\\'' + esc(pid) + '\\',true)">Select All</button>';
                html += '<button class="btn btn-secondary btn-sm" onclick="hoProbeZonesSelectAll(\\'' + esc(pid) + '\\',false)">Select None</button>';
                html += '</div>';
                html += '<div id="hoProbeZoneCbs_' + esc(pid) + '" style="font-size:12px;">Loading zones...</div>';
                html += '<button class="btn btn-primary btn-sm" style="margin-top:6px;" onclick="hoSaveProbeZones(\\'' + esc(pid) + '\\')">Save Zone Mapping</button>';
                html += '</div>';
                html += '</div>';
            }
            html += '</div>';
        }

        // Cellular Probe tiles
        if (cellularCount > 0) {
            html += '<div style="margin-top:16px;border-top:1px solid var(--border-light);padding-top:12px;">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">';
            html += '<span style="font-size:13px;font-weight:600;display:inline-flex;align-items:center;gap:4px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="flex-shrink:0;"><path d="M2 22V17h3v5H2zm5 0V14h3v8H7zm5 0V11h3v11h-3zm5 0V7h3v15h-3z"/><path d="M4.5 2L2 6h5L4.5 2z" stroke="currentColor" stroke-width="1.5" fill="currentColor"/><line x1="4.5" y1="6" x2="4.5" y2="10" stroke="currentColor" stroke-width="1.5"/></svg> Cellular Probes</span>';
            html += '</div>';
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;">';
            for (const [pid, probe] of Object.entries(cellularProbes)) {
                const sensors = probe.sensors_live || {};
                html += '<div style="background:var(--bg-tile);border-radius:10px;padding:12px;border:1px solid var(--border-light);">';
                // Header with cellular badge
                var cpZones = probe.zone_mappings || [];
                var cpSkipBadges = '';
                for (var cpzi = 0; cpzi < cpZones.length; cpzi++) {
                    var cpzEid = cpZones[cpzi];
                    var cpzInfo = perZone[cpzEid];
                    var cpzNum = (cpzEid.match(/zone[_]?(\\d+)/i) || [])[1] || '?';
                    if (cpzInfo && cpzInfo.skip) {
                        cpSkipBadges += ' <span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:var(--bg-danger-light);color:var(--color-danger);">Z' + cpzNum + ' Skip</span>';
                    } else if (cpzInfo && cpzInfo.moisture_multiplier != null && cpzInfo.moisture_multiplier !== 1.0) {
                        cpSkipBadges += ' <span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:var(--bg-warning);color:var(--text-warning);">Z' + cpzNum + ' ' + cpzInfo.moisture_multiplier.toFixed(2) + 'x</span>';
                    } else {
                        var cpmmVal = cpzInfo ? (cpzInfo.moisture_multiplier != null ? cpzInfo.moisture_multiplier.toFixed(2) : '1.00') : '1.00';
                        cpSkipBadges += ' <span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:var(--bg-tile);color:var(--text-muted);border:1px solid var(--border-light);">Z' + cpzNum + ' ' + cpmmVal + 'x</span>';
                    }
                }
                html += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:' + (cpSkipBadges ? '2' : '10') + 'px;">';
                html += '<span style="font-weight:600;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + esc(probe.display_name || pid) + '</span>';
                html += '<span style="display:inline-flex;align-items:center;gap:2px;padding:1px 6px;border-radius:4px;font-size:9px;font-weight:700;background:transparent;color:var(--text-success-dark);border:1px solid var(--text-success-dark);flex-shrink:0;"><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><path d="M2 22V17h3v5H2zm5 0V14h3v8H7zm5 0V11h3v11h-3zm5 0V7h3v15h-3z"/><path d="M4.5 2L2 6h5L4.5 2z" stroke="currentColor" stroke-width="1.5" fill="currentColor"/><line x1="4.5" y1="6" x2="4.5" y2="10" stroke="currentColor" stroke-width="1.5"/></svg> Cellular</span>';
                html += '</div>';
                if (cpSkipBadges) {
                    html += '<div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:8px;">' + cpSkipBadges + '</div>';
                }
                // Depth readings as horizontal bars
                for (const depth of ['shallow', 'mid', 'deep']) {
                    const s = sensors[depth];
                    if (!s) continue;
                    const val = s.value != null ? s.value : null;
                    const stale = s.stale;
                    const isCached = s.cached === true;
                    const pct = val != null ? Math.min(val, 100) : 0;
                    const color = val == null ? '#bbb' : stale ? '#999' : val > 70 ? '#3498db' : val > 40 ? '#2ecc71' : '#e67e22';
                    html += '<div style="margin-bottom:6px;">';
                    html += '<div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-bottom:2px;">';
                    html += '<span>' + depth.charAt(0).toUpperCase() + depth.slice(1) + (isCached ? ' <span style="font-size:9px;opacity:0.7;">(retained)</span>' : '') + '</span>';
                    html += '<span>' + (val != null ? val.toFixed(0) + '%' : '\\u2014') + (stale ? ' \\u23f3' : '') + '</span>';
                    html += '</div>';
                    html += '<div style="height:6px;background:var(--border-light);border-radius:3px;overflow:hidden;">';
                    html += '<div style="height:100%;width:' + pct + '%;background:' + color + ';border-radius:3px;transition:width 0.3s;"></div>';
                    html += '</div></div>';
                }
                // Signal & Battery from device_sensors_live (signal first, matching WiFi probe card order)
                var cpDevSensors = probe.device_sensors_live || {};
                var cpHasBat = cpDevSensors.battery && cpDevSensors.battery.value != null;
                var cpHasSig = cpDevSensors.signal && cpDevSensors.signal.value != null;
                if (cpHasBat || cpHasSig) {
                    html += '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;padding-top:8px;border-top:1px solid var(--border-light);font-size:11px;color:var(--text-muted);">';
                    if (cpHasSig) {
                        var csv = cpDevSensors.signal.value;
                        var csLabel = csv > -70 ? 'Good' : csv > -90 ? 'Fair' : 'Poor';
                        var csColor = csv > -70 ? 'var(--text-success-dark)' : csv > -90 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
                        html += '<span style="color:' + csColor + ';display:inline-flex;align-items:center;gap:2px;" title="Cell Signal: ' + csv.toFixed(0) + ' dBm"><svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor"><path d="M2 22V17h3v5H2zm5 0V14h3v8H7zm5 0V11h3v11h-3zm5 0V7h3v15h-3z"/><path d="M4.5 2L2 6h5L4.5 2z" stroke="currentColor" stroke-width="1.5" fill="currentColor"/><line x1="4.5" y1="6" x2="4.5" y2="10" stroke="currentColor" stroke-width="1.5"/></svg> ' + csLabel + '</span>';
                    }
                    if (cpHasBat) {
                        var cbv = cpDevSensors.battery.value;
                        var cbIcon = cbv > 50 ? '\\ud83d\\udd0b' : '\\ud83e\\udeab';
                        var cbColor = cbv > 50 ? 'var(--text-success-dark)' : cbv > 20 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
                        html += '<span style="color:' + cbColor + ';" title="Battery">' + cbIcon + ' ' + cbv.toFixed(0) + '%</span>';
                    }
                    html += '</div>';
                }
                // Last reading timestamp
                if (probe.last_reading_at) {
                    var cpAge = Math.round((Date.now() - new Date(probe.last_reading_at).getTime()) / 60000);
                    var cpAgeStr = cpAge < 1 ? 'Just now' : cpAge < 60 ? cpAge + ' min ago' : cpAge < 1440 ? Math.floor(cpAge / 60) + 'h ago' : Math.floor(cpAge / 1440) + 'd ago';
                    html += '<div style="margin-top:6px;font-size:10px;color:var(--text-muted);">Last reading: ' + cpAgeStr + '</div>';
                }
                // Moisture status reason — show the first non-empty reason from mapped zones
                var cpReasonText = '';
                for (var cpri = 0; cpri < cpZones.length; cpri++) {
                    var cprzInfo = perZone[cpZones[cpri]];
                    if (cprzInfo && cprzInfo.reason) { cpReasonText = cprzInfo.reason; break; }
                }
                if (cpReasonText) {
                    html += '<div style="margin-top:6px;font-size:10px;color:var(--text-muted);font-style:italic;">' + esc(cpReasonText) + '</div>';
                }
                // Zone count
                html += '<div style="margin-top:8px;display:flex;justify-content:space-between;align-items:center;">';
                if (cpZones.length > 0) {
                    html += '<span style="font-size:12px;color:var(--text-secondary);"><strong>' + cpZones.length + '</strong> zone' + (cpZones.length !== 1 ? 's' : '') + ' mapped</span>';
                } else {
                    html += '<span style="font-size:12px;color:var(--text-muted);font-style:italic;">No zones mapped</span>';
                }
                html += '</div>';
                // Device ID + cloud badge
                html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-top:8px;padding-top:8px;border-top:1px solid var(--border-light);">';
                html += '<span style="font-size:10px;color:var(--text-muted);font-family:monospace;" title="Particle Device ID">' + esc(probe.device_id || pid) + '</span>';
                html += '<span style="font-size:9px;color:var(--text-muted);font-style:italic;">\\u2601 Cloud managed</span>';
                html += '</div>';
                html += '</div>';
            }
            html += '</div></div>';
        }

        if (wifiCount === 0 && cellularCount === 0) {
            html += '<div style="text-align:center;padding:16px;color:var(--text-muted);">No moisture probes configured. Click <strong>Manage Probes</strong> below to discover and add probes.</div>';
        }

        // Expandable sections
        // Settings
        html += '<div style="margin-top:16px;border-top:1px solid var(--border-light);padding-top:12px;">';
        html += '<div style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;" onclick="toggleMoistureSection(\\'settings\\')">';
        html += '<span style="font-size:13px;font-weight:600;">Settings</span>';
        html += '<span id="moistureSettingsChevron" style="font-size:12px;color:var(--text-muted);">' + (_moistureExpanded.settings ? '▼' : '▶') + '</span>';
        html += '</div>';
        html += '<div id="moistureSettingsBody" style="display:' + (_moistureExpanded.settings ? 'block' : 'none') + ';margin-top:10px;">';

        // Enable toggle
        html += '<label style="display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer;margin-bottom:12px;">';
        html += '<input type="checkbox" id="moistureEnabled" ' + (settings.enabled ? 'checked' : '') + '> Enable Moisture Control</label>';

        // Schedule sync toggle
        html += '<label style="display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer;margin-bottom:12px;">';
        html += '<input type="checkbox" id="moistureScheduleSync" ' + (settings.schedule_sync_enabled !== false ? 'checked' : '') + '> Sync Schedules to Gophr Probes</label>';
        html += '<div style="font-size:11px;color:var(--text-muted);margin-bottom:12px;margin-top:-8px;">Syncs wake times to probes and dynamically manages sleep between mapped zones during runs.</div>';

        // Wake before minutes
        html += '<div style="margin-bottom:12px;">';
        html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Wake Before Zone Start</label>';
        html += '<div style="display:grid;grid-template-columns:120px 1fr;gap:8px;align-items:center;">';
        html += '<input type="number" id="moistureWakeBefore" value="' + (settings.wake_before_minutes || 10) + '" min="2" max="60" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;">';
        html += '<span style="font-size:12px;color:var(--text-muted);">minutes — how early the probe wakes before its mapped zone runs</span>';
        html += '</div></div>';

        // Max wake time
        html += '<div style="margin-bottom:12px;">';
        html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Max Wake Time</label>';
        html += '<div style="display:grid;grid-template-columns:120px 1fr;gap:8px;align-items:center;">';
        html += '<input type="number" id="moistureMaxWake" value="' + (settings.max_wake_minutes != null ? settings.max_wake_minutes : 120) + '" min="0" max="480" step="1" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;">';
        html += '<span style="font-size:12px;color:var(--text-muted);">minutes — auto re-enables sleep if exceeded (0 = unlimited)</span>';
        html += '</div></div>';

        // Stale threshold
        html += '<div style="margin-bottom:12px;">';
        html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Stale Reading Threshold</label>';
        html += '<div style="display:grid;grid-template-columns:120px 1fr;gap:8px;align-items:center;">';
        html += '<input type="number" id="moistureStaleMin" value="' + (settings.stale_reading_threshold_minutes || 120) + '" min="5" max="1440" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;">';
        html += '<span style="font-size:12px;color:var(--text-muted);">minutes — readings older than this are ignored</span>';
        html += '</div></div>';

        // Multi-Probe Mode
        var mpm = settings.multi_probe_mode || 'conservative';
        html += '<div style="margin-bottom:12px;">';
        html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Multi-Probe Mode</label>';
        html += '<div style="font-size:11px;color:var(--text-muted);margin-bottom:4px;">How to combine readings when multiple probes are mapped to the same zone</div>';
        html += '<select id="moistureMultiProbeMode" style="width:100%;padding:6px 10px;border-radius:6px;border:1px solid var(--border-input);background:var(--bg-input);color:var(--text-primary);font-size:13px;">';
        html += '<option value="conservative"' + (mpm === 'conservative' ? ' selected' : '') + '>Conservative \\u2014 use wettest probe (skip if any probe is saturated)</option>';
        html += '<option value="average"' + (mpm === 'average' ? ' selected' : '') + '>Average \\u2014 blend all probe readings (skip if majority saturated)</option>';
        html += '<option value="optimistic"' + (mpm === 'optimistic' ? ' selected' : '') + '>Optimistic \\u2014 use driest probe (skip only if all probes saturated)</option>';
        html += '</select></div>';

        // Root Zone Thresholds (gradient-based algorithm)
        const dt = settings.default_thresholds || {};
        html += '<div style="margin-bottom:12px;">';
        html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Root Zone Thresholds — Mid Sensor (%)</label>';
        html += '<div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">The <strong>mid sensor</strong> (root zone — where grass roots live) drives all watering decisions. Shallow detects rain; deep guards against over-irrigation.</div>';
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
        for (const [key, label, hint] of [
            ['root_zone_skip','Skip — Saturated (mid)','Mid sensor ≥ this → skip watering entirely'],
            ['root_zone_wet','Wet (mid)','Mid sensor ≥ this → reduce watering'],
            ['root_zone_optimal','Optimal (mid)','Mid sensor around this → normal watering (1.0x)'],
            ['root_zone_dry','Dry (mid)','Mid sensor ≤ this → increase watering']
        ]) {
            html += '<div><label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:2px;">' + label + '</label>';
            html += '<input type="number" id="moistureThresh_' + key + '" value="' + (dt[key] != null ? dt[key] : '') + '" min="0" max="100" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;" title="' + hint + '"></div>';
        }
        html += '</div>';
        html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:8px;">';
        for (const [key, label] of [['max_increase_percent','Max Increase %'], ['max_decrease_percent','Max Decrease %'], ['rain_boost_threshold','Rain Delta']]) {
            html += '<div><label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:2px;">' + label + '</label>';
            html += '<input type="number" id="moistureThresh_' + key + '" value="' + (dt[key] != null ? dt[key] : '') + '" min="0" max="100" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;"></div>';
        }
        html += '</div></div>';

        html += '<button class="btn btn-primary btn-sm" style="margin-top:4px;" onclick="saveMoistureSettings()">Save Settings</button>';
        html += '</div></div>';

        // Probe Management
        html += '<div style="margin-top:12px;border-top:1px solid var(--border-light);padding-top:12px;">';
        html += '<div style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;" onclick="toggleMoistureSection(\\'management\\')">';
        html += '<span style="font-size:13px;font-weight:600;">Manage Probes</span>';
        html += '<span id="moistureManagementChevron" style="font-size:12px;color:var(--text-muted);">' + (_moistureExpanded.management ? '▼' : '▶') + '</span>';
        html += '</div>';
        html += '<div id="moistureManagementBody" style="display:' + (_moistureExpanded.management ? 'block' : 'none') + ';margin-top:10px;">';

        // Existing WiFi probes — simple management cards (cellular probes are managed from cloud)
        if (wifiCount > 0) {
            for (const [pid, probe] of Object.entries(wifiProbes)) {
                const ss = probe.sensors || {};
                const es = probe.extra_sensors || {};
                const depthLabels = {shallow: 'Shallow', mid: 'Mid', deep: 'Deep'};
                html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;margin-bottom:8px;border:1px solid var(--border-light);">';
                html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
                html += '<div style="display:flex;align-items:center;gap:6px;">';
                html += '<strong style="font-size:14px;">' + esc(probe.display_name || pid) + '</strong>';
                html += '<a href="#" onclick="renameProbe(\\'' + esc(pid) + '\\');return false;" title="Rename probe" style="font-size:12px;color:var(--text-muted);text-decoration:none;">&#9998;</a>';
                html += '</div>';
                html += '<div style="display:flex;gap:6px;">';
                html += '<button class="btn btn-secondary btn-sm" onclick="updateProbeEntities(\\'' + esc(pid) + '\\')">Update Entities</button>';
                html += '<button class="btn btn-danger btn-sm" onclick="deleteMoistureProbe(\\'' + esc(pid) + '\\')">Remove</button>';
                html += '</div>';
                html += '</div>';
                // Sensor depth pills
                html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:6px;">';
                for (const depth of ['shallow', 'mid', 'deep']) {
                    if (ss[depth]) {
                        html += '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--bg-success-light);color:var(--text-success-dark);">' + depthLabels[depth] + '</span>';
                    } else {
                        html += '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--bg-hover);color:var(--text-muted);">' + depthLabels[depth] + ': —</span>';
                    }
                }
                html += '</div>';
                // Device sensor pills — show ALL detected entities
                const _extraLabels = [];
                if (es.wifi) _extraLabels.push('WiFi');
                if (es.battery) _extraLabels.push('Batt');
                if (es.sleep_duration) _extraLabels.push('Sleep');
                if (es.sleep_disabled) _extraLabels.push('Sleep Toggle');
                if (es.status_led) _extraLabels.push('Status LED');
                if (es.sleep_duration_number) _extraLabels.push('Sleep Control');
                if (es.solar_charging) _extraLabels.push('Solar');
                if (es.sleep_now) _extraLabels.push('Sleep Now');
                if (es.calibrate_dry && es.calibrate_dry.length > 0) _extraLabels.push('Calibrate');
                if (es.min_awake_minutes) _extraLabels.push('Min Awake');
                if (es.max_awake_minutes) _extraLabels.push('Max Awake');
                if (es.schedule_times && es.schedule_times.length) _extraLabels.push('Schedule (' + es.schedule_times.length + ')');
                if (_extraLabels.length > 0) {
                    html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:4px;">';
                    for (const lbl of _extraLabels) {
                        html += '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--bg-success-light);color:var(--text-success-dark);">' + lbl + '</span>';
                    }
                    html += '</div>';
                }
                // Zone count
                const zc = (probe.zone_mappings || []).length;
                html += '<div style="font-size:11px;color:var(--text-muted);margin-top:4px;">' + zc + ' zone' + (zc !== 1 ? 's' : '') + ' mapped</div>';
                html += '</div>';
            }
        }

        // Add probe from device — device picker
        html += '<div style="margin-top:8px;">';
        html += '<label style="font-size:13px;font-weight:600;display:block;margin-bottom:6px;">Add Probe from Device</label>';
        html += '<div style="display:flex;gap:8px;align-items:start;">';
        html += '<div style="flex:1;">';
        html += '<select id="hoMoistureDeviceSelect" onchange="onHoMoistureDeviceChange()" style="width:100%;padding:8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;">';
        html += '<option value="">-- Select a Gophr device --</option>';
        html += '</select>';
        html += '<p id="hoMoistureFilterToggle" style="display:none;font-size:12px;color:var(--text-muted);margin-top:4px;"></p>';
        html += '</div>';
        html += '<button class="btn btn-secondary btn-sm" onclick="refreshHoMoistureDevices()" style="white-space:nowrap;">Refresh</button>';
        html += '</div></div>';
        html += '<div id="hoMoistureDeviceSensors" style="margin-top:10px;"></div>';
        html += '</div></div>';

        // --- Probe History Section (collapsible) ---
        html += '<div style="margin-top:16px;border-top:1px solid var(--border-light);padding-top:12px;">';
        html += '<div style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;" onclick="toggleProbeHistory()">';
        html += '<span style="font-size:13px;font-weight:600;display:inline-flex;align-items:center;gap:4px;">\\ud83d\\udcca Probe History</span>';
        html += '<div style="display:flex;align-items:center;gap:6px;">';
        html += '<select id="probeHistoryFilter" onclick="event.stopPropagation()" onchange="renderProbeHistory()" style="padding:3px 6px;border:1px solid var(--border-input);border-radius:6px;font-size:11px;background:var(--bg-input,var(--bg-tile));color:var(--text-primary);max-width:130px;">';
        html += '<option value="">All Probes</option>';
        // WiFi probes
        for (const [pid, p] of Object.entries(wifiProbes)) {
            html += '<option value="' + esc(pid) + '">' + esc(p.display_name || pid) + '</option>';
        }
        // Cellular probes
        for (const [cpid, cp] of Object.entries(cellularProbes)) {
            html += '<option value="' + esc(cpid) + '">' + esc(cp.display_name || cpid) + ' (Cellular)</option>';
        }
        html += '</select>';
        html += '<select id="probeHistoryRange" onclick="event.stopPropagation()" onchange="loadProbeHistory()" style="padding:3px 6px;border:1px solid var(--border-input);border-radius:6px;font-size:11px;background:var(--bg-input,var(--bg-tile));color:var(--text-primary);">';
        html += '<option value="24">24 hours</option>';
        html += '<option value="168" selected>7 days</option>';
        html += '<option value="720">30 days</option>';
        html += '<option value="2160">90 days</option>';
        html += '</select>';
        html += '<span id="probeHistoryChevron" style="font-size:12px;color:var(--text-muted);">\\u25b6</span>';
        html += '</div></div>';
        html += '<div id="probeHistoryBody" style="display:none;margin-top:10px;">';
        html += '<div style="text-align:center;padding:8px;color:var(--text-muted);font-size:12px;">Click to load probe history</div>';
        html += '</div></div>';

        body.innerHTML = html;
        // Populate device picker after DOM is ready
        loadHoMoistureDevices();
    } catch (e) {
        console.error('[MOISTURE] loadMoisture failed:', e);
        card.style.display = 'none';
    }
}

// --- Probe History ---
let _probeHistoryOpen = false;
let _probeHistoryEvents = [];

function toggleProbeHistory() {
    _probeHistoryOpen = !_probeHistoryOpen;
    const body = document.getElementById('probeHistoryBody');
    const chevron = document.getElementById('probeHistoryChevron');
    if (body) body.style.display = _probeHistoryOpen ? 'block' : 'none';
    if (chevron) chevron.textContent = _probeHistoryOpen ? '\\u25bc' : '\\u25b6';
    if (_probeHistoryOpen && _probeHistoryEvents.length === 0) {
        loadProbeHistory();
    }
}

async function loadProbeHistory() {
    const body = document.getElementById('probeHistoryBody');
    if (!body) return;
    body.innerHTML = '<div style="text-align:center;padding:8px;color:var(--text-muted);font-size:12px;">Loading...</div>';
    try {
        const hoursRaw = (document.getElementById('probeHistoryRange') || {}).value || '168';
        const hours = parseInt(hoursRaw, 10) || 168;
        const data = await api('/history/runs?hours=' + hours);
        _probeHistoryEvents = (data.events || []).filter(e => e.source === 'moisture_probe');
        renderProbeHistory();
    } catch (e) {
        body.innerHTML = '<div style="color:var(--color-danger);font-size:12px;">Failed to load: ' + esc(e.message) + '</div>';
    }
}

function renderProbeHistory() {
    const body = document.getElementById('probeHistoryBody');
    if (!body) return;
    const filter = (document.getElementById('probeHistoryFilter') || {}).value || '';
    const events = filter ? _probeHistoryEvents.filter(e => e.probe_id === filter || (e.probe_name || '').indexOf(filter) >= 0) : _probeHistoryEvents;
    if (events.length === 0) {
        body.innerHTML = '<div style="text-align:center;padding:12px;color:var(--text-muted);font-size:12px;">No probe events in the selected time range.</div>';
        return;
    }
    var html = '<table style="width:100%;font-size:12px;border-collapse:collapse;">';
    html += '<thead><tr style="text-align:left;border-bottom:2px solid var(--border-light);color:var(--text-muted);">';
    html += '<th style="padding:5px;">Probe</th>';
    html += '<th style="padding:5px;">Event</th>';
    html += '<th style="padding:5px;">Zone</th>';
    html += '<th style="padding:5px;">Time</th>';
    html += '<th style="padding:5px;">Details</th>';
    html += '</tr></thead><tbody>';
    var shown = Math.min(events.length, 100);
    for (var i = 0; i < shown; i++) {
        var e = events[i];
        var probeName = e.probe_name || e.probe_id || '?';
        var eventCell;
        if (e.state === 'scheduled_wake') {
            eventCell = '<span style="color:var(--color-warning);font-weight:600;">Scheduled Wake</span>';
        } else if (e.state === 'probe_wake') {
            eventCell = '<span style="color:var(--color-link);font-weight:600;">Awake</span>';
        } else if (e.state === 'moisture_skip') {
            eventCell = '<span style="color:var(--color-danger);font-weight:600;">Moisture Skip</span>';
        } else if (e.state === 'watchdog_force_sleep') {
            eventCell = '<span style="color:var(--color-danger);font-weight:600;">⚠ Watchdog Sleep</span>';
        } else if (e.state === 'watchdog_retry') {
            eventCell = '<span style="color:var(--color-warning);font-weight:600;">⚠ Watchdog Retry</span>';
        } else {
            eventCell = '<span style="font-weight:600;">' + esc(e.state) + '</span>';
        }
        var zoneText = '';
        if (e.state === 'moisture_skip') {
            var skipZoneNum = (e.entity_id || '').match(/zone[_]?(\\d+)/i);
            zoneText = skipZoneNum ? 'Zone ' + skipZoneNum[1] : (e.zone_name || e.entity_id || '');
        } else if (e.mapped_zones && e.mapped_zones.length > 0) {
            zoneText = e.mapped_zones.map(function(z) {
                var n = (z.match(/zone[_]?(\\d+)/i) || [])[1] || z;
                return 'Z' + n;
            }).join(', ');
        } else {
            zoneText = e.zone_name || '-';
        }
        var detailText = '';
        if (e.state === 'moisture_skip') {
            if (e.mid_sensor_pct != null) detailText = 'Mid: ' + e.mid_sensor_pct + '%';
            if (e.reason) detailText += (detailText ? ' \\u2014 ' : '') + e.reason;
        } else if (e.state === 'scheduled_wake' || e.state === 'probe_wake') {
            if (e.mapped_zones) detailText = e.mapped_zones.length + ' zone' + (e.mapped_zones.length !== 1 ? 's' : '') + ' mapped';
        } else if (e.state === 'watchdog_force_sleep') {
            var wd = e.details || {};
            detailText = 'Awake ' + (wd.awake_minutes || '?') + 'min (limit ' + (wd.max_wake_minutes || '?') + 'min)';
            if (wd.battery != null) detailText += ' | Batt: ' + wd.battery + '%';
            if (wd.prep_state && wd.prep_state !== 'idle') detailText += ' | Prep: ' + wd.prep_state;
        } else if (e.state === 'watchdog_retry') {
            var wdr = e.details || {};
            detailText = 'Still awake ' + (wdr.minutes_since_watchdog || '?') + 'min after force sleep';
        }
        if (e.moisture_multiplier != null && e.state === 'moisture_skip') {
            detailText += (detailText ? ' | ' : '') + 'Factor: ' + e.moisture_multiplier + 'x';
        }
        var rowBg = (e.state === 'moisture_skip' || e.state === 'watchdog_force_sleep' || e.state === 'watchdog_retry') ? 'background:var(--bg-danger-light);' : e.state === 'scheduled_wake' ? 'background:var(--bg-tile);' : '';
        html += '<tr style="border-bottom:1px solid var(--border-row);' + rowBg + '">';
        html += '<td style="padding:5px;font-weight:500;">' + esc(probeName) + '</td>';
        html += '<td style="padding:5px;">' + eventCell + '</td>';
        html += '<td style="padding:5px;">' + esc(zoneText) + '</td>';
        html += '<td style="padding:5px;">' + formatTime(e.timestamp) + '</td>';
        html += '<td style="padding:5px;font-size:11px;color:var(--text-muted);">' + esc(detailText) + '</td>';
        html += '</tr>';
    }
    html += '</tbody></table>';
    if (events.length > 100) {
        html += '<div style="text-align:center;padding:4px;font-size:11px;color:var(--text-muted);">Showing 100 of ' + events.length + ' events</div>';
    }
    body.innerHTML = html;
}

// Moisture API helper (uses homeowner moisture prefix)
async function mapi(path, method = 'GET', bodyData = null) {
    const opts = { method, headers: {} };
    if (bodyData) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(bodyData);
    }
    const res = await fetch(HBASE + '/moisture' + path, opts);
    const data = await res.json();
    if (!res.ok) {
        const detail = data.detail || data.error || JSON.stringify(data);
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
    }
    return data;
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
            schedule_sync_enabled: document.getElementById('moistureScheduleSync').checked,
            wake_before_minutes: parseInt(document.getElementById('moistureWakeBefore').value) || 10,
            max_wake_minutes: parseInt(document.getElementById('moistureMaxWake').value) || 0,
            multi_probe_mode: document.getElementById('moistureMultiProbeMode').value,
            stale_reading_threshold_minutes: parseInt(document.getElementById('moistureStaleMin').value) || 120,
            default_thresholds: {
                root_zone_skip: parseInt(document.getElementById('moistureThresh_root_zone_skip').value) || 80,
                root_zone_wet: parseInt(document.getElementById('moistureThresh_root_zone_wet').value) || 65,
                root_zone_optimal: parseInt(document.getElementById('moistureThresh_root_zone_optimal').value) || 45,
                root_zone_dry: parseInt(document.getElementById('moistureThresh_root_zone_dry').value) || 30,
                max_increase_percent: parseInt(document.getElementById('moistureThresh_max_increase_percent').value) || 50,
                max_decrease_percent: parseInt(document.getElementById('moistureThresh_max_decrease_percent').value) || 50,
                rain_boost_threshold: parseInt(document.getElementById('moistureThresh_rain_boost_threshold').value) || 15,
            },
        };
        const result = await mapi('/settings', 'PUT', payload);
        showToast(result.message || 'Settings saved');
        _moistureDataCache = null;
        loadMoisture();
        loadStatus();
        loadControls();  // Refresh schedule card (factors may have changed)
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Homeowner Probe Zone Assignment ---
async function hoToggleProbeZones(probeId) {
    const el = document.getElementById('hoProbeZones_' + probeId);
    if (!el) return;
    if (el.style.display !== 'none') { el.style.display = 'none'; return; }
    el.style.display = 'block';
    const cbContainer = document.getElementById('hoProbeZoneCbs_' + probeId);
    cbContainer.innerHTML = '<div style="font-size:12px;color:var(--text-muted);">Loading zones...</div>';
    try {
        const probesData = await mapi('/probes');
        const probe = (probesData.probes || {})[probeId];
        const currentMappings = probe ? (probe.zone_mappings || []) : [];

        const zonesData = await api('/zones');
        const allZones = Array.isArray(zonesData) ? zonesData : (zonesData.zones || []);
        if (allZones.length === 0) {
            cbContainer.innerHTML = '<div style="color:var(--text-muted);">No zones found.</div>';
            return;
        }

        // Use the globally cached zone aliases (loaded at dashboard init)
        // Also refresh them in case they changed since page load
        try {
            window._currentZoneAliases = await api('/zone_aliases');
        } catch(_) {}

        // Filter out master valve / pump start relay zones
        const modes = window._zoneModes || {};
        const irrigationZones = allZones.filter(function(z) {
            const zNum = (z.entity_id.match(/zone[_]?(\\d+)/i) || [])[1] || '';
            const mode = (modes[zNum] && modes[zNum].state || '').toLowerCase();
            return !/pump|master|relay/.test(mode);
        });

        let cbHtml = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:4px;">';
        for (const z of irrigationZones) {
            const eid = z.entity_id;
            const checked = currentMappings.includes(eid) ? ' checked' : '';
            let label = resolveZoneName(eid, z.friendly_name || z.name || eid);
            cbHtml += '<label style="display:flex;align-items:center;gap:4px;cursor:pointer;padding:2px 4px;border-radius:4px;' + (checked ? 'background:var(--bg-success-light);' : '') + '">';
            cbHtml += '<input type="checkbox" data-probe="' + esc(probeId) + '" data-zone="' + esc(eid) + '"' + checked + ' style="accent-color:var(--color-primary);">';
            cbHtml += '<span style="font-size:11px;">' + esc(label) + '</span></label>';
        }
        cbHtml += '</div>';
        cbContainer.innerHTML = cbHtml;
    } catch (e) {
        cbContainer.innerHTML = '<div style="color:var(--color-danger);font-size:12px;">Failed: ' + esc(e.message) + '</div>';
    }
}

function hoProbeZonesSelectAll(probeId, selectAll) {
    const c = document.getElementById('hoProbeZoneCbs_' + probeId);
    if (!c) return;
    c.querySelectorAll('input[type="checkbox"]').forEach(function(cb) { cb.checked = selectAll; });
}

async function hoSaveProbeZones(probeId) {
    const c = document.getElementById('hoProbeZoneCbs_' + probeId);
    if (!c) return;
    const selected = [];
    c.querySelectorAll('input[type="checkbox"]').forEach(function(cb) {
        if (cb.checked) selected.push(cb.getAttribute('data-zone'));
    });
    try {
        await mapi('/probes/' + encodeURIComponent(probeId), 'PUT', { zone_mappings: selected });
        showToast('Zone mapping updated (' + selected.length + ' zones)');
        _moistureDataCache = null;
        loadMoisture();
        loadControls();  // Refresh schedule card (zone mappings affect factors)
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Homeowner Moisture Device Picker ---
let _hoMoistureShowAll = false;
let _hoAutodetectCache = null;

async function loadHoMoistureDevices(showAll) {
    const select = document.getElementById('hoMoistureDeviceSelect');
    if (!select) return;
    try {
        const all = showAll !== undefined ? showAll : _hoMoistureShowAll;
        const data = await mapi('/devices' + (all ? '?show_all=true' : ''));
        let devices = data.devices || [];
        const totalCount = data.total_count || devices.length;
        const filtered = data.filtered !== false;

        // Exclude devices that already have a probe configured
        try {
            const probeData = await mapi('/probes');
            const existingDeviceIds = new Set();
            for (const p of Object.values(probeData.probes || {})) {
                if (p.device_id) existingDeviceIds.add(p.device_id);
            }
            if (existingDeviceIds.size > 0) {
                devices = devices.filter(function(d) { return !existingDeviceIds.has(d.id); });
            }
        } catch (_) {}

        select.innerHTML = '<option value="">-- Select a Gophr device --</option>';
        for (const d of devices) {
            const label = d.manufacturer || d.model ? d.name + ' (' + [d.manufacturer, d.model].filter(Boolean).join(' ') + ')' : d.name;
            const opt = document.createElement('option');
            opt.value = d.id;
            opt.textContent = label;
            select.appendChild(opt);
        }

        const toggleEl = document.getElementById('hoMoistureFilterToggle');
        if (filtered && devices.length < totalCount) {
            toggleEl.innerHTML = 'Showing ' + devices.length + ' Gophr device' + (devices.length !== 1 ? 's' : '') +
                ' of ' + totalCount + ' total. <a href="#" onclick="_hoMoistureShowAll=true;loadHoMoistureDevices(true);return false;">Show all devices</a>';
            toggleEl.style.display = '';
        } else if (!filtered && totalCount > 0) {
            toggleEl.innerHTML = 'Showing all ' + totalCount + ' devices. <a href="#" onclick="_hoMoistureShowAll=false;loadHoMoistureDevices(false);return false;">Show only Gophr devices</a>';
            toggleEl.style.display = '';
        } else {
            toggleEl.style.display = 'none';
        }
    } catch (e) {
        select.innerHTML = '<option value="">Failed to load devices</option>';
    }
}

function refreshHoMoistureDevices() {
    loadHoMoistureDevices();
    showToast('Device list refreshed');
}

async function onHoMoistureDeviceChange() {
    const deviceId = document.getElementById('hoMoistureDeviceSelect').value;
    const el = document.getElementById('hoMoistureDeviceSensors');
    if (!deviceId) { el.innerHTML = ''; return; }
    el.innerHTML = '<div class="loading" style="font-size:12px;">Detecting sensors...</div>';
    try {
        const data = await mapi('/devices/' + encodeURIComponent(deviceId) + '/autodetect');
        _hoAutodetectCache = data;
        const depthSensors = data.sensors || {};
        const extraSensors = data.extra_sensors || {};
        const allSensors = data.all_sensors || [];

        let html = '<div style="background:var(--bg-tile);border-radius:8px;padding:12px;border:1px solid var(--border-light);">';

        // Auto-detected sensors summary
        const detected = [];
        if (depthSensors.shallow) detected.push('Shallow');
        if (depthSensors.mid) detected.push('Mid');
        if (depthSensors.deep) detected.push('Deep');
        const extras = [];
        if (extraSensors.wifi) extras.push('WiFi');
        if (extraSensors.battery) extras.push('Batt');
        if (extraSensors.sleep_duration) extras.push('Sleep');
        if (extraSensors.sleep_disabled) extras.push('Sleep Toggle');
        if (extraSensors.status_led) extras.push('Status LED');
        if (extraSensors.sleep_duration_number) extras.push('Sleep Control');
        if (extraSensors.solar_charging) extras.push('Solar');
        if (extraSensors.sleep_now) extras.push('Sleep Now');
        if (extraSensors.calibrate_dry) extras.push('Calibrate');

        if (detected.length > 0 || extras.length > 0) {
            html += '<div style="font-size:13px;font-weight:600;margin-bottom:6px;">Auto-detected sensors</div>';
            if (detected.length > 0) {
                html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:4px;">';
                for (const d of detected) {
                    html += '<span style="font-size:11px;padding:3px 8px;border-radius:10px;background:var(--bg-success-light);color:var(--text-success-dark);">✓ ' + d + '</span>';
                }
                html += '</div>';
            }
            if (extras.length > 0) {
                html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">';
                for (const e of extras) {
                    html += '<span style="font-size:11px;padding:3px 8px;border-radius:10px;background:var(--bg-success-light);color:var(--text-success-dark);">✓ ' + e + '</span>';
                }
                html += '</div>';
            }
        } else {
            html += '<div style="color:var(--text-warning);font-size:12px;margin-bottom:8px;">Could not auto-detect sensors. This device has ' + allSensors.length + ' sensor entities.</div>';
        }

        // Show all entity IDs found for this device (all domains)
        const allEntityIds = data.all_entity_ids || [];
        if (allEntityIds.length > 0) {
            html += '<details style="margin-bottom:8px;"><summary style="font-size:11px;color:var(--text-muted);cursor:pointer;">All device entities (' + allEntityIds.length + ')</summary>';
            html += '<div style="background:var(--bg-elevated);border-radius:6px;padding:8px;margin-top:4px;max-height:150px;overflow-y:auto;">';
            for (const eid of allEntityIds) {
                const domain = eid.split('.')[0] || '';
                const isMatched = (Object.values(depthSensors).includes(eid) || Object.values(extraSensors).includes(eid));
                const color = isMatched ? 'var(--text-success-dark)' : 'var(--text-muted)';
                const icon = isMatched ? '✓ ' : '  ';
                html += '<div style="font-size:10px;color:' + color + ';font-family:monospace;padding:1px 0;">' + icon + esc(eid) + '</div>';
            }
            html += '</div></details>';
        }

        if (detected.length === 0) {
            var diag = data.diagnostic || {};
            var hint = diag.hint || 'Make sure this is a Gophr device with moisture sensors.';
            html += '<div style="color:var(--color-danger);font-size:12px;margin-bottom:4px;font-weight:600;">No moisture depth sensors detected</div>';
            html += '<div style="color:var(--text-muted);font-size:11px;margin-bottom:4px;">' + esc(hint) + '</div>';
            if (diag.disabled_sensors && diag.disabled_sensors.length > 0) {
                html += '<div style="background:var(--bg-warning);padding:8px 10px;border-radius:6px;margin-bottom:8px;">';
                html += '<div style="font-size:11px;font-weight:600;color:var(--text-warning);margin-bottom:4px;">Disabled entities found:</div>';
                for (var di = 0; di < diag.disabled_sensors.length; di++) {
                    html += '<div style="font-size:10px;color:var(--text-warning);">' + esc(diag.disabled_sensors[di]) + '</div>';
                }
                html += '</div>';
            }
            if (diag.sensor_count !== undefined) {
                html += '<div style="color:var(--text-muted);font-size:11px;margin-bottom:2px;">Sensors: ' + diag.sensor_count + ' found, ' + (diag.filtered_sensor_count || 0) + ' filtered, ' + (diag.registry_entities_for_device || 0) + ' registry matches</div>';
            }
            if (diag.sensor_entities && diag.sensor_entities.length > 0) {
                html += '<div style="color:var(--text-muted);font-size:10px;margin-bottom:4px;">Entities: ' + diag.sensor_entities.join(', ') + '</div>';
            }
            html += '<div style="color:var(--text-muted);font-size:11px;margin-bottom:8px;">Device ID: ' + esc(data.device_id || '?') + '</div>';
        }

        // Display name
        const select = document.getElementById('hoMoistureDeviceSelect');
        const deviceName = select.options[select.selectedIndex] ? select.options[select.selectedIndex].textContent : 'Probe';
        html += '<div style="margin-bottom:8px;"><label style="font-size:11px;color:var(--text-muted);">Display Name</label>';
        html += '<input type="text" id="hoProbeDeviceName" value="' + esc(deviceName) + '" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;box-sizing:border-box;"></div>';

        html += '<button class="btn btn-primary btn-sm" onclick="addHoProbeFromDevice()">Add Probe</button>';
        html += '</div>';
        el.innerHTML = html;
    } catch (e) {
        el.innerHTML = '<div style="color:var(--color-danger);font-size:12px;">Failed to detect sensors: ' + esc(e.message) + '</div>';
    }
}

async function addHoProbeFromDevice() {
    if (!_hoAutodetectCache) { showToast('Select a device first', 'error'); return; }
    const sensors = _hoAutodetectCache.sensors || {};
    const extraSensors = _hoAutodetectCache.extra_sensors || {};
    const deviceId = _hoAutodetectCache.device_id;

    if (!sensors.shallow && !sensors.mid && !sensors.deep) {
        showToast('No moisture sensors detected on this device', 'error');
        return;
    }

    const nameInput = document.getElementById('hoProbeDeviceName');
    const displayName = nameInput ? nameInput.value.trim() : 'Gophr Probe';
    const probeId = 'probe_' + displayName.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');

    try {
        // Clean sensors — remove null values
        const cleanSensors = {};
        for (const [k, v] of Object.entries(sensors)) { if (v) cleanSensors[k] = v; }

        await mapi('/probes', 'POST', {
            probe_id: probeId,
            display_name: displayName,
            device_id: deviceId,
            sensors: cleanSensors,
            extra_sensors: extraSensors,
            zone_mappings: [],
        });
        showToast('Probe "' + displayName + '" added — use Edit Zones to assign zones');
        _moistureDataCache = null;
        _moistureExpanded.management = true;
        await loadMoisture();
        // Scroll to the management section so user sees their new probe
        const mgmtBody = document.getElementById('moistureManagementBody');
        if (mgmtBody) mgmtBody.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (e) { showToast(e.message || 'Failed to add probe', 'error'); }
}

async function deleteMoistureProbe(probeId) {
    if (!confirm('Remove probe "' + probeId + '"?')) return;
    try {
        await mapi('/probes/' + encodeURIComponent(probeId), 'DELETE');
        showToast('Probe removed');
        _moistureDataCache = null;
        _moistureExpanded.management = true;
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

async function renameProbe(probeId) {
    // Get current name from cached data
    var currentName = probeId;
    try {
        var data = await mapi('/probes');
        var probe = (data.probes || {})[probeId];
        if (probe) currentName = probe.display_name || probeId;
    } catch(e) {}
    var newName = prompt('Rename probe:', currentName);
    if (!newName || newName.trim() === '' || newName.trim() === currentName) return;
    try {
        await mapi('/probes/' + encodeURIComponent(probeId), 'PUT', { display_name: newName.trim() });
        showToast('Probe renamed to "' + newName.trim() + '"');
        _moistureDataCache = null;
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

async function updateProbeEntities(probeId) {
    try {
        showToast('Re-detecting entities...', 'info');
        var result = await mapi('/probes/' + encodeURIComponent(probeId) + '/update-entities', 'POST');
        if (result.changes && result.changes.length > 0) {
            showToast('Updated: ' + result.changes.join(', '));
        } else {
            showToast('No new entities found');
        }
        if (result.diagnostic && result.diagnostic.disabled_sensors) {
            showToast(result.diagnostic.disabled_sensors.length + ' sensors disabled in HA — enable them first', 'warning');
        }
        _moistureDataCache = null;
        _moistureExpanded.management = true;
        loadMoisture();
    } catch (e) { showToast(e.message || 'Failed to update entities', 'error'); }
}

async function hoSetSleepDuration(probeId) {
    const input = document.getElementById('sleepDur_' + probeId);
    if (!input) return;
    const minutes = parseFloat(input.value);
    if (isNaN(minutes) || minutes < 0.5 || minutes > 120) {
        showToast('Sleep duration must be 0.5-120 minutes', 'error');
        return;
    }
    // Store user value so it survives DOM rebuilds
    _userSleepDurValues[probeId] = input.value;
    await _doSetSleepDuration(probeId, minutes, false);
}

async function _doSetSleepDuration(probeId, minutes, force) {
    try {
        const result = await mapi('/probes/' + encodeURIComponent(probeId) + '/sleep-duration', 'PUT', { minutes: minutes, force: !!force });
        if (result.status === 'conflict' && result.conflicts && result.conflicts.length > 0) {
            _pendingForceSleep = { probeId: probeId, minutes: minutes };
            var html = _buildConflictModalHtml(result.conflicts);
            html += '<div style="display:flex;gap:8px;justify-content:flex-end;margin-top:12px;">' +
                '<button class="btn btn-secondary" onclick="closeDynamicModal()">Cancel</button>' +
                '<button class="btn btn-primary" onclick="_forceSleepSet()">Apply Anyway</button></div>';
            showModal('Probe Wake Conflict', html, '480px');
            return;
        }
        if (result.status === 'pending') {
            showToast('Sleep ' + minutes + ' min queued — will apply when probe wakes', 'warning');
            // Show pending indicator immediately (before full reload)
            _showPendingInline('sleepDurPending_' + probeId, '\\u23f3 Pending: ' + minutes + ' min \\u2014 applies on wake');
            var input = document.getElementById('sleepDur_' + probeId);
            if (input) input.style.borderColor = 'var(--color-warning)';
        } else {
            showToast('Sleep duration set to ' + minutes + ' min');
            // Value was applied — clear user override so input shows device value
            delete _userSleepDurValues[probeId];
        }
        _moistureDataCache = null;
        await loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

async function hoToggleSleepDisabled(probeId, disabled) {
    try {
        const result = await mapi('/probes/' + encodeURIComponent(probeId) + '/sleep-disabled', 'PUT', { disabled: disabled });
        const action = disabled ? 'disabled' : 'enabled';
        if (result.status === 'pending') {
            showToast('Sleep ' + action + ' queued — will apply when probe wakes', 'warning');
            // Show pending indicator immediately (before full reload)
            _showPendingInline('sleepDisPending_' + probeId, '\\u23f3 Pending \\u2014 applies on wake');
        } else {
            showToast('Sleep ' + action);
        }
        _moistureDataCache = null;
        await loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

function _showPendingInline(elId, text) {
    var el = document.getElementById(elId);
    if (el) {
        el.textContent = text;
        el.style.display = '';
    }
}

async function hoPressSleepNow(probeId) {
    try {
        const result = await mapi('/probes/' + encodeURIComponent(probeId) + '/sleep-now', 'POST');
        showToast(result.message || 'Sleep Now pressed');
        _moistureDataCache = null;
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Calibration Modal ---
var _calWetTimer = null;

function hoShowCalibrationModal(probeId) {
    if (_calWetTimer) { clearInterval(_calWetTimer); _calWetTimer = null; }
    var countdown = 60;

    var body = '';
    body += '<div style="font-size:13px;line-height:1.6;">';
    body += '<p style="margin-bottom:10px;"><strong>Sensor Calibration</strong> teaches the probe what "completely dry" and "fully submerged in water" look like. This ensures accurate 0\\u2013100% moisture readings.</p>';

    body += '<div style="background:var(--bg-tile);border:1px solid var(--border-light);border-radius:8px;padding:10px;margin-bottom:12px;">';
    body += '<p style="margin:0 0 6px 0;font-weight:600;">Steps:</p>';
    body += '<ol style="margin:0;padding-left:20px;">';
    body += '<li>Ensure probe is <strong>awake</strong> and <strong>sleep is disabled</strong></li>';
    body += '<li>Clean and thoroughly dry the sensor prongs</li>';
    body += '<li>Press <strong>Calibrate Dry</strong> while sensors are in open air</li>';
    body += '<li>Submerge only the sensor prongs into a glass of water</li>';
    body += '<li>Wait for the Wet button to turn blue (60 seconds)</li>';
    body += '<li>Press <strong>Calibrate Wet</strong> while sensors are submerged</li>';
    body += '</ol>';
    body += '</div>';

    body += '<div id="calPrereqMsg" style="margin-bottom:8px;"></div>';

    body += '<div style="display:flex;gap:10px;">';
    body += '<button id="calDryBtn" onclick="hoCalibrate(\\'' + probeId + '\\', \\'dry\\')" style="flex:1;padding:10px 16px;border:2px solid var(--color-warning);border-radius:8px;background:var(--color-warning);color:#fff;font-weight:600;font-size:14px;cursor:pointer;">Calibrate Dry</button>';
    body += '<button id="calWetBtn" disabled style="flex:1;padding:10px 16px;border:2px solid var(--border-light);border-radius:8px;background:var(--bg-tile);color:var(--text-muted);font-weight:600;font-size:14px;cursor:not-allowed;">Calibrate Wet <span id="calWetCountdown">(60s)</span></button>';
    body += '</div>';

    body += '<p style="font-size:11px;color:var(--text-muted);margin-top:10px;">After calibration, readings should show ~0% in air and ~100% in water. These settings are stored on the device but recalibration may be needed over time.</p>';
    body += '</div>';

    showModal('Calibrate Probe', body);

    // Check prerequisites
    hoUpdateCalPrereqs(probeId);

    // Start 60-second countdown for Wet button
    _calWetTimer = setInterval(function() {
        countdown--;
        var span = document.getElementById('calWetCountdown');
        var btn = document.getElementById('calWetBtn');
        if (!span || !btn) { clearInterval(_calWetTimer); _calWetTimer = null; return; }
        if (countdown <= 0) {
            clearInterval(_calWetTimer);
            _calWetTimer = null;
            span.textContent = '';
            btn.disabled = false;
            btn.style.border = '2px solid #3498db';
            btn.style.background = '#3498db';
            btn.style.color = '#fff';
            btn.style.cursor = 'pointer';
            btn.title = 'Press while sensors are submerged in water';
            btn.onclick = function() { hoCalibrate(probeId, 'wet'); };
        } else {
            span.textContent = '(' + countdown + 's)';
        }
    }, 1000);
}

async function hoUpdateCalPrereqs(probeId) {
    try {
        var data = await mapi('/probes');
        var probe = (data.probes || {})[probeId];
        if (!probe) return;
        var isAwake = probe.is_awake === true;
        var ds = probe.device_sensors || {};
        var isSleepDisabled = ds.sleep_disabled && ds.sleep_disabled.value === 'on';
        var prereqDiv = document.getElementById('calPrereqMsg');
        var dryBtn = document.getElementById('calDryBtn');
        if (!prereqDiv || !dryBtn) return;

        if (!isAwake || !isSleepDisabled) {
            var reasons = [];
            if (!isAwake) reasons.push('probe is sleeping');
            if (!isSleepDisabled) reasons.push('sleep is not disabled');
            prereqDiv.innerHTML = '<div style="padding:8px 10px;background:var(--bg-danger-light);border-radius:6px;font-size:12px;color:var(--color-danger);">&#9888;&#65039; Cannot calibrate: ' + reasons.join(' and ') + '. Wake the probe and disable sleep before calibrating.</div>';
            dryBtn.disabled = true;
            dryBtn.style.background = 'var(--bg-tile)';
            dryBtn.style.color = 'var(--text-muted)';
            dryBtn.style.border = '2px solid var(--border-light)';
            dryBtn.style.cursor = 'not-allowed';
        } else {
            prereqDiv.innerHTML = '<div style="padding:8px 10px;background:var(--bg-success-light);border-radius:6px;font-size:12px;color:var(--text-success-dark);">&#10003; Probe is awake and sleep is disabled. Ready to calibrate.</div>';
            dryBtn.disabled = false;
            dryBtn.style.background = 'var(--color-warning)';
            dryBtn.style.color = '#fff';
            dryBtn.style.border = '2px solid var(--color-warning)';
            dryBtn.style.cursor = 'pointer';
        }
    } catch(e) { console.error('Cal prereq check failed', e); }
}

async function hoCalibrate(probeId, action) {
    var btn = action === 'dry' ? document.getElementById('calDryBtn') : document.getElementById('calWetBtn');
    if (btn) { btn.disabled = true; btn.textContent = 'Pressing...'; }
    try {
        var result = await mapi('/probes/' + encodeURIComponent(probeId) + '/calibrate', 'POST', { action: action });
        showToast(result.message || ('Calibrate ' + action + ' pressed'));
        if (btn) {
            btn.textContent = action === 'dry' ? '\\u2713 Dry Done!' : '\\u2713 Wet Done!';
            btn.style.background = 'var(--color-success)';
            btn.style.border = '2px solid var(--color-success)';
            btn.style.color = '#fff';
        }
        _moistureDataCache = null;
        loadMoisture();
    } catch (e) {
        showToast(e.message, 'error');
        if (btn) {
            btn.disabled = false;
            btn.textContent = action === 'dry' ? 'Calibrate Dry' : 'Calibrate Wet';
        }
    }
}

async function hoShowWakeSchedule(probeId) {
    /* Show spinner while recalculating */
    var spinnerHtml = '<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:32px 0;">' +
        '<div class="water-spinner"></div>' +
        '<div style="margin-top:14px;font-size:13px;color:var(--text-muted);">Recalculating wake schedule...</div></div>';
    showModal('Wake Schedule', spinnerHtml, '440px');

    /* Force recalculate then fetch fresh timeline */
    try {
        var timeline = await mapi('/schedule-timeline/recalculate', 'POST');
        var freshPrep = (timeline.probe_prep || {})[probeId] || null;
        if (freshPrep) window['_wakePrep_' + probeId] = freshPrep;
    } catch(e) {
        /* If recalc fails, fall back to cached data */
    }

    var prep = window['_wakePrep_' + probeId];
    var skipMap = window['_wakeSkip_' + probeId] || {};
    var body = '';
    /* Check if ALL mapped zones are set to skip (probe is saturated) */
    var skipKeys = Object.keys(skipMap);
    var allSkipping = skipKeys.length > 0 && skipKeys.every(function(k) { return skipMap[k]; });
    if (allSkipping) {
        body = '<div style="padding:8px 0;"><div style="display:flex;align-items:center;gap:8px;padding:8px 10px;background:var(--bg-danger-light);border-radius:6px;margin-bottom:8px;"><span style="font-size:16px;">&#9940;</span><div style="font-size:13px;color:var(--color-danger);font-weight:500;">All mapped zones are set to skip &mdash; probe will not wake to monitor watering.</div></div><div style="font-size:12px;color:var(--text-muted);">The probe\\'s moisture readings indicate saturation. Once moisture levels drop below the skip threshold, wake scheduling will resume automatically.</div></div>';
        showModal('Wake Schedule', body);
        return;
    }
    var entries = (prep && prep.display_entries && prep.display_entries.length > 0) ? prep.display_entries : (prep && prep.prep_entries ? prep.prep_entries : []);
    if (entries.length > 0) {
        /* Sort entries by target_wake_minutes chronologically */
        var sorted = entries.slice().sort(function(a, b) {
            return a.target_wake_minutes - b.target_wake_minutes;
        });
        /* Use homeowner's configured timezone for NEXT marker */
        var _now = new Date();
        var nowMin;
        if (_homeTimezone) {
            try {
                var _parts = _now.toLocaleTimeString('en-GB', {timeZone: _homeTimezone, hour12: false}).split(':');
                nowMin = parseInt(_parts[0]) * 60 + parseInt(_parts[1]);
            } catch(e) { nowMin = _now.getHours() * 60 + _now.getMinutes(); }
        } else {
            nowMin = _now.getHours() * 60 + _now.getMinutes();
        }
        var nextIdx = -1;
        for (var ni = 0; ni < sorted.length; ni++) {
            if (sorted[ni].target_wake_minutes > nowMin && !skipMap[sorted[ni].zone_entity_id]) { nextIdx = ni; break; }
        }
        function _fmtTime(m) {
            var h = Math.floor(m / 60) % 24;
            var mn = Math.round(m % 60);
            var ap = h >= 12 ? 'PM' : 'AM';
            var h12 = h % 12 || 12;
            return h12 + ':' + (mn < 10 ? '0' : '') + mn + ' ' + ap;
        }
        body += '<div style="display:flex;flex-direction:column;gap:6px;">';
        for (var wi = 0; wi < sorted.length; wi++) {
            var we = sorted[wi];
            var wakeTimeStr = _fmtTime(we.target_wake_minutes);
            var zoneTimeStr = _fmtTime(we.zone_start_minutes || 0);
            var schedLabel = we.schedule_start_time || '';
            var isNext = (wi === nextIdx);
            var zoneSkipped = skipMap[we.zone_entity_id] || false;
            var keepAwake = we.action === 'keep_awake';
            /* Icon: skip=stop, keep_awake=eye, wake=clock */
            var icon = zoneSkipped ? '&#9940;' : keepAwake ? '&#128065;' : '&#9200;';
            body += '<div style="display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:6px;' +
                (zoneSkipped ? 'opacity:0.5;' : '') +
                (isNext && !zoneSkipped ? 'background:var(--bg-active-tile);' : '') + '">';
            body += '<span style="font-size:16px;">' + icon + '</span>';
            body += '<div style="flex:1;">';
            if (zoneSkipped) {
                body += '<div style="font-size:13px;color:var(--text-muted);text-decoration:line-through;">Wake at <strong>' + wakeTimeStr + '</strong></div>';
                body += '<div style="font-size:11px;color:var(--text-muted);">Zone ' + we.zone_num + ' — <span style="color:var(--color-danger);font-weight:500;">Skip (saturated)</span>' + (schedLabel ? ' &mdash; ' + schedLabel + ' schedule' : '') + '</div>';
            } else if (keepAwake) {
                body += '<div style="font-size:13px;' + (isNext ? 'font-weight:600;color:var(--color-warning);' : 'color:var(--text-secondary);') + '">Keep Awake</div>';
                body += '<div style="font-size:11px;color:var(--text-muted);">Zone ' + we.zone_num + ' runs at ' + zoneTimeStr + (schedLabel ? ' &mdash; ' + schedLabel + ' schedule' : '') + '</div>';
            } else {
                body += '<div style="font-size:13px;' + (isNext ? 'font-weight:600;color:var(--color-warning);' : 'color:var(--text-secondary);') + '">Wake at <strong>' + wakeTimeStr + '</strong></div>';
                body += '<div style="font-size:11px;color:var(--text-muted);">Zone ' + we.zone_num + ' runs at ' + zoneTimeStr + (schedLabel ? ' &mdash; ' + schedLabel + ' schedule' : '') + '</div>';
            }
            body += '</div>';
            if (isNext && !zoneSkipped) body += '<span style="font-size:9px;background:var(--color-warning);color:#fff;padding:2px 6px;border-radius:4px;font-weight:600;">NEXT</span>';
            if (zoneSkipped) body += '<span style="font-size:9px;background:var(--color-danger);color:#fff;padding:2px 6px;border-radius:4px;font-weight:600;">SKIP</span>';
            if (keepAwake && !zoneSkipped) body += '<span style="font-size:9px;background:var(--color-info);color:#fff;padding:2px 6px;border-radius:4px;font-weight:600;">AWAKE</span>';
            body += '</div>';
        }
        body += '</div>';
        if (prep.state && prep.state !== 'idle') {
            body += '<div style="margin-top:10px;padding:6px 8px;background:var(--bg-tile);border-radius:6px;font-size:11px;color:var(--text-muted);">Current state: <strong>' + prep.state + '</strong></div>';
        }
    } else {
        body = '<div style="font-size:13px;color:var(--text-muted);font-style:italic;padding:8px 0;">No schedule calculated yet. Configure schedule start times and zone durations to enable wake scheduling.</div>';
    }

    // Add wake schedule enable/disable toggle
    var isDisabled = window['_wakeScheduleDisabled_' + probeId] || false;
    body += '<div style="margin-top:12px;padding:8px 10px;background:var(--bg-tile);border-radius:6px;display:flex;align-items:center;justify-content:space-between;">';
    body += '<div style="font-size:12px;color:var(--text-secondary);"><strong>Wake Schedule</strong><br><span style="font-size:11px;color:var(--text-muted);">When disabled, probe sleep won\\'t be managed around irrigation runs</span></div>';
    body += '<button id="wakeSchedToggleBtn" onclick="hoToggleWakeSchedule(\\'' + esc(probeId) + '\\')" style="padding:5px 14px;border-radius:4px;border:none;cursor:pointer;font-size:12px;font-weight:600;' +
        (isDisabled ? 'background:var(--color-success, #2ecc71);color:#fff;">Enable' : 'background:rgba(150,150,150,0.2);color:var(--text-muted, #888);">Disable') + '</button>';
    body += '</div>';

    showModal('Wake Schedule', body, '440px');
}

async function hoToggleWakeSchedule(probeId) {
    var isDisabled = window['_wakeScheduleDisabled_' + probeId] || false;
    var newState = !isDisabled;
    try {
        await mapi('/probes/' + probeId + '/wake-schedule-disabled', 'PUT', { disabled: newState });
        window['_wakeScheduleDisabled_' + probeId] = newState;
        showToast('Wake schedule ' + (newState ? 'disabled' : 'enabled'));
        // Update probe card button color
        var cardBtn = document.getElementById('hoWakeSchedBtn_' + probeId);
        if (cardBtn) {
            if (newState) {
                cardBtn.style.color = 'var(--text-muted, #666)';
                cardBtn.style.borderColor = 'var(--border-light)';
                cardBtn.style.background = 'var(--bg-tile)';
            } else {
                cardBtn.style.color = 'var(--color-success, #2ecc71)';
                cardBtn.style.borderColor = 'var(--color-success, #2ecc71)';
                cardBtn.style.background = 'transparent';
            }
        }
        hoShowWakeSchedule(probeId); // Refresh the modal
    } catch(e) {
        showToast('Failed: ' + e.message, 'error');
    }
}

async function toggleApplyFactors(enable) {
    try {
        const result = await mapi('/settings', 'PUT', { apply_factors_to_schedule: enable });
        const isError = result.success === false;
        showToast(result.message || (enable ? 'Factors applied' : 'Factors disabled'), isError ? 'error' : undefined);
        loadControls();
    } catch (e) { showToast(e.message, 'error'); }
}

async function syncProbeSchedules() {
    try {
        const result = await mapi('/probes/sync-schedules', 'POST');
        showToast(result.synced > 0 ? 'Synced ' + result.synced + ' schedule time(s)' : (result.reason || 'Nothing to sync'));
        _moistureDataCache = null;
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Notifications Panel (with settings inside) ---
var _notifPanelEvents = [];
var _notifUnreadCount = 0;
var _notifPanelView = 'feed';  // 'feed' or 'settings'
var _notifPrefs = {};
var _haNotifSettings = {};
var _notifSubView = 'main'; // 'main', 'issues', 'system', 'ha'

async function openNotificationsPanel() {
    _notifPanelView = 'feed';
    var body = document.getElementById('notifPanelBody');
    body.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:40px;">Loading...</div>';
    document.getElementById('notifPanelModal').style.display = 'flex';
    try {
        var data = await api('/notifications?limit=50');
        _notifPanelEvents = data.events || [];
        _notifUnreadCount = data.unread_count || 0;
        updateNotifBadge();
        renderNotifPanelContent();
    } catch(e) {
        body.innerHTML = '<div style="color:#e74c3c;text-align:center;padding:40px;">Failed to load notifications.</div>';
    }
}

function closeNotificationsPanel() {
    document.getElementById('notifPanelModal').style.display = 'none';
}

function renderNotifPanelContent() {
    if (_notifPanelView === 'settings') {
        renderNotifSettingsView();
        return;
    }
    renderNotificationFeed();
}

function renderNotificationFeed() {
    var body = document.getElementById('notifPanelBody');
    var markAllBtn = document.getElementById('notifMarkAllBtn');
    var clearAllBtn = document.getElementById('notifClearAllBtn');
    if (_notifUnreadCount > 0) {
        markAllBtn.style.display = '';
    } else {
        markAllBtn.style.display = 'none';
    }
    clearAllBtn.style.display = _notifPanelEvents.length > 0 ? '' : 'none';
    if (_notifPanelEvents.length === 0) {
        body.innerHTML = '<div style="text-align:center;padding:30px;color:var(--text-muted);font-size:13px;">No notifications yet. When your management company makes changes, they will appear here.</div>';
        return;
    }
    var html = '';
    _notifPanelEvents.forEach(function(ev) {
        var dt = new Date(ev.created_at);
        var now = new Date();
        var diffMs = now - dt;
        var diffH = Math.floor(diffMs / 3600000);
        var timeAgo = diffH < 1 ? 'Just now' : diffH < 24 ? diffH + 'h ago' : Math.floor(diffH / 24) + 'd ago';
        var readOpacity = ev.read ? 'opacity:0.65;' : '';
        var newBadge = ev.read ? '' : '<span style="display:inline-block;background:var(--color-primary);color:white;font-size:9px;font-weight:700;padding:1px 5px;border-radius:4px;margin-left:6px;vertical-align:middle;">NEW</span>';
        html += '<div class="notif-item' + (ev.read ? '' : ' unread') + '" onclick="markNotificationRead(\\'' + ev.id + '\\')" style="cursor:pointer;' + readOpacity + '">';
        html += '<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px;">';
        html += '<span style="font-size:13px;font-weight:' + (ev.read ? '400' : '600') + ';color:var(--text-primary);min-width:0;word-break:break-word;">' + esc(ev.title) + newBadge + '</span>';
        html += '<span style="font-size:11px;color:var(--text-muted);white-space:nowrap;flex-shrink:0;">' + esc(timeAgo) + '</span>';
        html += '</div>';
        if (ev.message) {
            html += '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;word-break:break-word;line-height:1.4;">' + esc(ev.message) + '</div>';
        }
        html += '</div>';
    });
    body.innerHTML = html;
}

async function markNotificationRead(eventId) {
    try {
        await api('/notifications/' + eventId + '/read', { method: 'PUT' });
        _notifPanelEvents.forEach(function(ev) { if (ev.id === eventId) ev.read = true; });
        _notifUnreadCount = _notifPanelEvents.filter(function(e) { return !e.read; }).length;
        updateNotifBadge();
        renderNotificationFeed();
    } catch(e) {}
}

async function markAllNotificationsRead() {
    try {
        await api('/notifications/read-all', { method: 'PUT' });
        _notifPanelEvents.forEach(function(ev) { ev.read = true; });
        _notifUnreadCount = 0;
        updateNotifBadge();
        renderNotificationFeed();
    } catch(e) { showToast('Failed to mark all read', true); }
}

async function clearAllNotifications() {
    if (!confirm('Clear all notifications? This cannot be undone.')) return;
    try {
        await api('/notifications/clear', { method: 'DELETE' });
        _notifPanelEvents = [];
        _notifUnreadCount = 0;
        updateNotifBadge();
        renderNotificationFeed();
        showToast('Notifications cleared');
    } catch(e) { showToast('Failed to clear notifications', 'error'); }
}

function updateNotifBadge() {
    var badge = document.getElementById('notifBellBadge');
    if (_notifUnreadCount > 0) {
        badge.textContent = _notifUnreadCount > 99 ? '99+' : _notifUnreadCount;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

async function pollNotificationBadge() {
    try {
        var data = await api('/notifications?limit=1');
        _notifUnreadCount = data.unread_count || 0;
        updateNotifBadge();
    } catch(e) {}
}

// --- Notification Settings (inside bell panel) ---
function showNotifSettingsView() {
    _notifPanelView = 'settings';
    _notifSubView = 'main';
    document.getElementById('notifMarkAllBtn').style.display = 'none';
    document.getElementById('notifClearAllBtn').style.display = 'none';
    loadNotificationSettings();
}

function backToNotifFeed() {
    _notifPanelView = 'feed';
    renderNotifPanelContent();
}

async function loadNotificationSettings() {
    var body = document.getElementById('notifPanelBody');
    body.innerHTML = '<div style="color:var(--text-muted);text-align:center;padding:40px;">Loading...</div>';
    try {
        var results = await Promise.all([
            api('/notification-preferences'),
            api('/ha-notification-settings'),
        ]);
        _notifPrefs = results[0] || {};
        _haNotifSettings = results[1] || {};
        renderNotifSettingsView();
    } catch(e) {
        body.innerHTML = '<div style="color:#e74c3c;text-align:center;padding:40px;">Failed to load notification settings.</div>';
    }
}

function renderNotifSettingsView() {
    if (_notifSubView === 'ha') { renderNotifHA(); return; }
    if (_notifSubView === 'issues') { renderNotifIssues(); return; }
    if (_notifSubView === 'system') { renderNotifSystem(); return; }
    renderNotifMain();
}

function renderNotifMain() {
    var body = document.getElementById('notifPanelBody');
    var html = '<div style="padding:16px 20px 20px 20px;">';
    html += '<div style="margin-bottom:16px;"><a href="#" onclick="event.preventDefault();backToNotifFeed()" style="font-size:13px;color:var(--color-primary);text-decoration:none;">&laquo; Back to Notifications</a></div>';

    var masterEnabled = _notifPrefs.enabled !== false;

    // Master toggle
    html += '<div style="display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid var(--border-light);margin-bottom:16px;">';
    html += '<div><div style="font-size:14px;font-weight:600;color:var(--text-primary);">Management Notifications</div>';
    html += '<div style="font-size:11px;color:var(--text-muted);">Receive in-app notifications when your management company makes changes</div></div>';
    html += '<label class="toggle-switch"><input type="checkbox" onchange="toggleNotifPref(\\'enabled\\', this.checked)"' + (masterEnabled ? ' checked' : '') + '><span class="toggle-slider"></span></label>';
    html += '</div>';

    if (!masterEnabled) {
        html += '<div style="text-align:center;padding:24px;color:var(--text-muted);font-size:13px;">Notifications are disabled. Enable the toggle above to configure notification preferences.</div>';
    } else {
        // Sub-category cards
        html += '<h4 style="font-size:14px;font-weight:600;margin:0 0 10px 0;color:var(--text-primary);">Categories</h4>';

        // Issues Notifications card
        var issueCount = [_notifPrefs.service_appointments].filter(Boolean).length;
        html += '<div onclick="_notifSubView=\\'issues\\';renderNotifSettingsView();" style="display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:var(--bg-tile);border-radius:10px;margin-bottom:8px;cursor:pointer;border:1px solid var(--border-light);transition:background 0.15s;" onmouseover="this.style.borderColor=\\'var(--color-primary)\\'" onmouseout="this.style.borderColor=\\'var(--border-light)\\'">';
        html += '<div style="display:flex;align-items:center;gap:10px;">';
        html += '<span style="font-size:18px;">&#128295;</span>';
        html += '<div><div style="font-size:13px;font-weight:600;color:var(--text-primary);">Issue Notifications</div>';
        html += '<div style="font-size:11px;color:var(--text-muted);">Service appointments &amp; issue updates</div></div>';
        html += '</div>';
        html += '<div style="display:flex;align-items:center;gap:6px;"><span style="font-size:11px;color:var(--text-muted);">' + issueCount + '/1 on</span><span style="color:var(--text-muted);">&#9654;</span></div>';
        html += '</div>';

        // System Change Notifications card
        var sysKeys = ['system_changes','weather_changes','moisture_changes','equipment_changes','duration_changes','report_changes'];
        var sysCount = sysKeys.filter(function(k) { return !!_notifPrefs[k]; }).length;
        html += '<div onclick="_notifSubView=\\'system\\';renderNotifSettingsView();" style="display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:var(--bg-tile);border-radius:10px;margin-bottom:8px;cursor:pointer;border:1px solid var(--border-light);transition:background 0.15s;" onmouseover="this.style.borderColor=\\'var(--color-primary)\\'" onmouseout="this.style.borderColor=\\'var(--border-light)\\'">';
        html += '<div style="display:flex;align-items:center;gap:10px;">';
        html += '<span style="font-size:18px;">&#9881;</span>';
        html += '<div><div style="font-size:13px;font-weight:600;color:var(--text-primary);">System Change Notifications</div>';
        html += '<div style="font-size:11px;color:var(--text-muted);">Weather, moisture, equipment &amp; more</div></div>';
        html += '</div>';
        html += '<div style="display:flex;align-items:center;gap:6px;"><span style="font-size:11px;color:var(--text-muted);">' + sysCount + '/' + sysKeys.length + ' on</span><span style="color:var(--text-muted);">&#9654;</span></div>';
        html += '</div>';

        // HA Push Notifications card
        var haStatus = _haNotifSettings.enabled ? 'On' : 'Off';
        html += '<div onclick="_notifSubView=\\'ha\\';renderNotifSettingsView();" style="display:flex;align-items:center;justify-content:space-between;padding:14px 16px;background:var(--bg-tile);border-radius:10px;margin-bottom:8px;cursor:pointer;border:1px solid var(--border-light);transition:background 0.15s;" onmouseover="this.style.borderColor=\\'var(--color-primary)\\'" onmouseout="this.style.borderColor=\\'var(--border-light)\\'">';
        html += '<div style="display:flex;align-items:center;gap:10px;">';
        html += '<span style="font-size:18px;">&#127968;</span>';
        html += '<div><div style="font-size:13px;font-weight:600;color:var(--text-primary);">HA Push Notifications</div>';
        html += '<div style="font-size:11px;color:var(--text-muted);">Send notifications through Home Assistant</div></div>';
        html += '</div>';
        html += '<div style="display:flex;align-items:center;gap:6px;"><span style="font-size:11px;color:var(--text-muted);">' + haStatus + '</span><span style="color:var(--text-muted);">&#9654;</span></div>';
        html += '</div>';
    }

    html += '</div>';
    body.innerHTML = html;
}

function _notifBackBtn() {
    return '<div onclick="_notifSubView=\\'main\\';renderNotifSettingsView();" style="display:inline-flex;align-items:center;gap:4px;cursor:pointer;color:var(--color-primary);font-size:13px;font-weight:500;margin-bottom:12px;"><span style="font-size:16px;">&#9664;</span> Back</div>';
}

function _notifToggleRow(key, label, desc) {
    var checked = !!_notifPrefs[key];
    var html = '<div style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--border-light);">';
    html += '<div style="flex:1;min-width:0;"><div style="font-size:13px;font-weight:500;color:var(--text-primary);">' + esc(label) + '</div>';
    html += '<div style="font-size:11px;color:var(--text-muted);">' + esc(desc) + '</div></div>';
    html += '<label class="toggle-switch"><input type="checkbox" onchange="toggleNotifPref(\\'' + key + '\\', this.checked)"' + (checked ? ' checked' : '') + '><span class="toggle-slider"></span></label>';
    html += '</div>';
    return html;
}

function renderNotifIssues() {
    var body = document.getElementById('notifPanelBody');
    var html = '<div style="padding:16px 20px 20px 20px;">';
    html += _notifBackBtn();
    html += '<h4 style="font-size:15px;font-weight:600;margin:0 0 4px 0;color:var(--text-primary);">&#128295; Issue Notifications</h4>';
    html += '<p style="font-size:12px;color:var(--text-muted);margin:0 0 12px 0;">Notifications related to service appointments and issue tracking.</p>';
    html += _notifToggleRow('service_appointments', 'Service Appointments', 'When a service visit is scheduled or rescheduled');
    html += '</div>';
    body.innerHTML = html;
}

function renderNotifSystem() {
    var body = document.getElementById('notifPanelBody');
    var html = '<div style="padding:16px 20px 20px 20px;">';
    html += _notifBackBtn();
    html += '<h4 style="font-size:15px;font-weight:600;margin:0 0 4px 0;color:var(--text-primary);">&#9881; System Change Notifications</h4>';
    html += '<p style="font-size:12px;color:var(--text-muted);margin:0 0 12px 0;">Notifications when management modifies your system settings.</p>';
    html += _notifToggleRow('system_changes', 'System Pause / Resume', 'When management pauses or resumes your irrigation system');
    html += _notifToggleRow('weather_changes', 'Weather Rules', 'When weather adjustment rules are changed');
    html += _notifToggleRow('moisture_changes', 'Moisture Settings', 'When moisture probe settings are updated');
    html += _notifToggleRow('equipment_changes', 'Equipment Settings', 'When pump or water source settings change');
    html += _notifToggleRow('duration_changes', 'Zone Durations', 'When adjusted zone durations are applied or restored');
    html += _notifToggleRow('report_changes', 'Report Settings', 'When PDF report branding is changed');
    html += '</div>';
    body.innerHTML = html;
}

function renderNotifHA() {
    var body = document.getElementById('notifPanelBody');
    var html = '<div style="padding:16px 20px 20px 20px;">';
    html += _notifBackBtn();
    html += '<h4 style="font-size:15px;font-weight:600;margin:0 0 4px 0;color:var(--text-primary);">&#127968; HA Push Notifications</h4>';
    html += '<p style="font-size:12px;color:var(--text-muted);margin:0 0 16px 0;">Send push notifications (mobile app, SMS, etc.) through your Home Assistant notification service when management makes changes.</p>';

    // Enable toggle
    html += '<label style="display:flex;align-items:center;gap:10px;cursor:pointer;margin-bottom:14px;">';
    html += '<input type="checkbox" id="hoHaNotifEnabled"' + (_haNotifSettings.enabled ? ' checked' : '') + '>';
    html += '<span style="font-weight:600;color:var(--text-primary);">Enable HA Notifications</span></label>';

    // Notify service selector
    html += '<div style="margin-bottom:12px;">';
    html += '<label style="font-size:13px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Notify Service</label>';
    html += '<div style="display:flex;gap:6px;align-items:center;min-width:0;">';
    html += '<select id="hoHaNotifyService" style="flex:1;min-width:0;padding:8px 10px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);box-sizing:border-box;max-width:100%;">';
    html += '<option value="">-- Select a notify service --</option>';
    html += '</select>';
    html += '<button class="btn btn-secondary btn-sm" onclick="loadHomeownerNotifyServices()" title="Refresh" style="padding:6px 10px;font-size:16px;line-height:1;flex-shrink:0;">&#8635;</button>';
    html += '</div>';
    html += '<div id="hoHaServiceHint" style="font-size:11px;color:var(--text-placeholder);margin-top:3px;">Auto-detected from Home Assistant</div>';
    html += '</div>';

    // Category toggles
    html += '<p style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">Category filters:</p>';
    html += '<div style="display:flex;flex-direction:column;gap:10px;margin-bottom:14px;">';
    var cats = [
        {key:'notify_service_appointments', label:'Service Appointments', color:'var(--text-primary)'},
        {key:'notify_system_changes', label:'System Pause / Resume', color:'var(--text-primary)'},
        {key:'notify_weather_changes', label:'Weather Rules', color:'var(--text-primary)'},
        {key:'notify_moisture_changes', label:'Moisture Settings', color:'var(--text-primary)'},
        {key:'notify_equipment_changes', label:'Equipment Settings', color:'var(--text-primary)'},
        {key:'notify_duration_changes', label:'Zone Durations', color:'var(--text-primary)'},
        {key:'notify_report_changes', label:'Report Settings', color:'var(--text-primary)'},
    ];
    cats.forEach(function(c) {
        var chk = _haNotifSettings[c.key] ? ' checked' : '';
        html += '<label style="display:flex;align-items:center;gap:10px;cursor:pointer;"><input type="checkbox" id="hoHa_' + c.key + '"' + chk + '><span style="font-weight:500;color:' + c.color + ';">' + esc(c.label) + '</span></label>';
    });
    html += '</div>';

    // Action buttons
    html += '<div style="display:flex;gap:8px;justify-content:space-between;align-items:center;">';
    html += '<button class="btn btn-secondary btn-sm" onclick="testHomeownerHANotification()">&#128172; Test</button>';
    html += '<button class="btn btn-primary btn-sm" onclick="saveHomeownerHANotifSettings()">Save</button>';
    html += '</div>';
    html += '<div id="hoHaNotifStatus" style="font-size:11px;color:var(--text-muted);margin-top:8px;"></div>';

    html += '</div>';
    body.innerHTML = html;

    // Load the services dropdown after rendering
    loadHomeownerNotifyServices();
}

async function loadHomeownerNotifyServices() {
    var sel = document.getElementById('hoHaNotifyService');
    if (!sel) return;
    var saved = _haNotifSettings.ha_notify_service || '';
    var hint = document.getElementById('hoHaServiceHint');
    hint.textContent = 'Loading services from Home Assistant...';
    try {
        var data = await api('/ha-notification-settings/services');
        var services = data.services || [];
        sel.innerHTML = '<option value="">-- Select a notify service --</option>';
        services.forEach(function(s) {
            var opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = s.name + ' (notify.' + s.id + ')';
            sel.appendChild(opt);
        });
        if (saved) sel.value = saved;
        if (saved && sel.value !== saved) {
            var opt = document.createElement('option');
            opt.value = saved;
            opt.textContent = saved + ' (saved)';
            sel.appendChild(opt);
            sel.value = saved;
        }
        hint.textContent = services.length ? services.length + ' service(s) found' : 'No notify services found in HA';
    } catch (e) {
        hint.textContent = 'Could not load services';
    }
}

async function saveHomeownerHANotifSettings() {
    var payload = {
        enabled: document.getElementById('hoHaNotifEnabled').checked,
        ha_notify_service: document.getElementById('hoHaNotifyService').value.trim(),
        notify_service_appointments: document.getElementById('hoHa_notify_service_appointments').checked,
        notify_system_changes: document.getElementById('hoHa_notify_system_changes').checked,
        notify_weather_changes: document.getElementById('hoHa_notify_weather_changes').checked,
        notify_moisture_changes: document.getElementById('hoHa_notify_moisture_changes').checked,
        notify_equipment_changes: document.getElementById('hoHa_notify_equipment_changes').checked,
        notify_duration_changes: document.getElementById('hoHa_notify_duration_changes').checked,
        notify_report_changes: document.getElementById('hoHa_notify_report_changes').checked,
    };
    if (payload.enabled && !payload.ha_notify_service) {
        showToast('Please select a notify service', true);
        return;
    }
    try {
        var result = await api('/ha-notification-settings', { method: 'PUT', body: JSON.stringify(payload) });
        _haNotifSettings = result || {};
        showToast('HA notification settings saved');
        var st = document.getElementById('hoHaNotifStatus');
        if (st) st.textContent = 'Settings saved';
    } catch (e) {
        showToast('Failed to save HA notification settings', true);
    }
}

async function testHomeownerHANotification() {
    var svc = document.getElementById('hoHaNotifyService').value.trim();
    if (!svc) {
        showToast('Select a notify service first', true);
        return;
    }
    await saveHomeownerHANotifSettings();
    try {
        var result = await api('/ha-notification-settings/test', { method: 'POST' });
        showToast(result.message || 'Test notification sent');
        var st = document.getElementById('hoHaNotifStatus');
        if (st) st.textContent = 'Test sent successfully';
    } catch (e) {
        var msg = (e.message || '').replace('Error: ', '');
        showToast('Test failed: ' + msg, true);
        var st = document.getElementById('hoHaNotifStatus');
        if (st) st.textContent = 'Test failed \\u2014 check service name';
    }
}

async function toggleNotifPref(key, enabled) {
    try {
        var body = {};
        body[key] = enabled;
        await api('/notification-preferences', {
            method: 'PUT',
            body: JSON.stringify(body),
        });
        _notifPrefs[key] = enabled;
        showToast('Preference updated');
        // Re-render if master toggle changed (shows/hides categories)
        if (key === 'enabled') renderNotificationSettings();
    } catch(e) {
        showToast('Failed to update preference', true);
        renderNotificationSettings();
    }
}

// --- Dark Mode ---
function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('flux_dark_mode_homeowner', isDark);
    document.querySelector('.dark-toggle').textContent = isDark ? '☀️' : '🌙';
    _applyDarkTiles();
}
(function initDarkToggleIcon() {
    const btn = document.querySelector('.dark-toggle');
    if (btn && document.body.classList.contains('dark-mode')) btn.textContent = '☀️';
})();

// --- Live Clock ---
const STATE_TIMEZONES = {
    'AL':'America/Chicago','AK':'America/Anchorage','AZ':'America/Phoenix',
    'AR':'America/Chicago','CA':'America/Los_Angeles','CO':'America/Denver',
    'CT':'America/New_York','DE':'America/New_York','FL':'America/New_York',
    'GA':'America/New_York','HI':'Pacific/Honolulu','ID':'America/Boise',
    'IL':'America/Chicago','IN':'America/Indiana/Indianapolis','IA':'America/Chicago',
    'KS':'America/Chicago','KY':'America/New_York','LA':'America/Chicago',
    'ME':'America/New_York','MD':'America/New_York','MA':'America/New_York',
    'MI':'America/Detroit','MN':'America/Chicago','MS':'America/Chicago',
    'MO':'America/Chicago','MT':'America/Denver','NE':'America/Chicago',
    'NV':'America/Los_Angeles','NH':'America/New_York','NJ':'America/New_York',
    'NM':'America/Denver','NY':'America/New_York','NC':'America/New_York',
    'ND':'America/Chicago','OH':'America/New_York','OK':'America/Chicago',
    'OR':'America/Los_Angeles','PA':'America/New_York','RI':'America/New_York',
    'SC':'America/New_York','SD':'America/Chicago','TN':'America/Chicago',
    'TX':'America/Chicago','UT':'America/Denver','VT':'America/New_York',
    'VA':'America/New_York','WA':'America/Los_Angeles','WV':'America/New_York',
    'WI':'America/Chicago','WY':'America/Denver','DC':'America/New_York',
};
let _homeClockTimer = null;
let _homeTimezone = null;
function startHomeClock(state) {
    if (_homeClockTimer) clearInterval(_homeClockTimer);
    const el = document.getElementById('dashTimezone');
    _homeTimezone = STATE_TIMEZONES[(state || '').toUpperCase()] || null;
    function tick() {
        try {
            const now = new Date();
            const opts = {hour: 'numeric', minute: '2-digit', hour12: true};
            const abbrOpts = {timeZoneName: 'short'};
            if (_homeTimezone) { opts.timeZone = _homeTimezone; abbrOpts.timeZone = _homeTimezone; }
            const time = now.toLocaleTimeString('en-US', opts);
            const abbr = now.toLocaleTimeString('en-US', Object.assign({}, opts, abbrOpts)).split(' ').pop();
            el.textContent = time + ' ' + abbr;
        } catch(e) {}
    }
    tick();
    _homeClockTimer = setInterval(tick, 30000);
}

// --- Init ---
document.addEventListener('DOMContentLoaded', async () => {
    // Initialize collapsible card states (controls + expansion default collapsed)
    initCardState('status', false);
    initCardState('gallons', false);
    initCardState('pump', false);
    initCardState('rain', false);
    initCardState('weather', false);
    initCardState('moisture', false);
    initCardState('zones', false);
    initCardState('schedule', false);
    initCardState('sensors', false);
    initCardState('controls', true);
    initCardState('expansion', true);
    initCardState('history', false);

    // Start clock with browser time initially (will update with correct TZ after status loads)
    startHomeClock('');

    // Load system mode (for boundary area column visibility)
    try {
        var smBase = window.location.pathname.replace(/\\/+$/, '');
        var smRes = await fetch(smBase + '/api/system-mode');
        var smData = await smRes.json();
        window._hoSystemMode = smData.mode || 'standalone';
    } catch(e) {
        window._hoSystemMode = 'standalone';
    }

    // Load zone aliases
    try {
        window._currentZoneAliases = await api('/zone_aliases');
    } catch (e) {
        window._currentZoneAliases = {};
    }
    window._zoneModes = {};

    // Load dashboard
    loadDashboard();

    // Init map from status (address comes from config) and set timezone
    try {
        const status = await api('/status');
        if (status.state) {
            startHomeClock(status.state);
        }
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
<p style="margin-bottom:10px;">Each zone tile shows the current state (running or off). Zones are displayed as "Zone 1", "Zone 2", etc. by default — use aliases to give them friendly names. You can:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Start</strong> — Turn a zone on immediately with no time limit</li><li style="margin-bottom:4px;"><strong>Timed Start</strong> — Enter a duration in minutes and click <strong>Timed</strong> to run the zone for a set period, then auto-shutoff</li><li style="margin-bottom:4px;"><strong>Stop</strong> — Turn off a running zone immediately</li><li style="margin-bottom:4px;"><strong>Emergency Stop All</strong> — Instantly stops every active zone on the system</li><li style="margin-bottom:4px;"><strong>Auto Advance</strong> — Toggle at the top of the zone card. To run all enabled zones sequentially: start the first zone with a timed run, then click Auto Advance to enable it. Each zone will automatically advance to the next enabled zone when its timer expires. Turn Auto Advance off at any time to stop the sequence after the current zone finishes.</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Green-highlighted tiles indicate zones that are currently running. If your controller has expansion boards, only the physically connected zones are shown — extra pre-created entities are automatically hidden.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">🔩 Zone Head Details</h4>
<p style="margin-bottom:10px;">Click the <strong>ℹ</strong> icon on any zone tile to open the Zone Details modal. This lets you document every sprinkler head in the zone:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Number of Heads</strong> — Set how many sprinkler heads are in the zone, then click Update Table to build the inventory</li><li style="margin-bottom:4px;"><strong>Head Type</strong> — Pop-up spray, rotary nozzle, gear rotor, impact rotor, micro-spray, bubbler, drip emitter, drip line, fixed spray, or strip nozzle</li><li style="margin-bottom:4px;"><strong>Brand & Model</strong> — Select a manufacturer, then pick a model from the filtered picklist. Known models auto-fill the GPM field. Choose "Custom..." to type any model not in the list. The model database is stored in <code>sprinkler_models.json</code> and can be easily extended.</li><li style="margin-bottom:4px;"><strong>Mount Type</strong> — Pop-up, stationary, riser, shrub, or on-grade</li><li style="margin-bottom:4px;"><strong>GPM</strong> — Flow rate in gallons per minute. Auto-populated when you select a known model, or type your own value. The total zone flow is calculated automatically and displayed on the zone card.</li><li style="margin-bottom:4px;"><strong>Arc & Radius</strong> — Spray arc in degrees and throw radius in feet</li><li style="margin-bottom:4px;"><strong>Pop-Up Height</strong> — Riser height (2", 3", 4", 6", or 12")</li><li style="margin-bottom:4px;"><strong>PSI & Notes</strong> — Operating pressure and any location/condition notes</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Documenting your heads helps irrigation professionals service your system and ensures accurate watering calculations. Give each head a name/location (e.g. "Front left corner") so they can be easily found on the property.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Rain Sensor</h4>
<p style="margin-bottom:10px;">If your irrigation controller has a rain sensor connected, a dedicated Rain Sensor card appears showing:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Status Banner</strong> — Shows current state: Dry (green), Rain Detected (red), Rain Delay (yellow), or Disabled (gray)</li><li style="margin-bottom:4px;"><strong>Rain Sensor Enable</strong> — Toggle rain sensor monitoring on or off</li><li style="margin-bottom:4px;"><strong>Sensor Type</strong> — Set to NC (Normally Closed) or NO (Normally Open) to match your hardware wiring</li><li style="margin-bottom:4px;"><strong>Rain Delay Enable</strong> — Toggle the rain delay feature on or off</li><li style="margin-bottom:4px;"><strong>Delay Duration</strong> — How many hours to delay watering after rain is detected (1-72 hours)</li><li style="margin-bottom:4px;"><strong>Rain Delay Active</strong> — Shows whether rain delay is currently active</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">&#128161; The rain sensor card only appears when rain sensor entities are detected on your irrigation controller.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Sensors</h4>
<p style="margin-bottom:10px;">The sensors card shows real-time readings from your irrigation controller — soil moisture, temperature, Wi-Fi signal strength, and any other sensors exposed by your device. Wi-Fi signal includes a quality badge (Great/Good/Poor/Bad) based on signal strength in dBm.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Schedule Management</h4>
<p style="margin-bottom:10px;">Your irrigation schedule is configured through your Flux Open Home controller and managed via its ESPHome entities:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Schedule Enable/Disable</strong> — Master toggle to turn the entire schedule on or off</li><li style="margin-bottom:4px;"><strong>Days of Week</strong> — Click day buttons to toggle which days the schedule runs</li><li style="margin-bottom:4px;"><strong>Start Times</strong> — Set when each schedule program begins (HH:MM format)</li><li style="margin-bottom:4px;"><strong>Zone Settings</strong> — Enable/disable individual zones and set run durations for each</li><li style="margin-bottom:4px;"><strong>Zone Modes</strong> — Some zones may have special modes (Pump Start Relay, Master Valve) that are firmware-controlled</li><li style="margin-bottom:4px;"><strong>Apply Factors to Schedule</strong> — When enabled, automatically adjusts ESPHome run durations using the combined watering factor (weather &times; moisture). The input field shows the base duration (what you set), and a badge next to it shows the adjusted duration and factor (e.g. &quot;24 min (0.80x)&quot;). The base is what you control; the adjusted value is what the controller actually runs. Durations update automatically as conditions change and restore to originals when disabled. Even when this toggle is OFF, a preview badge shows what the projected duration would be given the current combined factor, so you can always see how weather and moisture conditions would affect your schedule.</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Schedule changes take effect immediately on your controller — no restart needed.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Weather-Based Control</h4>
<p style="margin-bottom:10px;">When weather is enabled (configured on the Configuration page), the dashboard shows current conditions and a <strong>watering multiplier</strong>:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>1.0x</strong> (green) — Normal watering, no adjustments active</li><li style="margin-bottom:4px;"><strong>Below 1.0x</strong> (yellow) — Reduced watering due to cool temps, humidity, etc.</li><li style="margin-bottom:4px;"><strong>Above 1.0x</strong> (red) — Increased watering due to hot temperatures</li><li style="margin-bottom:4px;"><strong>Skip/Pause</strong> — Watering paused entirely due to rain, freezing, or high wind</li></ul>
<p style="margin-bottom:10px;">The <strong>Weather Rules</strong> section is collapsed by default — click the header to expand and configure rules. Each rule can be individually enabled/disabled. Click <strong>Test Rules Now</strong> to evaluate which rules would trigger under current conditions. The action buttons (Test, Export, Clear) are always visible even when the rules section is collapsed.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Gophr Moisture Probes</h4>
<p style="margin-bottom:10px;">When Gophr moisture probes are connected to Home Assistant, the moisture card shows live soil moisture readings at three depths (shallow, mid, deep). The algorithm uses a <strong>gradient-based approach</strong> that treats each depth as a distinct signal:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Mid sensor (root zone)</strong> — The PRIMARY decision driver. This is where grass roots live and is the most important reading for determining watering needs.</li><li style="margin-bottom:4px;"><strong>Shallow sensor (surface)</strong> — Used for rain detection. If the surface is significantly wetter than the root zone and rain is forecasted, the system infers recent rainfall and reduces or skips watering.</li><li style="margin-bottom:4px;"><strong>Deep sensor (reserve)</strong> — Guards against over-irrigation. If deep soil is saturated while the root zone looks normal, it suggests water is pooling below and watering is reduced.</li></ul>

<p style="margin-bottom:6px;font-weight:600;font-size:13px;">Moisture Multiplier Formula</p>
<p style="margin-bottom:6px;font-size:13px;">The base multiplier is calculated from the <strong>mid sensor (root zone &mdash; where grass roots live)</strong> reading against four configurable thresholds (defaults shown):</p>
<table style="width:100%;font-size:12px;border-collapse:collapse;margin-bottom:8px;">
<tr style="border-bottom:1px solid var(--border-light);"><th style="text-align:left;padding:4px 6px;">Mid Sensor (Root Zone) Reading</th><th style="text-align:left;padding:4px 6px;">Multiplier</th><th style="text-align:left;padding:4px 6px;">Behavior</th></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Mid &ge; Skip (80%)</td><td style="padding:4px 6px;font-weight:600;color:var(--color-danger);">0.0x &mdash; Skip</td><td style="padding:4px 6px;">Soil saturated, no watering</td></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Mid Wet (65%) &ndash; Skip (80%)</td><td style="padding:4px 6px;">0.50x &rarr; 0.0x</td><td style="padding:4px 6px;">Linear reduction as moisture increases</td></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Mid Optimal (45%) &ndash; Wet (65%)</td><td style="padding:4px 6px;">1.0x &rarr; 0.50x</td><td style="padding:4px 6px;">Gradual reduction approaching wet</td></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Mid Dry (30%) &ndash; Optimal (45%)</td><td style="padding:4px 6px;">1.25x &rarr; 1.0x</td><td style="padding:4px 6px;">Slight increase as soil dries</td></tr>
<tr><td style="padding:4px 6px;">Mid &lt; Dry (30%)</td><td style="padding:4px 6px;font-weight:600;color:var(--color-danger);">1.50x</td><td style="padding:4px 6px;">Critically dry, maximum increase</td></tr>
</table>
<p style="margin-bottom:6px;font-weight:600;font-size:13px;">Shallow Sensor (Rain Detection)</p>
<p style="margin-bottom:6px;font-size:13px;">The shallow sensor detects recent rainfall by comparing surface moisture to root zone moisture. It does not directly set the multiplier but applies reductions after the base multiplier:</p>
<table style="width:100%;font-size:12px;border-collapse:collapse;margin-bottom:8px;">
<tr style="border-bottom:1px solid var(--border-light);"><th style="text-align:left;padding:4px 6px;">Condition</th><th style="text-align:left;padding:4px 6px;">Effect</th><th style="text-align:left;padding:4px 6px;">Behavior</th></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Shallow &minus; Mid &ge; 15% + Rain &ge; 50%</td><td style="padding:4px 6px;font-weight:600;">40% reduction</td><td style="padding:4px 6px;">High-confidence rain detected (wetting front + forecast)</td></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Shallow &minus; Mid &gt; 5% + Rain &ge; 40%</td><td style="padding:4px 6px;">20% reduction</td><td style="padding:4px 6px;">Moderate-confidence rain detected</td></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Weather is rainy/pouring/lightning</td><td style="padding:4px 6px;">40% reduction</td><td style="padding:4px 6px;">Active precipitation detected from weather data</td></tr>
<tr><td style="padding:4px 6px;">Mid &ge; Wet&minus;5% + high-confidence rain</td><td style="padding:4px 6px;font-weight:600;color:var(--color-danger);">0.0x &mdash; Skip</td><td style="padding:4px 6px;">Root zone near saturation with confirmed rain</td></tr>
</table>

<p style="margin-bottom:6px;font-weight:600;font-size:13px;">Deep Sensor (Over-Irrigation Guard)</p>
<p style="margin-bottom:6px;font-size:13px;">The deep sensor guards against over-irrigation by detecting water pooling below the root zone. It caps or further reduces the multiplier:</p>
<table style="width:100%;font-size:12px;border-collapse:collapse;margin-bottom:8px;">
<tr style="border-bottom:1px solid var(--border-light);"><th style="text-align:left;padding:4px 6px;">Deep Reading</th><th style="text-align:left;padding:4px 6px;">Effect</th><th style="text-align:left;padding:4px 6px;">Behavior</th></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Deep &ge; Skip threshold (80%)</td><td style="padding:4px 6px;font-weight:600;">Capped at 0.50x</td><td style="padding:4px 6px;">Deep soil saturated, prevent further over-watering</td></tr>
<tr><td style="padding:4px 6px;">Deep &minus; Mid &gt; 15%</td><td style="padding:4px 6px;">15% reduction</td><td style="padding:4px 6px;">Water pooling detected below root zone</td></tr>
</table>

<p style="margin-bottom:6px;font-weight:600;font-size:13px;">Combined Formula</p>
<p style="margin-bottom:6px;font-size:13px;">The final multiplier is calculated as: <strong>Base (root zone) &times; Rain adjustment &times; Deep guard</strong>. For zones with multiple probes, the <strong>Multi-Probe Mode</strong> setting controls how readings are combined (see below).</p>
<p style="margin-bottom:10px;font-size:13px;"><strong>Combined watering factor</strong> = Weather Multiplier &times; Moisture Multiplier. This combined factor is applied per-zone to run durations. Only zones with mapped probes are affected by moisture &mdash; unmapped zones use weather-only.</p>

<p style="margin-bottom:6px;font-weight:600;font-size:13px;">Multi-Probe Mode</p>
<p style="margin-bottom:6px;font-size:13px;">When multiple probes are mapped to the same zone, this setting (in Settings) controls how their readings are combined:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Conservative</strong> (default) &mdash; Uses the wettest probe reading (lowest multiplier). If ANY probe detects saturated soil, the zone is skipped. Best for preventing over-watering.</li>
<li style="margin-bottom:4px;"><strong>Average</strong> &mdash; Averages all probe readings. Skips the zone only if a majority of probes detect saturated soil. Good for zones with variable soil conditions.</li>
<li style="margin-bottom:4px;"><strong>Optimistic</strong> &mdash; Uses the driest probe reading (highest multiplier). Skips the zone only if ALL probes detect saturated soil. Best for preventing under-watering in zones with dry spots.</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:0 0 12px 0;font-size:13px;">💡 For zones with only one probe, the Multi-Probe Mode setting has no effect.</div>

<p style="margin-bottom:10px;">The moisture card also shows:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Probe tiles</strong> — Color-coded bars showing moisture level at each depth, with stale-data indicators</li><li style="margin-bottom:4px;"><strong>Device status</strong> — WiFi signal strength, battery percentage, solar charging state, sleep duration, and estimated next wake time are shown below the moisture readings when available (auto-detected from the Gophr device). When sleeping, the badge shows "Wake in X min" or "Wake at HH:MM" based on when the probe fell asleep plus the sleep duration.</li><li style="margin-bottom:4px;"><strong>Settings</strong> — Root zone thresholds (Skip, Wet, Optimal, Dry), max increase/decrease percentages, and rain detection sensitivity</li><li style="margin-bottom:4px;"><strong>Manage Probes</strong> — Select a Gophr device from the dropdown to auto-detect sensors, add/remove probes, assign to zones</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Moisture probes adjust both timed API/dashboard runs and ESPHome scheduled runs. The algorithm integrates weather forecast data for rain detection — if the shallow sensor shows a wetting front and rain is forecasted, watering is automatically reduced or skipped. Gophr devices sleep between readings — while the device is asleep, the system uses the last known good sensor values so the moisture multiplier stays active. If the cached readings become older than the Stale Reading Threshold, they are treated as stale and the multiplier reverts to neutral (1.0x).</div>

<p style="margin-bottom:6px;font-weight:600;font-size:13px;">Probe-Aware Irrigation (Schedule Timeline)</p>
<p style="margin-bottom:6px;font-size:13px;">The system automatically manages probe sleep/wake cycles around scheduled irrigation runs. For each probe with mapped zones, it:</p>
<ol style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Calculates</strong> when each zone will run based on the schedule start times and zone durations</li><li style="margin-bottom:4px;"><strong>Reprograms</strong> the probe&rsquo;s sleep duration before the schedule starts so it wakes up ~10 minutes before its mapped zone</li><li style="margin-bottom:4px;"><strong>Checks moisture</strong> when the probe wakes &mdash; if the soil is saturated, the zone is automatically <strong>skipped</strong> (disabled before it even starts)</li><li style="margin-bottom:4px;">If not saturated, <strong>disables sleep</strong> to keep the probe awake for continuous monitoring during the zone run</li><li style="margin-bottom:4px;">If consecutive mapped zones are close together (gap &le; probe sleep duration), the probe <strong>stays awake</strong> through both zones instead of sleeping and re-waking</li><li style="margin-bottom:4px;">If saturation is detected <strong>mid-run</strong>, the zone is shut off and the system <strong>auto-advances</strong> to the next zone</li><li style="margin-bottom:4px;">After the last mapped zone finishes, the <strong>original sleep duration</strong> is restored and any skipped zones are re-enabled for the next run</li></ol>
<p style="margin-bottom:6px;font-size:13px;">Click <strong>Wake Schedule</strong> on a probe card to see all mapped zones with their expected wake/run times. Each entry shows one of three states:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;">&#9200; <strong>Wake at HH:MM</strong> &mdash; The probe will wake from sleep before this zone runs</li><li style="margin-bottom:4px;">&#128065; <strong>Keep Awake</strong> &mdash; The probe stays awake from the previous zone (gap is shorter than sleep duration)</li><li style="margin-bottom:4px;">&#9940; <strong>Skip</strong> &mdash; The zone is saturated and will be skipped; the probe will not wake for it</li></ul>
<p style="margin-bottom:6px;font-size:13px;">The next upcoming entry is highlighted with a <strong>NEXT</strong> badge. All times use your configured timezone. The timeline recalculates automatically whenever schedule start times, zone durations, zone enable states, or probe mappings change.</p>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 The timeline uses the <strong>current adjusted durations</strong> (factored by weather and moisture) when &ldquo;Apply Factors to Schedule&rdquo; is enabled. This means probe wake times automatically shift when factors change.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Run History</h4>
<p style="margin-bottom:10px;">The run history table shows every zone on/off event with:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Zone name</strong> and source (API, schedule, weather pause, etc.)</li><li style="margin-bottom:4px;"><strong>State</strong> — ON (green) or OFF</li><li style="margin-bottom:4px;"><strong>Time</strong> and <strong>duration</strong> of each run</li><li style="margin-bottom:4px;"><strong>Watering Factor</strong> — The weather-based multiplier applied to schedule-triggered runs (green at 1.0x, yellow below, red above)</li><li style="margin-bottom:4px;"><strong>Probe Factor</strong> — The moisture probe multiplier (only shown when probes are enabled); includes sensor readings at each depth (T=Top/shallow, M=Middle/root zone, B=Bottom/deep) as percentages</li><li style="margin-bottom:4px;"><strong>Weather</strong> — Conditions at the time of the event with any triggered rules</li></ul>
<p style="margin-bottom:10px;">Use the time range dropdown to view the last 24 hours, 7 days, 30 days, 90 days, or full year. Click <strong>Export CSV</strong> to download history as a spreadsheet. The CSV includes additional columns for probe sensor readings (top, mid, bottom percentages) and moisture profile.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">&#128167; Water Monitor &amp; Water Source</h4>
<p style="margin-bottom:10px;">The Water Monitor card shows total water usage calculated from zone run times and configured GPM (gallons per minute) values from your Zone Head Details. Click the <strong>&#9881;&#65039; gear</strong> button to configure your water source:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>City Water</strong> &mdash; Municipal water supply; enter your cost per 1,000 gallons to see estimated water costs</li><li style="margin-bottom:4px;"><strong>Reclaimed Water</strong> &mdash; Recycled/reclaimed water; enter your cost per 1,000 gallons</li><li style="margin-bottom:4px;"><strong>Well Water</strong> &mdash; Private well (auto-detected when a Pump Start Relay is configured); no water utility cost &mdash; electricity costs are tracked in the Pump Monitor card</li></ul>
<p style="margin-bottom:10px;">When a cost is configured, the estimated water cost appears below the total gallons on the card and in PDF reports.</p>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">&#128161; If your controller has a Pump Start Relay zone, the water source automatically defaults to Well Water. You can change this at any time.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">&#9889; Pump Monitor</h4>
<p style="margin-bottom:10px;">If one of your zones is configured as a <strong>Pump Start Relay</strong>, a dedicated Pump Monitor card appears alongside the Water Monitor card. The card shows real-time pump usage statistics:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Total Cycles</strong> &mdash; Number of completed pump on/off cycles in the selected time range</li><li style="margin-bottom:4px;"><strong>Run Hours</strong> &mdash; Total hours the pump has been running</li><li style="margin-bottom:4px;"><strong>Power Used</strong> &mdash; Total electricity consumption in kilowatt-hours (kWh), calculated from pump HP/kW rating and run time</li><li style="margin-bottom:4px;"><strong>Estimated Cost</strong> &mdash; Electricity cost based on your configured rate ($/kWh)</li></ul>
<p style="margin-bottom:10px;">Use the <strong>time range dropdown</strong> to filter stats: Last 24 Hours, Last 30 Days (default), Last 90 Days, or Last Year.</p>
<p style="margin-bottom:10px;">Click the <strong>&#9881;&#65039; gear</strong> button to open Pump Settings where you can configure:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Brand</strong> &mdash; Pump manufacturer (e.g., Pentair, Hayward)</li><li style="margin-bottom:4px;"><strong>Horsepower / Kilowatts</strong> &mdash; Enter either value and the other is auto-calculated (1 HP = 0.7457 kW)</li><li style="margin-bottom:4px;"><strong>Voltage</strong> &mdash; Operating voltage (default 240V)</li><li style="margin-bottom:4px;"><strong>Year Installed</strong> &mdash; Used to calculate pump age displayed on the card</li><li style="margin-bottom:4px;"><strong>Electricity Cost ($/kWh)</strong> &mdash; Your standard electricity rate for cost estimates</li><li style="margin-bottom:4px;"><strong>Peak Rate ($/kWh)</strong> &mdash; Peak hours electricity rate for reference</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">&#128161; The pump relay zone is auto-detected from your controller&rsquo;s zone mode settings. If no pump relay is configured, the Water Monitor card stays full-width. The pump info line shows brand, power rating, voltage, and pump age (current year minus year installed).</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">PDF System Report</h4>
<p style="margin-bottom:10px;">The <strong>PDF System Report</strong> card appears below the status tiles. Select a time range and click <strong>Generate</strong> to create a comprehensive, professionally branded PDF document covering your entire irrigation system. The report includes:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>System Status</strong> &mdash; Online/offline, paused/active, weather multiplier, moisture status</li><li style="margin-bottom:4px;"><strong>Active Issues</strong> &mdash; Any reported issues with severity, description, and status</li><li style="margin-bottom:4px;"><strong>Zones Overview</strong> &mdash; All zones with name, state, GPM, and head count</li><li style="margin-bottom:4px;"><strong>Zone Head Details</strong> &mdash; Complete sprinkler head inventory per zone (type, brand, model, GPM, arc, radius, PSI)</li><li style="margin-bottom:4px;"><strong>Weather Settings</strong> &mdash; Current conditions, multiplier, and active adjustment rules</li><li style="margin-bottom:4px;"><strong>Moisture Probes</strong> &mdash; Probe configuration, mapped zones, and thresholds</li><li style="margin-bottom:4px;"><strong>Sensors</strong> &mdash; All sensor readings with values and units</li><li style="margin-bottom:4px;"><strong>Estimated Water Usage</strong> &mdash; Total gallons, per-zone breakdown, water source type, and estimated cost (when configured)</li><li style="margin-bottom:4px;"><strong>Run History</strong> &mdash; Recent zone run events with durations and sources</li></ul>
<p style="margin-bottom:10px;">Use the <strong>time range dropdown</strong> to select the period for history and water usage data: 24 Hours, 7 Days, 30 Days (default), 90 Days, or 1 Year. The PDF opens in a new tab for viewing or downloading.</p>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">&#128161; The report is generated server-side and branded with Flux Open Home and Gophr logos. Your management company can customize the report with their own logo, company name, accent color, section visibility, and footer text.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Expansion Boards</h4>
<p style="margin-bottom:10px;">If your controller supports I2C expansion boards for additional zones, the Expansion Boards card shows:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Zone Count</strong> — Total number of zones detected (base board + expansion)</li><li style="margin-bottom:4px;"><strong>Board Details</strong> — I2C addresses of connected expansion boards, with the zone range each board controls</li><li style="margin-bottom:4px;"><strong>Rescan</strong> — Trigger an I2C bus rescan to detect newly connected or disconnected boards</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">&#128161; The firmware pre-creates entities for up to 32 zones (to support up to 3 expansion boards). The system automatically detects how many zones are physically connected and only shows those zones throughout the dashboard — zone tiles, schedule settings, enables, and durations are all filtered to match.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">System Pause / Resume</h4>
<p style="margin-bottom:10px;"><strong>Pause System</strong> immediately stops all active zones and prevents any new zones from starting — including ESPHome schedule programs. While paused, any zone that tries to turn on will be automatically shut off.</p>
<p style="margin-bottom:10px;"><strong>Resume System</strong> lifts the pause and allows normal operation. Weather-triggered pauses auto-resume when conditions clear; manual pauses require clicking Resume.</p>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Use <strong>Emergency Stop All</strong> for a quick one-time stop. Use <strong>Pause System</strong> when you need to keep everything off until you manually resume.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Configuration Change Log</h4>
<p style="margin-bottom:10px;">Click the <strong>&#128203; Log</strong> button in the header to view a log of all configuration changes. Every change records:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Time</strong> — When the change was made (shown in your local timezone)</li><li style="margin-bottom:4px;"><strong>Who</strong> — Whether the change was made by the Homeowner (blue badge) or Management company (green badge)</li><li style="margin-bottom:4px;"><strong>Category</strong> — What type of setting was changed (Schedule, Weather Rules, Moisture Probes, System, Zone Control, Device Config, Connection Key, etc.)</li><li style="margin-bottom:4px;"><strong>Change</strong> — A detailed description of what was changed, showing old and new values (e.g., &quot;Humidity Threshold (%): 80 -&gt; 90&quot;, &quot;Zone alias Zone 1: Front Yard -&gt; Front Garden&quot;)</li></ul>
<p style="margin-bottom:10px;">The system stores up to 1,000 entries. When the limit is reached, the oldest entries are automatically overwritten. Records cannot be deleted. Click <strong>Export CSV</strong> to download the full log as a spreadsheet.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Report an Issue</h4>
<p style="margin-bottom:10px;">Click the <strong>&#9888;&#65039; Warning</strong> button in the header to report an issue to your management company. You can:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Select Severity</strong> — Choose from three levels: <span style="color:#3498db;font-weight:600;">Clarification</span> (question or minor request), <span style="color:#f39c12;font-weight:600;">Annoyance</span> (something bothering you), or <span style="color:#e74c3c;font-weight:600;">Severe Issue</span> (urgent problem needing immediate attention)</li><li style="margin-bottom:4px;"><strong>Describe the Issue</strong> — Provide details about what you are experiencing (up to 1,000 characters)</li></ul>
<p style="margin-bottom:10px;">After submitting, your issue appears in the <strong>Your Reported Issues</strong> section below the dashboard title. You can track the status of each issue:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Submitted</strong> — Your issue has been sent to management</li><li style="margin-bottom:4px;"><strong>Acknowledged</strong> — Management has reviewed your issue and may have left a note</li><li style="margin-bottom:4px;"><strong>Service Scheduled</strong> — A service date has been set</li><li style="margin-bottom:4px;"><strong>Resolved</strong> — Management has marked your issue as complete. You will see their response and can click <strong>Dismiss</strong> to remove it from your dashboard</li></ul>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Upcoming Service</h4>
<p style="margin-bottom:10px;">When your management company schedules a service visit, a green <strong>Upcoming Service</strong> banner appears at the top of your dashboard showing the scheduled date. If management included a note, it appears below the date. <strong>Tap the banner</strong> to add the appointment to your calendar — on mobile it opens Google Calendar with the event pre-filled; on desktop it downloads a calendar file (.ics) that opens in your default calendar app.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Property Address</h4>
<p style="margin-bottom:10px;">Your property address is shown below the dashboard title. <strong>Tap the address</strong> to open it in your default maps application (Apple Maps on iOS/Mac, Google Maps on other devices).</p>

<div style="border-top:1px solid var(--border-light);margin-top:20px;padding-top:16px;text-align:center;">
<a href="https://github.com/FluxOpenHome/ha-flux-irrigation-addons/blob/main/flux-irrigation-api/README.md" target="_blank" style="color:var(--color-primary);font-size:14px;font-weight:500;text-decoration:none;">&#128214; Full Documentation on GitHub</a>
</div>
`;

// --- Change Log ---
var _clAllEntries = [];
async function showChangelog() {
    document.getElementById('changelogModal').style.display = 'flex';
    document.getElementById('clFilterActor').value = 'all';
    document.getElementById('clFilterTime').value = '30';
    var catSel = document.getElementById('clFilterCategory');
    catSel.innerHTML = '<option value="all">All Categories</option>';
    loadChangelog();
}
function closeChangelogModal() {
    document.getElementById('changelogModal').style.display = 'none';
}
async function loadChangelog() {
    var el = document.getElementById('changelogContent');
    try {
        var data = await api('/changelog?limit=1000');
        _clAllEntries = data.entries || [];
        // Populate category filter dynamically
        var cats = {};
        _clAllEntries.forEach(function(e) { if (e.category) cats[e.category] = true; });
        var catSel = document.getElementById('clFilterCategory');
        var prev = catSel.value;
        catSel.innerHTML = '<option value="all">All Categories</option>';
        Object.keys(cats).sort().forEach(function(c) {
            catSel.innerHTML += '<option value="' + esc(c) + '">' + esc(c) + '</option>';
        });
        catSel.value = prev || 'all';
        if (!catSel.value) catSel.value = 'all';
        applyChangelogFilters();
    } catch (err) {
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load change log.</div>';
    }
}
function applyChangelogFilters() {
    var el = document.getElementById('changelogContent');
    var actorVal = document.getElementById('clFilterActor').value;
    var timeDays = parseInt(document.getElementById('clFilterTime').value);
    var catVal = document.getElementById('clFilterCategory').value;
    var cutoff = new Date(Date.now() - timeDays * 86400000);
    var filtered = _clAllEntries.filter(function(e) {
        if (actorVal !== 'all' && e.actor !== actorVal) return false;
        if (catVal !== 'all' && (e.category || '') !== catVal) return false;
        var dt = new Date(e.timestamp);
        if (dt < cutoff) return false;
        return true;
    });
    document.getElementById('clFilterCount').textContent = filtered.length + ' of ' + _clAllEntries.length + ' entries';
    if (filtered.length === 0) {
        el.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:32px;">No changes match the current filters.</div>';
        return;
    }
    var html = '<table style="width:100%;border-collapse:collapse;font-size:12px;">';
    html += '<thead><tr style="border-bottom:2px solid var(--border-light);text-align:left;">';
    html += '<th style="padding:6px 8px;">Time</th>';
    html += '<th style="padding:6px 8px;">Who</th>';
    html += '<th style="padding:6px 8px;">Category</th>';
    html += '<th style="padding:6px 8px;">Change</th>';
    html += '</tr></thead><tbody>';
    filtered.forEach(function(e) {
        var dt = new Date(e.timestamp);
        var _clMon = dt.toLocaleDateString('en-US', {month:'short'});
        var _clDay = dt.getDate();
        var _clYr = String(dt.getFullYear()).slice(-2);
        var _clTime = dt.toLocaleTimeString(undefined, {hour:'numeric',minute:'2-digit'});
        var timeStr = _clMon + ' ' + _clDay + '-' + _clYr + ' ' + _clTime;
        var isHO = e.actor === 'Homeowner';
        var badge = '<span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;' +
            'background:' + (isHO ? 'rgba(59,130,246,0.15)' : 'rgba(34,197,94,0.15)') + ';' +
            'color:' + (isHO ? 'var(--color-info)' : 'var(--color-success)') + ';">' +
            esc(e.actor) + '</span>';
        html += '<tr style="border-bottom:1px solid var(--border-light);">';
        html += '<td style="padding:6px 8px;white-space:nowrap;color:var(--text-muted);">' + esc(timeStr) + '</td>';
        html += '<td style="padding:6px 8px;">' + badge + '</td>';
        html += '<td style="padding:6px 8px;color:var(--text-muted);">' + esc(e.category || '') + '</td>';
        html += '<td style="padding:6px 8px;">' + esc(e.description || '') + '</td>';
        html += '</tr>';
    });
    html += '</tbody></table>';
    el.innerHTML = html;
}
function exportChangelogCSV() {
    window.open(HBASE + '/changelog/csv', '_blank');
}
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('changelogModal').style.display === 'flex') {
        closeChangelogModal();
    }
});
document.getElementById('changelogModal').addEventListener('click', function(e) {
    if (e.target === this) closeChangelogModal();
});

// --- Help ---
function showHelp() {
    document.getElementById('helpContent').innerHTML = HELP_CONTENT;
    document.getElementById('helpModal').style.display = 'flex';
}
function closeHelpModal() {
    document.getElementById('helpModal').style.display = 'none';
}

// --- Zone Head Details ---
var _hoNozzleRef = null;

async function hoShowZoneDetailsModal(entityId, displayName) {
    // Load reference data if not cached
    if (!_hoNozzleRef) {
        try { _hoNozzleRef = await api('/zone_heads/reference'); } catch(e) { _hoNozzleRef = {nozzle_types:[],brands:[],standard_arcs:[],models:[]}; }
    }
    // Load existing zone head data
    var zoneData = {heads:[], notes:'', show_gpm_on_card:false, show_head_count_on_card:false};
    try {
        var resp = await api('/zone_heads/' + entityId + '?t=' + Date.now());
        if (resp) zoneData = resp;
    } catch(e) {}

    // Detect if site map manages this zone (heads have lat/lng from editor)
    var _hoSiteMapManaged = zoneData.heads.some(function(h) { return !!(h.lat || h.lng); });
    window._hoZoneSiteMapManaged = _hoSiteMapManaged;

    var body = '<div style="margin-bottom:10px;">';

    if (_hoSiteMapManaged) {
        // Site-map managed notice
        body += '<div style="margin-bottom:10px;padding:8px 12px;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.25);border-radius:6px;font-size:12px;color:rgba(59,130,246,0.9);">';
        body += '<strong>&#128205; Site Map Managed</strong> &mdash; Head type, name, arc, radius, and zone area are set by your irrigation company via the Site Map Editor (shown greyed out). You can still edit GPM, brand, model, mount, pop-up height, PSI, and notes.';
        body += '</div>';
        body += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">';
        body += '<label style="font-weight:600;font-size:13px;">Number of Heads:</label>';
        body += '<span style="font-weight:700;font-size:14px;color:var(--text-primary);padding:4px 8px;background:var(--bg-hover);border-radius:4px;">' + zoneData.heads.length + '</span>';
        body += '<span style="font-size:11px;color:rgba(59,130,246,0.7);">&#128274; Managed</span>';
        body += '</div>';
    } else {
        body += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">';
        body += '<label style="font-weight:600;font-size:13px;">Number of Heads:</label>';
        body += '<input type="number" id="hoHeadCount" min="0" max="50" value="' + (zoneData.heads.length || 0) + '" style="width:60px;padding:4px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:13px;background:var(--bg-input);color:var(--text-primary);">';
        body += '<button class="btn btn-primary btn-sm" onclick="hoBuildHeadTable()" style="font-size:11px;">Update Table</button>';
        body += '</div>';

        body += '<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">';
        body += '<label style="font-weight:600;font-size:13px;">Copy From:</label>';
        body += '<select id="hoCopyFromZone" style="flex:1;max-width:250px;padding:4px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:13px;background:var(--bg-input);color:var(--text-primary);">';
        body += '<option value="">\\u2014 Select a zone \\u2014</option>';
        body += '</select>';
        body += '<button class="btn btn-sm" onclick="hoCopyFromZone()" style="font-size:11px;background:var(--bg-hover);border:1px solid var(--border-light);color:var(--text-primary);">&#128203; Copy</button>';
        body += '</div>';
    }

    body += '<div id="hoHeadTableWrap"></div>';

    // Lock area_sqft when site map manages this zone (area comes from boundary polygons set by management company)
    var _hoAreaRo = _hoSiteMapManaged ? ' readonly' : '';
    var _hoAreaBg = _hoSiteMapManaged ? 'background:var(--bg-hover);color:var(--text-secondary);cursor:not-allowed;opacity:0.7;' : 'background:var(--bg-input);color:var(--text-primary);';
    body += '<div style="margin-top:10px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">';
    body += '<div style="flex:0 0 auto;">';
    body += '<label style="font-weight:600;font-size:13px;display:block;margin-bottom:4px;">Zone Area (sq ft):' + (_hoSiteMapManaged ? ' <span style="font-size:10px;color:rgba(59,130,246,0.7);">&#128274; managed</span>' : '') + '</label>';
    body += '<input type="number" id="hoZoneAreaSqft" min="0" max="100000" step="1" value="' + (zoneData.area_sqft || '') + '" placeholder="e.g. 1500"' + _hoAreaRo + ' style="width:130px;padding:4px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:13px;' + _hoAreaBg + '">';
    body += '</div>';
    body += '<div style="flex:0 0 auto;">';
    body += '<label style="font-weight:600;font-size:13px;display:block;margin-bottom:4px;">Soil Type:</label>';
    body += '<select id="hoZoneSoilType" style="width:160px;padding:4px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:13px;background:var(--bg-input);color:var(--text-primary);">';
    body += '<option value="">-- Select --</option>';
    body += '<option value="sandy"' + (zoneData.soil_type === 'sandy' ? ' selected' : '') + '>Sandy</option>';
    body += '<option value="sandy_loam"' + (zoneData.soil_type === 'sandy_loam' ? ' selected' : '') + '>Sandy Loam</option>';
    body += '<option value="loam"' + (zoneData.soil_type === 'loam' ? ' selected' : '') + '>Loam</option>';
    body += '<option value="clay_loam"' + (zoneData.soil_type === 'clay_loam' ? ' selected' : '') + '>Clay Loam</option>';
    body += '<option value="silty_clay"' + (zoneData.soil_type === 'silty_clay' ? ' selected' : '') + '>Silty Clay</option>';
    body += '<option value="clay"' + (zoneData.soil_type === 'clay' ? ' selected' : '') + '>Clay</option>';
    body += '<option value="rock_gravel"' + (zoneData.soil_type === 'rock_gravel' ? ' selected' : '') + '>Rock / Gravel</option>';
    body += '</select>';
    body += '</div>';
    body += '';
    body += '</div>';

    body += '<div style="margin-top:10px;">';
    body += '<label style="font-weight:600;font-size:13px;display:block;margin-bottom:4px;">Zone Notes:</label>';
    body += '<textarea id="hoZoneNotes" rows="2" style="width:100%;padding:6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;resize:vertical;background:var(--bg-input);color:var(--text-primary);">' + esc(zoneData.notes || '') + '</textarea>';
    body += '</div>';

    body += '<div style="margin-top:10px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">';
    body += '<label style="display:flex;align-items:center;gap:5px;font-size:12px;color:var(--text-secondary);cursor:pointer;"><input type="checkbox" id="hoShowGpmOnCard"' + (zoneData.show_gpm_on_card ? ' checked' : '') + '> Show GPM on zone card</label>';
    body += '<label style="display:flex;align-items:center;gap:5px;font-size:12px;color:var(--text-secondary);cursor:pointer;"><input type="checkbox" id="hoShowHeadCountOnCard"' + (zoneData.show_head_count_on_card ? ' checked' : '') + '> Show head count on zone card</label>';
    body += '</div>';

    body += '<div style="margin-top:10px;display:flex;gap:8px;">';
    body += '<button class="btn btn-primary" onclick="hoSaveZoneHeads()" style="font-size:13px;">&#128190; Save</button>';
    body += '<button class="btn btn-sm" onclick="closeDynamicModal()" style="font-size:13px;background:transparent;border:1px solid var(--border-light);color:var(--text-secondary);">Cancel</button>';
    body += '<span id="hoZoneSaveStatus" style="font-size:12px;color:var(--color-success);align-self:center;"></span>';
    body += '</div>';

    if (_hoSiteMapManaged) {
        body += '<div style="margin-top:12px;padding:8px;background:var(--bg-hover);border-radius:6px;font-size:11px;color:var(--text-secondary);">';
        body += '<strong>&#128161; Note:</strong> Greyed-out fields (head type, name, arc, radius) are managed by your irrigation company through the Site Map Editor. ';
        body += 'You can edit GPM, brand, model, mount, pop-up height, PSI, notes, as well as zone area, soil type, and display preferences.';
        body += '</div>';
    } else {
        body += '<div style="margin-top:12px;padding:8px;background:var(--bg-hover);border-radius:6px;font-size:11px;color:var(--text-secondary);">';
        body += '<strong>&#128161; Tip:</strong> Document each sprinkler head in the zone — type, flow rate (GPM), spray arc, and location. ';
        body += 'This helps professionals service your system and ensures accurate watering calculations.';
        body += '</div>';
    }
    body += '</div>';

    // Store entity ID for save
    window._hoZoneDetailsEntityId = entityId;
    window._hoZoneDetailsHeads = zoneData.heads;

    showModal('Zone Details — ' + displayName, body, '95vw');

    // Build the table with existing data, then populate Copy From dropdown
    setTimeout(function() {
        hoRenderHeadTable(zoneData.heads);
        var copySelect = document.getElementById('hoCopyFromZone');
        if (copySelect) {
            var headCounts = window._hoZoneHeadCount || {};
            var zoneIds = Object.keys(headCounts).filter(function(eid) { return eid !== entityId; });
            zoneIds.sort(function(a, b) {
                var aNum = parseInt(extractZoneNumber(a, 'zone') || '999');
                var bNum = parseInt(extractZoneNumber(b, 'zone') || '999');
                return aNum - bNum;
            });
            for (var ci = 0; ci < zoneIds.length; ci++) {
                var opt = document.createElement('option');
                opt.value = zoneIds[ci];
                opt.textContent = resolveZoneName(zoneIds[ci]) + ' (' + headCounts[zoneIds[ci]] + ' heads)';
                copySelect.appendChild(opt);
            }
        }
    }, 50);
}

function hoBuildHeadTable() {
    if (window._hoZoneSiteMapManaged) {
        showToast('Head count is managed by the Site Map Editor', 'error');
        return;
    }
    var count = parseInt(document.getElementById('hoHeadCount').value) || 0;
    if (count < 0) count = 0;
    if (count > 50) count = 50;
    // Preserve existing data for rows that still exist
    var existing = hoCollectHeadData();
    var heads = [];
    for (var i = 0; i < count; i++) {
        heads.push(existing[i] || {});
    }
    hoRenderHeadTable(heads);
}

function hoRenderHeadTable(heads) {
    var wrap = document.getElementById('hoHeadTableWrap');
    var siteMapLocked = !!window._hoZoneSiteMapManaged;
    if (!heads || heads.length === 0) {
        wrap.innerHTML = '<div style="color:var(--text-secondary);font-size:12px;padding:8px;">No heads configured. Set the number above and click Update Table.</div>';
        var hcEl0 = document.getElementById('hoHeadCount');
        if (hcEl0) hcEl0.value = '0';
        return;
    }
    var hcEl = document.getElementById('hoHeadCount');
    if (hcEl) hcEl.value = String(heads.length);
    var ref = _hoNozzleRef || {nozzle_types:[],brands:[],standard_arcs:[],models:[]};

    // Disabled styling for site-map-controlled fields (nozzle_type, name, gpm, arc, radius)
    // Brand, model, mount, popup_height, psi, notes remain editable by homeowner.
    var _smDis = siteMapLocked ? ' disabled' : '';
    var _smRo = siteMapLocked ? ' readonly' : '';
    var _smBg = siteMapLocked ? 'background:var(--bg-hover);color:var(--text-secondary);cursor:not-allowed;opacity:0.7;' : 'background:var(--bg-input);color:var(--text-primary);';
    var _editBg = 'background:var(--bg-input);color:var(--text-primary);';

    // Check if boundary_name column should be shown (managed mode + any head has boundary_name)
    var showBoundaryCol = window._hoSystemMode === 'managed' && heads.some(function(h) { return h && h.boundary_name; });

    var html = '<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:11px;">';
    html += '<thead><tr style="background:var(--bg-hover);">';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;width:50px;"></th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">#</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Name / Location</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Head Type</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Brand</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Model</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Mount</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">GPM</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Arc (°)</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Radius (ft)</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Pop-Up Height</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">PSI</th>';
    html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Notes</th>';
    if (showBoundaryCol) html += '<th style="padding:6px;border:1px solid var(--border-light);white-space:nowrap;">Boundary Area</th>';
    html += '</tr></thead><tbody>';

    for (var i = 0; i < heads.length; i++) {
        var h = heads[i] || {};
        var rowBg = i % 2 === 0 ? '' : 'background:var(--bg-hover);';
        html += '<tr style="' + rowBg + '">';
        if (!siteMapLocked) {
            html += '<td style="padding:2px 4px;border:1px solid var(--border-light);text-align:center;white-space:nowrap;">';
            html += '<button onclick="hoCopyHeadDown(' + i + ')" title="Copy to rows below" style="background:none;border:none;cursor:pointer;font-size:13px;padding:1px 2px;color:var(--text-secondary);">\\u2b07</button>';
            html += '<button onclick="hoDuplicateHead(' + i + ')" title="Duplicate row" style="background:none;border:none;cursor:pointer;font-size:13px;padding:1px 2px;color:var(--text-secondary);">+</button>';
            html += '<button onclick="hoDeleteHead(' + i + ')" title="Delete head" style="background:none;border:none;cursor:pointer;font-size:13px;padding:1px 2px;color:var(--color-danger, #e74c3c);">\\u2715</button>';
            html += '</td>';
        } else {
            html += '<td style="padding:2px 4px;border:1px solid var(--border-light);text-align:center;white-space:nowrap;color:var(--text-secondary);font-size:10px;">&#128274;</td>';
        }
        html += '<td style="padding:4px 6px;border:1px solid var(--border-light);text-align:center;font-weight:600;">' + (i+1) + '</td>';

        // Name / Location — LOCKED by site map editor
        html += '<td style="padding:2px;border:1px solid var(--border-light);"><input type="text" data-field="name" data-row="' + i + '" value="' + esc(h.name || '') + '" placeholder="e.g. Front left corner"' + _smRo + ' style="width:100%;min-width:100px;padding:3px 4px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _smBg + '"></td>';

        // Head Type dropdown — LOCKED by site map editor
        html += '<td style="padding:2px;border:1px solid var(--border-light);"><select data-field="nozzle_type" data-row="' + i + '"' + _smDis + ' style="width:100%;min-width:90px;padding:3px 2px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _smBg + '">';
        html += '<option value="">—</option>';
        for (var t = 0; t < ref.nozzle_types.length; t++) {
            var nt = ref.nozzle_types[t];
            html += '<option value="' + nt.id + '"' + (h.nozzle_type === nt.id ? ' selected' : '') + '>' + esc(nt.name) + '</option>';
        }
        html += '</select></td>';

        // Brand — EDITABLE by homeowner
        html += '<td style="padding:2px;border:1px solid var(--border-light);"><select data-field="brand" data-row="' + i + '" style="width:100%;min-width:70px;padding:3px 2px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _editBg + '">';
        html += '<option value="">—</option>';
        for (var b = 0; b < ref.brands.length; b++) {
            html += '<option value="' + esc(ref.brands[b]) + '"' + (h.brand === ref.brands[b] ? ' selected' : '') + '>' + esc(ref.brands[b]) + '</option>';
        }
        html += '</select></td>';

        // Model — EDITABLE by homeowner
        html += '<td style="padding:2px;border:1px solid var(--border-light);">';
        html += '<select data-field="model_select" data-row="' + i + '" style="width:100%;min-width:100px;padding:3px 2px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _editBg + '">';
        html += '<option value="">—</option>';
        var selBrand = h.brand || '';
        var selType = h.nozzle_type || '';
        var models = (ref.models || []).filter(function(md) {
            return (!selBrand || md.brand === selBrand) && (!selType || md.nozzle_type === selType);
        });
        var foundModel = false;
        for (var mi = 0; mi < models.length; mi++) {
            var isSel = (h.model === models[mi].model);
            if (isSel) foundModel = true;
            html += '<option value="' + esc(models[mi].model) + '" data-gpm="' + (models[mi].gpm || '') + '"' + (isSel ? ' selected' : '') + '>' + esc(models[mi].model) + '</option>';
        }
        html += '<option value="__custom__"' + (h.model && !foundModel && h.model !== '' ? ' selected' : '') + '>Custom...</option>';
        html += '</select>';
        var showCustom = (h.model && !foundModel && h.model !== '') ? '' : 'display:none;';
        html += '<input type="text" data-field="model_custom" data-row="' + i + '" value="' + esc((!foundModel ? h.model : '') || '') + '" placeholder="Type model" style="' + showCustom + 'width:100%;margin-top:2px;padding:3px 4px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _editBg + '">';
        html += '</td>';

        // Mount type — EDITABLE by homeowner
        html += '<td style="padding:2px;border:1px solid var(--border-light);"><select data-field="mount" data-row="' + i + '" style="width:100%;min-width:65px;padding:3px 2px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _editBg + '">';
        html += '<option value="">—</option>';
        var mounts = ["Pop-Up","Stationary","Riser","Shrub","On-Grade"];
        for (var m = 0; m < mounts.length; m++) {
            html += '<option value="' + mounts[m] + '"' + (h.mount === mounts[m] ? ' selected' : '') + '>' + mounts[m] + '</option>';
        }
        html += '</select></td>';

        // GPM — EDITABLE by homeowner
        html += '<td style="padding:2px;border:1px solid var(--border-light);"><input type="number" data-field="gpm" data-row="' + i + '" value="' + (h.gpm || '') + '" min="0" max="20" step="0.01" placeholder="GPM" style="width:100%;min-width:50px;padding:3px 4px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _editBg + '"></td>';

        // Arc — LOCKED by site map editor
        html += '<td style="padding:2px;border:1px solid var(--border-light);"><input type="number" data-field="arc_degrees" data-row="' + i + '" value="' + (h.arc_degrees || '') + '" min="0" max="360" step="1" placeholder="°"' + _smRo + ' style="width:100%;min-width:45px;padding:3px 4px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _smBg + '"></td>';

        // Radius — LOCKED by site map editor
        html += '<td style="padding:2px;border:1px solid var(--border-light);"><input type="number" data-field="radius_ft" data-row="' + i + '" value="' + (h.radius_ft || '') + '" min="0" max="200" step="0.5" placeholder="ft"' + _smRo + ' style="width:100%;min-width:45px;padding:3px 4px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _smBg + '"></td>';

        // Pop-up Height — EDITABLE by homeowner
        html += '<td style="padding:2px;border:1px solid var(--border-light);"><select data-field="popup_height" data-row="' + i + '" style="width:100%;min-width:50px;padding:3px 2px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _editBg + '">';
        html += '<option value="">—</option>';
        var heights = ['2"','3"','4"','6"','12"'];
        var heightVals = ['2','3','4','6','12'];
        for (var p = 0; p < heights.length; p++) {
            html += '<option value="' + heightVals[p] + '"' + (String(h.popup_height) === heightVals[p] ? ' selected' : '') + '>' + heights[p] + '</option>';
        }
        html += '</select></td>';

        // PSI — EDITABLE by homeowner (unless pump overrides it)
        var pumpPressureAvail = window._pumpZoneEntity && window._cachedPumpSettings && parseFloat(window._cachedPumpSettings.pressure_psi) > 0;
        var headPsi = pumpPressureAvail ? window._cachedPumpSettings.pressure_psi : (h.psi || '');
        if (pumpPressureAvail) {
            html += '<td style="padding:2px;border:1px solid var(--border-light);position:relative;"><input type="number" data-field="psi" data-row="' + i + '" value="' + headPsi + '" min="0" max="150" step="1" readonly style="width:100%;min-width:45px;padding:3px 4px;border:1px solid rgba(59,130,246,0.4);border-radius:3px;font-size:11px;background:rgba(59,130,246,0.08);color:var(--text-secondary);cursor:not-allowed;" title="Pressure set by pump (' + window._cachedPumpSettings.pressure_psi + ' PSI)"><span style="position:absolute;top:1px;right:3px;font-size:7px;color:rgba(59,130,246,0.7);">PUMP</span></td>';
        } else {
            html += '<td style="padding:2px;border:1px solid var(--border-light);"><input type="number" data-field="psi" data-row="' + i + '" value="' + (h.psi || '') + '" min="0" max="150" step="1" placeholder="PSI" style="width:100%;min-width:45px;padding:3px 4px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _editBg + '"></td>';
        }

        // Notes — EDITABLE by homeowner
        html += '<td style="padding:2px;border:1px solid var(--border-light);"><input type="text" data-field="head_notes" data-row="' + i + '" value="' + esc(h.head_notes || '') + '" placeholder="Notes" style="width:100%;min-width:80px;padding:3px 4px;border:1px solid var(--border-input);border-radius:3px;font-size:11px;' + _editBg + '"></td>';

        // Boundary Area (only if managed mode + data exists)
        if (showBoundaryCol) html += '<td style="padding:4px 6px;border:1px solid var(--border-light);font-size:11px;color:var(--text-secondary);white-space:nowrap;">' + esc(h.boundary_name || '') + '</td>';

        html += '</tr>';
    }
    html += '</tbody></table></div>';

    // Total GPM summary
    html += '<div id="hoHeadGpmSummary" style="margin-top:6px;font-size:12px;color:var(--text-secondary);"></div>';

    wrap.innerHTML = html;

    // Update GPM summary
    hoUpdateGpmSummary();

    // Add GPM change listeners
    var gpmInputs = wrap.querySelectorAll('input[data-field="gpm"]');
    for (var g = 0; g < gpmInputs.length; g++) {
        gpmInputs[g].addEventListener('input', function() { hoUpdateGpmSummary(); });
    }

    // Model select: auto-fill GPM + toggle custom input
    var modelSels = wrap.querySelectorAll('select[data-field="model_select"]');
    for (var ms = 0; ms < modelSels.length; ms++) {
        modelSels[ms].addEventListener('change', function() {
            var row = this.getAttribute('data-row');
            var customInput = wrap.querySelector('input[data-field="model_custom"][data-row="' + row + '"]');
            if (this.value === '__custom__') {
                customInput.style.display = '';
                customInput.focus();
            } else {
                customInput.style.display = 'none';
                customInput.value = '';
                // Auto-fill GPM from selected model
                var opt = this.options[this.selectedIndex];
                var modelGpm = opt.getAttribute('data-gpm');
                if (modelGpm) {
                    var gpmInput = wrap.querySelector('input[data-field="gpm"][data-row="' + row + '"]');
                    if (gpmInput) {
                        gpmInput.value = modelGpm;
                        hoUpdateGpmSummary();
                    }
                }
            }
        });
    }

    // Brand / Type change: re-filter model picklist
    var brandSels = wrap.querySelectorAll('select[data-field="brand"]');
    var typeSels = wrap.querySelectorAll('select[data-field="nozzle_type"]');
    for (var bi = 0; bi < brandSels.length; bi++) {
        brandSels[bi].addEventListener('change', function() { hoRefreshModelOptions(this.getAttribute('data-row')); });
    }
    for (var ti = 0; ti < typeSels.length; ti++) {
        typeSels[ti].addEventListener('change', function() { hoRefreshModelOptions(this.getAttribute('data-row')); });
    }
}

function hoRefreshModelOptions(row) {
    var wrap = document.getElementById('hoHeadTableWrap');
    var ref = _hoNozzleRef || {nozzle_types:[],brands:[],standard_arcs:[],models:[]};
    var brandEl = wrap.querySelector('select[data-field="brand"][data-row="' + row + '"]');
    var typeEl = wrap.querySelector('select[data-field="nozzle_type"][data-row="' + row + '"]');
    var modelSel = wrap.querySelector('select[data-field="model_select"][data-row="' + row + '"]');
    if (!brandEl || !typeEl || !modelSel) return;
    var sb = brandEl.value || '';
    var st = typeEl.value || '';
    var allModels = (ref.models || []).filter(function(md) {
        return (!sb || md.brand === sb) && (!st || md.nozzle_type === st);
    });
    var curVal = modelSel.value;
    var opts = '<option value="">\\u2014</option>';
    for (var q = 0; q < allModels.length; q++) {
        opts += '<option value="' + esc(allModels[q].model) + '" data-gpm="' + (allModels[q].gpm || '') + '">' + esc(allModels[q].model) + '</option>';
    }
    opts += '<option value="__custom__">Custom...</option>';
    modelSel.innerHTML = opts;
    // Try to re-select previous value
    modelSel.value = curVal;
    if (modelSel.value !== curVal) modelSel.value = '';
}

function hoCopyHeadDown(sourceRow) {
    var wrap = document.getElementById('hoHeadTableWrap');
    if (!wrap) return;
    var rows = wrap.querySelectorAll('tbody tr');
    if (sourceRow >= rows.length - 1) { showToast('No rows below to copy to'); return; }

    // Fields to copy (skip name — location is unique per head)
    var copyFields = ['nozzle_type','brand','mount','gpm','arc_degrees','radius_ft','popup_height','psi','head_notes'];
    var srcRow = rows[sourceRow];
    var srcVals = {};
    copyFields.forEach(function(f) {
        var el = srcRow.querySelector('[data-field="' + f + '"]');
        if (el) srcVals[f] = el.value;
    });
    // Handle model (select + custom)
    var srcModelSel = srcRow.querySelector('[data-field="model_select"]');
    var srcModelCustom = srcRow.querySelector('[data-field="model_custom"]');
    var srcModelSelVal = srcModelSel ? srcModelSel.value : '';
    var srcModelCustomVal = srcModelCustom ? srcModelCustom.value : '';

    var count = 0;
    for (var i = sourceRow + 1; i < rows.length; i++) {
        copyFields.forEach(function(f) {
            var el = rows[i].querySelector('[data-field="' + f + '"]');
            if (el && srcVals[f] !== undefined) el.value = srcVals[f];
        });
        // Refresh model options after brand/type change, then set model
        hoRefreshModelOptions(i);
        var modelSel = rows[i].querySelector('[data-field="model_select"]');
        var modelCustom = rows[i].querySelector('[data-field="model_custom"]');
        if (modelSel) {
            modelSel.value = srcModelSelVal;
            if (modelSel.value !== srcModelSelVal) modelSel.value = '';
        }
        if (modelCustom) {
            modelCustom.value = srcModelCustomVal;
            modelCustom.style.display = srcModelSelVal === '__custom__' ? '' : 'none';
        }
        count++;
    }
    hoUpdateGpmSummary();
    showToast('Copied to ' + count + ' row' + (count > 1 ? 's' : '') + ' below');
}

function hoDuplicateHead(sourceRow) {
    var heads = hoCollectHeadData();
    if (sourceRow >= heads.length) return;
    var clone = JSON.parse(JSON.stringify(heads[sourceRow]));
    clone.name = '';
    heads.push(clone);
    document.getElementById('hoHeadCount').value = String(heads.length);
    hoRenderHeadTable(heads);
    showToast('Row duplicated');
}

function hoDeleteHead(rowIdx) {
    if (!confirm('Delete head #' + (rowIdx + 1) + '?')) return;
    var heads = hoCollectHeadData();
    if (rowIdx >= heads.length) return;
    heads.splice(rowIdx, 1);
    var hcEl = document.getElementById('hoHeadCount');
    if (hcEl) hcEl.value = String(heads.length);
    hoRenderHeadTable(heads);
    if (typeof hoUpdateGpmSummary === 'function') hoUpdateGpmSummary();
    showToast('Head #' + (rowIdx + 1) + ' deleted');
}

async function hoCopyFromZone() {
    var select = document.getElementById('hoCopyFromZone');
    if (!select || !select.value) {
        showToast('Select a zone to copy from', 'error');
        return;
    }
    var sourceEntityId = select.value;
    var sourceName = resolveZoneName(sourceEntityId);
    // Check if target zone has existing data — confirm overwrite
    var existingHeads = hoCollectHeadData();
    if (existingHeads.length > 0) {
        if (!confirm('This will replace all ' + existingHeads.length + ' existing head(s) in this zone with data from ' + sourceName + '. Continue?')) {
            return;
        }
    }
    try {
        var srcData = await api('/zone_heads/' + sourceEntityId + '?t=' + Date.now());
        if (!srcData || !srcData.heads || srcData.heads.length === 0) {
            showToast('Source zone has no head data', 'error');
            return;
        }
        // Deep-clone heads and clear IDs (new UUIDs assigned on save)
        var newHeads = JSON.parse(JSON.stringify(srcData.heads));
        for (var i = 0; i < newHeads.length; i++) {
            newHeads[i].id = '';
        }
        // Update head count input
        document.getElementById('hoHeadCount').value = String(newHeads.length);
        // Copy zone notes
        var notesEl = document.getElementById('hoZoneNotes');
        if (notesEl && srcData.notes) notesEl.value = srcData.notes;
        // Copy display settings
        var gpmCheck = document.getElementById('hoShowGpmOnCard');
        if (gpmCheck) gpmCheck.checked = !!srcData.show_gpm_on_card;
        var countCheck = document.getElementById('hoShowHeadCountOnCard');
        if (countCheck) countCheck.checked = !!srcData.show_head_count_on_card;
        // Re-render the head table with copied data
        hoRenderHeadTable(newHeads);
        showToast('Copied ' + newHeads.length + ' head(s) from ' + sourceName + '. Review and Save.');
    } catch(e) {
        showToast('Failed to load zone data: ' + e.message, 'error');
    }
}

function hoUpdateGpmSummary() {
    var inputs = document.querySelectorAll('#hoHeadTableWrap input[data-field="gpm"]');
    var total = 0;
    for (var i = 0; i < inputs.length; i++) {
        total += parseFloat(inputs[i].value) || 0;
    }
    var el = document.getElementById('hoHeadGpmSummary');
    if (el) el.innerHTML = '<strong>Total Zone Flow: ' + total.toFixed(2) + ' GPM</strong>';
}

function hoCollectHeadData() {
    var wrap = document.getElementById('hoHeadTableWrap');
    if (!wrap) return [];
    var heads = [];
    var rows = wrap.querySelectorAll('tbody tr');
    for (var i = 0; i < rows.length; i++) {
        var head = {};
        var fields = rows[i].querySelectorAll('[data-field]');
        for (var j = 0; j < fields.length; j++) {
            var field = fields[j].getAttribute('data-field');
            var val = fields[j].value;
            if (field === 'model_select') {
                // Resolve model: picklist value or custom text
                if (val === '__custom__') {
                    var customEl = rows[i].querySelector('[data-field="model_custom"]');
                    head['model'] = customEl ? (customEl.value || '') : '';
                } else {
                    head['model'] = val || '';
                }
            } else if (field === 'model_custom') {
                // Handled by model_select above — skip
            } else if (field === 'gpm' || field === 'arc_degrees' || field === 'radius_ft' || field === 'psi') {
                head[field] = val ? parseFloat(val) : null;
            } else if (field === 'popup_height') {
                head[field] = val || null;
            } else {
                head[field] = val || '';
            }
        }
        heads.push(head);
    }
    return heads;
}

async function hoSaveZoneHeads() {
    var entityId = window._hoZoneDetailsEntityId;
    if (!entityId) return;
    var heads;
    if (window._hoZoneSiteMapManaged) {
        // Site-map managed: start from original heads, merge editable fields from DOM
        var origHeads = window._hoZoneDetailsHeads || [];
        heads = origHeads.map(function(h, idx) {
            var merged = Object.assign({}, h);
            // Merge editable fields from DOM (gpm, brand, model, mount, popup_height, psi, head_notes)
            var wrap = document.getElementById('hoHeadTableWrap');
            if (wrap) {
                var gpmInput = wrap.querySelector('input[data-field="gpm"][data-row="' + idx + '"]');
                if (gpmInput) merged.gpm = parseFloat(gpmInput.value) || 0;
                var brandSel = wrap.querySelector('select[data-field="brand"][data-row="' + idx + '"]');
                if (brandSel) merged.brand = brandSel.value || '';
                var modelSel = wrap.querySelector('select[data-field="model_select"][data-row="' + idx + '"]');
                var modelCustom = wrap.querySelector('input[data-field="model_custom"][data-row="' + idx + '"]');
                if (modelSel) {
                    if (modelSel.value === '__custom__' && modelCustom) merged.model = modelCustom.value || '';
                    else if (modelSel.value) merged.model = modelSel.value;
                }
                var mountSel = wrap.querySelector('select[data-field="mount"][data-row="' + idx + '"]');
                if (mountSel) merged.mount = mountSel.value || '';
                var popSel = wrap.querySelector('select[data-field="popup_height"][data-row="' + idx + '"]');
                if (popSel) merged.popup_height = popSel.value || '';
                var psiInput = wrap.querySelector('input[data-field="psi"][data-row="' + idx + '"]');
                if (psiInput && !psiInput.readOnly) merged.psi = parseFloat(psiInput.value) || 0;
                var notesInput = wrap.querySelector('input[data-field="head_notes"][data-row="' + idx + '"]');
                if (notesInput) merged.head_notes = notesInput.value || '';
            }
            return merged;
        });
    } else {
        heads = hoCollectHeadData();
    }
    var notes = (document.getElementById('hoZoneNotes') || {}).value || '';
    var areaSqft = document.getElementById('hoZoneAreaSqft') ? parseFloat(document.getElementById('hoZoneAreaSqft').value) || 0 : 0;
    var soilType = document.getElementById('hoZoneSoilType') ? document.getElementById('hoZoneSoilType').value || '' : '';
    var showGpm = document.getElementById('hoShowGpmOnCard') ? document.getElementById('hoShowGpmOnCard').checked : false;
    var showCount = document.getElementById('hoShowHeadCountOnCard') ? document.getElementById('hoShowHeadCountOnCard').checked : false;
    var statusEl = document.getElementById('hoZoneSaveStatus');
    try {
        statusEl.textContent = 'Saving...';
        statusEl.style.color = 'var(--text-secondary)';
        await api('/zone_heads/' + entityId, {
            method: 'PUT',
            body: JSON.stringify({ heads: heads, notes: notes, area_sqft: areaSqft, soil_type: soilType, show_gpm_on_card: showGpm, show_head_count_on_card: showCount }),
        });
        statusEl.textContent = '\\u2713 Saved!';
        statusEl.style.color = 'var(--color-success)';
        showToast('Zone head details saved');
        // Refresh zone card GPM display
        try {
            var allHeads = await api('/zone_heads?t=' + Date.now());
            window._hoZoneGpmMap = {};
            window._hoZoneGpmShow = {};
            window._hoZoneHeadCountShow = {};
            window._hoZoneHeadCount = {};
            for (var eid in allHeads) {
                if (allHeads[eid].total_gpm > 0) window._hoZoneGpmMap[eid] = allHeads[eid].total_gpm;
                if (allHeads[eid].show_gpm_on_card) window._hoZoneGpmShow[eid] = true;
                if (allHeads[eid].show_head_count_on_card) window._hoZoneHeadCountShow[eid] = true;
                if (allHeads[eid].heads && allHeads[eid].heads.length > 0) window._hoZoneHeadCount[eid] = allHeads[eid].heads.length;
            }
            loadZones();
        } catch(e2) {}
    } catch(e) {
        statusEl.textContent = 'Error: ' + e.message;
        statusEl.style.color = 'var(--color-danger)';
        showToast('Failed to save: ' + e.message, 'error');
    }
}


function showModal(title, bodyHtml, maxWidth) {
    document.getElementById('dynamicModalTitle').textContent = title;
    document.getElementById('dynamicModalBody').innerHTML = bodyHtml;
    var inner = document.getElementById('dynamicModal').querySelector('div');
    inner.style.maxWidth = maxWidth || '400px';
    inner.style.maxHeight = maxWidth ? '90vh' : '80vh';
    document.getElementById('dynamicModal').style.display = 'flex';
}
function closeDynamicModal() {
    document.getElementById('dynamicModal').style.display = 'none';
    var inner = document.getElementById('dynamicModal').querySelector('div');
    inner.style.maxWidth = '400px';
    inner.style.maxHeight = '80vh';
    if (_calWetTimer) { clearInterval(_calWetTimer); _calWetTimer = null; }
}
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (document.getElementById('dataNerdOverlay')) { dnClose(); return; }
        if (document.getElementById('notifPanelModal').style.display === 'flex') closeNotificationsPanel();
        else if (document.getElementById('helpModal').style.display === 'flex') closeHelpModal();
        else if (document.getElementById('dynamicModal').style.display === 'flex') closeDynamicModal();
    }
});

// ============================================================
// DATA NERD VIEW — Comprehensive Analytics Dashboard
// ============================================================
var _dnCharts = {};
var _dnRawData = null;
var _dnCurrentRange = 720; // 30 days default
var _dnCurrentUnit = 'gallons'; // or 'minutes'
var _dnThemeObserver = null;

var DN_COLORS = [
    {border:'rgba(46,204,113,0.85)',fill:'rgba(46,204,113,0.12)'},
    {border:'rgba(52,152,219,0.85)',fill:'rgba(52,152,219,0.12)'},
    {border:'rgba(26,188,156,0.75)',fill:'rgba(26,188,156,0.10)'},
    {border:'rgba(155,89,182,0.75)',fill:'rgba(155,89,182,0.10)'},
    {border:'rgba(243,156,18,0.75)',fill:'rgba(243,156,18,0.10)'},
    {border:'rgba(231,76,60,0.75)',fill:'rgba(231,76,60,0.10)'},
    {border:'rgba(41,128,185,0.75)',fill:'rgba(41,128,185,0.10)'},
    {border:'rgba(22,160,133,0.75)',fill:'rgba(22,160,133,0.10)'}
];

function dnOpen() {
    if (document.getElementById('dataNerdOverlay')) return;
    if (typeof Chart === 'undefined') { showToast('Chart library still loading, please wait...','warning'); return; }
    document.body.style.overflow = 'hidden';
    var overlay = document.createElement('div');
    overlay.id = 'dataNerdOverlay';
    overlay.innerHTML = '<div id="dnToolbar">' +
        '<button class="dn-toolbar-btn" onclick="dnClose()" title="Close">&#10005; Close</button>' +
        '<span style="font-size:15px;font-weight:700;color:var(--text-primary);letter-spacing:0.3px;">&#128202; Data Nerd View</span>' +
        '<div style="flex:1;"></div>' +
        '<div class="dn-range-group">' +
        '<button class="dn-range-btn" onclick="dnSetTimeRange(168)" data-range="168">7d</button>' +
        '<button class="dn-range-btn active" onclick="dnSetTimeRange(720)" data-range="720">30d</button>' +
        '<button class="dn-range-btn" onclick="dnSetTimeRange(2160)" data-range="2160">90d</button>' +
        '<button class="dn-range-btn" onclick="dnSetTimeRange(8760)" data-range="8760">1yr</button>' +
        '</div>' +
        '<button class="dn-toolbar-btn" id="dnUnitToggle" onclick="dnToggleUnit()">Show Minutes</button>' +
        '<button class="dn-toolbar-btn" onclick="dnExportCSV()">Export CSV</button>' +
        '</div>' +
        '<div id="dnContent"><div id="dnGrid"><div class="dn-full dn-loading">Loading data...</div></div></div>';
    document.body.appendChild(overlay);
    // Start theme observer
    _dnThemeObserver = new MutationObserver(function() {
        if (document.getElementById('dataNerdOverlay') && _dnRawData) {
            dnDestroyCharts();
            dnRenderAllCharts(_dnRawData);
        }
    });
    _dnThemeObserver.observe(document.body, {attributes:true, attributeFilter:['class']});
    // Fetch and render
    _dnRawData = null;
    dnFetchAndRender(_dnCurrentRange);
}

function dnClose() {
    dnDestroyCharts();
    if (_dnThemeObserver) { _dnThemeObserver.disconnect(); _dnThemeObserver = null; }
    var el = document.getElementById('dataNerdOverlay');
    if (el) el.remove();
    document.body.style.overflow = '';
}

function dnDestroyCharts() {
    Object.keys(_dnCharts).forEach(function(k) {
        try { _dnCharts[k].destroy(); } catch(e) {}
    });
    _dnCharts = {};
}

async function dnFetchAndRender(hours) {
    var grid = document.getElementById('dnGrid');
    if (!grid) return;
    grid.innerHTML = '<div class="dn-full dn-loading">Fetching ' + (hours <= 168 ? '7 days' : hours <= 720 ? '30 days' : hours <= 2160 ? '90 days' : '1 year') + ' of data...</div>';
    try {
        var results = await Promise.all([
            api('/history/runs?hours=' + hours).catch(function() { return {events:[]}; }),
            api('/weather/log?hours=' + hours + '&limit=10000').catch(function() { return {events:[]}; }),
            mapi('/probes').catch(function() { return {probes:{}}; }),
            api('/water_settings').catch(function() { return null; })
        ]);
        _dnRawData = {
            runs: (results[0].events || results[0] || []),
            weather: (results[1].events || results[1] || []),
            probes: results[2].probes || results[2] || {},
            waterSettings: results[3]
        };
        // Make runs an array if needed
        if (!Array.isArray(_dnRawData.runs)) {
            _dnRawData.runs = Object.values(_dnRawData.runs);
        }
        if (!Array.isArray(_dnRawData.weather)) {
            _dnRawData.weather = Object.values(_dnRawData.weather);
        }
        dnRenderAllCharts(_dnRawData);
    } catch(e) {
        grid.innerHTML = '<div class="dn-full dn-loading" style="color:var(--color-danger);">Error loading data: ' + esc(e.message || String(e)) + '</div>';
    }
}

function dnSetTimeRange(hours) {
    _dnCurrentRange = hours;
    document.querySelectorAll('.dn-range-btn').forEach(function(b) {
        b.classList.toggle('active', parseInt(b.getAttribute('data-range')) === hours);
    });
    dnDestroyCharts();
    dnFetchAndRender(hours);
}

function dnToggleUnit() {
    _dnCurrentUnit = _dnCurrentUnit === 'gallons' ? 'minutes' : 'gallons';
    var btn = document.getElementById('dnUnitToggle');
    if (btn) btn.textContent = _dnCurrentUnit === 'gallons' ? 'Show Minutes' : 'Show Gallons';
    if (_dnRawData) { dnDestroyCharts(); dnRenderAllCharts(_dnRawData); }
}

// --- Chart defaults ---
function dnChartDefaults() {
    var isDark = document.body.classList.contains('dark-mode');
    var gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
    var textColor = isDark ? '#8a9bb0' : '#7f8c8d';
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600, easing: 'easeOutQuart' },
        plugins: {
            legend: {
                labels: {
                    color: textColor,
                    font: { family: '-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif', size: 11 },
                    usePointStyle: true,
                    pointStyleWidth: 8,
                    padding: 12
                }
            },
            tooltip: {
                backgroundColor: isDark ? 'rgba(15,25,50,0.95)' : 'rgba(255,255,255,0.95)',
                titleColor: isDark ? '#e0e0e0' : '#2c3e50',
                bodyColor: isDark ? '#b0b0b0' : '#555',
                borderColor: isDark ? 'rgba(46,204,113,0.3)' : 'rgba(0,0,0,0.1)',
                borderWidth: 1,
                padding: 10,
                cornerRadius: 8,
                displayColors: true,
                titleFont: { weight: '600' }
            }
        },
        scales: {
            x: { grid: { color: gridColor }, ticks: { color: textColor, font: { size: 10 }, maxRotation: 45 } },
            y: { grid: { color: gridColor }, ticks: { color: textColor, font: { size: 10 } }, beginAtZero: true }
        }
    };
}

// --- GPM Map builder ---
function dnBuildGpmMap(data) {
    var gpm = {};
    if (data.waterSettings && data.waterSettings.zones) {
        var zones = data.waterSettings.zones;
        for (var eid in zones) {
            if (zones[eid].gpm) gpm[eid] = zones[eid].gpm;
        }
    }
    // Also try from zone name map
    if (window._hoZoneGpmMap) {
        for (var k in window._hoZoneGpmMap) { if (!gpm[k]) gpm[k] = window._hoZoneGpmMap[k]; }
    }
    return gpm;
}

// --- Data transformers ---
function dnBucketByDay(events) {
    var buckets = {};
    for (var i = 0; i < events.length; i++) {
        var e = events[i];
        var d = (e.timestamp || '').substring(0, 10);
        if (!d) continue;
        if (!buckets[d]) buckets[d] = [];
        buckets[d].push(e);
    }
    return buckets;
}

function dnGetRunEvents(runs) {
    var out = [];
    for (var i = 0; i < runs.length; i++) {
        var r = runs[i];
        if (r.state === 'off' && r.duration_seconds != null && r.duration_seconds > 0) out.push(r);
    }
    return out;
}

function dnTransformWaterUsage(runs, gpmMap, unit) {
    var onRuns = dnGetRunEvents(runs);
    var zoneMap = {};
    var daySet = {};
    for (var i = 0; i < onRuns.length; i++) {
        var r = onRuns[i];
        var eid = r.entity_id || '';
        var name = r.zone_name || eid;
        var day = (r.timestamp || '').substring(0, 10);
        if (!day) continue;
        daySet[day] = true;
        if (!zoneMap[eid]) zoneMap[eid] = { name: name, days: {} };
        if (!zoneMap[eid].days[day]) zoneMap[eid].days[day] = 0;
        var mins = (r.duration_seconds || 0) / 60;
        var val = unit === 'gallons' ? mins * (gpmMap[eid] || 0) : mins;
        zoneMap[eid].days[day] += val;
    }
    var labels = Object.keys(daySet).sort();
    var zones = [];
    var zoneIds = Object.keys(zoneMap);
    for (var z = 0; z < zoneIds.length; z++) {
        var zm = zoneMap[zoneIds[z]];
        var vals = [];
        for (var d = 0; d < labels.length; d++) {
            vals.push(Math.round((zm.days[labels[d]] || 0) * 100) / 100);
        }
        zones.push({ name: zm.name, values: vals });
    }
    return { labels: labels, zones: zones };
}

function dnTransformSavings(runs, gpmMap) {
    var runEvts = dnGetRunEvents(runs);
    var daySet = {};
    for (var i = 0; i < runEvts.length; i++) {
        var r = runEvts[i];
        var day = (r.timestamp || '').substring(0, 10);
        if (!day) continue;
        if (!daySet[day]) daySet[day] = { used: 0, saved: 0, weatherSaved: 0, moistureSaved: 0 };
        var eid = r.entity_id || '';
        var actualMins = (r.duration_seconds || 0) / 60;
        var zoneGpm = gpmMap[eid] || 0;
        daySet[day].used += actualMins * zoneGpm;
        // Calculate savings from weather multiplier
        var wMult = (r.weather && r.weather.watering_multiplier != null) ? r.weather.watering_multiplier : 1.0;
        if (wMult > 0 && wMult < 1.0 && zoneGpm > 0) {
            var origMins = actualMins / wMult;
            var weatherSavedGal = (origMins - actualMins) * zoneGpm;
            daySet[day].weatherSaved += weatherSavedGal;
            daySet[day].saved += weatherSavedGal;
        }
        // Calculate savings from moisture multiplier
        var mMult = (r.moisture && r.moisture.moisture_multiplier != null) ? r.moisture.moisture_multiplier : 1.0;
        if (mMult > 0 && mMult < 1.0 && zoneGpm > 0) {
            var origMinsM = actualMins / mMult;
            var moistSavedGal = (origMinsM - actualMins) * zoneGpm;
            daySet[day].moistureSaved += moistSavedGal;
            daySet[day].saved += moistSavedGal;
        }
    }
    var labels = Object.keys(daySet).sort();
    var used = [], saved = [], cumSaved = [], totalCum = 0;
    var totalWeather = 0, totalMoisture = 0;
    for (var d = 0; d < labels.length; d++) {
        var ds = daySet[labels[d]];
        used.push(Math.round(ds.used * 100) / 100);
        saved.push(Math.round(ds.saved * 100) / 100);
        totalCum += ds.saved;
        cumSaved.push(Math.round(totalCum * 100) / 100);
        totalWeather += ds.weatherSaved;
        totalMoisture += ds.moistureSaved;
    }
    return { labels: labels, used: used, saved: saved, cumulativeSaved: cumSaved,
             totalWeather: Math.round(totalWeather), totalMoisture: Math.round(totalMoisture),
             totalSaved: Math.round(totalCum) };
}

function dnTransformMoisture(runs) {
    var points = [];
    var onRuns = dnGetRunEvents(runs);
    for (var i = 0; i < onRuns.length; i++) {
        var r = onRuns[i];
        var m = r.moisture || {};
        if (m.sensor_readings) {
            var sr = m.sensor_readings;
            points.push({
                ts: r.timestamp,
                shallow: sr.T != null ? sr.T : null,
                mid: sr.M != null ? sr.M : null,
                deep: sr.B != null ? sr.B : null,
                multiplier: m.moisture_multiplier || m.combined_multiplier || null
            });
        }
    }
    points.sort(function(a, b) { return a.ts < b.ts ? -1 : 1; });
    return {
        labels: points.map(function(p) { return p.ts; }),
        shallow: points.map(function(p) { return p.shallow; }),
        mid: points.map(function(p) { return p.mid; }),
        deep: points.map(function(p) { return p.deep; }),
        multiplier: points.map(function(p) { return p.multiplier; })
    };
}

function dnTransformWeather(weatherLog) {
    var points = [];
    for (var i = 0; i < weatherLog.length; i++) {
        var w = weatherLog[i];
        if (w.temperature != null || w.watering_multiplier != null) {
            points.push({
                ts: w.timestamp,
                temp: w.temperature != null ? w.temperature : null,
                humidity: w.humidity != null ? w.humidity : null,
                multiplier: w.watering_multiplier != null ? w.watering_multiplier : null,
                condition: w.condition || ''
            });
        }
    }
    points.sort(function(a, b) { return a.ts < b.ts ? -1 : 1; });
    // Thin out if too many points for chart performance
    if (points.length > 500) {
        var step = Math.ceil(points.length / 500);
        var thinned = [];
        for (var j = 0; j < points.length; j += step) thinned.push(points[j]);
        points = thinned;
    }
    return {
        labels: points.map(function(p) { return p.ts; }),
        temperature: points.map(function(p) { return p.temp; }),
        humidity: points.map(function(p) { return p.humidity; }),
        multiplier: points.map(function(p) { return p.multiplier; })
    };
}

function dnTransformZones(runs, gpmMap) {
    var onRuns = dnGetRunEvents(runs);
    var zones = {};
    for (var i = 0; i < onRuns.length; i++) {
        var r = onRuns[i];
        var eid = r.entity_id || '';
        if (!zones[eid]) zones[eid] = { name: r.zone_name || eid, runtime: 0, gallons: 0, runs: 0, skips: 0 };
        var mins = (r.duration_seconds || 0) / 60;
        zones[eid].runtime += mins;
        zones[eid].gallons += mins * (gpmMap[eid] || 0);
        zones[eid].runs++;
    }
    // Count skips from all runs
    for (var j = 0; j < runs.length; j++) {
        if (runs[j].source === 'moisture_skip' || (runs[j].moisture && runs[j].moisture.skip)) {
            var zeid = runs[j].entity_id || '';
            if (zones[zeid]) zones[zeid].skips++;
        }
    }
    var arr = Object.keys(zones).map(function(k) { return zones[k]; });
    arr.sort(function(a, b) { return b.gallons - a.gallons || b.runtime - a.runtime; });
    return arr;
}

function dnTransformHeatmap(runs) {
    var matrix = [];
    for (var d = 0; d < 7; d++) { matrix[d] = []; for (var h = 0; h < 24; h++) matrix[d][h] = 0; }
    var onRuns = dnGetRunEvents(runs);
    for (var i = 0; i < onRuns.length; i++) {
        var ts = onRuns[i].timestamp;
        if (!ts) continue;
        var dt = new Date(ts);
        var day = dt.getDay();
        var hour = dt.getHours();
        matrix[day][hour] += (onRuns[i].duration_seconds || 0) / 60;
    }
    return matrix;
}

function dnTransformProbeHealth(probes) {
    var arr = [];
    if (!probes) return arr;
    var keys = Object.keys(probes);
    for (var i = 0; i < keys.length; i++) {
        var p = probes[keys[i]];
        var ds = p.device_sensors || {};
        arr.push({
            name: p.display_name || keys[i],
            battery: ds.battery ? ds.battery.value : null,
            wifi: ds.wifi ? ds.wifi.value : null,
            isAwake: p.is_awake || false,
            mappedZones: (p.zone_mappings || []).length
        });
    }
    return arr;
}

// --- Summary cards ---
function dnBuildSummaryCards(data, gpmMap) {
    var runEvts = dnGetRunEvents(data.runs);
    var totalGal = 0, totalSaved = 0, totalMins = 0;
    for (var i = 0; i < runEvts.length; i++) {
        var r = runEvts[i];
        var mins = (r.duration_seconds || 0) / 60;
        var zoneGpm = gpmMap[r.entity_id] || 0;
        totalMins += mins;
        totalGal += mins * zoneGpm;
        // Calculate savings from weather multiplier
        var wMult = (r.weather && r.weather.watering_multiplier != null) ? r.weather.watering_multiplier : 1.0;
        if (wMult > 0 && wMult < 1.0 && zoneGpm > 0) { totalSaved += ((mins / wMult) - mins) * zoneGpm; }
        // Calculate savings from moisture multiplier
        var mMult = (r.moisture && r.moisture.moisture_multiplier != null) ? r.moisture.moisture_multiplier : 1.0;
        if (mMult > 0 && mMult < 1.0 && zoneGpm > 0) { totalSaved += ((mins / mMult) - mins) * zoneGpm; }
    }
    // Avg moisture from probes
    var moistVals = [], probeKeys = Object.keys(data.probes || {});
    for (var j = 0; j < probeKeys.length; j++) {
        var sl = (data.probes[probeKeys[j]].sensors_live || {});
        if (sl.mid && sl.mid.value != null) moistVals.push(sl.mid.value);
    }
    var avgMoist = moistVals.length > 0 ? Math.round(moistVals.reduce(function(a,b){return a+b;},0) / moistVals.length) : null;
    // Cost
    var costPer1000 = data.waterSettings ? (data.waterSettings.cost_per_1000_gal || data.waterSettings.cost_per_1000gal || 0) : 0;
    var costSaved = costPer1000 > 0 ? (totalSaved / 1000 * costPer1000) : 0;
    var savePct = totalGal + totalSaved > 0 ? Math.round(totalSaved / (totalGal + totalSaved) * 100) : 0;

    var html = '<div class="dn-summary-row">';
    html += '<div class="dn-stat-card"><div class="dn-stat-val">' + dnFmtNum(Math.round(totalGal)) + '</div><div class="dn-stat-label">Total Gallons</div><div class="dn-stat-sub">' + Math.round(totalMins) + ' minutes runtime</div></div>';
    html += '<div class="dn-stat-card"><div class="dn-stat-val" style="color:#27ae60;">' + dnFmtNum(Math.round(totalSaved)) + '</div><div class="dn-stat-label">Gallons Saved (' + savePct + '%)</div><div class="dn-stat-sub">' + (costSaved > 0 ? '$' + costSaved.toFixed(2) + ' saved' : 'No cost data') + '</div></div>';
    html += '<div class="dn-stat-card"><div class="dn-stat-val">' + (avgMoist != null ? avgMoist + '%' : '--') + '</div><div class="dn-stat-label">Avg Moisture</div><div class="dn-stat-sub">' + probeKeys.length + ' probe' + (probeKeys.length !== 1 ? 's' : '') + '</div></div>';
    // Zone count
    var zoneSet = {};
    for (var z = 0; z < runEvts.length; z++) { zoneSet[runEvts[z].entity_id] = true; }
    var zoneCount = Object.keys(zoneSet).length;
    html += '<div class="dn-stat-card"><div class="dn-stat-val">' + zoneCount + '</div><div class="dn-stat-label">Active Zones</div><div class="dn-stat-sub">' + runEvts.length + ' run events</div></div>';
    html += '</div>';
    return html;
}

// --- Chart builders ---
function dnBuildWaterUsage(canvasId, data, gpmMap) {
    var td = dnTransformWaterUsage(data.runs, gpmMap, _dnCurrentUnit);
    if (td.labels.length === 0) return null;
    var cfg = dnChartDefaults();
    var ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    var datasets = [];
    for (var i = 0; i < td.zones.length; i++) {
        var ci = i % DN_COLORS.length;
        datasets.push({
            label: td.zones[i].name,
            data: td.zones[i].values,
            borderColor: DN_COLORS[ci].border,
            backgroundColor: DN_COLORS[ci].fill,
            fill: true,
            tension: 0.3,
            pointRadius: td.labels.length > 60 ? 0 : 2,
            pointHitRadius: 8,
            borderWidth: 2
        });
    }
    _dnCharts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: { labels: td.labels, datasets: datasets },
        options: Object.assign({}, cfg, {
            scales: {
                x: Object.assign({}, cfg.scales.x, { stacked: true }),
                y: Object.assign({}, cfg.scales.y, { stacked: true, title: { display: true, text: _dnCurrentUnit === 'gallons' ? 'Gallons' : 'Minutes', color: cfg.scales.y.ticks.color } })
            },
            interaction: { mode: 'index', intersect: false }
        })
    });
    return _dnCharts[canvasId];
}

function dnBuildSavings(canvasId, data, gpmMap) {
    var td = dnTransformSavings(data.runs, gpmMap);
    if (td.labels.length === 0) return null;
    var cfg = dnChartDefaults();
    var ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    _dnCharts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: td.labels,
            datasets: [
                { label: 'Gallons Used', data: td.used, backgroundColor: 'rgba(52,152,219,0.6)', borderRadius: 4, order: 2 },
                { label: 'Gallons Saved', data: td.saved, backgroundColor: 'rgba(46,204,113,0.6)', borderRadius: 4, order: 2 },
                { label: 'Cumulative Savings', data: td.cumulativeSaved, type: 'line', borderColor: 'rgba(46,204,113,0.9)', backgroundColor: 'rgba(46,204,113,0.08)', fill: true, tension: 0.3, yAxisID: 'y1', pointRadius: 0, borderWidth: 2, order: 1 }
            ]
        },
        options: Object.assign({}, cfg, {
            scales: {
                x: cfg.scales.x,
                y: Object.assign({}, cfg.scales.y, { title: { display: true, text: 'Gallons', color: cfg.scales.y.ticks.color } }),
                y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { color: cfg.scales.y.ticks.color, font: { size: 10 } }, title: { display: true, text: 'Cumulative', color: cfg.scales.y.ticks.color }, beginAtZero: true }
            },
            interaction: { mode: 'index', intersect: false }
        })
    });
    return _dnCharts[canvasId];
}

function dnBuildMoisture(canvasId, data) {
    var td = dnTransformMoisture(data.runs);
    if (td.labels.length === 0) return null;
    var cfg = dnChartDefaults();
    var ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    _dnCharts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: td.labels,
            datasets: [
                { label: 'Shallow', data: td.shallow, borderColor: 'rgba(46,204,113,0.85)', backgroundColor: 'rgba(46,204,113,0.08)', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 },
                { label: 'Mid', data: td.mid, borderColor: 'rgba(52,152,219,0.85)', backgroundColor: 'rgba(52,152,219,0.08)', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 },
                { label: 'Deep', data: td.deep, borderColor: 'rgba(155,89,182,0.8)', backgroundColor: 'rgba(155,89,182,0.06)', fill: true, tension: 0.3, pointRadius: 3, borderWidth: 2 },
                { label: 'Multiplier', data: td.multiplier, borderColor: 'rgba(243,156,18,0.8)', borderDash: [5,3], fill: false, tension: 0.3, pointRadius: 0, borderWidth: 2, yAxisID: 'y1' }
            ]
        },
        options: Object.assign({}, cfg, {
            scales: {
                x: cfg.scales.x,
                y: Object.assign({}, cfg.scales.y, { min: 0, max: 100, title: { display: true, text: 'Moisture %', color: cfg.scales.y.ticks.color } }),
                y1: { position: 'right', min: 0, max: 2.5, grid: { drawOnChartArea: false }, ticks: { color: cfg.scales.y.ticks.color, font: { size: 10 } }, title: { display: true, text: 'Multiplier', color: cfg.scales.y.ticks.color } }
            },
            interaction: { mode: 'index', intersect: false }
        })
    });
    return _dnCharts[canvasId];
}

function dnBuildWeather(canvasId, data) {
    var td = dnTransformWeather(data.weather);
    if (td.labels.length === 0) return null;
    var cfg = dnChartDefaults();
    var ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    _dnCharts[canvasId] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: td.labels,
            datasets: [
                { label: 'Temperature', data: td.temperature, borderColor: 'rgba(231,76,60,0.7)', fill: false, tension: 0.3, pointRadius: 0, borderWidth: 1.5, yAxisID: 'yTemp' },
                { label: 'Humidity %', data: td.humidity, borderColor: 'rgba(52,152,219,0.5)', fill: false, tension: 0.3, pointRadius: 0, borderWidth: 1, yAxisID: 'yHumid' },
                { label: 'Multiplier', data: td.multiplier, borderColor: 'rgba(46,204,113,0.9)', backgroundColor: 'rgba(46,204,113,0.08)', fill: true, tension: 0.3, pointRadius: 0, borderWidth: 2.5, yAxisID: 'yMult' }
            ]
        },
        options: Object.assign({}, cfg, {
            scales: {
                x: cfg.scales.x,
                yTemp: { position: 'left', grid: { color: cfg.scales.x.grid.color }, ticks: { color: 'rgba(231,76,60,0.7)', font: { size: 10 } }, title: { display: true, text: 'Temp', color: 'rgba(231,76,60,0.7)' } },
                yHumid: { display: false },
                yMult: { position: 'right', min: 0, max: 2, grid: { drawOnChartArea: false }, ticks: { color: 'rgba(46,204,113,0.8)', font: { size: 10 } }, title: { display: true, text: 'Multiplier', color: 'rgba(46,204,113,0.8)' } }
            },
            interaction: { mode: 'index', intersect: false }
        })
    });
    return _dnCharts[canvasId];
}

function dnBuildZoneBar(canvasId, data, gpmMap) {
    var zones = dnTransformZones(data.runs, gpmMap);
    if (zones.length === 0) return null;
    var cfg = dnChartDefaults();
    var ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    _dnCharts[canvasId] = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: zones.map(function(z) { return z.name; }),
            datasets: [
                { label: 'Gallons Used', data: zones.map(function(z) { return Math.round(z.gallons); }), backgroundColor: 'rgba(52,152,219,0.6)', borderRadius: 4 },
                { label: 'Runtime (min)', data: zones.map(function(z) { return Math.round(z.runtime); }), backgroundColor: 'rgba(46,204,113,0.6)', borderRadius: 4 }
            ]
        },
        options: Object.assign({}, cfg, {
            indexAxis: 'y',
            scales: {
                x: Object.assign({}, cfg.scales.x, { title: { display: true, text: 'Value', color: cfg.scales.x.ticks.color } }),
                y: Object.assign({}, cfg.scales.y, { beginAtZero: undefined })
            }
        })
    });
    return _dnCharts[canvasId];
}

function dnBuildZoneRadar(canvasId, data, gpmMap) {
    var zones = dnTransformZones(data.runs, gpmMap);
    if (zones.length === 0) return null;
    var cfg = dnChartDefaults();
    var ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    // Normalize all metrics 0-100
    var maxRuntime = Math.max.apply(null, zones.map(function(z){return z.runtime;})) || 1;
    var maxGallons = Math.max.apply(null, zones.map(function(z){return z.gallons;})) || 1;
    var maxRuns = Math.max.apply(null, zones.map(function(z){return z.runs;})) || 1;
    var isDark = document.body.classList.contains('dark-mode');
    var datasets = [];
    for (var i = 0; i < Math.min(zones.length, 8); i++) {
        var z = zones[i];
        var skipRate = z.runs > 0 ? (z.skips / z.runs * 100) : 0;
        var efficiency = z.gallons > 0 && z.runtime > 0 ? (z.gallons / z.runtime) : 0;
        var maxEff = maxGallons / maxRuntime || 1;
        datasets.push({
            label: z.name,
            data: [
                Math.round(z.runtime / maxRuntime * 100),
                Math.round(z.gallons / maxGallons * 100),
                Math.round(efficiency / maxEff * 100),
                Math.round(skipRate),
                Math.round(z.runs / maxRuns * 100)
            ],
            borderColor: DN_COLORS[i % DN_COLORS.length].border,
            backgroundColor: DN_COLORS[i % DN_COLORS.length].fill,
            pointBackgroundColor: DN_COLORS[i % DN_COLORS.length].border,
            borderWidth: 2
        });
    }
    _dnCharts[canvasId] = new Chart(ctx, {
        type: 'radar',
        data: { labels: ['Runtime', 'Gallons', 'Efficiency', 'Skip Rate', 'Frequency'], datasets: datasets },
        options: Object.assign({}, cfg, {
            scales: {
                r: {
                    min: 0, max: 100,
                    ticks: { display: false, stepSize: 25 },
                    grid: { color: isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)' },
                    pointLabels: { color: isDark ? '#8a9bb0' : '#7f8c8d', font: { size: 11 } },
                    angleLines: { color: isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)' }
                }
            }
        })
    });
    return _dnCharts[canvasId];
}

function dnBuildHeatmap(containerId, data) {
    var matrix = dnTransformHeatmap(data.runs);
    var maxVal = 0;
    for (var d = 0; d < 7; d++) for (var h = 0; h < 24; h++) maxVal = Math.max(maxVal, matrix[d][h]);
    var days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    var html = '<div class="dn-heatmap">';
    for (var d = 0; d < 7; d++) {
        html += '<div class="dn-heatmap-row"><span class="dn-heatmap-label">' + days[d] + '</span>';
        for (var h = 0; h < 24; h++) {
            var v = matrix[d][h];
            var intensity = maxVal > 0 ? v / maxVal : 0;
            var bg = intensity > 0 ? 'rgba(46,204,113,' + (0.15 + intensity * 0.7).toFixed(2) + ')' : 'rgba(128,128,128,0.06)';
            html += '<div class="dn-heatmap-cell" style="background:' + bg + ';" title="' + days[d] + ' ' + h + ':00 \\u2014 ' + Math.round(v) + ' min"></div>';
        }
        html += '</div>';
    }
    // Hour labels
    html += '<div class="dn-heatmap-hours">';
    for (var h = 0; h < 24; h++) {
        html += '<span>' + (h === 0 ? '12a' : h < 12 ? h + 'a' : h === 12 ? '12p' : (h-12) + 'p') + '</span>';
    }
    html += '</div></div>';
    var el = document.getElementById(containerId);
    if (el) el.innerHTML = html;
}

function dnBuildProbeHealth(containerId, data) {
    var probes = dnTransformProbeHealth(data.probes);
    if (probes.length === 0) { document.getElementById(containerId).innerHTML = '<div style="text-align:center;padding:20px;color:var(--text-muted);font-size:12px;">No probes configured</div>'; return; }
    var html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px;">';
    for (var i = 0; i < probes.length; i++) {
        var p = probes[i];
        html += '<div class="dn-stat-card" style="text-align:left;">';
        html += '<div style="font-weight:600;font-size:13px;margin-bottom:8px;">' + esc(p.name) + '</div>';
        html += '<div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">Battery: <span style="font-weight:600;color:' + (p.battery != null && p.battery < 20 ? 'var(--color-danger)' : 'var(--text-primary)') + ';">' + (p.battery != null ? p.battery + '%' : '--') + '</span></div>';
        html += '<div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">WiFi: <span style="font-weight:600;">' + (p.wifi != null ? p.wifi + ' dBm' : '--') + '</span></div>';
        html += '<div style="font-size:12px;color:var(--text-muted);">Status: <span style="font-weight:600;color:' + (p.isAwake ? '#27ae60' : 'var(--text-hint)') + ';">' + (p.isAwake ? 'Awake' : 'Sleeping') + '</span></div>';
        html += '<div style="font-size:11px;color:var(--text-hint);margin-top:4px;">' + p.mappedZones + ' zone' + (p.mappedZones !== 1 ? 's' : '') + ' mapped</div>';
        html += '</div>';
    }
    html += '</div>';
    document.getElementById(containerId).innerHTML = html;
}

// --- Master render ---
function dnRenderAllCharts(data) {
    var grid = document.getElementById('dnGrid');
    if (!grid) return;
    var gpmMap = dnBuildGpmMap(data);
    var html = '';
    // 1. Summary cards
    html += '<div class="dn-full">' + dnBuildSummaryCards(data, gpmMap) + '</div>';
    // 2. Water Usage
    html += '<div class="dn-panel dn-wide"><div class="dn-panel-title">Water Usage Over Time</div><div class="dn-chart-wrap"><canvas id="dnChartUsage"></canvas></div></div>';
    // 3. Water Savings
    html += '<div class="dn-panel"><div class="dn-panel-title">Water Savings Analysis</div><div class="dn-chart-wrap"><canvas id="dnChartSavings"></canvas></div>';
    // Savings pills
    var sv = dnTransformSavings(data.runs, gpmMap);
    html += '<div style="margin-top:8px;text-align:center;">';
    html += '<span class="dn-pill" style="background:rgba(52,152,219,0.15);color:rgba(52,152,219,0.9);">Weather: ' + dnFmtNum(sv.totalWeather) + ' gal</span>';
    html += '<span class="dn-pill" style="background:rgba(46,204,113,0.15);color:rgba(46,204,113,0.9);">Moisture: ' + dnFmtNum(sv.totalMoisture) + ' gal</span>';
    html += '<span class="dn-pill" style="background:rgba(155,89,182,0.15);color:rgba(155,89,182,0.9);">Total: ' + dnFmtNum(sv.totalSaved) + ' gal</span>';
    html += '</div></div>';
    // 4. Moisture Trends
    html += '<div class="dn-panel"><div class="dn-panel-title">Moisture Trends</div><div class="dn-chart-wrap"><canvas id="dnChartMoisture"></canvas></div></div>';
    // 5. Weather Impact
    html += '<div class="dn-panel"><div class="dn-panel-title">Weather Impact</div><div class="dn-chart-wrap"><canvas id="dnChartWeather"></canvas></div></div>';
    // 6. Zone Performance — with bar/radar toggle
    html += '<div class="dn-panel"><div class="dn-panel-title">Zone Performance <div class="dn-tab-group"><button class="dn-tab-btn active" onclick="dnZoneView(&quot;bar&quot;,this)">Bar</button><button class="dn-tab-btn" onclick="dnZoneView(&quot;radar&quot;,this)">Radar</button></div></div><div class="dn-chart-wrap" id="dnZoneWrap"><canvas id="dnChartZoneBar"></canvas></div></div>';
    // 7. Probe Health
    html += '<div class="dn-panel"><div class="dn-panel-title">Probe Health</div><div id="dnProbeHealth"></div></div>';
    // 8. Heatmap
    html += '<div class="dn-panel dn-full"><div class="dn-panel-title">Watering Activity Heatmap</div><div id="dnHeatmap"></div></div>';

    grid.innerHTML = html;

    // Build charts after DOM is ready
    setTimeout(function() {
        dnBuildWaterUsage('dnChartUsage', data, gpmMap);
        dnBuildSavings('dnChartSavings', data, gpmMap);
        dnBuildMoisture('dnChartMoisture', data);
        dnBuildWeather('dnChartWeather', data);
        dnBuildZoneBar('dnChartZoneBar', data, gpmMap);
        dnBuildHeatmap('dnHeatmap', data);
        dnBuildProbeHealth('dnProbeHealth', data);
    }, 50);
}

// Zone view toggle
function dnZoneView(mode, btn) {
    var wrap = document.getElementById('dnZoneWrap');
    if (!wrap) return;
    // Toggle active tab
    var tabs = btn.parentElement.querySelectorAll('.dn-tab-btn');
    for (var i = 0; i < tabs.length; i++) tabs[i].classList.remove('active');
    btn.classList.add('active');
    // Destroy existing zone chart
    if (_dnCharts['dnChartZoneBar']) { _dnCharts['dnChartZoneBar'].destroy(); delete _dnCharts['dnChartZoneBar']; }
    if (_dnCharts['dnChartZoneRadar']) { _dnCharts['dnChartZoneRadar'].destroy(); delete _dnCharts['dnChartZoneRadar']; }
    var canvasId = mode === 'radar' ? 'dnChartZoneRadar' : 'dnChartZoneBar';
    wrap.innerHTML = '<canvas id="' + canvasId + '"></canvas>';
    var gpmMap = dnBuildGpmMap(_dnRawData);
    if (mode === 'radar') {
        dnBuildZoneRadar(canvasId, _dnRawData, gpmMap);
    } else {
        dnBuildZoneBar(canvasId, _dnRawData, gpmMap);
    }
}

// Format number with commas
function dnFmtNum(n) {
    if (n == null) return '--';
    return n.toString().replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',');
}

// CSV export
function dnExportCSV() {
    if (!_dnRawData || !_dnRawData.runs) { showToast('No data to export','warning'); return; }
    var onRuns = dnGetRunEvents(_dnRawData.runs);
    var gpmMap = dnBuildGpmMap(_dnRawData);
    var csv = 'Date,Zone,Duration_Min,Gallons,Saved_Gal,Weather_Mult,Moisture_Mult,Source\\n';
    for (var i = 0; i < onRuns.length; i++) {
        var r = onRuns[i];
        var mins = Math.round((r.duration_seconds || 0) / 60 * 100) / 100;
        var gal = Math.round(mins * (gpmMap[r.entity_id] || 0) * 100) / 100;
        var wMult = (r.weather || {}).watering_multiplier || '';
        var mMult = (r.moisture || {}).moisture_multiplier || '';
        csv += (r.timestamp || '') + ',' + (r.zone_name || '').replace(/,/g, ' ') + ',' + mins + ',' + gal + ',' + (r.water_saved_gallons || 0) + ',' + wMult + ',' + mMult + ',' + (r.source || '') + '\\n';
    }
    var blob = new Blob([csv], {type:'text/csv'});
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url; a.download = 'irrigation_data_export.csv';
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('CSV exported','success');
}

</script>
</body>
</html>
"""
