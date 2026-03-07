"""Small CLI for the core deterministic pieces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .prd import parse_prd_text, render_markdown as render_prd_markdown
from .work_shaping import classify_work, render_markdown as render_shape_markdown


def infer_title(body: str) -> str:
    for line in body.splitlines():
        candidate = line.strip().lstrip("#").strip()
        if candidate:
            return candidate[:120]
    return "Untitled input"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deterministic primitives for issue-driven agent workflows.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prd = subparsers.add_parser("prd", help="Parse a markdown PRD")
    prd.add_argument("--markdown-file", required=True)
    prd.add_argument("--title")
    prd.add_argument("--format", choices=("json", "markdown"), default="json")

    shape = subparsers.add_parser("shape", help="Classify how much process a task needs")
    shape.add_argument("--markdown-file")
    shape.add_argument("--text")
    shape.add_argument("--title")
    shape.add_argument("--format", choices=("json", "markdown"), default="json")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "prd":
        path = Path(args.markdown_file).expanduser().resolve()
        body = path.read_text(encoding="utf-8")
        packet = parse_prd_text(
            title=args.title or infer_title(body),
            body=body,
            source={"type": "markdown_file", "path": str(path)},
        )
        if args.format == "markdown":
            print(render_prd_markdown(packet))
        else:
            print(json.dumps(packet, ensure_ascii=False, indent=2))
        return

    if args.command == "shape":
        if args.markdown_file:
            path = Path(args.markdown_file).expanduser().resolve()
            body = path.read_text(encoding="utf-8")
            title = args.title or infer_title(body)
            source = {"type": "markdown_file", "path": str(path)}
        elif args.text:
            body = args.text
            title = args.title or infer_title(body)
            source = {"type": "text"}
        else:
            raise SystemExit("Provide --markdown-file or --text for shape.")

        result = classify_work(title=title, body=body, source=source)
        if args.format == "markdown":
            print(render_shape_markdown(result))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
