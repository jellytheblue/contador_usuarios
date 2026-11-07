#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip buildozer
buildozer -v android debug
printf '\nAPK generado en: %s\n' "$(find bin -maxdepth 1 -type f -name '*.apk' -print -quit)"
