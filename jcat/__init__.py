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

# Optional engine: open-ontologies-lite (Oxigraph-backed RDF/OWL).
# Install with `pip install jcat[engine]` to unlock real validation, SPARQL and serving.
try:
    from open_ontologies_lite import OntologyEngine
    _HAS_ENGINE = True
except Exception:  # pragma: no cover - engine is optional
    OntologyEngine = None
    _HAS_ENGINE = False

__version__ = "0.1.0"
__all__ = ["Graph", "parse_terms", "build_tree", "to_skos", "to_owl", "has_engine"]


def has_engine() -> bool:
    """True if the open-ontologies-lite engine is installed."""
    return _HAS_ENGINE


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
    def validate(self, mode: str = "taxonomy", depth: int = 2) -> dict:
        """Validate the graph. With the engine installed (`pip install jcat[engine]`),
        this parses the synthesised RDF through open-ontologies-lite (Oxigraph) and
        reports real triple counts, validation errors and lint findings. Without it,
        it falls back to a light structural check."""
        empties = [t for t in self.terms if not t.strip()]
        report = {
            "terms": len(self.terms),
            "empty": len(empties),
            "ok": len(empties) == 0 and len(self.terms) > 0,
        }
        if _HAS_ENGINE:
            ttl = self.taxonomy(depth) if mode == "taxonomy" else self.ontology(depth)
            vr = OntologyEngine.validate(ttl, "turtle")
            eng = OntologyEngine()
            triples = eng.load(ttl, "turtle")
            report.update({
                "engine": "open-ontologies-lite",
                "triples": triples,
                "valid": getattr(vr, "error", None) is None,
                "error": getattr(vr, "error", None),
                "lint": eng.lint(),
            })
        else:
            report["engine"] = "light (install jcat[engine] for RDF validation)"
        return report

    # ---- query (engine only) ---------------------------------------------
    def query(self, sparql: str, mode: str = "taxonomy", depth: int = 2) -> dict:
        """Run a SPARQL query against the synthesised graph. Requires the engine."""
        eng, _ = self._engine(mode, depth)
        return eng.query(sparql)

    def _engine(self, mode: str = "taxonomy", depth: int = 2):
        if not _HAS_ENGINE:
            raise RuntimeError(
                "This needs the engine. Install it with: pip install jcat[engine]"
            )
        ttl = self.taxonomy(depth) if mode == "taxonomy" else self.ontology(depth)
        eng = OntologyEngine()
        eng.load(ttl, "turtle")
        return eng, ttl

    # ---- synthesise -------------------------------------------------------
    def taxonomy(self, depth: int = 2) -> str:
        return to_skos(build_tree(self.terms, "taxonomy", depth))

    def ontology(self, depth: int = 2) -> str:
        return to_owl(build_tree(self.terms, "ontology", depth))

    # ---- serve ------------------------------------------------------------
    def serve(self, port: int = 8080, mode: str = "taxonomy", depth: int = 2):
        """Serve the synthesised graph over HTTP (Ctrl-C to stop).

        With the engine installed, this exposes a real SPARQL endpoint at
        ``/sparql?query=...`` (powered by open-ontologies-lite / Oxigraph) alongside the
        Turtle at ``/``. Without it, it serves the Turtle only."""
        import json
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from urllib.parse import parse_qs, urlparse

        ttl = self.taxonomy(depth) if mode == "taxonomy" else self.ontology(depth)
        body = ttl.encode("utf-8")
        eng = None
        if _HAS_ENGINE:
            eng = OntologyEngine()
            eng.load(ttl, "turtle")

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                if parsed.path.rstrip("/") == "/sparql" and eng is not None:
                    q = parse_qs(parsed.query).get("query", [""])[0]
                    try:
                        out = json.dumps(eng.query(q)).encode("utf-8")
                        ctype = "application/json"
                    except Exception as e:  # noqa: BLE001
                        out = json.dumps({"error": str(e)}).encode("utf-8")
                        ctype = "application/json"
                else:
                    out, ctype = body, "text/turtle; charset=utf-8"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.end_headers()
                self.wfile.write(out)

            def log_message(self, *a):
                pass

        extra = " + SPARQL at /sparql" if eng is not None else ""
        print(f"jcat serving {mode} ({len(self.terms)} terms) on http://localhost:{port}{extra}")
        HTTPServer(("", port), H).serve_forever()
