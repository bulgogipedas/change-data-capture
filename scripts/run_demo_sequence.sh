#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

run_step() {
  local label="$1"
  local script="$2"
  printf "\n== %s ==\n" "${label}"
  uv run --project scripts python "${script}"
}

printf "Running ShopPulse flash sale demo sequence\n"
printf "Repo: %s\n" "${REPO_ROOT}"
printf "Note: this mutates PostgreSQL demo data. Keep the CDC processor running in another terminal.\n"

run_step "Flash sale checkout: create order, order item, pending payment, inventory decrement, stock movement" scripts/simulate_flash_sale.py
run_step "Payment update: move one pending payment to SUCCESS and mark order PAID" scripts/simulate_payment_updates.py
run_step "Inventory incident: force one product below low-stock threshold" scripts/simulate_inventory_changes.py
run_step "Cancellation/refund: cancel a paid order and create a completed refund" scripts/simulate_refunds_and_cancellations.py
run_step "Delete handling: insert and physically delete a shipment row" scripts/simulate_delete_handling.py

printf "\nDemo sequence complete.\n"
printf "Next: refresh Streamlit, inspect Redpanda Console, and run 'cd stream_processor && uv run python -m src.quality.run_checks'.\n"
