#!/bin/bash
# Regenerate PDF artefacts from hand-authored SVG sources.
#
# Run on a node with librsvg2-bin (rsvg-convert) installed; the OHPC Valar
# login node does not have it. Either submit via sbatch onto a node that
# does, run on Overleaf at submit time, or install librsvg2-bin in a conda
# env locally. Per the ralph/prompt.md GOLDEN RULE, this is not training-
# heavy work — running locally is fine if rsvg-convert is on PATH.
#
# Convention: SVG sources live in FL_TDSC/figures/*.svg; the resulting
# PDFs land alongside as FL_TDSC/figures/*.pdf and are what
# \includegraphics{...} resolves to in the manuscript.

set -euo pipefail

cd "$(dirname "$0")/.."

rsvg-convert --format=pdf FL_TDSC/figures/threat_model_v2.svg -o FL_TDSC/figures/threat_model_v2.pdf
rsvg-convert --format=pdf FL_TDSC/figures/protocol_overview_v2.svg -o FL_TDSC/figures/protocol_overview_v2.pdf
