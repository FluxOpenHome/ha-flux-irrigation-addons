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
    .zone-settings-table { table-layout: fixed; }
    .zone-settings-table th, .zone-settings-table td { padding: 6px 4px; font-size: 12px; }
    .zone-settings-table td[style*="white-space"] { white-space: normal !important; }
    .zone-settings-table input[type="number"] { width: 50px !important; padding: 3px 2px !important; font-size: 11px !important; }
}
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
            <span class="nav-tab active">Homeowner</span>
            <a class="nav-tab" href="?view=config">Configuration</a>
        </div>
        <button class="dark-toggle" onclick="toggleDarkMode()" title="Toggle dark mode">🌙</button>
        <button class="dark-toggle" onclick="showChangelog()" title="Change Log">📋</button>
        <button class="dark-toggle" onclick="showHelp()" title="Help">&#10067;</button>
        <button class="dark-toggle" onclick="showReportIssue()" title="Report Issue">&#9888;&#65039;</button>
        <button class="btn btn-secondary btn-sm" onclick="switchToManagement()">Management</button>
    </div>
</div>

<div class="container">
    <div class="detail-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <div>
            <h2 id="dashTitle" style="font-size:22px;font-weight:600;">My Irrigation System</h2>
            <div id="dashAddress" onclick="openAddressInMaps()" style="font-size:14px;color:var(--color-link);margin-top:4px;display:none;cursor:pointer;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;" title="Open in Maps"></div>
            <div id="dashTimezone" style="font-size:12px;color:var(--text-muted);margin-top:2px;"></div>
        </div>
        <div style="display:flex;gap:8px;">
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
    <div class="card" id="rainSensorCard" style="display:none;">
        <div class="card-header">
            <h2>&#127783;&#65039; Rain Sensor</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <span id="rainStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-tile);color:var(--text-muted);">&#8212;</span>
            </div>
        </div>
        <div class="card-body" id="rainSensorCardBody">
            <div class="loading">Loading rain sensor...</div>
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
            <h2 style="display:flex;align-items:center;gap:8px;"><svg xmlns="http://www.w3.org/2000/svg" viewBox="155 170 745 295" style="height:28px;width:auto;"><path fill="var(--text-primary)" fill-rule="evenodd" d="M322.416931,281.625397 C323.073517,288.667053 324.062378,295.290680 324.095001,301.918976 C324.240021,331.407532 324.573761,360.907135 323.953278,390.384125 C323.315430,420.685608 305.951965,442.817230 276.750000,451.004150 C252.045670,457.930115 227.631088,457.462616 204.859512,444.061829 C193.733704,437.514404 185.529037,427.904022 179.913101,416.206268 C179.426056,415.191742 179.182327,414.060425 178.732849,412.703430 C192.772842,404.558502 206.657608,396.503632 221.095810,388.127686 C222.548920,398.588440 227.417007,406.291168 236.306213,411.228241 C242.295563,414.554749 248.872574,415.283630 255.195541,413.607391 C269.094299,409.922882 279.602142,400.331543 276.985321,375.408997 C268.292480,376.997406 259.625824,379.362396 250.827682,380.053528 C212.511551,383.063599 177.112976,355.681854 170.128632,318.134705 C162.288498,275.986908 187.834488,236.765533 229.805115,227.777832 C248.650925,223.742157 267.514679,224.860764 285.481567,232.988800 C306.417999,242.460220 318.099121,258.975830 322.416931,281.625397 M216.907806,286.065979 C225.295822,272.331604 237.176926,265.403442 252.929047,267.162231 C267.323669,268.769440 277.405518,277.037170 282.681366,290.504517 C288.739105,305.967712 282.622986,322.699615 267.827820,332.537079 C254.597519,341.334045 236.860046,339.821564 225.031052,328.887756 C212.268768,317.091309 209.342514,302.099945 216.907806,286.065979z"/><path fill="var(--text-primary)" fill-rule="evenodd" d="M440.778076,230.141632 C466.800079,239.483002 484.434601,256.637787 491.839233,283.105133 C500.007050,312.300537 489.084961,342.278625 464.074921,361.493744 C431.640076,386.413300 382.445770,383.545990 353.656403,355.057953 C318.682434,320.450043 324.759583,264.850739 366.581024,238.762604 C389.708984,224.335434 414.506042,222.091354 440.778076,230.141632 M419.079773,266.764740 C437.440765,270.748535 450.546936,286.287720 449.715515,302.670624 C448.781708,321.070160 434.135437,336.279297 415.803497,337.885803 C397.935547,339.451660 380.905334,327.358856 376.509705,309.984161 C370.390747,285.797394 393.025116,262.545013 419.079773,266.764740z"/><path fill="var(--text-primary)" fill-rule="evenodd" d="M505.651459,275.706696 C519.676758,244.101715 544.491516,227.960754 577.827881,226.121109 C611.160156,224.281693 638.083069,237.473114 655.040100,266.968140 C676.296448,303.941376 659.723389,352.082367 620.168030,369.955170 C596.583435,380.611755 572.628662,381.200958 548.535156,371.444641 C547.794678,371.144745 546.983826,371.018707 545.645447,370.662506 C545.645447,390.059296 545.645447,409.111145 545.645447,428.497070 C530.607544,428.497070 516.074341,428.497070 500.996918,428.497070 C500.996918,426.395355 500.996918,424.628113 500.996918,422.860901 C500.996948,382.885895 500.731262,342.907776 501.200592,302.938263 C501.306030,293.961548 503.980682,285.014954 505.651459,275.706696 M598.115479,334.281433 C575.892517,344.478851 553.161804,330.843811 547.077026,312.404572 C542.453613,298.393616 547.708435,283.178833 560.344666,273.573029 C572.626587,264.236572 589.550232,263.566986 602.341309,271.911499 C626.866516,287.910980 624.857971,320.051117 598.115479,334.281433z"/><path fill="var(--text-primary)" d="M670.825439,182.155045 C670.825439,180.187927 670.825439,178.699997 670.825439,176.849915 C685.635620,176.849915 700.198181,176.849915 715.259155,176.849915 C715.259155,197.175491 715.259155,217.587784 715.259155,238.510025 C716.406799,238.089737 717.045288,238.015717 717.473022,237.676285 C735.466553,223.398956 755.376953,222.532013 775.856384,230.443253 C790.949036,236.273605 798.483093,249.035553 801.756714,264.225281 C803.287109,271.326416 804.004150,278.725677 804.067200,285.998688 C804.319702,315.143738 804.171570,344.292236 804.171570,373.721710 C789.407043,373.721710 774.836182,373.721710 759.827942,373.721710 C759.827942,371.711731 759.835571,369.768616 759.826843,367.825562 C759.706604,341.165588 760.090210,314.490112 759.275696,287.851318 C758.772949,271.407867 746.863953,263.163330 731.353210,266.883484 C722.925842,268.904694 717.127258,275.714691 716.057434,285.099060 C715.681213,288.399445 715.542114,291.742798 715.536499,295.066956 C715.495117,319.566559 715.514954,344.066254 715.515503,368.565918 C715.515503,370.204803 715.515503,371.843689 715.515503,373.824829 C700.566040,373.824829 685.988281,373.824829 670.825439,373.824829 C670.825439,310.162415 670.825439,246.398331 670.825439,182.155045z"/><path fill="var(--text-primary)" d="M855.839355,323.000092 C855.839355,340.127289 855.839355,356.754486 855.839355,373.695129 C840.823486,373.695129 826.114746,373.695129 810.997253,373.695129 C810.997253,371.683563 810.994263,369.731567 810.997681,367.779572 C811.046997,339.965515 810.786316,312.145172 811.345886,284.341370 C811.503601,276.506470 813.144958,268.402985 815.701904,260.971832 C822.865173,240.153290 839.259949,230.438156 859.952881,227.148788 C867.723389,225.913574 875.715454,226.072052 883.918213,225.576279 C883.918213,240.530334 883.918213,254.247711 883.918213,268.202820 C883.009399,267.944122 882.380005,267.791504 881.768005,267.586914 C867.262085,262.736725 856.693237,269.680603 856.083313,285.032410 C855.587708,297.505157 855.890564,310.009644 855.839355,323.000092z"/><path fill="#6DAC39" d="M397.000000,391.998138 C428.473236,391.998138 459.446503,391.998138 490.792969,391.998138 C490.792969,404.699890 490.792969,417.072754 490.792969,429.726562 C438.290070,429.726562 385.895660,429.726562 333.244019,429.726562 C333.244019,417.257721 333.244019,404.991150 333.244019,391.998138 C354.328308,391.998138 375.414154,391.998138 397.000000,391.998138z"/></svg> Moisture Probes</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <span id="moistureMultBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-success-light);color:var(--text-success-dark);">1.0x</span>
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
    <div class="card" id="expansionCard" style="display:none;">
        <div class="card-header">
            <h2>&#128268; Expansion Boards</h2>
            <div style="display:flex;align-items:center;gap:8px;">
                <span id="expansionStatusBadge" style="font-size:12px;padding:3px 10px;border-radius:12px;background:var(--bg-tile);color:var(--text-muted);">&#8212;</span>
            </div>
        </div>
        <div class="card-body" id="expansionCardBody">
            <div class="loading">Loading expansion data...</div>
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

