#!/usr/bin/env python3
"""Lightweight stationarity diagnostics for kg_assoc_star_equilibrate output."""

import argparse
import math
import sys


OBSERVABLES = (
    "mean_rg2",
    "mean_center_terminal_r2",
    "temperature",
    "pressure",
)
REQUIRED_COLUMNS = (
    "step",
    "time",
    "e_bonded",
    "e_nonbonded",
    "e_kinetic",
    "e_total",
    "temperature",
    "pressure",
    "mean_rg2",
    "mean_center_terminal_r2",
    "min_permanent_bond",
    "max_permanent_bond",
)
MIN_UNIFORM_SAMPLES = 32
TIME_TOLERANCE = 1.0e-8


def read_diagnostics(stream):
    header = None
    rows = []
    for line_number, raw_line in enumerate(stream, 1):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            candidate = line[1:].strip().split()
            if candidate[:2] == ["step", "time"]:
                header = candidate
            continue
        if header is None:
            raise ValueError("data row before diagnostics header at line " + str(line_number))
        fields = line.split()
        if len(fields) != len(header):
            raise ValueError("wrong column count at line " + str(line_number))
        row = {}
        for name, field in zip(header, fields):
            try:
                value = float(field)
            except ValueError as error:
                raise ValueError("non-numeric value at line " + str(line_number)) from error
            if not math.isfinite(value):
                raise ValueError("non-finite value at line " + str(line_number))
            row[name] = value
        rows.append(row)
    if header is None:
        raise ValueError("missing diagnostics header")
    missing = [name for name in REQUIRED_COLUMNS if name not in header]
    if missing:
        raise ValueError("missing columns: " + ", ".join(missing))
    if not rows:
        raise ValueError("diagnostics contains no samples")
    return rows


def mean(values):
    return sum(values) / len(values)


def half_comparison(values):
    midpoint = len(values) // 2
    if midpoint == 0 or midpoint == len(values):
        raise ValueError("at least two samples are required for half comparison")
    first = mean(values[:midpoint])
    second = mean(values[midpoint:])
    scale = max(abs(first), abs(second), 1.0e-30)
    return first, second, abs(second - first) / scale


def linear_slope(times, values):
    if len(values) < 2:
        raise ValueError("at least two samples are required for a trend")
    time_mean = mean(times)
    value_mean = mean(values)
    denominator = sum((time - time_mean) ** 2 for time in times)
    if denominator == 0.0:
        raise ValueError("trend requires distinct times")
    numerator = sum(
        (time - time_mean) * (value - value_mean)
        for time, value in zip(times, values)
    )
    return numerator / denominator


