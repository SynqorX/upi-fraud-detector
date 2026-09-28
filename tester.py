#!/usr/bin/env python3
"""
SentinelUPI: Real-Time Continuous Scenario Stream & Model Solver
===============================================================
Generates consecutive real-time transaction streams across users:
- Routine consecutive daily spends (chai, lunch, fuel, groceries)
- Benign lifestyle spikes (festive shopping, vacation domestic travel)
- Hostile attacks (3 AM Account Takeovers, botnet bursts, impossible travel)
- Hard edge cases (midnight sales, borderline velocity, small-amount spoofing)

The model solves each transaction in real-time.
Any 'Wrong Guess' (False Positive / False Negative) is highlighted and saved
to data/wrong_guesses.json and data/live_stream.json, which is rendered live
on http://localhost:8501 (the Streamlit dashboard).
"""

import os
import sys
import time
import json
import math
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List

from engine import (
    INDIAN_CITIES,
    MERCHANT_CATEGORIES,
    UserProfile,
    ProfileManager,
    FeatureExtractor,
    FraudModel,
    ExplainabilityEngine,
    generate_synthetic_upi_dataset
)

WRONG_GUESSES_FILE = "data/wrong_guesses.json"
LIVE_STREAM_FILE = "data/live_stream.json"


def ensure_data_dir():
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(WRONG_GUESSES_FILE):
        with open(WRONG_GUESSES_FILE, "w") as f:
            json.dump([], f)
    if not os.path.exists(LIVE_STREAM_FILE):
        with open(LIVE_STREAM_FILE, "w") as f:
            json.dump([], f)


def save_record_to_stream(record: Dict[str, Any], is_wrong: bool):
    """Saves record to live stream and wrong guesses log for localhost:8501 to display."""
    ensure_data_dir()

    # Update live stream (keep last 50)
    try:
        with open(LIVE_STREAM_FILE, "r") as f:
            stream_data = json.load(f)
    except Exception:
        stream_data = []

    stream_data.append(record)
    if len(stream_data) > 60:
        stream_data = stream_data[-60:]

    with open(LIVE_STREAM_FILE, "w") as f:
        json.dump(stream_data, f, indent=2)

    # If wrong guess, save to wrong guesses list
    if is_wrong:
        try:
            with open(WRONG_GUESSES_FILE, "r") as f:
                wrong_data = json.load(f)
        except Exception:
            wrong_data = []

        wrong_data.append(record)
        with open(WRONG_GUESSES_FILE, "w") as f:
            json.dump(wrong_data, f, indent=2)


