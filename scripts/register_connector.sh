#!/usr/bin/env bash
set -euo pipefail

DEBEZIUM_URL="${DEBEZIUM_URL:-http://localhost:8083}"
CONNECTOR_FILE="${CONNECTOR_FILE:-debezium/connectors/postgres-source.json}"
CONNECTOR_NAME="${CONNECTOR_NAME:-shop-postgres-source}"
CURL_RETRY_ARGS=(--retry 10 --retry-delay 2 --retry-all-errors)

if curl "${CURL_RETRY_ARGS[@]}" -fsS "${DEBEZIUM_URL}/connectors/${CONNECTOR_NAME}" >/dev/null 2>&1; then
  TMP_CONFIG="$(mktemp)"
  python3 -c 'import json,sys; print(json.dumps(json.load(open(sys.argv[1]))["config"]))' "${CONNECTOR_FILE}" > "${TMP_CONFIG}"
  curl "${CURL_RETRY_ARGS[@]}" -sS -X PUT \
    -H "Content-Type: application/json" \
    --data-binary "@${TMP_CONFIG}" \
    "${DEBEZIUM_URL}/connectors/${CONNECTOR_NAME}/config"
  rm -f "${TMP_CONFIG}"
else
  curl "${CURL_RETRY_ARGS[@]}" -sS -X POST \
    -H "Content-Type: application/json" \
    --data-binary "@${CONNECTOR_FILE}" \
    "${DEBEZIUM_URL}/connectors"
fi

printf "\nConnector registered at %s\n" "${DEBEZIUM_URL}"
