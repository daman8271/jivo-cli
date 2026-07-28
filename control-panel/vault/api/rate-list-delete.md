---
endpoint: /realise/api/rate-list/delete/
method: POST
auth: session + X-CSRFToken (JSON body)
readonly: false
used_by: [rate-list]
tags: [jivo, api, calculator-ratelist]
---

# `POST /realise/api/rate-list/delete/`

## Purpose
Deletes one saved result from the [[rate-list]] by id. Fired by the ✕ button on a Rate List result card (after a browser confirm). **WRITE — not executed during recon; signature captured from page JS only.**

## Request
`Content-Type: application/json`, `X-CSRFToken: <csrftoken>`. Body:

| Field | Type | Meaning |
|---|---|---|
| `id` | str/int | Primary key of the saved result to delete |

Example (structure only, NOT sent):
```json
{"id":"12"}
```

## Response
Not probed. The page JS does not read the body — on any response it simply drops the row from the local list and re-renders (implying a `{"status":"ok"}`-style reply on success).

## Used by
[[rate-list]] (delete ✕ button)

## Notes
- **WRITE endpoint — mutating/destructive.** In the recipe's skip list; documented from `realise__rate-list.html` only, never called.
- Create counterpart: [[rate-list-save]]. List: [[rate-list]].
