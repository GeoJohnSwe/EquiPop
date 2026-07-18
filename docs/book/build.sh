#!/usr/bin/env bash
# build.sh - compile EquiPop: The Book (all chapters, sorted) to docx.
# Run from docs/book/. Figures first (cookbook scripts), then compile.
set -e
cd "$(dirname "$0")"
echo "[book] regenerating figures..."
for f in ../../examples/cookbook_0*.py; do
  (cd ../.. && PYTHONPATH=. python "examples/$(basename $f)")
done
echo "[book] compiling chapters: $(ls ch*.md | tr '\n' ' ')"
npm ls docx >/dev/null 2>&1 || npm install --silent docx
node build_book.js ch*.md "${1:-EquiPop_Book.docx}"
