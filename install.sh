#!/bin/sh
# Installs thai-ocr next to this script:
#   1. downloads OpenThai2.0-OCR-Text from Hugging Face at a PINNED revision and verifies SHA-256
#   2. builds a Python virtualenv (./venv) with the pinned requirements
# Safe to re-run. Does not use sudo and does not touch anything outside this folder.
set -eu

HF_REPO="iapp/OpenThai2.0-OCR-Text"
# The model ships Python runtime code (runtime/*.py) that thai-ocr imports, so it is pinned to the
# revision that was read and checked. Change it only after reviewing the new runtime code.
HF_REV="39fa41bdd49f067ba41b1d9de79c06ab506d67d4"
FILES="NOTICE SHA256SUMS config.json det.onnx det.yml rec.onnx rec_dict.txt runtime/__init__.py runtime/line_engine.py runtime/thai_norm.py"

H="$(cd "$(dirname "$0")" && pwd)"
cd "$H"
say() { printf '==> %s\n' "$*"; }

say "Model: $HF_REPO @ ${HF_REV%"${HF_REV#????????}"}"
mkdir -p model/runtime
for f in $FILES; do
  if [ ! -f "model/$f" ]; then
    curl -fL --retry 3 -sS -o "model/$f.part" "https://huggingface.co/$HF_REPO/resolve/$HF_REV/$f"
    mv "model/$f.part" "model/$f"
  fi
done

say "Verifying checksums"
if command -v shasum >/dev/null 2>&1; then SHA="shasum -a 256 -c"; else SHA="sha256sum -c"; fi
# SHA256SUMS also lists files we do not download (README, pytorch training weights): check only ours.
( cd model && grep -E ' \./(NOTICE|config\.json|det\.onnx|det\.yml|rec\.onnx|rec_dict\.txt|runtime/.*)$' SHA256SUMS | $SHA - )

say "Python environment"
if [ ! -x venv/bin/python ]; then
  if command -v uv >/dev/null 2>&1; then
    uv venv --python 3.12 venv
  else
    PY=""
    for c in python3.12 python3.13 python3.11 python3; do
      if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
    done
    [ -n "$PY" ] || { echo "Need 'uv' (https://docs.astral.sh/uv/) or Python 3.11-3.13." >&2; exit 1; }
    "$PY" -m venv venv
  fi
fi
if command -v uv >/dev/null 2>&1; then
  uv pip install --python venv/bin/python -r requirements.txt
else
  venv/bin/python -m pip install --quiet -r requirements.txt
fi

chmod +x bin/thai-ocr
say "Done. Try:  $H/bin/thai-ocr --help"
say "Put it on your PATH (needs sudo for /usr/local/bin):"
printf '      sudo ln -sf "%s/bin/thai-ocr" /usr/local/bin/thai-ocr\n' "$H"
printf '    or without sudo:\n      mkdir -p ~/.local/bin && ln -sf "%s/bin/thai-ocr" ~/.local/bin/thai-ocr\n' "$H"
