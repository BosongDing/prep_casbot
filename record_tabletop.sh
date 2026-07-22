#!/usr/bin/env bash
set -euo pipefail

echo "DISABLED: tabletop recording caused a physical collision during the" >&2
echo "automatic return on 2026-07-22. Do not run another tabletop motion" >&2
echo "until the return path is redesigned, collision-audited with the real" >&2
echo "table geometry, and reviewed by the CASBOT engineer." >&2
exit 1