class RealtimeStreamGenerator:
    """Generates consecutive, contextual UPI transaction streams."""
    def __init__(self, profile_mgr: ProfileManager):
        self.profile_mgr = profile_mgr
        self.users = list(self.profile_mgr.profiles.keys())
        self.seq_id = 1000

    def generate_consecutive_batch(self, count: int = 30) -> List[Dict[str, Any]]:
        """Generates a consecutive series of connected user transactions."""
        batch = []
        user_id = random.choice(self.users)
        profile = self.profile_mgr.get_or_create(user_id)
        current_time = datetime.now() - timedelta(hours=36)
        home_city = profile.trusted_cities[0]
        home_device_id = list(profile.trusted_devices.keys())[0]
        home_device_model = list(profile.trusted_devices.values())[0]

        # Define a sequential storyline of transactions for this user
        storyline_templates = [
            # 1. Morning Routine Chai & Breakfast
            {"desc": "Morning Tea & Breakfast at local cafe", "amount_mult": 0.15, "cat": "Food_Dining",
             "dev_id": home_device_id, "dev_model": home_device_model, "city": home_city,
             "hour_offset": 8.5, "explicit_hour": 8, "explicit_min": 30, "burst": 1, "expected": "LEGITIMATE", "type": "routine"},

            # 2. Commute Metro / Fuel
            {"desc": "Metro Transit recharge", "amount_mult": 0.25, "cat": "Utility_Bills",
             "dev_id": home_device_id, "dev_model": home_device_model, "city": home_city,
             "hour_offset": 9.2, "explicit_hour": 9, "explicit_min": 15, "burst": 1, "expected": "LEGITIMATE", "type": "routine"},

            # 3. Midday Lunch with colleagues
            {"desc": "Team Lunch payment", "amount_mult": 0.45, "cat": "Food_Dining",
             "dev_id": home_device_id, "dev_model": home_device_model, "city": home_city,
             "hour_offset": 13.5, "explicit_hour": 13, "explicit_min": 30, "burst": 1, "expected": "LEGITIMATE", "type": "routine"},

            # 4. Evening Groceries
            {"desc": "Weekly supermarket essentials", "amount_mult": 1.1, "cat": "Groceries_Daily",
             "dev_id": home_device_id, "dev_model": home_device_model, "city": home_city,
             "hour_offset": 18.0, "explicit_hour": 18, "explicit_min": 0, "burst": 1, "expected": "LEGITIMATE", "type": "routine"},

            # 5. Benign Spike: Festive Sale purchase
            {"desc": "Diwali Festival Electronics purchase", "amount_mult": 8.5, "cat": "Electronics_Gadgets",
             "dev_id": home_device_id, "dev_model": home_device_model, "city": home_city,
             "hour_offset": 20.5, "explicit_hour": 20, "explicit_min": 30, "burst": 2, "expected": "LEGITIMATE", "type": "benign_festive"},

            # 6. Hard Edge Case: Midnight Flash Sale
            {"desc": "Borderline: 1:15 AM Midnight Flash Sale on trusted phone", "amount_mult": 5.2, "cat": "Electronics_Gadgets",
             "dev_id": home_device_id, "dev_model": home_device_model, "city": home_city,
             "hour_offset": 25.25, "explicit_hour": 1, "explicit_min": 15, "burst": 2, "expected": "LEGITIMATE", "type": "edge_case_nocturnal_sale"},

            # 7. Benign Domestic Travel: Flying to Goa for the weekend
            {"desc": "Weekend Travel: Dinner at Calangute Beach, Goa", "amount_mult": 1.8, "cat": "Food_Dining",
             "dev_id": home_device_id, "dev_model": home_device_model, "city": "Goa",
             "hour_offset": 32.0, "explicit_hour": 20, "explicit_min": 15, "burst": 1, "expected": "LEGITIMATE", "type": "benign_travel"},

            # 8. Hostile Attack: Unrecognized Emulator attempting 3 AM Account Takeover
            {"desc": "CRITICAL ATTACK: 03:20 AM Hostile Takeover from Cloud Emulator", "amount_mult": 35.0, "cat": "P2P_Transfer",
             "dev_id": f"DEV_ROGUE_{random.randint(100, 999)}", "dev_model": "Linux Cloud Emulator", "city": "Bengaluru",
             "hour_offset": 51.3, "explicit_hour": 3, "explicit_min": 20, "burst": 4, "expected": "FRAUD", "type": "hostile_ato"},

            # 9. Hostile Attack: Impossible Geo-Jump (Goa to Moscow in 20 minutes)
            {"desc": "CRITICAL ATTACK: Impossible Travel Jump (4,800 km in 20 mins)", "amount_mult": 12.0, "cat": "Gaming_Crypto",
             "dev_id": f"DEV_CLONE_{random.randint(10, 99)}", "dev_model": "Rooted Android 12", "city": "Moscow",
             "hour_offset": 51.6, "explicit_hour": 14, "explicit_min": 45, "burst": 2, "expected": "FRAUD", "type": "impossible_travel"},

            # 10. Hostile Attack: Rapid Scripted Bot Burst
            {"desc": "CRITICAL ATTACK: Automated Card Testing Botnet (15 micro-txns)", "amount_mult": 0.08, "cat": "Gaming_Crypto",
             "dev_id": f"DEV_BOT_{random.randint(10, 99)}", "dev_model": "Python Requests Bot", "city": home_city,
             "hour_offset": 52.0, "explicit_hour": 2, "explicit_min": 10, "burst": 15, "expected": "FRAUD", "type": "botnet_burst"},

            # 11. Subtle Fraud Edge Case: Daytime small P2P transfer from newly switched unknown device
            {"desc": "Subtle Fraud Edge Case: Unregistered burner phone making small daytime P2P", "amount_mult": 0.25, "cat": "P2P_Transfer",
             "dev_id": f"DEV_BURNER_{random.randint(100, 999)}", "dev_model": "Itel A50", "city": home_city,
             "hour_offset": 58.0, "explicit_hour": 11, "explicit_min": 30, "burst": 1, "expected": "FRAUD", "type": "subtle_burner_fraud"},

            # 12. Edge Case: Legitimate user bought a new phone and made a purchase
            {"desc": "Edge Case: User bought new iPhone 16 Pro and made payment in home city", "amount_mult": 6.5, "cat": "Electronics_Gadgets",
             "dev_id": "DEV_NEW_IPHONE16_99", "dev_model": "iPhone 16 Pro", "city": home_city,
             "hour_offset": 60.0, "explicit_hour": 14, "explicit_min": 15, "burst": 1, "expected": "LEGITIMATE", "type": "edge_new_device_high_spend"},

            # 13. Edge Case: Urgent midnight hospital pharmacy bill on trusted phone
            {"desc": "Edge Case: 02:45 AM emergency pharmacy purchase on trusted phone", "amount_mult": 2.2, "cat": "Utility_Bills",
             "dev_id": home_device_id, "dev_model": home_device_model, "city": home_city,
             "hour_offset": 74.75, "explicit_hour": 2, "explicit_min": 45, "burst": 1, "expected": "LEGITIMATE", "type": "emergency_nocturnal_legit"}
        ]

        for item in storyline_templates:
            self.seq_id += 1
            txn_dt = current_time + timedelta(hours=item["hour_offset"])
            if "explicit_hour" in item:
                txn_dt = txn_dt.replace(hour=item["explicit_hour"], minute=item.get("explicit_min", 15), second=0)
            amt = round(max(30.0, profile.ewma_mean * item["amount_mult"] + random.uniform(-20, 20)), 2)

            batch.append({
                "transaction_id": f"TXN_STREAM_{self.seq_id}",
                "user_id": user_id,
                "description": item["desc"],
                "amount": amt,
                "merchant_category": item["cat"],
                "device_id": item["dev_id"],
                "device_model": item["dev_model"],
                "location_city": item["city"],
                "timestamp_dt": txn_dt,
                "timestamp": txn_dt.strftime("%Y-%m-%d %H:%M:%S"),
                "txn_velocity_1h": item["burst"],
                "expected": item["expected"],
                "scenario_type": item["type"]
            })

        return batch


