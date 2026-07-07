#!/usr/bin/env python3
"""Build self-contained, interactive "Obsidian-style" graph visualizations for the
rule_navigation brand knowledge bases (kb/{brand}/).

For each brand this script:
  1. Loads graph/graph.json (typed nodes + edges) as the topology backbone.
  2. Hydrates every node with its FULL source record (not just the compact graph
     label) by reading rules/, tokens/, assets/, governance/, subtypes/.
  3. Materializes `rule_group` nodes from groups/rule_groups.json — these exist as
     edge targets (`from_group`) in graph.json but were never emitted as nodes,
     which would otherwise leave 21-28 dangling references per brand.
  4. Enriches asset_group nodes with their full record and section_type nodes with
     their prose description from schema/section_vocab.md.
  5. Bundles the brand's schema/*.md docs (lightly converted to HTML) for an
     in-app "Schema & Legend" help modal, so the artifact is self-documenting.
  6. Renders a single self-contained HTML file (vendored JS inlined — no network
     access needed to view it) per brand, plus an index.html landing page.

Usage:
    python3 build_kb_graph.py [--brand lisraya ibsrela] [--kb-root ../kb] [--out out]
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_KB_ROOT = SCRIPT_DIR.parent / "kb"
DEFAULT_OUT_DIR = SCRIPT_DIR / "out"
TEMPLATE_PATH = SCRIPT_DIR / "template.html"
VENDOR_DIR = SCRIPT_DIR / "vendor"

# Kept in sync with kb/{brand}/schema/conventions.md id prefixes.
# (governance was retired as an entity — it is now a facet on brand rules)
KIND_LABELS = {
    "rule": "Brand rule",
    "token": "Brand token",
    "asset": "Design asset",
    "subtype": "Content sub-type",
    "template": "Design template",
    "template_group": "Template group",
    "section_type": "Section type",
    "asset_group": "Asset group",
    "rule_group": "Rule group (provenance)",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_dir_records(dir_path: Path) -> dict[str, dict]:
    """Load every *.json file in a KB entity directory (skipping _index.json),
    keyed by its `id` field."""
    records: dict[str, dict] = {}
    if not dir_path.exists():
        return records
    for fp in sorted(dir_path.glob("*.json")):
        if fp.name == "_index.json":
            continue
        rec = load_json(fp)
        records[rec["id"]] = rec
    return records


def parse_section_vocab(md_text: str) -> dict[str, str]:
    """Parse schema/section_vocab.md lines like `hero — lead visual ...` into
    {label: description}."""
    out: dict[str, str] = {}
    for line in md_text.splitlines():
        m = re.match(r"^([a-z_]+)\s+—\s+(.*)$", line.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


def markdown_to_html(md_text: str) -> str:
    """Minimal, purpose-built markdown->HTML converter for the short schema docs
    (headers, bold, inline code, bullet lists, tables, paragraphs). Not a general
    markdown engine — just enough fidelity to render these specific files well."""
    lines = md_text.splitlines()
    out: list[str] = []
    in_list = False
    in_table = False
    table_rows: list[list[str]] = []

    def inline(text: str) -> str:
        text = html.escape(text, quote=False)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        return text

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def flush_table():
        nonlocal in_table, table_rows
        if in_table:
            if table_rows:
                out.append("<table>")
                out.append("<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in table_rows[0]) + "</tr></thead>")
                out.append("<tbody>")
                body_rows = table_rows[2:] if len(table_rows) > 1 and re.match(r"^:?-+:?$", table_rows[1][0]) else table_rows[1:]
                for row in body_rows:
                    out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>")
                out.append("</tbody></table>")
            table_rows = []
            in_table = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_list()
            flush_table()
            continue
        if line.startswith("# "):
            flush_list(); flush_table()
            out.append(f"<h2>{inline(line[2:])}</h2>")
        elif line.startswith("## "):
            flush_list(); flush_table()
            out.append(f"<h3>{inline(line[3:])}</h3>")
        elif line.strip().startswith("|"):
            flush_list()
            in_table = True
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            table_rows.append(cells)
        elif line.strip().startswith("- "):
            flush_table()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line.strip()[2:])}</li>")
        else:
            flush_list(); flush_table()
            out.append(f"<p>{inline(line.strip())}</p>")
    flush_list()
    flush_table()
    return "\n".join(out)


def build_brand_dataset(brand: str, kb_root: Path) -> dict:
    brand_dir = kb_root / brand
    graph = load_json(brand_dir / "graph" / "graph.json")

    rules = load_dir_records(brand_dir / "rules")
    tokens = load_dir_records(brand_dir / "tokens")
    assets = load_dir_records(brand_dir / "assets")
    subtypes = load_dir_records(brand_dir / "subtypes")
    templates = load_dir_records(brand_dir / "templates" / "_meta")

    rule_groups = {r["id"]: r for r in load_json(brand_dir / "groups" / "rule_groups.json")}
    asset_groups = {r["id"]: r for r in load_json(brand_dir / "groups" / "asset_groups.json")}
    tg_path = brand_dir / "groups" / "template_groups.json"
    template_groups = {r["id"]: r for r in load_json(tg_path)} if tg_path.exists() else {}

    section_vocab_md = (brand_dir / "schema" / "section_vocab.md").read_text(encoding="utf-8")
    section_desc = parse_section_vocab(section_vocab_md)

    detail_lookup = {
        "rule": rules,
        "token": tokens,
        "asset": assets,
        "subtype": subtypes,
        "template": templates,
        "template_group": template_groups,
        "asset_group": asset_groups,
    }

    nodes_by_id: dict[str, dict] = {}
    missing_detail: list[str] = []

    for n in graph["nodes"]:
        node = dict(n)
        kind = node["kind"]
        if kind == "section_type":
            label = node["label"]
            node["detail"] = {"id": node["id"], "label": label, "description": section_desc.get(label, "")}
        else:
            table = detail_lookup.get(kind, {})
            rec = table.get(node["id"])
            if rec is None:
                missing_detail.append(node["id"])
                node["detail"] = {}
            else:
                node["detail"] = rec
        nodes_by_id[node["id"]] = node

    # Materialize rule_group nodes: referenced by `from_group` edges but absent
    # from graph.json's node list entirely (would otherwise be dangling edges).
    added_rule_groups = 0
    for gid, rec in rule_groups.items():
        if gid not in nodes_by_id:
            doc_ref = rec.get("doc_ref", gid)
            nodes_by_id[gid] = {
                "id": gid,
                "kind": "rule_group",
                "label": doc_ref,
                "detail": rec,
            }
            added_rule_groups += 1

    links = []
    dangling = []
    for e in graph["edges"]:
        if e["src"] not in nodes_by_id or e["dst"] not in nodes_by_id:
            dangling.append(e)
            continue
        links.append({
            "source": e["src"],
            "target": e["dst"],
            "type": e["type"],
            "note": e.get("note"),
            "order": e.get("order"),
        })

    degree: dict[str, int] = {nid: 0 for nid in nodes_by_id}
    for l in links:
        degree[l["source"]] = degree.get(l["source"], 0) + 1
        degree[l["target"]] = degree.get(l["target"], 0) + 1
    for nid, node in nodes_by_id.items():
        node["degree"] = degree.get(nid, 0)

    nodes = list(nodes_by_id.values())

    kind_counts: dict[str, int] = {}
    for node in nodes:
        kind_counts[node["kind"]] = kind_counts.get(node["kind"], 0) + 1
    edge_type_counts: dict[str, int] = {}
    for l in links:
        edge_type_counts[l["type"]] = edge_type_counts.get(l["type"], 0) + 1

    overview_md = (brand_dir / "schema" / "overview.md").read_text(encoding="utf-8")

    schema_docs = []
    schema_dir = brand_dir / "schema"
    preferred_order = [
        "overview.md", "conventions.md", "brand_rule.md", "brand_token.md",
        "design_asset.md", "content_sub_type.md", "design_template.md",
        "support_entities.md", "section_vocab.md", "predicate_registry.md",
    ]
    seen = set()
    ordered_files = [schema_dir / n for n in preferred_order if (schema_dir / n).exists()]
    ordered_files += sorted(p for p in schema_dir.glob("*.md") if p.name not in preferred_order)
    for fp in ordered_files:
        if fp.name in seen:
            continue
        seen.add(fp.name)
        schema_docs.append({
            "file": fp.name,
            "html": markdown_to_html(fp.read_text(encoding="utf-8")),
        })

    meta = {
        "brand": brand,
        "node_count": len(nodes),
        "link_count": len(links),
        "kind_counts": kind_counts,
        "edge_type_counts": edge_type_counts,
        "added_rule_group_nodes": added_rule_groups,
        "dangling_edges_dropped": len(dangling),
        "missing_detail_ids": missing_detail,
        "overview": overview_md,
    }

    if dangling:
        print(f"  WARNING [{brand}]: {len(dangling)} dangling edges (unresolved src/dst): {dangling[:5]}")
    if missing_detail:
        print(f"  WARNING [{brand}]: {len(missing_detail)} nodes missing detail record: {missing_detail[:5]}")

    return {
        "nodes": nodes,
        "links": links,
        "meta": meta,
        "schema_docs": schema_docs,
    }


def inject(template: str, values: dict[str, str]) -> str:
    out = template
    for key, val in values.items():
        token = "/*{{" + key + "}}*/"
        if token not in out:
            token = "{{" + key + "}}"
        if token not in out:
            raise KeyError(f"template placeholder not found for key: {key}")
        out = out.replace(token, val)
    return out


def json_for_script(data: Any) -> str:
    """Serialize to JSON safe for embedding inside a <script> tag."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


