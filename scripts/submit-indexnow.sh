#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Submit sitemap URLs to IndexNow.

Usage:
  scripts/submit-indexnow.sh [--key KEY] [--sitemap-url URL] [--host HOST]
                             [--key-location URL] [--endpoint URL] [--dry-run]

Env vars (optional):
  INDEXNOW_KEY
  INDEXNOW_SITEMAP_URL
  INDEXNOW_HOST
  INDEXNOW_KEY_LOCATION
  INDEXNOW_ENDPOINT
EOF
}

KEY="${INDEXNOW_KEY:-}"
SITEMAP_URL="${INDEXNOW_SITEMAP_URL:-https://pastmysteries.com/sitemap.xml}"
HOST="${INDEXNOW_HOST:-}"
KEY_LOCATION="${INDEXNOW_KEY_LOCATION:-}"
ENDPOINT="${INDEXNOW_ENDPOINT:-https://api.indexnow.org/indexnow}"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --key)
      KEY="${2:-}"
      shift 2
      ;;
    --sitemap-url)
      SITEMAP_URL="${2:-}"
      shift 2
      ;;
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --key-location)
      KEY_LOCATION="${2:-}"
      shift 2
      ;;
    --endpoint)
      ENDPOINT="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${KEY}" ]]; then
  echo "Missing key. Use --key or INDEXNOW_KEY." >&2
  exit 1
fi

if [[ -z "${HOST}" ]]; then
  HOST="$(printf '%s' "${SITEMAP_URL}" | sed -E 's#https?://([^/]+)/?.*#\1#')"
fi

if [[ -z "${KEY_LOCATION}" ]]; then
  KEY_LOCATION="https://${HOST}/${KEY}.txt"
fi

SITEMAP_XML="$(curl -fsSL "${SITEMAP_URL}")"
if command -v rg >/dev/null 2>&1; then
  URLS_RAW="$(
    printf '%s' "${SITEMAP_XML}" \
      | rg -o --no-filename '<loc>[^<]+</loc>' \
      | sed -E 's#<loc>(.*)</loc>#\1#' \
      | sed '/^$/d'
  )"
else
  URLS_RAW="$(
    printf '%s' "${SITEMAP_XML}" \
      | grep -Eo '<loc>[^<]+</loc>' \
      | sed -E 's#<loc>(.*)</loc>#\1#' \
      | sed '/^$/d'
  )"
fi

if [[ -z "${URLS_RAW}" ]]; then
  echo "No <loc> URLs found in sitemap: ${SITEMAP_URL}" >&2
  exit 1
fi

URL_COUNT="$(printf '%s\n' "${URLS_RAW}" | wc -l | tr -d ' ')"

URL_LIST_JSON="$(
  printf '%s\n' "${URLS_RAW}" \
    | sed 's#\\#\\\\#g; s#"#\\"#g; s#^#"#; s#$#"#' \
    | paste -sd, -
)"

PAYLOAD="$(cat <<EOF
{"host":"${HOST}","key":"${KEY}","keyLocation":"${KEY_LOCATION}","urlList":[${URL_LIST_JSON}]}
EOF
)"

if [[ "${DRY_RUN}" -eq 1 ]]; then
  echo "Dry run only. Payload:"
  echo "${PAYLOAD}"
  exit 0
fi

TMP_FILE="$(mktemp)"
HTTP_STATUS="$(
  curl -sS -o "${TMP_FILE}" -w '%{http_code}' \
    -X POST "${ENDPOINT}" \
    -H 'Content-Type: application/json; charset=utf-8' \
    --data "${PAYLOAD}"
)"

if [[ "${HTTP_STATUS}" == 2* ]]; then
  echo "IndexNow accepted (${HTTP_STATUS}). Submitted ${URL_COUNT} URLs from ${SITEMAP_URL}."
  if [[ -s "${TMP_FILE}" ]]; then
    echo "Response:"
    cat "${TMP_FILE}"
  fi
  rm -f "${TMP_FILE}"
  exit 0
fi

echo "IndexNow failed with HTTP ${HTTP_STATUS}." >&2
if [[ -s "${TMP_FILE}" ]]; then
  echo "Response:" >&2
  cat "${TMP_FILE}" >&2
fi
rm -f "${TMP_FILE}"
exit 1
