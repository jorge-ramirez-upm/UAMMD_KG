# Associating-star system files

The system directories separate externally generated inputs from successive
equilibration products:

| Directory | Purpose |
|---|---|
| `generated/` | External raw C++ star-generator output. |
| `e1_equilibrated/` | Conformationally equilibrated configurations with chemistry disabled. |
| `e2_equilibrated/` | Future chemical/topological-equilibration output. |
| `restarts/` | Future validated restart ensemble. |

Generated `.lammpsdat` files are local, intentionally untracked inputs. E1
uses only permanent KG topology; it creates no associative bonds. E2 and
restart support are not implemented by E1.

| Development IDs | Generated input |
|---|---|
| C1, C2 | `Stars_NA4N10C1000rho0.85rhopoly0.8.lammpsdat` |
| C3 | `Stars_NA4N10C1000rho0.85rhopoly0.4.lammpsdat` |
| C4 | `Stars_NA4N10C1000rho0.85rhopoly0.2.lammpsdat` |
| C5 | `Stars_NA4N20C1000rho0.85rhopoly0.8.lammpsdat` |
| C6 | `Stars_NA4N40C1000rho0.85rhopoly0.8.lammpsdat` |

C1 and C2 share one E1 configuration because they differ only in `Ee`, which
is introduced later in E2.

Example E1 invocation:

```bash
./kg_assoc_star_equilibrate \
  -i systems/generated/Stars_NA4N10C1000rho0.85rhopoly0.8.lammpsdat \
  -o systems/e1_equilibrated/Stars_NA4N10C1000rho0.85rhopoly0.8.e1.lammpsdat \
  --arms 4 --narm 10
```

Stage-4 diagnostics default to `OUTPUT.e1_diagnostics`; use `--diagnostics`
and `--conformation-every` to override the path and cadence. The file contains
metadata comments followed by:

```text
# step time e_bonded e_nonbonded e_kinetic e_total temperature pressure mean_rg2 mean_center_terminal_r2 min_permanent_bond max_permanent_bond
```
