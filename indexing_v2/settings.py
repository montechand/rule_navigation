"""v2 configuration surface: env overrides, shared.config fallbacks, pipeline defaults."""

from __future__ import annotations

import os

from shared import config

from .contracts import RunVariant

_DEFAULT_CLASSIFY_MODEL = "claude-sonnet-5"
_DEFAULT_EXTRACT_MODEL = "claude-opus-4-8"
_DEFAULT_CRITIC_MODEL = "claude-sonnet-5"
_DEFAULT_SECONDARY_MODEL = _DEFAULT_CRITIC_MODEL
_DEFAULT_TRIAGE_FILE = "review/triage.jsonl"
_DEFAULT_DTCG_NAMESPACE = "com.solstice.kb"

_ENV_KEYS: dict[str, str] = {
    "CLASSIFY_MODEL": "RULE_NAV_CLASSIFY_MODEL",
    "EXTRACT_MODEL": "RULE_NAV_EXTRACT_MODEL",
    "CRITIC_MODEL": "RULE_NAV_CRITIC_MODEL",
    "SECONDARY_MODEL": "RULE_NAV_SECONDARY_MODEL",
    "MAX_CRITIC_ROUNDS": "RULE_NAV_MAX_CRITIC_ROUNDS",
    "MAX_GAP_ROUNDS": "RULE_NAV_MAX_GAP_ROUNDS",
    "TRIAGE_FILE": "RULE_NAV_TRIAGE_FILE",
    "FUZZY_MATCH_MIN_RATIO": "RULE_NAV_FUZZY_MATCH_MIN_RATIO",
    "DTCG_NAMESPACE": "RULE_NAV_DTCG_NAMESPACE",
    "CONCURRENCY": "RULE_NAV_CONCURRENCY",
}


def _resolve_str(name: str, default: str) -> str:
    env_key = _ENV_KEYS[name]
    env_val = os.getenv(env_key)
    if env_val is not None:
        return env_val
    return str(getattr(config, name, default))


def _resolve_int(name: str, default: int) -> int:
    env_key = _ENV_KEYS[name]
    env_val = os.getenv(env_key)
    if env_val is not None:
        return int(env_val)
    cfg_val = getattr(config, name, default)
    return int(cfg_val)


def _resolve_float(name: str, default: float) -> float:
    env_key = _ENV_KEYS[name]
    env_val = os.getenv(env_key)
    if env_val is not None:
        return float(env_val)
    cfg_val = getattr(config, name, default)
    return float(cfg_val)


def _default_ensemble_runs(extract_model: str, secondary_model: str) -> list[RunVariant]:
    return [
        RunVariant(run_id="r0", model=extract_model, temperature=0.0, replicate=0),
        RunVariant(run_id="r1", model=extract_model, temperature=0.4, replicate=1),
        RunVariant(run_id="r2", model=secondary_model, temperature=0.2, replicate=0),
    ]


def reload_settings() -> None:
    """Re-read env/config and refresh module-level settings (safe for tests)."""
    global CLASSIFY_MODEL
    global EXTRACT_MODEL
    global CRITIC_MODEL
    global SECONDARY_MODEL
    global ENSEMBLE_RUNS
    global MAX_CRITIC_ROUNDS
    global MAX_GAP_ROUNDS
    global TRIAGE_FILE
    global FUZZY_MATCH_MIN_RATIO
    global DTCG_NAMESPACE
    global CONCURRENCY

    CLASSIFY_MODEL = _resolve_str("CLASSIFY_MODEL", _DEFAULT_CLASSIFY_MODEL)
    EXTRACT_MODEL = _resolve_str("EXTRACT_MODEL", _DEFAULT_EXTRACT_MODEL)
    CRITIC_MODEL = _resolve_str("CRITIC_MODEL", _DEFAULT_CRITIC_MODEL)
    SECONDARY_MODEL = _resolve_str("SECONDARY_MODEL", _DEFAULT_SECONDARY_MODEL)
    ENSEMBLE_RUNS = _default_ensemble_runs(EXTRACT_MODEL, SECONDARY_MODEL)
    MAX_CRITIC_ROUNDS = _resolve_int("MAX_CRITIC_ROUNDS", 2)
    MAX_GAP_ROUNDS = _resolve_int("MAX_GAP_ROUNDS", 3)
    TRIAGE_FILE = _resolve_str("TRIAGE_FILE", _DEFAULT_TRIAGE_FILE)
    FUZZY_MATCH_MIN_RATIO = _resolve_float("FUZZY_MATCH_MIN_RATIO", 0.92)
    DTCG_NAMESPACE = _resolve_str("DTCG_NAMESPACE", _DEFAULT_DTCG_NAMESPACE)
    CONCURRENCY = _resolve_int("CONCURRENCY", 4)


# Initialized on import; call reload_settings() after env changes in tests.
CLASSIFY_MODEL: str
EXTRACT_MODEL: str
CRITIC_MODEL: str
SECONDARY_MODEL: str
ENSEMBLE_RUNS: list[RunVariant]
MAX_CRITIC_ROUNDS: int
MAX_GAP_ROUNDS: int
TRIAGE_FILE: str
FUZZY_MATCH_MIN_RATIO: float
DTCG_NAMESPACE: str
CONCURRENCY: int

reload_settings()
