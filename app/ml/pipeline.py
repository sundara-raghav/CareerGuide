"""
Feature preprocessing pipeline for the recommendation engine.

Handles:
- Mark-based feature engineering (tier, aggregate)
- Aptitude composite score
- Categorical encoding (board, school_type, caste)
- Income normalization
- Interest multi-hot encoding
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

APTITUDE_COLS = [
    "apt_logical",
    "apt_verbal",
    "apt_quantitative",
    "apt_social",
    "apt_creative",
    "apt_technical",
]

MARK_COLS_10 = ["mark_math", "mark_science", "mark_social", "mark_english", "mark_regional_language"]
MARK_COLS_12 = ["mark_english", "mark_core_subject_1", "mark_core_subject_2", "mark_elective_1", "mark_elective_2"]

INTEREST_COLS = [
    "interest_mathematics",
    "interest_biology",
    "interest_computers",
    "interest_sports",
    "interest_arts",
    "interest_music",
    "interest_social_service",
    "interest_business",
    "interest_nature",
    "interest_writing",
    "interest_politics",
    "interest_cooking",
    "interest_electronics",
    "interest_farming",
    "interest_healthcare",
    "interest_teaching",
]

CATEGORICAL_COLS = ["board", "school_type", "caste_category", "gender"]


class MarkFeatureEngineer(BaseEstimator, TransformerMixin):
    """Compute aggregate, marks tier (1–5), and per-subject z-score bucket."""

    def fit(self, X: pd.DataFrame, y=None):
        seen = set()
        mark_cols = []
        for c in MARK_COLS_10 + MARK_COLS_12:
            if c in X.columns and c not in seen:
                mark_cols.append(c)
                seen.add(c)
        self.mark_cols_ = mark_cols
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        mark_cols = [c for c in self.mark_cols_ if c in X.columns]
        if mark_cols:
            X["_aggregate"] = X[mark_cols].mean(axis=1)
            X["_marks_tier"] = pd.cut(
                X["_aggregate"],
                bins=[0, 40, 55, 70, 85, 100],
                labels=[1, 2, 3, 4, 5],
                right=True,
            ).astype(float)
        return X


class AptitudeEngineer(BaseEstimator, TransformerMixin):
    """Compute composite aptitude score and domain dominance flag."""

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        apt_present = [c for c in APTITUDE_COLS if c in X.columns]
        if apt_present:
            X["_apt_composite"] = X[apt_present].mean(axis=1)
            X["_apt_stem"] = (
                X[["apt_logical", "apt_quantitative", "apt_technical"]].mean(axis=1)
                if all(c in X.columns for c in ["apt_logical", "apt_quantitative", "apt_technical"])
                else 0
            )
            X["_apt_humanities"] = (
                X[["apt_verbal", "apt_social", "apt_creative"]].mean(axis=1)
                if all(c in X.columns for c in ["apt_verbal", "apt_social", "apt_creative"])
                else 0
            )
            X["_apt_domain_flag"] = (X["_apt_stem"] > X["_apt_humanities"]).astype(int)
        return X


class CategoricalEncoder(BaseEstimator, TransformerMixin):
    """Label-encode categorical columns."""

    def __init__(self, cols: list[str] | None = None):
        self.cols = cols or CATEGORICAL_COLS

    def fit(self, X: pd.DataFrame, y=None):
        self.encoders_: dict[str, LabelEncoder] = {}
        for col in self.cols:
            if col in X.columns:
                le = LabelEncoder()
                le.fit(X[col].fillna("Unknown").astype(str))
                self.encoders_[col] = le
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col, le in self.encoders_.items():
            if col in X.columns:
                vals = X[col].fillna("Unknown").astype(str)
                # Handle unseen labels
                known = set(le.classes_)
                vals = vals.apply(lambda v: v if v in known else le.classes_[0])
                X[col] = le.transform(vals)
        return X


class IncomeNormalizer(BaseEstimator, TransformerMixin):
    """Log-transform + scale income and budget features."""

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for col in ["annual_family_income", "budget_for_education"]:
            if col in X.columns:
                X[col] = np.log1p(X[col].fillna(0))
        return X


class ColumnSelector(BaseEstimator, TransformerMixin):
    """Select only ML-relevant columns and drop IDs / label columns."""

    DROP_COLS = ["student_id", "target_stream", "target_course", "target_career_cluster", "district"]

    def fit(self, X: pd.DataFrame, y=None):
        self.feature_cols_ = [c for c in X.columns if c not in self.DROP_COLS]
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        return X[[c for c in self.feature_cols_ if c in X.columns]].fillna(0)


def build_preprocessing_pipeline() -> Pipeline:
    """Returns a sklearn Pipeline that transforms raw student DataFrames."""
    return Pipeline(
        [
            ("mark_eng", MarkFeatureEngineer()),
            ("apt_eng", AptitudeEngineer()),
            ("income_norm", IncomeNormalizer()),
            ("cat_enc", CategoricalEncoder()),
            ("col_select", ColumnSelector()),
            ("scaler", StandardScaler()),
        ]
    )
