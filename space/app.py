"""JCAT ontology engine — Hugging Face Space.

A thin Gradio front-end over the open `jcat` engine. Paste terms, pick taxonomy or
ontology, choose the layer depth, and get standards-compliant SKOS/OWL Turtle plus a
readable tree. Mirrors the in-browser demo at https://jcatlabs.com/#demo.
"""
import gradio as gr

from jcat import Graph
from jcat.core import build_tree, parse_terms

EXAMPLE = """credit risk
market risk
operational risk
liquidity risk
savings account
current account
business account
mortgage loan
personal loan
business loan
retail customer
corporate customer"""


def _tree_text(node, prefix=""):
    lines = []
    n = len(node.children)
    for i, c in enumerate(node.children):
        last = i == n - 1
        lines.append(prefix + ("└─ " if last else "├─ ") + c.label)
        lines.append(_tree_text(c, prefix + ("   " if last else "│  ")))
    return "\n".join(l for l in lines if l)


def run(text, mode, depth):
    terms = parse_terms(text)
    if not terms:
        return "Add a few terms first.", ""
    g = Graph(terms)
    ttl = g.taxonomy(int(depth)) if mode == "Taxonomy (SKOS)" else g.ontology(int(depth))
    root = build_tree(terms, "taxonomy" if mode.startswith("Tax") else "ontology", int(depth))
    return ttl, (root.label + "\n" + _tree_text(root))


with gr.Blocks(title="JCAT ontology engine", theme=gr.themes.Soft(primary_hue="green")) as demo:
    gr.Markdown(
        "# 🐱 JCAT ontology engine\n"
        "Paste a flat list of terms. Get a standards-compliant **SKOS taxonomy** or "
        "**OWL ontology**. This is the open [`jcat`](https://github.com/fabio-rovai/jcat) "
        "engine, the same one running at [jcatlabs.com](https://jcatlabs.com). Free forever."
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
            tree = gr.Textbox(label="Structure", lines=10)
            ttl = gr.Code(label="Turtle")
    btn.click(run, [inp, mode, depth], [ttl, tree])
    demo.load(run, [inp, mode, depth], [ttl, tree])

if __name__ == "__main__":
    demo.launch()
