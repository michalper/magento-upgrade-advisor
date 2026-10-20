# Eval harness report

Not yet generated — this needs a real `ANTHROPIC_API_KEY` and a live run:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
magento-upgrade-advisor eval --out docs/eval-report.md
```

That overwrites this placeholder with the real table (faithfulness, missing/fabricated/duplicate
indices, token usage, latency per fixture per model) and a pass-rate summary by model — see
`src/magento_upgrade_advisor/eval/report.py` for the exact format.
