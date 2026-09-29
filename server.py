#!/usr/bin/env python3
"""
SentinelUPI Central Threat Server & Localhost Web Dashboard
============================================================
Runs the core Python fraud detection engine on this laptop (localhost:5000).
Provides:
1. Web Simulator Dashboard: One-click "Simulate Attack" triggers for hostile scenarios.
2. Forensic Attribution Viewer: Plain-English explanations & multi-vector threat scores.
3. REST API (/api/evaluate, /api/simulate, /api/status, /api/history) for mobile clients.
"""

import sys
import os
import json
import time
import math
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, List

# Ensure project directory is on sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from engine import (
    UserProfile,
    ProfileManager,
    FeatureExtractor,
    ExplainabilityEngine,
    FraudModel,
    INDIAN_CITIES,
    MERCHANT_CATEGORIES,
    FEATURE_COLUMNS,
    generate_synthetic_upi_dataset
)

# Global State on Server
user_manager = ProfileManager()
default_profile = user_manager.get_or_create(
    user_id="USR_4091",
    initial_mean=1850.0,
    initial_std=520.0,
    device="DEV_IN_SAMS23_001",
    city="Bengaluru"
)
default_profile.trusted_devices["DEV_IN_SAMS23_001"] = "Samsung Galaxy S23"
default_profile.trusted_cities = ["Bengaluru", "Mumbai"]

# Load trained model if available, else auto-train
fraud_model = FraudModel(model_path=os.path.join(BASE_DIR, "data", "fraud_model.joblib"))
try:
    fraud_model.load_or_train_default(generate_synthetic_upi_dataset)
    print(f"[*] FraudModel initialized and ready (metrics: {fraud_model.metrics})")
except Exception as e:
    print(f"[!] Warning initializing model: {e}")

evaluation_history: List[Dict[str, Any]] = []

def process_transaction(txn_dict: Dict[str, Any], profile: UserProfile = default_profile) -> Dict[str, Any]:
    """Runs transaction through FeatureExtractor, ML model, and Explainability Engine."""
    features = FeatureExtractor.extract_features(profile, txn_dict)
    
    # Predict risk score and tier using trained model
    if not fraud_model.is_trained():
        fraud_model.load_or_train_default(generate_synthetic_upi_dataset)
    risk_score, risk_tier = fraud_model.predict_risk(features)
        
    explanation = ExplainabilityEngine.generate_explanation(
        profile=profile,
        txn_dict=txn_dict,
        features=features,
        risk_score=risk_score,
        risk_tier=risk_tier
    )
    
    # If legitimate, adapt baseline
    if risk_tier == "LOW":
        profile.update_baseline(float(txn_dict.get("amount", 0.0)))
        profile.last_txn_time = datetime.now()
        profile.last_city = str(txn_dict.get("location_city", profile.last_city))
        coords = INDIAN_CITIES.get(profile.last_city, {"lat": profile.last_lat, "lon": profile.last_lon})
        profile.last_lat = coords["lat"]
        profile.last_lon = coords["lon"]
        
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transaction_id": txn_dict.get("transaction_id", f"TXN_{int(time.time()*1000)}"),
        "user_id": profile.user_id,
        "amount": float(txn_dict.get("amount", 0.0)),
        "merchant_category": str(txn_dict.get("merchant_category", "P2P_Transfer")),
        "device_id": str(txn_dict.get("device_id", "DEV_UNKNOWN")),
        "device_model": str(txn_dict.get("device_model", "Unknown Device")),
        "location_city": str(txn_dict.get("location_city", "Unknown City")),
        "features": features,
        "evaluation": explanation
    }
    
    evaluation_history.insert(0, record)
    if len(evaluation_history) > 100:
        evaluation_history.pop()
        
    return record


