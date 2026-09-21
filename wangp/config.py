"""Zero-configuration resolution for the one supported render host."""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Mapping

if TYPE_CHECKING:  # pragma: no cover - typing only, keeps the runtime import lazy
    from host.render_host import SshHost


HOST_KEYS = ("host.target", "host.wgp_root", "host.pull_root")
OPTIONAL_HOST_KEYS = ("host.wgp_python",)
ALL_HOST_KEYS = HOST_KEYS + OPTIONAL_HOST_KEYS
ENVIRONMENT_KEYS = {
    "host.target": "WANGP_SSH_TARGET",
    "host.wgp_root": "WANGP_WGP_ROOT",
    "host.pull_root": "WANGP_PULL_ROOT",
    "host.wgp_python": "WANGP_WGP_PYTHON",
}
_HOST_FIELDS = {"target", "wgp_root", "pull_root", "wgp_python"}
_FIELD_NAMES = ("target", "wgp_root", "pull_root", "wgp_python")
_ABSOLUTE_PATH_FIELDS = {"wgp_root", "pull_root", "wgp_python"}


class HostConfigError(ValueError):
    """A render host was requested without a complete configuration."""


@dataclass(frozen=True)
class HostSetting:
    """One resolved host value and the layer that supplied it."""

    key: str
    value: str
    source: str
    origin: Path | None = None

    def provenance(self) -> str:
        if self.origin is None:
            return self.source
        return f"{self.source} ({self.origin})"


@dataclass(frozen=True)
class HostConfig:
    """Resolved host settings; absent values remain explicitly unconfigured."""

    target: HostSetting | None
    wgp_root: HostSetting | None
    pull_root: HostSetting | None
    wgp_python: HostSetting | None
    repository_root: Path
    repository_config: Path
    user_config: Path

    @property
    def complete(self) -> bool:
        return not missing_host_keys(self)

    def settings(self) -> tuple[HostSetting | None, ...]:
        return (self.target, self.wgp_root, self.pull_root, self.wgp_python)

    def required_settings(self) -> tuple[HostSetting | None, ...]:
        return (self.target, self.wgp_root, self.pull_root)


def missing_host_keys(config: HostConfig) -> tuple[str, ...]:
    """Return every missing host key, preserving the documented order."""

    return tuple(
        key
        for key, setting in zip(HOST_KEYS, config.required_settings(), strict=True)
        if setting is None
    )


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _repository_root() -> Path:
    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if (candidate / "wangp.toml").is_file():
            return candidate
    package_root = Path(__file__).resolve().parent.parent
    return package_root if (package_root / "wangp.toml").is_file() else cwd


def _user_config_path(environ: Mapping[str, str]) -> Path:
    selected = environ.get("WANGP_CONFIG", "").strip()
    if selected:
        return Path(selected).expanduser()
    configured_home = environ.get("XDG_CONFIG_HOME", "").strip()
    base = (
        Path(configured_home).expanduser()
        if configured_home
        else Path.home() / ".config"
    )
    return base / "wangp" / "config.toml"


def _validate_path_field(field: str, value: str, context: str) -> str:
    if field in _ABSOLUTE_PATH_FIELDS and not Path(value).is_absolute():
        raise HostConfigError(
            f"{context}: field host.{field} must be an absolute path "
            f"(got {value!r})"
        )
    return value


