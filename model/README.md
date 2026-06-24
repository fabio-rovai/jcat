---
license: mit
language:
- en
tags:
- ontology
- taxonomy
- knowledge-graph
- skos
- owl
- rdf
- semantic-web
- glam
library_name: jcat
---

# jcat-mini

**Knowledge-graph infrastructure as code.** The open, free-forever model in the JCAT
family. `jcat-mini` turns a flat list of terms into a standards-compliant **SKOS taxonomy**
or **OWL ontology**, deterministically, with no dependencies and nothing sent anywhere.

- 🌐 Site: [jcatlabs.com](https://jcatlabs.com)
- 🧪 Live demo (Space): [huggingface.co/spaces/fabsssss/jcat](https://huggingface.co/spaces/fabsssss/jcat)
- 💻 Code: [github.com/fabio-rovai/jcat](https://github.com/fabio-rovai/jcat)

## The model family

| Model | What it is | Where |
|-------|------------|-------|
| **jcat-mini** | Open engine. Flat term lists into SKOS/OWL. | Free forever, here + GitHub |
| **jcat-base** | Managed curation and hosting at scale. | [Curated Cloud](https://jcatlabs.com/#pricing) |
| **jcat-max** | Private VPC / on-prem, dedicated curation, SLAs. | [Enterprise](https://jcatlabs.com/#pricing) |

`jcat-mini` is the free tier: start simple here, then bring the mess (documentation,
guidelines, spreadsheets, raw data) to `jcat-base` / `jcat-max` when you want it sorted
and hosted for you.

## Intended use

Domain-agnostic knowledge structuring. Built for any sector that has to organise a
vocabulary, with GLAM (galleries, libraries, archives, museums) and defence / intelligence
as flagship ranges. It feeds search, analytics, RAG pipelines and agents from a single
governed graph.

## Usage

```bash
pip install git+https://github.com/fabio-rovai/jcat
```

```python
from jcat import Graph

g = Graph.load("terms.txt")        # term list, CSV column, or labels from a .ttl
print(g.taxonomy(depth=2))         # SKOS ConceptScheme (Turtle)
print(g.ontology(depth=2))         # OWL ontology (Turtle)
```

Command line:

```bash
jcat build terms.txt --as owl --depth 2 -o ontology.ttl
```

## What it emits

**Taxonomy** → SKOS `ConceptScheme` with `skos:broader` / `skos:narrower`,
`skos:topConceptOf`, `skos:prefLabel`, `skos:inScheme`.

**Ontology** → OWL with `owl:Class`, `rdfs:subClassOf`, `rdfs:label`, an
`owl:ObjectProperty`, and an `owl:AllDisjointClasses` axiom over the top classes.

Every artifact parses cleanly with `rdflib` across all depths (1–3).

## How it works

Deterministic, not neural. `jcat-mini` groups terms by head noun (e.g. *credit risk*,
*market risk* → **Risk**) and builds a hierarchy to the requested `depth` (1 = flat,
2 = head-noun groups, 3 = head-noun then shared-modifier subgroups), then serialises to
standards-native Turtle.

## Limitations

The open model infers structure lexically. Semantic alignment across vocabularies, SHACL
validation against your shapes, versioning/lineage and managed hosting are the paid
`jcat-base` / `jcat-max` models. No training data, no weights: output is a pure function of
input, which makes it auditable and reproducible.

## License

MIT. Built by [JCAT Labs](https://jcatlabs.com).
