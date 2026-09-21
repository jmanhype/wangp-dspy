"""Leakage-safe, no-GPU replay for the preregistered spend-gate baselines."""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from services.director.renderers.policy import (
    RendererPolicyError, check_duration_on_grid, check_facing, check_guide_duration)
from training.spend_gate import canonical_json


@dataclass(frozen=True)
class ReplayReport:
    """Machine-readable replay evidence and its human-readable rendering."""

    metrics: dict[str, Any]
    markdown: str

    def write(self, output_dir: Path) -> tuple[Path, Path]:
        output_dir.mkdir(parents=True, exist_ok=True)
        metrics_path, report_path = output_dir / "replay-metrics.json", output_dir / "replay-report.md"
        metrics_path.write_text(canonical_json(self.metrics), encoding="utf-8")
        report_path.write_text(self.markdown, encoding="utf-8")
        return metrics_path, report_path


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    exponent = math.exp(value)
    return exponent / (1.0 + exponent)


def _complete(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if all(value["usable"] for value in row["gate_coverage"].values())]


def _bad(row: dict[str, Any]) -> bool:
    return any(row["gate_coverage"][name]["outcome"] == "fail" for name in ("whisper_post", "vision", "av_sync"))


def _features(row: dict[str, Any]) -> list[float]:
    value = row["preflight"]
    required = ("guide_duration_s", "requested_frames", "width", "height", "prompt_chars", "prompt_words")
    if any(value.get(name) is None for name in required) or not isinstance(value.get("whisper_pre_passed"), bool):
        raise ValueError("unknown preflight feature")
    return [float(value[name]) for name in ("whisper_pre_passed", "guide_duration_s", "requested_frames", "width", "height", "prompt_chars", "prompt_words")] + [1.0]


def _fit_logistic(rows: list[dict[str, Any]]) -> list[float] | None:
    labels, weights = [float(_bad(row)) for row in rows], None
    if len(set(labels)) < 2: return None
    weights = [0.0] * len(_features(rows[0]))
    for _ in range(500):
        gradient = [0.0] * len(weights)
        for row, label in zip(rows, labels, strict=True):
            features = _features(row)
            error = _sigmoid(sum(w * x for w, x in zip(weights, features, strict=True))) - label
            gradient = [g + error * x for g, x in zip(gradient, features, strict=True)]
        weights = [w - 0.02 * g / len(rows) for w, g in zip(weights, gradient, strict=True)]
    return weights


def _probability(weights: list[float], row: dict[str, Any]) -> float:
    return _sigmoid(sum(w * x for w, x in zip(weights, _features(row), strict=True)))


def _calibrate(probabilities: list[float], labels: list[float]) -> tuple[float, float] | None:
    if len(set(labels)) < 2: return None
    a, b = 0.0, 0.0
    for _ in range(300):
        ga = gb = 0.0
        for probability, label in zip(probabilities, labels, strict=True):
            error = _sigmoid(a * probability + b) - label
            ga += error * probability
            gb += error
        a -= 0.05 * ga / len(labels)
        b -= 0.05 * gb / len(labels)
    return a, b


def _deterministic(row: dict[str, Any]) -> str:
    try:
        _features(row)
        value = row["preflight"]
        guide, declared = float(value["guide_duration_s"]), float(value["declared_shot_duration_s"])
        check_duration_on_grid(guide, int(value.get("fps") or 24))
        check_guide_duration(guide, declared)
        if int(value["requested_frames"]) != round(guide * int(value.get("fps") or 24)): raise RendererPolicyError("frame envelope mismatch")
        if value["width"] is None or value["height"] is None:
            raise ValueError("unknown resolution")
        video = next((stream for stream in row["media"].get("ffprobe", {}).get("streams", []) if stream.get("codec_type") == "video"), None)
        if video is None or "nb_frames" not in video: raise ValueError("unknown delivered media envelope")
        if (int(video["width"]), int(video["height"])) != (value["width"], value["height"]): raise RendererPolicyError("resolution envelope mismatch")
        if int(video["nb_frames"]) != int(value["requested_frames"]): raise RendererPolicyError("delivered frame envelope mismatch")
        if not value.get("plate_available") or value.get("plate_facing") is None:
            return "abstain"
        check_facing(str(value["plate_path"]), "camera")
        return "abstain" if row["preflight"].get("plate_facing") != "camera" else "admit"
    except RendererPolicyError:
        return "reject"
    except ValueError:
        return "abstain"


def _heuristic(row: dict[str, Any]) -> str:
    value = row["preflight"]
    guide, chars = value.get("guide_duration_s"), value.get("prompt_chars")
    if guide is None or chars is None:
        return "abstain"
    return "admit" if value.get("audio_carrier") == "native_h3" and abs(float(guide) - 56.0 / 24.0) <= 1e-9 and chars >= 500 else "reject"