def _read_host_table(path: Path, source: str) -> dict[str, str]:
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HostConfigError(f"cannot read {source} {path}: {exc}") from exc
    except (UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise HostConfigError(f"invalid TOML in {source} {path}: {exc}") from exc

    unknown_tables = sorted(set(payload) - {"host"})
    if unknown_tables:
        raise HostConfigError(
            f"{path}: unknown configuration table(s) {', '.join(unknown_tables)}; "
            "only [host] is supported"
        )
    table = payload.get("host", {})
    if not isinstance(table, dict):
        raise HostConfigError(f"{path}: field host must be a table")
    unknown_fields = sorted(set(table) - _HOST_FIELDS)
    if unknown_fields:
        raise HostConfigError(
            f"{path}: unknown host field(s) {', '.join(unknown_fields)}; "
            f"expected {', '.join(sorted(_HOST_FIELDS))}"
        )
    for field in sorted(table):
        if not _nonempty(table[field]):
            raise HostConfigError(
                f"{path}: field host.{field} must be a nonempty string "
                f"(got {type(table[field]).__name__})"
            )
        assert isinstance(table[field], str)
        _validate_path_field(field, table[field], str(path))
    return {
        field: value
        for field, value in table.items()
        if isinstance(value, str)
    }


def _detect_wgp_root(repository_root: Path) -> Path | None:
    """Find a local Wan2GP checkout using filesystem markers only."""

    candidates = (
        repository_root / "Wan2GP",
        repository_root.parent / "Wan2GP",
        Path.cwd().resolve() / "Wan2GP",
    )
    for candidate in candidates:
        try:
            if (candidate / "wgp.py").is_file():
                return candidate.resolve()
        except OSError:
            continue
    return None


def _default_pull_root(repository_root: Path, environ: Mapping[str, str]) -> Path:
    """Keep source runs local, but never derive data from site-packages."""

    if (repository_root / "pyproject.toml").is_file():
        return repository_root / "datasets" / "runs" / "pull"
    selected_data = environ.get("XDG_DATA_HOME", "").strip()
    data_home = (
        Path(selected_data).expanduser()
        if selected_data
        else Path.home() / ".local" / "share"
    )
    return data_home / "wangp" / "runs" / "pull"


def _actionable_message(keys: tuple[str, ...], config: HostConfig) -> str:
    environment = ", ".join(ENVIRONMENT_KEYS[key] for key in keys)
    file_keys = ", ".join(keys)
    return (
        f"render host is not configured: missing {file_keys}. "
        f"Set {environment}, or set those keys in {config.repository_config} "
        f"or {config.user_config}; then run 'wgp doctor' to review resolution. "
        "The no-GPU planning lane does not require a host."
    )


def require_host_config(config: HostConfig) -> HostConfig:
    """Fail closed before SSH construction when any host key is absent."""

    missing = missing_host_keys(config)
    if missing:
        raise HostConfigError(_actionable_message(missing, config))
    return config


def require_wgp_python(config: HostConfig) -> HostSetting:
    """Return the explicit Wan2GP interpreter without requiring SSH keys."""

    if config.wgp_python is None:
        raise HostConfigError(
            _actionable_message(("host.wgp_python",), config)
        )
    return config.wgp_python


def host_config_error(
    config: HostConfig, keys: tuple[str, ...]
) -> HostConfigError:
    """Build the shared actionable error for the supplied host keys."""

    return HostConfigError(_actionable_message(keys, config))


def load_host_config(
    *,
    repository_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> HostConfig:
    """Resolve host settings as environment, user file, repo file, detection."""

    environment = os.environ if environ is None else environ
    root = repository_root.expanduser().resolve() if repository_root else _repository_root()
    repository_path = root / "wangp.toml"
    user_path = _user_config_path(environment)

    layers: list[tuple[str, Path | None, dict[str, str] | None]] = []
    for key, variable in ENVIRONMENT_KEYS.items():
        value = environment.get(variable, "")
        if _nonempty(value):
            assert isinstance(value, str)
            field = key.removeprefix("host.")
            value = _validate_path_field(
                field, value, f"environment {variable}"
            )
            layers.append((key, None, {key.removeprefix("host."): value}))
    if user_path.is_file():
        user_values = _read_host_table(user_path, "user config")
        layers.extend(
            (f"host.{field}", user_path, user_values)
                for field in _FIELD_NAMES
        )
    if repository_path.is_file():
        repository_values = _read_host_table(
            repository_path, "repository config"
        )
        layers.extend(
            (f"host.{field}", repository_path, repository_values)
                for field in _FIELD_NAMES
        )

    resolved: dict[str, HostSetting] = {}
    for key, origin, values in layers:
        field = key.removeprefix("host.")
        if field in resolved:
            continue
        if field in values:
            source = "environment" if origin is None else (
                "user_config" if origin == user_path else "repository_config"
            )
            resolved[field] = HostSetting(
                key=key, value=values[field], source=source, origin=origin
            )

    detected_root = _detect_wgp_root(root)
    # Local detection is all-or-nothing. Filling only one side of target/root
    # for an explicit setting would combine two machines into one host.
    if detected_root is not None and not any(
        field in resolved for field in ("target", "wgp_root")
    ):
        resolved["wgp_root"] = HostSetting(
            key="host.wgp_root",
            value=str(detected_root),
            source="detection",
            origin=detected_root,
        )
        resolved["target"] = HostSetting(
            key="host.target", value="localhost", source="detection"
        )
    if "pull_root" not in resolved:
        detected_pull = _default_pull_root(root, environment)
        resolved["pull_root"] = HostSetting(
            key="host.pull_root",
            value=str(detected_pull),
            source="detection",
            origin=root,
        )
    if "wgp_python" not in resolved:
        local_target = resolved.get("target")
        if local_target is not None and local_target.value == "localhost":
            interpreter = Path(sys.executable).resolve()
            resolved["wgp_python"] = HostSetting(
                key="host.wgp_python",
                value=str(interpreter),
                source="detection",
                origin=interpreter,
            )

    return HostConfig(
        target=resolved.get("target"),
        wgp_root=resolved.get("wgp_root"),
        pull_root=resolved.get("pull_root"),
        wgp_python=resolved.get("wgp_python"),
        repository_root=root,
        repository_config=repository_path,
        user_config=user_path,
    )


def render_host(config: HostConfig) -> SshHost:
    """Construct the existing SSH seam only from a complete configuration."""

    from host.render_host import SshHost

    require_host_config(config)
    assert config.target is not None
    assert config.wgp_root is not None
    assert config.pull_root is not None
    return SshHost(
        target=config.target.value,
        wgp_root=config.wgp_root.value,
        pull_root=config.pull_root.value,
    )


__all__ = [
    "ALL_HOST_KEYS",
    "ENVIRONMENT_KEYS",
    "HOST_KEYS",
    "HostConfig",
    "HostConfigError",
    "HostSetting",
    "load_host_config",
    "missing_host_keys",
    "host_config_error",
    "render_host",
    "require_host_config",
    "require_wgp_python",
]
