"""Central configuration: paths, env loading, model defaults.

All API keys come from newest_email_pipeline/.env (never checked in here).
Every model is overridable via RULE_NAV_* env vars.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

RULE_NAV_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = RULE_NAV_ROOT.parent

ENV_PATH = WORKSPACE_ROOT / "newest_email_pipeline" / ".env"
BRAND_RULES_DIR = WORKSPACE_ROOT / "newest_email_pipeline" / "brand_rules"
KB_ROOT = RULE_NAV_ROOT / "kb"
SIMPLE_KB_ROOT = RULE_NAV_ROOT / "simple_kb"
OUTPUTS_DIR = RULE_NAV_ROOT / "outputs"
EXAMPLES_DIR = RULE_NAV_ROOT / "examples"

# Existing env (shell) wins over the .env file.
load_dotenv(ENV_PATH, override=False)

BRANDS = ("lisraya", "ibsrela")

DESIGN_BIBLES = {
    "lisraya": BRAND_RULES_DIR / "design_bible_lisraya_1.json",
    "ibsrela": BRAND_RULES_DIR / "design_bible_ibsrela_1.json",
}

# Concrete approved template libraries (email top/end matter etc.), ingested into
# content_sub_type rows at build time. Absent brands are skipped.
TEMPLATE_LIBRARIES = {
    "ibsrela": RULE_NAV_ROOT / "template_library_202607071034.json",
}

# Models (names match what Backend-Server uses in production today).
AGENT_MODEL = os.getenv("RULE_NAV_AGENT_MODEL", "claude-sonnet-5")
EXTRACT_MODEL = os.getenv("RULE_NAV_EXTRACT_MODEL", "claude-opus-4-8")
SUMMARY_MODEL = os.getenv("RULE_NAV_SUMMARY_MODEL", "gpt-4.1-mini")
EMBED_MODEL = os.getenv("RULE_NAV_EMBED_MODEL", "text-embedding-3-large")


def kb_dir(brand: str) -> Path:
    return KB_ROOT / brand


def simple_kb_dir(brand: str) -> Path:
    return SIMPLE_KB_ROOT / brand


def require_keys() -> None:
    missing = [k for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not os.getenv(k)]
    if missing:
        raise RuntimeError(
            f"Missing API keys {missing}. Expected them in {ENV_PATH} or the environment."
        )