BRAND_META = {
    # Accent colors echo each brand's own primary palette (see kb/{brand}/tokens):
    # LISRAYA Brand Blue #00529b, IBSRELA Purple #92278F (brightened for dark-UI contrast).
    "lisraya": {"display": "LISRAYA", "accent": "#6a97ff"},
    "ibsrela": {"display": "IBSRELA", "accent": "#c15fd6"},
}


def render_brand_html(brand: str, dataset: dict, other_brands: list[str], template: str,
                       force_graph_js: str, d3_js: str) -> str:
    display = BRAND_META.get(brand, {}).get("display", brand.upper())
    accent = BRAND_META.get(brand, {}).get("accent", "#8ab4f8")

    other_links = "".join(
        f'<a class="brand-pill" href="{ob}.html">{BRAND_META.get(ob, {}).get("display", ob.upper())}</a>'
        for ob in other_brands
    )

    values = {
        "BRAND_ID": brand,
        "BRAND_DISPLAY": display,
        "BRAND_ACCENT": accent,
        "BRAND_ACCENT_JSON": json_for_script(accent),
        "OTHER_BRAND_LINKS": other_links,
        "GRAPH_DATA_JSON": json_for_script({"nodes": dataset["nodes"], "links": dataset["links"]}),
        "META_JSON": json_for_script(dataset["meta"]),
        "SCHEMA_DOCS_JSON": json_for_script(dataset["schema_docs"]),
        "KIND_LABELS_JSON": json_for_script(KIND_LABELS),
        "FORCE_GRAPH_JS": force_graph_js,
        "D3_JS": d3_js,
    }
    return inject(template, values)


