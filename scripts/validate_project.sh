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

run_check() {
  local label="$1"
  shift
  if "$@" >/tmp/cdc_validate.out 2>/tmp/cdc_validate.err; then
    pass "${label}"
  else
    fail "${label}"
    sed 's/^/     /' /tmp/cdc_validate.err
  fi
}

check_file() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    pass "required file exists: ${path}"
  else
    fail "required file missing: ${path}"
  fi
}

check_executable() {
  local path="$1"
  if [[ -x "${path}" ]]; then
    pass "executable permission set: ${path}"
  else
    fail "missing executable permission: ${path}"
  fi
}

printf "Validating Real-Time Order & Inventory CDC Platform\n"
printf "Repo: %s\n\n" "${REPO_ROOT}"

required_files=(
  README.md
  Makefile
  compose.yml
  .env.example
  .github/workflows/validate.yml
  debezium/connectors/postgres-source.json
  postgres/init/001_schema.sql
  clickhouse/init/001_raw_tables.sql
  clickhouse/init/002_current_tables.sql
  clickhouse/init/003_fact_dim_marts.sql
  clickhouse/init/004_observability_tables.sql
  stream_processor/pyproject.toml
  stream_processor/src/main.py
  dashboard/pyproject.toml
  dashboard/app.py
  scripts/register_connector.sh
  scripts/create_topics.sh
  scripts/check_demo_health.sh
  scripts/run_demo_sequence.sh
)

for file in "${required_files[@]}"; do
  check_file "${file}"
done

if [[ -f .env ]]; then
  pass ".env exists"
else
  warn ".env is missing; copy .env.example to .env before running the stack"
fi

check_executable scripts/register_connector.sh
check_executable scripts/create_topics.sh
check_executable scripts/validate_project.sh
check_executable scripts/check_demo_health.sh
check_executable scripts/run_demo_sequence.sh

python_files=()
while IFS= read -r file; do
  python_files+=("${file}")
done < <(
  find stream_processor dashboard scripts \
    -path '*/.venv/*' -prune -o \
    -path '*/__pycache__/*' -prune -o \
    -name '*.py' -type f -print | sort
)

if [[ ${#python_files[@]} -gt 0 ]]; then
  run_check "Python syntax compile (${#python_files[@]} files)" python3 -B -m py_compile "${python_files[@]}"
else
  fail "no Python files found to validate"
fi

shell_files=()
while IFS= read -r file; do
  shell_files+=("${file}")
done < <(find scripts -maxdepth 1 -name '*.sh' -type f -print | sort)
if [[ ${#shell_files[@]} -gt 0 ]]; then
  run_check "Shell syntax bash -n (${#shell_files[@]} files)" bash -n "${shell_files[@]}"
else
  fail "no shell scripts found to validate"
fi

run_check "Debezium connector JSON validity" python3 -m json.tool debezium/connectors/postgres-source.json

if command -v ruby >/dev/null 2>&1; then
  run_check "compose.yml YAML validity" ruby -e 'require "yaml"; YAML.load_file("compose.yml");'
else
  warn "ruby is not available; skipping standalone YAML parse for compose.yml"
fi

if command -v podman >/dev/null 2>&1; then
  if podman info >/dev/null 2>&1; then
    run_check "podman compose config" podman compose -f compose.yml config
  else
    warn "Podman is installed but not running; skipped podman compose config"
  fi
else
  warn "Podman is not installed; skipped podman compose config"
fi

rm -f /tmp/cdc_validate.out /tmp/cdc_validate.err

printf "\nValidation summary: %s failure(s), %s warning(s)\n" "${failures}" "${warnings}"

if [[ ${failures} -gt 0 ]]; then
  printf "Result: FAIL\n"
  exit 1
fi

printf "Result: PASS\n"
exit 0
