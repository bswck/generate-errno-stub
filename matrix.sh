#!/usr/bin/env bash
set -HCETeuxo pipefail

: && \
    curl -fsSL 'https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json' \
    | jq '.[].version' \
    | sed -E -e 's/"(.*)"/- \1/' -e '/3\.[0-8]\./d' -e '/(-rc|beta|alpha)/d'

