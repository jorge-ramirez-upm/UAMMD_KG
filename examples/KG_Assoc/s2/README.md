# S2 CUDA campaign

Build on the CUDA host, then execute gates in order. Do not proceed if the
previous gate has a stationarity or invariant failure.

```bash
make -C examples/KG_Assoc kg_assoc_stars
examples/KG_Assoc/s2/run_s2_campaign.sh INPUT_FILE OUTPUT_DIRECTORY baseline
python3 examples/KG_Assoc/analysis/analyze_s2.py OUTPUT_DIRECTORY/baseline_*.state \
  --summary OUTPUT_DIRECTORY/baseline_summary.csv
```

Gate A has three 500,000-step canonical replicas. Their stationary bonded
fractions should span no more than 0.02; each individual stationarity-half
difference should be at most 0.01.

```bash
examples/KG_Assoc/s2/run_s2_campaign.sh INPUT_FILE OUTPUT_DIRECTORY cadence
python3 examples/KG_Assoc/analysis/analyze_s2.py OUTPUT_DIRECTORY/cadence_*.state \
  --summary OUTPUT_DIRECTORY/cadence_summary.csv
```

Gate B has four 500,000-step cadence runs (`Nevery=20,50,100,200`). Compare
20, 50, and 100 first: their stationary bonded fractions should agree within
0.01. Treat 200 as a coarse diagnostic only.

After choosing a cadence, run Gates C and D with `S2_NEVERY` set to that value
(the default is 100):

```bash
S2_NEVERY=100 examples/KG_Assoc/s2/run_s2_campaign.sh INPUT_FILE OUTPUT_DIRECTORY ea
S2_NEVERY=100 examples/KG_Assoc/s2/run_s2_campaign.sh INPUT_FILE OUTPUT_DIRECTORY ee
```

Gate C has three Ea runs: 500,000 steps for Ea 2 and 4, 1,000,000 for Ea 6.
Gate D has four 500,000-step Ee runs. The script creates `.command` and `.log`
files for every run and refuses existing output unless `--force` is supplied.
Use `list` instead of a stage to print all 14 commands without executing them.

`analyze_s2.py` uses the final half of each trajectory by default. It fails on
missing provenance, invalid event histories, non-unit sticker valence, or a
failure to reproduce state-file active-bond counts. S2 does not interpret
bonded or intra/inter fractions as equilibrium quantities until GPU outputs are
returned and analyzed.
