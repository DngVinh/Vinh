"""Capture auditable real-browser screenshots and reflow evidence across all P0 routes.

Uses real Google Chrome and Microsoft Edge on Windows with isolated user-data-dir.
Generates screenshots for:
- Mobile: 360x800
- Tablet: 768x1024
- Desktop: 1280x900
- Zoom 200%: 1280x900 with force-device-scale-factor=2
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

BASE_URL = "http://localhost:3000"
OUTPUT_DIR = Path("release/evidence/screenshots")

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

ROUTES = [
    ("dashboard", "/"),
    ("chat", "/chat"),
    ("schedule", "/schedule"),
    ("tickets", "/tickets"),
    ("rooms", "/rooms"),
    ("staff", "/staff"),
    ("knowledge", "/knowledge"),
    ("privacy", "/privacy"),
    ("admin", "/admin"),
]

VIEWPORTS = [
    ("mobile_360px", 360, 800, 1),
    ("tablet_768px", 768, 1024, 1),
    ("desktop_1280px", 1280, 900, 1),
    ("zoom_200pct", 1280, 900, 2),
]


def capture_screenshot(browser_path: str, url: str, out_file: Path, width: int, height: int, scale: int = 1) -> bool:
    with tempfile.TemporaryDirectory(prefix="browser_evidence_") as temp_dir:
        args = [
            browser_path,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--user-data-dir={temp_dir}",
            f"--window-size={width},{height}",
            f"--screenshot={out_file.resolve()}",
            url,
        ]
        if scale > 1:
            args.insert(5, f"--force-device-scale-factor={scale}")

        try:
            res = subprocess.run(args, capture_output=True, timeout=20)
            return out_file.exists() and out_file.stat().st_size > 0
        except Exception as e:
            print(f"Error capturing {out_file.name}: {e}", file=sys.stderr)
            return False


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = 0
    passed = 0

    print("=== STARTING REAL BROWSER EVIDENCE CAPTURE (CHROME + EDGE) ===")

    # 1. Capture Chrome across all viewports and routes
    for route_name, route_path in ROUTES:
        url = f"{BASE_URL}{route_path}"
        for vp_name, w, h, s in VIEWPORTS:
            total += 1
            filename = f"chrome_{route_name}_{vp_name}.png"
            target_path = OUTPUT_DIR / filename
            success = capture_screenshot(CHROME_PATH, url, target_path, w, h, s)
            if success:
                passed += 1
                size_kb = target_path.stat().st_size / 1024
                print(f"[PASS] {filename} ({w}x{h}, scale={s}) -> {size_kb:.1f} KB")
            else:
                print(f"[FAIL] {filename}")

    # 2. Capture Edge for cross-browser verification on desktop
    for route_name, route_path in ROUTES:
        total += 1
        url = f"{BASE_URL}{route_path}"
        filename = f"edge_{route_name}_desktop_1280px.png"
        target_path = OUTPUT_DIR / filename
        success = capture_screenshot(EDGE_PATH, url, target_path, 1280, 900, 1)
        if success:
            passed += 1
            size_kb = target_path.stat().st_size / 1024
            print(f"[PASS] {filename} (Edge 1280x900) -> {size_kb:.1f} KB")
        else:
            print(f"[FAIL] {filename}")

    print(f"\nCompleted: {passed}/{total} screenshots captured successfully.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