def _score(rows: list[dict[str, Any]], decisions: dict[str, str]) -> dict[str, Any]:
    admitted_bad = admitted = rejected_bad = rejected_good = abstain = correct = incorrect = avoided = 0
    for row in rows:
        decision, bad = decisions[row["row_id"]], _bad(row)
        attempts = int((row.get("queue") or {}).get("attempt_count") or 0) + 1
        if decision == "abstain": abstain += 1
        elif decision == "admit": admitted, admitted_bad, correct, incorrect = admitted + 1, admitted_bad + bad, correct + (not bad), incorrect + bad
        else: rejected_bad, rejected_good, correct, incorrect, avoided = rejected_bad + bad, rejected_good + (not bad), correct + bad, incorrect + (not bad), avoided + attempts * bad
    false_admit = admitted_bad / admitted if admitted else None
    feasible = false_admit is not None and false_admit <= 0.10
    return {"rows": len(rows), "admitted": admitted, "abstained": abstain, "rejected_bad": rejected_bad,
            "rejected_good": rejected_good, "correct_decisions": correct, "incorrect_decisions": incorrect,
            "false_admit": false_admit, "budget_met": feasible,
            "failed_attempts_avoided_per_run": avoided / len({row["run_group_id"] for row in rows}) if feasible else None}


def _bootstrap(rows: list[dict[str, Any]], decisions: dict[str, str], seed: int, samples: int) -> list[float]:
    groups = sorted({row["run_group_id"] for row in rows})
    rng = random.Random(seed)
    values = []
    for _ in range(samples):
        selected = [row for group in (rng.choice(groups) for _ in groups) for row in rows if row["run_group_id"] == group]
        value = _score(selected, decisions)["failed_attempts_avoided_per_run"]
        if value is not None:
            values.append(value)
    return values


def _bounds(values: list[float]) -> tuple[float | None, float | None]:
    if not values: return None, None
    ordered = sorted(values)
    return (ordered[max(0, math.floor(0.025 * (len(ordered) - 1)))], ordered[min(len(ordered) - 1, math.ceil(0.975 * (len(ordered) - 1)))])


def _probability_table(complete: list[dict[str, Any]], decisions: dict[str, str], probabilities: dict[str, float]) -> dict[str, Any]:
    score = _score(complete, decisions)
    defined = [(float(_bad(row)), probabilities[row["row_id"]]) for row in complete if row["row_id"] in probabilities]
    brier = sum((label - probability) ** 2 for label, probability in defined) / len(defined) if defined else None
    logloss = -sum(label * math.log(max(probability, 1e-15)) + (1-label) * math.log(max(1-probability, 1e-15))
                   for label, probability in defined) / len(defined) if defined else None
    bins = []
    for index in range(5):
        bucket = [(label, probability) for label, probability in defined if index / 5 <= probability < (index + 1) / 5]
        bins.append({"bin": f"{index/5:.1f}-{(index+1)/5:.1f}", "rows": len(bucket), "bad_rows": int(sum(label for label, _ in bucket)),
                     "mean_probability": sum(probability for _, probability in bucket) / len(bucket) if bucket else None})
    score.update(brier_score=brier, log_loss=logloss, confidence_bins=bins)
    return score


