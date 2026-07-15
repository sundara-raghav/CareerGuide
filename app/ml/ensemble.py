"""
Ensemble recommendation model.

Architecture:
  Base learners:  RandomForest  +  XGBoost  +  LogisticRegression
  Ensemble:       Stacking with LogisticRegression meta-learner
  Post-process:   Calibration (Platt) for confidence, rule-based hard constraints

Three tasks:
  1. stream_clf  — predicts stream (Science/Commerce/Arts/Vocational)
  2. course_clf  — predicts top course category
  3. career_clf  — predicts career cluster
"""

from __future__ import annotations

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_score, recall_score
from sklearn.preprocessing import LabelEncoder

try:
    from xgboost import XGBClassifier

    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False


def _make_base_estimators(n_classes: int) -> list:
    estimators = [
        (
            "rf",
            RandomForestClassifier(
                n_estimators=200,
                max_depth=12,
                min_samples_split=5,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ),
        ),
        (
            "lr",
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                random_state=42,
                C=1.0,
            ),
        ),
    ]
    if XGB_AVAILABLE:
        estimators.append(
            (
                "xgb",
                XGBClassifier(
                    n_estimators=150,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    use_label_encoder=False,
                    eval_metric="mlogloss",
                    random_state=42,
                ),
            )
        )
    return estimators


class EnsembleClassifier:
    """
    Stacking ensemble with calibrated confidence.
    Wraps sklearn's StackingClassifier and adds:
      - LabelEncoder for string targets
      - Calibrated probability output
      - Top-K prediction with confidence
    """

    def __init__(self, task_name: str) -> None:
        self.task_name = task_name
        self.label_encoder = LabelEncoder()
        self._clf: StackingClassifier | None = None
        self._calibrated: CalibratedClassifierCV | None = None
        self.classes_: list[str] = []
        self.feature_names_: list[str] = []
        self.is_fitted = False

    def fit(self, X: np.ndarray, y_raw: np.ndarray, feature_names: list[str] | None = None) -> EnsembleClassifier:
        y = self.label_encoder.fit_transform(y_raw)
        self.classes_ = list(self.label_encoder.classes_)
        n_classes = len(self.classes_)
        self.feature_names_ = feature_names or [f"f{i}" for i in range(X.shape[1])]

        base = _make_base_estimators(n_classes)
        meta = LogisticRegression(max_iter=500, random_state=42)

        self._clf = StackingClassifier(
            estimators=base,
            final_estimator=meta,
            cv=5,
            stack_method="predict_proba",
            passthrough=False,
            n_jobs=-1,
        )
        self._clf.fit(X, y)

        # Calibrate on the same data (in production: use held-out calibration set)
        try:
            from sklearn.frozen import FrozenEstimator

            self._calibrated = CalibratedClassifierCV(estimator=FrozenEstimator(self._clf), cv=None, method="sigmoid")
        except ImportError:
            try:
                self._calibrated = CalibratedClassifierCV(estimator=self._clf, cv="prefit", method="sigmoid")
            except TypeError:
                self._calibrated = CalibratedClassifierCV(base_estimator=self._clf, cv="prefit", method="sigmoid")
        self._calibrated.fit(X, y)

        self.is_fitted = True
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self._calibrated.predict_proba(X)

    def predict_top_k(self, X: np.ndarray, k: int = 5) -> list[list[dict]]:
        """Returns top-k predictions with confidence for each sample."""
        proba = self.predict_proba(X)
        results = []
        for sample_proba in proba:
            top_idx = np.argsort(sample_proba)[::-1][:k]
            top = [
                {"rank": i + 1, "label": self.classes_[idx], "confidence": round(float(sample_proba[idx]), 4)}
                for i, idx in enumerate(top_idx)
            ]
            results.append(top)
        return results

    def evaluate(self, X: np.ndarray, y_raw: np.ndarray) -> dict:
        y_true = self.label_encoder.transform(y_raw)
        y_pred = self._calibrated.predict(X)
        return {
            "task": self.task_name,
            "accuracy": round(accuracy_score(y_true, y_pred), 4),
            "f1_macro": round(f1_score(y_true, y_pred, average="macro", zero_division=0), 4),
            "precision_macro": round(precision_score(y_true, y_pred, average="macro", zero_division=0), 4),
            "recall_macro": round(recall_score(y_true, y_pred, average="macro", zero_division=0), 4),
            "report": classification_report(y_true, y_pred, target_names=self.classes_, output_dict=True),
        }

    def get_feature_importances(self) -> dict[str, float]:
        """Extract feature importances from the RandomForest base learner."""
        rf = dict(self._clf.named_estimators_).get("rf")
        if rf and hasattr(rf, "feature_importances_"):
            return dict(zip(self.feature_names_, rf.feature_importances_.tolist()))
        return {}


class CareerRecommendationEnsemble:
    """
    Top-level wrapper that runs all three classifiers and applies rule-based constraints.
    """

    def __init__(self) -> None:
        self.stream_clf = EnsembleClassifier("stream")
        self.course_clf = EnsembleClassifier("course")
        self.career_clf = EnsembleClassifier("career_cluster")

    def fit(
        self,
        X_stream: np.ndarray,
        y_stream: np.ndarray,
        X_course: np.ndarray,
        y_course: np.ndarray,
        X_career: np.ndarray,
        y_career: np.ndarray,
        feature_names: list[str] | None = None,
    ) -> CareerRecommendationEnsemble:
        print("[TRAIN] Training stream classifier...")
        self.stream_clf.fit(X_stream, y_stream, feature_names)
        print("[TRAIN] Training course classifier...")
        self.course_clf.fit(X_course, y_course, feature_names)
        print("[TRAIN] Training career cluster classifier...")
        self.career_clf.fit(X_career, y_career, feature_names)
        print("[TRAIN] All classifiers trained.")
        return self

    def predict(self, X: np.ndarray, student_context: dict | None = None) -> dict:
        """
        Full inference for one student.
        student_context: optional dict with budget, travel_radius, needs_hostel, etc.
        for rule-based post-processing.
        """
        streams = self.stream_clf.predict_top_k(X, k=4)
        courses = self.course_clf.predict_top_k(X, k=5)
        careers = self.career_clf.predict_top_k(X, k=5)

        stream_top = streams[0]
        course_top = courses[0]
        career_top = careers[0]

        # Rule-based hard constraint: if budget < 50000, boost Vocational/Diploma
        budget = student_context.get("budget_for_education") if student_context else None
        if budget is not None and budget < 50000:
            for item in course_top:
                if "Diploma" in item["label"] or "ITI" in item["label"] or "Polytechnic" in item["label"]:
                    item["confidence"] = min(1.0, item["confidence"] * 1.3)
                    item["rule_flag"] = "budget_boost"
            course_top.sort(key=lambda x: x["confidence"], reverse=True)
            for i, item in enumerate(course_top):
                item["rank"] = i + 1

        return {
            "stream": stream_top,
            "courses": course_top,
            "careers": career_top,
        }