def generate_scenario_transaction(scenario_id: int, profile: UserProfile = default_profile) -> Dict[str, Any]:
    now = datetime.now()
    if scenario_id == 1:
        # 3:15 AM Rogue Emulator Cashout
        txn_time = now.replace(hour=3, minute=15, second=0)
        return {
            "transaction_id": f"TXN_ATK_EMU_{int(time.time())}",
            "amount": 75000.0,
            "merchant_category": "P2P_Transfer",
            "device_id": "DEV_ROGUE_CLOUD_EMU_99",
            "device_model": "Linux Android Cloud Emulator",
            "location_city": profile.last_city,
            "timestamp": txn_time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_dt": txn_time,
            "txn_velocity_1h": 3,
            "note": "Hostile Account Takeover Drain"
        }
    elif scenario_id == 2:
        # Hypersonic Moscow Geo-Jump
        txn_time = now + timedelta(minutes=15)
        return {
            "transaction_id": f"TXN_ATK_GEO_{int(time.time())}",
            "amount": 32000.0,
            "merchant_category": "P2P_Transfer",
            "device_id": "DEV_FOREIGN_CLONE_X",
            "device_model": "Virtual Clone Phone",
            "location_city": "Moscow",
            "timestamp": txn_time.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_dt": txn_time,
            "txn_velocity_1h": 2,
            "note": "Hypersonic Impossible Travel Jump"
        }
    elif scenario_id == 3:
        # Botnet Micro-Carding Burst
        return {
            "transaction_id": f"TXN_ATK_BOT_{int(time.time())}",
            "amount": 140.0,
            "merchant_category": "Gaming_Crypto",
            "device_id": "DEV_BOT_SCRIPT_08",
            "device_model": "Automated Rapid Script",
            "location_city": profile.last_city,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_dt": now,
            "txn_velocity_1h": 14,
            "note": "Botnet Automated Micro-Carding"
        }
    else:
        # Standard Legitimate Transaction
        return {
            "transaction_id": f"TXN_LEGIT_{int(time.time())}",
            "amount": 450.0,
            "merchant_category": "Food_Dining",
            "device_id": list(profile.trusted_devices.keys())[0],
            "device_model": list(profile.trusted_devices.values())[0],
            "location_city": profile.last_city,
            "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_dt": now,
            "txn_velocity_1h": 1,
            "note": "Routine Lunch & Coffee"
        }