def replay_baselines(corpus_path: Path, *, seed: int = 17, bootstrap_samples: int = 2000, false_admit_budget: float = 0.10) -> ReplayReport:
    """Replay four preregistered policies on identical grouped folds."""
    rows = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines()]
    complete = _complete(rows)
    groups = sorted({row["run_group_id"] for row in complete})
    policies = {"always_admit": {row["row_id"]: "admit" for row in complete},
                "deterministic_preflight": {row["row_id"]: _deterministic(row) for row in complete},
                "transparent_heuristic": {row["row_id"]: _heuristic(row) for row in complete},
                "calibrated_model": {}}
    raw_decisions, raw_probabilities = {}, {}
    calibrated_probabilities, probability_rows, folds, recording_errors = {}, [], [], []
    for held in groups:
        train, weights = [row for row in complete if row["run_group_id"] != held], None
        try: weights = _fit_logistic(train)
        except ValueError as exc: recording_errors.append(f"held_out_group={held}: {exc}")
        training_groups = sorted({row["run_group_id"] for row in train})
        folds.append({"held_out_run_group": held, "training_rows": len(train), "training_groups": len(training_groups), "training_run_groups": training_groups, "training_row_ids": [row["row_id"] for row in train], "held_out_row_ids": [row["row_id"] for row in complete if row["run_group_id"] == held], "training_bad_rows": sum(_bad(row) for row in train)})
        if weights is None: continue
        fit = _calibrate([_probability(weights, row) for row in train], [float(_bad(row)) for row in train])
        for row in complete:
            if row["run_group_id"] != held: continue
            probability = _probability(weights, row)
            raw_probabilities[row["row_id"]] = probability
            raw_decisions[row["row_id"]] = "admit" if probability >= 0.5 else "reject"
            calibrated = _sigmoid(fit[0] * probability + fit[1]) if fit else 0.5
            calibrated_probabilities[row["row_id"]] = calibrated
            confidence = max(calibrated, 1.0 - calibrated)
            policies["calibrated_model"][row["row_id"]] = "abstain" if confidence < 0.70 else "admit" if calibrated >= 0.5 else "reject"
            probability_rows.append({"row_id": row["row_id"], "raw_probability": probability, "calibrated_probability": calibrated, "decision": policies["calibrated_model"][row["row_id"]]})
    for row in complete:
        policies["calibrated_model"].setdefault(row["row_id"], "abstain"); raw_decisions.setdefault(row["row_id"], "abstain")
    baselines = {}
    for name, decisions in policies.items():
        value = _score(complete, decisions)
        lower, upper = _bounds(_bootstrap(complete, decisions, seed, bootstrap_samples))
        baselines[name] = value | {"bootstrap_ci_2_5": lower, "bootstrap_ci_97_5": upper}
    raw_table = _probability_table(complete, raw_decisions, raw_probabilities)
    calibrated_table = _probability_table(complete, policies["calibrated_model"], calibrated_probabilities)
    feasible = [name for name, value in baselines.items() if value["budget_met"]]
    insufficient = len(complete) < 50 or sum(_bad(row) for row in complete) < 10 or len(groups) < 8
    decision = "insufficient_data" if insufficient else "not_warranted" if not feasible else "warrant_future_training_story"
    sweep = []
    for threshold in (0.5, 0.6, 0.7, 0.8, 0.9):
        decisions = {row["row_id"]: "admit" if calibrated_probabilities.get(row["row_id"], 0) >= threshold else "reject" for row in complete}
        sweep.append({"threshold": threshold} | _score(complete, decisions))
    metrics = {"schema": "wangp-dspy.spend-gate-replay/v1", "seed": seed, "bootstrap_samples": bootstrap_samples,
               "false_admit_budget": false_admit_budget, "row_count": len(rows), "complete_row_count": len(complete),
               "bad_complete_rows": sum(_bad(row) for row in complete), "run_groups": groups,
               "grouped_folds": folds, "baselines": baselines,
               "raw_probability_policy": raw_table, "calibrated_probability_policy": calibrated_table,
               "preflight_feature_names": ["whisper_pre_passed", "guide_duration_s", "requested_frames", "width", "height", "prompt_chars", "prompt_words", "intercept"],
               "model_probability_rows": probability_rows, "recording_errors": recording_errors,
               "primary_metric": baselines["calibrated_model"]["failed_attempts_avoided_per_run"],
               "primary_result": "feasible" if feasible else "infeasible_at_budget", "decision": decision,
               "exploratory_threshold_sweep": sweep,
               "limits": ["N=36 total rows and 18 complete rows; this replay is underpowered.", "Calibration produced no feasible policy: this is a negative calibration result.", "Threshold sweeps are exploratory and did not select the primary result.",
                          "Queue joins are partial; unmatched attempt counts are explicitly unavailable."]}
    return ReplayReport(metrics, _markdown(metrics))


def _markdown(metrics: dict[str, Any]) -> str:
    lines = ["# Spend-gate replay (preregistered)", "",
             f"- Decision: **{metrics['decision']}**", f"- Primary result: **{metrics['primary_result']}**",
             f"- Rows: {metrics['row_count']} total / {metrics['complete_row_count']} complete / {metrics['bad_complete_rows']} bad",
             "- The complete-row sample is underpowered; no production model is warranted by this run.", "",
             "| Baseline | Admitted | Abstained | False admit | Avoided/run | Bootstrap 95% CI |", "|---|---:|---:|---:|---:|---:|"]
    for name, value in metrics["baselines"].items():
        false_admit = "undefined" if value["false_admit"] is None else f"{value['false_admit']:.3f}"
        avoided = "undefined" if value["failed_attempts_avoided_per_run"] is None else f"{value['failed_attempts_avoided_per_run']:.3f}"
        ci = "undefined" if value["bootstrap_ci_2_5"] is None else f"[{value['bootstrap_ci_2_5']:.3f}, {value['bootstrap_ci_97_5']:.3f}]"
        lines.append(f"| {name} | {value['admitted']} | {value['abstained']} | {false_admit} | {avoided} | {ci} |")
    lines += ["", "## Raw versus calibrated model", "", "| Policy | Coverage | Correct | Incorrect | Brier | Log loss |", "|---|---:|---:|---:|---:|---:|"]
    for name, value in (("raw", metrics["raw_probability_policy"]), ("calibrated", metrics["calibrated_probability_policy"])):
        brier = "undefined" if value["brier_score"] is None else f"{value['brier_score']:.3f}"
        loss = "undefined" if value["log_loss"] is None else f"{value['log_loss']:.3f}"
        lines.append(f"| {name} | {value['rows'] - value['abstained']}/{value['rows']} | {value['correct_decisions']} | {value['incorrect_decisions']} | {brier} | {loss} |")
    lines += ["", "## Explicit limits", "", *[f"- {limit}" for limit in metrics["limits"]],
              "", "## Exploratory sensitivity only", "", "The following sweep did not select or replace the primary metric."]
    return "\n".join(lines) + "\n"
