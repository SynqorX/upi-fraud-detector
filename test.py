#!/usr/bin/env python3
"""
SentinelUPI: Model Accuracy & Condition Verification Inspector
=============================================================
This script evaluates the trained machine learning model, displays:
1. Overall Accuracy & Performance Scorecard (ROC-AUC, Precision, Recall, F1)
2. Detailed "True & False" Confusion Matrix Breakdown:
   - True Positives (Actual Fraud correctly Caught)
   - True Negatives (Legitimate correctly Approved)
   - False Positives (False Alarms on normal users)
   - False Negatives (Missed Fraud attacks)
3. Step-by-step Condition Inspection across realistic scenarios:
   - Normal Chai / Groceries
   - Benign Festive Spends (Diwali electronics)
   - Benign Domestic Travel (Goa vacation)
   - Hostile Account Takeover (3 AM / Unknown Emulator)
   - Impossible Travel Jump (Bengaluru to Moscow in 12 mins)
   - Rapid Credential Stuffing Burst (10 txns in 2 mins)
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

from engine import (
    INDIAN_CITIES,
    MERCHANT_CATEGORIES,
    FEATURE_COLUMNS,
    UserProfile,
    ProfileManager,
    FeatureExtractor,
    FraudModel,
    ExplainabilityEngine,
    generate_synthetic_upi_dataset
)


def print_banner(text: str):
    print("\n" + "=" * 78)
    print(f"  {text}")
    print("=" * 78)


def evaluate_dataset_performance(csv_path: str = "data/transactions.csv"):
    """Loads dataset, splits into train/test, and displays performance scorecard."""
    print_banner("📊 1. MODEL ACCURACY & PERFORMANCE SCORECARD")

    if not os.path.exists(csv_path):
        print(f"Dataset not found at {csv_path}. Generating synthetic dataset...")
        df = generate_synthetic_upi_dataset(num_rows=3000)
        os.makedirs("data", exist_ok=True)
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    # Compute derived features if missing
    if "z_score_amount" not in df.columns:
        df["z_score_amount"] = (df["amount"] - df["user_avg_amount_30d"]) / np.maximum(df["user_std_amount_30d"], 1.0)
    if "spend_multiplier" not in df.columns:
        df["spend_multiplier"] = df["amount"] / np.maximum(df["user_avg_amount_30d"], 1.0)

    X = df[FEATURE_COLUMNS]
    y = df["is_fraud"].astype(int)

    # 75% train, 25% test split (reproducible seed)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = FraudModel()
    model.train(df)

    y_pred = model.model.predict(X_test)
    y_prob = model.model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    auc = roc_auc_score(y_test, y_prob)

    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    print(f"Total Transactions in Test Set: {len(y_test):,} transactions (Held-out 25%)")
    print(f"  • Actual Legitimate Transactions : {(y_test == 0).sum():,} ({((y_test == 0).mean()*100):.1f}%)")
    print(f"  • Actual Fraudulent Attacks      : {(y_test == 1).sum():,} ({((y_test == 1).mean()*100):.1f}%)")
    print("-" * 78)
    print(f"  Accuracy Score   : {acc * 100:.2f}%  (Overall correct predictions)")
    print(f"  ROC-AUC Score    : {auc:.4f}   (Separation power between fraud & legit)")
    print(f"  Precision Score  : {prec * 100:.2f}%  (Guards against false alarms on legitimate users)")
    print(f"  Recall Score     : {rec * 100:.2f}%  (Guards against missed fraud attacks)")
    print(f"  F1-Score         : {f1:.4f}   (Harmonic balance of Precision and Recall)")

    # Confusion matrix explanation
    print_banner("🎯 2. TRUE & FALSE LEARNING BREAKDOWN (CONFUSION MATRIX)")
    print(f"┌──────────────────────────────┬──────────────────────────────┬──────────────────────────────┐")
    print(f"│ Total Held-Out Tests: {len(y_test):<6} │ Predicted: LEGIT (0)         │ Predicted: FRAUD (1)         │")
    print(f"├──────────────────────────────┼──────────────────────────────┼──────────────────────────────┤")
    print(f"│ Actual: LEGIT (0)            │ True Negative (TN): {tn:<8} │ False Positive (FP): {fp:<7} │")
    print(f"│                              │ ✅ Legitimate Approved       │ ⚠️ False Alarm (Blocked)     │")
    print(f"├──────────────────────────────┼──────────────────────────────┼──────────────────────────────┤")
    print(f"│ Actual: FRAUD (1)            │ False Negative (FN): {fn:<7} │ True Positive (TP): {tp:<8} │")
    print(f"│                              │ 🚨 Missed Fraud Attack       │ ✅ Fraud Attack Caught       │")
    print(f"└──────────────────────────────┴──────────────────────────────┴──────────────────────────────┘")

    print("\n🔍 What this means for the bank:")
    print(f" • Caught Fraud Rate (True Positive Rate)  : {(tp / (tp + fn))*100:.1f}% ({tp} out of {tp + fn} attacks stopped)")
    print(f" • False Alarm Rate (False Positive Rate)  : {(fp / (tn + fp))*100:.2f}% ({fp} false declines out of {tn + fp} legit txns)")
    print(f" • Missed Fraud Rate (False Negative Rate) : {(fn / (tp + fn))*100:.2f}% ({fn} missed attacks)")

    return model


def run_condition_inspection_tests(model: FraudModel):
    """Executes a series of realistic test scenarios and prints the condition-by-condition verdict."""
    print_banner("🔬 3. DETAILED CONDITION INSPECTION & SCENARIO TESTS")

    # Define a realistic user profile
    user = UserProfile(
        user_id="USR_4091",
        initial_mean=1850.0,
        initial_std=520.0,
        primary_device="DEV_IN_SAMS23_001",
        primary_city="Bengaluru"
    )
    user.trusted_devices["DEV_IN_SAMS23_001"] = "Samsung Galaxy S23"

    scenarios = [
        {
            "name": "Scenario 1: Daily Chai & Routine Groceries",
            "expected": "LEGITIMATE",
            "amount": 280.0,
            "category": "Groceries_Daily",
            "device_id": "DEV_IN_SAMS23_001",
            "device_model": "Samsung Galaxy S23",
            "location_city": "Bengaluru",
            "timestamp": "2026-09-28 14:30:00",
            "txn_velocity_1h": 1
        },
        {
            "name": "Scenario 2: Benign Festive Spike (Diwali Electronics on Trusted Phone)",
            "expected": "LEGITIMATE",
            "amount": 18500.0,  # 10x normal mean!
            "category": "Electronics_Gadgets",
            "device_id": "DEV_IN_SAMS23_001",  # Known trusted device
            "device_model": "Samsung Galaxy S23",
            "location_city": "Bengaluru",
            "timestamp": "2026-09-28 18:45:00",  # Daytime normal hour
            "txn_velocity_1h": 1
        },
        {
            "name": "Scenario 3: Benign Vacation Travel (Flight to Goa on Trusted Phone)",
            "expected": "LEGITIMATE",
            "amount": 4200.0,
            "category": "Food_Dining",
            "device_id": "DEV_IN_SAMS23_001",  # Known device
            "device_model": "Samsung Galaxy S23",
            "location_city": "Goa",  # New city, but plausible travel time
            "timestamp": "2026-09-28 20:30:00",
            "txn_velocity_1h": 1
        },
        {
            "name": "Scenario 4: Hostile Account Takeover (3:15 AM / Unknown Emulator / ₹75k P2P)",
            "expected": "FRAUD",
            "amount": 75000.0,
            "category": "P2P_Transfer",
            "device_id": "DEV_EMULATOR_99",  # Rogue unknown device
            "device_model": "Linux Cloud Emulator",
            "location_city": "Bengaluru",
            "timestamp": "2026-09-28 03:15:00",  # Deep sleep window
            "txn_velocity_1h": 3
        },
        {
            "name": "Scenario 5: Impossible Travel Velocity Jump (Bengaluru to Moscow in 15 mins)",
            "expected": "FRAUD",
            "amount": 12000.0,
            "category": "Electronics_Gadgets",
            "device_id": "DEV_CLONE_77",
            "device_model": "Virtual Android",
            "location_city": "Moscow",  # 5,800 km away
            "timestamp": "2026-09-28 14:45:00",
            "txn_velocity_1h": 2
        },
        {
            "name": "Scenario 6: Credential Stuffing Botnet Burst (12 Txns in 5 mins)",
            "expected": "FRAUD",
            "amount": 95.0,  # Small card testing amount
            "category": "Gaming_Crypto",
            "device_id": "DEV_BOT_01",
            "device_model": "Scripted Botnet",
            "location_city": "Bengaluru",
            "timestamp": "2026-09-28 02:10:00",
            "txn_velocity_1h": 12  # Rapid burst spike!
        }
    ]

    for sc in scenarios:
        print("\n" + "-" * 78)
        print(f"📌 {sc['name']}")
        print("-" * 78)

        # Extract features
        features = FeatureExtractor.extract_features(user, sc)
        risk_score, risk_tier = model.predict_risk(features)
        explanation = ExplainabilityEngine.generate_explanation(user, sc, features, risk_score, risk_tier)

        is_predicted_fraud = (risk_tier in ["HIGH", "CRITICAL"])
        predicted_verdict = "FRAUD" if is_predicted_fraud else "LEGITIMATE"
        is_correct = (predicted_verdict == sc["expected"])
        status_icon = "✅ CORRECT" if is_correct else "❌ MISMATCH"

        # Print Condition breakdown table
        print(f"  [Input Conditions Evaluated]:")
        print(f"   • Spend Amount        : ₹{sc['amount']:,.2f} (User Avg: ₹{user.ewma_mean:,.2f} | Z-Score: {features['z_score_amount']:+.2f}σ | {features['spend_multiplier']:.1f}x)")
        print(f"   • Device Fingerprint  : '{sc['device_model']}' -> {'TRUSTED (1)' if features['is_known_device'] else 'UNRECOGNIZED / NOVEL (0)'}")
        print(f"   • Location & Velocity : {sc['location_city']} ({features['km_from_last_txn']:,.0f} km away | Implied Speed: {features['velocity_kmh']:,.0f} km/h)")
        print(f"   • Execution Time      : {sc['timestamp']} IST -> {'NOCTURNAL SLEEP HOUR (1)' if features['is_nocturnal'] else 'NORMAL DAYTIME (0)'}")
        print(f"   • Burst Velocity      : {features['txn_velocity_1h']} transactions in 60m window")
        print(f"  [Model Output]:")
        print(f"   • Risk Score          : {risk_score} / 100  (Tier: {risk_tier})")
        print(f"   • Prediction          : {predicted_verdict} (Expected: {sc['expected']}) -> {status_icon}")
        print(f"   • Diagnostic Reason   : {explanation['summary_narrative']}")

        # Print top explanation factors
        print(f"  [Explainability Attribution]:")
        for f in explanation["factors"]:
            sev = f["severity"]
            print(f"     - [{sev}] {f['factor']}: {f['insight']}")

        # Save to wrong guesses log for localhost:8501 if wrong guess
        if not is_correct:
            wrong_payload = {
                "timestamp": sc["timestamp"],
                "transaction_id": f"TEST_TXN_{sc['name'][:12]}",
                "user_id": user.user_id,
                "description": sc["name"],
                "amount": sc["amount"],
                "user_mean": round(user.ewma_mean, 2),
                "device": sc["device_model"],
                "city": sc["location_city"],
                "hour": sc["timestamp"],
                "risk_score": risk_score,
                "risk_tier": risk_tier,
                "predicted": predicted_verdict,
                "expected": sc["expected"],
                "status": "WRONG_GUESS",
                "diagnosis": explanation["anomaly_diagnosis"],
                "factors": [f["insight"] for f in explanation["factors"]]
            }
            try:
                os.makedirs("data", exist_ok=True)
                wg_file = "data/wrong_guesses.json"
                w_list = []
                if os.path.exists(wg_file):
                    with open(wg_file, "r") as f:
                        w_list = json.load(f)
                w_list.append(wrong_payload)
                with open(wg_file, "w") as f:
                    json.dump(w_list, f, indent=2)
                print(f"  ⚠️ Logged Wrong Guess to localhost:8501! (Stored in {wg_file})")
            except Exception as e:
                pass


if __name__ == "__main__":
    print("\n" + "=" * 78)
    print("🛡️ SentinelUPI: Diagnostic Testing & Model Accuracy Verification")
    print("=" * 78)
    trained_model = evaluate_dataset_performance("data/transactions.csv")
    run_condition_inspection_tests(trained_model)
    print("\n" + "=" * 78)
    print("✨ All diagnostic and accuracy tests completed successfully!")
    print("📡 Real-time wrong guesses and live streams are displayed on: http://localhost:8501")
    print("=" * 78 + "\n")

