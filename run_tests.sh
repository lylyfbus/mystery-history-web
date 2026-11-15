#!/bin/sh
# Runs all tests for the site. Use this before each commit and each push.
cd "$(dirname "$0")" || exit 1
status=0
python3 -m unittest discover -s tests -p 'test_*.py' "$@" || status=1
if ls tests/*.test.js >/dev/null 2>&1; then
  node --test tests/ || status=1
fi
exit $status