def render_index_html(brands: list[str], datasets: dict[str, dict]) -> str:
    cards = []
    for b in brands:
        m = datasets[b]["meta"]
        kc = m["kind_counts"]
        display = BRAND_META.get(b, {}).get("display", b.upper())
        accent = BRAND_META.get(b, {}).get("accent", "#8ab4f8")
        rows = "".join(
            f"<li><span class='k'>{KIND_LABELS.get(k, k)}</span><span class='v'>{v}</span></li>"
            for k, v in sorted(kc.items(), key=lambda kv: -kv[1])
        )
        cards.append(f"""
        <a class="card" href="{b}.html" style="--accent: {accent}">
          <h2>{display}</h2>
          <p class="sub">{m['node_count']} nodes &middot; {m['link_count']} relations</p>
          <ul class="stat-list">{rows}</ul>
          <span class="cta">Open interactive graph &rarr;</span>
        </a>""")

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Brand Rule Knowledge Graphs</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ color-scheme: dark; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; min-height: 100vh; display: flex; flex-direction: column; align-items: center;
    justify-content: center; gap: 32px; padding: 48px 24px;
    background: radial-gradient(circle at 50% 0%, #1b1d24 0%, #101114 60%, #0a0a0c 100%);
    color: #dcdde3; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  }}
  h1 {{ font-size: 28px; font-weight: 600; margin: 0; letter-spacing: -0.01em; }}
  p.lede {{ color: #9799a6; max-width: 640px; text-align: center; line-height: 1.5; margin: 0; }}
  .cards {{ display: flex; gap: 24px; flex-wrap: wrap; justify-content: center; }}
  .card {{
    --accent: #8ab4f8;
    width: 300px; border-radius: 14px; padding: 24px; text-decoration: none; color: inherit;
    background: linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0.015));
    border: 1px solid rgba(255,255,255,0.08); transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
  }}
  .card:hover {{ transform: translateY(-3px); border-color: var(--accent); box-shadow: 0 10px 30px -10px var(--accent); }}
  .card h2 {{ margin: 0 0 4px; color: var(--accent); font-size: 22px; letter-spacing: 0.02em; }}
  .card .sub {{ margin: 0 0 16px; color: #8b8d98; font-size: 13px; }}
  .stat-list {{ list-style: none; margin: 0 0 20px; padding: 0; display: flex; flex-direction: column; gap: 6px; }}
  .stat-list li {{ display: flex; justify-content: space-between; font-size: 13px; color: #c2c3cc; border-bottom: 1px dashed rgba(255,255,255,0.06); padding-bottom: 4px; }}
  .stat-list .v {{ color: #f0f0f3; font-variant-numeric: tabular-nums; }}
  .cta {{ font-size: 13px; color: var(--accent); font-weight: 500; }}
  footer {{ color: #55575f; font-size: 12px; }}
</style>
</head>
<body>
  <h1>Brand Rule Knowledge Graphs</h1>
  <p class="lede">Interactive, Obsidian-style force-directed graphs of each brand's atomized rule
  knowledge base &mdash; rules, tokens, assets, governance, sub-types, sections and their
  full typed relationships. Hover to trace connections, click any node for full detail.</p>
  <div class="cards">{''.join(cards)}</div>
  <footer>Generated by rule_navigation/viz/build_kb_graph.py</footer>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brand", nargs="+", default=["lisraya", "ibsrela"])
    parser.add_argument("--kb-root", type=Path, default=DEFAULT_KB_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    force_graph_js = (VENDOR_DIR / "force-graph.min.js").read_text(encoding="utf-8")
    d3_js = (VENDOR_DIR / "d3.v7.min.js").read_text(encoding="utf-8")

    datasets = {}
    for brand in args.brand:
        print(f"Building dataset for brand={brand} ...")
        datasets[brand] = build_brand_dataset(brand, args.kb_root)
        m = datasets[brand]["meta"]
        print(f"  nodes={m['node_count']} links={m['link_count']} kinds={m['kind_counts']}")

    for brand in args.brand:
        others = [b for b in args.brand if b != brand]
        html_out = render_brand_html(brand, datasets[brand], others, template, force_graph_js, d3_js)
        out_path = args.out / f"{brand}.html"
        out_path.write_text(html_out, encoding="utf-8")
        print(f"Wrote {out_path} ({len(html_out)/1024:.0f} KB)")

    index_html = render_index_html(args.brand, datasets)
    index_path = args.out / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    print(f"Wrote {index_path}")


if __name__ == "__main__":
    main()
