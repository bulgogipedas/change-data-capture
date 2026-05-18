#!/usr/bin/env bash
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

failures=0
warnings=0

pass() {
  printf "PASS %s\n" "$1"
}

warn() {
  warnings=$((warnings + 1))
  printf "WARN %s\n" "$1"
}

fail() {
  failures=$((failures + 1))
  printf "FAIL %s\n" "$1"
}

run_required() {
  local label="$1"
  shift
  if "$@" >/tmp/cdc_health.out 2>/tmp/cdc_health.err; then
    pass "${label}"
    if [[ -s /tmp/cdc_health.out ]]; then
      sed 's/^/     /' /tmp/cdc_health.out
    fi
  else
    fail "${label}"
    sed 's/^/     /' /tmp/cdc_health.err
  fi
}

run_optional() {
  local label="$1"
  shift
  if "$@" >/tmp/cdc_health.out 2>/tmp/cdc_health.err; then
    pass "${label}"
    if [[ -s /tmp/cdc_health.out ]]; then
      sed 's/^/     /' /tmp/cdc_health.out
    fi
  else
    warn "${label}"
    sed 's/^/     /' /tmp/cdc_health.err
  fi
}

printf "Checking live CDC demo health\n"
printf "Repo: %s\n\n" "${REPO_ROOT}"

if ! command -v podman >/dev/null 2>&1; then
  fail "podman command is not available"
  printf "Hint: install/start Podman or use Docker manually with the README commands.\n"
  exit 1
fi

if ! podman info >/dev/null 2>&1; then
  fail "Podman is not running"
  printf "Hint: run 'podman machine start' and retry.\n"
  exit 1
fi

run_required "Compose containers" podman compose -f compose.yml ps
run_required "PostgreSQL readiness" podman exec cdc-postgres pg_isready -U cdc_user -d shopdb
run_required "Redpanda cluster health" podman exec cdc-redpanda rpk cluster health
run_required "Debezium REST endpoint" curl -fsS http://localhost:8083/connectors
run_required "ClickHouse ping" curl -fsS http://localhost:8123/ping
run_required "Redpanda topic list" podman exec cdc-redpanda rpk topic list

run_optional "Debezium connector status" curl -fsS http://localhost:8083/connectors/shop-postgres-source/status

run_optional "ClickHouse raw_cdc_events count" curl -sS "http://localhost:8123/?database=cdc_analytics" --data-binary "SELECT count() FROM raw_cdc_events"
run_optional "ClickHouse raw event counts by table" curl -sS "http://localhost:8123/?database=cdc_analytics" --data-binary "SELECT source_table, count() FROM raw_cdc_events GROUP BY source_table ORDER BY source_table"
run_optional "Executive mart query" curl -sS "http://localhost:8123/?database=cdc_analytics" --data-binary "SELECT * FROM mart_executive_overview FORMAT PrettyCompact"
run_optional "Data quality latest summary" curl -sS "http://localhost:8123/?database=cdc_analytics" --data-binary "SELECT status, count(), sum(failed_count) FROM data_quality_results GROUP BY status FORMAT PrettyCompact"

rm -f /tmp/cdc_health.out /tmp/cdc_health.err

printf "\nHealth summary: %s failure(s), %s warning(s)\n" "${failures}" "${warnings}"

if [[ ${failures} -gt 0 ]]; then
  printf "Result: FAIL\n"
  printf "Next steps: run 'podman compose -f compose.yml up -d', then './scripts/register_connector.sh' and './scripts/create_topics.sh'.\n"
  exit 1
fi

printf "Result: PASS\n"
exit 0
