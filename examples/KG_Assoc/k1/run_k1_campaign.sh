#!/usr/bin/env bash
# GPU host: ./run_k1_campaign.sh ../../kg_assoc_k1 pilot|baseline|full
set -euo pipefail
exe=${1:?executable}; mode=${2:-pilot}; root=$(cd "$(dirname "$0")" && pwd); out=$root/results; mkdir -p "$out"
run(){ local ea=$1 ee=$2 every=$3 rep=$4 tag="Ea${ea}_Ee${ee}_N${every}_r${rep}"; [[ -s $out/$tag.state ]]&&return; "$exe" --rho .05 --Ea "$ea" --Ee "$ee" --Nevery "$every" --seed $((410000+rep*1000+ea*100+ee*10+every)) --output "$out/$tag"; }
case $mode in
 pilot) run 4 4 100 1;;
 baseline) for r in 1 2 3 4;do run 4 4 100 $r;done;;
 full) for r in 1 2 3 4;do for ea in 2 3 4 5 6;do run $ea 4 100 $r;done;for ee in 2 4 6 8;do run 4 $ee 100 $r;done;for n in 50 100 200;do run 4 4 $n $r;done;done;;
 *) echo 'mode: pilot|baseline|full' >&2;exit 2;;esac
