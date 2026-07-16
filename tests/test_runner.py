"""WP-05 runner, prompt loader, and cache tests."""

from __future__ import annotations

import asyncio
import importlib
import json
import textwrap
from pathlib import Path
from typing import Any

import pytest

from indexing_v2.contracts import RunVariant, SourceUnit, UnitLabel
from indexing_v2.extraction import prompts, runner
from indexing_v2.extraction.prompts import PromptRenderError, PromptTemplate, load_prompt
from indexing_v2.extraction.runner import (
    DEFAULT_CACHE_ROOT,
    LLMClient,
    RuleGroupOutput,
    RunOutput,
    SharedLLMClient,
    cache_path,
    chat_cached,
    clear_brand_cache,
    complete_json_cached,
    make_cache_key,
    make_content_hash,
    normalize_rule_groups,
    normalize_token_ids,
    render_units,
    run_extraction,
    select_units,
    validate_rule_refs,
)
from shared.llm import Usage
from tests.fakes import FIXTURE_ROOT, FakeLLM, MINIBIBLE_BRAND

RULE_NAV_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_LLM_ROOT = FIXTURE_ROOT / "llm"


def _read_jsonl_dicts(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.fixture
def minibible_units() -> list[SourceUnit]:
    rows = _read_jsonl_dicts(FIXTURE_ROOT / "expected" / "units.jsonl")
    return [SourceUnit.model_validate(row) for row in rows]


@pytest.fixture
def minibible_labels() -> list[UnitLabel]:
    rows = _read_jsonl_dicts(FIXTURE_ROOT / "expected" / "labels.jsonl")
    return [UnitLabel.model_validate(row) for row in rows]


@pytest.fixture
def prompt_dir(tmp_path: Path) -> Path:
    templates = {
        "tokens_primitive": textwrap.dedent(
            """\
            ---SYSTEM---
            primitive system
            ---USER---
            brand={brand}
            units:
            {units}
            """
        ),
        "tokens_semantic": textwrap.dedent(
            """\
            ---SYSTEM---
            semantic system
            ---USER---
            brand={brand}
            primitives:
            {primitives}
            units:
            {units}
            """
        ),
        "catalog_rest": textwrap.dedent(
            """\
            ---SYSTEM---
            catalog system
            ---USER---
            brand={brand}
            tokens:
            {tokens}
            units:
            {units}
            """
        ),
        "rules_cluster": textwrap.dedent(
            """\
            ---SYSTEM---
            rules system
            ---USER---
            brand={brand}
            doc_ref={doc_ref}
            group_id={group_id}
            catalog:
            {catalog}
            units:
            {units}
            """
        ),
    }
    for name, body in templates.items():
        (tmp_path / f"{name}.md").write_text(body, encoding="utf-8")
    return tmp_path


def test_render_units_preserves_text() -> None:
    units = [
        SourceUnit(
            unit_id="u_a",
            brand_id="b",
            doc_ref="d[0]",
            ordinal=0,
            start=0,
            end=12,
            kind="sentence",
            text="hello world\n",
        ),
        SourceUnit(
            unit_id="u_b",
            brand_id="b",
            doc_ref="d[0]",
            ordinal=1,
            start=12,
            end=18,
            kind="blank",
            text="\n\n",
        ),
    ]
    rendered = render_units(units)
    assert rendered == "[u_a] (sentence) hello world\n[u_b] (blank) \n\n"


def test_render_units_starts_adjacent_sentence_headers_on_new_lines() -> None:
    units = [
        SourceUnit(
            unit_id="u_a",
            brand_id="b",
            doc_ref="d[0]",
            ordinal=0,
            start=0,
            end=6,
            kind="sentence",
            text="first ",
        ),
        SourceUnit(
            unit_id="u_b",
            brand_id="b",
            doc_ref="d[0]",
            ordinal=1,
            start=6,
            end=12,
            kind="sentence",
            text="second",
        ),
    ]

    assert render_units(units) == "[u_a] (sentence) first \n[u_b] (sentence) second"


def test_select_units_keeps_all_classifications_by_default(
    minibible_units: list[SourceUnit],
    minibible_labels: list[UnitLabel],
) -> None:
    del minibible_labels
    selected = select_units(minibible_units)
    selected_ids = {unit.unit_id for unit in selected}
    assert len(selected) == len(minibible_units)
    assert "u_brand_foundation_0_0001" in selected_ids
    assert "u_brand_foundation_0_0046" in selected_ids
    assert "u_brand_foundation_0_0048" in selected_ids

    excluded = select_units(
        minibible_units,
        exclude_unit_ids={"u_brand_foundation_0_0046"},
    )
    assert "u_brand_foundation_0_0046" not in {unit.unit_id for unit in excluded}


def test_prompt_template_strict_render() -> None:
    template = PromptTemplate(
        name="demo",
        system="sys {brand}",
        user="hello {name}",
        template_hash="abc",
    )
    rendered = template.render(brand="minibible", name="world")
    assert rendered.system == "sys minibible"
    assert rendered.user == "hello world"
    with pytest.raises(PromptRenderError) as exc:
        template.render()
    assert exc.value.missing == ["brand", "name"]

    # Injected values may contain brace tokens (e.g. {{fn1}}); they are data, not template keys.
    rendered_braces = template.render(brand="{unknown}", name="world")
    assert rendered_braces.system == "sys {unknown}"
    assert rendered_braces.user == "hello world"


def test_normalize_rule_groups_assigns_ids_and_maps_relations() -> None:
    groups = [
        RuleGroupOutput(
            group_id="grp_lisraya_other_00",
            doc_ref="other_rules[0]",
            original_text="x",
            rules=[
                {
                    "slug": "footnote_symbols_assembly_assigned",
                    "rule_text": "Use {{fn1}} placeholders.",
                },
                {
                    "slug": "footnote_symbols_assembly_assigned",
                    "rule_text": "Duplicate slug gets suffix.",
                },
                {
                    "slug": "section_metadata_declaration",
                    "rule_text": "Declare section metadata.",
                },
            ],
            relations=[
                {
                    "src_slug": "section_metadata_declaration",
                    "dst_slug": "footnote_symbols_assembly_assigned",
                    "relation": "refines",
                }
            ],
        )
    ]
    normalized = normalize_rule_groups("lisraya", groups)
    rules = normalized[0].rules
    assert rules[0]["id"] == "rule_lisraya_footnote_symbols_assembly_assigned"
    assert rules[1]["id"] == "rule_lisraya_footnote_symbols_assembly_assigned_2"
    assert rules[2]["id"] == "rule_lisraya_section_metadata_declaration"
    relation = normalized[0].relations[0]
    assert relation["src_rule_id"] == rules[2]["id"]
    # Duplicate slug map keeps the last assignment (v1 Pass C behavior).
    assert relation["dst_rule_id"] == rules[1]["id"]
    again = normalize_rule_groups("lisraya", normalized)
    assert again[0].rules[0]["id"] == rules[0]["id"]
    assert again[0].rules[1]["id"] == rules[1]["id"]


def test_normalize_token_ids_renames_cross_kind_collision() -> None:
    primitives = [
        {
            "id": "tok_lisraya_motion_max_duration",
            "key": "motion.gif.max_duration_5s",
            "kind": "primitive",
            "value": {"default": "~5s"},
        }
    ]
    semantics = [
        {
            "id": "tok_lisraya_motion_max_duration",
            "key": "motion.gif.max_duration",
            "kind": "semantic",
            "value": {"default": {"$ref": "tok_lisraya_motion_max_duration"}},
        }
    ]
    prim_out, sem_out = normalize_token_ids("lisraya", primitives, semantics)
    assert prim_out[0]["id"] == "tok_lisraya_motion_max_duration"
    assert sem_out[0]["id"] == "tok_lisraya_motion_gif_max_duration"
    assert sem_out[0]["value"]["default"]["$ref"] == "tok_lisraya_motion_max_duration"
    # Idempotent once ids no longer collide.
    _, again = normalize_token_ids("lisraya", prim_out, sem_out)
    assert again[0]["id"] == sem_out[0]["id"]


def test_normalize_token_ids_rewrites_key_derived_refs() -> None:
    primitives = [
        {
            "id": "tok_lisraya_size_icon_badge_margin_top",
            "key": "size.icon.badge_margin_top_neg40",
            "kind": "primitive",
            "value": {"default": "-40px"},
        }
    ]
    semantics = [
        {
            "id": "tok_lisraya_icon_badge_margin_top",
            "key": "icon.badge.margin_top",
            "kind": "semantic",
            "value": {
                "default": {"$ref": "tok_lisraya_size_icon_badge_margin_top_neg40"},
                "variants": [
                    {
                        "when": {"theme": "dark"},
                        "value": {"$ref": "tok_lisraya_size_icon_badge_margin_top_neg40"},
                    }
                ],
            },
        }
    ]
    _, sem_out = normalize_token_ids("lisraya", primitives, semantics)
    assert sem_out[0]["value"]["default"]["$ref"] == "tok_lisraya_size_icon_badge_margin_top"
    assert (
        sem_out[0]["value"]["variants"][0]["value"]["$ref"]
        == "tok_lisraya_size_icon_badge_margin_top"
    )


def test_token_lines_include_aliases_and_ref_validation() -> None:
    rendered = runner._token_lines(
        [
            {
                "id": "tok_x_spacing_a",
                "key": "spacing.a",
                "value": {"default": "8px"},
                "aliases": ["space small"],
            }
        ]
    )
    assert 'aliases=["space small"]' in rendered
    violations = validate_rule_refs(
        [
            {
                "slug": "bad",
                "effect": [{"token_id": "tok_x_a_spacing"}],
            }
        ],
        {"tok_x_spacing_a"},
    )
    assert violations[0].unknown_ids == ["tok_x_a_spacing"]


@pytest.mark.asyncio
async def test_reference_violation_retries_with_isolated_cache_key(
    prompt_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str | None, str]] = []

    class RefRetryLLM:
        async def complete_json(
            self,
            model: str,
            system: str,
            user: str,
            max_tokens: int = 16_000,
            usage: Usage | None = None,
            *,
            prompt_name: str,
            cache_key: str | None = None,
        ) -> dict[str, Any]:
            del model, system, max_tokens, usage
            calls.append((prompt_name, cache_key, user))
            if prompt_name == "tokens_primitive":
                return {
                    "tokens": [
                        {
                            "id": "tok_x_spacing_a",
                            "key": "spacing.a",
                            "value": {"default": "8px"},
                        }
                    ]
                }
            if prompt_name == "tokens_semantic":
                return {"tokens": []}
            if prompt_name == "catalog_rest":
                return {"assets": [], "subtypes": [], "templates": []}
            rule_calls = sum(name == "rules_cluster" for name, _, _ in calls)
            token_id = "tok_x_a_spacing" if rule_calls == 1 else "tok_x_spacing_a"
            return {
                "rules": [
                    {
                        "slug": "spacing_rule",
                        "effect": [{"element_path": "a", "token_id": token_id}],
                    }
                ],
                "relations": [],
                "missing_token_requests": [],
            }

        async def chat(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise AssertionError("chat not expected")

    monkeypatch.setattr(runner.settings, "REF_RETRIES", 2)
    unit = SourceUnit(
        unit_id="u_x",
        brand_id="x",
        doc_ref="doc[0]",
        ordinal=0,
        start=0,
        end=9,
        kind="sentence",
        text="A is 8px.",
    )
    output = await run_extraction(
        "x",
        RunVariant(run_id="r0", model="fake"),
        [unit],
        [],
        Usage(),
        RefRetryLLM(),
        prompts_dir=prompt_dir,
        cache_root=tmp_path / "cache",
    )
    assert output.rule_groups[0].rules[0]["effect"][0]["token_id"] == "tok_x_spacing_a"
    rule_calls = [call for call in calls if call[0] == "rules_cluster"]
    assert len(rule_calls) == 2
    assert rule_calls[0][1] != rule_calls[1][1]
    assert "REFERENCE CONTRACT VIOLATIONS" in rule_calls[1][2]


@pytest.mark.asyncio
async def test_reference_terminal_fallback_moves_unknown_to_request(
    prompt_dir: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class TerminalLLM:
        async def complete_json(
            self,
            model: str,
            system: str,
            user: str,
            max_tokens: int = 16_000,
            usage: Usage | None = None,
            *,
            prompt_name: str,
            cache_key: str | None = None,
        ) -> dict[str, Any]:
            del model, system, user, max_tokens, usage, cache_key
            if prompt_name == "tokens_primitive":
                return {"tokens": [{"id": "tok_x_good", "key": "x.good", "value": {"default": "8px"}}]}
            if prompt_name == "tokens_semantic":
                return {"tokens": []}
            if prompt_name == "catalog_rest":
                return {"assets": [], "subtypes": [], "templates": []}
            return {
                "rules": [
                    {
                        "slug": "bad",
                        "effect": [{"element_path": "x", "token_id": "tok_x_invented"}],
                        "evidence": {"unit_ids": ["u_x"], "quotes": ["8px"]},
                    }
                ],
                "relations": [],
            }

        async def chat(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise AssertionError("chat not expected")

    monkeypatch.setattr(runner.settings, "REF_RETRIES", 0)
    unit = SourceUnit(
        unit_id="u_x",
        brand_id="x",
        doc_ref="doc[0]",
        ordinal=0,
        start=0,
        end=3,
        kind="sentence",
        text="8px",
    )
    output = await run_extraction(
        "x",
        RunVariant(run_id="r0", model="fake"),
        [unit],
        [],
        Usage(),
        TerminalLLM(),
        prompts_dir=prompt_dir,
        cache_root=tmp_path / "cache",
    )
    group = output.rule_groups[0]
    assert group.rules[0]["effect"] == []
    assert group.rules[0]["unresolved_refs"] == ["tok_x_invented"]
    assert group.missing_token_requests[0]["for_rule_slug"] == "bad"


def test_load_prompt_frontmatter_and_separator(tmp_path: Path) -> None:
    frontmatter = tmp_path / "with_meta.md"
    frontmatter.write_text(
        "---\nsystem: |\n  meta-system\nuser: |\n  brand={brand}\n---\nignored\n",
        encoding="utf-8",
    )
    loaded = load_prompt("with_meta", tmp_path)
    assert loaded.system == "meta-system"
    assert loaded.render(brand="x").user == "brand=x"

    separated = tmp_path / "separated.md"
    separated.write_text("---SYSTEM---\ns\n---USER---\nu={value}\n", encoding="utf-8")
    loaded_sep = load_prompt("separated", tmp_path)
    assert loaded_sep.render(value="1").user.strip() == "u=1"


def test_make_cache_key_changes_with_variant_and_template() -> None:
    variant_a = RunVariant(run_id="r0", model="m1", temperature=0.0, replicate=0)
    variant_b = RunVariant(run_id="r1", model="m1", temperature=0.4, replicate=1)
    content = make_content_hash(system="s", user="u")
    key_a = make_cache_key(
        prompt_name="tokens_primitive",
        template_hash="hash_a",
        variant=variant_a,
        content_hash=content,
    )
    key_b = make_cache_key(
        prompt_name="tokens_primitive",
        template_hash="hash_b",
        variant=variant_a,
        content_hash=content,
    )
    key_c = make_cache_key(
        prompt_name="tokens_primitive",
        template_hash="hash_a",
        variant=variant_b,
        content_hash=content,
    )
    assert key_a != key_b
    assert key_a != key_c


@pytest.mark.asyncio
async def test_complete_json_cached_hit_skips_llm(tmp_path: Path) -> None:
    calls: list[str] = []

    class RecordingLLM:
        async def complete_json(
            self,
            model: str,
            system: str,
            user: str,
            max_tokens: int = 16_000,
            usage: Usage | None = None,
            *,
            prompt_name: str,
            cache_key: str | None = None,
        ) -> dict[str, Any]:
            del model, system, user, max_tokens, prompt_name, cache_key
            calls.append("call")
            if usage is not None:
                usage.add("fake", 10, 5)
            return {"ok": True}

        async def chat(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            raise AssertionError("chat not expected")

    template = PromptTemplate(name="p", system="s", user="u", template_hash="t1")
    variant = RunVariant(run_id="r0", model="fake", temperature=0.0, replicate=0)
    ctx = runner.CacheContext(
        brand="brand",
        variant=variant,
        prompt_name="p",
        template=template,
        content_hash="",
        cache_root=tmp_path,
    )
    usage = Usage()
    client = RecordingLLM()
    first = await complete_json_cached(client, ctx, "s", "u", usage, force=True)
    second = await complete_json_cached(client, ctx, "s", "u", usage)
    assert first == second == {"ok": True}
    assert calls == ["call"]
    assert usage.llm_calls == 1


@pytest.mark.asyncio
async def test_prompt_edit_changes_cache_key(tmp_path: Path) -> None:
    path = tmp_path / "tokens_primitive.md"
    path.write_text("---USER---\n{units}\n", encoding="utf-8")
    template_v1 = load_prompt("tokens_primitive", tmp_path)
    key_v1 = make_cache_key(
        prompt_name="tokens_primitive",
        template_hash=template_v1.template_hash,
        variant=RunVariant(run_id="r0", model="m", temperature=0.0, replicate=0),
        content_hash=make_content_hash(system="", user="body"),
    )

    path.write_text("---USER---\n{units}\n# edited\n", encoding="utf-8")
    template_v2 = load_prompt("tokens_primitive", tmp_path)
    key_v2 = make_cache_key(
        prompt_name="tokens_primitive",
        template_hash=template_v2.template_hash,
        variant=RunVariant(run_id="r0", model="m", temperature=0.0, replicate=0),
        content_hash=make_content_hash(system="", user="body"),
    )
    assert key_v1 != key_v2


@pytest.mark.asyncio
async def test_chat_cached_serializes_dict_results(tmp_path: Path) -> None:
    class DictChatLLM:
        async def complete_json(self, *args: Any, **kwargs: Any) -> Any:
            raise AssertionError("complete_json not expected")

        async def chat(
            self,
            model: str,
            system: str,
            messages: list[dict[str, Any]],
            *,
            prompt_name: str,
            cache_key: str | None = None,
            usage: Usage | None = None,
            max_tokens: int = 16_000,
            **_: Any,
        ) -> dict[str, Any]:
            del model, system, messages, prompt_name, cache_key, usage, max_tokens
            return {"role": "assistant", "content": "{\"x\": 1}"}

    template = PromptTemplate(name="chat", system="s", user="", template_hash="h")
    ctx = runner.CacheContext(
        brand="b",
        variant=RunVariant(run_id="r0", model="m", temperature=0.0, replicate=0),
        prompt_name="chat",
        template=template,
        content_hash="",
        cache_root=tmp_path,
    )
    usage = Usage()
    out = await chat_cached(
        DictChatLLM(),
        ctx,
        "s",
        [{"role": "user", "content": "hi"}],
        usage,
        force=True,
    )
    assert out["content"] == "{\"x\": 1}"
    cached_path = next((tmp_path / "b" / "chat").glob("*.json"))
    cached = json.loads(cached_path.read_text(encoding="utf-8"))
    assert cached["role"] == "assistant"


@pytest.mark.asyncio
async def test_run_extraction_with_fake_llm(
    minibible_units: list[SourceUnit],
    minibible_labels: list[UnitLabel],
    prompt_dir: Path,
    tmp_path: Path,
) -> None:
    llm = FakeLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND)
    usage = Usage()
    cache_root = tmp_path / "cache"
    work_dir = tmp_path / "work"
    variant = RunVariant(run_id="r0", model="fake-model", temperature=0.0, replicate=0)

    output = await run_extraction(
        MINIBIBLE_BRAND,
        variant,
        minibible_units,
        minibible_labels,
        usage,
        llm,
        prompts_dir=prompt_dir,
        cache_root=cache_root,
        work_dir=work_dir,
        force=True,
    )

    assert isinstance(output, RunOutput)
    assert output.schema_version == "2.0"
    assert output.variant.run_id == "r0"
    assert output.primitive_tokens
    assert output.semantic_tokens
    assert output.catalog_rest == {"assets": [], "subtypes": [], "templates": []}
    assert set(output.rules_by_doc_ref) == {"brand_foundation[0]", "layout_constraints[0]"}
    assert len(llm.calls()) == 5
    assert usage.llm_calls == 5

    primitive_call = next(call for call in llm.calls() if call.prompt_name == "tokens_primitive")
    assert "[u_brand_foundation_0_0001] (blank) " in primitive_call.user
    narrative = next(
        unit.text
        for unit in minibible_units
        if unit.unit_id == "u_brand_foundation_0_0046"
    )
    assert narrative in primitive_call.user
    brand_rules_call = next(
        call
        for call in llm.calls()
        if call.prompt_name == "rules_cluster" and "doc_ref=brand_foundation[0]" in call.user
    )
    assert "[u_brand_foundation_0_0001] (blank) " in brand_rules_call.user
    assert narrative in brand_rules_call.user

    blobs = json.loads((FIXTURE_ROOT / "blobs.json").read_text(encoding="utf-8"))
    for group in output.rule_groups:
        assert group.schema_version == "2.0"
        assert group.original_text == blobs[group.doc_ref]

    run_dir = work_dir / "runs" / variant.run_id
    expected_paths = {
        "catalog_rest.json",
        "rules/grp_minibible_brand_foundation_00.json",
        "rules/grp_minibible_layout_constraints_00.json",
        "tokens_primitive.json",
        "tokens_semantic.json",
    }
    assert {
        path.relative_to(run_dir).as_posix()
        for path in run_dir.rglob("*.json")
    } == expected_paths
    assert json.loads((run_dir / "tokens_primitive.json").read_text(encoding="utf-8")) == (
        output.primitive_tokens
    )
    assert json.loads((run_dir / "tokens_semantic.json").read_text(encoding="utf-8")) == (
        output.semantic_tokens
    )
    assert json.loads((run_dir / "catalog_rest.json").read_text(encoding="utf-8")) == (
        output.catalog_rest
    )
    for group in output.rule_groups:
        artifact = json.loads(
            (run_dir / "rules" / f"{group.group_id}.json").read_text(encoding="utf-8")
        )
        assert artifact == group.model_dump(mode="json")

    assert not (work_dir / "result.json").exists()
    assert not (work_dir / "rules_by_doc_ref.json").exists()
    first_artifacts = {
        path.relative_to(run_dir).as_posix(): path.read_text(encoding="utf-8")
        for path in run_dir.rglob("*.json")
    }
    await run_extraction(
        MINIBIBLE_BRAND,
        variant,
        minibible_units,
        minibible_labels,
        Usage(),
        FakeLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND),
        prompts_dir=prompt_dir,
        cache_root=cache_root,
        work_dir=work_dir,
        force=True,
    )
    assert {
        path.relative_to(run_dir).as_posix(): path.read_text(encoding="utf-8")
        for path in run_dir.rglob("*.json")
    } == first_artifacts


@pytest.mark.asyncio
async def test_a1b_receives_same_run_a1a_primitives(
    minibible_units: list[SourceUnit],
    minibible_labels: list[UnitLabel],
    prompt_dir: Path,
    tmp_path: Path,
) -> None:
    captured: dict[str, str] = {}

    class ChainLLM(FakeLLM):
        async def complete_json(
            self,
            model: str,
            system: str,
            user: str,
            max_tokens: int = 16_000,
            usage: Usage | None = None,
            *,
            prompt_name: str,
            cache_key: str | None = None,
        ) -> Any:
            if prompt_name == "tokens_semantic":
                captured["semantic_user"] = user
            return await super().complete_json(
                model,
                system,
                user,
                max_tokens=max_tokens,
                usage=usage,
                prompt_name=prompt_name,
                cache_key=cache_key,
            )

    llm = ChainLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND)
    output = await run_extraction(
        MINIBIBLE_BRAND,
        RunVariant(run_id="r0", model="fake-model", temperature=0.0, replicate=0),
        minibible_units,
        minibible_labels,
        Usage(),
        llm,
        prompts_dir=prompt_dir,
        cache_root=tmp_path / "cache",
        force=True,
    )
    assert "tok_minibible_color_primary_green_01" in captured["semantic_user"]
    assert any(token["id"] == "tok_minibible_color_primary_green_01" for token in output.primitive_tokens)


@pytest.mark.asyncio
async def test_run_extraction_respects_semaphore_limit(
    minibible_units: list[SourceUnit],
    minibible_labels: list[UnitLabel],
    prompt_dir: Path,
    tmp_path: Path,
) -> None:
    active = 0
    peak = 0
    lock = asyncio.Lock()

    class SlowLLM(FakeLLM):
        async def complete_json(self, *args: Any, **kwargs: Any) -> Any:
            nonlocal active, peak
            async with lock:
                active += 1
                peak = max(peak, active)
            try:
                await asyncio.sleep(0.05)
                return await super().complete_json(*args, **kwargs)
            finally:
                async with lock:
                    active -= 1

    await run_extraction(
        MINIBIBLE_BRAND,
        RunVariant(run_id="r0", model="fake-model", temperature=0.0, replicate=0),
        minibible_units,
        minibible_labels,
        Usage(),
        SlowLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND),
        prompts_dir=prompt_dir,
        cache_root=tmp_path / "cache",
        concurrency=2,
        force=True,
    )
    assert peak <= 2


