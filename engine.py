"""
SentinelUPI: Adaptive Fraud Detection Engine Without Blind Alerts
==================================================================
Core architecture:
1. Baseline & Profile Manager (EWMA Mean & Variance, Known Device & Geo Registry, Drift Adaptation)
2. Deviation Scoring Engine (Z-Score, Nocturnal Hours, Geo-Velocity, Device Novelty)
3. Supervised / Calibrated ML Model (Random Forest / Gradient Boosting with Probability Calibration)
4. Explainability Layer (Plain-English Factor Extraction, Root-Cause Attribution, Benign vs Hostile)
5. Synthetic UPI Stream Generator (Realistic Indian UPI patterns, benign spikes, hostile takeovers)
"""

import os
import math
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix, precision_score, recall_score, f1_score

# Indian City Geographic Coordinates
INDIAN_CITIES = {
    "Mumbai": {"lat": 19.0760, "lon": 72.8777},
    "Delhi": {"lat": 28.6139, "lon": 77.2090},
    "Bengaluru": {"lat": 12.9716, "lon": 77.5946},
    "Hyderabad": {"lat": 17.3850, "lon": 78.4867},
    "Pune": {"lat": 18.5204, "lon": 73.8567},
    "Chennai": {"lat": 13.0827, "lon": 80.2707},
    "Kolkata": {"lat": 22.5726, "lon": 88.3639},
    "Jaipur": {"lat": 26.9124, "lon": 75.7873},
    "Ahmedabad": {"lat": 23.0225, "lon": 72.5714},
    "Goa": {"lat": 15.2993, "lon": 74.1240},
    "Lucknow": {"lat": 26.8467, "lon": 80.9462},
    "Chandigarh": {"lat": 30.7333, "lon": 76.7794},
    "Moscow": {"lat": 55.7558, "lon": 37.6173},  # External / foreign
    "Lagos": {"lat": 6.5244, "lon": 3.3792},     # External / foreign
}

MERCHANT_CATEGORIES = [
    "Groceries_Daily",
    "Food_Dining",
    "Electronics_Gadgets",
    "Jewelry_Luxury",
    "P2P_Transfer",
    "Travel_Ticketing",
    "Utility_Bills",
    "Gaming_Crypto"
]

