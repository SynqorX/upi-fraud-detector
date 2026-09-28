"""
Test suite for SentinelUPI engine and components.
"""
import unittest
import os
import pandas as pd
from datetime import datetime, timedelta
from engine import (
    UserProfile, ProfileManager, FeatureExtractor,
    FraudModel, ExplainabilityEngine, generate_synthetic_upi_dataset,
    haversine_distance, FEATURE_COLUMNS
)

class TestSentinelUPI(unittest.TestCase):
    def setUp(self):
        self.profile = UserProfile(
            user_id="USR_TEST_01",
            initial_mean=1000.0,
            initial_std=200.0,
            primary_device="DEV_TEST_PHONE",
            primary_city="Mumbai",
            alpha=0.10
        )

    def test_ewma_baseline_update(self):
        initial_mean = self.profile.ewma_mean
        # Normal update with small amount
        self.profile.update_baseline(1200.0, is_feedback_legitimate=False)
        self.assertGreater(self.profile.ewma_mean, initial_mean)

        # Benign feedback adaptation
        pre_adapt_mean = self.profile.ewma_mean
        self.profile.update_baseline(
            5000.0,
            is_feedback_legitimate=True,
            new_device_id="DEV_NEW_LAPTOP",
            new_device_model="MacBook Air M2",
            new_city="Delhi"
        )
        self.assertGreater(self.profile.ewma_mean, pre_adapt_mean)
        self.assertIn("DEV_NEW_LAPTOP", self.profile.trusted_devices)
        self.assertIn("Delhi", self.profile.trusted_cities)

    def test_feature_extractor(self):
        txn = {
            "amount": 2500.0,
            "device_id": "DEV_TEST_PHONE",
            "device_model": "Test Phone",
            "location_city": "Mumbai",
            "timestamp": "2026-09-28 14:00:00",
            "txn_velocity_1h": 1
        }
        feats = FeatureExtractor.extract_features(self.profile, txn)
        self.assertEqual(feats["is_known_device"], 1)
        self.assertEqual(feats["is_known_city"], 1)
        self.assertEqual(feats["is_nocturnal"], 0)
        self.assertAlmostEqual(feats["amount"], 2500.0)
        self.assertIn("z_score_amount", feats)
        self.assertIn("velocity_kmh", feats)

    def test_haversine(self):
        # Mumbai to Pune (~120 km)
        dist = haversine_distance(19.0760, 72.8777, 18.5204, 73.8567)
        self.assertGreater(dist, 100.0)
        self.assertLess(dist, 160.0)

    def test_synthetic_data_generation(self):
        df = generate_synthetic_upi_dataset(num_rows=200, random_seed=42)
        self.assertEqual(len(df), 200)
        for col in FEATURE_COLUMNS:
            self.assertIn(col, df.columns)
        self.assertIn("is_fraud", df.columns)
        self.assertIn("scenario_type", df.columns)

    def test_explainability_generation(self):
        txn = {
            "amount": 50000.0,
            "device_id": "DEV_UNKNOWN",
            "device_model": "Rooted Android",
            "location_city": "Moscow",
            "timestamp": "2026-09-28 03:00:00",
            "merchant_category": "P2P_Transfer",
            "txn_velocity_1h": 6
        }
        feats = FeatureExtractor.extract_features(self.profile, txn)
        explanation = ExplainabilityEngine.generate_explanation(
            self.profile, txn, feats, risk_score=95.0, risk_tier="CRITICAL"
        )
        self.assertEqual(explanation["risk_tier"], "CRITICAL")
        self.assertEqual(explanation["anomaly_diagnosis"], "HOSTILE_ACCOUNT_TAKEOVER")
        self.assertTrue(len(explanation["factors"]) > 0)
        self.assertIn("summary_narrative", explanation)

if __name__ == "__main__":
    unittest.main()
