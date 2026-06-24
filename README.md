<p align="center">
  <img src="https://raw.githubusercontent.com/fabio-rovai/jcatlabs/main/dog.png" alt="JCAT Labs" height="120" />
</p>

<h1 align="center">JCAT</h1>
<p align="center"><strong>Knowledge-graph infrastructure as code.</strong><br/>
Flat term lists in. Standards-compliant taxonomies and ontologies out.</p>

<p align="center">
  <a href="https://jcatlabs.com">jcatlabs.com</a> ·
  <a href="https://jcatlabs.com/#demo">Live demo</a> ·
  <a href="https://huggingface.co/spaces/fabsssss/jcat">Hugging Face Space</a> ·
  <a href="#license">MIT</a>
</p>

---

## What this is

If Terraform turned cloud resources into declarative code, **JCAT does the same for knowledge.**
You declare your vocabulary, and JCAT plans and renders it into a governed graph: a SKOS
taxonomy or an OWL ontology, valid against the W3C standards, ready to serve.

The core engine is **open source and free forever.** The hard parts at enterprise scale,
curation, alignment, hosting and governance, are the managed product at
[jcatlabs.com](https://jcatlabs.com). The brand site is the front door; the model and the
interactive demo live on [Hugging Face](https://huggingface.co/spaces/fabsssss/jcat); the
code lives here.

## Install

```bash
pip install git+https://github.com/fabio-rovai/jcat
# PyPI release (pip install jcat) coming with v0.2
```

The core (`jcat-mini`) is pure Python, **zero dependencies**, 3.9+. For real RDF validation,
SPARQL and serving, add the engine extra, which pulls in
[open-ontologies-lite](https://pypi.org/project/open-ontologies-lite/), an Oxigraph-backed
RDF/OWL engine:

```bash
pip install "jcat[engine] @ git+https://github.com/fabio-rovai/jcat"
```

No dependencies. Pure Python, 3.9+.

## Quickstart

```python
from jcat import Graph

g = Graph.load("terms.txt")        # a term list, a CSV column, or labels from a .ttl
g.validate()                       # {'terms': 12, 'empty': 0, 'ok': True}

print(g.taxonomy(depth=2))         # -> SKOS ConceptScheme (Turtle)
print(g.ontology(depth=2))         # -> OWL ontology (Turtle)

g.serve(port=8080)                 # serve the artifact over HTTP
```

Command line:

```bash
jcat build terms.txt --as owl  --depth 2 -o ontology.ttl
jcat build terms.txt --as skos --depth 1
jcat serve terms.txt --as skos --port 8080
```

## What it emits

**Taxonomy mode** produces a SKOS `ConceptScheme` with `skos:broader` / `skos:narrower`,
`skos:topConceptOf`, `skos:prefLabel` and `skos:inScheme`.

**Ontology mode** produces an OWL ontology with `owl:Class`, `rdfs:subClassOf`,
`rdfs:label`, an `owl:ObjectProperty`, and an `owl:AllDisjointClasses` axiom over the top
classes.

Every artifact this repo emits parses cleanly with `rdflib` across all depths (1, 2, 3).

```
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix ex:   <https://jcatlabs.com/scheme/> .

ex:risk a skos:Concept ;
    skos:prefLabel "Risk"@en ;
    skos:topConceptOf ex:scheme ;
    skos:narrower ex:credit_risk , ex:market_risk .
```

## The layer model

`depth` controls how much structure JCAT infers:

| depth | shape |
|-------|-------|
| 1 | flat: scheme/ontology → terms |
| 2 | grouped by head noun (e.g. *credit risk*, *market risk* → **Risk**) |
| 3 | head noun, then shared-modifier subgroups |

## Why "free forever"

The engine is the commodity. The value is the curation and the infrastructure around it.
We never paywall the engine, the same way you never pay to run `terraform plan`. You pay
when you want it managed: hosted graphs, alignment across vendors and acquisitions,
versioning and audit, SLAs. That is [Curated Cloud and Enterprise](https://jcatlabs.com/#pricing).

## The engine (optional)

`jcat-mini` synthesises graphs with zero dependencies. Install `jcat[engine]` to back the
heavy operations with [open-ontologies-lite](https://pypi.org/project/open-ontologies-lite/)
(Oxigraph):

```python
import jcat
jcat.has_engine()                     # True when the engine is installed

g.validate(mode="ontology")           # real validation: triple count, errors, lint
g.query("SELECT (COUNT(?c) AS ?n) WHERE { ?c a owl:Class }")   # SPARQL over the graph
g.serve()                             # serves Turtle at / and live SPARQL at /sparql
```

Without the engine these fall back gracefully and synthesis still works. This is the same
split as the product: the free model is light and self-contained; validation, SPARQL,
alignment and hosting at scale run on the open-ontologies engine.

## Roadmap

- [x] open-ontologies-lite engine integration (validation, SPARQL, serving)
- [x] Hugging Face model card ([jcat-mini](https://huggingface.co/fabsssss/jcat-mini))
- [ ] PyPI release
- [ ] SHACL shape validation surfaced through `validate()`
- [ ] Alignment between two schemes (candidate scoring + adjudication)
- [ ] `jcat plan` / `jcat apply` diff workflow against a target graph

## License

MIT. See [LICENSE](LICENSE). Built by [JCAT Labs](https://jcatlabs.com).
