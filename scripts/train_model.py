"""
Full model training script.

Usage:
  python scripts/train_model.py

Steps:
  1. Load synthetic dataset (generate if missing)
  2. Preprocess with pipeline.py
  3. Train ensemble (stream + course + career)
  4. Evaluate on test split
  5. Save artifacts to app/ml/artifacts/

Artifacts saved:
  - preprocessing_pipeline.pkl
  - stream_clf.pkl
  - course_clf.pkl
  - career_clf.pkl
  - ensemble.pkl (full CareerRecommendationEnsemble)
  - metrics.json
"""
import json
import os
import sys
from pathlib import Path

# Make sure app/ is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from app.ml.ensemble import CareerRecommendationEnsemble
from app.ml.pipeline import build_preprocessing_pipeline


ARTIFACTS_DIR = Path("app/ml/artifacts")
DATA_PATH = Path("data/synthetic_students.csv")


def load_or_generate_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        print("[DATA] Dataset not found -- generating...")
        from scripts.generate_dataset import generate_dataset, main as gen_main
        gen_main()
    return pd.read_csv(DATA_PATH)


def main() -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load data ─────────────────────────────────────────────────────────────
    df = load_or_generate_data()
    print(f"Loaded {len(df)} student records.")

    y_stream = df["target_stream"].values
    y_course = df["target_course"].values
    y_career = df["target_career_cluster"].values

    # ── Preprocess ────────────────────────────────────────────────────────────
    pp = build_preprocessing_pipeline()
    X_raw = df.drop(columns=["target_stream", "target_course", "target_career_cluster"], errors="ignore")
    X = pp.fit_transform(X_raw)
    feature_names: list[str] = pp.named_steps["col_select"].feature_cols_  # type: ignore

    print(f"Preprocessed: {X.shape[1]} features, {X.shape[0]} samples.")

    # ── Train / test split ────────────────────────────────────────────────────
    (X_train, X_test,
     ys_train, ys_test,
     yc_train, yc_test,
     ycar_train, ycar_test) = train_test_split(
        X, y_stream, y_course, y_career,
        test_size=0.2, random_state=42, stratify=y_stream,
    )

    # ── Train ensemble ────────────────────────────────────────────────────────
    ensemble = CareerRecommendationEnsemble()
    ensemble.fit(
        X_train, ys_train,
        X_train, yc_train,
        X_train, ycar_train,
        feature_names=feature_names,
    )

    # ── Evaluate ──────────────────────────────────────────────────────────────
    metrics = {
        "stream": ensemble.stream_clf.evaluate(X_test, ys_test),
        "course": ensemble.course_clf.evaluate(X_test, yc_test),
        "career": ensemble.career_clf.evaluate(X_test, ycar_test),
    }

    for task, m in metrics.items():
        print(f"\n== {task.upper()} ==")
        print(f"  Accuracy : {m['accuracy']:.4f}")
        print(f"  F1 Macro : {m['f1_macro']:.4f}")

    # ── Top-K accuracy ────────────────────────────────────────────────────────
    def topk_acc(clf, X_test, y_test, k=3):
        preds = clf.predict_top_k(X_test, k=k)
        correct = sum(any(p["label"] == t for p in pred) for pred, t in zip(preds, y_test))
        return round(correct / len(y_test), 4)

    metrics["stream"]["top3_accuracy"] = topk_acc(ensemble.stream_clf, X_test, ys_test)
    metrics["course"]["top3_accuracy"] = topk_acc(ensemble.course_clf, X_test, yc_test)

    # ── Feature importance ────────────────────────────────────────────────────
    metrics["feature_importances"] = ensemble.stream_clf.get_feature_importances()

    # ── Save artifacts ────────────────────────────────────────────────────────
    joblib.dump(pp, ARTIFACTS_DIR / "preprocessing_pipeline.pkl")
    joblib.dump(ensemble, ARTIFACTS_DIR / "ensemble.pkl")

    with open(ARTIFACTS_DIR / "metrics.json", "w") as f:
        # Remove non-serializable report dicts for top-level metrics file
        clean = {k: {kk: vv for kk, vv in v.items() if kk != "report"} for k, v in metrics.items() if isinstance(v, dict)}
        json.dump(clean, f, indent=2)

    print(f"\nArtifacts saved to {ARTIFACTS_DIR}/")
    print("   preprocessing_pipeline.pkl")
    print("   ensemble.pkl")
    print("   metrics.json")


if __name__ == "__main__":
    main()
