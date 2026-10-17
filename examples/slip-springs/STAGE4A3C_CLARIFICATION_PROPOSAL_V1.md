# Stage 4A.3c clarification proposal V1 — not an applied amendment

The original plan and282 scientific commands are unchanged. No new criterion
in this proposal is applied. Resolve any desired amendment separately before
host acceptance; retain both versions and their hashes. Stage4A.3b.1 authorizes
readiness tools only, not Stage4A.3c experiments.

1. The frozen word "near" in the2*tau_e signal gate has no numerical proximity
   cutoff. The analyzer selects the nearest supported exported bin, records its
   offset, requires acquisition to reach2*tau_e and preserves all frozen origin/
   block-width conditions. Proposal for a future version: explicitly name this
   nearest-supported-bin convention, or agree a numerical cutoff before results.
2. "Resolved" timestep bins are not formally defined. The analyzer reports bins
   where either estimate's magnitude exceeds six chain SE; Gaussian comparisons
   cover all exported bins. Proposal: explicitly codify resolution before any
   extension; do not choose it after inspecting nonlinear tails.
3. Gate6's1% scale for comparing mean stresses names a zero-lag product scale
   (different dimensions). The tool uses the literal corresponding diagonal
   zero-lag scale for means and geometric-mean diagonals for cross-products.
   Proposal: a separately reviewed version could define sqrt(C_aa(0)) for mean
   stresses. That alternative is NOT used in this implementation.
4. Original memory scripts have peak CPU RSS and unscoped whole-device GPU
   observations, insufficient to prove sustained post-initialization resident
   growth. The new runner adds production-scoped process-tree RSS and GPU data
   without changing simulation argv. At least three observed production points
   are needed to identify a sustained monotone trend. Sparse or large oscillatory
   evidence remains insufficient, not passing. Proposal: specify monitoring
   cadence/minimum support and warm-up convention explicitly if short runs do
   not provide evidence. Do not lengthen frozen experiments or relax16MiB/5%
   thresholds automatically. Whole-device monitoring cannot assign GPU usage
   to this process; peak RSS alone cannot prove a plateau.

These ambiguities limit automatic interpretation, not the accepted Hamiltonian
or GPU stress implementation. The machine report preserves insufficient and
unresolved statuses; there is no silent acceptance of missing scientific evidence.