def block_means(values, block_count=5):
    block_count = min(block_count, len(values))
    if block_count < 1:
        raise ValueError("at least one sample is required for blocks")
    return [
        mean(values[index * len(values) // block_count :
             (index + 1) * len(values) // block_count])
        for index in range(block_count)
    ]


def select_uniform_stage4_suffix(rows, minimum_samples=MIN_UNIFORM_SAMPLES,
                                 tolerance=TIME_TOLERANCE):
    if len(rows) < minimum_samples:
        raise ValueError("no sufficiently long uniform Stage-4 suffix")
    final_interval = rows[-1]["time"] - rows[-2]["time"]
    if final_interval <= 0.0:
        raise ValueError("final Stage-4 sampling interval is not positive")
    start = len(rows) - 2
    while start > 0:
        interval = rows[start]["time"] - rows[start - 1]["time"]
        scale = max(abs(final_interval), abs(interval), 1.0)
        if abs(interval - final_interval) > tolerance * scale:
            break
        start -= 1
    selected = rows[start:]
    if len(selected) < minimum_samples:
        raise ValueError("no sufficiently long uniform Stage-4 suffix")
    intervals = [later["time"] - earlier["time"]
                 for earlier, later in zip(selected, selected[1:])]
    sampling_interval = mean(intervals)
    return selected, sampling_interval


def integrated_autocorrelation_time(times, values):
    if len(values) < 32:
        return {"status": "insufficient samples", "tau": None, "effective": None}
    intervals = [later - earlier for earlier, later in zip(times, times[1:])]
    timestep = mean(intervals)
    if timestep <= 0.0 or any(abs(interval - timestep) > 1.0e-6 * timestep
                              for interval in intervals):
        return {"status": "nonuniform sampling", "tau": None, "effective": None}
    center = mean(values)
    variance = sum((value - center) ** 2 for value in values) / len(values)
    if variance == 0.0:
        return {"status": "zero variance", "tau": None, "effective": None}
    tau_steps = 0.5
    positive_lags = 0
    for lag in range(1, len(values) // 2):
        covariance = sum(
            (values[index] - center) * (values[index + lag] - center)
            for index in range(len(values) - lag)
        ) / (len(values) - lag)
        correlation = covariance / variance
        if correlation <= 0.0:
            break
        tau_steps += correlation
        positive_lags += 1
    if positive_lags == 0:
        return {"status": "no positive autocorrelation lag", "tau": timestep / 2.0,
                "effective": float(len(values))}
    tau = tau_steps * timestep
    effective = len(values) * timestep / (2.0 * tau)
    return {"status": "ok", "tau": tau, "effective": effective}


def summarize(rows, block_count):
    selected_rows, sampling_interval = select_uniform_stage4_suffix(rows)
    times = [row["time"] for row in selected_rows]
    result = {
        "total_rows_read": len(rows),
        "stage4_uniform_samples": len(selected_rows),
        "stage4_first_time": times[0],
        "stage4_last_time": times[-1],
        "sampling_interval": sampling_interval,
    }
    for name in OBSERVABLES:
        values = [row[name] for row in selected_rows]
        first, second, relative = half_comparison(values)
        second_start = len(values) // 2
        result[name] = {
            "first_mean": first,
            "second_mean": second,
            "relative_difference": relative,
            "second_half_slope": linear_slope(times[second_start:], values[second_start:]),
            "blocks": block_means(values, block_count),
        }
    for name in ("min_permanent_bond", "max_permanent_bond"):
        values = [row[name] for row in selected_rows]
        result[name] = {"minimum": min(values), "maximum": max(values)}
    result["autocorrelation"] = {
        name: integrated_autocorrelation_time(
            times, [row[name] for row in selected_rows])
        for name in ("mean_rg2", "mean_center_terminal_r2")
    }
    return result


def print_summary(summary):
    print("total_rows_read={total_rows_read} stage4_uniform_samples="
          "{stage4_uniform_samples} stage4_first_time={stage4_first_time:.12g} "
          "stage4_last_time={stage4_last_time:.12g} "
          "sampling_interval={sampling_interval:.12g}".format(**summary))
    for name in OBSERVABLES:
        values = summary[name]
        print("{} first_half_mean={:.12g} second_half_mean={:.12g} "
              "relative_half_difference={:.12g} second_half_slope={:.12g}".format(
                  name, values["first_mean"], values["second_mean"],
                  values["relative_difference"], values["second_half_slope"]))
        print("{} block_means={}".format(
            name, ",".join("{:.12g}".format(value) for value in values["blocks"])))
    for name in ("min_permanent_bond", "max_permanent_bond"):
        values = summary[name]
        print("{} observed_min={:.12g} observed_max={:.12g}".format(
            name, values["minimum"], values["maximum"]))
    for name, values in summary["autocorrelation"].items():
        if values["tau"] is None:
            print("{} autocorrelation_status={}".format(name, values["status"]))
        else:
            print("{} autocorrelation_status={} tau_int={:.12g} "
                  "effective_samples={:.12g}".format(
                      name, values["status"], values["tau"], values["effective"]))


def run_self_test():
    header = "# " + " ".join(REQUIRED_COLUMNS)
    lines = [header]
    for index in range(40):
        values = [
            index,
            index * 0.5,
            1.0,
            2.0,
            3.0,
            6.0,
            1.0,
            2.0,
            4.0 + index * 0.1,
            5.0 + index * 0.2,
            0.8,
            1.1,
        ]
        lines.append(" ".join(str(value) for value in values))
    rows = read_diagnostics(lines)
    assert len(rows) == 40
    selected, interval = select_uniform_stage4_suffix(rows)
    assert len(selected) == 40 and interval == 0.5
    first, second, relative = half_comparison([row["mean_rg2"] for row in rows])
    assert first < second and relative > 0.0
    assert linear_slope([0.0, 1.0, 2.0], [1.0, 3.0, 5.0]) == 2.0
    assert len(block_means([1.0] * 10, 5)) == 5
    autocorrelation = integrated_autocorrelation_time(
        [float(index) for index in range(40)], [float(index % 2) for index in range(40)])
    assert autocorrelation["tau"] is not None
    try:
        read_diagnostics([header, "0 0 nan 2 3 6 1 2 4 5 0.8 1.1"])
    except ValueError:
        pass
    else:
        raise AssertionError("non-finite input was accepted")
    try:
        read_diagnostics(["# step time bad", "0 0 1"])
    except ValueError:
        pass
    else:
        raise AssertionError("malformed input was accepted")
    transition_rows = []
    for index, time in enumerate((0.0, 0.1, 0.7, 1.4)):
        values = [
            index,
            time,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            100.0,
            -100.0,
            -100.0,
            0.1,
            5.0,
        ]
        transition_rows.append(dict(zip(REQUIRED_COLUMNS, values)))
    for index in range(40):
        time = 10.0 + index * 0.5
        values = [
            index + 4,
            time,
            1.0,
            2.0,
            3.0,
            6.0,
            1.0,
            2.0,
            4.0,
            5.0,
            0.8,
            1.1,
        ]
        transition_rows.append(dict(zip(REQUIRED_COLUMNS, values)))
    summary = summarize(transition_rows, 5)
    assert summary["total_rows_read"] == 44
    assert summary["stage4_uniform_samples"] == 40
    assert summary["stage4_first_time"] == 10.0
    assert summary["stage4_last_time"] == 29.5
    assert summary["sampling_interval"] == 0.5
    assert summary["mean_rg2"]["first_mean"] == 4.0
    try:
        select_uniform_stage4_suffix(rows[:10])
    except ValueError:
        pass
    else:
        raise AssertionError("short uniform suffix was accepted")
    print("E1_STATIONARITY_SELF_TEST PASS parsing, blocks, halves, trend, autocorrelation")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("diagnostics", nargs="?")
    parser.add_argument("--blocks", type=int, default=5)
    parser.add_argument("--self-test", action="store_true")
    arguments = parser.parse_args(argv)
    if arguments.self_test:
        run_self_test()
        return 0
    if not arguments.diagnostics or arguments.blocks < 1:
        parser.error("diagnostics path and positive --blocks are required")
    try:
        with open(arguments.diagnostics, encoding="utf-8") as stream:
            print_summary(summarize(read_diagnostics(stream), arguments.blocks))
    except (OSError, ValueError) as error:
        print("E1_STATIONARITY ERROR: {}".format(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
