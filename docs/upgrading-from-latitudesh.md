# Upgrading from `latitudesh-python-sdk`

> Placeholder. Full migration guide lands in step 5 of [`SPEC.md`](../SPEC.md#13-sign-off).

The constructor is the only API difference; every operation
(`servers`, `projects`, `ssh_keys`, …) is identical to upstream.

```python
# Before
from latitudesh_python_sdk import Latitudesh
client = Latitudesh(bearer="lt_...")

# After
from edge_python_sdk import EdgeClient
client = EdgeClient(provider="latitude", bearer="lt_...")
```

Switching to a Latitude-shaped adapter at a different URL:

```python
client = EdgeClient(
    provider="digital-frontier",
    base_url="https://df.example.com/api/v1",
    bearer="df_...",
)
```

See [`SPEC.md` §10](../SPEC.md#10-documentation).