<!-- Change Log Modal -->
<div id="changelogModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.4);z-index:10000;align-items:center;justify-content:center;">
    <div style="background:var(--bg-card);border-radius:12px;padding:0;width:90%;max-width:720px;max-height:80vh;box-shadow:0 8px 32px rgba(0,0,0,0.2);display:flex;flex-direction:column;">
        <div style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px 12px 24px;border-bottom:1px solid var(--border-light);">
            <h3 style="font-size:17px;font-weight:600;margin:0;color:var(--text-primary);">Configuration Change Log</h3>
            <div style="display:flex;gap:6px;align-items:center;">
                <button class="btn btn-secondary btn-sm" onclick="exportChangelogCSV()">Export CSV</button>
                <button onclick="closeChangelogModal()" style="background:none;border:none;font-size:22px;cursor:pointer;color:var(--text-muted);padding:0 4px;">&times;</button>
            </div>
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

<div class="toast-container" id="toastContainer"></div>

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

// Escape + backdrop for report issue modal
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('reportIssueModal').style.display === 'flex') {
        closeReportIssue();
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
    document.getElementById('upcomingServiceDate').textContent = 'Upcoming Service: ' + dateStr;
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
    const statusLabels = {open: 'Submitted', acknowledged: 'Acknowledged', scheduled: 'Service Scheduled', resolved: 'Resolved'};
    let html = '<div style="background:var(--bg-card);border-radius:12px;padding:16px 20px;box-shadow:0 1px 4px rgba(0,0,0,0.06);">';
    html += '<div style="font-size:14px;font-weight:600;color:var(--text-primary);margin-bottom:10px;">Your Reported Issues</div>';
    issues.forEach(function(issue) {
        const color = sevColors[issue.severity] || '#999';
        const isResolved = issue.status === 'resolved';
        const dt = new Date(issue.created_at);
        const timeStr = dt.toLocaleDateString(undefined, {month:'short', day:'numeric'}) + ' ' + dt.toLocaleTimeString(undefined, {hour:'numeric', minute:'2-digit'});
        html += '<div style="display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-light);' + (isResolved ? 'opacity:0.85;' : '') + '">';
        if (isResolved) {
            html += '<span style="display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;background:#27ae6022;color:#27ae60;white-space:nowrap;">&#10003; Resolved</span>';
        } else {
            html += '<span style="display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600;background:' + color + '22;color:' + color + ';white-space:nowrap;">' + esc(sevLabels[issue.severity] || issue.severity) + '</span>';
        }
        html += '<div style="flex:1;min-width:0;">';
        html += '<div style="font-size:13px;color:var(--text-primary);word-break:break-word;">' + esc(issue.description) + '</div>';
        html += '<div style="font-size:11px;color:var(--text-muted);margin-top:2px;">' + esc(timeStr) + ' &middot; ' + esc(statusLabels[issue.status] || issue.status) + '</div>';
        if (issue.management_note) {
            html += '<div style="font-size:12px;color:var(--text-secondary);margin-top:4px;padding:6px 10px;background:var(--bg-tile);border-radius:6px;border-left:3px solid var(--color-primary);">&#128172; <strong>Management:</strong> ' + esc(issue.management_note) + '</div>';
        }
        if (isResolved) {
            html += '<div style="margin-top:6px;"><button onclick="dismissIssue(\\''+issue.id+'\\')" class="btn btn-secondary btn-sm" style="font-size:11px;padding:3px 10px;">Dismiss</button></div>';
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
        domain === 'number' && (/run_duration/.test(eid) || (/zone_?\d/.test(eid) && !/repeat|cycle|mode/.test(eid)) || /duration.*zone/.test(eid)),
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
let _initialLoadDone = false;
async function loadDashboard() {
    loadStatus();
    loadWeather();
    loadMoisture();
    loadZones();
    loadSensors();
    if (!_initialLoadDone) { loadControls(); _initialLoadDone = true; }
    loadHistory();
    loadActiveIssues();
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

        const wf = s.combined_multiplier != null ? s.combined_multiplier : 1.0;
        const wfColor = wf === 1.0 ? 'var(--color-success)' : wf < 1 ? 'var(--color-warning)' : 'var(--color-danger)';
        const wm = s.weather_multiplier != null ? s.weather_multiplier : 1.0;
        const mmult = s.moisture_multiplier != null ? s.moisture_multiplier : 1.0;
        const moistureActive = s.moisture_enabled && s.moisture_probe_count > 0;
        const factorBreakdown = moistureActive ? 'W: ' + wm + 'x · M: ' + mmult + 'x' : 'W: ' + wm + 'x';

        el.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;">
            <div class="tile"><div class="tile-name">Connection</div><div class="tile-state ${s.ha_connected ? 'on' : ''}">${s.ha_connected ? 'Connected' : 'Disconnected'}</div></div>
            <div class="tile"><div class="tile-name">System</div><div class="tile-state ${s.system_paused ? '' : 'on'}">${s.system_paused ? 'Paused' : 'Active'}</div></div>
            <div class="tile"><div class="tile-name">Zones</div><div class="tile-state ${s.active_zones > 0 ? 'on' : ''}">${s.active_zones > 0 ? esc(resolveZoneName(s.active_zone_entity_id, s.active_zone_name)) + ' running' : 'Idle (' + (s.total_zones || 0) + ' zones)'}</div></div>
            <div class="tile"><div class="tile-name">Sensors</div><div class="tile-state">${s.total_sensors || 0} total</div></div>
            <div class="tile"><div class="tile-name">Watering Factor</div><div class="tile-state" style="color:${wfColor};font-weight:700;">${wf}x</div><div style="font-size:10px;color:var(--text-muted);margin-top:2px;">${factorBreakdown}</div></div>
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
    return ' <span style="font-weight:600;color:' + color + ';">(' + label + ')</span>';
}

// --- Sensors ---
let _sensorGridBuilt = false;
async function loadSensors() {
    const el = document.getElementById('detailSensors');
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
    const controlsEl = document.getElementById('detailControls');
    const scheduleEl = document.getElementById('detailSchedule');
    try {
        const [data, durData] = await Promise.all([
            api('/entities'),
            mapi('/durations').catch(() => ({})),
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

        // Extract rain and expansion control entities into their own cards
        const rainControls = controlEntities.filter(e => isRainEntity(e.entity_id));
        const expansionControls = controlEntities.filter(e => isExpansionEntity(e.entity_id));
        const regularControls = controlEntities.filter(e => !isRainEntity(e.entity_id) && !isExpansionEntity(e.entity_id));
        window._rainControls = rainControls;
        window._expansionControls = expansionControls;
        renderRainSensorCard();
        renderExpansionCard();

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
                    html += renderControlTile(e);
                }
                html += '</div></div>';
            }
            controlsEl.innerHTML = html;
        }

        // Render Schedule card
        renderScheduleCard(scheduleByCategory, durData);

    } catch (e) {
        controlsEl.innerHTML = '<div style="color:var(--color-danger);">Failed to load controls: ' + esc(e.message) + '</div>';
        scheduleEl.innerHTML = '<div style="color:var(--color-danger);">Failed to load schedule: ' + esc(e.message) + '</div>';
    }
}

// --- Rain Sensor Card ---
function renderRainSensorCard() {
    const card = document.getElementById('rainSensorCard');
    const body = document.getElementById('rainSensorCardBody');
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
    const body = document.getElementById('expansionCardBody');
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

function renderScheduleCard(sched, durData) {
    const el = document.getElementById('detailSchedule');
    const { schedule_enable, day_switches, start_times, run_durations, repeat_cycles, zone_enables, zone_modes, system_controls } = sched;
    const adjDurations = (durData && durData.adjusted_durations) || {};
    const baseDurations = (durData && durData.base_durations) || {};
    const factorsActive = durData && durData.duration_adjustment_active;
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
    html += '<div style="display:flex;align-items:center;justify-content:space-between;' +
        'padding:12px 16px;border-radius:8px;margin-bottom:16px;background:' + (afOn ? 'var(--bg-active-tile)' : 'var(--bg-inactive-tile)') + ';">' +
        '<div><div style="font-size:14px;font-weight:600;color:' + (afOn ? 'var(--color-success)' : 'var(--text-secondary)') + ';">' +
        'Apply Factors to Schedule</div>' +
        '<div style="font-size:12px;color:var(--text-muted);">Automatically adjust run durations by the combined watering factor</div></div>' +
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
                const adj = factorsActive ? adjDurations[eid] : null;
                const baseVal = adj ? String(adj.original) : duration.state;
                html += '<td style="white-space:nowrap;"><input type="number" id="' + inputId + '" value="' + esc(baseVal) + '" ' +
                    'min="' + (attrs.min || 0) + '" max="' + (attrs.max || 999) + '" step="' + (attrs.step || 1) + '" ' +
                    'style="width:70px;padding:3px 6px;border:1px solid var(--border-input);border-radius:4px;font-size:12px;"> ' +
                    esc(unit) + ' ' +
                    '<button class="btn btn-primary btn-sm" onclick="setEntityValue(\\'' + eid +
                    '\\',\\'number\\',{value:parseFloat(document.getElementById(\\'' + inputId + '\\').value)})">Set</button>' +
                    (adj ? ' <span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;' +
                    'background:var(--bg-active-tile);color:' + (Math.abs(adj.combined_multiplier - 1.0) < 0.005 ? 'var(--color-success)' : 'var(--color-warning)') + ';">' +
                    adj.adjusted + ' ' + esc(unit) + ' (' + adj.combined_multiplier.toFixed(2) + 'x)</span>' : '') +
                    '</td>';
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
    const parts = friendlyName.split(' ');
    const last = parts[parts.length - 1];
    if (parts.length > 1 && last.includes('_') && entityId && entityId.includes(last)) {
        return parts.slice(0, -1).join(' ');
    }
    return friendlyName;
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

async function setEntityValue(entityId, domain, bodyObj) {
    try {
        await api('/entities/' + entityId + '/set', {
            method: 'POST',
            body: JSON.stringify(bodyObj),
        });
        showToast('Updated ' + entityId.split('.').pop());
        setTimeout(() => { loadControls(); loadSensors(); }, 1000);
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

        // Determine if any event has probe (moisture) data — show column only if so
        const hasProbeData = events.some(e => e.moisture && e.moisture.moisture_multiplier != null);

        el.innerHTML = weatherSummary +
            '<table style="width:100%;font-size:13px;border-collapse:collapse;"><thead><tr style="text-align:left;border-bottom:2px solid var(--border-light);"><th style="padding:6px;">Zone</th><th style="padding:6px;">State</th><th style="padding:6px;">Time</th><th style="padding:6px;">Duration</th><th style="padding:6px;">Watering Factor</th>' +
            (hasProbeData ? '<th style="padding:6px;">Probe Factor</th>' : '') +
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
                // Watering Factor column — weather multiplier for schedule-triggered events
                let wFactorCell = '<span style="color:var(--text-disabled);">—</span>';
                if (e.source === 'schedule') {
                    const wMult = wx.watering_multiplier != null ? wx.watering_multiplier : null;
                    if (wMult != null) {
                        const fc = wMult === 1.0 ? 'var(--color-success)' : wMult < 1 ? 'var(--color-warning)' : 'var(--color-danger)';
                        wFactorCell = '<span style="color:' + fc + ';font-weight:600;">' + wMult + 'x</span>';
                    }
                }
                // Probe Factor column — moisture multiplier + sensor readings
                let pFactorCell = '<span style="color:var(--text-disabled);">—</span>';
                if (e.source === 'schedule') {
                    const mo = e.moisture || {};
                    const mMult = mo.moisture_multiplier != null ? mo.moisture_multiplier : null;
                    if (mMult != null) {
                        const fc = mMult === 1.0 ? 'var(--color-success)' : mMult < 1 ? 'var(--color-warning)' : 'var(--color-danger)';
                        pFactorCell = '<span style="color:' + fc + ';font-weight:600;">' + mMult + 'x</span>';
                        // Show sensor readings (T/M/B) if available
                        const sr = mo.sensor_readings || {};
                        const parts = [];
                        if (sr.T != null) parts.push('T:' + sr.T + '%');
                        if (sr.M != null) parts.push('M:' + sr.M + '%');
                        if (sr.B != null) parts.push('B:' + sr.B + '%');
                        if (parts.length > 0) {
                            pFactorCell += '<div style="font-size:10px;color:var(--text-muted);margin-top:1px;">' + parts.join(' ') + '</div>';
                        }
                    }
                }
                const srcLabel = e.source ? '<div style="font-size:10px;color:var(--text-placeholder);">' + esc(e.source) + '</div>' : '';
                return `<tr style="border-bottom:1px solid var(--border-row);">
                <td style="padding:6px;">${esc(resolveZoneName(e.entity_id, e.zone_name))}${srcLabel}</td>
                <td style="padding:6px;">${e.state === 'on' || e.state === 'open' ? '<span style="color:var(--color-success);">ON</span>' : '<span style="color:var(--text-disabled);">OFF</span>'}</td>
                <td style="padding:6px;">${formatTime(e.timestamp)}</td>
                <td style="padding:6px;">${e.duration_seconds ? Math.round(e.duration_seconds / 60) + ' min' : '-'}</td>
                <td style="padding:6px;font-size:12px;">${wFactorCell}</td>` +
                (hasProbeData ? `<td style="padding:6px;font-size:12px;">${pFactorCell}</td>` : '') +
                `<td style="padding:6px;font-size:12px;">${wxCell}</td>
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

let _weatherDataCache = null;
let _weatherRulesCache = null;
let _moistureDataCache = null;
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
    const fc = (w.forecast || []).slice(0, 5);
    for (const f of fc) {
        parts.push(f.condition, f.temperature, f.precipitation_probability);
    }
    return parts.join('|');
}

async function loadWeather() {
    const card = document.getElementById('weatherCard');
    const body = document.getElementById('weatherCardBody');
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

        // Badge
        badge.textContent = mult + 'x';
        badge.style.background = mult === 1.0 ? 'var(--bg-success-light)' : mult < 1 ? 'var(--bg-warning)' : 'var(--bg-danger-light)';
        badge.style.color = mult === 1.0 ? 'var(--text-success-dark)' : mult < 1 ? 'var(--text-warning)' : 'var(--text-danger-dark)';

        // Current conditions — update text only
        const el = (id) => body.querySelector('[data-id=\"' + id + '\"]');
        el('wIcon').textContent = icon;
        el('wCondition').textContent = w.condition || 'unknown';
        el('wTemp').textContent = w.temperature != null ? w.temperature + (w.temperature_unit || '°F') : 'N/A';
        el('wHumidity').textContent = w.humidity != null ? w.humidity + '%' : 'N/A';
        el('wWind').textContent = w.wind_speed != null ? w.wind_speed + ' ' + (w.wind_speed_unit || 'mph') : 'N/A';

        // Forecast — rebuild only the forecast strip (lightweight)
        const forecastEl = el('wForecast');
        const forecast = w.forecast || [];
        if (forecast.length > 0) {
            let fh = '<div style="margin-top:12px;"><div style="font-size:12px;font-weight:600;color:var(--text-muted);text-transform:uppercase;margin-bottom:8px;">Forecast</div>';
            fh += '<div style="display:flex;gap:8px;overflow-x:auto;">';
            for (let i = 0; i < Math.min(forecast.length, 5); i++) {
                const f = forecast[i];
                const dt = f.datetime ? new Date(f.datetime) : null;
                const dayLabel = dt ? dt.toLocaleDateString('en-US', { weekday: 'short' }) : '';
                const fIcon = _condIcons[f.condition] || '🌡️';
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

        // Active adjustments — rebuild only the adjustments box
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
        const result = await wapi('/weather/rules', {
            method: 'PUT',
            body: JSON.stringify({ rules }),
        });
        const mult = result.watering_multiplier;
        showToast('Weather rules saved' + (mult != null ? ' — multiplier: ' + mult + 'x' : ''));
        // Clear cache to pick up new multiplier; card structure stays intact
        _weatherDataCache = null;
        _weatherRulesCache = null;
        loadWeather();
        loadStatus();
        loadControls();
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
        loadWeather();
        loadStatus();
        loadControls();
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

async function loadMoisture() {
    const card = document.getElementById('moistureCard');
    const body = document.getElementById('moistureCardBody');
    const badge = document.getElementById('moistureStatusBadge');
    const multBadge = document.getElementById('moistureMultBadge');
    try {
        const data = await mapi('/probes');
        const settings = await mapi('/settings');
        let multData = {};
        try { multData = await mapi('/multiplier'); } catch (_) {}

        const probes = data.probes || {};
        const probeCount = Object.keys(probes).length;

        // Hide the card on the dashboard if no probes are configured
        // (probes are added via the Configuration page)
        if (!settings.enabled && probeCount === 0) {
            card.style.display = 'none';
            _moistureDataCache = null;
            return;
        }
        // Skip DOM rebuild if data hasn't changed (prevents flickering on refresh)
        const moistureKey = JSON.stringify(data) + '|' + JSON.stringify(settings) + '|' + JSON.stringify(multData);
        if (_moistureDataCache === moistureKey) return;
        _moistureDataCache = moistureKey;
        card.style.display = 'block';

        badge.textContent = settings.enabled ? probeCount + ' probe(s)' : 'Disabled';
        badge.style.background = settings.enabled ? 'var(--bg-success-light)' : 'var(--bg-tile)';
        badge.style.color = settings.enabled ? 'var(--text-success-dark)' : 'var(--text-muted)';

        // Update moisture multiplier badge
        const mm = multData.moisture_multiplier != null ? multData.moisture_multiplier : 1.0;
        multBadge.textContent = mm + 'x';
        multBadge.style.background = mm === 1.0 ? 'var(--bg-success-light)' : mm < 1 ? 'var(--bg-warning)' : 'var(--bg-danger-light)';
        multBadge.style.color = mm === 1.0 ? 'var(--text-success-dark)' : mm < 1 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
        multBadge.style.display = settings.enabled ? '' : 'none';

        let html = '';

        // Probe tiles
        if (probeCount > 0) {
            html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:10px;">';
            for (const [pid, probe] of Object.entries(probes)) {
                const sensors = probe.sensors_live || {};
                const devSensors = probe.device_sensors || {};
                html += '<div style="background:var(--bg-tile);border-radius:10px;padding:12px;border:1px solid var(--border-light);">';
                html += '<div style="font-weight:600;font-size:14px;margin-bottom:10px;">' + esc(probe.display_name || pid) + '</div>';

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

                // Device status row: WiFi, Battery, Sleep
                const hasDeviceInfo = devSensors.wifi || devSensors.battery || devSensors.sleep_duration;
                if (hasDeviceInfo) {
                    html += '<div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:8px;padding-top:8px;border-top:1px solid var(--border-light);font-size:11px;color:var(--text-muted);">';
                    if (devSensors.wifi) {
                        const wv = devSensors.wifi.value;
                        const wIcon = wv == null ? '📶' : wv > -50 ? '📶' : wv > -70 ? '📶' : '📶';
                        const wColor = wv == null ? 'var(--text-muted)' : wv > -50 ? 'var(--text-success-dark)' : wv > -70 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
                        html += '<span style="color:' + wColor + ';" title="WiFi Signal">' + wIcon + ' ' + (wv != null ? wv.toFixed(0) + ' ' + esc(devSensors.wifi.unit) : '—') + '</span>';
                    }
                    if (devSensors.battery) {
                        const bv = devSensors.battery.value;
                        const bIcon = bv == null ? '🔋' : bv > 50 ? '🔋' : bv > 20 ? '🪫' : '🪫';
                        const bColor = bv == null ? 'var(--text-muted)' : bv > 50 ? 'var(--text-success-dark)' : bv > 20 ? 'var(--text-warning)' : 'var(--text-danger-dark)';
                        html += '<span style="color:' + bColor + ';" title="Battery">' + bIcon + ' ' + (bv != null ? bv.toFixed(0) + '%' : '—') + '</span>';
                    }
                    if (devSensors.sleep_duration) {
                        const sv = devSensors.sleep_duration.value;
                        let sleepLabel = '—';
                        if (sv != null) {
                            const unit = (devSensors.sleep_duration.unit || 's').toLowerCase();
                            if (unit === 'min' || unit === 'minutes') sleepLabel = sv.toFixed(0) + ' min';
                            else if (unit === 'h' || unit === 'hours') sleepLabel = sv.toFixed(1) + ' hr';
                            else sleepLabel = sv.toFixed(0) + ' ' + esc(devSensors.sleep_duration.unit);
                        }
                        html += '<span title="Sleep Duration">💤 ' + sleepLabel + '</span>';
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

        // Stale threshold
        html += '<div style="margin-bottom:12px;">';
        html += '<label style="font-size:12px;font-weight:500;color:var(--text-secondary);display:block;margin-bottom:4px;">Stale Reading Threshold</label>';
        html += '<div style="display:grid;grid-template-columns:120px 1fr;gap:8px;align-items:center;">';
        html += '<input type="number" id="moistureStaleMin" value="' + (settings.stale_reading_threshold_minutes || 120) + '" min="5" max="1440" style="width:100%;padding:6px 8px;border:1px solid var(--border-input);border-radius:6px;background:var(--bg-input);color:var(--text-primary);font-size:13px;">';
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

        // Existing probes — simple cards
        if (probeCount > 0) {
            for (const [pid, probe] of Object.entries(probes)) {
                const ss = probe.sensors || {};
                const es = probe.extra_sensors || {};
                const depthLabels = {shallow: 'Shallow', mid: 'Mid', deep: 'Deep'};
                html += '<div style="background:var(--bg-tile);border-radius:8px;padding:10px;margin-bottom:8px;border:1px solid var(--border-light);">';
                html += '<div style="display:flex;justify-content:space-between;align-items:center;">';
                html += '<strong style="font-size:14px;">' + esc(probe.display_name || pid) + '</strong>';
                html += '<button class="btn btn-danger btn-sm" onclick="deleteMoistureProbe(\\'' + esc(pid) + '\\')">Remove</button>';
                html += '</div>';
                // Sensor depth pills
                html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:6px;">';
                for (const depth of ['shallow', 'mid', 'deep']) {
                    if (ss[depth]) {
                        html += '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--bg-success-light);color:var(--text-success-dark);">' + depthLabels[depth] + '</span>';
                    } else {
                        html += '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--bg-disabled,#eee);color:var(--text-muted);">' + depthLabels[depth] + ': —</span>';
                    }
                }
                // Extra sensor pills
                if (es.wifi) html += '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--bg-tile);color:var(--text-muted);">📶 WiFi</span>';
                if (es.battery) html += '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--bg-tile);color:var(--text-muted);">🔋 Battery</span>';
                if (es.sleep_duration) html += '<span style="font-size:11px;padding:2px 8px;border-radius:10px;background:var(--bg-tile);color:var(--text-muted);">💤 Sleep</span>';
                html += '</div>';
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

        body.innerHTML = html;
        // Populate device picker after DOM is ready
        loadHoMoistureDevices();
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

        // Fetch zone aliases
        let aliases = {};
        try {
            const aliasRes = await fetch(HBASE + '/zone_aliases');
            aliases = await aliasRes.json();
            if (aliases.aliases) aliases = aliases.aliases;
        } catch(_) {}

        let cbHtml = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:4px;">';
        for (const z of allZones) {
            const eid = z.entity_id;
            const checked = currentMappings.includes(eid) ? ' checked' : '';
            let label = aliases[eid] || z.friendly_name || z.name || eid;
            const m = eid.match(/zone[_]?(\\d+)/i);
            if (label === eid && m) label = 'Zone ' + m[1];
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
        const devices = data.devices || [];
        const totalCount = data.total_count || devices.length;
        const filtered = data.filtered !== false;

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
            toggleEl.innerHTML = 'Showing ' + devices.length + ' moisture device' + (devices.length !== 1 ? 's' : '') +
                ' of ' + totalCount + ' total. <a href="#" onclick="_hoMoistureShowAll=true;loadHoMoistureDevices(true);return false;">Show all devices</a>';
            toggleEl.style.display = '';
        } else if (!filtered && totalCount > 0) {
            toggleEl.innerHTML = 'Showing all ' + totalCount + ' devices. <a href="#" onclick="_hoMoistureShowAll=false;loadHoMoistureDevices(false);return false;">Show only moisture devices</a>';
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
        if (extraSensors.battery) extras.push('Battery');
        if (extraSensors.sleep_duration) extras.push('Sleep');

        if (detected.length > 0 || extras.length > 0) {
            html += '<div style="font-size:13px;font-weight:600;margin-bottom:6px;">Auto-detected sensors</div>';
            html += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">';
            for (const d of detected) {
                html += '<span style="font-size:11px;padding:3px 8px;border-radius:10px;background:var(--bg-success-light);color:var(--text-success-dark);">✓ ' + d + '</span>';
            }
            for (const e of extras) {
                html += '<span style="font-size:11px;padding:3px 8px;border-radius:10px;background:var(--bg-tile);color:var(--text-muted);">✓ ' + e + '</span>';
            }
            html += '</div>';
        } else {
            html += '<div style="color:var(--text-warning);font-size:12px;margin-bottom:8px;">Could not auto-detect sensors. This device has ' + allSensors.length + ' sensor entities.</div>';
        }

        if (detected.length === 0) {
            html += '<div style="color:var(--text-muted);font-size:12px;margin-bottom:8px;">No moisture depth sensors detected. Make sure this is a Gophr device with moisture sensors.</div>';
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

    // Map to all zones by default
    try {
        const zonesData = await api('/zones');
        const allZones = (Array.isArray(zonesData) ? zonesData : zonesData.zones || []).map(function(z) { return z.entity_id; });

        // Clean sensors — remove null values
        const cleanSensors = {};
        for (const [k, v] of Object.entries(sensors)) { if (v) cleanSensors[k] = v; }

        await mapi('/probes', 'POST', {
            probe_id: probeId,
            display_name: displayName,
            device_id: deviceId,
            sensors: cleanSensors,
            extra_sensors: extraSensors,
            zone_mappings: allZones,
        });
        showToast('Probe "' + displayName + '" added and mapped to all ' + allZones.length + ' zones');
        _moistureDataCache = null;
        loadMoisture();
    } catch (e) { showToast(e.message || 'Failed to add probe', 'error'); }
}

async function deleteMoistureProbe(probeId) {
    if (!confirm('Remove probe "' + probeId + '"?')) return;
    try {
        await mapi('/probes/' + encodeURIComponent(probeId), 'DELETE');
        showToast('Probe removed');
        _moistureDataCache = null;
        loadMoisture();
    } catch (e) { showToast(e.message, 'error'); }
}

async function toggleApplyFactors(enable) {
    try {
        const result = await mapi('/settings', 'PUT', { apply_factors_to_schedule: enable });
        const isError = result.success === false;
        showToast(result.message || (enable ? 'Factors applied' : 'Factors disabled'), isError ? 'error' : undefined);
        loadControls();
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

// --- Live Clock ---
let _homeClockTimer = null;
function startHomeClock() {
    if (_homeClockTimer) clearInterval(_homeClockTimer);
    const el = document.getElementById('dashTimezone');
    function tick() {
        try {
            const now = new Date();
            const time = now.toLocaleTimeString('en-US', {hour: 'numeric', minute: '2-digit', hour12: true});
            const abbr = now.toLocaleTimeString('en-US', {timeZoneName: 'short'}).split(' ').pop();
            el.textContent = time + ' ' + abbr;
        } catch(e) {}
    }
    tick();
    _homeClockTimer = setInterval(tick, 30000);
}

// --- Init ---
document.addEventListener('DOMContentLoaded', async () => {
    // Start live clock
    startHomeClock();

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

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Rain Sensor</h4>
<p style="margin-bottom:10px;">If your irrigation controller has a rain sensor connected, a dedicated Rain Sensor card appears showing:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Status Banner</strong> — Shows current state: Dry (green), Rain Detected (red), Rain Delay (yellow), or Disabled (gray)</li><li style="margin-bottom:4px;"><strong>Rain Sensor Enable</strong> — Toggle rain sensor monitoring on or off</li><li style="margin-bottom:4px;"><strong>Sensor Type</strong> — Set to NC (Normally Closed) or NO (Normally Open) to match your hardware wiring</li><li style="margin-bottom:4px;"><strong>Rain Delay Enable</strong> — Toggle the rain delay feature on or off</li><li style="margin-bottom:4px;"><strong>Delay Duration</strong> — How many hours to delay watering after rain is detected (1-72 hours)</li><li style="margin-bottom:4px;"><strong>Rain Delay Active</strong> — Shows whether rain delay is currently active</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">&#128161; The rain sensor card only appears when rain sensor entities are detected on your irrigation controller.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Sensors</h4>
<p style="margin-bottom:10px;">The sensors card shows real-time readings from your irrigation controller — soil moisture, temperature, Wi-Fi signal strength, and any other sensors exposed by your device. Wi-Fi signal includes a quality badge (Great/Good/Poor/Bad) based on signal strength in dBm.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Schedule Management</h4>
<p style="margin-bottom:10px;">Your irrigation schedule is configured through your Flux Open Home controller and managed via its ESPHome entities:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Schedule Enable/Disable</strong> — Master toggle to turn the entire schedule on or off</li><li style="margin-bottom:4px;"><strong>Days of Week</strong> — Click day buttons to toggle which days the schedule runs</li><li style="margin-bottom:4px;"><strong>Start Times</strong> — Set when each schedule program begins (HH:MM format)</li><li style="margin-bottom:4px;"><strong>Zone Settings</strong> — Enable/disable individual zones and set run durations for each</li><li style="margin-bottom:4px;"><strong>Zone Modes</strong> — Some zones may have special modes (Pump Start Relay, Master Valve) that are firmware-controlled</li><li style="margin-bottom:4px;"><strong>Apply Factors to Schedule</strong> — When enabled, automatically adjusts ESPHome run durations using the combined watering factor (weather &times; moisture). The input field shows the base duration (what you set), and a badge next to it shows the adjusted duration and factor (e.g. &quot;24 min (0.80x)&quot;). The base is what you control; the adjusted value is what the controller actually runs. Durations update automatically as conditions change and restore to originals when disabled.</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Schedule changes take effect immediately on your controller — no restart needed.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Weather-Based Control</h4>
<p style="margin-bottom:10px;">When weather is enabled (configured on the Configuration page), the dashboard shows current conditions and a <strong>watering multiplier</strong>:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>1.0x</strong> (green) — Normal watering, no adjustments active</li><li style="margin-bottom:4px;"><strong>Below 1.0x</strong> (yellow) — Reduced watering due to cool temps, humidity, etc.</li><li style="margin-bottom:4px;"><strong>Above 1.0x</strong> (red) — Increased watering due to hot temperatures</li><li style="margin-bottom:4px;"><strong>Skip/Pause</strong> — Watering paused entirely due to rain, freezing, or high wind</li></ul>
<p style="margin-bottom:10px;">The <strong>Weather Rules</strong> section is collapsed by default — click the header to expand and configure rules. Each rule can be individually enabled/disabled. Click <strong>Test Rules Now</strong> to evaluate which rules would trigger under current conditions. The action buttons (Test, Export, Clear) are always visible even when the rules section is collapsed.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Gophr Moisture Probes</h4>
<p style="margin-bottom:10px;">When Gophr moisture probes are connected to Home Assistant, the moisture card shows live soil moisture readings at three depths (shallow, mid, deep). The algorithm uses a <strong>gradient-based approach</strong> that treats each depth as a distinct signal:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Mid sensor (root zone)</strong> — The PRIMARY decision driver. This is where grass roots live and is the most important reading for determining watering needs.</li><li style="margin-bottom:4px;"><strong>Shallow sensor (surface)</strong> — Used for rain detection. If the surface is significantly wetter than the root zone and rain is forecasted, the system infers recent rainfall and reduces or skips watering.</li><li style="margin-bottom:4px;"><strong>Deep sensor (reserve)</strong> — Guards against over-irrigation. If deep soil is saturated while the root zone looks normal, it suggests water is pooling below and watering is reduced.</li></ul>
<p style="margin-bottom:10px;">The moisture card also shows:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Probe tiles</strong> — Color-coded bars showing moisture level at each depth, with stale-data indicators</li><li style="margin-bottom:4px;"><strong>Device status</strong> — WiFi signal strength, battery percentage, and sleep duration are shown below the moisture readings when available (auto-detected from the Gophr device)</li><li style="margin-bottom:4px;"><strong>Zone multipliers</strong> — Combined weather &times; moisture multiplier for each mapped zone</li><li style="margin-bottom:4px;"><strong>Settings</strong> — Root zone thresholds (Skip, Wet, Optimal, Dry), max increase/decrease percentages, and rain detection sensitivity</li><li style="margin-bottom:4px;"><strong>Manage Probes</strong> — Discover probes from HA sensors, add/remove probes, assign to zones</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">💡 Moisture probes adjust both timed API/dashboard runs and ESPHome scheduled runs. The algorithm integrates weather forecast data for rain detection — if the shallow sensor shows a wetting front and rain is forecasted, watering is automatically reduced or skipped.</div>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Run History</h4>
<p style="margin-bottom:10px;">The run history table shows every zone on/off event with:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Zone name</strong> and source (API, schedule, weather pause, etc.)</li><li style="margin-bottom:4px;"><strong>State</strong> — ON (green) or OFF</li><li style="margin-bottom:4px;"><strong>Time</strong> and <strong>duration</strong> of each run</li><li style="margin-bottom:4px;"><strong>Watering Factor</strong> — The weather-based multiplier applied to schedule-triggered runs (green at 1.0x, yellow below, red above)</li><li style="margin-bottom:4px;"><strong>Probe Factor</strong> — The moisture probe multiplier (only shown when probes are enabled); includes sensor readings at each depth (T=Top/shallow, M=Middle/root zone, B=Bottom/deep) as percentages</li><li style="margin-bottom:4px;"><strong>Weather</strong> — Conditions at the time of the event with any triggered rules</li></ul>
<p style="margin-bottom:10px;">Use the time range dropdown to view the last 24 hours, 7 days, 30 days, 90 days, or full year. Click <strong>Export CSV</strong> to download history as a spreadsheet. The CSV includes additional columns for probe sensor readings (top, mid, bottom percentages) and moisture profile.</p>

<h4 style="font-size:15px;font-weight:600;color:var(--text-primary);margin:20px 0 8px 0;">Expansion Boards</h4>
<p style="margin-bottom:10px;">If your controller supports I2C expansion boards for additional zones, the Expansion Boards card shows:</p>
<ul style="margin:4px 0 12px 20px;"><li style="margin-bottom:4px;"><strong>Zone Count</strong> — Total number of zones detected (base board + expansion)</li><li style="margin-bottom:4px;"><strong>Board Details</strong> — I2C addresses of connected expansion boards, with the zone range each board controls</li><li style="margin-bottom:4px;"><strong>Rescan</strong> — Trigger an I2C bus rescan to detect newly connected or disconnected boards</li></ul>
<div style="background:var(--bg-tile);border-radius:6px;padding:8px 12px;margin:8px 0 12px 0;font-size:13px;">&#128161; If no expansion boards are connected, the card shows &quot;No expansion boards connected&quot; with the base zone count. This card only appears when expansion board entities are detected on your controller.</div>

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
`;

// --- Change Log ---
async function showChangelog() {
    document.getElementById('changelogModal').style.display = 'flex';
    loadChangelog();
}
function closeChangelogModal() {
    document.getElementById('changelogModal').style.display = 'none';
}
async function loadChangelog() {
    const el = document.getElementById('changelogContent');
    try {
        const data = await api('/changelog');
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
