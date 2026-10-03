# K1 UAMMD validation harness

`kg_assoc_k1` is the many-sticker K1 analogue of the LAMMPS isolated WCA fluid. During preparation, association is disabled: random positions undergo bounded DPD push-off, a 10-level DPD ramp from amplitude 25 toward 1000, then WCA/Langevin equilibration. Persistent-ID diagnostics report the minimum separation and finite position/velocity status after the initial soft stage, DPD ramp, and WCA equilibration; the post-ramp state must satisfy the 0.8 WCA-safety threshold.

`run_k1_campaign.sh` is the unchanged historical N=256 reference launcher. Its purpose is the four-replica K1 comparison campaign at `rho=.05`, `T=1`, `dt=.005`, `nu0=20`, damping 2, 5,000 DPD steps, 20,000 WCA warm-up steps, and 100,000 production steps.

## Large-N campaign

`run_k1_large_campaign.sh` is the separate N=32768 validation launcher. Its frozen parameters are `rho=.05`, `T=1`, `dt=.005`, `nu0=20`, damping 2, 10,000 initial DPD push-off steps, the built-in staged DPD ramp, 20,000 WCA warm-up steps, and 1,000,000 production steps. It starts with one replica; set `REPLICAS=N` to add replicas later.

The full grid has exactly 10 unique conditions:

- Ea sweep: `(Ea,Ee,Nevery) = (2,4,100), (3,4,100), (4,4,100), (5,4,100), (6,4,100)`.
- Additional Ee points: `(4,2,100), (4,6,100), (4,8,100)`.
- Additional cadence points: `(4,4,50), (4,4,200)`.

On a CUDA host:

```bash
make -C examples/KG_Assoc
examples/KG_Assoc/k1/run_k1_large_campaign.sh \
  examples/KG_Assoc/kg_assoc_k1 pilot
examples/KG_Assoc/k1/run_k1_large_campaign.sh \
  examples/KG_Assoc/kg_assoc_k1 central
examples/KG_Assoc/k1/run_k1_large_campaign.sh \
  examples/KG_Assoc/kg_assoc_k1 full
```

`pilot` is a 20,000-step central-condition run with a distinct `pilot_` prefix; `central` is the full central run; `full` executes the ten-condition grid. `list` prints the full grid without execution. Completed non-empty `.state` files are skipped. Output prefixes use `large_Np32768_Ea*_Ee*_N*_r*`; metadata in the state header is authoritative. The seed formula is `((((Np*10+Ea)*10+Ee)*1000+Nevery)*10+replica)`, unique for the frozen integer grid.

Analyze large-N output with:

```bash
python3 examples/KG_Assoc/analysis/analyze_k1.py \
  'examples/KG_Assoc/k1/results_large/*.state' \
  --summary examples/KG_Assoc/k1/results_large/k1_large_summary.csv
```

State rows are timestep, physical time, free stickers, active dimers, creations, and breaks. The analyzer uses exact finite-N pair exposure, trapezoidal physical-time integrals, reports rectangle exposure differences, and groups conditions by `Nparticles`, `Ea`, `Ee`, and `Nevery`. `Nevery=50` samples every 100 steps by default, so its exposure diagnostic is intentionally weaker; events remain exact.
