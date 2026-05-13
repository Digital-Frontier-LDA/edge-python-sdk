# Patches

Three `git format-patch` files applied to the unpacked upstream tarball by
`scripts/apply-patches.sh`. See [`SPEC.md` §4](../SPEC.md#4-patches-against-upstream).

| Patch | Files modified |
|---|---|
| `0001-site-enum-permissive.patch` | `models/create_serverop.py`, `models/post_vpn_sessionop.py`, `models/create_virtual_networkop.py` |
| `0002-plan-enum-permissive.patch` | `models/create_serverop.py` |
| `0003-os-enum-permissive.patch` | `models/create_serverop.py`, `models/create_server_reinstallop.py`, `models/update_server_deploy_configop.py` |

The patches don't exist yet — they're generated in step 2 of [`SPEC.md` §13](../SPEC.md#13-sign-off)
against pinned upstream `latitudesh-python-sdk==3.0.5`.