@pytest.mark.asyncio
async def test_run_extraction_rejects_nonpositive_concurrency(
    minibible_units: list[SourceUnit],
    minibible_labels: list[UnitLabel],
    prompt_dir: Path,
    tmp_path: Path,
) -> None:
    cache_root = tmp_path / "cache"
    with pytest.raises(ValueError, match="concurrency must be greater than zero"):
        await run_extraction(
            MINIBIBLE_BRAND,
            RunVariant(run_id="r0", model="fake-model", temperature=0.0, replicate=0),
            minibible_units,
            minibible_labels,
            Usage(),
            FakeLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND),
            prompts_dir=prompt_dir,
            cache_root=cache_root,
            concurrency=0,
            force=True,
        )
    assert not cache_root.exists()


@pytest.mark.asyncio
async def test_force_clears_brand_cache_only(
    minibible_units: list[SourceUnit],
    minibible_labels: list[UnitLabel],
    prompt_dir: Path,
    tmp_path: Path,
) -> None:
    cache_root = tmp_path / "cache"
    other_brand_dir = cache_root / "other" / "tokens_primitive"
    other_brand_dir.mkdir(parents=True)
    stale = other_brand_dir / "deadbeef.json"
    stale.write_text("{}", encoding="utf-8")

    llm = FakeLLM(fixture_root=FIXTURE_LLM_ROOT, brand=MINIBIBLE_BRAND)
    await run_extraction(
        MINIBIBLE_BRAND,
        RunVariant(run_id="r0", model="fake-model", temperature=0.0, replicate=0),
        minibible_units,
        minibible_labels,
        Usage(),
        llm,
        prompts_dir=prompt_dir,
        cache_root=cache_root,
        force=True,
    )
    assert (cache_root / MINIBIBLE_BRAND).exists()
    assert stale.is_file()


