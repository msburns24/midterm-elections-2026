"""Load the model configuration from ``config/model.toml`` into typed dataclasses."""

import tomllib
from dataclasses import dataclass, fields, is_dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "config" / "model.toml"


@dataclass(frozen=True)
class SimulationConfig:
    n_draws: int
    seed: int


@dataclass(frozen=True)
class PollsConfig:
    window_days: int
    population_priority: tuple[str, ...]
    include_internal: bool
    include_partisan: bool
    half_life_days: float
    sample_size_cap: int


@dataclass(frozen=True)
class PollErrorConfig:
    total_survey_error_factor: float
    bias_floor: float


@dataclass(frozen=True)
class NationalConfig:
    distribution: str
    df: float
    scale: float


@dataclass(frozen=True)
class FactorConfig:
    kind: str
    scale: float


@dataclass(frozen=True)
class RaceNoiseConfig:
    house_sd: float
    senate_sd: float


@dataclass(frozen=True)
class ModelConfig:
    simulation: SimulationConfig
    polls: PollsConfig
    poll_error: PollErrorConfig
    national: NationalConfig
    factor: FactorConfig
    race_noise: RaceNoiseConfig


def load_config(path: Path | str = DEFAULT_PATH) -> ModelConfig:
    """Read and validate the model config TOML at ``path``."""
    return _build_dataclass(ModelConfig, _read_toml(path), "root")


def _read_toml(path: Path | str) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)


def _build_dataclass[T: DataclassInstance](
    cls: type[T], table: dict[str, Any], where: str
) -> T:
    _require_exact_keys(cls, table, where)
    values = {
        f.name: _convert_value(table[f.name], f.type, f"{where}.{f.name}")
        for f in fields(cls)
    }
    return cls(**values)


def _require_exact_keys(cls: "type[DataclassInstance]", table: Any, where: str) -> None:
    if not isinstance(table, dict):
        raise TypeError(f"[{where}] expected a table, got {type(table).__name__}")
    expected = {f.name for f in fields(cls)}
    missing = expected - table.keys()
    unknown = table.keys() - expected
    if missing or unknown:
        raise KeyError(
            f"[{where}] missing keys {sorted(missing)}, unknown keys {sorted(unknown)}"
        )


def _convert_value(value: Any, annotation: Any, where: str) -> Any:
    if is_dataclass(annotation):
        return _build_dataclass(annotation, value, where)
    if annotation == tuple[str, ...]:
        return _convert_string_list(value, where)
    if annotation is float:
        return _convert_float(value, where)
    return _require_type(value, annotation, where)


def _convert_string_list(value: Any, where: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise TypeError(f"{where}: expected a list of strings, got {value!r}")
    return tuple(value)


def _convert_float(value: Any, where: str) -> float:
    # bool is a subclass of int, so it would otherwise pass as a number
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{where}: expected float, got {type(value).__name__}")
    return float(value)


def _require_type(value: Any, annotation: type, where: str) -> Any:
    wrong_bool = isinstance(value, bool) and annotation is not bool
    if wrong_bool or not isinstance(value, annotation):
        raise TypeError(
            f"{where}: expected {annotation.__name__}, got {type(value).__name__}"
        )
    return value
