from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, roc_auc_score


def classification_metrics(y_true, y_pred, labels: list[int] | None = None) -> dict[str, Any]:
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "per_class": report,
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist() if labels else confusion_matrix(y_true, y_pred).tolist(),
    }


def binary_metrics(y_true, y_pred, y_score=None) -> dict[str, Any]:
    metrics = classification_metrics(y_true, y_pred, labels=[0, 1])
    if y_score is not None and len(set(y_true)) > 1:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
        metrics["reliability_summary"] = reliability_summary(y_true, y_score)
    else:
        metrics["roc_auc"] = None
        metrics["reliability_summary"] = []
    return metrics


def reliability_summary(y_true, y_score, bins: int = 5) -> list[dict[str, float]]:
    y_true_arr = np.asarray(y_true)
    y_score_arr = np.asarray(y_score)
    edges = np.linspace(0.0, 1.0, bins + 1)
    rows: list[dict[str, float]] = []
    for low, high in zip(edges[:-1], edges[1:]):
        mask = (y_score_arr >= low) & (y_score_arr < high if high < 1 else y_score_arr <= high)
        if not mask.any():
            continue
        rows.append(
            {
                "prob_low": float(low),
                "prob_high": float(high),
                "mean_predicted_probability": float(y_score_arr[mask].mean()),
                "observed_success_rate": float(y_true_arr[mask].mean()),
                "count": int(mask.sum()),
            }
        )
    return rows

