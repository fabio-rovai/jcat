"""JCAT core: turn flat term lists into standards-compliant taxonomies and ontologies.

The synthesis logic here is identical to the in-browser demo on https://jcatlabs.com.
Everything is deterministic and dependency-free: parse terms, group by head noun,
build a hierarchy to the requested depth, then emit SKOS (taxonomy) or OWL (ontology)
Turtle.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


def _words(s: str) -> List[str]:
    return [w for w in s.split() if w]


def _snake(s: str) -> str:
    return re.sub(r"^_|_$", "", re.sub(r"[^a-z0-9]+", "_", s.lower()))


def _camel(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", "".join(_cap(w) for w in _words(s)))


def parse_terms(text: str, limit: int = 5000) -> List[str]:
    """Split raw text (newlines, commas, semicolons) into a deduped term list."""
    seen, out = set(), []
    for raw in re.split(r"[\n,;]+", text):
        t = raw.strip().lower()
        if t and t not in seen:
            seen.add(t)
            out.append(t)
        if len(out) >= limit:
            break
    return out


@dataclass
class Node:
    label: str
    kind: str  # root | cat | leaf
    children: List["Node"] = field(default_factory=list)
    parent: Optional["Node"] = None
    cid: str = ""


def _set_parents(n: Node) -> None:
    for c in n.children:
        c.parent = n
        _set_parents(c)


def build_tree(terms: List[str], mode: str = "taxonomy", depth: int = 2) -> Node:
    """Group terms into a hierarchy. depth 1 = flat, 2 = head-noun groups,
    3 = head-noun then shared-modifier subgroups."""
    root = Node("Scheme" if mode == "taxonomy" else "Ontology", "root")
    if depth <= 1:
        root.children = [Node(_cap(t), "leaf") for t in terms]
        _set_parents(root)
        return root

    groups: dict[str, List[str]] = {}
    for t in terms:
        groups.setdefault(_words(t)[-1], []).append(t)

    for h in sorted(groups):
        members = groups[h]
        if len(members) < 2:
            root.children.append(Node(_cap(members[0]), "leaf"))
            continue
        g = Node(_cap(h), "cat")
        if depth >= 3:
            sub: dict[str, List[str]] = {}
            for t in members:
                sub.setdefault(_words(t)[0], []).append(t)
            done = set()
            for f in sorted(sub):
                if len(sub[f]) >= 2:
                    g.children.append(
                        Node(f"{_cap(f)} {_cap(h)}", "cat",
                             [Node(_cap(t), "leaf") for t in sub[f]])
                    )
                    done.update(sub[f])
            g.children += [Node(_cap(t), "leaf") for t in members if t not in done]
        else:
            g.children = [Node(_cap(t), "leaf") for t in members]
        root.children.append(g)

    _set_parents(root)
    return root


class _Uniq:
    def __init__(self):
        self.seen: dict[str, int] = {}

    def __call__(self, s: str) -> str:
        k = s or "node"
        if k in self.seen:
            self.seen[k] += 1
            return f"{k}_{self.seen[k]}"
        self.seen[k] = 0
        return k


def to_skos(root: Node) -> str:
    """Emit a SKOS ConceptScheme (Turtle)."""
    u = _Uniq()
    alln: List[Node] = []

    def walk(n: Node):
        for c in n.children:
            c.cid = "ex:" + u(_snake(c.label))
            alln.append(c)
            walk(c)

    walk(root)
    tops = root.children
    o = (
        "@prefix skos: <http://www.w3.org/2004/02/skos/core#> .\n"
        "@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
        "@prefix dct:  <http://purl.org/dc/terms/> .\n"
        "@prefix ex:   <https://jcatlabs.com/scheme/> .\n\n"
        "ex:scheme a skos:ConceptScheme ;\n"
        '    dct:title "Generated taxonomy"@en ;\n'
        '    dct:creator "JCAT Labs" ;\n'
        f"    skos:hasTopConcept {' , '.join(t.cid for t in tops)} .\n\n"
    )
    for n in alln:
        o += f"{n.cid} a skos:Concept ;\n    skos:prefLabel \"{n.label}\"@en ;\n    skos:inScheme ex:scheme"
        if n in tops:
            o += " ;\n    skos:topConceptOf ex:scheme"
        else:
            o += f" ;\n    skos:broader {n.parent.cid}"
        if n.children:
            o += f" ;\n    skos:narrower {' , '.join(c.cid for c in n.children)}"
        o += " .\n\n"
    return o


def to_owl(root: Node) -> str:
    """Emit an OWL ontology (Turtle) with subClassOf, an object property and a
    disjointness axiom over the top classes."""
    u = _Uniq()
    alln: List[Node] = []

    def walk(n: Node):
        for c in n.children:
            c.cid = ":" + u(_camel(c.label))
            alln.append(c)
            walk(c)

    walk(root)
    tops = root.children
    o = (
        "@prefix owl:  <http://www.w3.org/2002/07/owl#> .\n"
        "@prefix rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n"
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
        "@prefix xsd:  <http://www.w3.org/2001/XMLSchema#> .\n"
        "@prefix :     <https://jcatlabs.com/onto#> .\n\n"
        "<https://jcatlabs.com/onto> a owl:Ontology ;\n"
        '    rdfs:label "Generated ontology"@en ;\n'
        '    rdfs:comment "Synthesised by the JCAT open engine."@en .\n\n'
    )
    for n in alln:
        o += f"{n.cid} a owl:Class ;\n    rdfs:label \"{n.label}\"@en"
        if n not in tops:
            o += f" ;\n    rdfs:subClassOf {n.parent.cid}"
        o += " ;\n    rdfs:isDefinedBy <https://jcatlabs.com/onto> .\n\n"
    o += (
        ":relatedTo a owl:ObjectProperty ;\n"
        '    rdfs:label "related to"@en ;\n'
        "    rdfs:domain owl:Thing ;\n    rdfs:range owl:Thing .\n\n"
    )
    if len(tops) > 1:
        o += "[] a owl:AllDisjointClasses ;\n    owl:members ( " + " ".join(t.cid for t in tops) + " ) .\n"
    return o