def test_runner_has_no_module_level_llm_client() -> None:
    for name, value in vars(runner).items():
        if name.startswith("_"):
            continue
        assert not isinstance(value, SharedLLMClient), f"module-global client: {name}"
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "shared_complete_json" in source
    assert "shared_chat" in source
    assert "Usage" in source
    prompts_source = Path(prompts.__file__).read_text(encoding="utf-8")
    assert "shared.llm" not in prompts_source


def test_shared_llm_client_satisfies_protocol() -> None:
    assert isinstance(SharedLLMClient(), LLMClient)


def test_cache_path_layout() -> None:
    template = PromptTemplate(name="tokens_primitive", system="", user="", template_hash="h")
    ctx = runner.CacheContext(
        brand="minibible",
        variant=RunVariant(run_id="r0", model="m", temperature=0.0, replicate=0),
        prompt_name="tokens_primitive",
        template=template,
        content_hash="",
        cache_root=DEFAULT_CACHE_ROOT,
    )
    path = cache_path(ctx, "abc123")
    assert path == DEFAULT_CACHE_ROOT / "minibible" / "tokens_primitive" / "abc123.json"


def test_clear_brand_cache(tmp_path: Path) -> None:
    brand_dir = tmp_path / "brand" / "tokens_primitive"
    brand_dir.mkdir(parents=True)
    (brand_dir / "k.json").write_text("{}", encoding="utf-8")
    clear_brand_cache("brand", tmp_path)
    assert not (tmp_path / "brand").exists()


def test_gap_round_and_cache_bust_affect_content_hash() -> None:
    base = make_content_hash(system="s", user="u")
    with_gap = make_content_hash(system="s", user="u", gap_round=1)
    with_bust = make_content_hash(system="s", user="u", cache_bust="x")
    assert len({base, with_gap, with_bust}) == 3


def test_runner_import_has_no_prompt_files_required() -> None:
    importlib.reload(prompts)
    importlib.reload(runner)
    assert runner.STAGE_VERSION
