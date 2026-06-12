"""Patched enum classes must accept arbitrary strings (SPEC §3, §4).

These tests exercise the patched `_generated/` tree directly — they do NOT
go through `EdgeClient`. The goal is to catch a regression where the patch
script lands but mangles a class, or where the upstream changes its enum
definitions in a way that breaks the patch.
"""

from __future__ import annotations

import pytest

from edge_python_sdk._generated.models.create_server_reinstallop import (
    CreateServerReinstallServersOperatingSystem,
)
from edge_python_sdk._generated.models.create_serverop import (
    _ORIGINAL_OS,
    _ORIGINAL_PLANS,
    _ORIGINAL_SITES,
    CreateServerServersAttributes,
    CreateServerServersOperatingSystem,
    CreateServerServersPlan,
    CreateServerServersSite,
)
from edge_python_sdk._generated.models.create_virtual_networkop import (
    CreateVirtualNetworkPrivateNetworksSite,
)
from edge_python_sdk._generated.models.post_vpn_sessionop import (
    PostVpnSessionVpnSessionsSite,
)
from edge_python_sdk._generated.models.update_server_deploy_configop import (
    UpdateServerDeployConfigServersOperatingSystem,
)

PATCHED_ALIASES = [
    ("CreateServerServersSite", CreateServerServersSite),
    ("PostVpnSessionVpnSessionsSite", PostVpnSessionVpnSessionsSite),
    ("CreateVirtualNetworkPrivateNetworksSite", CreateVirtualNetworkPrivateNetworksSite),
    ("CreateServerServersPlan", CreateServerServersPlan),
    ("CreateServerServersOperatingSystem", CreateServerServersOperatingSystem),
    ("CreateServerReinstallServersOperatingSystem", CreateServerReinstallServersOperatingSystem),
    ("UpdateServerDeployConfigServersOperatingSystem", UpdateServerDeployConfigServersOperatingSystem),
]


@pytest.mark.parametrize("name,alias", PATCHED_ALIASES, ids=[name for name, _ in PATCHED_ALIASES])
def test_patched_enum_is_str_alias(name: str, alias: type) -> None:
    assert alias is str, f"{name} is {alias!r}, expected `str`"


def test_pydantic_accepts_arbitrary_strings() -> None:
    attrs = CreateServerServersAttributes(
        site="df-region-mtl-1",
        plan="df-shape-h100-8x",
        operating_system="custom-distro-edge",
    )
    assert attrs.site == "df-region-mtl-1"
    assert attrs.plan == "df-shape-h100-8x"
    assert attrs.operating_system == "custom-distro-edge"


def test_pydantic_still_accepts_canonical_latitude_values() -> None:
    attrs = CreateServerServersAttributes(
        site="SAO",
        plan="c3-large-x86",
        operating_system="ubuntu_24_04_x64_lts",
    )
    assert attrs.site == "SAO"
    assert attrs.plan == "c3-large-x86"
    assert attrs.operating_system == "ubuntu_24_04_x64_lts"


def test_original_constants_are_non_empty_tuples() -> None:
    assert isinstance(_ORIGINAL_SITES, tuple) and len(_ORIGINAL_SITES) >= 18
    assert isinstance(_ORIGINAL_PLANS, tuple) and len(_ORIGINAL_PLANS) >= 19
    assert isinstance(_ORIGINAL_OS, tuple) and len(_ORIGINAL_OS) >= 15
    assert all(isinstance(s, str) and s for s in _ORIGINAL_SITES)
    assert all(isinstance(s, str) and s for s in _ORIGINAL_PLANS)
    assert all(isinstance(s, str) and s for s in _ORIGINAL_OS)
