"""E2 token_table: detection, deterministic compilation, and pipeline hooks.

Fixtures are verbatim SourceUnits from ``kb/lisraya/_work/units.jsonl``
(themselves derived from ``simple_kb/lisraya/design_bible.json``): the palette
tables, the typography hierarchy (markdown table + type-scale spec-list), the
canvas/grid spec-list, and the gradient set.
"""

from __future__ import annotations

import json
from pathlib import Path

from indexing.build_kb import Warnings, build_graph
from indexing_v2.build_kb import validate_table
from indexing_v2.contracts import SourceUnit, read_jsonl, stable_hash
from indexing_v2.extraction.provenance import verify_entities
from indexing_v2.tables import (
    compile_brand_tables,
    detect_table_blocks,
    merge_row_tokens,
    resolve_literal_against_tables,
    table_row_token_ids,
)

FIXTURES = Path(__file__).parent / "fixtures" / "tables"


def _units(name: str) -> list[SourceUnit]:
    return read_jsonl(FIXTURES / f"{name}.jsonl", SourceUnit)


def test_detects_markdown_tables_with_multiple_headers_per_run() -> None:
    blocks = detect_table_blocks(_units("palette"))
    tables = [block for block in blocks if block.kind == "table"]
    # The Complete Palette section holds three separate markdown tables.
    assert len(tables) == 3
    assert tables[0].header == ("Name", "HEX", "RGB", "CMYK", "Pantone")
    assert [len(block.rows) for block in tables] == [3, 3, 5]


def test_detects_spec_lists() -> None:
    blocks = detect_table_blocks(_units("canvas"))
    spec_lists = [block for block in blocks if block.kind == "spec_list"]
    assert len(spec_lists) == 1
    assert spec_lists[0].header == ("item", "value")
    assert len(spec_lists[0].rows) >= 3


def test_classification_heuristics() -> None:
    by_type = {
        block.doc_ref: []  # type: ignore[var-annotated]
        for name in ("palette", "typography", "canvas", "gradients")
        for block in detect_table_blocks(_units(name))
    }
    for name in ("palette", "typography", "canvas", "gradients"):
        for block in detect_table_blocks(_units(name)):
            from indexing_v2.tables import classify_table_type

            by_type[block.doc_ref].append(classify_table_type(block))
    assert set(by_type["color_scheme_rules[0]"]) == {"color_palette"}
    assert "gradient_set" in by_type["color_scheme_rules[3]"]
    assert "typography_scale" in by_type["content_pattern_rules[1]"]
    assert "canvas_spec" in by_type["design_pattern_rules[0]"]


def test_compiled_row_tokens_and_tables_pass_provenance() -> None:
    units = [unit for name in ("palette", "typography", "canvas") for unit in _units(name)]
    compiled = compile_brand_tables("lisraya", units)
    tokens = [token for item in compiled for token in item.row_tokens]
    result = verify_entities(
        {
            "token_primitive": tokens,
            "rule": [item.umbrella_rule for item in compiled],
            "token_table": [item.table for item in compiled],
        },
        units,
    )
    assert tokens
    assert result.quarantine == []


def test_compilation_is_deterministic() -> None:
    units = [unit for name in ("palette", "typography", "gradients") for unit in _units(name)]
    first = compile_brand_tables("lisraya", units)
    second = compile_brand_tables("lisraya", units)
    assert stable_hash([item.table for item in first]) == stable_hash(
        [item.table for item in second]
    )
    assert stable_hash([item.umbrella_rule for item in first]) == stable_hash(
        [item.umbrella_rule for item in second]
    )
    assert stable_hash([item.row_tokens for item in first]) == stable_hash(
        [item.row_tokens for item in second]
    )


def test_umbrella_rule_carries_every_row_token() -> None:
    compiled = compile_brand_tables("lisraya", _units("palette"))
    for item in compiled:
        rule_token_ids = set(item.umbrella_rule["token_ids"])
        assignments = {
            row["token_id"] for row in item.umbrella_rule["effect"]["assignments"]
        }
        minted = {str(token["id"]) for token in item.row_tokens}
        # Cross-table dedupe may reuse earlier tokens, so minted <= carried.
        assert minted <= rule_token_ids
        assert rule_token_ids == assignments