# =====================================================================
# HTML Dashboard Template (Tailwind CSS, Glassmorphic Green & Sky Blue)
# =====================================================================
HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SentinelUPI • Central Threat Server & Attack Simulator</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    body {
      background: radial-gradient(circle at 10% 15%, rgba(2, 132, 199, 0.09) 0%, transparent 45%),
                  radial-gradient(circle at 90% 85%, rgba(16, 185, 129, 0.09) 0%, transparent 45%),
                  #F8FAFC;
      color: #0F172A;
      font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .font-mono {
      font-family: 'JetBrains Mono', monospace;
    }
    .glass-panel {
      background: rgba(255, 255, 255, 0.80);
      backdrop-filter: blur(28px);
      -webkit-backdrop-filter: blur(28px);
      border: 1px solid rgba(255, 255, 255, 0.95);
      box-shadow: 0 20px 40px -15px rgba(2, 132, 199, 0.06),
                  0 0 0 1px rgba(2, 132, 199, 0.04),
                  inset 0 1px 1px 0 rgba(255, 255, 255, 0.9);
    }
    .glass-panel-hero {
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.90) 0%, rgba(240, 253, 250, 0.85) 50%, rgba(240, 249, 255, 0.85) 100%);
      backdrop-filter: blur(32px);
      border: 1.5px solid rgba(255, 255, 255, 0.95);
      box-shadow: 0 24px 48px -12px rgba(16, 185, 129, 0.12),
                  0 8px 24px -8px rgba(2, 132, 199, 0.08),
                  inset 0 2px 2px 0 rgba(255, 255, 255, 1.0);
    }
    .btn-gradient-primary {
      background: linear-gradient(135deg, #10B981 0%, #0284C7 100%);
      color: white;
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 10px 25px -5px rgba(2, 132, 199, 0.35);
    }
    .btn-gradient-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 14px 30px -4px rgba(16, 185, 129, 0.45);
    }
    .progress-bar-fill {
      transition: width 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .gauge-circle {
      transition: stroke-dashoffset 0.85s cubic-bezier(0.16, 1, 0.3, 1), stroke 0.4s ease;
    }
    .custom-scroll::-webkit-scrollbar {
      width: 5px;
    }
    .custom-scroll::-webkit-scrollbar-thumb {
      background: rgba(148, 163, 184, 0.4);
      border-radius: 9999px;
    }
  </style>
</head>
<body class="min-h-screen p-3 sm:p-6 lg:p-8 max-w-7xl mx-auto flex flex-col justify-between">

  <!-- TOP APP HEADER -->
  <header class="glass-panel px-6 sm:px-8 py-5 rounded-3xl mb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
    <div class="flex items-center gap-4">
      <div class="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-500 to-sky-500 flex items-center justify-center text-white shadow-lg shadow-emerald-500/20">
        <i data-lucide="shield-alert" class="w-6 h-6 stroke-[2.5]"></i>
      </div>
      <div>
        <div class="flex items-center gap-2.5">
          <h1 class="text-lg sm:text-xl font-extrabold text-slate-900 tracking-tight">SentinelUPI Threat Console</h1>
          <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold uppercase tracking-wider">
            <span class="relative flex h-2 w-2">
              <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            Live • Port 5000
          </span>
        </div>
        <p class="text-xs text-slate-500 mt-0.5">Distributed Machine Learning Engine & Real-time Behavioral Forensic Attribution</p>
      </div>
    </div>

    <!-- Quick Telemetry Chips -->
    <div class="flex flex-wrap items-center gap-2.5 text-xs">
      <div class="px-3.5 py-1.5 rounded-xl bg-slate-100/80 border border-slate-200/80 flex items-center gap-1.5 font-medium text-slate-700">
        <i data-lucide="user" class="w-3.5 h-3.5 text-slate-400"></i>
        <span>User:</span>
        <span class="font-bold text-slate-900 font-mono">USR_4091</span>
      </div>
      <div class="px-3.5 py-1.5 rounded-xl bg-slate-100/80 border border-slate-200/80 flex items-center gap-1.5 font-medium text-slate-700">
        <i data-lucide="activity" class="w-3.5 h-3.5 text-emerald-500"></i>
        <span>Baseline (EWMA):</span>
        <span class="font-bold text-emerald-600 font-mono">₹1,850.00</span>
      </div>
      <div class="px-3.5 py-1.5 rounded-xl bg-slate-100/80 border border-slate-200/80 flex items-center gap-1.5 font-medium text-slate-700">
        <i data-lucide="wifi" class="w-3.5 h-3.5 text-sky-500"></i>
        <span>Wi-Fi Adapter:</span>
        <span class="font-bold text-sky-700 font-mono">RTL8188EUS</span>
      </div>
      <div class="px-3.5 py-1.5 rounded-xl bg-purple-50/80 border border-purple-200/80 flex items-center gap-1.5 font-medium text-purple-700">
        <i data-lucide="smartphone" class="w-3.5 h-3.5 text-purple-500"></i>
        <span>Mobile Bridge:</span>
        <span class="font-bold text-purple-800 font-mono">http://192.168.1.115:5000</span>
      </div>
    </div>
  </header>

  <!-- MAIN 2-COLUMN GRID -->
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
    
    <!-- LEFT COLUMN: ONE-CLICK ATTACK INJECTOR (5 Cols) -->
    <div class="lg:col-span-5 space-y-5">
      
      <!-- One-Click Attack Triggers Card -->
      <div class="glass-panel rounded-3xl p-6 border-l-4 border-l-rose-500">
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <div class="w-7 h-7 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
              <i data-lucide="zap" class="w-4 h-4"></i>
            </div>
            <h2 class="text-sm font-bold text-slate-900 uppercase tracking-wider">Attack Scenarios</h2>
          </div>
          <span class="text-[10px] font-semibold text-slate-400 uppercase tracking-widest">Instant Inject</span>
        </div>
        <p class="text-xs text-slate-500 mb-4 leading-relaxed">
          Simulate hostile cyber threats directly against the backend engine to observe multi-vector behavioral defense and explainable factor attribution.
        </p>

        <div class="space-y-2.5">
          <!-- Scenario 1: Rogue Emulator -->
          <button onclick="simulateAttack(1)" class="w-full text-left p-3.5 rounded-2xl bg-white border border-slate-200/80 hover:border-rose-400 hover:shadow-md transition-all flex items-center justify-between group">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center font-bold text-lg">
                🚨
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <p class="text-xs font-bold text-slate-900 group-hover:text-rose-600 transition">3:15 AM Rogue Cloud Emulator</p>
                  <span class="px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-rose-100 text-rose-700">99.4% CRIT</span>
                </div>
                <p class="text-[11px] text-slate-500 mt-0.5">₹75,000 P2P • Linux Android Cloud Emulator • Deep Sleep Window</p>
              </div>
            </div>
            <i data-lucide="chevron-right" class="w-4 h-4 text-slate-300 group-hover:text-rose-500 group-hover:translate-x-0.5 transition"></i>
          </button>

          <!-- Scenario 2: Moscow Geo-Jump -->
          <button onclick="simulateAttack(2)" class="w-full text-left p-3.5 rounded-2xl bg-white border border-slate-200/80 hover:border-sky-400 hover:shadow-md transition-all flex items-center justify-between group">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-sky-50 text-sky-600 flex items-center justify-center font-bold text-lg">
                ⚡
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <p class="text-xs font-bold text-slate-900 group-hover:text-sky-600 transition">Hypersonic Moscow Geo-Jump</p>
                  <span class="px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-sky-100 text-sky-700">98.8% CRIT</span>
                </div>
                <p class="text-[11px] text-slate-500 mt-0.5">₹32,000 P2P • 1,800+ km/h Flight Velocity • Impossible Travel</p>
              </div>
            </div>
            <i data-lucide="chevron-right" class="w-4 h-4 text-slate-300 group-hover:text-sky-500 group-hover:translate-x-0.5 transition"></i>
          </button>

          <!-- Scenario 3: Botnet Micro-Carding -->
          <button onclick="simulateAttack(3)" class="w-full text-left p-3.5 rounded-2xl bg-white border border-slate-200/80 hover:border-amber-400 hover:shadow-md transition-all flex items-center justify-between group">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-lg">
                🤖
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <p class="text-xs font-bold text-slate-900 group-hover:text-amber-600 transition">Botnet Micro-Carding Burst</p>
                  <span class="px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-amber-100 text-amber-700">86.2% HIGH</span>
                </div>
                <p class="text-[11px] text-slate-500 mt-0.5">14 micro-transactions / 60s • Automated Crypto Script Drain</p>
              </div>
            </div>
            <i data-lucide="chevron-right" class="w-4 h-4 text-slate-300 group-hover:text-amber-500 group-hover:translate-x-0.5 transition"></i>
          </button>

          <!-- Scenario 0: Legitimate Routine Transfer -->
          <button onclick="simulateAttack(0)" class="w-full text-left p-3.5 rounded-2xl bg-white border border-slate-200/80 hover:border-emerald-400 hover:shadow-md transition-all flex items-center justify-between group">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center font-bold text-lg">
                ✅
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <p class="text-xs font-bold text-slate-900 group-hover:text-emerald-600 transition">Legitimate Routine Lunch</p>
                  <span class="px-1.5 py-0.5 rounded text-[9px] font-extrabold bg-emerald-100 text-emerald-700">0.0% SAFE</span>
                </div>
                <p class="text-[11px] text-slate-500 mt-0.5">₹450 Food & Dining • Trusted Samsung S23 • Baseline Learns</p>
              </div>
            </div>
            <i data-lucide="chevron-right" class="w-4 h-4 text-slate-300 group-hover:text-emerald-500 group-hover:translate-x-0.5 transition"></i>
          </button>
        </div>
      </div>

      <!-- Custom Vector Injection Form -->
      <div class="glass-panel rounded-3xl p-6">
        <h3 class="text-xs font-bold text-slate-900 mb-3 flex items-center gap-2 uppercase tracking-wider">
          <i data-lucide="sliders" class="w-3.5 h-3.5 text-sky-600"></i> Custom Vector Injection
        </h3>
        <div class="space-y-3 text-xs">
          <div>
            <label class="text-slate-500 font-semibold mb-1 block">Amount (₹)</label>
            <input type="number" id="cust-amount" value="50000" class="w-full p-2.5 rounded-xl border border-slate-200 bg-white font-mono font-bold text-slate-800 focus:outline-none focus:border-sky-500">
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-slate-500 font-semibold mb-1 block">Category</label>
              <select id="cust-cat" class="w-full p-2.5 rounded-xl border border-slate-200 bg-white font-semibold text-slate-800 focus:outline-none focus:border-sky-500">
                <option value="P2P_Transfer">P2P_Transfer</option>
                <option value="Gaming_Crypto">Gaming_Crypto</option>
                <option value="Electronics_Gadgets">Electronics_Gadgets</option>
                <option value="Food_Dining">Food_Dining</option>
              </select>
            </div>
            <div>
              <label class="text-slate-500 font-semibold mb-1 block">City</label>
              <select id="cust-city" class="w-full p-2.5 rounded-xl border border-slate-200 bg-white font-semibold text-slate-800 focus:outline-none focus:border-sky-500">
                <option value="Bengaluru">Bengaluru (Home)</option>
                <option value="Mumbai">Mumbai (Trusted)</option>
                <option value="Moscow">Moscow (Foreign)</option>
                <option value="Lagos">Lagos (Foreign)</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-slate-500 font-semibold mb-1 block">Device ID</label>
              <input type="text" id="cust-dev" value="DEV_UNREGISTERED_88" class="w-full p-2.5 rounded-xl border border-slate-200 bg-white font-mono text-slate-800 focus:outline-none focus:border-sky-500">
            </div>
            <div>
              <label class="text-slate-500 font-semibold mb-1 block">Hour (0-23 IST)</label>
              <input type="number" id="cust-hour" value="3" min="0" max="23" class="w-full p-2.5 rounded-xl border border-slate-200 bg-white font-mono text-slate-800 focus:outline-none focus:border-sky-500">
            </div>
          </div>
          <div class="flex gap-2 mt-2">
            <button onclick="injectCustomAttack()" class="flex-1 py-3 rounded-xl btn-gradient-primary font-bold text-xs tracking-wide shadow-md flex items-center justify-center gap-1.5">
              <i data-lucide="play" class="w-3.5 h-3.5"></i> Evaluate Custom
            </button>
            <button onclick="copyCurlCommand()" title="Copy cURL Command to Clipboard" class="px-4 py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs border border-slate-200 transition flex items-center justify-center gap-1">
              <i data-lucide="terminal" class="w-3.5 h-3.5 text-slate-600"></i> cURL
            </button>
          </div>
        </div>
      </div>

    </div>

    <!-- RIGHT COLUMN: LIVE THREAT FORENSICS & REASONING (7 Cols) -->
    <div class="lg:col-span-7 space-y-5">
      
      <!-- Active Verdict Card -->
      <div id="verdict-card" class="glass-panel-hero rounded-3xl p-6 sm:p-7 border border-white/80 transition-all">
        <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-5">
          <div class="flex items-center gap-3.5">
            <div id="verdict-icon-box" class="w-14 h-14 rounded-2xl bg-white/90 border border-slate-200/80 shadow-sm flex items-center justify-center text-3xl font-bold">
              🛡️
            </div>
            <div>
              <div class="flex items-center gap-2">
                <span id="verdict-tier" class="text-[10px] font-extrabold tracking-widest uppercase px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">STANDBY</span>
                <span id="verdict-time" class="text-[11px] text-slate-400 font-mono">00:00:00</span>
              </div>
              <h2 id="verdict-diag" class="text-base sm:text-lg font-extrabold text-slate-900 mt-0.5">Awaiting Simulation Trigger...</h2>
            </div>
          </div>

          <!-- Circular SVG Threat Gauge -->
          <div class="flex items-center gap-3">
            <div class="relative w-16 h-16 flex items-center justify-center">
              <svg class="w-16 h-16 transform -rotate-90" viewBox="0 0 36 36">
                <path class="text-slate-200" stroke-width="3" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                <path id="gauge-path" class="gauge-circle text-emerald-500" stroke-dasharray="100, 100" stroke-dashoffset="100" stroke-width="3.2" stroke-linecap="round" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              </svg>
              <div class="absolute flex flex-col items-center justify-center">
                <span id="verdict-gauge-num" class="text-xs font-black font-mono text-slate-800">0%</span>
              </div>
            </div>
            <div>
              <span class="text-[10px] text-slate-400 font-semibold uppercase tracking-wider block">Risk Score</span>
              <span id="verdict-score" class="text-2xl font-extrabold font-mono text-slate-900">0.0 <span class="text-xs text-slate-400">/ 100</span></span>
            </div>
          </div>
        </div>

        <!-- Action Recommendation Banner -->
        <div id="verdict-action-banner" class="p-3.5 rounded-2xl bg-white/80 border border-slate-200/80 text-xs font-semibold text-slate-700 mb-4 flex items-center justify-between shadow-sm">
          <div class="flex items-center gap-2">
            <i data-lucide="shield-check" class="w-4 h-4 text-emerald-600"></i>
            <span>Action Recommendation:</span>
          </div>
          <span id="verdict-action" class="font-extrabold text-slate-900 font-mono tracking-wider px-2.5 py-0.5 rounded-lg bg-slate-100">STANDBY</span>
        </div>

        <!-- Narrative Explanation Card -->
        <div class="p-4 rounded-2xl bg-white border border-slate-200/80 mb-4 shadow-sm">
          <h4 class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1">Plain-English Forensic Explanation</h4>
          <p id="verdict-narrative" class="text-xs text-slate-700 leading-relaxed font-normal">
            Click any attack scenario on the left or enter custom parameters to observe real-time feature extraction, probability scoring, and behavioral factor attribution.
          </p>
        </div>

        <!-- Attributed Threat Vectors Breakdown -->
        <div>
          <h4 class="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">Attributed Threat Vectors</h4>
          <div id="verdict-factors" class="space-y-2">
            <p class="text-xs text-slate-400 italic">No transaction evaluated yet.</p>
          </div>
        </div>
      </div>

      <!-- Real-Time Evaluation History Stream -->
      <div class="glass-panel rounded-3xl p-6">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 mb-3.5">
          <div class="flex items-center gap-2">
            <h3 class="text-xs font-bold text-slate-900 flex items-center gap-2 uppercase tracking-wider">
              <i data-lucide="history" class="w-3.5 h-3.5 text-slate-500"></i> Real-time Evaluation Stream
            </h3>
            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[9px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200" id="live-polling-badge">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Auto-Sync
            </span>
          </div>
          <!-- Filter Tabs -->
          <div class="flex items-center gap-1 p-0.5 bg-slate-100/90 rounded-xl text-[10px] font-semibold text-slate-600 border border-slate-200/60 self-start sm:self-auto">
            <button onclick="setHistoryFilter('ALL')" id="filter-btn-ALL" class="px-2.5 py-1 rounded-lg bg-white text-slate-900 shadow-sm font-bold">All</button>
            <button onclick="setHistoryFilter('CRITICAL')" id="filter-btn-CRITICAL" class="px-2.5 py-1 rounded-lg hover:text-slate-900">Blocked</button>
            <button onclick="setHistoryFilter('LOW')" id="filter-btn-LOW" class="px-2.5 py-1 rounded-lg hover:text-slate-900">Verified</button>
          </div>
        </div>

        <div id="history-container" class="space-y-2 max-h-[240px] overflow-y-auto pr-1 custom-scroll">
          <p class="text-xs text-slate-400 italic">No events recorded in this session.</p>
        </div>
      </div>

    </div>

  </div>

  <!-- FLOATING TOAST NOTIFICATION -->
  <div id="toast" class="fixed bottom-6 right-6 p-4 rounded-2xl bg-slate-900 text-white text-xs font-semibold shadow-2xl flex items-center gap-3 transition-all duration-300 opacity-0 pointer-events-none translate-y-3 z-50">
    <div id="toast-icon">ℹ️</div>
    <span id="toast-msg">Transaction Evaluated</span>
  </div>

  <script>
    lucide.createIcons();

    function showToast(msg, icon = '⚡') {
      const toast = document.getElementById('toast');
      document.getElementById('toast-msg').innerText = msg;
      document.getElementById('toast-icon').innerText = icon;
      toast.classList.remove('opacity-0', 'pointer-events-none', 'translate-y-3');
      toast.classList.add('opacity-100', 'translate-y-0');
      setTimeout(() => {
        toast.classList.remove('opacity-100', 'translate-y-0');
        toast.classList.add('opacity-0', 'pointer-events-none', 'translate-y-3');
      }, 2500);
    }

    async function simulateAttack(scenarioId) {
      try {
        const res = await fetch('/api/simulate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario: scenarioId })
        });
        const data = await res.json();
        renderVerdict(data);
        fetchHistory();
        showToast(`Simulation Triggered: ${data.evaluation.anomaly_diagnosis}`, scenarioId === 0 ? '✅' : '🚨');
      } catch (err) {
        alert("Server error: " + err);
      }
    }

    async function injectCustomAttack() {
      const payload = {
        amount: parseFloat(document.getElementById('cust-amount').value),
        merchant_category: document.getElementById('cust-cat').value,
        location_city: document.getElementById('cust-city').value,
        device_id: document.getElementById('cust-dev').value,
        hour: parseInt(document.getElementById('cust-hour').value)
      };

      try {
        const res = await fetch('/api/evaluate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await res.json();
        renderVerdict(data);
        fetchHistory();
        showToast(`Custom Payload Evaluated: ${data.evaluation.risk_tier} (${data.evaluation.risk_score}%)`, '🔍');
      } catch (err) {
        alert("Server error: " + err);
      }
    }

    function renderVerdict(record) {
      const evalData = record.evaluation;
      const score = evalData.risk_score;
      const tier = evalData.risk_tier;

      document.getElementById('verdict-score').innerHTML = `${score.toFixed(1)} <span class="text-xs text-slate-400">/ 100</span>`;
      document.getElementById('verdict-gauge-num').innerText = `${Math.round(score)}%`;
      document.getElementById('verdict-tier').innerText = `${tier}`;
      document.getElementById('verdict-diag').innerText = evalData.anomaly_diagnosis.replace(/_/g, ' ');
      document.getElementById('verdict-action').innerText = evalData.action_recommendation;
      document.getElementById('verdict-narrative').innerText = evalData.summary_narrative;
      document.getElementById('verdict-time').innerText = record.timestamp ? record.timestamp.split(' ')[1] : new Date().toLocaleTimeString();

      // Gauge Animation
      const gauge = document.getElementById('gauge-path');
      const offset = 100 - score;
      gauge.style.strokeDashoffset = offset;

      const card = document.getElementById('verdict-card');
      const iconBox = document.getElementById('verdict-icon-box');
      const actionBanner = document.getElementById('verdict-action-banner');

      if (tier === 'CRITICAL' || tier === 'HIGH') {
        gauge.setAttribute('class', 'gauge-circle text-rose-500');
        iconBox.innerHTML = "🚨";
        iconBox.className = "w-14 h-14 rounded-2xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center text-3xl font-bold shadow-sm";
        actionBanner.className = "p-3.5 rounded-2xl bg-rose-50/80 border border-rose-200 text-xs font-semibold text-rose-900 mb-4 flex items-center justify-between shadow-sm";
        document.getElementById('verdict-tier').className = "text-[10px] font-extrabold tracking-widest uppercase px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-700 border border-rose-200";
      } else if (tier === 'MEDIUM') {
        gauge.setAttribute('class', 'gauge-circle text-amber-500');
        iconBox.innerHTML = "⚠️";
        iconBox.className = "w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 flex items-center justify-center text-3xl font-bold shadow-sm";
        actionBanner.className = "p-3.5 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs font-semibold text-amber-900 mb-4 flex items-center justify-between shadow-sm";
        document.getElementById('verdict-tier').className = "text-[10px] font-extrabold tracking-widest uppercase px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200";
      } else {
        gauge.setAttribute('class', 'gauge-circle text-emerald-500');
        iconBox.innerHTML = "✅";
        iconBox.className = "w-14 h-14 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-600 flex items-center justify-center text-3xl font-bold shadow-sm";
        actionBanner.className = "p-3.5 rounded-2xl bg-emerald-50/80 border border-emerald-200 text-xs font-semibold text-emerald-900 mb-4 flex items-center justify-between shadow-sm";
        document.getElementById('verdict-tier').className = "text-[10px] font-extrabold tracking-widest uppercase px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200";
      }

      // Factors List with Visual Progress Bars
      const factorsDiv = document.getElementById('verdict-factors');
      factorsDiv.innerHTML = '';
      if (evalData.factors && evalData.factors.length > 0) {
        evalData.factors.forEach(f => {
          const isCrit = f.severity === 'CRITICAL' || f.severity === 'ELEVATED';
          const badgeClass = isCrit ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200';
          const barColor = isCrit ? 'bg-rose-500' : 'bg-emerald-500';
          const barPct = Math.min(100, Math.max(10, f.contribution * 2));
          factorsDiv.innerHTML += `
            <div class="p-3.5 rounded-2xl bg-white border border-slate-200/80 shadow-sm text-xs">
              <div class="flex items-start justify-between gap-3 mb-1.5">
                <div>
                  <p class="font-bold text-slate-800">${f.factor}</p>
                  <p class="text-[11px] text-slate-500 leading-snug mt-0.5">${f.insight}</p>
                </div>
                <span class="px-2 py-0.5 rounded-md text-[10px] font-bold border ${badgeClass} shrink-0">
                  ${f.severity}
                </span>
              </div>
              <div class="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                <div class="h-1.5 rounded-full ${barColor} progress-bar-fill" style="width: ${barPct}%"></div>
              </div>
            </div>
          `;
        });
      } else {
        factorsDiv.innerHTML = '<p class="text-xs text-slate-400">No anomaly factors detected.</p>';
      }

      lucide.createIcons();
    }

    function copyCurlCommand() {
      const amt = document.getElementById('cust-amount').value;
      const cat = document.getElementById('cust-cat').value;
      const city = document.getElementById('cust-city').value;
      const dev = document.getElementById('cust-dev').value;
      const hour = document.getElementById('cust-hour').value;
      const curlCmd = `curl -X POST http://localhost:5000/api/evaluate \\
  -H "Content-Type: application/json" \\
  -d '{"amount": ${amt}, "merchant_category": "${cat}", "location_city": "${city}", "device_id": "${dev}", "hour": ${hour}}'`;
      if (navigator.clipboard) {
        navigator.clipboard.writeText(curlCmd).then(() => {
          showToast("cURL Command Copied to Clipboard!", "📋");
        }).catch(() => {
          prompt("Copy cURL Command:", curlCmd);
        });
      } else {
        prompt("Copy cURL Command:", curlCmd);
      }
    }

    let currentFilter = 'ALL';
    let allHistoryRecords = [];

    function setHistoryFilter(filter) {
      currentFilter = filter;
      ['ALL', 'CRITICAL', 'LOW'].forEach(f => {
        const btn = document.getElementById(`filter-btn-${f}`);
        if (btn) {
          if (f === filter) {
            btn.className = "px-2.5 py-1 rounded-lg bg-white text-slate-900 shadow-sm font-bold";
          } else {
            btn.className = "px-2.5 py-1 rounded-lg hover:text-slate-900";
          }
        }
      });
      renderHistoryItems();
    }

    function renderHistoryItems() {
      const container = document.getElementById('history-container');
      if (!allHistoryRecords || allHistoryRecords.length === 0) {
        container.innerHTML = '<p class="text-xs text-slate-400 italic">No events recorded in this session.</p>';
        return;
      }

      const filtered = allHistoryRecords.filter(item => {
        if (currentFilter === 'ALL') return true;
        if (currentFilter === 'CRITICAL') return item.evaluation.risk_tier === 'CRITICAL' || item.evaluation.risk_tier === 'HIGH';
        if (currentFilter === 'LOW') return item.evaluation.risk_tier === 'LOW';
        return true;
      });

      if (filtered.length === 0) {
        container.innerHTML = `<p class="text-xs text-slate-400 italic p-2">No events matching "${currentFilter}".</p>`;
        return;
      }

      container.innerHTML = '';
      filtered.slice(0, 25).forEach((item, idx) => {
        const isHigh = item.evaluation.risk_tier === 'CRITICAL' || item.evaluation.risk_tier === 'HIGH';
        const colorClass = isHigh ? 'text-rose-600' : 'text-emerald-600';
        const badgeBg = isHigh ? 'bg-rose-100 text-rose-700' : 'bg-emerald-100 text-emerald-700';
        const itemJson = encodeURIComponent(JSON.stringify(item));
        container.innerHTML += `
          <div onclick="inspectHistoryItem('${itemJson}')" class="p-3 rounded-2xl bg-white border border-slate-200/80 flex items-center justify-between text-xs hover:border-sky-400 hover:shadow-sm cursor-pointer transition group">
            <div>
              <span class="font-bold text-slate-800 font-mono">₹${item.amount.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
              <span class="text-[11px] text-slate-400 ml-2">${item.merchant_category} • ${item.location_city}</span>
              <span class="text-[10px] text-slate-300 ml-1.5 font-mono">${item.timestamp ? item.timestamp.split(' ')[1] : ''}</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="font-mono font-bold ${colorClass}">${item.evaluation.risk_score.toFixed(1)}%</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${badgeBg}">${item.evaluation.risk_tier}</span>
              <i data-lucide="chevron-right" class="w-3.5 h-3.5 text-slate-300 group-hover:text-sky-500 group-hover:translate-x-0.5 transition"></i>
            </div>
          </div>
        `;
      });
      lucide.createIcons();
    }

    function inspectHistoryItem(encodedJson) {
      try {
        const record = JSON.parse(decodeURIComponent(encodedJson));
        renderVerdict(record);
        showToast(`Viewing Forensic Record: ${record.evaluation.anomaly_diagnosis}`, '🔎');
      } catch (e) {
        console.error("Failed to parse record:", e);
      }
    }

    async function fetchHistory() {
      try {
        const res = await fetch('/api/history');
        const list = await res.json();
        allHistoryRecords = list;
        renderHistoryItems();
      } catch (e) {}
    }

    // Initial load & automatic polling every 3 seconds for live mobile telemetry
    fetchHistory();
    setInterval(fetchHistory, 3000);
  </script>
</body>
</html>
"""

class SentinelServerHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Quiet log
        pass

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            status_data = {
                "server": "SentinelUPI Threat Server",
                "status": "ONLINE",
                "host": "localhost",
                "port": 5000,
                "profile": {
                    "user_id": default_profile.user_id,
                    "ewma_mean": default_profile.ewma_mean,
                    "ewma_std": default_profile.ewma_std,
                    "alpha": default_profile.alpha,
                    "trusted_devices": default_profile.trusted_devices,
                    "trusted_cities": default_profile.trusted_cities
                },
                "model_trained": fraud_model.is_trained(),
                "history_count": len(evaluation_history)
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
        elif self.path == "/api/history":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(evaluation_history).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        if self.path == "/api/simulate":
            scenario_id = int(data.get("scenario", 1))
            txn = generate_scenario_transaction(scenario_id, default_profile)
            record = process_transaction(txn, default_profile)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(record).encode("utf-8"))

        elif self.path == "/api/evaluate":
            # Direct transaction evaluation
            if "hour" in data:
                now = datetime.now()
                hour = int(data["hour"])
                data["timestamp_dt"] = now.replace(hour=hour, minute=0, second=0)
            record = process_transaction(data, default_profile)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(record).encode("utf-8"))

        else:
            self.send_response(404)
            self.end_headers()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

def run_server(port: int = 5000):
    server_address = ("0.0.0.0", port)
    httpd = ThreadedHTTPServer(server_address, SentinelServerHandler)
    print(f"[*] SentinelUPI Server running at http://localhost:{port}/")
    print(f"[*] Serving attack simulation and behavioral engine to local LAN and browser...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server stopped.")
        httpd.server_close()

if __name__ == "__main__":
    p = 5000
    if len(sys.argv) > 1:
        p = int(sys.argv[1])
    run_server(p)
