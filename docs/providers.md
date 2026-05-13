# Providers

> Placeholder. Full provider matrix lands in step 5 of [`SPEC.md`](../SPEC.md#13-sign-off).

| `provider=` | Default `base_url` | Enum behavior | Catalog source for sites |
|---|---|---|---|
| `latitude` | `https://api.latitude.sh` | Upstream enums validate | Static enum mirror |
| `digital-frontier` | Required from caller | All 7 enums permissive | `GET /regions` |

See [`SPEC.md` §3](../SPEC.md#3-provider-contract) for full details.
