"""Unit tests for the ML pipeline and inference service."""
import numpy as np
import pandas as pd
import pytest

from app.ml.pipeline import (
    AptitudeEngineer,
    CategoricalEncoder,
    IncomeNormalizer,
    MarkFeatureEngineer,
    build_preprocessing_pipeline,
)


class TestMarkFeatureEngineer:
    def test_aggregate_computed(self):
        df = pd.DataFrame([{
            "mark_math": 80.0, "mark_science": 70.0, "mark_social": 60.0,
            "mark_english": 75.0, "mark_regional_language": 65.0,
        }])
        eng = MarkFeatureEngineer().fit(df)
        result = eng.transform(df)
        assert "_aggregate" in result.columns
        assert abs(result["_aggregate"].iloc[0] - 70.0) < 0.01

    def test_marks_tier_range(self):
        df = pd.DataFrame([{"mark_math": 90.0, "mark_english": 95.0}])
        eng = MarkFeatureEngineer().fit(df)
        result = eng.transform(df)
        assert "_marks_tier" in result.columns
        assert result["_marks_tier"].iloc[0] == 5.0


class TestAptitudeEngineer:
    def test_composite_score(self):
        df = pd.DataFrame([{
            "apt_logical": 80, "apt_verbal": 70, "apt_quantitative": 90,
            "apt_social": 60, "apt_creative": 75, "apt_technical": 85,
        }])
        eng = AptitudeEngineer().fit(df)
        result = eng.transform(df)
        expected = np.mean([80, 70, 90, 60, 75, 85])
        assert abs(result["_apt_composite"].iloc[0] - expected) < 0.01

    def test_stem_vs_humanities(self):
        df = pd.DataFrame([{
            "apt_logical": 90, "apt_verbal": 40, "apt_quantitative": 85,
            "apt_social": 40, "apt_creative": 45, "apt_technical": 90,
        }])
        eng = AptitudeEngineer().fit(df)
        result = eng.transform(df)
        assert result["_apt_domain_flag"].iloc[0] == 1  # STEM dominant


class TestCategoricalEncoder:
    def test_encodes_board(self):
        df = pd.DataFrame([{"board": "CBSE"}, {"board": "State Board"}])
        enc = CategoricalEncoder(cols=["board"]).fit(df)
        result = enc.transform(df)
        assert result["board"].dtype in [int, np.int64, np.int32]

    def test_handles_unseen_labels(self):
        train = pd.DataFrame([{"board": "CBSE"}, {"board": "ICSE"}])
        test = pd.DataFrame([{"board": "Unknown New Board"}])
        enc = CategoricalEncoder(cols=["board"]).fit(train)
        result = enc.transform(test)  # Should not raise
        assert len(result) == 1


class TestIncomNormalizer:
    def test_log_transform(self):
        df = pd.DataFrame([{"annual_family_income": 200000}])
        norm = IncomeNormalizer().fit(df)
        result = norm.transform(df)
        expected = np.log1p(200000)
        assert abs(result["annual_family_income"].iloc[0] - expected) < 0.01


class TestPreprocessingPipeline:
    def test_pipeline_runs_end_to_end(self):
        from scripts.generate_dataset import generate_dataset
        df = generate_dataset(50)
        pipeline = build_preprocessing_pipeline()
        X_raw = df.drop(columns=["target_stream", "target_course", "target_career_cluster"], errors="ignore")
        X = pipeline.fit_transform(X_raw)
        assert X.shape[0] == 50
        assert X.shape[1] > 10
        # No NaN values in output
        assert not np.isnan(X).any()
