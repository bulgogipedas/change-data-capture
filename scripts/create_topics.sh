#!/usr/bin/env bash
set -euo pipefail

BROKER_CONTAINER="${BROKER_CONTAINER:-cdc-redpanda}"

topics=(
  dbserver1.public.customers
  dbserver1.public.sellers
  dbserver1.public.products
  dbserver1.public.inventory
  dbserver1.public.stock_movements
  dbserver1.public.orders
  dbserver1.public.order_items
  dbserver1.public.payments
  dbserver1.public.shipments
  dbserver1.public.refunds
)

for topic in "${topics[@]}"; do
  podman exec "${BROKER_CONTAINER}" rpk topic create "${topic}" --partitions 1 --replicas 1 >/dev/null 2>&1 || true
done

podman exec "${BROKER_CONTAINER}" rpk topic list
