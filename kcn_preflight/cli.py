"""Command-line entry point for a conservative initial assurance report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from .constitution import ConstitutionalPreflight
from .models import Stage


def main() -> int:
    parser = argparse.ArgumentParser(prog="kcn-preflight")
    parser.add_argument("artifact", type=Path, help="File to hash and evaluate")
    args = parser.parse_args()
    if not args.artifact.is_file():
        parser.error("artifact must be an existing regular file")
    content = args.artifact.read_bytes()
    engine = ConstitutionalPreflight()
    report = {
        "artifact": str(args.artifact),
        "stages": [
            engine.run_checkpoint(stage, content).to_dict()
            for stage in Stage
        ],
        "qualification": "NOT_MEASURED",
        "note": "No runtime adapters are registered; this report cannot authorize execution.",
    }
    print(json.dumps(report, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