def run_stream_solver(num_rounds: int = 1, delay_sec: float = 0.5):
    """Generates consecutive transactions in real-time and model solves them live."""
    print("\n" + "=" * 80)
    print("🛡️ SentinelUPI: Real-Time Consecutive Transaction Streamer & Model Solver")
    print("   Output & Wrong Guesses are mirrored live to: http://localhost:8501")
    print("=" * 80)

    ensure_data_dir()

    # Load Model & Profiles
    model = FraudModel()
    model.load_or_train_default(generate_synthetic_upi_dataset)

    profile_mgr = ProfileManager()
    if os.path.exists("data/transactions.csv"):
        df = pd.read_csv("data/transactions.csv")
        profile_mgr.load_from_dataframe(df)

    streamer = RealtimeStreamGenerator(profile_mgr)

    total_evaluated = 0
    correct_count = 0
    wrong_count = 0

    print(f"\n🚀 Beginning real-time consecutive transaction stream...")
    print(f"   (Press Ctrl+C at any time to pause stream)\n")

    try:
        for r in range(num_rounds):
            batch = streamer.generate_consecutive_batch()

            for txn in batch:
                total_evaluated += 1
                user = profile_mgr.get_or_create(txn["user_id"])

                # 1. Feature Extraction
                features = FeatureExtractor.extract_features(user, txn)

                # 2. Model Prediction & Explainability
                risk_score, risk_tier = model.predict_risk(features)
                explanation = ExplainabilityEngine.generate_explanation(user, txn, features, risk_score, risk_tier)

                is_predicted_fraud = (risk_tier in ["HIGH", "CRITICAL"])
                predicted_verdict = "FRAUD" if is_predicted_fraud else "LEGITIMATE"
                expected_verdict = txn["expected"]
                is_correct = (predicted_verdict == expected_verdict)

                if is_correct:
                    correct_count += 1
                    status_badge = "✅ CORRECT"
                else:
                    wrong_count += 1
                    status_badge = "❌ WRONG GUESS"

                # Update user profile baseline if legitimate to simulate real-world adaptation
                if expected_verdict == "LEGITIMATE" and is_correct:
                    user.update_baseline(txn["amount"], is_feedback_legitimate=False)
                user.record_transaction({
                    "timestamp_dt": txn["timestamp_dt"],
                    "location_city": txn["location_city"],
                    "amount": txn["amount"]
                })

                # Prepare payload for localhost:8501 live stream
                stream_record = {
                    "timestamp": txn["timestamp"],
                    "transaction_id": txn["transaction_id"],
                    "user_id": txn["user_id"],
                    "description": txn["description"],
                    "amount": txn["amount"],
                    "user_mean": round(user.ewma_mean, 2),
                    "device": txn["device_model"],
                    "city": txn["location_city"],
                    "hour": txn["timestamp_dt"].strftime("%I:%M %p"),
                    "risk_score": risk_score,
                    "risk_tier": risk_tier,
                    "predicted": predicted_verdict,
                    "expected": expected_verdict,
                    "status": "CORRECT" if is_correct else "WRONG_GUESS",
                    "diagnosis": explanation["anomaly_diagnosis"],
                    "factors": [f["insight"] for f in explanation["factors"]]
                }

                # Save record to JSON logs for localhost:8501
                save_record_to_stream(stream_record, is_wrong=not is_correct)

                # CLI Printout
                if not is_correct:
                    print("\n" + "!" * 80)
                    print(f"🚨 [WRONG GUESS DETECTED #{wrong_count}] Streamed to localhost:8501!")
                    print(f"   • Txn ID      : {txn['transaction_id']} | User: {txn['user_id']}")
                    print(f"   • Description : {txn['description']}")
                    print(f"   • Amount      : ₹{txn['amount']:,.2f} (User Avg: ₹{user.ewma_mean:,.2f} | Z-Score: {features['z_score_amount']:+.2f})")
                    print(f"   • Device      : {txn['device_model']} (Known: {features['is_known_device']})")
                    print(f"   • City/Speed  : {txn['location_city']} ({features['velocity_kmh']:,.0f} km/h)")
                    print(f"   • Model Verdict: PREDICTED {predicted_verdict} (Risk: {risk_score}/100, Tier: {risk_tier})")
                    print(f"   • Expected    : {expected_verdict}")
                    print(f"   • Factor Reason: {explanation['summary_narrative']}")
                    print("!" * 80 + "\n")
                else:
                    print(f"[{txn['timestamp']}] {txn['user_id']} | ₹{txn['amount']:>8,.2f} | {txn['merchant_category']:<18} | "
                          f"Risk: {risk_score:>5.1f} ({risk_tier:<8}) | Pred: {predicted_verdict:<10} | {status_badge}")

                time.sleep(delay_sec)

    except KeyboardInterrupt:
        print("\n🛑 Stream interrupted by user.")

    print("\n" + "=" * 80)
    print(f"📊 STREAM EVALUATION SUMMARY")
    print(f"   Total Consecutive Txns Evaluated : {total_evaluated}")
    print(f"   Correct Model Solves             : {correct_count} ({(correct_count/max(total_evaluated,1))*100:.1f}%)")
    print(f"   Wrong Guesses Recorded           : {wrong_count} ({(wrong_count/max(total_evaluated,1))*100:.1f}%)")
    print(f"   Inspect all wrong guesses at     : http://localhost:8501")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    rounds = 3 if len(sys.argv) < 2 else int(sys.argv[1])
    speed = 0.15 if len(sys.argv) < 3 else float(sys.argv[2])
    run_stream_solver(num_rounds=rounds, delay_sec=speed)
