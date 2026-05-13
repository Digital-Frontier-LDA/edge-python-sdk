# Quickstart

> Placeholder. Full walkthrough lands in step 5 of [`SPEC.md`](../SPEC.md#13-sign-off).

## Install

```bash
pip install edge-provider-sdk
```

## Latitude direct

```python
from edge_provider_sdk import EdgeClient

client = EdgeClient(provider="latitude", bearer="lt_...")
```

## Digital Frontier adapter

```python
client = EdgeClient(
    provider="digital-frontier",
    base_url="https://df.example.com/api/v1",
    bearer="df_...",
)
```

See [`SPEC.md` §2](../SPEC.md#2-public-api-surface) for the full API surface.
