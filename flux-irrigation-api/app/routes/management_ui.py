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
<script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js" crossorigin="" async></script>
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
.customer-card.has-severe-issue { border-left-color: #e74c3c !important; }
.customer-card.has-annoyance-issue { border-left-color: #f39c12 !important; }
.customer-card.has-clarification-issue { border-left-color: #3498db !important; }
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
    .customer-card-body { padding: 10px; }
    .customer-card-header { margin-bottom: 4px; }
    .customer-name { font-size: 14px; }
    .customer-address { margin-bottom: 2px; font-size: 11px; }
    .customer-stats { margin-top: 4px; gap: 10px; font-size: 12px; }
    .customer-actions { flex-wrap: wrap; gap: 4px; margin-top: 6px; padding-top: 6px; }
    .customer-grid { gap: 10px; }
    .zone-settings-table { table-layout: fixed; }
    .zone-settings-table th, .zone-settings-table td { padding: 6px 4px; font-size: 12px; }
    .zone-settings-table td[style*="white-space"] { white-space: normal !important; }
    .zone-settings-table input[type="number"] { width: 50px !important; padding: 3px 2px !important; font-size: 11px !important; }
}
</style>
</head>
<body>
<script>(function(){if(localStorage.getItem('flux_dark_mode_management')==='true')document.body.classList.add('dark-mode');})()</script>

<div class="header">
    <div class="header-left" style="display:flex;align-items:center;gap:14px;">
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAARYAAABaCAYAAAB9oHnsAAAACXBIWXMAAC4jAAAuIwF4pT92AAAQnklEQVR4nO2d0XHjOBKGf1xdqaQnOwNrI7AuAnMjsDYCcyIYTQSjiWA8EZiOYDURDB3ByhGcnIH9JJVe+h7QvKEpgARIAgRlfFUslymKhEjgJ9BodAsiQiQSifTJv4cuwEdgMp1dAkgBXALIjof9btACKeAyrvjf/HjY5wMWJ6JACLEAsOR/dwA2RPQ6XIn0CFWPhStZBuDWc3l+AlgfD/tt3UGT6SwFsMbvhrqqO35oJtPZFsA1//sGIGn6jT7h570FcFXa/dfxsN+0PN8cUkhz3rULUUzHghBC1x7fAKyIKPNdpib+pdmfwb+ogK9ZW5kn09kCwANkI7gA8HkynQUrLJPpLMFvUQFkmZfqowdjgfeiAkhhaMscwFcAv3jb8nMLnsl0lk6mMypt+ZDlYVHJoW6PFwAehBCh1SetsAwhKgXVCl7l0nBfpBt93tMLAHno4jKZzpaQL62QuMf7F5OKjIdJwaATliF5GboAEScELS5crmzocpQRQmQA7gwOvQCQhyQuoQnLM8IbJkTs2UI+yyoXADK26QQDi0oOWb4qgxhHLUSl4AKy5xLEvbWZFXoEsDoe9kFaoSPhcDzsX9nAnuO0sV5D9lySEOpSg6g8o5utqRUNovIGvc3lGrLnkgw9W2TaY3k7HvZpCBUhMg541iuBbAhVCnEZ9O1qICrexc9AVBIiWgJ40hxzjQCGdKbCEszUaGQ8hCwuIxaVoi0uoR5uAsAtn2swQrOxRM6MEMUlUFFZo96mkpZEBTzUSaC+rwBwJ4QYzA0jCkvEOQbikvkqC4tYjrBEJYX0+9HxiYhO/LsMxOU7n9s7UVgiXmBxSTUf306ms8x1GRpE5Q2AdzsiN/w635lPdZ613ItJar7/IISo+9wJUVgi3uAlAp80H9+5FJeSqKiczQZZZtFVVApYXHT3FQA2vn1corBEvHI87DN4FpdzFpUCPvaL5uPCgc6bLSsKS8Q7PsXlI4hKARHdQ/qbqfAqLlFYIoNgIC7rrtcYqah86bJamYhS6MXlGr9XnDslCktkMFhcvmk+/sreu60IVFQWkIsKdTxyr6MrK+h9XK59+LhEYYkMyvGwX0P/hn3oIC51q4KXA4lKDvWMFCBFJe3jWqVpaJ243Akh+hAwLVFYIoNzPOxT9CgubKPROZt98h0dz6eoFLC4LKH3cfns0sclCkskCPoSFwNRyWzL1oUhRKWAiHaod6B7cCUuUVgiwWAgLrUhNaKonMI+LnXXuHfh4xKFJRIULC4/NR9nukBRUVT08HIA3QyckyBRUVgiIZJCHyjqJApdgKJSt3QAAJ59iUoBT2HrZuAuIL1ze/NxicISCQ5er5NALy7/lANeY2Sigvq1Pc4gojX0Q80r9OhAF4UlEiQN4mLCjwFFRTfN/QwZU2WwgGncU3IeJMo0NOXCcRqEzHcliIQPh7hMUN9YVTz6zjU1BlEpsYS+rLdCiKzrUM1UWC4A3HS5UAM3k+lsG1ISr0gYlMSlmlBNxyMbgL0xMlEBEb1yKAXdPb0TQux46NSKkIZCMTp/RAkPi3aGh2fuSnLK2ESlwMCB7msXH5eQhKVVOs9IZCgMROUFAYpKgcsgUSEIywuk9T4OgyJjo2490huAZaiiUuAqSJSpjeXpeNgntiePRPqAbSymNr57HzmLLCPqBw0RZUIIQB3O4f8OdLxEwIgQeiyRiBZ2hrMZJjsPzn1OolLADnR1QaKsHOiisESCpSFNRx3OgnOfo6gU9BkkKgpLJEgaROUF0smr2FT0Hj/3nEWlgMWlc5CoKCyR4DBIKLY4HvZJscFD/NyPIColEtQHicqaThCFJRIUbbIUug7ObZulcOwY+LjcNfm4RGFxj2p2wmuOFwMSxT7vDaVL6lMDcWkVipGnWq2zFI6drkGiorA4RuOfM/ddjgZU1n6v/hcc/HoDfZbCxilkFhddbp3PLePn1nmEt0rTMRa4F1b3+x90Pi6mfiyRbrzg/ZqM68l0duk7nWcNiWKftx5LKaK+at2KkagUHA/7e+75qIYuD5PpDJYLXnea/UaiMkR6Uwc8Qj8U3EDxoozC4gfVYq8lPK9rUTGZzuZQe496ERYXaTqOh306mc6AHsSFncdWlfI1iooQoni+tlPlY+NKCDGvOs/FoZAfVGPw1HchNKSKfc/Hw37n+sIuc//0GfmfiBYA/oKMwPaHoaj8jfMXlYKToXQUFj+ohOWGXdUHgxu2Km5J5unaORwmFOtZXDZEtDZ0a3easycw3lQzYlFYPMD2AVUFX3suSpUV1G/VzOVFfWYpbBCXwh7TG2zMNIkbcy6sVTujsPhjrdh3M5nOvEY6K+AGpbr2owejcg6/qU91KUeVwbk70ltA6sB5g8wzreydReOtJ46H/W4ynams698n01nuM2wE9xgynPZW3qAWmz6vnUEfaiB1cR8aQlwW4uIjl/MT5DAplNnAtrw2OQRGYfHLCnI2qNqgfVXssr+IqnGvXfZWDNJ0OHM0C0BcnogocXTu4IhDIY9wo00VH7nokp9Qsm2oYps8HQ97Z0bHEHL/GKQVcfkMPpJBNwqLb/it/EPxUZEvx8lQhBvMFnrbhrOYwyGISoGBuGxYgPtm7MMfK6KwDACnptDNVHyfTGd5X1PRk+nscjKdrQH8gx48W1tcP0MgolLAv1W3yO4KsufyUYywTjgXYUmGLoAtDdOgNwB+scC06klMprM5C8oO+kV0rmZhijJkCExUCtgBMIFaXK7xgcRFCLEUQrwKIUgIsesjj/O5GG9vJtNZOrakZ+x6/grgs+aQG8jf9gJpG9kA2Oq8YrmXs4B8GzfFiHUtKmvoReWL7bPi35Z0KpSaHMCtYn8hLs7j5w6JEGIO6SVccAXN+h+r8xLRyU7Oh1smmGDaXMF+aT5+gXn+mb54hZxNad1AuVeSwd4F/BnSb8LWIesJwNLh8CeFOjAz0CKhWEPPxzU/j4e9ca+x5M5f5T8hxmzhRZKq9vQnEeVtz3suPZaCKwzj9ThHhxgrx8N+w8bVe6jfnjps0o4C7KfioWeXava3ERXdSmVf2A6HlPUgRFFxybnYWIbGtoGfcDzsd/xm/BP6OK5teYNcQDcfcLjYNvXph7BznBs6YalW7JDGmCGVpeClrxMdD/uch51/QE5Ldzn3T8ioavPjYe/U+a2B1vmUj4d9Dn38VR+EWN+CRzcUWkF2y28gRSb1VaAmjof9djKdfYIsXwjL0l/gwAeEDbQrACseDiSQ3ew5b9UhX/EyyCH9VfIBhaRwBptD2p+yjudLIOug795LzsIWsURpvI1EIu3gwNsn0/tEJPyXphlXxttoY4lEIr0ThSUSifROa2Fhx5rIByM+94gJRsIihLgUQqyEEFt2+yUA/y25AGem0ciFEElxDoNtJ4TIhRD3Jgmp+VjTc+u2pHLOdeXzzOR3lr7/7vw231Wcq1qW3PB7J/fc4poJP9/XynMnvt+pxbmqz8f4u5XzGN+HHuqD9twRPY3Cwg1tB+A71P4aV5AOTL9MBcCCK8iZqc8AdlyhhvZruDuTlA618MtkA2nYu4N6Bu4GMrdM2/Ul65bFS1t+L+KJWmHhN8ovmE/rfgaQO2r8F5DWdlfntyEb+PpO4fubw9wL+AryuaSWl7qyFWl2mf9IMWVHiVZY+AHq1nvUcQ23De8a6qj3PrniacVzJYe9N/EFgPsWPRfb+DODxAiO2KF0kOM3Vqb46I33byGHRwmkc1i1Et4KIVKL9JN/1ny2hOz6lntNN0KIxGCe/RH2Ime6puOrECIzTAcxGlgwVaLyBF5dDen4luB0Dc8FpHNcYnHJW6FIeKUp2xzNq7ab+AK7ZGzR87YNRHSyQb4VqLJtASw0x2eK43eaY5PqsarjKt9ZQD7g8vc2iuPyyjHrpnMbXHut+G3Flht83+q3Wpal8fq291xxnwnAyuK5EICl5vjq8ym2e8PfcW/7HBTHJl3rRJv64vKaHct7Ujf6uE+6oZDKRX1JmhWaRJTidH3RVUuDnur8W5zGDE36OHdHbnjIeBbwb6na036QJsUD6ZOG296T1KBslybHRcJAJyzV7uYjNXdV14p9fQYmziv/h7BOCACyAIzJfaF6XrVBoEkOR6sLJeeW170wMPyqRC8SKKYOco3GUq5g1VWoc8vy1BFKPIvqb7zA8BkNXfFk8EIBTsWnzQulySgbjbYjwlRYTBu1S0OX09QYFmwgwxGU+dzXsG9gksr/ueH3qvWjTc/iWjf1zPs7x7zxhKoeDBn2YRBOhEXVQAzfWq6pvrF6i4HSghVOgzBnA5Tj3Egt94eIalj84WaWVNPNXewFTm4gj7+rzlomviyJhb9JZiqgRLTj834v7b4WQqx0hk5HzA1/39xxOdryhPf2vDshxLr8HNh+VZ3W/gm7EJ5lUlOnPCJat7zGmNhp9neyG/Yd83aLFg+8oXGo/GQAs8xyNzD3e8hhEYibiO5Z8MplWwshNh57eFfQp/YYAzlOg1aleG+zqvZUn9CynjE28XPXjUeMHH5Jqj5aoIMjaijBtG0bx7eAhmflIDmFg9jZTEF7YI33Ht4rvG/QaeX4DOH2wCLMGOOxPIbSReWZsGq61NuPsEixRzZ4b6/6/9Qz/y33Zl7I3Js7MiB991jmPZ+vzBukJ62NDeMJ5jMbO9sCMWucLjnIhBALInJttHuBmdF4jmFTaGgholcORVFO2raC/F1p5fCsh0s+wn/uqQ9HKMKiS3ex421LRG3Ge7nr3g03jBXed+evcNqld8HO5PdxDypIYWHu8V5Yrrm3UrWPZT1cK6MOsVwjZpwICxHlVWOO6SKxthBR4urcPiCiTNEQvtoGhfqosAGxOkNUXVlv4v0dCQRTG8vc8LhzcW1vQ6rYl3kuQ1eqjm6J4ffmPVy7aYib9XCNiCdMhSVtOoAd66rTwjvL8owWfpt+q+zuusTfN1Wb0MJwHVRa+d86kyMPdXVOj88jH77Mhy6ADlce46aZEO8MKphqLcfOukTj5h7DegR3ReWaX7tGh+03VQFta7TW9Vp8Oh264KptfF8PrDX7d11OqjPebnBaWTZCiKVqpoNvWtU4+Dbyt4w1bMhNoU4ANQZyyNm38gzXSgihNJ5z4CVVo2/rWJXhvTczIOtR1vJ8Q5BD3VN94PuVeyxLHXPInqauV513OblOWDJIJXsXtQ3AVghxj99eqgkXTuUFue5SsLHCxu8uLueDwcK4wfuXxAWAv4UQPyCfew7plZlA9maqCw5b+5rw9R8r1291rgHJoHf4/FrzWUiYrmrXUxNZShVFznTb2kSs6jEaVt6hzMrIWTiNCLY2KMcc6shqnX6roiy54feM7zmkAV5Z9jb3r+H5nNxLvn5S2i673Ice6oPRPa5cM+vhukNu2mdoummNtyQd0R51n9fwjDCiuw0Gq/164GK0guRQN8Hp6m0TPlHH4S8RvRJRXtrGuDJ4hfGGSvjW9RkCDbNCJENOfoJ5JXuCVLsxVoZeYWEeZeUiGXJyAfPyvwH4i8ZlC3FGSZzH9vy/UE8OpY3TzVxZFpC9F53APEO+raKovGe0Uc+IaEdEC8gXi66BvECulZpTO8/os4V7XsX9C3mm8A2ybf9BPYb8EDwmNP+CnPcuTz1vo5icP+xuUPZ52FH0hDWGZ4Tmw5bihFfSBMjvirWwRCKRSBP/A3Jkqd9jS9KSAAAAAElFTkSuQmCC" alt="Flux Open Home" style="height:44px;filter:brightness(0) invert(1);">
        <h1>Irrigation</h1>
    </div>
    <div class="header-actions">
        <span class="mode-badge">Management Mode</span>
        <button class="btn btn-secondary btn-sm" onclick="switchToHomeowner()">Homeowner</button>
        <button class="dark-toggle" onclick="showAlertsPanel()" title="Customer Issues" id="alertBadgeBtn" style="position:relative;display:none;">&#9888;&#65039;<span id="alertBadgeCount" style="position:absolute;top:-4px;right:-4px;background:#e74c3c;color:white;font-size:10px;font-weight:700;border-radius:50%;min-width:16px;height:16px;line-height:16px;text-align:center;padding:0 4px;"></span></button>
        <button class="dark-toggle" onclick="showNotifPrefs()" title="Notification Settings">&#9881;&#65039;</button>
        <button class="dark-toggle" id="darkModeBtn" onclick="toggleDarkMode()" title="Toggle dark mode">🌙</button>
        <button class="dark-toggle" onclick="showHelp()" title="Help">&#10067;</button>
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
                        <div style="display:flex;align-items:center;gap:8px;margin-top:6px;">
                            <p class="hint" style="margin:0;">The homeowner generates this key from their Flux Open Home Irrigation Control add-on.</p>
                            <button class="btn btn-secondary btn-sm" onclick="openQRScanner()" style="white-space:nowrap;font-size:12px;">&#128247; Scan QR Code</button>
                        </div>
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
                        <select id="filterIssues" onchange="filterCustomers()">
                            <option value="">All Issues</option>
                            <option value="has_issues">Has Issues</option>
                            <option value="severe">Severe Issues</option>
                            <option value="annoyance">Annoyances</option>
                            <option value="clarification">Clarifications</option>
                            <option value="no_issues">No Issues</option>
                        </select>
                        <select id="sortBy" onchange="filterCustomers()">
                            <option value="name">Sort: Name</option>
                            <option value="city">Sort: City</option>
                            <option value="state">Sort: State</option>
                            <option value="zones">Sort: Zones</option>
                            <option value="status">Sort: Status</option>
                            <option value="recent">Sort: Last Seen</option>
                            <option value="issues">Sort: Issues</option>
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
                <div id="detailAddress" class="customer-address" style="font-size:14px;margin-top:4px;cursor:pointer;color:var(--color-link);text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;" onclick="openAddressInMaps(this.textContent)" title="Open in Maps"></div>
                <div id="detailContact" style="font-size:14px;color:var(--text-secondary-alt);margin-top:2px;display:none;">&#128100; <span id="detailContactName"></span></div>
                <div id="detailPhone" style="font-size:13px;color:var(--text-muted);margin-top:2px;display:none;">&#128222; <a id="detailPhoneLink" href="" style="color:var(--color-link);text-decoration:none;"></a></div>
                <div id="mgmtTimezone" style="font-size:12px;color:var(--text-muted);margin-top:2px;"></div>
            </div>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-secondary btn-sm" onclick="mgmtShowChangelog()" title="Change Log">&#128203; Log</button>
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

        <!-- Issues Card -->
        <div class="card" id="detailIssuesCard" style="display:none;">
            <div class="card-header">
                <h2>&#9888;&#65039; Issues <span id="detailIssuesBadge" style="font-size:12px;padding:2px 8px;border-radius:10px;background:#e74c3c;color:white;margin-left:6px;display:none;"></span></h2>
            </div>
            <div class="card-body" id="detailIssuesBody">
                <div class="loading">Loading issues...</div>
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

        <!-- Rain Sensor Card -->
        <div class="card" id="detailRainSensorCard" style="display:none;">
            <div class="card-header">
                <h2>&#127783;&#65039; Rain Sensor</h2>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span id="detailRainStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-tile);color:var(--text-muted);">&#8212;</span>
                </div>
            </div>
            <div class="card-body" id="detailRainSensorCardBody">
                <div class="loading">Loading rain sensor...</div>
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

        <!-- Moisture Probes Card -->
        <div class="card" id="detailMoistureCard" style="display:none;">
            <div class="card-header">
                <h2 style="display:flex;align-items:center;gap:8px;"><svg xmlns="http://www.w3.org/2000/svg" viewBox="155 170 745 295" style="height:28px;width:auto;"><path fill="var(--text-primary)" fill-rule="evenodd" d="M322.416931,281.625397 C323.073517,288.667053 324.062378,295.290680 324.095001,301.918976 C324.240021,331.407532 324.573761,360.907135 323.953278,390.384125 C323.315430,420.685608 305.951965,442.817230 276.750000,451.004150 C252.045670,457.930115 227.631088,457.462616 204.859512,444.061829 C193.733704,437.514404 185.529037,427.904022 179.913101,416.206268 C179.426056,415.191742 179.182327,414.060425 178.732849,412.703430 C192.772842,404.558502 206.657608,396.503632 221.095810,388.127686 C222.548920,398.588440 227.417007,406.291168 236.306213,411.228241 C242.295563,414.554749 248.872574,415.283630 255.195541,413.607391 C269.094299,409.922882 279.602142,400.331543 276.985321,375.408997 C268.292480,376.997406 259.625824,379.362396 250.827682,380.053528 C212.511551,383.063599 177.112976,355.681854 170.128632,318.134705 C162.288498,275.986908 187.834488,236.765533 229.805115,227.777832 C248.650925,223.742157 267.514679,224.860764 285.481567,232.988800 C306.417999,242.460220 318.099121,258.975830 322.416931,281.625397 M216.907806,286.065979 C225.295822,272.331604 237.176926,265.403442 252.929047,267.162231 C267.323669,268.769440 277.405518,277.037170 282.681366,290.504517 C288.739105,305.967712 282.622986,322.699615 267.827820,332.537079 C254.597519,341.334045 236.860046,339.821564 225.031052,328.887756 C212.268768,317.091309 209.342514,302.099945 216.907806,286.065979z"/><path fill="var(--text-primary)" fill-rule="evenodd" d="M440.778076,230.141632 C466.800079,239.483002 484.434601,256.637787 491.839233,283.105133 C500.007050,312.300537 489.084961,342.278625 464.074921,361.493744 C431.640076,386.413300 382.445770,383.545990 353.656403,355.057953 C318.682434,320.450043 324.759583,264.850739 366.581024,238.762604 C389.708984,224.335434 414.506042,222.091354 440.778076,230.141632 M419.079773,266.764740 C437.440765,270.748535 450.546936,286.287720 449.715515,302.670624 C448.781708,321.070160 434.135437,336.279297 415.803497,337.885803 C397.935547,339.451660 380.905334,327.358856 376.509705,309.984161 C370.390747,285.797394 393.025116,262.545013 419.079773,266.764740z"/><path fill="var(--text-primary)" fill-rule="evenodd" d="M505.651459,275.706696 C519.676758,244.101715 544.491516,227.960754 577.827881,226.121109 C611.160156,224.281693 638.083069,237.473114 655.040100,266.968140 C676.296448,303.941376 659.723389,352.082367 620.168030,369.955170 C596.583435,380.611755 572.628662,381.200958 548.535156,371.444641 C547.794678,371.144745 546.983826,371.018707 545.645447,370.662506 C545.645447,390.059296 545.645447,409.111145 545.645447,428.497070 C530.607544,428.497070 516.074341,428.497070 500.996918,428.497070 C500.996918,426.395355 500.996918,424.628113 500.996918,422.860901 C500.996948,382.885895 500.731262,342.907776 501.200592,302.938263 C501.306030,293.961548 503.980682,285.014954 505.651459,275.706696 M598.115479,334.281433 C575.892517,344.478851 553.161804,330.843811 547.077026,312.404572 C542.453613,298.393616 547.708435,283.178833 560.344666,273.573029 C572.626587,264.236572 589.550232,263.566986 602.341309,271.911499 C626.866516,287.910980 624.857971,320.051117 598.115479,334.281433z"/><path fill="var(--text-primary)" d="M670.825439,182.155045 C670.825439,180.187927 670.825439,178.699997 670.825439,176.849915 C685.635620,176.849915 700.198181,176.849915 715.259155,176.849915 C715.259155,197.175491 715.259155,217.587784 715.259155,238.510025 C716.406799,238.089737 717.045288,238.015717 717.473022,237.676285 C735.466553,223.398956 755.376953,222.532013 775.856384,230.443253 C790.949036,236.273605 798.483093,249.035553 801.756714,264.225281 C803.287109,271.326416 804.004150,278.725677 804.067200,285.998688 C804.319702,315.143738 804.171570,344.292236 804.171570,373.721710 C789.407043,373.721710 774.836182,373.721710 759.827942,373.721710 C759.827942,371.711731 759.835571,369.768616 759.826843,367.825562 C759.706604,341.165588 760.090210,314.490112 759.275696,287.851318 C758.772949,271.407867 746.863953,263.163330 731.353210,266.883484 C722.925842,268.904694 717.127258,275.714691 716.057434,285.099060 C715.681213,288.399445 715.542114,291.742798 715.536499,295.066956 C715.495117,319.566559 715.514954,344.066254 715.515503,368.565918 C715.515503,370.204803 715.515503,371.843689 715.515503,373.824829 C700.566040,373.824829 685.988281,373.824829 670.825439,373.824829 C670.825439,310.162415 670.825439,246.398331 670.825439,182.155045z"/><path fill="var(--text-primary)" d="M855.839355,323.000092 C855.839355,340.127289 855.839355,356.754486 855.839355,373.695129 C840.823486,373.695129 826.114746,373.695129 810.997253,373.695129 C810.997253,371.683563 810.994263,369.731567 810.997681,367.779572 C811.046997,339.965515 810.786316,312.145172 811.345886,284.341370 C811.503601,276.506470 813.144958,268.402985 815.701904,260.971832 C822.865173,240.153290 839.259949,230.438156 859.952881,227.148788 C867.723389,225.913574 875.715454,226.072052 883.918213,225.576279 C883.918213,240.530334 883.918213,254.247711 883.918213,268.202820 C883.009399,267.944122 882.380005,267.791504 881.768005,267.586914 C867.262085,262.736725 856.693237,269.680603 856.083313,285.032410 C855.587708,297.505157 855.890564,310.009644 855.839355,323.000092z"/><path fill="#6DAC39" d="M397.000000,391.998138 C428.473236,391.998138 459.446503,391.998138 490.792969,391.998138 C490.792969,404.699890 490.792969,417.072754 490.792969,429.726562 C438.290070,429.726562 385.895660,429.726562 333.244019,429.726562 C333.244019,417.257721 333.244019,404.991150 333.244019,391.998138 C354.328308,391.998138 375.414154,391.998138 397.000000,391.998138z"/></svg> Moisture Probes</h2>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span id="detailMoistureBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-success-light);color:var(--text-success-dark);">—</span>
                </div>
            </div>
            <div class="card-body" id="detailMoistureBody">
                <div class="loading">Loading moisture data...</div>
            </div>
        </div>

        <!-- Zones Card -->
        <div class="card">
            <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                <h2>Zones</h2>
                <div id="mgmtAutoAdvanceToggle" style="display:none;"></div>
            </div>
            <div class="card-body" id="detailZones">
                <div class="loading">Loading zones...</div>
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

        <!-- Expansion Boards Card -->
        <div class="card" id="detailExpansionCard" style="display:none;">
            <div class="card-header">
                <h2>&#128268; Expansion Boards</h2>
                <div style="display:flex;align-items:center;gap:8px;">
                    <span id="detailExpansionStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-tile);color:var(--text-muted);">&#8212;</span>
                </div>
            </div>
            <div class="card-body" id="detailExpansionCardBody">
                <div class="loading">Loading expansion data...</div>
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
<div id="notesModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
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
<div id="keyModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
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

<!-- Change Log Modal -->
<div id="mgmtChangelogModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:720px;max-height:80vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">Configuration Change Log</h3>
            <div style="display:flex;gap:6px;align-items:center;">
                <button class="btn btn-secondary btn-sm" onclick="mgmtExportChangelogCSV()">Export CSV</button>
                <button onclick="mgmtCloseChangelogModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
            </div>
        </div>
        <div id="mgmtChangelogContent" style="padding:16px 24px 24px 24px;overflow-y:auto;font-size:13px;color:var(--text-secondary);line-height:1.5;">
            Loading...
        </div>
    </div>
</div>

<!-- Help Modal -->
<div id="qrScanModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:480px;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px 12px 20px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:16px;font-weight:600;margin:0;color:var(--text-primary);">Scan QR Code</h3>
            <button onclick="closeQRScanner()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div style="padding:16px 20px 20px 20px;">
            <div id="qrReader" style="width:100%;border-radius:8px;overflow:hidden;"></div>
            <p id="qrScanStatus" style="text-align:center;font-size:13px;color:var(--text-muted);margin:12px 0 0 0;">Point your camera at the homeowner's QR code</p>
        </div>
    </div>
</div>

<div id="helpModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:640px;max-height:80vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">Management Dashboard Help</h3>
            <button onclick="closeHelpModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div id="helpContent" style="padding:16px 24px 24px 24px;overflow-y:auto;font-size:14px;color:var(--text-secondary);line-height:1.6;"></div>
    </div>
</div>

<!-- Alerts Panel Modal -->
<div id="alertsPanelModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:640px;max-height:80vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">&#9888;&#65039; Customer Issues</h3>
            <div style="display:flex;align-items:center;gap:8px;">
                <button onclick="showNotifPrefs()" style="background:none;border:none;font-size:18px;cursor:pointer;color:var(--text-muted);padding:0 4px;" title="Notification Preferences">&#9881;&#65039;</button>
                <button onclick="closeAlertsPanel()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
            </div>
        </div>
        <div id="alertsPanelContent" style="padding:16px 24px 24px 24px;overflow-y:auto;font-size:14px;color:var(--text-secondary);line-height:1.6;"></div>
    </div>
</div>

<!-- Acknowledge Issue Modal -->
<div id="ackModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10001;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:480px;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">Acknowledge Issue</h3>
            <button onclick="closeAckModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div style="padding:20px 24px 24px 24px;">
            <div id="ackIssueDetails" style="margin-bottom:16px;"></div>
            <label style="font-size:13px;font-weight:600;color:var(--text-secondary);display:block;margin-bottom:6px;">Note to Homeowner (optional)</label>
            <textarea id="ackNote" maxlength="500" placeholder="Add a note for the homeowner..." style="width:100%;min-height:80px;padding:10px 12px;border-radius:8px;border:1px solid var(--border-light);background:var(--bg-tile);color:var(--text-primary);font-size:14px;font-family:inherit;resize:vertical;box-sizing:border-box;"></textarea>
            <label style="font-size:13px;font-weight:600;color:var(--text-secondary);display:block;margin:12px 0 6px 0;">Schedule Service Date (optional)</label>
            <input type="date" id="ackServiceDate" style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--border-light);background:var(--bg-tile);color:var(--text-primary);font-size:14px;box-sizing:border-box;">
            <div style="display:flex;gap:8px;margin-top:16px;justify-content:flex-end;">
                <button class="btn btn-secondary btn-sm" onclick="closeAckModal()">Cancel</button>
                <button class="btn btn-primary btn-sm" id="ackSubmitBtn" onclick="submitAcknowledge()">Acknowledge</button>
            </div>
        </div>
    </div>
</div>

<!-- Notification Preferences Modal -->
<div id="notifPrefsModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10002;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:460px;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;max-height:90vh;overflow-y:auto;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">&#128276; Notification Preferences</h3>
            <button onclick="closeNotifPrefs()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
        </div>
        <div style="padding:20px 24px 24px 24px;">
            <!-- Browser Notifications Section -->
            <p style="font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:6px;">&#127760; Browser Notifications</p>
            <p style="font-size:13px;color:var(--text-muted);margin-bottom:14px;">Choose which issue severities trigger browser notifications:</p>
            <div style="display:flex;flex-direction:column;gap:10px;">
                <label style="display:flex;align-items:center;gap:10px;cursor:pointer;"><input type="checkbox" id="notifSevere" checked><span style="font-weight:600;color:#e74c3c;">Severe Issues</span></label>
                <label style="display:flex;align-items:center;gap:10px;cursor:pointer;"><input type="checkbox" id="notifAnnoyance" checked><span style="font-weight:600;color:#f39c12;">Annoyances</span></label>
                <label style="display:flex;align-items:center;gap:10px;cursor:pointer;"><input type="checkbox" id="notifClarification"><span style="font-weight:600;color:#3498db;">Clarifications</span></label>
            </div>
            <div style="display:flex;gap:8px;margin-top:16px;justify-content:space-between;align-items:center;">
                <button class="btn btn-secondary btn-sm" onclick="requestNotifPermission()">Enable Notifications</button>
                <button class="btn btn-primary btn-sm" onclick="saveNotifPrefs()">Save</button>
            </div>
            <div id="notifPermStatus" style="font-size:11px;color:var(--text-muted);margin-top:8px;"></div>

            <!-- HA Notification Section -->
            <div style="border-top:1px solid var(--border-light);margin-top:20px;padding-top:20px;">
                <p style="font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:6px;">&#127968; Home Assistant Notifications</p>
                <p style="font-size:13px;color:var(--text-muted);margin-bottom:14px;">Send push notifications (SMS, mobile app, etc.) through your HA notification service when customers report new issues.</p>
                <label style="display:flex;align-items:center;gap:10px;cursor:pointer;margin-bottom:14px;">
                    <input type="checkbox" id="haNotifEnabled">
                    <span style="font-weight:600;color:var(--text-primary);">Enable HA Notifications</span>
                </label>
                <div style="margin-bottom:12px;">
                    <label style="font-size:13px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Notify Service</label>
                    <div style="display:flex;gap:6px;align-items:center;">
                        <select id="haNotifyService" style="flex:1;padding:8px 12px;border:1px solid var(--border-input);border-radius:6px;font-size:14px;background:var(--bg-input);color:var(--text-primary);">
                            <option value="">-- Select a notify service --</option>
                        </select>
                        <button class="btn btn-secondary btn-sm" onclick="loadNotifyServices()" title="Refresh service list" style="padding:6px 10px;font-size:16px;line-height:1;">&#8635;</button>
                    </div>
                    <div id="haNotifyServiceHint" style="font-size:11px;color:var(--text-placeholder);margin-top:3px;">Auto-detected from Home Assistant</div>
                </div>
                <p style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">Severity filters:</p>
                <div style="display:flex;flex-direction:column;gap:10px;margin-bottom:14px;">
                    <label style="display:flex;align-items:center;gap:10px;cursor:pointer;"><input type="checkbox" id="haNotifSevere" checked><span style="font-weight:600;color:#e74c3c;">Severe Issues</span></label>
                    <label style="display:flex;align-items:center;gap:10px;cursor:pointer;"><input type="checkbox" id="haNotifAnnoyance" checked><span style="font-weight:600;color:#f39c12;">Annoyances</span></label>
                    <label style="display:flex;align-items:center;gap:10px;cursor:pointer;"><input type="checkbox" id="haNotifClarification"><span style="font-weight:600;color:#3498db;">Clarifications</span></label>
                </div>
                <div style="display:flex;gap:8px;justify-content:space-between;align-items:center;">
                    <button class="btn btn-secondary btn-sm" onclick="testHANotification()">&#128172; Test</button>
                    <button class="btn btn-primary btn-sm" onclick="saveHANotifSettings()">Save</button>
                </div>
                <div id="haNotifStatus" style="font-size:11px;color:var(--text-muted);margin-top:8px;"></div>
            </div>
        </div>
    </div>
</div>

<div class="toast-container" id="toastContainer"></div>

<script>
function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('flux_dark_mode_management', isDark);
    document.getElementById('darkModeBtn').textContent = isDark ? '☀️' : '🌙';
}
(function initDarkToggleIcon() {
    const btn = document.getElementById('darkModeBtn');
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
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    try {
        const res = await fetch(BASE + path, {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            signal: controller.signal,
            ...options,
        });
        clearTimeout(timeoutId);
        let data;
        try { data = await res.json(); } catch (_) {
            throw new Error('Server returned non-JSON response (HTTP ' + res.status + ')');
        }
        if (!res.ok) {
            const detail = data.detail || data.error || JSON.stringify(data);
            console.error('[API]', options.method || 'GET', path, res.status, detail);
            throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
        }
        return data;
    } catch (e) {
        clearTimeout(timeoutId);
        if (e.name === 'AbortError') {
            throw new Error('Request timed out — the property may be offline or slow to respond');
        }
        throw e;
    }
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
        updateAlertBadge(allCustomers);
        checkForNewIssues(allCustomers);
        // Verify "running" cards with live status (cached status can be stale)
        refreshRunningStatuses();
    } catch (e) {
        document.getElementById('customerGrid').innerHTML =
            '<div class="empty-state"><h3>Error loading properties</h3><p>' + e.message + '</p></div>';
    }
}

