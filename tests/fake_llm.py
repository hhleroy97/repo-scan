#!/usr/bin/env python3
"""Fake LLM CLI for offline tests.

Prints $RADAR_FAKE_RESPONSE. If RADAR_FAKE_RESPONSES_DIR is set instead, pops
the lowest-numbered file from that directory (one response per call), enabling
multi-turn pipeline tests. Exits 1 if neither is configured.
"""

import os
import sys
from pathlib import Path


def main():
    resp = os.environ.get("RADAR_FAKE_RESPONSE")
    if resp is not None:
        print(resp)
        return 0

    queue_dir = os.environ.get("RADAR_FAKE_RESPONSES_DIR")
    if queue_dir:
        files = sorted(Path(queue_dir).glob("*.txt"))
        if not files:
            print("fake llm: response queue empty", file=sys.stderr)
            return 1
        print(files[0].read_text())
        files[0].unlink()
        return 0

    print("fake llm: no response configured", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
