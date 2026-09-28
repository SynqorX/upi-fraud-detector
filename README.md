# 🛡️ SentinelUPI: Adaptive Fraud Detection Without Blind Alerts

> **Track:** D6 · Fintech | **Target:** Working Prototype | **Difficulty:** Expert

---

## 📌 Executive Summary

Traditional payment fraud detection systems act as black boxes. When a legitimate user's transaction gets blocked, they receive generic, opaque error messages like *"Transaction declined due to security reasons"*. This design leads to **blind alerts**, user panic, support ticket floods, and false positives caused by normal life changes (travel, promotions, festival spending).

**SentinelUPI** is an Explainable AI (XAI) transaction verification prototype. Instead of returning only a raw risk number, it:
1. **Explains the exact factors** behind flagged transactions in plain English[cite: 1].
2. **Distinguishes benign anomalies** from hostile account takeovers[cite: 1].
3. **Dynamically adapts user baselines** to concept drift (e.g., relocation, lifestyle upgrades) without recurring false alarms[cite: 1].

---

## 🚀 Key Features

* **No Blind Alerts (Attribution Layer):** Breaks down flagged decisions into transparent, actionable signals (e.g., spend multiple vs. historical average, unfamiliar device hardware signature, geographic velocity jumps)[cite: 1].
* **Dynamic Behavioral Baselines:** Tracks continuous spending patterns, typical execution hours, active geolocations, and trusted devices per user using Exponentially Weighted Moving Averages (EWMA)[cite: 1].
* **Concept Drift & Adaptation:** Provides a human-in-the-loop recalibration feedback loop[cite: 1]. When a flagged transaction is confirmed legitimate, the engine updates baseline statistics, preventing repetitive alerts on subsequent transactions[cite: 1].
* **Synthetic Simulation Pipeline:** Generates realistic behavioral streams incorporating standard spend routines, benign anomalies, and coordinated fraud patterns without requiring sensitive real banking data[cite: 1].

---

## 🏗️ System Architecture

```text
  [ Incoming Transaction ]
             │
             ▼
┌────────────────────────────────────────┐
│  1. Baseline & Profile Manager         │
│     - EWMA Mean & Variance             │
│     - Known Device & Geo Registry      │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│  2. Deviation Scoring Engine           │
│     - Z-Score Spending Deviation       │
│     - Nocturnal Timing Check           │
│     - Device Fingerprint Verification  │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│  3. Explainability Layer               │
│     - Plain-English Factor Extraction  │
│     - Root-Cause Attribution Cards     │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│  4. Interactive Streamlit Interface    │
│     - Live Transaction Simulator       │
│     - Factor Attribution Card          │
│     - Adaptive Drift Progression Chart │
└────────────────────────────────────────┘