async function refreshRunningStatuses() {
    // For each customer currently showing as "running", fetch live status
    // to verify they are still running (cached last_status can be up to 5 min stale)
    const running = allCustomers.filter(c => getSystemStatus(c) === 'running');
    for (const c of running) {
        try {
            const live = await api('/customers/' + c.id + '/status');
            if (live && live.system_status) {
                const liveActive = live.system_status.active_zones || 0;
                const cachedActive = (c.last_status && c.last_status.system_status)
                    ? c.last_status.system_status.active_zones : 0;
                if (liveActive !== cachedActive) {
                    // Update the cached status and re-render
                    if (!c.last_status) c.last_status = {};
                    c.last_status.system_status = live.system_status;
                    filterCustomers();  // Re-render grid with updated status
                    return;  // Only need to re-render once
                }
            }
        } catch(_) {
            // Silently skip — live check failed, keep cached status
        }
    }
}

function renderCustomerGrid(customers) {
    const grid = document.getElementById('customerGrid');
    if (customers.length === 0) {
        const isFiltered = document.getElementById('searchInput').value || document.getElementById('filterState').value || document.getElementById('filterCity').value || document.getElementById('filterZones').value || document.getElementById('filterStatus').value || document.getElementById('filterSystemStatus').value || document.getElementById('filterIssues').value;
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
        const issueSummary = c.issue_summary;
        const issueCount = issueSummary && issueSummary.active_count ? issueSummary.active_count : 0;
        const issueMaxSev = issueSummary ? issueSummary.max_severity : null;
        const issueCardClass = issueCount > 0 ? (issueMaxSev === 'severe' ? ' has-severe-issue' : issueMaxSev === 'annoyance' ? ' has-annoyance-issue' : ' has-clarification-issue') : '';
        const issueBadgeColor = issueMaxSev === 'severe' ? '#e74c3c' : issueMaxSev === 'annoyance' ? '#f39c12' : '#3498db';
        const issueBadgeHtml = issueCount > 0 ? '<span style="display:inline-block;margin-left:6px;padding:1px 7px;border-radius:8px;font-size:11px;font-weight:700;background:' + issueBadgeColor + '22;color:' + issueBadgeColor + ';">&#9888; ' + issueCount + '</span>' : '';
        return `
        <div class="customer-card ${status}${issueCardClass}" onclick="viewCustomer('${c.id}')">
            <div class="customer-card-body">
                <div class="customer-card-header">
                    <span class="customer-name">${esc(c.name)}${issueBadgeHtml}</span>
                    <span class="customer-status">
                        <span class="status-dot ${status}"></span>
                        ${status === 'online' ? 'Online' : status === 'revoked' ? '<span style="color:var(--text-disabled);">Access Revoked</span>' : status === 'offline' ? 'Offline' : 'Unknown'}
                    </span>
                </div>
                ${contactName ? '<div style="font-size:13px;color:var(--text-secondary-alt);margin-bottom:2px;">&#128100; ' + esc(contactName) + '</div>' : ''}
                ${addr ? '<div class="customer-address" onclick="openAddressInMaps(\\''+encodeURIComponent(addr)+'\\');event.stopPropagation();" style="cursor:pointer;color:var(--color-link);text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;" title="Open in Maps">' + esc(addr) + '</div>' : ''}
                ${c.phone ? '<div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;">&#128222; <a href="tel:' + esc(c.phone) + '" style="color:var(--color-link);text-decoration:none;" onclick="event.stopPropagation();">' + esc(c.phone) + '</a></div>' : ''}
                ${c.notes ? '<div style="font-size:13px;color:var(--text-muted);margin-bottom:6px;">' + esc(c.notes) + '</div>' : ''}
                <div class="customer-stats">
                    ${zoneInfo}${stats}
                </div>
                ${issueCount > 0 ? '<div style="margin-top:8px;padding-top:8px;border-top:1px solid var(--border-light);">' +
                    (issueSummary.issues || []).slice(0, 3).map(function(issue) {
                        const iColor = issue.severity === 'severe' ? '#e74c3c' : issue.severity === 'annoyance' ? '#f39c12' : '#3498db';
                        const iLabel = issue.severity === 'severe' ? 'Severe' : issue.severity === 'annoyance' ? 'Annoyance' : 'Clarification';
                        const iStatus = issue.status === 'open' ? 'Open' : issue.status === 'acknowledged' ? 'Acknowledged' : issue.status === 'scheduled' ? 'Scheduled' : issue.status;
                        const iDesc = (issue.description || '').length > 80 ? issue.description.substring(0, 80) + '...' : (issue.description || '');
                        return '<div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:6px;font-size:12px;">' +
                            '<span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:' + iColor + '22;color:' + iColor + ';white-space:nowrap;flex-shrink:0;">' + esc(iLabel) + '</span>' +
                            '<span style="color:var(--text-secondary);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">' + esc(iDesc) + '</span>' +
                            '<span style="color:var(--text-muted);font-size:10px;white-space:nowrap;">' + esc(iStatus) + '</span>' +
                        '</div>';
                    }).join('') +
                    (issueSummary.issues && issueSummary.issues.length > 3 ? '<div style="font-size:11px;color:var(--text-muted);">+ ' + (issueSummary.issues.length - 3) + ' more</div>' : '') +
                '</div>' : ''}
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

// --- Open Address in Maps ---
function openAddressInMaps(addrOrEncoded) {
    let addr = addrOrEncoded;
    if (!addr) return;
    // If it looks URL-encoded (from card onclick), decode it
    if (addr.indexOf('%') !== -1) {
        try { addr = decodeURIComponent(addr); } catch(e) {}
    }
    const encoded = encodeURIComponent(addr);
    const isApple = /iPad|iPhone|iPod|Macintosh/.test(navigator.userAgent);
    if (isApple) {
        window.open('https://maps.apple.com/?q=' + encoded, '_blank');
    } else {
        window.open('https://www.google.com/maps/search/?api=1&query=' + encoded, '_blank');
    }
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
    const issuesFilter = document.getElementById('filterIssues').value;
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
    if (issuesFilter) {
        filtered = filtered.filter(c => {
            const count = (c.issue_summary && c.issue_summary.active_count) ? c.issue_summary.active_count : 0;
            const maxSev = c.issue_summary ? c.issue_summary.max_severity : null;
            if (issuesFilter === 'has_issues') return count > 0;
            if (issuesFilter === 'no_issues') return count === 0;
            if (issuesFilter === 'severe') return count > 0 && c.issue_summary.issues && c.issue_summary.issues.some(i => i.severity === 'severe');
            if (issuesFilter === 'annoyance') return count > 0 && c.issue_summary.issues && c.issue_summary.issues.some(i => i.severity === 'annoyance');
            if (issuesFilter === 'clarification') return count > 0 && c.issue_summary.issues && c.issue_summary.issues.some(i => i.severity === 'clarification');
            return true;
        });
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
        if (sortBy === 'issues') {
            const aCount = (a.issue_summary && a.issue_summary.active_count) || 0;
            const bCount = (b.issue_summary && b.issue_summary.active_count) || 0;
            if (bCount !== aCount) return bCount - aCount;
            const sevOrder = {severe: 3, annoyance: 2, clarification: 1};
            const aSev = a.issue_summary ? (sevOrder[a.issue_summary.max_severity] || 0) : 0;
            const bSev = b.issue_summary ? (sevOrder[b.issue_summary.max_severity] || 0) : 0;
            return bSev - aSev;
        }
        return 0;
    });

    // Update filter count and clear button
    const hasFilters = search || stateFilter || cityFilter || zonesFilter || statusFilter || systemStatusFilter || issuesFilter;
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
    document.getElementById('filterIssues').value = '';
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

// --- Customer Local Time ---
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
let _customerClockTimer = null;
function startCustomerClock(state) {
    stopCustomerClock();
    const el = document.getElementById('mgmtTimezone');
    const tz = STATE_TIMEZONES[(state || '').toUpperCase()];
    if (!tz) { el.textContent = ''; return; }
    function tick() {
        const now = new Date();
        const time = now.toLocaleTimeString('en-US', {timeZone: tz, hour: 'numeric', minute: '2-digit', hour12: true});
        const abbr = now.toLocaleTimeString('en-US', {timeZone: tz, timeZoneName: 'short'}).split(' ').pop();
        el.textContent = time + ' ' + abbr;
    }
    tick();
    _customerClockTimer = setInterval(tick, 30000);
}
function stopCustomerClock() {
    if (_customerClockTimer) { clearInterval(_customerClockTimer); _customerClockTimer = null; }
    document.getElementById('mgmtTimezone').textContent = '';
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
    const btn = document.querySelector('#addForm .btn-primary');
    if (btn) { btn.disabled = true; btn.textContent = 'Connecting...'; }
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
    } finally {
        if (btn) { btn.disabled = false; btn.textContent = 'Connect'; }
    }
}

// --- QR Code Scanner ---
let qrScanner = null;

function openQRScanner() {
    // Make sure the add form is visible
    const form = document.getElementById('addForm');
    if (!form.classList.contains('visible')) form.classList.add('visible');

    const modal = document.getElementById('qrScanModal');
    const status = document.getElementById('qrScanStatus');
    status.textContent = 'Initializing camera...';
    status.style.color = 'var(--text-muted)';
    modal.style.display = 'flex';

    if (typeof Html5Qrcode === 'undefined') {
        status.textContent = 'QR scanner library failed to load. Please check your internet connection.';
        status.style.color = 'var(--color-danger)';
        return;
    }

    qrScanner = new Html5Qrcode('qrReader');
    qrScanner.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        function onScanSuccess(decodedText) {
            // Validate it looks like a connection key
            try {
                const decoded = JSON.parse(atob(decodedText.replace(/-/g, '+').replace(/_/g, '/')));
                if (!decoded.url || !decoded.key) {
                    status.textContent = 'QR code does not contain a valid connection key. Try again.';
                    status.style.color = 'var(--color-danger)';
                    return;
                }
            } catch (e) {
                status.textContent = 'QR code does not contain a valid connection key. Try again.';
                status.style.color = 'var(--color-danger)';
                return;
            }
            // Success — fill in the key and close scanner
            document.getElementById('addKey').value = decodedText;
            previewKey();
            closeQRScanner();
            showToast('QR code scanned successfully');
        },
        function onScanFailure() {
            // Ignore scan failures — camera is still trying
        }
    ).then(function() {
        status.textContent = 'Point your camera at the homeowner\\'s QR code';
        status.style.color = 'var(--text-muted)';
    }).catch(function(err) {
        var msg = String(err);
        if (msg.indexOf('NotAllowedError') !== -1 || msg.indexOf('Permission') !== -1) {
            status.textContent = 'Camera access denied. Please allow camera access in your browser or Home Assistant settings and try again.';
        } else if (msg.indexOf('NotFoundError') !== -1 || msg.indexOf('no camera') !== -1) {
            status.textContent = 'No camera found. QR scanning requires a device with a camera.';
        } else {
            status.textContent = 'Could not start camera: ' + msg;
        }
        status.style.color = 'var(--color-danger)';
    });
}

function closeQRScanner() {
    var modal = document.getElementById('qrScanModal');
    modal.style.display = 'none';
    if (qrScanner) {
        qrScanner.stop().catch(function() {});
        qrScanner.clear();
        qrScanner = null;
    }
}

async function removeCustomer(id, name) {
    if (!confirm('Remove "' + name + '"?\\n\\nThis is permanent and cannot be recovered. You will need a new connection key from the homeowner to re-add this property.')) return;
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
        startCustomerClock(customer.state);
    } catch (e) {
        document.getElementById('detailName').textContent = 'Unknown Property';
        document.getElementById('detailAddress').style.display = 'none';
        document.getElementById('detailContact').style.display = 'none';
        document.getElementById('detailPhone').style.display = 'none';
        document.getElementById('detailMap').style.display = 'none';
        document.getElementById('detailNotesSection').style.display = 'none';
        stopCustomerClock();
    }

    loadDetailData(id);
    detailRefreshTimer = setInterval(() => loadDetailData(id), 15000);
}

function backToList() {
    currentCustomerId = null;
    stopCustomerClock();
    document.getElementById('detailView').classList.remove('visible');
    document.getElementById('listView').style.display = 'block';
    document.getElementById('apiDocsCard').style.display = 'block';
    if (detailRefreshTimer) { clearInterval(detailRefreshTimer); detailRefreshTimer = null; }
    if (leafletMap) { leafletMap.remove(); leafletMap = null; }
    document.getElementById('detailMap').style.display = 'none';
    window._currentZoneAliases = {};
    window._zoneModes = {};
    // Clear data caches so next customer loads fresh
    _mgmtWeatherDataCache = null;
    _mgmtWeatherRulesCache = null;
    _mgmtMoistureDataCache = null;
    _mgmtWeatherCardBuilt = false;
    _mgmtSensorGridBuilt = false;
    _mgmtControlsLoadedFor = null;
    window._rainSensors = [];
    window._rainControls = [];
    window._expansionSensors = [];
    window._expansionControls = [];
    // Hide issue card for next customer
    document.getElementById('detailIssuesCard').style.display = 'none';
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

let _mgmtControlsLoadedFor = null;
async function loadDetailData(id) {
    loadDetailStatus(id);
    loadDetailWeather(id);
    loadDetailMoisture(id);
    loadDetailZones(id);
    loadDetailSensors(id);
    if (_mgmtControlsLoadedFor !== id) {
        loadDetailControls(id);
        _mgmtControlsLoadedFor = id;
    }
    loadDetailHistory(id);
    loadDetailIssues(id);
}

// --- Detail: Weather ---
let _mgmtWeatherDataCache = null;
let _mgmtWeatherRulesCache = null;
let _mgmtMoistureDataCache = null;
let _mgmtWeatherCardBuilt = false;

const _mgmtCondIcons = {
    'sunny': '☀️', 'clear-night': '🌙', 'partlycloudy': '⛅',
    'cloudy': '☁️', 'rainy': '🌧️', 'pouring': '🌧️',
    'snowy': '❄️', 'windy': '💨', 'fog': '🌫️',
    'lightning': '⚡', 'lightning-rainy': '⛈️', 'hail': '🧊',
};

function _buildMgmtWeatherCardShell() {
    let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;">';
    html += '<div style="background:var(--bg-weather);border-radius:8px;padding:10px;text-align:center;">';
    html += '<div data-id="wIcon" style="font-size:24px;"></div>';
    html += '<div data-id="wCondition" style="font-weight:600;text-transform:capitalize;font-size:13px;color:var(--text-primary);"></div>';
    html += '</div>';
    html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
    html += '<div style="color:var(--text-placeholder);font-size:11px;">Temperature</div>';
    html += '<div data-id="wTemp" style="font-weight:600;font-size:16px;color:var(--text-primary);"></div>';
    html += '</div>';
    html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
    html += '<div style="color:var(--text-placeholder);font-size:11px;">Humidity</div>';
    html += '<div data-id="wHumidity" style="font-weight:600;font-size:16px;color:var(--text-primary);"></div>';
    html += '</div>';
    html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;">';
    html += '<div style="color:var(--text-placeholder);font-size:11px;">Wind</div>';
    html += '<div data-id="wWind" style="font-weight:600;font-size:16px;color:var(--text-primary);"></div>';
    html += '</div>';
    html += '</div>';
    html += '<div data-id="wForecast"></div>';
    html += '<div data-id="wAdjustments"></div>';
    html += '<div style="margin-top:16px;border-top:1px solid var(--border-light);padding-top:16px;">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0;cursor:pointer;" onclick="mgmtToggleWeatherRules()">';
    html += '<div style="display:flex;align-items:center;gap:8px;">';
    html += '<span id="mgmtWeatherRulesChevron" style="font-size:12px;transition:transform 0.2s;">&#9654;</span>';
    html += '<div style="font-size:14px;font-weight:600;">Weather Rules</div>';
    html += '</div>';
    html += '<div style="display:flex;gap:6px;">';
    html += '<button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();mgmtEvaluateWeather()">Test Rules Now</button>';
    html += '<button class="btn btn-secondary btn-sm" onclick="event.stopPropagation();mgmtExportWeatherLogCSV()">Export Log</button>';
    html += '<button class="btn btn-danger btn-sm" onclick="event.stopPropagation();mgmtClearWeatherLog()">Clear Log</button>';
    html += '</div>';
    html += '</div>';
    html += '<div id="mgmtWeatherRulesContainer" style="display:none;margin-top:12px;"><div class="loading">Loading rules...</div></div>';
    html += '</div>';
    return html;
}

function _getMgmtVisibleWeatherKey(data) {
    const w = data.weather || {};
    const parts = [
        w.condition, w.temperature, w.humidity, w.wind_speed,
        data.watering_multiplier,
        JSON.stringify((data.active_adjustments || []).map(a => a.reason || a.rule)),
    ];
    const fc = (w.forecast || []).slice(0, 5);
    for (const f of fc) {
        parts.push(f.condition, f.temperature, f.precipitation_probability);
    }
    return parts.join('|');
}

async function loadDetailWeather(id) {
    const card = document.getElementById('detailWeatherCard');
    const body = document.getElementById('detailWeatherBody');
    const badge = document.getElementById('detailWeatherBadge');
    try {
        const data = await api('/customers/' + id + '/weather');
        if (!data.weather_enabled) {
            card.style.display = 'none';
            _mgmtWeatherDataCache = null;
            _mgmtWeatherCardBuilt = false;
            return;
        }

        // Build the card shell once, then only update data values
        if (!_mgmtWeatherCardBuilt) {
            body.innerHTML = _buildMgmtWeatherCardShell();
            _mgmtWeatherCardBuilt = true;
            _mgmtWeatherDataCache = null;
            loadMgmtWeatherRules(id);
        }

        // Skip updates if visible data hasn't changed
        const visibleKey = _getMgmtVisibleWeatherKey(data);
        if (_mgmtWeatherDataCache === visibleKey) return;
        _mgmtWeatherDataCache = visibleKey;

        card.style.display = 'block';
        const w = data.weather || {};
        if (w.error) {
            body.innerHTML = '<div style="color:var(--text-placeholder);text-align:center;padding:12px;">' + esc(w.error) + '</div>';
            _mgmtWeatherCardBuilt = false;
            return;
        }

        // --- Targeted updates: only change text/styles, no DOM rebuild ---
        const icon = _mgmtCondIcons[w.condition] || '🌡️';
        const mult = data.watering_multiplier != null ? data.watering_multiplier : 1.0;

        badge.textContent = mult + 'x';
        badge.style.background = mult === 1.0 ? 'var(--bg-success-light)' : mult < 1 ? 'var(--bg-warning)' : 'var(--bg-danger-light)';
        badge.style.color = mult === 1.0 ? 'var(--text-success-dark)' : mult < 1 ? 'var(--text-warning)' : 'var(--text-danger-dark)';

        const el = (did) => body.querySelector('[data-id=\"' + did + '\"]');
        el('wIcon').textContent = icon;
        el('wCondition').textContent = w.condition || 'unknown';
        el('wTemp').textContent = w.temperature != null ? w.temperature + (w.temperature_unit || '°F') : 'N/A';
        el('wHumidity').textContent = w.humidity != null ? w.humidity + '%' : 'N/A';
        el('wWind').textContent = w.wind_speed != null ? w.wind_speed + ' ' + (w.wind_speed_unit || 'mph') : 'N/A';

        // Forecast strip
        const forecastEl = el('wForecast');
        const forecast = w.forecast || [];
        if (forecast.length > 0) {
            let fh = '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;margin-bottom:8px;">Forecast</div>';
            fh += '<div style="display:flex;gap:8px;overflow-x:auto;">';
            for (let i = 0; i < Math.min(forecast.length, 5); i++) {
                const f = forecast[i];
                const dt = f.datetime ? new Date(f.datetime) : null;
                const dayLabel = dt ? dt.toLocaleDateString('en-US', { weekday: 'short' }) : '';
                const fIcon = _mgmtCondIcons[f.condition] || '🌡️';
                const precip = f.precipitation_probability || 0;
                fh += '<div style="flex:0 0 auto;background:var(--bg-tile);border-radius:8px;padding:8px 12px;text-align:center;min-width:70px;">';
                fh += '<div style="font-size:11px;color:var(--text-placeholder);">' + esc(dayLabel) + '</div>';
                fh += '<div style="font-size:18px;">' + fIcon + '</div>';
                fh += '<div style="font-size:12px;font-weight:600;">' + (f.temperature != null ? f.temperature + '°' : '') + '</div>';
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

        // Active adjustments
        const adjEl = el('wAdjustments');
        const adjustments = data.active_adjustments || [];
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

async function loadMgmtWeatherRules(custId) {
    const container = document.getElementById('mgmtWeatherRulesContainer');
    if (!container) return;
    try {
        const data = await api('/customers/' + custId + '/weather/rules');
        // Skip DOM rebuild if rules haven't changed
        const rulesKey = JSON.stringify(data);
        if (_mgmtWeatherRulesCache === rulesKey) return;
        _mgmtWeatherRulesCache = rulesKey;
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
        const result = await api('/customers/' + currentCustomerId + '/weather/rules', {
            method: 'PUT',
            body: JSON.stringify({ rules }),
        });
        const mult = result.watering_multiplier;
        showToast('Weather rules saved' + (mult != null ? ' — multiplier: ' + mult + 'x' : ''));
        _mgmtWeatherDataCache = null;
        _mgmtWeatherRulesCache = null;
        loadDetailWeather(currentCustomerId);
        loadDetailStatus(currentCustomerId);
        loadDetailControls(currentCustomerId);
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
        _mgmtWeatherDataCache = null;
        loadDetailWeather(currentCustomerId);
        loadDetailStatus(currentCustomerId);
        loadDetailControls(currentCustomerId);
    } catch (e) {
        showToast('Evaluation failed: ' + e.message, 'error');
    }
}

// --- CSV Export ---
function mgmtExportHistoryCSV() {
    if (!currentCustomerId) return;
    const hoursRaw = document.getElementById('mgmtHistoryRange') ? document.getElementById('mgmtHistoryRange').value : '24';
    const hours = parseInt(hoursRaw, 10) || 24;
    const url = BASE + '/customers/' + currentCustomerId + '/history/runs/csv?hours=' + hours;
    window.open(url, '_blank');
}

function mgmtToggleWeatherRules() {
    const container = document.getElementById('mgmtWeatherRulesContainer');
    const chevron = document.getElementById('mgmtWeatherRulesChevron');
    if (!container) return;
    const isHidden = container.style.display === 'none';
    container.style.display = isHidden ? 'block' : 'none';
    if (chevron) chevron.style.transform = isHidden ? 'rotate(90deg)' : 'rotate(0deg)';
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

// --- Detail: Moisture Probes ---
async function loadDetailMoisture(id) {
    const card = document.getElementById('detailMoistureCard');
    const body = document.getElementById('detailMoistureBody');
    const badge = document.getElementById('detailMoistureBadge');
    try {
        const data = await api('/customers/' + id + '/moisture/probes');
        const settings = await api('/customers/' + id + '/moisture/settings');
        let multData = {};
        try { multData = await api('/customers/' + id + '/moisture/multiplier'); } catch (_) {}

        // Skip DOM rebuild if data hasn't changed (prevents flickering on refresh)
        const moistureKey = JSON.stringify(data) + '|' + JSON.stringify(settings) + '|' + JSON.stringify(multData);
        if (_mgmtMoistureDataCache === moistureKey) return;
        _mgmtMoistureDataCache = moistureKey;

        // Always show the moisture card for management — they need access
        // to settings even when probes aren't configured yet
        card.style.display = 'block';

        const probes = data.probes || {};
        const probeCount = Object.keys(probes).length;
        badge.textContent = settings.enabled ? probeCount + ' probe(s)' : 'Disabled';
        badge.style.background = settings.enabled ? 'var(--bg-success-light)' : 'var(--bg-tile)';
        badge.style.color = settings.enabled ? 'var(--text-success-dark)' : 'var(--text-muted)';

        const perZone = (multData && multData.per_zone) || {};

        let html = '';

        if (probeCount > 0) {
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;">';
            for (const [pid, probe] of Object.entries(probes)) {
                const sensors = probe.sensors_live || {};
                const devSensors = probe.device_sensors || {};
                const zones = probe.zone_mappings || [];
                html += '<div style="background:var(--bg-tile);border-radius:10px;padding:14px;border:1px solid var(--border-light);">';
                // Header with per-zone skip/multiplier badges
                var probeZones = zones;
                var probeSkipBadges = '';
                var probeFactorLines = '';
                var liveWMult = (multData && multData.weather_multiplier != null) ? multData.weather_multiplier : 1.0;
                var afEnabled = settings.apply_factors_to_schedule;
                for (var pzi = 0; pzi < probeZones.length; pzi++) {
                    var pzEid = probeZones[pzi];
                    var pzInfo = perZone[pzEid];
                    if (pzInfo) {
                        var pzNum = (pzEid.match(/zone[_]?(\\d+)/i) || [])[1] || '?';
                        if (pzInfo.skip) {
                            probeSkipBadges += ' <span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:var(--bg-danger-light);color:var(--color-danger);">Z' + pzNum + ' Skip</span>';
                        } else if (pzInfo.moisture_multiplier != null && pzInfo.moisture_multiplier !== 1.0) {
                            probeSkipBadges += ' <span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;background:var(--bg-warning);color:var(--text-warning);">Z' + pzNum + ' ' + pzInfo.moisture_multiplier.toFixed(2) + 'x</span>';
                        }
                        // Factor detail line per zone
                        if (pzInfo.skip) {
                            probeFactorLines += '<div style="font-size:10px;color:var(--color-danger);">Z' + pzNum + ': Skip watering (soil saturated)</div>';
                        } else {
                            var cmult = pzInfo.combined != null ? pzInfo.combined : liveWMult;
                            if (afEnabled || Math.abs(cmult - 1.0) >= 0.005) {
                                probeFactorLines += '<div style="font-size:10px;color:var(--text-muted);">Z' + pzNum + ': Weather ' + liveWMult.toFixed(2) + 'x \\u00d7 Moisture ' + (pzInfo.moisture_multiplier != null ? pzInfo.moisture_multiplier.toFixed(2) : '1.00') + 'x = <strong>' + cmult.toFixed(2) + 'x</strong>' + (afEnabled ? ' \\u2713 Applied' : '') + '</div>';
                            }
                        }
                    }
                }
                html += '<div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-weight:600;font-size:14px;margin-bottom:' + (probeFactorLines ? '4' : '10') + 'px;">' + esc(probe.display_name || pid) + probeSkipBadges + '</div>';
                if (probeFactorLines) {
                    html += '<div style="margin-bottom:8px;">' + probeFactorLines + '</div>';
                }
                // Moisture bars
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
                // Device status row: WiFi, Battery, Sleep
                const hasDeviceInfo = devSensors.wifi || devSensors.battery || devSensors.sleep_duration;
                if (hasDeviceInfo) {
                    html += '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;padding-top:8px;border-top:1px solid var(--border-light);font-size:11px;color:var(--text-muted);">';
                    if (devSensors.wifi) {
                        const wv = devSensors.wifi.value;
                        const wLabel = wv == null ? '—' : wv > -50 ? 'Great' : wv > -60 ? 'Good' : wv > -70 ? 'Fair' : 'Poor';
                        const wColor = wv == null ? 'var(--text-muted)' : wv > -50 ? 'var(--text-success-dark)' : wv > -60 ? 'var(--text-success-dark)' : wv > -70 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
                        html += '<span style="color:' + wColor + ';" title="WiFi Signal: ' + (wv != null ? wv.toFixed(0) + ' dBm' : 'unknown') + '">📶 ' + wLabel + '</span>';
                    }
                    if (devSensors.battery) {
                        const bv = devSensors.battery.value;
                        const bIcon = bv == null ? '🔋' : bv > 50 ? '🔋' : bv > 20 ? '🪫' : '🪫';
                        const bColor = bv == null ? 'var(--text-muted)' : bv > 50 ? 'var(--text-success-dark)' : bv > 20 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
                        html += '<span style="color:' + bColor + ';" title="Battery">' + bIcon + ' ' + (bv != null ? bv.toFixed(0) + '%' : '—') + '</span>';
                    }
                    if (devSensors.sleep_duration) {
                        const sv = devSensors.sleep_duration.value;
                        let sleepSec = sv != null ? sv : '';
                        const unit = (devSensors.sleep_duration.unit || 's').toLowerCase();
                        if (unit === 'min' || unit === 'minutes') sleepSec = sv != null ? Math.round(sv * 60) : '';
                        else if (unit === 'h' || unit === 'hours') sleepSec = sv != null ? Math.round(sv * 3600) : '';
                        else sleepSec = sv != null ? Math.round(sv) : '';
                        const pendingSleep = probe.pending_sleep_duration;
                        html += '<span style="display:inline-flex;align-items:center;gap:4px;" title="Sleep Duration">';
                        html += '💤 <input type="number" id="mgmtSleepDur_' + esc(pid) + '" value="' + sleepSec + '" min="30" max="7200" step="30" style="width:60px;padding:1px 4px;border:1px solid var(--border-light);border-radius:4px;font-size:11px;background:var(--bg-card);color:var(--text-primary);">';
                        html += '<span style="font-size:10px;">sec</span>';
                        html += '<button onclick="mgmtSetSleepDuration(\\'' + esc(pid) + '\\')" style="padding:1px 6px;font-size:10px;border:1px solid var(--border-light);border-radius:4px;cursor:pointer;background:var(--bg-tile);color:var(--text-secondary);">Set</button>';
                        if (pendingSleep != null) {
                            html += '<span style="color:var(--color-warning);font-size:10px;" title="Pending: will apply when probe wakes">⏳ ' + pendingSleep + 's</span>';
                        }
                        html += '</span>';
                    }
                    if (devSensors.sleep_disabled) {
                        const sdVal = (devSensors.sleep_disabled.value || '').toLowerCase();
                        const isDisabled = sdVal === 'on';
                        html += '<span style="color:' + (isDisabled ? 'var(--color-warning)' : 'var(--text-success-dark)') + ';" title="Sleep ' + (isDisabled ? 'disabled (staying awake)' : 'enabled') + '">' +
                            (isDisabled ? '⏰ Awake' : '😴 Sleep OK') + '</span>';
                    }
                    html += '</div>';
                }
                // Schedule sync display (Gophr probes)
                if (devSensors.schedule_times && devSensors.schedule_times.length > 0) {
                    html += '<div style="margin-top:6px;padding-top:6px;border-top:1px solid var(--border-light);font-size:11px;">';
                    html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">';
                    html += '<span style="font-weight:600;color:var(--text-secondary);">Schedule Sync</span>';
                    html += '<button class="btn btn-primary btn-sm" style="font-size:10px;padding:2px 8px;" ' +
                        'onclick="mgmtSyncProbeSchedules()">Sync Now</button>';
                    html += '</div>';
                    html += '<div style="display:flex;gap:8px;flex-wrap:wrap;">';
                    for (var si = 0; si < devSensors.schedule_times.length; si++) {
                        var st = devSensors.schedule_times[si];
                        var stVal = st.value || '—';
                        var stNum = si + 1;
                        var stColor = stVal === '00:00' || stVal === '—' || stVal === 'unknown' ? 'var(--text-muted)' : 'var(--text-success-dark)';
                        html += '<span style="color:' + stColor + ';" title="' + esc(st.entity_id) + '">⏱ ' + stNum + ': ' + esc(stVal) + '</span>';
                    }
                    html += '</div></div>';
                }
                // Zone summary + edit toggle
                html += '<div style="margin-top:10px;display:flex;justify-content:space-between;align-items:center;">';
                if (zones.length > 0) {
                    html += '<span style="font-size:12px;color:var(--text-secondary-alt);"><strong>' + zones.length + '</strong> zone' + (zones.length !== 1 ? 's' : '') + ' mapped</span>';
                } else {
                    html += '<span style="font-size:12px;color:var(--text-muted);font-style:italic;">No zones mapped</span>';
                }
                html += '<a href="#" onclick="mgmtToggleProbeZones(\\'' + esc(pid) + '\\');return false;" style="font-size:12px;">Edit Zones</a>';
                html += '</div>';
                // Collapsible zone assignment
                html += '<div id="mgmtProbeZones_' + esc(pid) + '" style="display:none;margin-top:10px;border-top:1px solid var(--border-light);padding-top:10px;">';
                html += '<div style="display:flex;gap:6px;margin-bottom:8px;">';
                html += '<button class="btn btn-secondary btn-sm" onclick="mgmtProbeZonesSelectAll(\\'' + esc(pid) + '\\',true)">Select All</button>';
                html += '<button class="btn btn-secondary btn-sm" onclick="mgmtProbeZonesSelectAll(\\'' + esc(pid) + '\\',false)">Select None</button>';
                html += '</div>';
                html += '<div id="mgmtProbeZoneCbs_' + esc(pid) + '" style="font-size:12px;">Loading zones...</div>';
                html += '<button class="btn btn-primary btn-sm" style="margin-top:8px;" onclick="mgmtSaveProbeZones(\\'' + esc(pid) + '\\')">Save Zone Mapping</button>';
                html += '</div>';
                html += '</div>';
            }
            html += '</div>';
        } else {
            html += '<div style="text-align:center;padding:12px;color:var(--text-muted);">No moisture probes configured on this system.</div>';
        }

        // Settings (expandable)
        html += '<div style="margin-top:16px;border-top:1px solid var(--border-light);padding-top:12px;">';
        html += '<div style="cursor:pointer;display:flex;justify-content:space-between;align-items:center;" onclick="toggleMgmtMoistureSettings()">';
        html += '<span style="font-size:13px;font-weight:600;">Settings</span>';
        html += '<span id="mgmtMoistureSettingsChevron" style="font-size:12px;color:var(--text-muted);">' + (_mgmtMoistureSettingsOpen ? '▼' : '▶') + '</span>';
        html += '</div>';
        html += '<div id="mgmtMoistureSettingsBody" style="display:' + (_mgmtMoistureSettingsOpen ? 'block' : 'none') + ';margin-top:10px;">';

        // Enable toggle
        html += '<label style="display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer;margin-bottom:12px;">';
        html += '<input type="checkbox" id="mgmtMoistureEnabled" ' + (settings.enabled ? 'checked' : '') + '> Enable Moisture Control</label>';

        // Schedule sync toggle
        html += '<label style="display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer;margin-bottom:12px;">';
        html += '<input type="checkbox" id="mgmtMoistureScheduleSync" ' + (settings.schedule_sync_enabled !== false ? 'checked' : '') + '> Sync Schedules to Gophr Probes</label>';
        html += '<div style="font-size:11px;color:var(--text-muted);margin-bottom:12px;margin-top:-8px;">Syncs wake times to probes and dynamically manages sleep between mapped zones during runs.</div>';

        // Stale threshold
        html += '<div style="margin-bottom:12px;">';
        html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Stale Reading Threshold</label>';
        html += '<div style="display:grid;grid-template-columns:120px 1fr;gap:8px;align-items:center;">';
        html += '<input type="number" id="mgmtMoistureStaleMin" value="' + (settings.stale_reading_threshold_minutes || 120) + '" min="5" max="1440" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;">';
        html += '<span style="font-size:12px;color:var(--text-muted);">minutes — readings older than this are ignored</span>';
        html += '</div></div>';

        // Root Zone Thresholds (gradient-based algorithm)
        const dt = settings.default_thresholds || {};
        html += '<div style="margin-bottom:12px;">';
        html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Root Zone Thresholds (%)</label>';
        html += '<div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;">The mid sensor (root zone) drives watering decisions. Shallow detects rain; deep guards against over-irrigation.</div>';
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">';
        for (const [key, label, hint] of [
            ['root_zone_skip','Skip (saturated)','Skip watering entirely'],
            ['root_zone_wet','Wet','Reduce watering'],
            ['root_zone_optimal','Optimal','Normal watering (1.0x)'],
            ['root_zone_dry','Dry','Increase watering']
        ]) {
            html += '<div><label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:2px;">' + label + '</label>';
            html += '<input type="number" id="mgmtMoistureThresh_' + key + '" value="' + (dt[key] != null ? dt[key] : '') + '" min="0" max="100" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;" title="' + hint + '"></div>';
        }
        html += '</div>';
        html += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:8px;">';
        for (const [key, label] of [['max_increase_percent','Max Increase %'], ['max_decrease_percent','Max Decrease %'], ['rain_boost_threshold','Rain Delta']]) {
            html += '<div><label style="font-size:11px;color:var(--text-muted);display:block;margin-bottom:2px;">' + label + '</label>';
            html += '<input type="number" id="mgmtMoistureThresh_' + key + '" value="' + (dt[key] != null ? dt[key] : '') + '" min="0" max="100" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;"></div>';
        }
        html += '</div></div>';

        html += '<button class="btn btn-primary btn-sm" style="margin-top:4px;" onclick="mgmtSaveMoistureSettings()">Save Settings</button>';
        html += '</div></div>';

        body.innerHTML = html;
    } catch (e) {
        card.style.display = 'none';
    }
}

let _mgmtMoistureSettingsOpen = false;

function toggleMgmtMoistureSettings() {
    _mgmtMoistureSettingsOpen = !_mgmtMoistureSettingsOpen;
    const body = document.getElementById('mgmtMoistureSettingsBody');
    const chevron = document.getElementById('mgmtMoistureSettingsChevron');
    if (body) body.style.display = _mgmtMoistureSettingsOpen ? 'block' : 'none';
    if (chevron) chevron.textContent = _mgmtMoistureSettingsOpen ? '▼' : '▶';
}

async function mgmtSaveMoistureSettings() {
    try {
        const payload = {
            enabled: document.getElementById('mgmtMoistureEnabled').checked,
            schedule_sync_enabled: document.getElementById('mgmtMoistureScheduleSync').checked,
            stale_reading_threshold_minutes: parseInt(document.getElementById('mgmtMoistureStaleMin').value) || 120,
            default_thresholds: {
                root_zone_skip: parseInt(document.getElementById('mgmtMoistureThresh_root_zone_skip').value) || 80,
                root_zone_wet: parseInt(document.getElementById('mgmtMoistureThresh_root_zone_wet').value) || 65,
                root_zone_optimal: parseInt(document.getElementById('mgmtMoistureThresh_root_zone_optimal').value) || 45,
                root_zone_dry: parseInt(document.getElementById('mgmtMoistureThresh_root_zone_dry').value) || 30,
                max_increase_percent: parseInt(document.getElementById('mgmtMoistureThresh_max_increase_percent').value) || 50,
                max_decrease_percent: parseInt(document.getElementById('mgmtMoistureThresh_max_decrease_percent').value) || 50,
                rain_boost_threshold: parseInt(document.getElementById('mgmtMoistureThresh_rain_boost_threshold').value) || 15,
            },
        };
        const result = await api('/customers/' + currentCustomerId + '/moisture/settings', { method: 'PUT', body: JSON.stringify(payload) });
        showToast(result.message || 'Moisture settings saved');
        _mgmtMoistureDataCache = null;
        loadDetailMoisture(currentCustomerId);
        loadDetailStatus(currentCustomerId);
        loadDetailControls(currentCustomerId);  // Refresh schedule card (factors may have changed)
    } catch (e) { showToast(e.message, 'error'); }
}

async function mgmtSetSleepDuration(probeId) {
    const input = document.getElementById('mgmtSleepDur_' + probeId);
    if (!input) return;
    const seconds = parseInt(input.value);
    if (isNaN(seconds) || seconds < 30 || seconds > 7200) {
        showToast('Sleep duration must be 30-7200 seconds', 'error');
        return;
    }
    try {
        const result = await api('/customers/' + currentCustomerId + '/moisture/probes/' + encodeURIComponent(probeId) + '/sleep-duration', {
            method: 'PUT',
            body: JSON.stringify({ seconds: seconds }),
        });
        if (result.status === 'pending') {
            showToast('Sleep ' + seconds + 's queued — will apply when probe wakes', 'warning');
        } else {
            showToast('Sleep duration set to ' + seconds + 's');
        }
        _mgmtMoistureDataCache = null;
        loadDetailMoisture(currentCustomerId);
    } catch (e) { showToast(e.message, 'error'); }
}

async function mgmtToggleApplyFactors(enable) {
    try {
        const result = await api('/customers/' + currentCustomerId + '/moisture/settings', {
            method: 'PUT',
            body: JSON.stringify({ apply_factors_to_schedule: enable }),
        });
        const isError = result.success === false;
        showToast(result.message || (enable ? 'Factors applied' : 'Factors disabled'), isError ? 'error' : undefined);
        loadDetailControls(currentCustomerId);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Probe Zone Assignment (Management) ---
let _mgmtProbeZoneCache = {};

async function mgmtToggleProbeZones(probeId) {
    const el = document.getElementById('mgmtProbeZones_' + probeId);
    if (!el) return;
    const isVisible = el.style.display !== 'none';
    if (isVisible) {
        el.style.display = 'none';
        return;
    }
    el.style.display = 'block';
    const cbContainer = document.getElementById('mgmtProbeZoneCbs_' + probeId);
    cbContainer.innerHTML = '<div style="font-size:12px;color:var(--text-muted);">Loading zones...</div>';
    try {
        // Fetch current probe data via proxy
        const probesData = await api('/customers/' + currentCustomerId + '/moisture/probes');
        const probes = probesData.probes || {};
        const probe = probes[probeId];
        const currentMappings = probe ? (probe.zone_mappings || []) : [];
        _mgmtProbeZoneCache[probeId] = currentMappings;

        // Fetch all zones for this customer
        const zonesData = await api('/customers/' + currentCustomerId + '/zones');
        const allZones = Array.isArray(zonesData) ? zonesData : (zonesData.zones || []);

        if (allZones.length === 0) {
            cbContainer.innerHTML = '<div style="color:var(--text-muted);">No zones found on this controller.</div>';
            return;
        }

        // Refresh zone aliases from the customer to ensure they're current
        try {
            const freshCustomer = await api('/customers/' + currentCustomerId);
            window._currentZoneAliases = freshCustomer.zone_aliases || {};
        } catch(_) {}

        let cbHtml = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:4px;">';
        for (const z of allZones) {
            const eid = z.entity_id;
            const checked = currentMappings.includes(eid) ? ' checked' : '';
            let label = resolveZoneName(eid, z.friendly_name || z.name || eid);
            cbHtml += '<label style="display:flex;align-items:center;gap:4px;cursor:pointer;padding:3px 4px;border-radius:4px;' + (checked ? 'background:var(--bg-success-light);' : '') + '">';
            cbHtml += '<input type="checkbox" data-probe="' + esc(probeId) + '" data-zone="' + esc(eid) + '"' + checked + ' style="accent-color:var(--color-primary);">';
            cbHtml += '<span>' + esc(label) + '</span></label>';
        }
        cbHtml += '</div>';
        cbContainer.innerHTML = cbHtml;
    } catch (e) {
        cbContainer.innerHTML = '<div style="color:var(--color-danger);">Failed to load zones: ' + esc(e.message || 'Unknown error') + '</div>';
    }
}

function mgmtProbeZonesSelectAll(probeId, selectAll) {
    const container = document.getElementById('mgmtProbeZoneCbs_' + probeId);
    if (!container) return;
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(function(cb) { cb.checked = selectAll; });
}

async function mgmtSaveProbeZones(probeId) {
    const container = document.getElementById('mgmtProbeZoneCbs_' + probeId);
    if (!container) return;
    const checkboxes = container.querySelectorAll('input[type="checkbox"]');
    const selectedZones = [];
    checkboxes.forEach(function(cb) {
        if (cb.checked) selectedZones.push(cb.getAttribute('data-zone'));
    });
    try {
        await api('/customers/' + currentCustomerId + '/moisture/probes/' + encodeURIComponent(probeId), {
            method: 'PUT',
            body: JSON.stringify({ zone_mappings: selectedZones }),
        });
        showToast('Zone mapping updated (' + selectedZones.length + ' zones)');
        _mgmtMoistureDataCache = null;
        loadDetailMoisture(currentCustomerId);
        loadDetailControls(currentCustomerId);  // Refresh schedule card (zone mappings affect factors)
    } catch (e) { showToast(e.message, 'error'); }
}

async function mgmtSyncProbeSchedules() {
    try {
        const result = await api('/customers/' + currentCustomerId + '/moisture/probes/sync-schedules', { method: 'POST' });
        showToast(result.synced > 0 ? 'Synced ' + result.synced + ' schedule time(s)' : (result.reason || 'Nothing to sync'));
        _mgmtMoistureDataCache = null;
        loadDetailMoisture(currentCustomerId);
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
        return 'Zone ' + zoneNum;
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
        return 'Zone ' + zoneNum;
    }
    return fallbackName || entityId;
}

async function loadDetailZones(id) {
    const el = document.getElementById('detailZones');
    try {
        const data = await api('/customers/' + id + '/zones');
        // /api/zones returns a bare list [...], not {zones: [...]}
        let zones = Array.isArray(data) ? data : (data.zones || []);
        // Filter by detected zone count (server already filters, but belt-and-suspenders)
        const maxZ = window._mgmtDetectedZoneCount || 0;
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

    const parts = [];
    if (years)  parts.push({ val: years,  label: years === 1 ? 'yr' : 'yrs' });
    if (months) parts.push({ val: months, label: months === 1 ? 'mo' : 'mos' });
    if (weeks)  parts.push({ val: weeks,  label: weeks === 1 ? 'wk' : 'wks' });
    if (days)   parts.push({ val: days,   label: days === 1 ? 'day' : 'days' });
    parts.push({ val: hours, label: 'hrs' });
    parts.push({ val: mins,  label: 'min' });

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
    if (val >= -50)      { label = 'Great'; color = '#1a7a1a'; }
    else if (val >= -60) { label = 'Good';  color = '#3a9a2a'; }
    else if (val >= -70) { label = 'Poor';  color = '#d4930a'; }
    else                 { label = 'Bad';   color = '#cc2222'; }
    return ' <span style="font-weight:600;color:' + color + ';">(' + label + ')</span>';
}

// --- Detail: Sensors ---
let _mgmtSensorGridBuilt = false;
async function loadDetailSensors(id) {
    const el = document.getElementById('detailSensors');
    try {
        const data = await api('/customers/' + id + '/sensors');
        const allSensors = Array.isArray(data) ? data : (data.sensors || []);

        // Extract rain and expansion sensor entities into their own cards
        window._rainSensors = allSensors.filter(s => isRainEntity(s.entity_id));
        window._expansionSensors = allSensors.filter(s => isExpansionEntity(s.entity_id));
        mgmtRenderRainSensorCard(id);
        mgmtRenderExpansionCard(id);

        // Regular sensors (exclude rain + expansion)
        const sensors = allSensors.filter(s => !isRainEntity(s.entity_id) && !isExpansionEntity(s.entity_id));
        if (sensors.length === 0) { el.innerHTML = '<div class="empty-state"><p>No sensors found</p></div>'; _mgmtSensorGridBuilt = false; return; }

        const eids = sensors.map(s => s.entity_id).sort().join(',');
        const gridExists = _mgmtSensorGridBuilt && el.querySelector('.tile-grid');
        if (!gridExists || el.getAttribute('data-eids') !== eids) {
            el.innerHTML = '<div class="tile-grid">' + sensors.map(s => {
                const eid = esc(s.entity_id);
                return '<div class="tile" data-eid="' + eid + '">' +
                    '<div class="tile-name">' + esc(cleanSensorName(s)) + '</div>' +
                    '<div class="tile-value">' + renderSensorValue(s) + '</div>' +
                '</div>';
            }).join('') + '</div>';
            el.setAttribute('data-eids', eids);
            _mgmtSensorGridBuilt = true;
        } else {
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
        _mgmtSensorGridBuilt = false;
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

// --- Detail: Device Controls (also populates Schedule card) ---
async function loadDetailControls(id) {
    const controlsEl = document.getElementById('detailControls');
    const scheduleEl = document.getElementById('detailSchedule');
    try {
        const [data, durData, multData] = await Promise.all([
            api('/customers/' + id + '/entities'),
            api('/customers/' + id + '/moisture/durations').catch(() => ({})),
            api('/customers/' + id + '/moisture/multiplier').catch(() => ({ combined_multiplier: 1.0, weather_multiplier: 1.0, moisture_multiplier: 1.0 })),
        ]);
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

        // Extract rain and expansion control entities into their own cards
        const rainControls = controlEntities.filter(e => isRainEntity(e.entity_id));
        const expansionControls = controlEntities.filter(e => isExpansionEntity(e.entity_id));
        const regularControls = controlEntities.filter(e => !isRainEntity(e.entity_id) && !isExpansionEntity(e.entity_id));
        window._rainControls = rainControls;
        window._expansionControls = expansionControls;
        mgmtRenderRainSensorCard(id);
        mgmtRenderExpansionCard(id);

        // Detect zone count from expansion sensor for zone filtering
        window._mgmtDetectedZoneCount = 0;
        const expansionSensors = (window._expansionSensors || []);
        for (const es of expansionSensors) {
            if (/detected_zones/i.test(es.entity_id) && es.state) {
                const czm = es.state.match(/(\\d+)\\s*zones?/i);
                if (czm) window._mgmtDetectedZoneCount = parseInt(czm[1]);
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
        var aaEl = document.getElementById('mgmtAutoAdvanceToggle');
        if (autoAdvanceEntity && aaEl) {
            var aaOn = autoAdvanceEntity.state === 'on';
            aaEl.style.display = '';
            aaEl.innerHTML = '<div style="display:flex;align-items:center;gap:8px;">' +
                '<span style="font-size:13px;color:var(--text-secondary);">Auto Advance</span>' +
                '<button class="btn ' + (aaOn ? 'btn-primary' : 'btn-secondary') + ' btn-sm" ' +
                'onclick="setEntityValue(\\'' + currentCustomerId + '\\',\\'' + autoAdvanceEntity.entity_id + '\\',\\'switch\\',' +
                '{state:\\'' + (aaOn ? 'off' : 'on') + '\\'});setTimeout(function(){loadDetailControls(currentCustomerId)},500)">' +
                (aaOn ? 'On' : 'Off') + '</button></div>';
        } else if (aaEl) {
            aaEl.style.display = 'none';
        }

        // Render Device Controls (excluding rain + expansion)
        if (regularControls.length === 0) {
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
        renderScheduleCard(id, scheduleByCategory, durData, multData);

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

// --- Rain Sensor Card (Management) ---
function mgmtRenderRainSensorCard(custId) {
    const card = document.getElementById('detailRainSensorCard');
    const body = document.getElementById('detailRainSensorCardBody');
    const badge = document.getElementById('detailRainStatusBadge');
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
            'onclick="setEntityValue(\\'' + custId + '\\',\\'' + enabledEntity.entity_id + '\\',\\'switch\\',' +
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
            '<select id="sel_mgmt_rain_type" style="padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">' + optionsHtml + '</select>' +
            '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + typeEntity.entity_id + '\\',\\'select\\',{option:document.getElementById(\\'sel_mgmt_rain_type\\').value})">Set</button>' +
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
            'onclick="setEntityValue(\\'' + custId + '\\',\\'' + delayEnabledEntity.entity_id + '\\',\\'switch\\',' +
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
            '<input type="number" id="num_mgmt_rain_delay" value="' + esc(delayHoursEntity.state) + '" min="' + min + '" max="' + max + '" step="' + step + '" style="width:60px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);">' +
            '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + delayHoursEntity.entity_id + '\\',\\'number\\',{value:parseFloat(document.getElementById(\\'num_mgmt_rain_delay\\').value)})">Set</button>' +
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

// --- Expansion Board Card (Management) ---
function mgmtRenderExpansionCard(custId) {
    const card = document.getElementById('detailExpansionCard');
    const body = document.getElementById('detailExpansionCardBody');
    const badge = document.getElementById('detailExpansionStatusBadge');
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
            '<button class="btn btn-secondary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + rescanEntity.entity_id + '\\',\\'button\\',{})">&#128260; Rescan Expansion Boards</button>' +
            '</div>';
    }

    body.innerHTML = html;
}

function renderScheduleCard(custId, sched, durData, multData) {
    const el = document.getElementById('detailSchedule');
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
            'onclick="setEntityValue(\\'' + custId + '\\',\\'' + se.entity_id + '\\',\\'switch\\',' +
            '{state:\\'' + (isOn ? 'off' : 'on') + '\\'})">' +
            (isOn ? 'Disable Schedule' : 'Enable Schedule') + '</button>' +
            '</div></div>';
    }

    // --- Apply Factors Toggle (rendered inline from durData) ---
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
        'onclick="mgmtToggleApplyFactors(' + !afOn + ')">' +
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
        var sortedZones = Object.keys(zoneMap).sort(function(a, b) {
            // Normal zones first, Pump Start Relay / Master Valve last
            var aMode = (zoneMap[a].mode && zoneMap[a].mode.state || '').toLowerCase();
            var bMode = (zoneMap[b].mode && zoneMap[b].mode.state || '').toLowerCase();
            var aSpecial = /pump|master|relay/.test(aMode) ? 1 : 0;
            var bSpecial = /pump|master|relay/.test(bMode) ? 1 : 0;
            if (aSpecial !== bSpecial) return aSpecial - bSpecial;
            return parseInt(a) - parseInt(b);
        });
        // Filter by detected zone count (expansion board limit)
        const maxZones = window._mgmtDetectedZoneCount || 0;
        if (maxZones > 0) {
            sortedZones = sortedZones.filter(function(zn) { return parseInt(zn) <= maxZones; });
        }
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
                if (adj && adj.skip) {
                    // Factors applied and skip triggered — show skip badge
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
                }
                html += '<td style="white-space:nowrap;"><input type="number" id="' + inputId + '" value="' + esc(baseVal) + '" ' +
                    'min="' + (attrs.min || 0) + '" max="' + (attrs.max || 999) + '" step="' + (attrs.step || 1) + '" ' +
                    'style="width:70px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;background:var(--bg-input);color:var(--text-primary);"> ' +
                    esc(unit) + ' ' +
                    '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid +
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

function cleanEntityName(friendlyName, entityId) {
    // HA often appends the device name to entity friendly names, e.g.
    // "Irrigation System Restart irrigation_controller" — strip it
    if (!friendlyName) return entityId || 'Unknown';
    const parts = friendlyName.split(' ');
    const last = parts[parts.length - 1];
    if (parts.length > 1 && last.includes('_') && entityId && entityId.includes(last)) {
        return parts.slice(0, -1).join(' ');
    }
    return friendlyName;
}

function renderControlTile(custId, e) {
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
            '<div class="tile-actions">' +
                '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + custId + '\\',\\'' + eid + '\\',\\'button\\',{})">PRESS</button>' +
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
        setTimeout(() => { loadDetailControls(custId); loadDetailSensors(custId); }, 1000);
    } catch (e) { showToast(e.message, 'error'); }
}

// --- Detail: History ---
async function loadDetailHistory(id) {
    const el = document.getElementById('detailHistory');
    try {
        const hoursRaw = document.getElementById('mgmtHistoryRange') ? document.getElementById('mgmtHistoryRange').value : '24';
        const hours = parseInt(hoursRaw, 10) || 24;
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

        // Determine if any event has probe (moisture) data — show column only if so
        const hasProbeData = events.some(e => e.moisture && e.moisture.moisture_multiplier != null);

        el.innerHTML = weatherSummary +
            '<table style="width:100%;font-size:13px;border-collapse:collapse;"><thead><tr style="text-align:left;border-bottom:2px solid var(--border-light);color:var(--text-muted);"><th style="padding:6px;">Zone</th><th style="padding:6px;">State</th><th style="padding:6px;">Time</th><th style="padding:6px;">Duration</th><th style="padding:6px;">Moisture Factor</th>' +
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
                // Moisture Factor column — moisture probe value for schedule-triggered events
                let mFactorCell = '<span style="color:var(--text-disabled);">—</span>';
                if (e.source === 'schedule' || e.source === 'moisture_cutoff') {
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
                        // Show sensor readings (T/M/B) if available
                        const sr = mo.sensor_readings || {};
                        const parts = [];
                        if (sr.T != null) parts.push('T:' + sr.T + '%');
                        if (sr.M != null) parts.push('M:' + sr.M + '%');
                        if (sr.B != null) parts.push('B:' + sr.B + '%');
                        if (parts.length > 0) {
                            mFactorCell += '<div style="font-size:10px;color:var(--text-muted);margin-top:1px;">' + parts.join(' ') + '</div>';
                        }
                    } else {
                        // No probe data — show weather factor as fallback
                        const wMult = wx.watering_multiplier != null ? wx.watering_multiplier : null;
                        if (wMult != null) {
                            const fc = wMult === 1.0 ? 'var(--color-success)' : wMult < 1 ? 'var(--color-warning)' : 'var(--color-danger)';
                            mFactorCell = '<span style="color:' + fc + ';font-weight:600;">' + wMult + 'x</span>';
                            mFactorCell += '<div style="font-size:10px;color:var(--text-muted);">weather</div>';
                        }
                    }
                }
                const srcLabel = e.source && e.source !== 'schedule' ? '<div style="font-size:10px;color:var(--text-placeholder);">' + esc(e.source) + '</div>' : '';
                // State display: handle skip events
                let stateCell;
                if (e.state === 'skip') {
                    stateCell = '<span style="color:var(--color-danger);font-weight:600;">Skipped</span><br><span style="color:var(--text-disabled);font-size:11px;">OFF</span>';
                } else if (e.state === 'on' || e.state === 'open') {
                    stateCell = '<span style="color:var(--color-success);">ON</span>';
                } else {
                    stateCell = '<span style="color:var(--text-disabled);">OFF</span>';
                }
                return `<tr style="border-bottom:1px solid var(--border-row);${e.state === 'skip' ? 'opacity:0.7;' : ''}">
                <td style="padding:6px;">${esc(resolveZoneName(e.entity_id, e.zone_name))}${srcLabel}</td>
                <td style="padding:6px;">${stateCell}</td>
                <td style="padding:6px;">${formatTime(e.timestamp)}</td>
                <td style="padding:6px;">${e.duration_seconds ? Math.round(e.duration_seconds / 60) + ' min' : '-'}</td>
                <td style="padding:6px;font-size:12px;">${mFactorCell}</td>
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

// --- Issue Management ---
const SEV_COLORS = {severe: '#e74c3c', annoyance: '#f39c12', clarification: '#3498db'};
const SEV_LABELS = {severe: 'Severe Issue', annoyance: 'Annoyance', clarification: 'Clarification'};
const ISSUE_STATUS_LABELS = {open: 'Open', acknowledged: 'Acknowledged', scheduled: 'Service Scheduled', resolved: 'Resolved'};
let _ackCustId = null, _ackIssueId = null;

function updateAlertBadge(customers) {
    let totalActive = 0;
    let maxSev = null;
    const sevOrder = {severe: 3, annoyance: 2, clarification: 1};
    customers.forEach(function(c) {
        if (c.issue_summary && c.issue_summary.active_count > 0) {
            totalActive += c.issue_summary.active_count;
            if (!maxSev || (sevOrder[c.issue_summary.max_severity] || 0) > (sevOrder[maxSev] || 0)) {
                maxSev = c.issue_summary.max_severity;
            }
        }
    });
    const btn = document.getElementById('alertBadgeBtn');
    const count = document.getElementById('alertBadgeCount');
    if (totalActive > 0) {
        btn.style.display = 'inline-flex';
        count.textContent = totalActive;
        count.style.background = SEV_COLORS[maxSev] || '#e74c3c';
    } else {
        btn.style.display = 'none';
    }
}

function showAlertsPanel() {
    loadAlertsPanel();
    document.getElementById('alertsPanelModal').style.display = 'flex';
}
function closeAlertsPanel() {
    document.getElementById('alertsPanelModal').style.display = 'none';
}

function loadAlertsPanel() {
    const el = document.getElementById('alertsPanelContent');
    const customersWithIssues = allCustomers.filter(function(c) {
        return c.issue_summary && c.issue_summary.active_count > 0;
    });
    if (customersWithIssues.length === 0) {
        el.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:32px;">No active issues across any properties.</div>';
        return;
    }
    let html = '';
    customersWithIssues.forEach(function(c) {
        const issues = c.issue_summary.issues || [];
        html += '<div style="margin-bottom:20px;">';
        html += '<div style="font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:8px;cursor:pointer;text-decoration:underline;" onclick="closeAlertsPanel();viewCustomer(\\'' + c.id + '\\')">' + esc(c.name) + '</div>';
        issues.forEach(function(issue) {
            const color = SEV_COLORS[issue.severity] || '#999';
            const dt = new Date(issue.created_at);
            const now = new Date();
            const diffMs = now - dt;
            const diffH = Math.floor(diffMs / 3600000);
            const timeAgo = diffH < 1 ? 'Just now' : diffH < 24 ? diffH + 'h ago' : Math.floor(diffH / 24) + 'd ago';
            html += '<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-light);">';
            html += '<span style="display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;background:' + color + '22;color:' + color + ';white-space:nowrap;">' + esc(SEV_LABELS[issue.severity] || issue.severity) + '</span>';
            html += '<div style="flex:1;min-width:0;">';
            html += '<div style="font-size:13px;color:var(--text-primary);word-break:break-word;">' + esc(issue.description) + '</div>';
            html += '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">' + esc(timeAgo) + ' &middot; ' + esc(ISSUE_STATUS_LABELS[issue.status] || issue.status) + '</div>';
            html += '</div>';
            html += '<div style="display:flex;gap:4px;flex-shrink:0;">';
            if (issue.status === 'open') {
                html += '<button class="btn btn-primary btn-sm" onclick="openAckModal(\\'' + c.id + '\\', \\'' + issue.id + '\\')">Acknowledge</button>';
            }
            if (issue.status !== 'resolved') {
                html += '<button class="btn btn-secondary btn-sm" onclick="resolveIssueFromPanel(\\'' + c.id + '\\', \\'' + issue.id + '\\')">Resolve</button>';
            }
            html += '</div></div>';
        });
        html += '</div>';
    });
    el.innerHTML = html;
}

// --- Detail View Issues ---
async function loadDetailIssues(custId) {
    const card = document.getElementById('detailIssuesCard');
    const body = document.getElementById('detailIssuesBody');
    const badge = document.getElementById('detailIssuesBadge');
    try {
        const data = await api('/customers/' + custId + '/issues/active');
        const issues = data.issues || [];
        if (issues.length === 0) {
            card.style.display = 'none';
            return;
        }
        card.style.display = 'block';
        badge.textContent = issues.length;
        badge.style.display = 'inline';
        let html = '';
        issues.forEach(function(issue) {
            const color = SEV_COLORS[issue.severity] || '#999';
            const dt = new Date(issue.created_at);
            const timeStr = dt.toLocaleDateString(undefined, {month:'short', day:'numeric'}) + ' ' + dt.toLocaleTimeString(undefined, {hour:'numeric', minute:'2-digit'});
            html += '<div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--border-light);">';
            html += '<span style="display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;background:' + color + '22;color:' + color + ';white-space:nowrap;">' + esc(SEV_LABELS[issue.severity] || issue.severity) + '</span>';
            html += '<div style="flex:1;min-width:0;">';
            html += '<div style="font-size:13px;color:var(--text-primary);word-break:break-word;">' + esc(issue.description) + '</div>';
            html += '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">' + esc(timeStr) + ' &middot; ' + esc(ISSUE_STATUS_LABELS[issue.status] || issue.status) + '</div>';
            if (issue.management_note) {
                html += '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;padding:4px 8px;background:var(--bg-tile);border-radius:4px;">&#128172; ' + esc(issue.management_note) + '</div>';
            }
            if (issue.service_date) {
                html += '<div style="font-size:12px;color:var(--color-success);margin-top:2px;">&#128197; Service: ' + esc(issue.service_date) + '</div>';
            }
            html += '</div>';
            html += '<div style="display:flex;gap:4px;flex-shrink:0;">';
            if (issue.status === 'open') {
                html += '<button class="btn btn-primary btn-sm" onclick="openAckModal(\\'' + custId + '\\', \\'' + issue.id + '\\')">Acknowledge</button>';
            } else if (issue.status === 'acknowledged' || issue.status === 'scheduled') {
                html += '<button class="btn btn-secondary btn-sm" onclick="openAckModal(\\'' + custId + '\\', \\'' + issue.id + '\\')">Update</button>';
            }
            if (issue.status !== 'resolved') {
                html += '<button class="btn btn-secondary btn-sm" onclick="resolveIssue(\\'' + custId + '\\', \\'' + issue.id + '\\')">Resolve</button>';
            }
            html += '</div></div>';
        });
        body.innerHTML = html;
    } catch (e) {
        card.style.display = 'none';
    }
}

// --- Acknowledge Modal ---
function openAckModal(custId, issueId) {
    _ackCustId = custId;
    _ackIssueId = issueId;
    document.getElementById('ackNote').value = '';
    document.getElementById('ackServiceDate').value = '';
    // Set min date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('ackServiceDate').min = today;
    // Show issue details
    const cust = allCustomers.find(function(c) { return c.id === custId; });
    let issueDetail = '';
    if (cust && cust.issue_summary && cust.issue_summary.issues) {
        const issue = cust.issue_summary.issues.find(function(i) { return i.id === issueId; });
        if (issue) {
            const color = SEV_COLORS[issue.severity] || '#999';
            issueDetail = '<div style="padding:10px;border-radius:8px;background:var(--bg-tile);margin-bottom:12px;">';
            issueDetail += '<span style="display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;background:' + color + '22;color:' + color + ';">' + esc(SEV_LABELS[issue.severity] || issue.severity) + '</span>';
            issueDetail += '<div style="font-size:13px;color:var(--text-primary);margin-top:6px;">' + esc(issue.description) + '</div>';
            issueDetail += '</div>';
        }
    }
    document.getElementById('ackIssueDetails').innerHTML = issueDetail;
    document.getElementById('ackModal').style.display = 'flex';
}
function closeAckModal() {
    document.getElementById('ackModal').style.display = 'none';
    _ackCustId = null;
    _ackIssueId = null;
}

async function submitAcknowledge() {
    if (!_ackCustId || !_ackIssueId) return;
    const btn = document.getElementById('ackSubmitBtn');
    btn.disabled = true;
    btn.textContent = 'Saving...';
    try {
        const body = {};
        const note = document.getElementById('ackNote').value.trim();
        const serviceDate = document.getElementById('ackServiceDate').value;
        if (note) body.note = note;
        if (serviceDate) body.service_date = serviceDate;
        await api('/customers/' + _ackCustId + '/issues/' + _ackIssueId + '/acknowledge', {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(body),
        });
        showToast('Issue acknowledged');
        closeAckModal();
        if (currentCustomerId) loadDetailIssues(currentCustomerId);
        loadCustomers();
    } catch (e) {
        showToast(e.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Acknowledge';
    }
}

async function resolveIssue(custId, issueId) {
    if (!confirm('Mark this issue as resolved?')) return;
    try {
        await api('/customers/' + custId + '/issues/' + issueId + '/resolve', {
            method: 'PUT',
        });
        showToast('Issue resolved');
        if (currentCustomerId) loadDetailIssues(currentCustomerId);
        loadCustomers();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

async function resolveIssueFromPanel(custId, issueId) {
    if (!confirm('Mark this issue as resolved?')) return;
    try {
        await api('/customers/' + custId + '/issues/' + issueId + '/resolve', {
            method: 'PUT',
        });
        showToast('Issue resolved');
        loadCustomers();
        loadAlertsPanel();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

// --- Browser Notifications ---
function checkForNewIssues(customers) {
    if (typeof Notification === 'undefined') return;
    if (Notification.permission !== 'granted') return;
    const prefs = JSON.parse(localStorage.getItem('flux_notification_prefs') || '{"severe":true,"annoyance":true,"clarification":false}');
    const lastKnown = JSON.parse(localStorage.getItem('flux_last_known_issues') || '{}');
    const newKnown = {};
    customers.forEach(function(c) {
        const summary = c.issue_summary;
        const currentIds = (summary && summary.issues) ? summary.issues.map(function(i) { return i.id; }) : [];
        newKnown[c.id] = {count: currentIds.length, ids: currentIds};
        const prev = lastKnown[c.id];
        if (!prev) return;  // First load — don't spam notifications
        const prevIds = prev.ids || [];
        if (summary && summary.issues) {
            summary.issues.forEach(function(issue) {
                if (prevIds.indexOf(issue.id) === -1 && prefs[issue.severity]) {
                    try {
                        new Notification('New Issue: ' + esc(c.name), {
                            body: (SEV_LABELS[issue.severity] || issue.severity) + ': ' + (issue.description || '').substring(0, 100),
                            icon: '&#9888;',
                            tag: 'flux-issue-' + issue.id,
                        });
                    } catch (e) { /* notification failed */ }
                }
            });
        }
    });
    localStorage.setItem('flux_last_known_issues', JSON.stringify(newKnown));
}

// --- Notification Preferences ---
function showNotifPrefs() {
    const prefs = JSON.parse(localStorage.getItem('flux_notification_prefs') || '{"severe":true,"annoyance":true,"clarification":false}');
    document.getElementById('notifSevere').checked = !!prefs.severe;
    document.getElementById('notifAnnoyance').checked = !!prefs.annoyance;
    document.getElementById('notifClarification').checked = !!prefs.clarification;
    const statusEl = document.getElementById('notifPermStatus');
    if (typeof Notification !== 'undefined') {
        statusEl.textContent = 'Browser notification permission: ' + Notification.permission;
    } else {
        statusEl.textContent = 'Browser notifications not supported';
    }
    // Load HA notification settings from server
    loadHANotifSettings();
    document.getElementById('notifPrefsModal').style.display = 'flex';
}
function closeNotifPrefs() {
    document.getElementById('notifPrefsModal').style.display = 'none';
}
function saveNotifPrefs() {
    const prefs = {
        severe: document.getElementById('notifSevere').checked,
        annoyance: document.getElementById('notifAnnoyance').checked,
        clarification: document.getElementById('notifClarification').checked,
    };
    localStorage.setItem('flux_notification_prefs', JSON.stringify(prefs));
    showToast('Notification preferences saved');
    closeNotifPrefs();
}
function requestNotifPermission() {
    if (typeof Notification === 'undefined') {
        showToast('Browser notifications not supported', 'error');
        return;
    }
    Notification.requestPermission().then(function(perm) {
        document.getElementById('notifPermStatus').textContent = 'Browser notification permission: ' + perm;
        if (perm === 'granted') showToast('Notifications enabled');
        else showToast('Notification permission ' + perm, 'error');
    });
}

// --- HA Notification Settings ---
async function loadNotifyServices() {
    var sel = document.getElementById('haNotifyService');
    var saved = sel.value;
    var hint = document.getElementById('haNotifyServiceHint');
    hint.textContent = 'Loading services from Home Assistant...';
    try {
        var data = await api('/notification-settings/services');
        var services = data.services || [];
        // Keep the first placeholder option, clear the rest
        sel.innerHTML = '<option value="">-- Select a notify service --</option>';
        services.forEach(function(s) {
            var opt = document.createElement('option');
            opt.value = s.id;
            opt.textContent = s.name + ' (notify.' + s.id + ')';
            sel.appendChild(opt);
        });
        // Restore previously saved value
        if (saved) sel.value = saved;
        // If saved value not in list, add it as a custom option so it's not lost
        if (saved && sel.value !== saved) {
            var opt = document.createElement('option');
            opt.value = saved;
            opt.textContent = saved + ' (saved)';
            sel.appendChild(opt);
            sel.value = saved;
        }
        hint.textContent = services.length ? services.length + ' service(s) found' : 'No notify services found in HA';
    } catch (e) {
        hint.textContent = 'Could not load services — you can type a name manually';
    }
}
async function loadHANotifSettings() {
    try {
        var data = await api('/notification-settings');
        document.getElementById('haNotifEnabled').checked = !!data.enabled;
        document.getElementById('haNotifSevere').checked = !!data.notify_severe;
        document.getElementById('haNotifAnnoyance').checked = !!data.notify_annoyance;
        document.getElementById('haNotifClarification').checked = !!data.notify_clarification;
        document.getElementById('haNotifStatus').textContent = '';
        // Load services dropdown, then set the saved value
        await loadNotifyServices();
        if (data.ha_notify_service) {
            var sel = document.getElementById('haNotifyService');
            sel.value = data.ha_notify_service;
            // If saved value not in dropdown, add it
            if (sel.value !== data.ha_notify_service) {
                var opt = document.createElement('option');
                opt.value = data.ha_notify_service;
                opt.textContent = data.ha_notify_service + ' (saved)';
                sel.appendChild(opt);
                sel.value = data.ha_notify_service;
            }
        }
    } catch (e) {
        document.getElementById('haNotifStatus').textContent = 'Could not load HA notification settings';
    }
}
async function saveHANotifSettings() {
    var payload = {
        enabled: document.getElementById('haNotifEnabled').checked,
        ha_notify_service: document.getElementById('haNotifyService').value.trim(),
        notify_severe: document.getElementById('haNotifSevere').checked,
        notify_annoyance: document.getElementById('haNotifAnnoyance').checked,
        notify_clarification: document.getElementById('haNotifClarification').checked,
    };
    if (payload.enabled && !payload.ha_notify_service) {
        showToast('Please select a notify service', 'error');
        return;
    }
    try {
        await api('/notification-settings', { method: 'PUT', body: JSON.stringify(payload) });
        showToast('HA notification settings saved');
        document.getElementById('haNotifStatus').textContent = 'Settings saved';
    } catch (e) {
        showToast('Failed to save HA notification settings', 'error');
    }
}
async function testHANotification() {
    var svc = document.getElementById('haNotifyService').value.trim();
    if (!svc) {
        showToast('Select a notify service first', 'error');
        return;
    }
    // Save first so the test uses current values
    await saveHANotifSettings();
    try {
        const result = await api('/notification-settings/test', { method: 'POST' });
        showToast(result.message || 'Test notification sent');
        document.getElementById('haNotifStatus').textContent = 'Test sent successfully';
    } catch (e) {
        const msg = (e.message || '').replace('Error: ', '');
        showToast('Test failed: ' + msg, 'error');
        document.getElementById('haNotifStatus').textContent = 'Test failed — check service name';
    }
}

// --- Help Modal ---
const HELP_CONTENT = `
<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:0 0 8px 0;">Dashboard Overview</h4>
<p style="margin-bottom:10px;">The Management Dashboard lets you monitor and control irrigation systems across multiple properties from a single interface. Each property is a homeowner who has shared their connection key with you.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Adding Properties</h4>
<p style="margin-bottom:10px;">To add a property, click <strong>+ Add Property</strong> and either paste the connection key or scan the homeowner's QR code. The key is generated from their Flux Open Home Irrigation Control add-on's Configuration page.</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Paste key</strong> — Paste the connection key directly into the text area</li>
<li style="margin-bottom:4px;"><strong>Scan QR Code</strong> — Click the 📷 Scan QR Code button to open your camera and scan the homeowner's QR code. The connection key will be filled in automatically</li>
<li style="margin-bottom:4px;">The key is automatically decoded to preview the property name, address, and connection type</li>
<li style="margin-bottom:4px;">You can optionally set a custom display name and notes</li>
<li style="margin-bottom:4px;">Click <strong>Connect</strong> to add the property to your dashboard</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Connection keys contain the URL, API key, and property details. You don't need to configure anything else.</div>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">📷 QR scanning requires camera access. Your browser or Home Assistant app may ask for camera permission the first time you use it.</div>

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

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Clickable Addresses</h4>
<p style="margin-bottom:10px;">Property addresses on both the card list and detail view are clickable. <strong>Click an address</strong> to open it in your default maps application (Apple Maps on iOS/Mac, Google Maps on other devices). This makes it easy to get directions to a property.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Property Detail View</h4>
<p style="margin-bottom:10px;">Click a property card to see its full details including zone controls, sensors, schedule, weather, and run history. Use the <strong>← Back</strong> button to return to the property list.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Remote Zone Control</h4>
<p style="margin-bottom:10px;">From the detail view, you can remotely control any irrigation zone. Zones are displayed as "Zone 1", "Zone 2", etc. by default — use aliases to give them friendly names. Controls include:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Start</strong> — Turn on a zone (optionally set a timed run in minutes)</li>
<li style="margin-bottom:4px;"><strong>Stop</strong> — Turn off a specific zone</li>
<li style="margin-bottom:4px;"><strong>🛑 Stop All Zones</strong> — Emergency stop for all zones at once</li>
<li style="margin-bottom:4px;"><strong>⏸ Pause / ▶ Resume</strong> — Pause or resume the entire irrigation system</li>
<li style="margin-bottom:4px;"><strong>Auto Advance</strong> — Toggle at the top of the zone card. To run all enabled zones sequentially: start the first zone with a timed run, then click Auto Advance to enable it. Each zone will automatically advance to the next enabled zone when its timer expires. Turn Auto Advance off at any time to stop the sequence after the current zone finishes.</li>
</ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 When the system is paused, any zone that turns on (even from an ESPHome schedule) will be immediately shut off. If expansion boards are detected, only the physically connected zones are shown — extra pre-created entities are automatically hidden.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Schedule Management</h4>
<p style="margin-bottom:10px;">View and manage watering schedules for each property:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Days</strong> — Select which days of the week to water</li>
<li style="margin-bottom:4px;"><strong>Start Times</strong> — Set one or more daily start times</li>
<li style="margin-bottom:4px;"><strong>Zone Durations</strong> — Configure how long each zone runs (in minutes)</li>
<li style="margin-bottom:4px;"><strong>Enable/Disable</strong> — Toggle the schedule on or off without deleting it</li>
<li style="margin-bottom:4px;"><strong>Apply Factors to Schedule</strong> — When enabled, automatically adjusts ESPHome run durations using the combined watering factor (weather &times; moisture). The input field shows the base duration (what the user sets), and a badge next to it shows the adjusted duration and factor (e.g. &quot;24 min (0.80x)&quot;). The base is what you control; the adjusted value is what the controller actually runs. Durations update automatically as conditions change and restore to originals when disabled. Even when this toggle is OFF, a preview badge shows what the projected duration would be given the current combined factor.</li>
</ul>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Weather Rules</h4>
<p style="margin-bottom:10px;">If the homeowner has configured weather integration, you can view and manage weather-based watering adjustments. The Weather Rules section is collapsed by default — click the header to expand. Action buttons (Test, Export, Clear) remain visible when collapsed.</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Rain Skip</strong> — Skip watering when rain is detected or forecasted</li>
<li style="margin-bottom:4px;"><strong>Wind Delay</strong> — Delay watering during high winds</li>
<li style="margin-bottom:4px;"><strong>Temperature Adjustments</strong> — Increase or decrease watering based on temperature</li>
<li style="margin-bottom:4px;"><strong>Watering Multiplier</strong> — The weather-adjusted multiplier applied to run times</li>
</ul>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Gophr Moisture Probes</h4>
<p style="margin-bottom:10px;">View live soil moisture data, configure settings, and manage duration adjustments for properties with Gophr moisture probes. The algorithm uses a <strong>gradient-based approach</strong> where each sensor depth serves a distinct role:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Mid sensor (root zone)</strong> — PRIMARY decision driver for watering needs</li>
<li style="margin-bottom:4px;"><strong>Shallow sensor</strong> — Rain detection: wet surface + rain forecast = recent rainfall, reduces/skips watering</li>
<li style="margin-bottom:4px;"><strong>Deep sensor</strong> — Over-irrigation guard: saturated deep soil triggers reduction</li>
<li style="margin-bottom:4px;"><strong>Device status</strong> — WiFi signal strength, battery level, and sleep duration are shown below the moisture bars when available</li>
<li style="margin-bottom:4px;"><strong>Zone assignment</strong> — Click "Edit Zones" on a probe card to assign or reassign zones to the probe</li>
<li style="margin-bottom:4px;"><strong>Settings</strong> — Root zone thresholds (Skip, Wet, Optimal, Dry), max increase/decrease, and rain detection sensitivity</li>
</ul>

<p style="margin-bottom:6px;font-weight:600;font-size:13px;">Moisture Multiplier Formula</p>
<p style="margin-bottom:6px;font-size:13px;">The base multiplier is calculated from the <strong>mid (root zone)</strong> sensor reading against four configurable thresholds (defaults shown):</p>
<table style="width:100%;font-size:12px;border-collapse:collapse;margin-bottom:8px;">
<tr style="border-bottom:1px solid var(--border-light);"><th style="text-align:left;padding:4px 6px;">Root Zone Reading</th><th style="text-align:left;padding:4px 6px;">Multiplier</th><th style="text-align:left;padding:4px 6px;">Behavior</th></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">&ge; Skip (80%)</td><td style="padding:4px 6px;font-weight:600;color:var(--color-danger);">0.0x &mdash; Skip</td><td style="padding:4px 6px;">Soil saturated, no watering</td></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Wet (65%) &ndash; Skip (80%)</td><td style="padding:4px 6px;">0.50x &rarr; 0.0x</td><td style="padding:4px 6px;">Linear reduction as moisture increases</td></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Optimal (45%) &ndash; Wet (65%)</td><td style="padding:4px 6px;">1.0x &rarr; 0.50x</td><td style="padding:4px 6px;">Gradual reduction approaching wet</td></tr>
<tr style="border-bottom:1px solid var(--border-light);"><td style="padding:4px 6px;">Dry (30%) &ndash; Optimal (45%)</td><td style="padding:4px 6px;">1.25x &rarr; 1.0x</td><td style="padding:4px 6px;">Slight increase as soil dries</td></tr>
<tr><td style="padding:4px 6px;">&lt; Dry (30%)</td><td style="padding:4px 6px;font-weight:600;color:var(--color-danger);">1.50x</td><td style="padding:4px 6px;">Critically dry, maximum increase</td></tr>
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
<p style="margin-bottom:6px;font-size:13px;">The final multiplier is calculated as: <strong>Base (root zone) &times; Rain adjustment &times; Deep guard</strong>. For zones with multiple probes, the most conservative (lowest) multiplier is used. If any probe triggers skip, the zone is skipped.</p>
<p style="margin-bottom:10px;font-size:13px;"><strong>Combined watering factor</strong> = Weather Multiplier &times; Moisture Multiplier. This combined factor is applied per-zone to run durations. Only zones with mapped probes are affected by moisture &mdash; unmapped zones use weather-only.</p>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Probe device selection and sensor mapping are configured from the homeowner's Configuration page. The management dashboard controls settings, thresholds, zone assignments, and duration adjustments. Gophr devices sleep between readings — while asleep, the system uses the last known good sensor values so the moisture multiplier stays active. If cached readings become older than the Stale Reading Threshold, they are treated as stale and the multiplier reverts to neutral (1.0x).</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Rain Sensor</h4>
<p style="margin-bottom:10px;">If the customer's irrigation controller has a rain sensor connected, a dedicated Rain Sensor card appears in the detail view showing:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Status</strong> — Current state: Dry (green), Rain Detected (red), Rain Delay (yellow), or Disabled (gray)</li><li style="margin-bottom:4px;"><strong>Rain Sensor Enable</strong> — Toggle rain sensor monitoring</li><li style="margin-bottom:4px;"><strong>Sensor Type</strong> — NC (Normally Closed) or NO (Normally Open) to match hardware wiring</li><li style="margin-bottom:4px;"><strong>Rain Delay</strong> — Enable/disable rain delay and configure duration (1-72 hours)</li><li style="margin-bottom:4px;"><strong>Rain Delay Active</strong> — Whether rain delay is currently in effect</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">&#128161; The rain sensor card only appears when rain sensor entities are detected on the customer's controller.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Expansion Boards</h4>
<p style="margin-bottom:10px;">For controllers with I2C expansion board support, the Expansion Boards card shows:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Zone Count</strong> — Total detected zones (base + expansion)</li><li style="margin-bottom:4px;"><strong>Board Details</strong> — I2C addresses and zone ranges for each expansion board</li><li style="margin-bottom:4px;"><strong>Rescan</strong> — Trigger an I2C bus rescan to detect board changes</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">&#128161; The firmware pre-creates entities for up to 32 zones (to support up to 3 expansion boards). The system automatically detects how many zones are physically connected and only shows those zones — zone tiles, schedule settings, enables, and durations are all filtered to match.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Run History</h4>
<p style="margin-bottom:10px;">View a detailed log of all irrigation activity for each property:</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;">Each entry shows the zone, start/stop time, duration, and source (API, schedule, manual, etc.)</li>
<li style="margin-bottom:4px;"><strong>Watering Factor</strong> — The weather-based multiplier for schedule-triggered runs</li>
<li style="margin-bottom:4px;"><strong>Probe Factor</strong> — The moisture probe multiplier with sensor readings (T=Top, M=Middle, B=Bottom) shown as percentages; only visible when probe data exists</li>
<li style="margin-bottom:4px;"><strong>Weather</strong> — Conditions at the time of each run with triggered rules</li>
<li style="margin-bottom:4px;"><strong>CSV Export</strong> — Download the run history as a spreadsheet (includes probe sensor readings and profile columns)</li>
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

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Customer Local Time</h4>
<p style="margin-bottom:10px;">The property detail view header shows the customer's local time in 12-hour format with timezone abbreviation (e.g., &quot;2:30 PM EST&quot;). The timezone is derived from the customer's state address field. This helps you know what time it is at the property when making schedule changes or troubleshooting.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Configuration Change Log</h4>
<p style="margin-bottom:10px;">Click the <strong>Log</strong> button in the property detail view to see all configuration changes made to that customer's system. Every entry shows the exact property changed with old and new values (e.g., &quot;Humidity Threshold (%): 80 -&gt; 90&quot;, &quot;Phone: (empty) -&gt; 555-1234&quot;). The log tracks who made each change (Homeowner or Management), when, and what category. Changes you make through this dashboard are automatically attributed to &quot;Management.&quot; Export to CSV for record-keeping. Up to 1,000 entries are stored per property.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Issue Reporting &amp; Alerts</h4>
<p style="margin-bottom:10px;">Homeowners can report issues directly from their dashboard. Issues appear in two places:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Alert Badge</strong> — The &#9888;&#65039; button in the header shows a count of all active issues across properties. Click it to see all issues in one panel.</li><li style="margin-bottom:4px;"><strong>Property Cards</strong> — Cards with active issues show a colored badge and border indicating the highest severity: <span style="color:#e74c3c;font-weight:600;">Red</span> = Severe, <span style="color:#f39c12;font-weight:600;">Amber</span> = Annoyance, <span style="color:#3498db;font-weight:600;">Blue</span> = Clarification.</li><li style="margin-bottom:4px;"><strong>Detail View</strong> — When viewing a property, the Issues card shows all active issues with full details and action buttons.</li></ul>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Acknowledging &amp; Scheduling Service</h4>
<p style="margin-bottom:10px;">For each issue, you can:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Acknowledge</strong> — Let the homeowner know you have seen their issue. You can add a note and optionally schedule a service date.</li><li style="margin-bottom:4px;"><strong>Schedule Service</strong> — Pick a date and the homeowner will see an &quot;Upcoming Service&quot; banner on their dashboard.</li><li style="margin-bottom:4px;"><strong>Resolve</strong> — Mark the issue as complete. It is removed from active lists but remains in the system history.</li></ul>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Browser Notifications</h4>
<p style="margin-bottom:10px;">Click the &#9881;&#65039; gear icon in the alerts panel to configure browser notifications. You can choose which severity levels trigger notifications. Browser notification permission must be granted via the &quot;Enable Notifications&quot; button. Notifications fire when new issues are detected during the 60-second auto-refresh.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Home Assistant Notifications</h4>
<p style="margin-bottom:10px;">In addition to browser notifications, you can configure Home Assistant notifications to receive push notifications on your phone (via the HA Companion App), SMS, or any other notification service set up in your Home Assistant instance.</p>
<ul style="margin:4px 0 12px 20px;">
<li style="margin-bottom:4px;"><strong>Enable</strong> — Check &quot;Enable HA Notifications&quot; and enter the name of your notify service (the part after <code>notify.</code>)</li>
<li style="margin-bottom:4px;"><strong>Find your service name</strong> — In Home Assistant, go to Settings &rarr; Automations &rarr; Actions, search for &quot;notify&quot;, and look for your service (e.g. <code>mobile_app_brandons_iphone</code>)</li>
<li style="margin-bottom:4px;"><strong>Severity filters</strong> — Choose which severity levels trigger HA notifications, independently of browser notification settings</li>
<li style="margin-bottom:4px;"><strong>Test</strong> — Click the Test button to send a test notification and verify everything works</li>
<li style="margin-bottom:4px;">Notifications include the customer name, issue severity, and description so you know exactly what was reported</li>
</ul>
`;

// --- Change Log ---
async function mgmtShowChangelog() {
    if (!currentCustomerId) {
        showToast('Select a customer first', 'error');
        return;
    }
    document.getElementById('mgmtChangelogModal').style.display = 'flex';
    mgmtLoadChangelog();
}
function mgmtCloseChangelogModal() {
    document.getElementById('mgmtChangelogModal').style.display = 'none';
}
async function mgmtLoadChangelog() {
    const el = document.getElementById('mgmtChangelogContent');
    try {
        const data = await api('/customers/' + currentCustomerId + '/changelog');
        const entries = data.entries || [];
        if (entries.length === 0) {
            el.innerHTML = '<div style="text-align:center;color:var(--text-muted);padding:32px;">No changes recorded yet.</div>';
            return;
        }
        let html = '<table style="width:100%;border-collapse:collapse;font-size:12px;">';
        html += '<thead><tr style="border-bottom:2px solid var(--border-light);text-align:left;">';
        html += '<th style="padding:6px 8px;">Time</th>';
        html += '<th style="padding:6px 8px;">Who</th>';
        html += '<th style="padding:6px 8px;">Category</th>';
        html += '<th style="padding:6px 8px;">Change</th>';
        html += '</tr></thead><tbody>';
        entries.forEach(function(e) {
            const dt = new Date(e.timestamp);
            const timeStr = dt.toLocaleDateString(undefined, {month:'short',day:'numeric'}) + ' ' + dt.toLocaleTimeString(undefined, {hour:'numeric',minute:'2-digit'});
            const isHO = e.actor === 'Homeowner';
            const badge = '<span style="display:inline-block;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:600;' +
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
    } catch (err) {
        el.innerHTML = '<div style="color:var(--color-danger);">Failed to load change log.</div>';
    }
}
function mgmtExportChangelogCSV() {
    if (!currentCustomerId) return;
    window.open(BASE + '/customers/' + currentCustomerId + '/changelog/csv', '_blank');
}
document.getElementById('mgmtChangelogModal').addEventListener('click', function(e) {
    if (e.target === this) mgmtCloseChangelogModal();
});

// --- Help ---
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
    document.getElementById('mgmtTimezone').textContent = '';
    loadCustomers();
    listRefreshTimer = setInterval(loadCustomers, 60000);
    // Close modals on backdrop click or Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            if (document.getElementById('notifPrefsModal').style.display === 'flex') closeNotifPrefs();
            else if (document.getElementById('ackModal').style.display === 'flex') closeAckModal();
            else if (document.getElementById('alertsPanelModal').style.display === 'flex') closeAlertsPanel();
            else if (document.getElementById('qrScanModal').style.display === 'flex') closeQRScanner();
            else if (document.getElementById('mgmtChangelogModal').style.display === 'flex') mgmtCloseChangelogModal();
            else if (document.getElementById('helpModal').style.display === 'flex') closeHelpModal();
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
    document.getElementById('qrScanModal').addEventListener('click', function(e) {
        if (e.target === this) closeQRScanner();
    });
    document.getElementById('alertsPanelModal').addEventListener('click', function(e) {
        if (e.target === this) closeAlertsPanel();
    });
    document.getElementById('ackModal').addEventListener('click', function(e) {
        if (e.target === this) closeAckModal();
    });
    document.getElementById('notifPrefsModal').addEventListener('click', function(e) {
        if (e.target === this) closeNotifPrefs();
    });
});
</script>
</body>
</html>
"""
