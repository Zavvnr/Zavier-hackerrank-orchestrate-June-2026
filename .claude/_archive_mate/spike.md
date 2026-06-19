---
description: Run the go/no-go commentary spike on the demo match.
argument-hint: [--language es] [--start N] [--count N] [--mock]
---
Run the commentary spike (events -> one Granite call -> commentary):

```
python spike/go_no_go.py $ARGUMENTS
```

Default language comes from `DEFAULT_LANGUAGE`. Use `--mock` to print the assembled prompt without
calling Granite (offline). A real run needs the chat model `granite-4-h-tiny` loaded in LM Studio.
After it runs, judge the output against the go/no-go checklist the spike prints.
