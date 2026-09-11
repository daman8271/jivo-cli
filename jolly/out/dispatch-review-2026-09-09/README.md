# Dispatch review prototype — 9 September 2026

Open `index.html` directly in a desktop browser. All assets are local; no server, network login, CDN or installation is needed. Select trucks or their rows, and move the historical replay slider. The keyboard-operable list remains available if WebGL is unavailable.

Scope: historical 8 September actual departures from BH-BT and BH-PF only. Source checked 9 September at 00:58 IST. Five trips, 54,076 litres. All truck geometry is illustrative, not GPS. Planning tonnes mean 1,000 litres, not actual weight. The 100-tonne daily aim is not an expected booking. Opening stock, production, other movements and physical closing count are absent; no stock reconciliation is claimed. The optional what-if fields remain separate unconfirmed user inputs.

## Verification

Run `node --check app.js` and `node verify.cjs`.

PASS: source sums, warehouse scope, 0/midday/full-day replay, WebGL fallback, positive/negative/missing-input scenarios.

The VPS gstack browser could not start because its Playwright installation requires missing chromium_headless_shell-1243. Rendering and visual appearance have not been browser-verified. No browser process was left running by that failed launch. No production deployment or runtime change was made.

Three.js revision 185 is wrapped from the installed CommonJS build for direct file opening; its MIT license is included.
