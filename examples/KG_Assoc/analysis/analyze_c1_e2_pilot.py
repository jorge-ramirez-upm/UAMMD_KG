#!/usr/bin/env python3
"""Fail-closed C1 E2 validation and descriptive three-replica scientific review."""

import argparse
import collections
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
import sys

import analyze_e2_stationarity as stationarity
import analyze_p45_topology as topology
import analyze_p46_bond_dynamics as dynamics
import validate_c1_restart_bank as restart

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "campaign"))
import kg_assoc_campaign as campaign
import kg_assoc_e1 as e1


BANK_ID = "F04_N010_RP080_EE08"
STEPS = 6000000
METRICS = ("bonds", "bound_fraction", "free", "intra", "inter",
           "largest_cluster_fraction", "mean_degree", "L1", "L2")
OUTPUTS = (".state", ".events", ".numerics.tsv", ".restart.lammpsdat",
           ".assoc_restart", ".final_permanent.lammpsdat", ".final_associations")


def model():
    return next(item for item in campaign.campaign_systems()
                if item["system_id"] == "F04_N010_RP080_EE08_EA04")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def numerics(path, rows, count):
    parsed = []
    with path.open() as source:
        require(source.readline().strip() ==
                "# step time kinetic_energy temperature min_permanent_bond max_permanent_bond",
                "incorrect E2 numerics header")
        for line in source:
            values = list(map(float, line.split()))
            require(len(values) == 6 and all(math.isfinite(value) for value in values),
                    "malformed or nonfinite numerics")
            require(values[2] > 0 and math.isclose(2 * values[2] / (3 * count), values[3],
                                                rel_tol=1e-10), "kinetic-temperature mismatch")
            require(0 < values[4] <= values[5] < 1.5, "invalid sampled permanent FENE bond")
            parsed.append(values)
    require(len(parsed) == len(rows), "numerics/state count mismatch")
    for values, row in zip(parsed, rows):
        require(values[0] == row["step"] and math.isclose(values[1], row["time"], abs_tol=1e-9),
                "numerics/state synchronization failure")
    return parsed


