#!/usr/bin/env bash
# Builds the website into _site/: the browser board plus the engine files it runs in the browser.
# Used by .github/workflows/pages.yml, and locally to test the site:
#   bash tools/build_site.sh && python3 -m http.server 8000 --directory _site
set -euo pipefail
cd "$(dirname "$0")/.."

rm -rf _site
mkdir -p _site/engine/tools

cp -R web/. _site/
cp web/main_page.html _site/index.html          # GitHub Pages opens index.html by default
cp engine.py _site/engine/
cp tools/book.py tools/book.txt _site/engine/tools/
find _site -name .DS_Store -delete

echo "built _site/"
