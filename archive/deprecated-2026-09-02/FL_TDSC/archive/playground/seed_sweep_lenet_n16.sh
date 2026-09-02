#!/usr/bin/env bash
# Multi-seed verification: is N=16 LeNet M8a = 0.7026 a robust effect or seed luck?
set -euo pipefail
cd "$(dirname "$0")/.."
source playground/.venv/bin/activate
mkdir -p playground/results

for seed in 42 7 123 1 5; do
    out="playground/results/m8_seed${seed}.json"
    log="playground/results/m8_seed${seed}.log"
    echo "=== seed=$seed -> $out ==="
    python -u -m playground.m8_oneandhalfshot \
        --Ns 16 \
        --methods M8a \
        --arch lenet5 \
        --probe-size 500 \
        --seed "$seed" \
        --out "$out" 2>&1 | tee "$log"
done
echo "=== seed sweep done ==="
