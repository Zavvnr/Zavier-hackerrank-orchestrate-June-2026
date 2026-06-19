---
description: Rebuild the Laws-of-the-Game RAG index with Docling + Granite.
---
Rebuild the local Laws index:

```
python -m context.ingest_laws
```

Preconditions: the IFAB PDF is at `context/laws/laws_of_the_game.pdf`, and the **Granite embedding
model is loaded in LM Studio** with `GRANITE_BASE_URL` set. On success it writes
`context/index/laws_chunks.json` + `laws_vectors.npy` and prints the chunk count and embedding
dimension. If it errors, diagnose first (missing PDF, embedding model not loaded, OCR/memory) before
retrying.