def replay(rows, events, system, network=True):
    """Reconstruct from the explicitly unassociated E1 start, retaining event order."""
    active, partners = set(), {}
    multiplicity = collections.Counter()
    counters = collections.Counter()
    event_rows = []
    event_index = 0
    for index, row in enumerate(rows):
        while event_index < len(events) and events[event_index][0] <= row["step"]:
            step, kind, pair = events[event_index]
            first, second = pair
            stars = tuple(sorted((system["atom_to_star"][first], system["atom_to_star"][second])))
            inter = stars[0] != stars[1]
            gain = loss = 0
            if kind == "C":
                require(first not in partners and second not in partners,
                        "duplicate creation or valence-one violation")
                active.add(pair)
                partners[first], partners[second] = second, first
                counters["creations"] += 1
                counters["inter" if inter else "intra"] += 1
                if inter:
                    gain = int(multiplicity[stars] == 0)
                    multiplicity[stars] += 1
            else:
                require(pair in active and partners.get(first) == second and
                        partners.get(second) == first, "break without reciprocal active pair")
                active.remove(pair)
                del partners[first], partners[second]
                counters["breaks"] += 1
                counters["inter" if inter else "intra"] -= 1
                if inter:
                    multiplicity[stars] -= 1
                    loss = int(multiplicity[stars] == 0)
            counters["neighbor_gains"] += gain
            counters["neighbor_losses"] += loss
            event_rows.append({"step": step, "type": kind, "neighbor_gain": gain,
                               "neighbor_loss": loss})
            event_index += 1
        require(row["creations"] == counters["creations"] and
                row["breaks"] == counters["breaks"] and row["bonds"] == len(active) and
                row["intra"] == counters["intra"] and row["inter"] == counters["inter"],
                "accepted-event/state accounting mismatch")
        row["neighbor_gains"] = counters["neighbor_gains"]
        row["neighbor_losses"] = counters["neighbor_losses"]
        if network:
            pairs = [(a, b, system["atom_to_star"][a], system["atom_to_star"][b])
                     for a, b in sorted(active)]
            graph = topology.frame_observables(index, int(row["step"]), row["time"], pairs, system)
            l1 = sum(value * (value - 1) // 2 for value in graph["edge_multiplicity"].values())
            neighbors = graph["neighbors"]
            l2 = sum(1 for a in system["stars"] for b in neighbors[a] if b > a
                     for c in neighbors[b] if c > b and c in neighbors[a])
            comparison = {"intra": graph["intra_bonds"], "inter": graph["inter_bonds"],
                          "components": graph["connected_components"],
                          "largest_size": graph["largest_component_size"],
                          "largest_cluster_fraction": graph["largest_component_fraction"],
                          "mean_degree": graph["mean_k_neighbor"], "L1": l1, "L2": l2,
                          "second_degree_moment": statistics.mean(
                              degree ** 2 for degree in graph["neighbor_degree"].values())}
            require(all(math.isclose(row[key], value, rel_tol=1e-9, abs_tol=1e-9)
                        for key, value in comparison.items()), "event/network reconstruction mismatch")
    require(event_index == len(events), "events after final diagnostic")
    return active, event_rows


def verify_outputs(prefix, steps=STEPS, seed=None, network=False):
    prefix = Path(prefix)
    for suffix in OUTPUTS:
        require(Path(str(prefix) + suffix).is_file(), "missing E2 output: " + str(prefix) + suffix)
    metadata, rows = stationarity.read_state(str(prefix) + ".state")
    expected = dict(restart.CANONICAL, T=1, diagnostic_every=1000, start_step=0,
                    total_requested_steps=steps, total_particles=43563, stickers=4000,
                    permanent_bonds=40000)
    expected.pop("temperature")
    for key, value in expected.items():
        require(math.isclose(float(metadata.get(key, "nan")), value, rel_tol=0, abs_tol=1e-12),
                "C1 state metadata mismatch: " + key)
    require(steps % 1000 == 0 and [row["step"] for row in rows] == list(range(0, steps + 1, 1000)),
            "incomplete or duplicated E2 state samples")
    require(all(math.isclose(row["time"], row["step"] * 0.01, abs_tol=1e-9) for row in rows),
            "incorrect E2 absolute time")
    require(rows[0]["bonds"] == rows[0]["creations"] == rows[0]["breaks"] == 0,
            "pilot must start from unassociated E1, not an earlier E2 state")
    require(float(metadata.get("chemistry_sweeps", "nan")) == steps // 100,
            "missing or incorrect completed chemistry cadence")
    if seed is not None:
        require(int(metadata["seed"]) == seed, "unexpected E2 seed")
    snapshot_path = Path(str(prefix) + ".restart.lammpsdat")
    snapshot_check = e1.check_snapshot(snapshot_path, model())
    system = topology.read_system(str(snapshot_path), 2)
    event_metadata, events = dynamics.read_events(str(prefix) + ".events", system)
    require(all(float(event_metadata.get(key, "nan")) == float(metadata[key])
                for key in expected if key != "diagnostic_every"), "event/state provenance mismatch")
    require(int(event_metadata["seed"]) == int(metadata["seed"]) and
            event_metadata["input_file"] == metadata["input_file"], "event input/seed mismatch")
    require(all(0 < step <= steps and step % 100 == 0 for step, _, _ in events),
            "accepted event outside chemistry cadence")
    active, event_rows = replay(rows, events, system, network)
    sidecar, pairs = restart.read_metadata(str(prefix) + ".assoc_restart")
    for key, value in restart.CANONICAL.items():
        require(float(sidecar.get(key, "nan")) == value, "restart parameter mismatch: " + key)
    require(int(sidecar["seed"]) == int(metadata["seed"]) and
            int(sidecar["completed_steps"]) == steps and set(pairs) == active and
            len(pairs) == len(active), "restart identity or completed-step mismatch")
    require(int(sidecar["creations"]) == rows[-1]["creations"] and
            int(sidecar["breaks"]) == rows[-1]["breaks"], "restart counter mismatch")
    require(rows[-1]["creations"] > 0 and rows[-1]["breaks"] > 0,
            "C1 pilot has no accepted creation or rupture")
    data = campaign.parse_lammps_data(snapshot_path)
    mirrored = []
    with Path(str(prefix) + ".final_associations").open() as source:
        for line in source:
            if line.strip() and not line.startswith("#"):
                fields = list(map(int, line.split()))
                require(len(fields) == 4 and fields[0] in system["stickers"] and
                        fields[1] in system["stickers"] and fields[2:] ==
                        [system["atom_to_star"][fields[0]], system["atom_to_star"][fields[1]]],
                        "invalid final association mirror IDs")
                mirrored.append(tuple(fields[:2]))
    require(set(mirrored) == active and len(mirrored) == len(active), "final association mirror mismatch")
    require(Path(str(prefix) + ".final_permanent.lammpsdat").read_bytes().split(b"\n", 1)[1] ==
            snapshot_path.read_bytes().split(b"\n", 1)[1], "archival/restart particle states differ")
    for first, second in active:
        require(restart.distance(data["positions"][first], data["positions"][second],
                                 data["bounds"]) < 1.5, "invalid final temporary FENE geometry")
    with snapshot_path.open() as source:
        require(source.readline().rstrip().endswith("step " + str(steps)), "snapshot step mismatch")
    numeric_rows = numerics(Path(str(prefix) + ".numerics.tsv"), rows, 43563)
    require(math.isclose(numeric_rows[-1][3], snapshot_check["final_temperature"],
                         rel_tol=1e-5), "final snapshot/numerical velocity mismatch")
    previous = None
    observed_bonds = 0
    integer_fields = ("free", "bonds", "creations", "breaks", "intra", "inter", "components",
                      "largest_size", "L1", "L2", "active_observations")
    for row, numeric in zip(rows, numeric_rows):
        require(all(row[key] >= 0 and row[key].is_integer() for key in integer_fields),
                "invalid E2 population/count")
        observed_bonds += row["bonds"]
        require(row["active_observations"] == observed_bonds,
                "active-geometry observation count mismatch")
        if previous is not None:
            require(all(row[key] >= previous[key] for key in
                        ("creations", "breaks", "active_observations", "max_active_bond_distance")),
                    "nonmonotonic cumulative diagnostics")
        require(0 <= row["max_active_bond_distance"] < 1.5 and
                all(0 <= row[key] <= 1 for key in
                    ("fraction_active_gt_1p25", "fraction_active_gt_1p30", "fraction_active_gt_1p40")),
                "invalid cumulative active-distance diagnostic")
        row.update(kinetic_energy=numeric[2], temperature=numeric[3],
                   min_permanent_bond=numeric[4], max_permanent_bond=numeric[5])
        previous = row
    return metadata, rows, event_rows, {"numerical_status": "valid",
            "chemical_stationarity": "review_required", "network_stationarity": "review_required",
            "scientific_acceptance": "review_required", "snapshot": snapshot_check,
            "network_reconstructed": network, "samples": len(rows), "events": len(events),
            "files": {suffix: campaign.sha256(Path(str(prefix) + suffix)) for suffix in OUTPUTS}}


def describe_window(rows, events, start, end):
    selected = [row for row in rows if start < row["step"] <= end]
    require(len(selected) >= 4, "too few window samples")
    times = [row["time"] for row in selected]
    metrics = {}
    for name in METRICS:
        values = [row[name] for row in selected]
        tau, effective = stationarity.iat(values, times)
        variance = statistics.pvariance(values)
        metrics[name] = {"mean": statistics.mean(values),
                         "tau_time": tau * statistics.mean(b - a for a, b in zip(times, times[1:])),
                         "effective_samples_estimate": effective if variance else None,
                         "sem_estimate": math.sqrt(variance / effective) if effective and variance else None,
                         "blocks": stationarity.block_means(values, 10),
                         "slope": stationarity.slope(times, values)}
    accepted = [event for event in events if start < event["step"] <= end]
    duration = (end - start) * 0.01
    counts = {key: sum(event["type"] == code for event in accepted)
              for key, code in (("creations", "C"), ("breaks", "B"))}
    counts.update(neighbor_gains=sum(event["neighbor_gain"] for event in accepted),
                  neighbor_losses=sum(event["neighbor_loss"] for event in accepted))
    return {"start_step_exclusive": start, "end_step_inclusive": end,
            "duration": duration, "metrics": metrics, "event_counts": counts,
            "event_rates_per_time": {key: value / duration for key, value in counts.items()},
            "event_rates_per_star_time": {key: value / (1000 * duration) for key, value in counts.items()}}


def write_csv(path, rows):
    with path.open("x", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze(root, output, historical):
    require(not output.exists(), "analysis directory already exists")
    summaries, tables, histories = [], [], []
    # Validate all runs before creating an analysis directory or plotting anything.
    for replica in (1, 2, 3):
        bank = root / "banks/e2" / BANK_ID / f"r{replica:03d}"
        command = campaign.load_json(bank / "command.json")
        require(command["status"] == "finished" and command.get("exit_code") == 0 and
                (bank / "complete.json").is_file(), "E2 replica is incomplete or unverified")
        metadata, rows, events, validation = verify_outputs(
            bank / "state", steps=STEPS, seed=22000 + replica, network=True)
        complete = campaign.load_json(bank / "complete.json")
        require(complete["files"] == validation["files"], "completed E2 outputs changed")
        window_steps = STEPS // 3
        windows = [describe_window(rows, events, start, start + window_steps)
                   for start in (0, window_steps, 2 * window_steps)]
        summaries.append({"replica": replica, "seed": 22000 + replica, "metadata": metadata,
                          "validation": validation, "full_stationarity": stationarity.describe(rows, 12),
                          "windows": windows, "command": command})
        summaries[-1]["numerical_windows"] = [
            {"start_step_exclusive": start, "end_step_inclusive": start + window_steps,
             "mean_temperature": statistics.mean(row["temperature"] for row in rows
                                                   if start < row["step"] <= start + window_steps),
             "min_permanent_bond": min(row["min_permanent_bond"] for row in rows
                                       if start < row["step"] <= start + window_steps),
             "max_permanent_bond": max(row["max_permanent_bond"] for row in rows
                                       if start < row["step"] <= start + window_steps)}
            for start in (0, window_steps, 2 * window_steps)]
        histories.append(rows)
        for index, window in enumerate(windows, 1):
            for name, metric in window["metrics"].items():
                tables.append({"replica": replica, "window": index, "observable": name,
                               "mean": metric["mean"], "sem_estimate": metric["sem_estimate"],
                               "tau_time": metric["tau_time"],
                               "effective_samples_estimate": metric["effective_samples_estimate"],
                               "slope": metric["slope"]})
    historical_reports = []
    for path in historical:
        metadata, rows = stationarity.read_state(path)
        require(all(float(metadata.get(key, "nan")) == value for key, value in
                    {"Ea": 4, "Ee": 8, "nu0": 20, "Nevery": 100, "r_assoc": 1.25,
                     "dt": 0.01, "T": 1, "arms": 4, "narm": 10, "stickers": 4000}.items()),
                "historical comparison is not C1")
        historical_reports.append({"path": str(path), "sha256": campaign.sha256(path),
                                   "summary": stationarity.describe(rows, 10)})
    output.mkdir(parents=True)
    historical_path = Path(__file__).with_name("c1_e2_historical.json")
    reference = campaign.load_json(historical_path)
    comparison = {name: dynamics.replica_statistics(
                      [item["windows"][-1]["metrics"][name]["mean"] for item in summaries])
                  for name in METRICS}
    campaign.write_json(output / "summary.json", {"replicas": summaries,
                        "replica_comparison_last_2M": comparison, "historical": historical_reports,
                        "historical_p31_reference": reference,
                        "scientific_acceptance": "review_required"})
    configuration = {"git_sha": campaign.git_sha(), "analyzer_sha256": campaign.sha256(Path(__file__)),
                     "dataset_root": str(root), "created_at": datetime.now(timezone.utc).isoformat(),
                     "windows": "(0,2M],(2M,4M],(4M,6M]", "blocks_per_window": 10,
                     "historical_paths": list(map(str, historical)), "independent_units": "replicas",
                     "historical_p31_reference_sha256": campaign.sha256(historical_path),
                     "iat_method": "existing E2 biased autocovariance, first nonpositive lag",
                     "turnover": "event-level loss/gain of distinct molecular neighbors; not diffusion"}
    campaign.write_json(output / "analysis_config.json", configuration)
    write_csv(output / "windowed_observables.csv", tables)
    historical_table = []
    for name in METRICS:
        historical_values = []
        for old in reference["replicas"]:
            if name == "bonds":
                value = 2000 * old["bound_fraction"]
            elif name == "free":
                value = 4000 * (1 - old["bound_fraction"])
            else:
                value = old[name]
            historical_values.append(value)
        historical_table.append({"observable": name,
            "historical_s12001_last_3M": historical_values[0],
            "historical_s12002_last_3M": historical_values[1],
            **{f"new_r{item['replica']:03d}_last_2M": item["windows"][-1]["metrics"][name]["mean"]
               for item in summaries}})
    write_csv(output / "historical_comparison.csv", historical_table)
    write_csv(output / "historical_events.csv", [
        dict(seed=old["seed"], creations=old["creations"], breaks=old["breaks"],
             duration=reference["late_event_window_duration"],
             creations_per_time=old["creations"] / reference["late_event_window_duration"],
             breaks_per_time=old["breaks"] / reference["late_event_window_duration"])
        for old in reference["late_accepted_events"]])
    rates = []
    for item in summaries:
        for index, window in enumerate(item["windows"], 1):
            rates.append(dict(replica=item["replica"], window=index,
                              **window["event_counts"],
                              **{name + "_per_time": value for name, value in window["event_rates_per_time"].items()}))
        write_csv(output / f"r{item['replica']:03d}_time_series.csv", histories[item["replica"] - 1])
        campaign.write_json(output / f"r{item['replica']:03d}_summary.json", item)
    write_csv(output / "windowed_events.csv", rates)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(3, 3, figsize=(12, 9))
    blocks, block_axes = plt.subplots(3, 3, figsize=(12, 9))
    for axis, block_axis, name in zip(axes.flat, block_axes.flat, METRICS):
        for replica, rows in enumerate(histories, 1):
            times = [row["time"] for row in rows]
            values = [row[name] for row in rows]
            axis.plot(times, values, linewidth=0.6, label=f"r{replica:03d}")
            block_axis.plot(stationarity.block_means(times, 30),
                            stationarity.block_means(values, 30), marker=".", label=f"r{replica:03d}")
        axis.set_title(name)
        block_axis.set_title(name)
        axis.set_xlabel("E2 time")
        block_axis.set_xlabel("E2 time (30 contiguous blocks)")
    axes.flat[0].legend()
    block_axes.flat[0].legend()
    figure.tight_layout()
    blocks.tight_layout()
    figure.savefig(output / "time_series.png", dpi=150)
    blocks.savefig(output / "block_means.png", dpi=150)
    numerical_figure, numerical_axes = plt.subplots(3, 1, figsize=(10, 8))
    for axis, name in zip(numerical_axes, ("temperature", "min_permanent_bond", "max_permanent_bond")):
        for replica, rows in enumerate(histories, 1):
            axis.plot([row["time"] for row in rows], [row[name] for row in rows],
                      linewidth=0.6, label=f"r{replica:03d}")
        axis.set_ylabel(name)
        axis.set_xlabel("E2 time")
    numerical_axes[0].legend()
    numerical_figure.tight_layout()
    numerical_figure.savefig(output / "numerics.png", dpi=150)
    plt.close("all")
    report = ["# C1 E2 pilot scientific review", "", "All three replicas passed numerical and event/network reconstruction checks.",
              "Chemical stationarity, network stationarity, replica agreement and final acceptance require scientific review.",
              "", "| Observable | Last-2M replica mean | Replica SEM | 95% t interval half-width |",
              "|---|---:|---:|---:|"]
    for name, metric in comparison.items():
        report.append(f"| {name} | {metric['mean']:.8g} | {metric['sem']:.5g} | {metric['ci95_half_width']:.5g} |")
    report += ["", "Inspect windowed_observables.csv, windowed_events.csv and both plots for drift and replica disagreement.",
               "IAT/SEM are estimates, not independent-frame counts or universal acceptance thresholds; constants have undefined temporal uncertainty.",
               "Historical intra/L1 IATs are approximately 1,700–2,800 time units; each 2M window spans 20,000 and each finer block only 2,000. Fine blocks are not independent. Finite-window IATs can miss slow tails; review replica-level spread and window drift together.",
               "L1 counts pairs of parallel inter-star bonds; L2 counts distinct-star triangles, not graph cycle rank.",
               "Geometry maxima and tail fractions in .state are cumulative, not instantaneous/window-local.",
               "Event turnover counts distinct-neighbor gain/loss with multiplicity accounted for; same-step recrossings remain events.",
               "Historical summaries in summary.json are comparison evidence, never pass/fail targets. Continuation segments are not stitched.",
               "historical_comparison.csv compares historical last-3M means with new last-2M means; these are not identical observation windows.",
               "No lifetime fit or transport inference is made from this nonstationary pilot."]
    with (output / "REPORT.md").open("x") as destination:
        destination.write("\n".join(report) + "\n")
    print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--output", required=True, help="new versioned directory under aggregate/e2")
    parser.add_argument("--historical-state", action="append", default=[])
    args = parser.parse_args()
    root = Path(args.dataset_root).resolve()
    output = Path(args.output).resolve()
    try:
        output.relative_to(root / "aggregate/e2")
        analyze(root, output, [Path(path).resolve() for path in args.historical_state])
    except (OSError, ValueError, KeyError) as error:
        print("C1 E2 ANALYSIS FAIL:", error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
