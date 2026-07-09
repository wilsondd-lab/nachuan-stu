from typing import TYPE_CHECKING

from .trae import TraeProvider
from .mulerun import MuleRunProvider
from .apimart import ApimartProvider
from .atlascloud import AtlasCloudProvider

if TYPE_CHECKING:
    from .base import BaseProvider

_PROVIDERS = {
    "trae": TraeProvider,
    "mulerun": MuleRunProvider,
    "apimart": ApimartProvider,
    "atlascloud": AtlasCloudProvider,
}


def get_provider(name: str, api_key: str = "", output_dir: str = "./output") -> "BaseProvider":
    """Return an instantiated provider by name."""
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name}")
    # trae provider 接受 output_dir 参数
    if name == "trae":
        return cls(api_key=api_key, output_dir=output_dir)
    return cls(api_key)


def get_provider_class(name: str) -> type["BaseProvider"]:
    """Return the provider class (for accessing class-level attributes like env_var)."""
    cls = _PROVIDERS.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider: {name}")
    return cls


def list_providers() -> list[str]:
    """Return all registered provider names."""
    return list(_PROVIDERS.keys())
