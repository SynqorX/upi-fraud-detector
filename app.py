"""
SentinelUPI: Interactive Streamlit Web Interface
Adaptive UPI Fraud Detection & Explainable Attribution Dashboard
"""

import os
import json
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

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

# Page configuration
st.set_page_config(
    page_title="SentinelUPI | Adaptive Fraud Detection",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .factor-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        margin-right: 8px;
    }
    .pill-critical { background-color: #FEE2E2; color: #991B1B; }
    .pill-elevated { background-color: #FEF3C7; color: #92400E; }
    .pill-normal { background-color: #ECFDF5; color: #065F46; }
    .pill-trusted { background-color: #EFF6FF; color: #1E40AF; }
</style>
""", unsafe_allow_html=True)


# Session state initialization
if "profile_manager" not in st.session_state:
    pm = ProfileManager()
    if os.path.exists("data/transactions.csv"):
        try:
            df_init = pd.read_csv("data/transactions.csv")
            pm.load_from_dataframe(df_init)
        except Exception:
            pass
    st.session_state.profile_manager = pm

if "model" not in st.session_state:
    model = FraudModel()
    model.load_or_train_default(generate_synthetic_upi_dataset)
    st.session_state.model = model

if "drift_history" not in st.session_state:
    first_user_id = list(st.session_state.profile_manager.profiles.keys())[0]
    u = st.session_state.profile_manager.get_or_create(first_user_id)
    st.session_state.drift_history = [
        {"step": 1, "txn_amount": round(u.ewma_mean * 0.9, 2), "ewma_mean": round(u.ewma_mean, 2), "ewma_std": round(u.ewma_std, 2), "event": "Routine Grocery"},
        {"step": 2, "txn_amount": round(u.ewma_mean * 1.05, 2), "ewma_mean": round(u.ewma_mean * 1.01, 2), "ewma_std": round(u.ewma_std * 0.98, 2), "event": "Dinner with friends"},
        {"step": 3, "txn_amount": round(u.ewma_mean * 1.15, 2), "ewma_mean": round(u.ewma_mean * 1.02, 2), "ewma_std": round(u.ewma_std * 0.97, 2), "event": "Fuel & commuting"},
        {"step": 4, "txn_amount": round(u.ewma_mean * 0.95, 2), "ewma_mean": round(u.ewma_mean * 1.01, 2), "ewma_std": round(u.ewma_std * 0.96, 2), "event": "Online order"}
    ]

# Sidebar
st.sidebar.title("🛡️ SentinelUPI Control")
st.sidebar.caption("Adaptive Fraud Detection Without Blind Alerts")

nav_choice = st.sidebar.radio(
    "Navigation",
    ["Live Transaction Simulator", "🚨 Real-Time Stream & Wrong Guesses", "Adaptive Baseline & Drift", "Model Studio & Training", "Dataset Specification & AI Prompt"]
)

# Sidebar User Selector
st.sidebar.markdown("---")
st.sidebar.subheader("Active User Profile")
available_users = list(st.session_state.profile_manager.profiles.keys())
selected_user_id = st.sidebar.selectbox("Select User Profile", available_users, index=0)
active_profile = st.session_state.profile_manager.get_or_create(selected_user_id)

st.sidebar.markdown(f"**Baseline Mean:** ₹{active_profile.ewma_mean:,.2f}")
st.sidebar.markdown(f"**Std Dev (σ):** ₹{active_profile.ewma_std:,.2f}")
st.sidebar.markdown(f"**Trusted Devices:** {len(active_profile.trusted_devices)}")
st.sidebar.markdown(f"**Trusted Cities:** {', '.join(active_profile.trusted_cities)}")


# =====================================================================
# TAB 1: LIVE TRANSACTION SIMULATOR
# =====================================================================
if nav_choice == "Live Transaction Simulator":
    st.markdown('<div class="main-header">🛡️ Live Transaction Risk & Attribution Inspector</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Inspect incoming UPI transactions in real-time with plain-English factor explainability (No Blind Alerts).</div>', unsafe_allow_html=True)

    # Preset Quick-Load Scenarios
    st.markdown("##### ⚡ Quick Scenarios")
    sc_cols = st.columns(4)
    preset_scenario = None

    if sc_cols[0].button("🛒 1. Normal Chai/Groceries"):
        preset_scenario = {
            "amount": 280.0,
            "category": "Groceries_Daily",
            "device_id": list(active_profile.trusted_devices.keys())[0],
            "device_model": list(active_profile.trusted_devices.values())[0],
            "city": active_profile.trusted_cities[0],
            "hour": 14,
            "minute": 20,
            "burst": 1
        }
    if sc_cols[1].button("✨ 2. Benign Festive Spend (Diwali)"):
        preset_scenario = {
            "amount": 14500.0,
            "category": "Electronics_Gadgets",
            "device_id": list(active_profile.trusted_devices.keys())[0],
            "device_model": list(active_profile.trusted_devices.values())[0],
            "city": active_profile.trusted_cities[0],
            "hour": 18,
            "minute": 45,
            "burst": 2
        }
    if sc_cols[2].button("✈️ 3. Benign Travel (Goa Trip)"):
        preset_scenario = {
            "amount": 3400.0,
            "category": "Food_Dining",
            "device_id": list(active_profile.trusted_devices.keys())[0],
            "device_model": list(active_profile.trusted_devices.values())[0],
            "city": "Goa",
            "hour": 20,
            "minute": 15,
            "burst": 1
        }
    if sc_cols[3].button("🚨 4. Hostile Takeover (3 AM / Moscow)"):
        preset_scenario = {
            "amount": 65000.0,
            "category": "P2P_Transfer",
            "device_id": "DEV_ROGUE_777",
            "device_model": "Linux Cloud Emulator",
            "city": "Moscow",
            "hour": 3,
            "minute": 15,
            "burst": 4
        }

    # Simulation Form
    with st.expander("📝 Transaction Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)

        default_amount = preset_scenario["amount"] if preset_scenario else float(active_profile.ewma_mean)
        default_cat = preset_scenario["category"] if preset_scenario else "Groceries_Daily"
        default_city = preset_scenario["city"] if preset_scenario else active_profile.trusted_cities[0]
        default_dev_id = preset_scenario["device_id"] if preset_scenario else list(active_profile.trusted_devices.keys())[0]
        default_dev_model = preset_scenario["device_model"] if preset_scenario else list(active_profile.trusted_devices.values())[0]
        default_hour = preset_scenario["hour"] if preset_scenario else 15
        default_burst = preset_scenario["burst"] if preset_scenario else 1

        with col1:
            inp_amount = st.number_input("Transaction Amount (INR ₹)", min_value=1.0, max_value=200000.0, value=float(default_amount), step=100.0)
            inp_category = st.selectbox("Merchant Category", MERCHANT_CATEGORIES, index=MERCHANT_CATEGORIES.index(default_cat) if default_cat in MERCHANT_CATEGORIES else 0)

        with col2:
            city_list = list(INDIAN_CITIES.keys())
            inp_city = st.selectbox("Transaction City", city_list, index=city_list.index(default_city) if default_city in city_list else 0)
            inp_device_id = st.text_input("Device ID Hardware Hash", value=default_dev_id)
            inp_device_model = st.text_input("Device Model Name", value=default_dev_model)

        with col3:
            inp_hour = st.slider("Execution Time (Hour IST 0-23)", 0, 23, int(default_hour))
            inp_minute = st.slider("Minute", 0, 59, 30)
            inp_burst = st.number_input("Burst Velocity (Txns in last 60m)", min_value=1, max_value=20, value=int(default_burst))

        btn_analyze = st.button("🔍 Evaluate Transaction", type="primary", width="stretch")

    # Process evaluation
    txn_time_dt = datetime.now().replace(hour=inp_hour, minute=inp_minute)
    txn_dict = {
        "amount": inp_amount,
        "merchant_category": inp_category,
        "device_id": inp_device_id,
        "device_model": inp_device_model,
        "location_city": inp_city,
        "timestamp_dt": txn_time_dt,
        "timestamp": txn_time_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "txn_velocity_1h": inp_burst
    }

    features = FeatureExtractor.extract_features(active_profile, txn_dict)
    risk_score, risk_tier = st.session_state.model.predict_risk(features)
    explanation = ExplainabilityEngine.generate_explanation(active_profile, txn_dict, features, risk_score, risk_tier)

    st.markdown("---")
    res_col1, res_col2 = st.columns([1, 2])

    with res_col1:
        st.markdown("#### 🎯 Risk Verdict")

        # Color-coded risk gauge
        if risk_tier == "LOW":
            tier_color = "#10B981"
            badge = "✅ APPROVED"
        elif risk_tier == "MEDIUM":
            tier_color = "#F59E0B"
            badge = "⚠️ ADVISORY / STEP-UP"
        elif risk_tier == "HIGH":
            tier_color = "#EF4444"
            badge = "🛑 HIGH RISK CHALLENGE"
        else:
            tier_color = "#7F1D1D"
            badge = "⛔ CRITICAL BLOCK"

        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"<b>{badge}</b><br><span style='font-size:0.85em;color:#64748B'>{explanation['anomaly_diagnosis']}</span>"},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': tier_color},
                'steps': [
                    {'range': [0, 30], 'color': '#ECFDF5'},
                    {'range': [30, 65], 'color': '#FFFBEB'},
                    {'range': [65, 85], 'color': '#FEF2F2'},
                    {'range': [85, 100], 'color': '#FEE2E2'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 3},
                    'thickness': 0.75,
                    'value': risk_score
                }
            }
        ))
        fig_gauge.update_layout(height=260, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_gauge, width="stretch")

        st.info(f"**Action Recommended:** `{explanation['action_recommendation']}`")

    with res_col2:
        st.markdown("#### 🔍 Explainability Attribution Card (No Blind Alerts)")
        st.markdown(f"**Executive Diagnostic:**\n> {explanation['summary_narrative']}")

        st.markdown("##### Detailed Contributing Factors:")
        for factor in explanation["factors"]:
            sev = factor["severity"]
            pill_class = f"pill-{sev.lower()}"
            st.markdown(f"""
            <div style="margin-bottom: 8px; padding: 10px; background: #FFFFFF; border-left: 4px solid {'#EF4444' if sev == 'CRITICAL' else '#F59E0B' if sev == 'ELEVATED' else '#10B981'}; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                <span class="factor-pill {pill_class}">{factor['factor']}</span>
                <span style="font-weight: 500; font-size: 0.95rem;">{factor['insight']}</span>
            </div>
            """, unsafe_allow_html=True)

    # Attribution Breakdown Chart
    st.markdown("##### 📊 Factor Risk Contribution Breakdown")
    attr = explanation["attribution_breakdown"]
    df_attr = pd.DataFrame({
        "Factor": [k.replace("_", " ").title() for k in attr.keys()],
        "Contribution (%)": list(attr.values())
    })
    fig_bar = px.bar(
        df_attr, x="Contribution (%)", y="Factor", orientation="h",
        color="Contribution (%)", color_continuous_scale="Reds",
        range_x=[0, 100], text="Contribution (%)"
    )
    fig_bar.update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20), yaxis={'autorange': 'reversed'})
    st.plotly_chart(fig_bar, width="stretch")

    # Human-in-the-Loop Concept Drift Adaptation Controls
    st.markdown("---")
    st.markdown("#### 🔄 Human-in-the-Loop Drift Recalibration")
    st.caption("When a benign anomaly is approved by the user, the baseline immediately recalibrates to prevent recurring false alarms.")

    fb_col1, fb_col2 = st.columns(2)
    with fb_col1:
        if st.button("✅ Confirm Legitimate (Adapt Baseline & Register Device/City)", type="primary", width="stretch"):
            old_mean = active_profile.ewma_mean
            old_std = active_profile.ewma_std
            active_profile.update_baseline(
                amount=inp_amount,
                is_feedback_legitimate=True,
                new_device_id=inp_device_id,
                new_device_model=inp_device_model,
                new_city=inp_city
            )
            # Record in drift history
            step_num = len(st.session_state.drift_history) + 1
            st.session_state.drift_history.append({
                "step": step_num,
                "txn_amount": inp_amount,
                "ewma_mean": round(active_profile.ewma_mean, 2),
                "ewma_std": round(active_profile.ewma_std, 2),
                "event": f"Adapted: {inp_category} (₹{inp_amount:,.0f})"
            })
            st.success(
                f"🎉 Baseline Adapted! EWMA Mean shifted from ₹{old_mean:,.2f} ➔ ₹{active_profile.ewma_mean:,.2f} "
                f"(± ₹{active_profile.ewma_std:,.2f}). Device and location added to trusted profile."
            )
            st.rerun()

    with fb_col2:
        if st.button("⛔ Confirm Hostile Fraud (Block & Preserve Baseline)", type="secondary", width="stretch"):
            st.error(f"🚨 Confirmed Fraud! Device '{inp_device_model}' has been blacklisted. Behavioral baseline preserved from contamination.")


# =====================================================================
# TAB 2: REAL-TIME STREAM & WRONG GUESS AUDITOR (PORT 8501)
# =====================================================================
elif nav_choice == "🚨 Real-Time Stream & Wrong Guesses":
    st.markdown('<div class="main-header">🚨 Real-Time Scenario Stream & Wrong Guess Auditor</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Live feed of consecutive transactions, real-time model solves, and automated discrepancy/wrong guess alerts on localhost:8501.</div>', unsafe_allow_html=True)

    from tester import RealtimeStreamGenerator, save_record_to_stream, WRONG_GUESSES_FILE, LIVE_STREAM_FILE

    # Controls
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 1, 1])
    with ctrl_col1:
        st.caption("Transactions streamed from `python tester.py` or triggered below appear here live.")
    with ctrl_col2:
        if st.button("▶️ Stream 11 Consecutive Scenarios", type="primary", width="stretch"):
            streamer = RealtimeStreamGenerator(st.session_state.profile_manager)
            batch = streamer.generate_consecutive_batch()
            for txn in batch:
                u = st.session_state.profile_manager.get_or_create(txn["user_id"])
                feats = FeatureExtractor.extract_features(u, txn)
                r_score, r_tier = st.session_state.model.predict_risk(feats)
                expl = ExplainabilityEngine.generate_explanation(u, txn, feats, r_score, r_tier)
                is_pred_fraud = (r_tier in ["HIGH", "CRITICAL"])
                pred_verdict = "FRAUD" if is_pred_fraud else "LEGITIMATE"
                exp_verdict = txn["expected"]
                is_corr = (pred_verdict == exp_verdict)

                if exp_verdict == "LEGITIMATE" and is_corr:
                    u.update_baseline(txn["amount"], is_feedback_legitimate=False)
                u.record_transaction({
                    "timestamp_dt": txn["timestamp_dt"],
                    "location_city": txn["location_city"],
                    "amount": txn["amount"]
                })

                stream_rec = {
                    "timestamp": txn["timestamp"],
                    "transaction_id": txn["transaction_id"],
                    "user_id": txn["user_id"],
                    "description": txn["description"],
                    "amount": txn["amount"],
                    "user_mean": round(u.ewma_mean, 2),
                    "device": txn["device_model"],
                    "city": txn["location_city"],
                    "hour": txn["timestamp_dt"].strftime("%I:%M %p"),
                    "risk_score": r_score,
                    "risk_tier": r_tier,
                    "predicted": pred_verdict,
                    "expected": exp_verdict,
                    "status": "CORRECT" if is_corr else "WRONG_GUESS",
                    "diagnosis": expl["anomaly_diagnosis"],
                    "factors": [f["insight"] for f in expl["factors"]]
                }
                save_record_to_stream(stream_rec, is_wrong=not is_corr)
            st.success("Streamed 11 consecutive transactions!")
            st.rerun()

    with ctrl_col3:
        if st.button("🗑️ Clear Logs", type="secondary", width="stretch"):
            with open(WRONG_GUESSES_FILE, "w") as f:
                json.dump([], f)
            with open(LIVE_STREAM_FILE, "w") as f:
                json.dump([], f)
            st.rerun()

    # Load logs
    wrong_guesses = []
    live_stream = []
    if os.path.exists(WRONG_GUESSES_FILE):
        try:
            with open(WRONG_GUESSES_FILE, "r") as f:
                wrong_guesses = json.load(f)
        except Exception:
            wrong_guesses = []

    if os.path.exists(LIVE_STREAM_FILE):
        try:
            with open(LIVE_STREAM_FILE, "r") as f:
                live_stream = json.load(f)
        except Exception:
            live_stream = []

    # KPI Metrics
    total_txns = len(live_stream)
    wrong_count = len(wrong_guesses)
    correct_count = total_txns - wrong_count if total_txns >= wrong_count else total_txns
    acc_pct = (correct_count / total_txns * 100.0) if total_txns > 0 else 100.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Streamed Transactions", f"{total_txns}")
    kpi2.metric("Model Solved Correctly", f"{correct_count} ({acc_pct:.1f}%)")
    kpi3.metric("Total Wrong Guesses", f"{wrong_count}", delta=f"{wrong_count} flagged" if wrong_count > 0 else "0", delta_color="inverse")
    fp_count = sum(1 for w in wrong_guesses if w.get("expected") == "LEGITIMATE" and w.get("predicted") == "FRAUD")
    fn_count = sum(1 for w in wrong_guesses if w.get("expected") == "FRAUD" and w.get("predicted") == "LEGITIMATE")
    kpi4.metric("False Alarms / Missed", f"{fp_count} FP / {fn_count} FN")

    # Section 1: Wrong Guesses
    st.markdown("---")
    st.markdown("### ⚠️ Wrong Guess Diagnostic Cards")
    st.caption("Any transaction where the model's prediction mismatched the ground-truth expectation.")

    if not wrong_guesses:
        st.success("🎉 No Wrong Guesses logged yet! Run `python tester.py` in your terminal or click 'Stream 11 Consecutive Scenarios' above to test.")
    else:
        for idx, wg in enumerate(reversed(wrong_guesses)):
            exp = wg.get("expected", "UNKNOWN")
            pred = wg.get("predicted", "UNKNOWN")
            is_fp = (exp == "LEGITIMATE" and pred == "FRAUD")
            box_border = "#F59E0B" if is_fp else "#EF4444"
            badge_title = "⚠️ FALSE ALARM (Blocked Legitimate User)" if is_fp else "🚨 MISSED FRAUD (Fraudster Allowed)"

            with st.container():
                st.markdown(f"""
                <div style="border: 2px solid {box_border}; border-radius: 8px; padding: 14px; margin-bottom: 15px; background: #FFF;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-weight: 700; color: {box_border}; font-size: 1.05rem;">{badge_title}</span>
                        <span style="font-size: 0.85rem; color: #64748B;">{wg.get('timestamp', '')} | ID: {wg.get('transaction_id', '')}</span>
                    </div>
                    <div style="font-size: 1rem; font-weight: 600; margin-bottom: 6px;">{wg.get('description', '')}</div>
                    <div style="font-size: 0.9rem; color: #334155; margin-bottom: 8px;">
                        <b>User:</b> {wg.get('user_id', '')} &nbsp;|&nbsp;
                        <b>Amount:</b> ₹{wg.get('amount', 0):,.2f} (User Avg: ₹{wg.get('user_mean', 0):,.2f}) &nbsp;|&nbsp;
                        <b>Device:</b> {wg.get('device', '')} &nbsp;|&nbsp;
                        <b>City:</b> {wg.get('city', '')} &nbsp;|&nbsp;
                        <b>Risk Score:</b> {wg.get('risk_score', 0)}/100 ({wg.get('risk_tier', '')})
                    </div>
                    <div style="background: #F8FAFC; border-left: 3px solid {box_border}; padding: 8px 12px; font-size: 0.88rem; margin-top: 6px;">
                        <b>Diagnostic Factors:</b> {', '.join(wg.get('factors', []))}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Section 2: Live Stream Feed
    st.markdown("---")
    st.markdown("### 📡 Consecutive Live Stream Feed")
    if live_stream:
        df_stream = pd.DataFrame(live_stream)[["timestamp", "user_id", "description", "amount", "risk_score", "predicted", "expected", "status"]]
        df_stream = df_stream.iloc[::-1].reset_index(drop=True)
        st.dataframe(df_stream, width="stretch")
    else:
        st.info("No stream records recorded yet. Start streaming with `python tester.py` or the button above.")


# =====================================================================
# TAB 3: ADAPTIVE BASELINE & DRIFT
# =====================================================================
elif nav_choice == "Adaptive Baseline & Drift":
    st.markdown('<div class="main-header">📈 Adaptive Baseline & Concept Drift Progression</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Visualizing continuous EWMA spending baselines adapting to user lifestyle changes without false alarm fatigue.</div>', unsafe_allow_html=True)

    df_drift = pd.DataFrame(st.session_state.drift_history)

    # Plotly progression chart
    fig_drift = go.Figure()

    # Upper and Lower bound envelope (Mean +/- 2*Std)
    upper_bound = df_drift["ewma_mean"] + 2.0 * df_drift["ewma_std"]
    lower_bound = np.maximum(0, df_drift["ewma_mean"] - 2.0 * df_drift["ewma_std"])

    fig_drift.add_trace(go.Scatter(
        x=df_drift["step"], y=upper_bound,
        mode='lines', line=dict(width=0),
        showlegend=False, name='Upper Envelope'
    ))
    fig_drift.add_trace(go.Scatter(
        x=df_drift["step"], y=lower_bound,
        mode='lines', line=dict(width=0),
        fill='tonexty', fillcolor='rgba(59, 130, 246, 0.12)',
        name='±2σ Normal Spend Envelope'
    ))

    # EWMA Mean line
    fig_drift.add_trace(go.Scatter(
        x=df_drift["step"], y=df_drift["ewma_mean"],
        mode='lines+markers', line=dict(color='#2563EB', width=3),
        marker=dict(size=8), name='Adaptive EWMA Mean (μ)'
    ))

    # Actual transaction amounts
    fig_drift.add_trace(go.Scatter(
        x=df_drift["step"], y=df_drift["txn_amount"],
        mode='markers+text', marker=dict(color='#EF4444', size=11, symbol='diamond'),
        text=df_drift["event"], textposition="top center",
        name='Recorded Transactions'
    ))

    fig_drift.update_layout(
        title="<b>Dynamic EWMA Spending Baseline vs. Actual Transactions</b>",
        xaxis_title="Transaction Sequence Step",
        yaxis_title="Amount in INR (₹)",
        hovermode="x unified",
        template="plotly_white",
        height=450
    )

    st.plotly_chart(fig_drift, width="stretch")

    st.markdown("##### 📋 Baseline Progression Audit Table")
    st.dataframe(df_drift, width="stretch")

    # Live Drift Experiment Box
    st.markdown("---")
    st.markdown("#### 🧪 Test Rapid Concept Drift")
    st.caption("Simulate 5 consecutive high-value transactions (e.g. user moving into higher salary tier or wedding planning).")

    drift_step_col1, drift_step_col2 = st.columns([2, 1])
    with drift_step_col1:
        bulk_amount = st.slider("Simulated Spend Level (₹)", 5000, 50000, 15000, step=1000)
    with drift_step_col2:
        if st.button("🚀 Push 5 Adapted Transactions", width="stretch"):
            for _ in range(5):
                active_profile.update_baseline(bulk_amount, is_feedback_legitimate=True)
                step_num = len(st.session_state.drift_history) + 1
                st.session_state.drift_history.append({
                    "step": step_num,
                    "txn_amount": bulk_amount,
                    "ewma_mean": round(active_profile.ewma_mean, 2),
                    "ewma_std": round(active_profile.ewma_std, 2),
                    "event": f"Lifestyle Shift (₹{bulk_amount:,.0f})"
                })
            st.success(f"New EWMA Mean is now ₹{active_profile.ewma_mean:,.2f}!")
            st.rerun()


# =====================================================================
# TAB 3: MODEL STUDIO & TRAINING
# =====================================================================
elif nav_choice == "Model Studio & Training":
    st.markdown('<div class="main-header">🧠 Model Studio & Performance Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Train, evaluate, and inspect the machine learning engine on labeled transaction datasets.</div>', unsafe_allow_html=True)

    csv_path = "data/transactions.csv"
    if os.path.exists(csv_path):
        df_loaded = pd.read_csv(csv_path)
    else:
        df_loaded = generate_synthetic_upi_dataset(num_rows=3000)
        os.makedirs("data", exist_ok=True)
        df_loaded.to_csv(csv_path, index=False)

    stat_cols = st.columns(4)
    stat_cols[0].metric("Total Dataset Rows", f"{len(df_loaded):,}")
    stat_cols[1].metric("Legitimate Txns", f"{(df_loaded['is_fraud'] == 0).sum():,}")
    stat_cols[2].metric("Fraudulent Txns", f"{(df_loaded['is_fraud'] == 1).sum():,}")
    stat_cols[3].metric("Fraud Incidence Rate", f"{df_loaded['is_fraud'].mean()*100:.2f}%")

    # Metrics Display
    metrics = st.session_state.model.metrics
    if metrics:
        st.markdown("##### 🏆 Current Test Evaluation Metrics")
        m_cols = st.columns(4)
        m_cols[0].metric("ROC-AUC Score", f"{metrics.get('roc_auc', 0.0):.4f}")
        m_cols[1].metric("Precision", f"{metrics.get('precision', 0.0):.4f}")
        m_cols[2].metric("Recall", f"{metrics.get('recall', 0.0):.4f}")
        m_cols[3].metric("F1-Score", f"{metrics.get('f1_score', 0.0):.4f}")

        # Confusion Matrix & Feature Importances
        viz_col1, viz_col2 = st.columns(2)

        with viz_col1:
            st.markdown("###### Confusion Matrix")
            cm = metrics.get("confusion_matrix", [[0, 0], [0, 0]])
            cm_df = pd.DataFrame(cm, index=["Actual Legitimate", "Actual Fraud"], columns=["Pred Legitimate", "Pred Fraud"])
            fig_cm = px.imshow(cm_df, text_auto=True, color_continuous_scale="Blues")
            fig_cm.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_cm, width="stretch")

        with viz_col2:
            st.markdown("###### Feature Importances")
            fi = metrics.get("feature_importances", {})
            df_fi = pd.DataFrame({"Feature": list(fi.keys()), "Importance": list(fi.values())}).sort_values("Importance", ascending=True)
            fig_fi = px.bar(df_fi, x="Importance", y="Feature", orientation="h", color="Importance", color_continuous_scale="Teal")
            fig_fi.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_fi, width="stretch")

    # Retrain section
    st.markdown("---")
    st.markdown("#### ⚡ Retrain or Upload New Dataset")
    upload_file = st.file_uploader("Upload custom CSV dataset (matches schema)", type=["csv"])

    rt_cols = st.columns(2)
    with rt_cols[0]:
        if st.button("🔄 Retrain on Current Dataset", type="primary", width="stretch"):
            with st.spinner("Training model with 5-fold stratified random forest..."):
                if upload_file is not None:
                    train_df = pd.read_csv(upload_file)
                else:
                    train_df = df_loaded
                new_metrics = st.session_state.model.train(train_df)
                st.success(f"Retrained successfully! ROC-AUC: {new_metrics['roc_auc']:.4f}")
                st.rerun()

    with rt_cols[1]:
        if st.button("🎲 Generate Fresh 5,000 Records", width="stretch"):
            with st.spinner("Generating 5,000 realistic UPI behavioral records..."):
                fresh_df = generate_synthetic_upi_dataset(num_rows=5000, random_seed=int(datetime.now().timestamp()) % 10000)
                fresh_df.to_csv(csv_path, index=False)
                st.session_state.model.train(fresh_df)
                st.success("New 5,000 record dataset synthesized and model trained!")
                st.rerun()

    # Raw dataset preview
    st.markdown("##### 📄 Dataset Sample (Top 50 Rows)")
    st.dataframe(df_loaded.head(50), width="stretch")


# =====================================================================
# TAB 4: DATASET SPECIFICATION & AI PROMPT
# =====================================================================
elif nav_choice == "Dataset Specification & AI Prompt":
    st.markdown('<div class="main-header">📋 Trainable Data Format & AI Prompt Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Exact schema definitions, required mathematical relationships, and copyable prompt for external LLM dataset generation.</div>', unsafe_allow_html=True)

    # Schema specifications
    st.markdown("### 1. Data Schema & Feature Contract")
    schema_data = [
        {"Column": "transaction_id", "Type": "string", "Example": "TXN_UPI_100001", "Description": "Unique transaction key"},
        {"Column": "user_id", "Type": "string", "Example": "USR_1042", "Description": "Identifier across recurring transactions"},
        {"Column": "timestamp", "Type": "string (YYYY-MM-DD HH:MM:SS)", "Example": "2026-09-28 14:30:00", "Description": "IST Timestamp"},
        {"Column": "amount", "Type": "float", "Example": "450.00", "Description": "Transaction amount in INR ₹"},
        {"Column": "merchant_category", "Type": "string", "Example": "Groceries_Daily", "Description": "Category of payment/merchant"},
        {"Column": "device_id", "Type": "string", "Example": "DEV_SAMS23_01", "Description": "Hardware identifier"},
        {"Column": "device_model", "Type": "string", "Example": "Samsung Galaxy S23", "Description": "Device commercial model name"},
        {"Column": "location_city", "Type": "string", "Example": "Bengaluru", "Description": "City of execution"},
        {"Column": "location_lat", "Type": "float", "Example": "12.9716", "Description": "Latitude"},
        {"Column": "location_lon", "Type": "float", "Example": "77.5946", "Description": "Longitude"},
        {"Column": "user_avg_amount_30d", "Type": "float", "Example": "1850.00", "Description": "User EWMA historical spend mean"},
        {"Column": "user_std_amount_30d", "Type": "float", "Example": "520.00", "Description": "User EWMA spend std deviation"},
        {"Column": "z_score_amount", "Type": "float", "Example": "-2.69", "Description": "(amount - mean) / std"},
        {"Column": "spend_multiplier", "Type": "float", "Example": "0.24", "Description": "amount / mean"},
        {"Column": "is_known_device", "Type": "int (0 or 1)", "Example": "1", "Description": "1 if device in trusted profile"},
        {"Column": "is_known_city", "Type": "int (0 or 1)", "Example": "1", "Description": "1 if city in trusted profile"},
        {"Column": "hours_since_last_txn", "Type": "float", "Example": "3.50", "Description": "Hours elapsed since prior txn"},
        {"Column": "km_from_last_txn", "Type": "float", "Example": "4.20", "Description": "Haversine distance in km"},
        {"Column": "velocity_kmh", "Type": "float", "Example": "1.20", "Description": "km_from_last_txn / hours"},
        {"Column": "is_nocturnal", "Type": "int (0 or 1)", "Example": "0", "Description": "1 if between 01:00 AM & 05:30 AM IST"},
        {"Column": "txn_velocity_1h", "Type": "int", "Example": "1", "Description": "Count of txns in last 60 minutes"},
        {"Column": "scenario_type", "Type": "string", "Example": "normal_routine", "Description": "Behavioral scenario"},
        {"Column": "is_fraud", "Type": "int (0 or 1)", "Example": "0", "Description": "Target label (0=Legitimate, 1=Fraud)"}
    ]
    st.table(pd.DataFrame(schema_data))

    st.markdown("---")
    st.markdown("### 2. Copyable LLM Dataset Generation Prompt (`prompt.txt`)")
    st.caption("You can copy the prompt below and paste it into Claude 3.5 Sonnet, ChatGPT, or Gemini to generate massive datasets.")

    prompt_content = ""
    if os.path.exists("prompt.txt"):
        with open("prompt.txt", "r") as f:
            prompt_content = f.read()

    st.text_area("Prompt Text", value=prompt_content, height=350)
