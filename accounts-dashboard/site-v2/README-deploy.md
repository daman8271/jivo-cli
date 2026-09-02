# site-v2 deploy notes

`vercel.json` validates strictly and rejects unknown keys, so the reasoning that
would otherwise sit beside each setting lives here.

- **`cleanUrls: false`** — deliberate. Every internal link, and every derivation
  record's `drill.page`, uses an explicit `.html`. With `cleanUrls` on, each
  drill-down would 308-redirect (`/party.html` -> `/party`): one wasted round
  trip on the single most-clicked path in the board.
- **`/data/*` is `max-age=0, must-revalidate`** — the board rebuilds every two
  minutes and pages poll `manifest.json`; a cached manifest is a board that
  looks live and is not.
- **`/assets/*` is `max-age=300`** — the modules change only on a deploy.
- `notes/` and `sql/` are copied into this directory by `pipeline/split_data.py`.
  They are NOT hand-maintained here, and `pipeline/` itself is never deployed —
  which is why any `../pipeline/...` fetch 404s in production.