def test_merge_row_tokens_skips_known_ids() -> None:
    compiled = compile_brand_tables("lisraya", _units("palette"))
    existing = [dict(compiled[0].row_tokens[0])]
    merged = merge_row_tokens(existing, compiled)
    ids = [str(token["id"]) for token in merged]
    assert len(ids) == len(set(ids))
    assert set(ids) >= {str(token["id"]) for item in compiled for token in item.row_tokens}


def test_table_row_token_ids_and_literal_resolution() -> None:
    compiled = compile_brand_tables("lisraya", _units("palette"))
    tables = [item.table for item in compiled]
    ids = table_row_token_ids(tables)
    assert ids
    resolved = resolve_literal_against_tables("#00529b", tables)
    assert resolved in ids
    assert resolve_literal_against_tables("nonexistent-literal-xyz", tables) is None


def test_validate_table_filters_uncataloged_refs_and_missing_rule() -> None:
    compiled = compile_brand_tables("lisraya", _units("palette"))
    item = compiled[0]
    catalog_ids = {str(token["id"]) for token in item.row_tokens}
    dropped_id = sorted(catalog_ids)[0]
    warns = Warnings()
    table = validate_table(
        item.table,
        "lisraya",
        catalog_ids - {dropped_id},
        set(),  # umbrella rule did not survive
        warns,
    )
    assert table is not None
    assert table.umbrella_rule_id is None
    remaining = {token_id for row in table.rows for token_id in row.token_ids}
    assert dropped_id not in remaining
    assert any("uncataloged" in warning for warning in warns.items)
    assert any("umbrella rule" in warning for warning in warns.items)


def test_validate_table_rejects_foreign_id_prefix() -> None:
    warns = Warnings()
    assert (
        validate_table({"id": "tok_lisraya_notatable"}, "lisraya", set(), set(), warns)
        is None
    )


def test_graph_gets_member_of_table_and_bound_by_edges() -> None:
    from indexing.build_kb import validate_catalog, validate_rule

    compiled = compile_brand_tables("lisraya", _units("palette"))
    item = compiled[0]
    warns = Warnings()
    catalog = validate_catalog(
        {
            "tokens": [
                {k: v for k, v in token.items() if k not in {"evidence", "entity_kind", "compiled_by"}}
                for token in item.row_tokens
            ],
            "assets": [],
            "subtypes": [],
            "templates": [],
            "template_groups": [],
            "asset_groups": [],
        },
        "lisraya",
        warns,
    )
    rule_raw = {
        k: v
        for k, v in item.umbrella_rule.items()
        if k not in {"evidence", "compiled_by"}
    }
    rule = validate_rule(
        rule_raw, "lisraya", "grp_x", "color_scheme_rules[0]",
        set(), set(catalog["tokens"]), warns, [],
    )
    assert rule is not None
    table = validate_table(
        item.table, "lisraya", set(catalog["tokens"]), {rule.id}, warns,
    )
    assert table is not None
    graph = build_graph({rule.id: rule}, catalog, [], [], tables={table.id: table})
    edges = {(e["src"], e["dst"], e["type"]) for e in graph["edges"]}
    assert (table.id, rule.id, "bound_by") in edges
    member_edges = {e for e in edges if e[2] == "member_of_table" and e[0] == table.id}
    assert member_edges
    nodes = {n["id"]: n for n in graph["nodes"]}
    assert nodes[table.id]["kind"] == "token_table"


def test_render_brand_sheets_includes_global_tables() -> None:
    from indexing_v2.cascade.compile import render_brand_sheets
    from indexing_v2.contracts import KBSnapshot
    from shared.schemas import BrandTokenTable

    compiled = compile_brand_tables("lisraya", _units("palette"))
    warns = Warnings()
    tables = {}
    for item in compiled:
        catalog_ids = {str(token["id"]) for token in item.row_tokens}
        table = validate_table(item.table, "lisraya", catalog_ids, set(), warns)
        assert table is not None
        tables[table.id] = table
    snapshot = KBSnapshot.model_construct(
        brand="lisraya",
        rules={},
        tokens={},
        assets={},
        subtypes={},
        templates={},
        tables=tables,
        predicate_domains={},
    )
    text = render_brand_sheets(snapshot)
    assert "# Brand sheets — lisraya" in text
    for table in tables.values():
        assert table.name in text
    assert "| Name | HEX |" in text