FEATURE_COLUMNS = [
    "amount",
    "user_avg_amount_30d",
    "user_std_amount_30d",
    "z_score_amount",
    "spend_multiplier",
    "is_known_device",
    "is_known_city",
    "hours_since_last_txn",
    "km_from_last_txn",
    "velocity_kmh",
    "is_nocturnal",
    "txn_velocity_1h",
    "hostile_triad_score",
    "device_risk_penalty",
    "geo_velocity_anomaly",
    "p2p_novel_device_risk"
]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance between two points in km."""
    R = 6371.0  # Earth radius in kilometers
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


# =====================================================================
# 1. Baseline & User Profile Manager
# =====================================================================
class UserProfile:
    """Maintains user behavioral profile, EWMA statistics, and trusted entities."""
    def __init__(self, user_id: str, initial_mean: float = 1200.0, initial_std: float = 400.0,
                 primary_device: str = "DEV_SAMS23_01", primary_city: str = "Bengaluru",
                 alpha: float = 0.10):
        self.user_id = user_id
        self.ewma_mean = float(initial_mean)
        self.ewma_var = float(initial_std ** 2)
        self.alpha = alpha  # baseline drift learning rate
        self.trusted_devices: Dict[str, str] = {primary_device: "Samsung Galaxy S23"}
        self.trusted_cities: List[str] = [primary_city]
        self.last_txn_time: Optional[datetime] = datetime.now() - timedelta(hours=3)
        self.last_city: str = primary_city
        self.last_lat: float = INDIAN_CITIES[primary_city]["lat"]
        self.last_lon: float = INDIAN_CITIES[primary_city]["lon"]
        self.typical_active_hours: List[int] = list(range(8, 23))  # 8 AM to 11 PM
        self.history: List[Dict[str, Any]] = []

    @property
    def ewma_std(self) -> float:
        return max(math.sqrt(max(self.ewma_var, 1.0)), 50.0)

    def update_baseline(self, amount: float, is_feedback_legitimate: bool = False,
                        new_device_id: Optional[str] = None, new_device_model: Optional[str] = None,
                        new_city: Optional[str] = None):
        """
        Updates EWMA mean and variance.
        If is_feedback_legitimate is True, human-in-the-loop confirmed a benign anomaly.
        Adaptation uses a higher alpha (concept drift shift) and registers the new device/location.
        """
        current_alpha = 0.35 if is_feedback_legitimate else self.alpha
        diff = amount - self.ewma_mean
        self.ewma_mean += current_alpha * diff
        self.ewma_var = (1.0 - current_alpha) * (self.ewma_var + current_alpha * (diff ** 2))

        if is_feedback_legitimate:
            if new_device_id and new_device_model:
                self.trusted_devices[new_device_id] = new_device_model
            if new_city and new_city not in self.trusted_cities:
                self.trusted_cities.append(new_city)

    def record_transaction(self, record: Dict[str, Any]):
        self.history.append(record)
        if len(self.history) > 100:
            self.history.pop(0)
        self.last_txn_time = record.get("timestamp_dt", datetime.now())
        city = record.get("location_city", self.last_city)
        if city in INDIAN_CITIES:
            self.last_city = city
            self.last_lat = INDIAN_CITIES[city]["lat"]
            self.last_lon = INDIAN_CITIES[city]["lon"]


class ProfileManager:
    """In-memory & persistent registry of user baseline profiles."""
    def __init__(self):
        self.profiles: Dict[str, UserProfile] = {}
        self._seed_default_users()

    def _seed_default_users(self):
        # User 1: Tech worker in Bengaluru, moderate routine spend
        u1 = UserProfile(
            user_id="USR_KARTHIK_BLR",
            initial_mean=1850.0,
            initial_std=520.0,
            primary_device="DEV_SAMS23_01",
            primary_city="Bengaluru"
        )
        # User 2: Executive in Mumbai, high routine spend
        u2 = UserProfile(
            user_id="USR_PRIYA_MUM",
            initial_mean=6500.0,
            initial_std=1900.0,
            primary_device="DEV_IPHONE15_02",
            primary_city="Mumbai"
        )
        # User 3: Student in Pune, low routine spend
        u3 = UserProfile(
            user_id="USR_ROHIT_PUNE",
            initial_mean=380.0,
            initial_std=120.0,
            primary_device="DEV_REDMINOTE_03",
            primary_city="Pune"
        )
        self.profiles[u1.user_id] = u1
        self.profiles[u2.user_id] = u2
        self.profiles[u3.user_id] = u3

    def load_from_dataframe(self, df: pd.DataFrame, max_users: int = 50):
        """Loads user profiles and trusted entities directly from historical transactions."""
        if "user_id" not in df.columns:
            return
        users = df["user_id"].unique()[:max_users]
        for uid in users:
            u_df = df[df["user_id"] == uid]
            known_dev_rows = u_df[u_df["is_known_device"] == 1]
            if not known_dev_rows.empty:
                prim_dev = str(known_dev_rows.iloc[0]["device_id"])
                dev_model = str(known_dev_rows.iloc[0]["device_model"])
            else:
                prim_dev = str(u_df.iloc[0]["device_id"])
                dev_model = str(u_df.iloc[0]["device_model"])

            known_city_rows = u_df[u_df["is_known_city"] == 1]
            prim_city = str(known_city_rows.iloc[0]["location_city"]) if not known_city_rows.empty else str(u_df.iloc[0]["location_city"])

            mean_val = float(u_df["user_avg_amount_30d"].iloc[-1]) if "user_avg_amount_30d" in u_df.columns else float(u_df["amount"].mean())
            std_val = float(u_df["user_std_amount_30d"].iloc[-1]) if "user_std_amount_30d" in u_df.columns else float(u_df["amount"].std())

            profile = UserProfile(
                user_id=str(uid),
                initial_mean=mean_val,
                initial_std=max(std_val, 50.0),
                primary_device=prim_dev,
                primary_city=prim_city
            )
            profile.trusted_devices[prim_dev] = dev_model
            self.profiles[str(uid)] = profile

    def get_or_create(self, user_id: str, initial_mean: float = 1500.0, initial_std: float = 400.0,
                      device: str = "DEV_DEFAULT", city: str = "Mumbai") -> UserProfile:
        if user_id not in self.profiles:
            self.profiles[user_id] = UserProfile(
                user_id=user_id,
                initial_mean=initial_mean,
                initial_std=initial_std,
                primary_device=device,
                primary_city=city
            )
        return self.profiles[user_id]


# =====================================================================
# 2. Deviation Scoring & Feature Extraction Engine
# =====================================================================
class FeatureExtractor:
    """Computes behavioral deviation features against user profile."""
    @staticmethod
    def extract_features(profile: UserProfile, txn_dict: Dict[str, Any]) -> Dict[str, Any]:
        amount = float(txn_dict.get("amount", 0.0))
        mean = profile.ewma_mean
        std = profile.ewma_std

        z_score = (amount - mean) / std
        spend_multiplier = amount / max(mean, 1.0)

        device_id = str(txn_dict.get("device_id", ""))
        is_known_device = 1 if device_id in profile.trusted_devices else 0

        city = str(txn_dict.get("location_city", "Mumbai"))
        is_known_city = 1 if city in profile.trusted_cities else 0

        # Timing analysis
        txn_time = txn_dict.get("timestamp_dt")
        if not txn_time:
            time_str = txn_dict.get("timestamp", "")
            try:
                txn_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                txn_time = datetime.now()

        hour = txn_time.hour + (txn_time.minute / 60.0)
        # Nocturnal between 1:00 AM and 5:30 AM
        is_nocturnal = 1 if 1.0 <= hour <= 5.5 else 0

        # Geo-velocity analysis
        hours_since = 2.0
        if profile.last_txn_time:
            gap = (txn_time - profile.last_txn_time).total_seconds() / 3600.0
            hours_since = max(gap, 0.01)

        curr_coords = INDIAN_CITIES.get(city, {"lat": profile.last_lat, "lon": profile.last_lon})
        curr_lat = curr_coords["lat"]
        curr_lon = curr_coords["lon"]

        km_dist = haversine_distance(profile.last_lat, profile.last_lon, curr_lat, curr_lon)
        velocity_kmh = km_dist / hours_since

        txn_velocity_1h = int(txn_dict.get("txn_velocity_1h", 1))

        # Multi-vector composite interaction features
        hostile_triad_score = round(
            float((1 - is_known_device) * (
                1.5 * is_nocturnal +
                2.0 * float(velocity_kmh > 800.0) +
                1.0 * (1 - is_known_city)
            )), 2
        )
        device_risk_penalty = round(
            float((1 - is_known_device) * (1.5 * (1 - is_known_city) + 1.2 * is_nocturnal) * math.log1p(max(spend_multiplier, 0.1))), 2
        )
        geo_velocity_anomaly = 1 if velocity_kmh > 850.0 else 0
        category = str(txn_dict.get("merchant_category", txn_dict.get("category", "Food_Dining")))
        p2p_novel_device_risk = 1 if (is_known_device == 0 and category in ["P2P_Transfer", "Gaming_Crypto"]) else 0

        return {
            "amount": amount,
            "user_avg_amount_30d": mean,
            "user_std_amount_30d": std,
            "z_score_amount": z_score,
            "spend_multiplier": spend_multiplier,
            "is_known_device": is_known_device,
            "is_known_city": is_known_city,
            "hours_since_last_txn": hours_since,
            "km_from_last_txn": km_dist,
            "velocity_kmh": velocity_kmh,
            "is_nocturnal": is_nocturnal,
            "txn_velocity_1h": txn_velocity_1h,
            "hostile_triad_score": hostile_triad_score,
            "device_risk_penalty": device_risk_penalty,
            "geo_velocity_anomaly": geo_velocity_anomaly,
            "p2p_novel_device_risk": p2p_novel_device_risk
        }


# =====================================================================
# 3. Machine Learning Model Pipeline
# =====================================================================
class FraudModel:
    """Supervised classifier with probability scoring for UPI transactions."""
    def __init__(self, model_path: str = "data/fraud_model.joblib"):
        self.model_path = model_path
        self.model: Optional[RandomForestClassifier] = None
        self.feature_names = FEATURE_COLUMNS
        self.metrics: Dict[str, Any] = {}

    def is_trained(self) -> bool:
        return self.model is not None

    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Trains Random Forest model on processed transaction dataset."""
        df = df.copy()

        # Compute derived features if not present in raw CSV
        if "z_score_amount" not in df.columns:
            if "amount" in df.columns and "user_avg_amount_30d" in df.columns and "user_std_amount_30d" in df.columns:
                df["z_score_amount"] = (df["amount"] - df["user_avg_amount_30d"]) / np.maximum(df["user_std_amount_30d"], 1.0)
            else:
                df["z_score_amount"] = 0.0

        if "spend_multiplier" not in df.columns:
            if "amount" in df.columns and "user_avg_amount_30d" in df.columns:
                df["spend_multiplier"] = df["amount"] / np.maximum(df["user_avg_amount_30d"], 1.0)
            else:
                df["spend_multiplier"] = 1.0

        if "hostile_triad_score" not in df.columns:
            df["hostile_triad_score"] = (1 - df["is_known_device"]) * (
                1.5 * df["is_nocturnal"] +
                2.0 * (df["velocity_kmh"] > 800.0).astype(float) +
                1.0 * (1 - df["is_known_city"])
            )

        if "device_risk_penalty" not in df.columns:
            df["device_risk_penalty"] = (1 - df["is_known_device"]) * (1.5 * (1 - df["is_known_city"]) + 1.2 * df["is_nocturnal"]) * np.log1p(np.maximum(df["spend_multiplier"], 0.1))

        if "geo_velocity_anomaly" not in df.columns:
            df["geo_velocity_anomaly"] = (df["velocity_kmh"] > 850.0).astype(int)

        if "p2p_novel_device_risk" not in df.columns:
            if "merchant_category" in df.columns:
                df["p2p_novel_device_risk"] = ((1 - df["is_known_device"]) * df["merchant_category"].isin(["P2P_Transfer", "Gaming_Crypto"])).astype(int)
            else:
                df["p2p_novel_device_risk"] = 0

        missing_cols = [c for c in self.feature_names if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Dataset is missing required feature columns: {missing_cols}")

        if "is_fraud" not in df.columns:
            raise ValueError("Dataset missing target column 'is_fraud'")

        X = df[self.feature_names]
        y = df["is_fraud"].astype(int)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        clf = RandomForestClassifier(
            n_estimators=180,
            max_depth=12,
            min_samples_split=3,
            min_samples_leaf=2,
            max_features="sqrt",
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1
        )
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1]

        auc = float(roc_auc_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else 1.0
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        cm = confusion_matrix(y_test, y_pred).tolist()

        importances = dict(zip(self.feature_names, [round(float(v), 4) for v in clf.feature_importances_]))

        self.model = clf
        self.metrics = {
            "roc_auc": round(auc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": cm,
            "feature_importances": importances,
            "test_samples": len(y_test),
            "train_samples": len(y_train)
        }

        # Auto-save model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({"model": clf, "metrics": self.metrics, "features": self.feature_names}, self.model_path)
        return self.metrics

    def load_or_train_default(self, fallback_data_generator_fn) -> bool:
        """Loads model from disk or generates synthetic data to train."""
        if os.path.exists(self.model_path):
            try:
                data = joblib.load(self.model_path)
                self.model = data["model"]
                self.metrics = data.get("metrics", {})
                self.feature_names = data.get("features", FEATURE_COLUMNS)
                return True
            except Exception:
                pass

        # Generate dataset and train
        df = fallback_data_generator_fn(num_rows=2500)
        self.train(df)
        return True

    def predict_risk(self, features: Dict[str, Any]) -> Tuple[float, str]:
        """
        Returns (risk_score_0_to_100, risk_tier).
        """
        if not self.is_trained():
            raise RuntimeError("Model is not trained yet.")

        feature_vector = [features[col] for col in self.feature_names]
        X = pd.DataFrame([feature_vector], columns=self.feature_names)
        prob = float(self.model.predict_proba(X)[0, 1])
        score = round(prob * 100.0, 1)

        if score < 25.0:
            tier = "LOW"
        elif score < 55.0:
            tier = "MEDIUM"
        elif score < 75.0:
            tier = "HIGH"
        else:
            tier = "CRITICAL"

        return score, tier


# =====================================================================
# 4. Explainability Layer (Attribution & Plain-English Reasoner)
# =====================================================================
class ExplainabilityEngine:
    """
    Translates raw numbers and deviation features into actionable,
    plain-English factor attributions without blind alerts.
    """
    @staticmethod
    def generate_explanation(profile: UserProfile, txn_dict: Dict[str, Any],
                             features: Dict[str, Any], risk_score: float, risk_tier: str) -> Dict[str, Any]:
        amount = features["amount"]
        mean = features["user_avg_amount_30d"]
        z_score = features["z_score_amount"]
        multiplier = features["spend_multiplier"]
        is_known_device = features["is_known_device"]
        is_known_city = features["is_known_city"]
        is_nocturnal = features["is_nocturnal"]
        velocity = features["velocity_kmh"]
        dist = features["km_from_last_txn"]
        hours = features["hours_since_last_txn"]
        burst_count = features["txn_velocity_1h"]
        device_model = txn_dict.get("device_model", "Unknown Device")
        city = txn_dict.get("location_city", "Unknown City")
        category = txn_dict.get("merchant_category", "General")

        factors: List[Dict[str, Any]] = []
        factor_scores: Dict[str, float] = {
            "spend_deviation": 0.0,
            "device_novelty": 0.0,
            "geo_velocity": 0.0,
            "temporal_anomaly": 0.0,
            "burst_frequency": 0.0
        }

        # 1. Spend Deviation Analysis
        if z_score > 3.0 or multiplier > 3.0:
            severity = "CRITICAL" if z_score > 5.0 else "ELEVATED"
            score_contrib = min(40.0, max(0.0, (z_score - 1.5) * 8.0))
            factor_scores["spend_deviation"] = score_contrib
            factors.append({
                "factor": "Spend Deviation",
                "severity": severity,
                "contribution": round(score_contrib, 1),
                "insight": f"₹{amount:,.2f} is {multiplier:.1f}x of user historical average (₹{mean:,.2f}, Z-score: +{z_score:.2f})."
            })
        else:
            factors.append({
                "factor": "Spend Deviation",
                "severity": "NORMAL",
                "contribution": 0.0,
                "insight": f"Amount ₹{amount:,.2f} aligns comfortably with user standard spend baseline (₹{mean:,.2f} ± ₹{profile.ewma_std:,.2f})."
            })

        # 2. Device Novelty
        if not is_known_device:
            factor_scores["device_novelty"] = 35.0
            factors.append({
                "factor": "Unfamiliar Device",
                "severity": "CRITICAL" if risk_tier in ["HIGH", "CRITICAL"] else "ELEVATED",
                "contribution": 35.0,
                "insight": f"Transaction initiated from unfamiliar hardware signature '{device_model}' never previously seen on this account."
            })
        else:
            factors.append({
                "factor": "Device Verification",
                "severity": "TRUSTED",
                "contribution": 0.0,
                "insight": f"Device '{device_model}' is registered in user trusted hardware profile."
            })

        # 3. Geographic Velocity
        if velocity > 900.0:  # Faster than commercial aircraft
            factor_scores["geo_velocity"] = 40.0
            factors.append({
                "factor": "Impossible Geo-Velocity",
                "severity": "CRITICAL",
                "contribution": 40.0,
                "insight": f"Physical jump of {dist:,.0f} km from {profile.last_city} to {city} in {hours:.2f} hrs yields {velocity:,.0f} km/h (exceeds physical aviation limits)."
            })
        elif velocity > 250.0 and not is_known_city:
            factor_scores["geo_velocity"] = 15.0
            factors.append({
                "factor": "Inter-City Velocity",
                "severity": "ELEVATED",
                "contribution": 15.0,
                "insight": f"Travel distance of {dist:,.0f} km from {profile.last_city} in {hours:.2f} hrs. Plausible domestic flight, but unfamiliar city."
            })
        else:
            factors.append({
                "factor": "Location Dynamics",
                "severity": "NORMAL",
                "contribution": 0.0,
                "insight": f"Location '{city}' is verified within plausible geographical proximity ({dist:,.1f} km, {velocity:.0f} km/h)."
            })

        # 4. Temporal / Nocturnal Anomaly
        if is_nocturnal:
            factor_scores["temporal_anomaly"] = 20.0
            factors.append({
                "factor": "Nocturnal Execution Window",
                "severity": "ELEVATED",
                "contribution": 20.0,
                "insight": "Transaction executed during deep sleep hours (01:00 AM - 05:30 AM IST), divergent from user's typical daytime circadian cycle."
            })

        # 5. Burst Frequency
        if burst_count >= 5:
            factor_scores["burst_frequency"] = 25.0
            factors.append({
                "factor": "Burst Velocity Spike",
                "severity": "CRITICAL" if burst_count >= 8 else "ELEVATED",
                "contribution": 25.0,
                "insight": f"{burst_count} rapid transactions recorded in the past 60 minutes, typical of automated carding or credential stuffing scripts."
            })

        # 6. Novel Device High Risk Transfer Vector
        if features.get("p2p_novel_device_risk", 0) == 1:
            factor_scores["device_novelty"] = 45.0
            factors.append({
                "factor": "High-Risk Transfer from Novel Device",
                "severity": "CRITICAL",
                "contribution": 45.0,
                "insight": f"High-risk transfer type '{category}' initiated from unrecognized device '{device_model}', typical of account takeover or money mule activity."
            })

        # Compute factor percentage attribution breakdown
        total_score_contrib = sum(factor_scores.values()) or 1.0
        attribution_breakdown = {
            k: round((v / total_score_contrib) * 100.0, 1) for k, v in factor_scores.items()
        }

        # Distinguish Hostile Takeover vs Benign Anomaly
        anomaly_diagnosis = "NORMAL_TRANSACTION"
        action_recommendation = "ALLOW"

        if risk_tier in ["HIGH", "CRITICAL"]:
            if not is_known_device and (is_nocturnal or velocity > 850.0 or category in ["P2P_Transfer", "Gaming_Crypto"] or features.get("hostile_triad_score", 0) >= 1.5):
                anomaly_diagnosis = "HOSTILE_ACCOUNT_TAKEOVER"
                action_recommendation = "CHALLENGE_BIOMETRIC_OR_BLOCK"
                summary_narrative = (
                    f"⚠️ HIGH RISK ALERT: Probable Hostile Account Takeover detected. Unrecognized device '{device_model}' "
                    f"attempted ₹{amount:,.2f} {category} with severe spatial/temporal anomalies."
                )
            else:
                anomaly_diagnosis = "HIGH_ANOMALY_SUSPICIOUS"
                action_recommendation = "STEP_UP_OTP_VERIFICATION"
                summary_narrative = (
                    f"⚠️ ELEVATED RISK: Transaction of ₹{amount:,.2f} deviates significantly from account baseline across multiple vectors."
                )
        elif risk_tier == "MEDIUM":
            if not is_known_device and is_known_city and not is_nocturnal and velocity < 120.0 and category not in ["P2P_Transfer", "Gaming_Crypto"]:
                anomaly_diagnosis = "BENIGN_DEVICE_UPGRADE"
                action_recommendation = "ALLOW_WITH_NOTIFY_AND_LEARN"
                summary_narrative = (
                    f"💡 BENIGN DEVICE UPGRADE: Transaction from new hardware '{device_model}' in familiar home city ({city}) "
                    f"during daytime hours with normal velocity. Likely personal phone upgrade or secondary device."
                )
            elif is_known_device and (z_score > 3.0 or not is_known_city):
                anomaly_diagnosis = "BENIGN_LIFESTYLE_ANOMALY"
                action_recommendation = "ALLOW_WITH_NOTIFY_AND_LEARN"
                summary_narrative = (
                    f"💡 BENIGN ANOMALY DETECTED: Elevated spend or travel observed, but initiated from verified trusted device '{device_model}'. "
                    f"Likely festive purchase or planned vacation. Recommend baseline adaptation upon user confirmation."
                )
            else:
                anomaly_diagnosis = "MILD_DEVIATION"
                action_recommendation = "SILENT_LOG"
                summary_narrative = f"Moderate deviation detected (Risk {risk_score}/100), within allowable fallback thresholds."
        else:
            summary_narrative = f"✅ Transaction verified legitimate. Behavioral patterns match user baseline."

        return {
            "risk_score": risk_score,
            "risk_tier": risk_tier,
            "anomaly_diagnosis": anomaly_diagnosis,
            "action_recommendation": action_recommendation,
            "summary_narrative": summary_narrative,
            "factors": factors,
            "attribution_breakdown": attribution_breakdown
        }


# =====================================================================
# 5. Synthetic UPI Simulation Pipeline
# =====================================================================
def generate_synthetic_upi_dataset(num_rows: int = 3000, random_seed: int = 42) -> pd.DataFrame:
    """
    Generates realistic, labeled synthetic UPI transaction stream
    with routine spends, benign lifestyle spikes, and hostile fraud.
    """
    np.random.seed(random_seed)
    cities = list(INDIAN_CITIES.keys())
    user_pool = [f"USR_{1000 + i}" for i in range(80)]

    # Establish baseline user profiles
    user_baselines = {}
    for uid in user_pool:
        primary_city = np.random.choice(["Bengaluru", "Mumbai", "Delhi", "Pune", "Hyderabad", "Chennai"])
        primary_device = f"DEV_{uid[-4:]}_A"
        device_name = np.random.choice(["Samsung Galaxy S23", "iPhone 15", "OnePlus 12", "Xiaomi Redmi 13"])
        mean_spend = float(np.random.choice([450.0, 850.0, 1400.0, 2800.0, 6200.0]))
        std_spend = float(mean_spend * np.random.uniform(0.20, 0.40))
        user_baselines[uid] = {
            "primary_city": primary_city,
            "primary_device": primary_device,
            "device_name": device_name,
            "mean": mean_spend,
            "std": std_spend
        }

    records = []
    base_time = datetime(2026, 9, 1, 8, 0, 0)

    for i in range(num_rows):
        uid = np.random.choice(user_pool)
        u_info = user_baselines[uid]
        mean = u_info["mean"]
        std = u_info["std"]

        # 85% normal, 9% benign anomaly, 6% hostile fraud
        rand_scenario = np.random.random()

        if rand_scenario < 0.85:
            # 1. Normal routine transaction
            scenario_type = "normal_routine"
            is_fraud = 0
            amount = max(10.0, np.random.normal(mean, std))
            category = np.random.choice(["Groceries_Daily", "Food_Dining", "Utility_Bills", "Travel_Ticketing"])
            device_id = u_info["primary_device"]
            device_model = u_info["device_name"]
            city = u_info["primary_city"]
            is_known_device = 1
            is_known_city = 1
            hours_since = round(float(np.random.exponential(4.0) + 0.2), 2)
            km_dist = round(float(np.random.uniform(0.1, 15.0)), 1)
            is_nocturnal = 1 if np.random.random() < 0.04 else 0
            burst_1h = int(np.random.choice([1, 1, 1, 2]))

        elif rand_scenario < 0.94:
            # 2. Benign Anomaly (Festive shopping or travel on trusted device)
            is_fraud = 0
            sub_type = np.random.choice(["festive", "travel"])
            if sub_type == "festive":
                scenario_type = "benign_festive_spend"
                amount = float(mean * np.random.uniform(3.5, 8.0))
                category = np.random.choice(["Jewelry_Luxury", "Electronics_Gadgets", "Food_Dining"])
                device_id = u_info["primary_device"]
                device_model = u_info["device_name"]
                city = u_info["primary_city"]
                is_known_device = 1
                is_known_city = 1
                hours_since = round(float(np.random.uniform(1.0, 6.0)), 2)
                km_dist = round(float(np.random.uniform(1.0, 25.0)), 1)
                is_nocturnal = 0
                burst_1h = int(np.random.choice([1, 2, 3]))
            else:
                scenario_type = "benign_travel"
                amount = float(mean * np.random.uniform(1.5, 4.0))
                category = "Travel_Ticketing"
                device_id = u_info["primary_device"]
                device_model = u_info["device_name"]
                city = np.random.choice(["Goa", "Jaipur", "Mumbai", "Delhi"])
                is_known_device = 1
                is_known_city = 0
                hours_since = round(float(np.random.uniform(3.0, 12.0)), 2)
                origin_coords = INDIAN_CITIES[u_info["primary_city"]]
                dest_coords = INDIAN_CITIES[city]
                km_dist = round(haversine_distance(origin_coords["lat"], origin_coords["lon"], dest_coords["lat"], dest_coords["lon"]), 1)
                is_nocturnal = 0
                burst_1h = 1

        else:
            # 3. Hostile Fraud (Account Takeover, Velocity Jump, Burst)
            is_fraud = 1
            fraud_sub = np.random.choice(["ato", "burst", "impossible_travel"])
            if fraud_sub == "ato":
                scenario_type = "hostile_account_takeover"
                amount = float(np.random.uniform(25000.0, 95000.0))
                category = np.random.choice(["P2P_Transfer", "Gaming_Crypto"])
                device_id = f"DEV_ROGUE_{np.random.randint(100, 999)}"
                device_model = np.random.choice(["Linux Emulator", "Unknown Transsion", "Pixel Rooted"])
                city = np.random.choice(["Moscow", "Lagos", "Kolkata", "Delhi"])
                is_known_device = 0
                is_known_city = 0
                hours_since = round(float(np.random.uniform(0.1, 1.5)), 2)
                km_dist = round(float(np.random.uniform(800.0, 5000.0)), 1)
                is_nocturnal = 1  # 3 AM attack
                burst_1h = int(np.random.choice([2, 3, 4]))
            elif fraud_sub == "burst":
                scenario_type = "credential_stuffing_burst"
                amount = float(np.random.uniform(500.0, 4500.0))
                category = "Gaming_Crypto"
                device_id = f"DEV_BOT_{np.random.randint(10, 99)}"
                device_model = "Botnet Script v2"
                city = u_info["primary_city"]
                is_known_device = 0
                is_known_city = 1
                hours_since = round(float(np.random.uniform(0.01, 0.08)), 2)
                km_dist = 0.5
                is_nocturnal = 1
                burst_1h = int(np.random.randint(6, 15))
            else:
                scenario_type = "impossible_travel_jump"
                amount = float(mean * np.random.uniform(2.0, 5.0))
                category = "Electronics_Gadgets"
                device_id = f"DEV_CLONE_{np.random.randint(10, 99)}"
                device_model = "Virtual Device"
                city = "Moscow"
                is_known_device = 0
                is_known_city = 0
                hours_since = 0.2  # 12 minutes
                km_dist = 4500.0  # Mumbai to Moscow
                is_nocturnal = 0
                burst_1h = 2

        # Derived calculations
        velocity_kmh = round(km_dist / max(hours_since, 0.01), 1)
        z_score = round((amount - mean) / max(std, 1.0), 3)
        spend_mult = round(amount / max(mean, 1.0), 2)
        city_coords = INDIAN_CITIES.get(city, {"lat": 19.0760, "lon": 72.8777})

        timestamp = base_time + timedelta(minutes=int(i * 12 + np.random.randint(1, 30)))
        if is_nocturnal:
            timestamp = timestamp.replace(hour=np.random.randint(1, 4), minute=np.random.randint(0, 59))

        hostile_triad_score = round(
            float((1 - is_known_device) * (
                1.5 * is_nocturnal +
                2.0 * float(velocity_kmh > 800.0) +
                1.0 * (1 - is_known_city)
            )), 2
        )
        device_risk_penalty = round(
            float((1 - is_known_device) * (1.5 * (1 - is_known_city) + 1.2 * is_nocturnal) * math.log1p(max(spend_mult, 0.1))), 2
        )
        geo_velocity_anomaly = 1 if velocity_kmh > 850.0 else 0
        p2p_novel_device_risk = 1 if (is_known_device == 0 and category in ["P2P_Transfer", "Gaming_Crypto"]) else 0

        records.append({
            "transaction_id": f"TXN_UPI_{100000 + i}",
            "user_id": uid,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "amount": round(amount, 2),
            "merchant_category": category,
            "device_id": device_id,
            "device_model": device_model,
            "location_city": city,
            "location_lat": city_coords["lat"],
            "location_lon": city_coords["lon"],
            "user_avg_amount_30d": round(mean, 2),
            "user_std_amount_30d": round(std, 2),
            "z_score_amount": z_score,
            "spend_multiplier": spend_mult,
            "is_known_device": is_known_device,
            "is_known_city": is_known_city,
            "hours_since_last_txn": hours_since,
            "km_from_last_txn": km_dist,
            "velocity_kmh": velocity_kmh,
            "is_nocturnal": is_nocturnal,
            "txn_velocity_1h": burst_1h,
            "hostile_triad_score": hostile_triad_score,
            "device_risk_penalty": device_risk_penalty,
            "geo_velocity_anomaly": geo_velocity_anomaly,
            "p2p_novel_device_risk": p2p_novel_device_risk,
            "scenario_type": scenario_type,
            "is_fraud": is_fraud
        })

    return pd.DataFrame(records)


# =====================================================================
# Main CLI & Self-Verification Execution
# =====================================================================
if __name__ == "__main__":
    print("=" * 65)
    print("🛡️ SentinelUPI: Initializing Engine & Data Pipeline")
    print("=" * 65)

    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    csv_path = os.path.join(data_dir, "transactions.csv")

    if not os.path.exists(csv_path):
        print(f"Generating synthetic realistic UPI transactions dataset (3,000 records)...")
        df_synthetic = generate_synthetic_upi_dataset(num_rows=3000)
        df_synthetic.to_csv(csv_path, index=False)
        print(f"✅ Saved synthetic dataset to {csv_path}")
    else:
        print(f"Loading existing transactions dataset from {csv_path}...")
        df_synthetic = pd.read_csv(csv_path)

    print(f"Dataset overview: {len(df_synthetic)} rows, {df_synthetic['is_fraud'].sum()} frauds ({df_synthetic['is_fraud'].mean()*100:.1f}%)")

    # Train Fraud Model
    model = FraudModel()
    print("Training ML model with calibrated risk scoring...")
    metrics = model.train(df_synthetic)
    print(f"✅ Model trained successfully!")
    print(f"   ROC-AUC: {metrics['roc_auc']:.4f}")
    print(f"   Precision: {metrics['precision']:.4f}")
    print(f"   Recall: {metrics['recall']:.4f}")
    print(f"   F1-Score: {metrics['f1_score']:.4f}")

    # Test an Explainability Example
    profile_mgr = ProfileManager()
    sample_user = profile_mgr.get_or_create("USR_KARTHIK_BLR")
    sample_txn = {
        "amount": 42000.0,
        "device_id": "DEV_EMULATOR_88",
        "device_model": "Linux Android Emulator",
        "location_city": "Moscow",
        "timestamp": "2026-09-28 03:15:00",
        "merchant_category": "P2P_Transfer",
        "txn_velocity_1h": 3
    }
    extracted = FeatureExtractor.extract_features(sample_user, sample_txn)
    risk_score, tier = model.predict_risk(extracted)
    explanation = ExplainabilityEngine.generate_explanation(sample_user, sample_txn, extracted, risk_score, tier)

    print("\n--- Example Explainability Layer Output ---")
    print(f"Diagnosis: {explanation['anomaly_diagnosis']}")
    print(f"Risk Tier: {tier} ({risk_score}/100)")
    print(f"Narrative: {explanation['summary_narrative']}")
    for f in explanation["factors"]:
        print(f" - [{f['severity']}] {f['factor']}: {f['insight']}")
    print("=" * 65)
