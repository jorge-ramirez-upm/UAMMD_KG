#!/usr/bin/env python3
"""Versioned, nonstitched four-window C1 recovery review; never runs MD."""

import argparse
from datetime import datetime, timezone
import math
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "campaign"))
import kg_assoc_c1_recovery as recovery

analysis = recovery.analysis
campaign = recovery.campaign
require = analysis.require
ACTIVITY = ("creations", "breaks", "neighbor_gains", "neighbor_losses")


def estimate(values, times):
    tau, effective = analysis.stationarity.iat(values, times)
    blocking = {}
    for count in (5, 10, 20):
        means = analysis.stationarity.block_means(values, count)
        blocking[count] = statistics.stdev(means) / math.sqrt(len(means))
    return dict(mean=statistics.mean(values),
                sem_estimate=math.sqrt(statistics.pvariance(values) / effective),
                tau_time=tau * (times[1] - times[0]), effective_samples_estimate=effective,
                slope=analysis.stationarity.slope(times, values),
                blocks=analysis.stationarity.block_means(values, 10),
                blocking_sem_sensitivity=blocking,
                resolution_warning=tau * (times[1] - times[0]) >= (times[-1] - times[0]) / 10)


def window(rows, events, start, end, stickers=4000, dt=.01, stars=1000, metrics=analysis.METRICS):
    result = analysis.describe_window(rows, events, start, end, metrics=metrics, dt=dt, stars=stars)
    require((end - start) % 1000 == 0, "window must align to diagnostics")
    bins = {key: [0] * ((end - start) // 1000) for key in ACTIVITY}
    boundary = next(row for row in rows if row["step"] == start)
    active = boundary["bonds"]
    previous = start
    free_exposure = bond_exposure = 0.0
    for event in events:
        step = event["step"]
        if not start < step <= end:
            continue
        interval = (step - previous) * dt
        free_exposure += (stickers - 2 * active) * interval
        bond_exposure += active * interval
        index = (step - start - 1) // 1000
        bins["creations" if event["type"] == "C" else "breaks"][index] += 1
        bins["neighbor_gains"][index] += event["neighbor_gain"]
        bins["neighbor_losses"][index] += event["neighbor_loss"]
        active += 1 if event["type"] == "C" else -1
        previous = step
    interval = (end - previous) * dt
    free_exposure += (stickers - 2 * active) * interval
    bond_exposure += active * interval
    times = [(start + (index + .5) * 1000) * dt for index in range(len(bins["creations"]))]
    result["activity"] = {key: estimate([count / (1000 * dt) for count in counts], times)
                          for key, counts in bins.items()}
    result["exposure"] = dict(free_sticker_time=free_exposure, active_bond_time=bond_exposure)
    result["population_normalized_rates"] = dict(
        creation_events_per_free_sticker_time=(result["event_counts"]["creations"] / free_exposure
                                             if free_exposure else None),
        rupture_events_per_active_bond_time=(result["event_counts"]["breaks"] / bond_exposure
                                            if bond_exposure else None))
    selected = [row for row in rows if start < row["step"] <= end]
    for key in metrics:
        result["metrics"][key].update(estimate([row[key] for row in selected],
                                               [row["time"] for row in selected]))
    for key in ("temperature", "min_permanent_bond", "max_permanent_bond"):
        if key in selected[0]:
            result["metrics"][key] = estimate([row[key] for row in selected],
                                              [row["time"] for row in selected])
    return result


def comparisons(records):
    comparisons = []
    for category in ("metrics", "activity"):
        for name in records[0]["corrected"][0][category]:
            for index in range(4):
                values = [record["corrected"][index][category][name]["mean"] for record in records]
                comparisons.append(dict(category=category, observable=name, window=index + 1,
                                        **analysis.dynamics.replica_statistics(values)))
            changes = [record["corrected"][-1][category][name]["mean"] -
                       record["corrected"][-2][category][name]["mean"] for record in records]
            comparisons.append(dict(category=category, observable=name, window="last_minus_previous",
                                    **analysis.dynamics.replica_statistics(changes)))
            changes = [record["corrected"][-1][category][name]["mean"] - statistics.mean(
                item[category][name]["mean"] for item in record["defective"]) for record in records]
            comparisons.append(dict(category=category, observable=name,
                                    window="last_corrected_minus_defective_4_6M",
                                    **analysis.dynamics.replica_statistics(changes)))
    return comparisons


def analyze(root, attempt, output):
    output.relative_to(root / "aggregate/e2")
    require(not output.exists(), "analysis directory already exists")
    recovery.verify(root, attempt)
    records, hashes = [], {}
    for replica in (1, 2, 3):
        parent, parent_hashes = recovery.authenticate_parent(root, replica, oracle=False)
        hashes.update(parent_hashes)
        # Old history remains explicitly defective context, not an equilibrium target.
        _, old_rows, old_events, _ = analysis.verify_outputs(parent, network=False)
        prefix = attempt / f"r{replica:03d}" / "state"
        _, rows = analysis.stationarity.read_state(str(prefix) + ".state")
        numeric = analysis.numerics(Path(str(prefix) + ".numerics.tsv"), rows, 43563)
        for row, values in zip(rows, numeric):
            row.update(temperature=values[3], min_permanent_bond=values[4], max_permanent_bond=values[5])
        system = analysis.topology.read_system(str(prefix) + ".restart.lammpsdat", 2)
        _, raw = analysis.dynamics.read_events(str(prefix) + ".events", system)
        initial, pairs = analysis.restart.read_metadata(str(parent) + ".assoc_restart")
        _, events = analysis.replay(rows, raw, system, network=False, initial=dict(
            pairs=pairs, creations=int(initial["creations"]), breaks=int(initial["breaks"])))
        for suffix in analysis.OUTPUTS:
            path = Path(str(prefix) + suffix)
            hashes[str(path)] = campaign.sha256(path)
        records.append(dict(replica=replica,
                            corrected=[window(rows, events, start, start + 500000)
                                       for start in range(6000000, 8000000, 500000)],
                            defective=[window(old_rows, old_events, start, start + 500000)
                                       for start in range(4000000, 6000000, 500000)]))
    output.mkdir(parents=True, exist_ok=False)
    tables = []
    for record in records:
        campaign.write_json(output / f"r{record['replica']:03d}.json", record)
        for label in ("corrected", "defective"):
            for index, item in enumerate(record[label], 1):
                for category in ("metrics", "activity"):
                    for name, values in item[category].items():
                        tables.append(dict(replica=record["replica"], dynamics=label, window=index,
                                           start_step=item["start_step_exclusive"],
                                           end_step=item["end_step_inclusive"], category=category,
                                           observable=name, mean=values["mean"], sem=values["sem_estimate"],
                                           tau_time=values["tau_time"]))
    analysis.write_csv(output / "windowed_observables.csv", tables)
    activity_rows = []
    for record in records:
        for label in ("corrected", "defective"):
            for index, item in enumerate(record[label], 1):
                activity_rows.append(dict(replica=record["replica"], dynamics=label, window=index,
                                          duration=item["duration"], **item["event_counts"],
                                          **{key + "_per_time": value for key, value in
                                             item["event_rates_per_time"].items()},
                                          **item["exposure"], **item["population_normalized_rates"]))
    analysis.write_csv(output / "windowed_events.csv", activity_rows)
    ensemble = comparisons(records)
    analysis.write_csv(output / "replica_comparisons.csv", ensemble)
    campaign.write_json(output / "summary.json", dict(replicas=records, comparisons=ensemble,
                                                     scientific_acceptance="review_required"))
    campaign.write_json(output / "analysis_config.json", dict(
        git_sha=campaign.git_sha(), analyzer_sha256=campaign.sha256(Path(__file__)),
        source_sha256=hashes, created_at=datetime.now(timezone.utc).isoformat(),
        corrected_windows="(6M,6.5M],(6.5M,7M],(7M,7.5M],(7.5M,8M]",
        defective_windows="(4M,4.5M],(4.5M,5M],(5M,5.5M],(5.5M,6M]",
        rate_bins_steps=1000, physical_bin_duration=10, blocks_per_window=10,
        uncertainty="first-nonpositive-lag IAT + block sensitivity; independent replicas Student-t df=2",
        exposure="exact piecewise-constant accepted-event populations, not candidate opportunity",
        continuity="no stitching through algorithm/MD-reseed boundary"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(3, 3, figsize=(12, 9))
    for axis, name in zip(axes.flat, analysis.METRICS):
        for record in records:
            for label, style in (("corrected", "-"), ("defective", "--")):
                windows = record[label]
                axis.errorbar([(item["start_step_exclusive"] + item["end_step_inclusive"]) * .005
                               for item in windows], [item["metrics"][name]["mean"] for item in windows],
                              yerr=[item["metrics"][name]["sem_estimate"] for item in windows],
                              linestyle=style, label=f"r{record['replica']:03d} {label}")
        axis.set_title(name)
        axis.set_xlabel("absolute E2 time; separate windows")
    axes.flat[0].legend(fontsize=6)
    figure.tight_layout()
    figure.savefig(output / "window_comparison.png", dpi=150)
    plt.close(figure)
    report = ["# C1 corrected-chemistry recovery review", "",
              "Numerical/completeness and seeded event/network reconstruction checks passed.",
              "Scientific acceptance: REVIEW REQUIRED; 2M is not guaranteed sufficient.", "",
              "Four corrected 500k windows and four defective 4–6M windows are kept separate.",
              "Rates count actual accepted events over 5000 physical time units per window.",
              "Neighbor activity counts zero-to-one/one-to-zero distinct inter-star edges, not bonds.",
              "IAT SEMs assume local stationarity; examine block means and trends before trusting them.",
              "Independent units are three histories, not frames; paired last-minus-previous replica",
              "differences use Student-t df=2. Original histories are not pass/fail targets.", "",
              "Review population, intra/inter, L1/L2, degree/component and activity changes together.",
              "Require no unresolved late drift at the available correlation-aware resolution,",
              "compatible independent histories and stable numerical diagnostics; impose no universal",
              "percent-change threshold. Broad intervals/long correlations mean unresolved evidence.",
              "Do not stitch lifetimes or stress/transport histories across the correction/reseed."]
    with (output / "REPORT.md").open("x") as target:
        target.write("\n".join(report) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    analyze(Path(args.dataset_root).resolve(), Path(args.attempt).resolve(), Path(args.output).resolve())


if __name__ == "__main__":
    main()
