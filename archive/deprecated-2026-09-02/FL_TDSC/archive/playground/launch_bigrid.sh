#!/usr/bin/env bash
# Big grid: {mlp, lenet5} x {uniform, samples} x {M0, M1, M3, M4} x N in {4,8,16,32}
set -euo pipefail
cd "$(dirname "$0")/.."
source playground/.venv/bin/activate

mkdir -p playground/results
for arch in mlp lenet5; do
    for wm in uniform samples; do
        out="playground/results/grid_${arch}_${wm}.json"
        log="playground/results/grid_${arch}_${wm}.log"
        echo "=== arch=$arch wm=$wm -> $out ==="
        python -u -m playground.run \
            --Ns 4,8,16,32 \
            --methods M0,M1,M3,M4 \
            --arch "$arch" \
            --weight-mode "$wm" \
            --teacher-epochs 10 \
            --K 5 \
            --anchors-per-class 50 \
            --within-class-cos 0.5 \
            --pre-align-epochs 5 \
            --anchor-lambda 1.0 \
            --out "$out" 2>&1 | tee "$log"
    done
done
echo "=== bigrid done ==="
