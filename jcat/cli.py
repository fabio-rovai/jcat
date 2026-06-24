"""Command-line interface for JCAT.

    jcat build terms.txt --as owl --depth 2 -o onto.ttl
    jcat build terms.txt --as skos
    jcat serve terms.txt --as skos --port 8080
"""
from __future__ import annotations

import argparse
import sys

from . import Graph, __version__


def main(argv=None):
    p = argparse.ArgumentParser(prog="jcat", description="Knowledge-graph infrastructure as code.")
    p.add_argument("--version", action="version", version=f"jcat {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="synthesise a taxonomy or ontology from a term list")
    b.add_argument("file", help="path to a .txt/.csv term list or .ttl graph")
    b.add_argument("--as", dest="fmt", choices=["skos", "owl"], default="skos")
    b.add_argument("--depth", type=int, default=2, choices=[1, 2, 3])
    b.add_argument("-o", "--out", help="write Turtle to this file (default: stdout)")

    s = sub.add_parser("serve", help="serve the synthesised graph over HTTP")
    s.add_argument("file")
    s.add_argument("--as", dest="fmt", choices=["skos", "owl"], default="skos")
    s.add_argument("--depth", type=int, default=2, choices=[1, 2, 3])
    s.add_argument("--port", type=int, default=8080)

    args = p.parse_args(argv)
    g = Graph.load(args.file)

    if args.cmd == "build":
        ttl = g.taxonomy(args.depth) if args.fmt == "skos" else g.ontology(args.depth)
        if args.out:
            open(args.out, "w", encoding="utf-8").write(ttl)
            print(f"wrote {args.fmt.upper()} ({len(g.terms)} terms) -> {args.out}", file=sys.stderr)
        else:
            sys.stdout.write(ttl)
    elif args.cmd == "serve":
        mode = "taxonomy" if args.fmt == "skos" else "ontology"
        g.serve(port=args.port, mode=mode, depth=args.depth)


if __name__ == "__main__":
    main()
