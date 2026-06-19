---
description: Start the MATE Flask web app locally.
---
Start the web app:

```
python -m web.app
```

Preconditions: both Granite models loaded in LM Studio (chat + embedding), `GRANITE_BASE_URL` set,
and the Laws index built (`/ingest`) so the explainer can answer. Open the local URL it prints —
`/api/stream` streams the two-voice commentary, and the question box calls `/api/ask` for the
explainer.
