"""JCAT: knowledge-graph infrastructure as code.

Turn flat term lists into standards-compliant taxonomies (SKOS) and ontologies (OWL).

    from jcat import Graph

    g = Graph.load("catalog.txt")     # a list of terms, CSV column, or .ttl labels
    print(g.taxonomy(depth=2))        # SKOS Turtle
    print(g.ontology(depth=2))        # OWL Turtle
    g.serve(port=8080)                # expose the artifact over HTTP

The synthesis is deterministic and dependency-free, and is the exact engine that
runs in the browser demo at https://jcatlabs.com.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List

from .core import build_tree, parse_terms, to_owl, to_skos

__version__ = "0.1.0"
__all__ = ["Graph", "parse_terms", "build_tree", "to_skos", "to_owl"]


class Graph:
    """A working set of terms that can be synthesised into a taxonomy or ontology."""

    def __init__(self, terms: List[str]):
        self.terms = terms

    # ---- ingest -----------------------------------------------------------
    @classmethod
    def from_text(cls, text: str) -> "Graph":
        return cls(parse_terms(text))

    @classmethod
    def load(cls, path: str | Path) -> "Graph":
        """Load terms from a .txt/.csv list, or pull labels out of an existing
        .ttl/.rdf graph (skos:prefLabel / rdfs:label literals)."""
        p = Path(path)
        raw = p.read_text(encoding="utf-8")
        if p.suffix.lower() in {".ttl", ".rdf", ".n3", ".nt"}:
            labels = re.findall(r'"([^"]+)"(?:@\w+)?\s*[;.]', raw)
            return cls(parse_terms("\n".join(labels)))
        return cls(parse_terms(raw))

    def align(self, other: "str | Path | Graph") -> "Graph":
        """Merge another source of terms into this graph (deduplicated)."""
        extra = other.terms if isinstance(other, Graph) else Graph.load(other).terms
        merged = self.terms + [t for t in extra if t not in set(self.terms)]
        self.terms = merged
        return self

    # ---- validate ---------------------------------------------------------
    def validate(self) -> dict:
        """Lightweight structural validation. The managed product validates against
        your SHACL shapes; the open core reports basic health."""
        empties = [t for t in self.terms if not t.strip()]
        return {
            "terms": len(self.terms),
            "empty": len(empties),
            "ok": len(empties) == 0 and len(self.terms) > 0,
        }

    # ---- synthesise -------------------------------------------------------
    def taxonomy(self, depth: int = 2) -> str:
        return to_skos(build_tree(self.terms, "taxonomy", depth))

    def ontology(self, depth: int = 2) -> str:
        return to_owl(build_tree(self.terms, "ontology", depth))

    # ---- serve ------------------------------------------------------------
    def serve(self, port: int = 8080, mode: str = "taxonomy", depth: int = 2):
        """Serve the synthesised Turtle over HTTP (Ctrl-C to stop)."""
        from http.server import BaseHTTPRequestHandler, HTTPServer

        ttl = self.taxonomy(depth) if mode == "taxonomy" else self.ontology(depth)
        body = ttl.encode("utf-8")

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/turtle; charset=utf-8")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *a):
                pass

        print(f"jcat serving {mode} ({len(self.terms)} terms) on http://localhost:{port}")
        HTTPServer(("", port), H).serve_forever()
