import argparse
import json
from pathlib import Path
from .discovery import inspect_repository
from .engine import Engine, digest
from .server import serve
from .store import Store


def main():
    parser = argparse.ArgumentParser(description="LUCY local migration planning and evidence prototype")
    parser.add_argument("--data", default=".lucy", help="Local state directory")
    sub = parser.add_subparsers(dest="command", required=True)
    web = sub.add_parser("serve")
    web.add_argument("--port", type=int, default=8765)
    inspect = sub.add_parser("inspect", help="Read-only metadata discovery; does not execute repository code")
    inspect.add_argument("path")
    demo = sub.add_parser("demo", help="Optional synthetic fixture, not a real application migration")
    demo.add_argument("--approve-demo", action="store_true", help="Approve the fixed fixture contract and eight bounded steps")
    report = sub.add_parser("report")
    report.add_argument("project_id")
    args = parser.parse_args()
    if args.command == "serve":
        serve(args.data, args.port)
    elif args.command == "inspect":
        print(json.dumps(inspect_repository(args.path), indent=2))
    elif args.command == "demo":
        engine = Engine(Store(args.data))
        project = engine.create()
        if args.approve_demo:
            project = engine.approve(project["id"], digest(project["requirements"]))
            while project["status"] == "ready":
                project = engine.step(project["id"])
        print(json.dumps(engine.detail(project["id"]), indent=2))
    else:
        print(json.dumps(Engine(Store(args.data)).detail(args.project_id), indent=2))


if __name__ == "__main__":
    main()
