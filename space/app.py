"""JCAT ontology engine — Hugging Face Space.

A Gradio front-end over the open `jcat` engine. Paste terms, pick taxonomy or ontology,
choose the layer depth, and get standards-compliant SKOS/OWL Turtle plus a readable tree.
When the optional engine (open-ontologies-lite / Oxigraph) is installed, the Space also
validates the graph for real and runs live SPARQL over it. Mirrors the demo at
https://jcatlabs.com/#demo.
"""
import json

import gradio as gr

import jcat
from jcat import Graph
from jcat.core import build_tree, parse_terms

EXAMPLE = """credit risk
market risk
operational risk
liquidity risk
savings account
current account
business account
fixed deposit
retail customer
corporate customer
private customer
mortgage loan
personal loan
business loan"""

DEFAULT_SPARQL = "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 15"


def _tree_text(node, prefix=""):
    lines = []
    n = len(node.children)
    for i, c in enumerate(node.children):
        last = i == n - 1
        lines.append(prefix + ("└─ " if last else "├─ ") + c.label)
        lines.append(_tree_text(c, prefix + ("   " if last else "│  ")))
    return "\n".join(l for l in lines if l)


def _is_owl(mode):
    return mode.startswith("Ont")


def run(text, mode, depth):
    terms = parse_terms(text)
    if not terms:
        return "Add a few terms first.", "", "—"
    g = Graph(terms)
    owl = _is_owl(mode)
    ttl = g.ontology(int(depth)) if owl else g.taxonomy(int(depth))
    root = build_tree(terms, "ontology" if owl else "taxonomy", int(depth))
    if jcat.has_engine():
        rep = g.validate(mode="ontology" if owl else "taxonomy", depth=int(depth))
        ok = "valid" if rep.get("valid") else "INVALID"
        status = f"✓ {ok} · {rep.get('triples')} triples · validated by open-ontologies-lite (Oxigraph)"
    else:
        status = "light mode — engine not installed (synthesis only)"
    return ttl, (root.label + "\n" + _tree_text(root)), status


def run_sparql(text, mode, depth, sparql):
    if not jcat.has_engine():
        return "Engine not available in this Space."
    terms = parse_terms(text)
    if not terms:
        return "Add terms first."
    try:
        res = Graph(terms).query(
            sparql, mode="ontology" if _is_owl(mode) else "taxonomy", depth=int(depth)
        )
        rows = res.get("rows", res)
        return json.dumps(rows, indent=2)
    except Exception as e:  # noqa: BLE001
        return f"Error: {e}"


with gr.Blocks(title="JCAT ontology engine", theme=gr.themes.Soft(primary_hue="green")) as demo:
    gr.Markdown(
        "# 🐱 JCAT ontology engine\n"
        "Paste a flat list of terms. Get a standards-compliant **SKOS taxonomy** or "
        "**OWL ontology**, validated for real and queryable with SPARQL. This is the open "
        "[`jcat`](https://github.com/fabio-rovai/jcat) engine running on "
        "[open-ontologies-lite](https://pypi.org/project/open-ontologies-lite/) "
        "(Oxigraph), the same stack behind [jcatlabs.com](https://jcatlabs.com). Free forever."
    )
    with gr.Row():
        with gr.Column():
            inp = gr.Textbox(EXAMPLE, lines=14, label="Your terms")
            mode = gr.Radio(
                ["Taxonomy (SKOS)", "Ontology (OWL)"],
                value="Taxonomy (SKOS)", label="Output",
            )
            depth = gr.Slider(1, 3, value=2, step=1, label="Layer depth")
            btn = gr.Button("Give it a try", variant="primary")
        with gr.Column():
            status = gr.Markdown("—")
            tree = gr.Textbox(label="Structure", lines=8)
            ttl = gr.Code(label="Turtle")
    with gr.Accordion("Run SPARQL over the graph (powered by open-ontologies-lite)", open=False):
        sparql = gr.Textbox(DEFAULT_SPARQL, lines=3, label="SPARQL")
        sbtn = gr.Button("Run query")
        sout = gr.Code(label="Results")
        sbtn.click(run_sparql, [inp, mode, depth, sparql], sout)

    btn.click(run, [inp, mode, depth], [ttl, tree, status])
    demo.load(run, [inp, mode, depth], [ttl, tree, status])

if __name__ == "__main__":
    demo.launch()
