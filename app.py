import requests
import streamlit as st

st.set_page_config(page_title="KopaScore Loan Portal", page_icon="💳")

st.title("💳 KopaScore Automated Credit Portal")
st.write(
    "Enter the borrower's raw financial details below. KopaScore automatically calculates risk ratios and returns an instant decision."
)

st.markdown("---")

with st.form("loan_application_form"):
    st.subheader("📋 Borrower Raw Financial Input")

    col1, col2 = st.columns(2)

    with col1:
        requested_loan = st.number_input(
            "Requested Loan Amount (KES)",
            min_value=500,
            max_value=200000,
            value=10000,
            step=500,
        )

        monthly_inflow = st.number_input(
            "Monthly Income / Inflow (KES)",
            min_value=1000,
            max_value=1000000,
            value=40000,
            step=1000,
        )

        monthly_outflow = st.number_input(
            "Monthly Expenses / Outflow (KES)",
            min_value=0,
            max_value=1000000,
            value=22000,
            step=1000,
        )

    with col2:
        inflow_volatility = st.slider(
            "Inflow Volatility (Income Variation)",
            min_value=0.00,
            max_value=1.00,
            value=0.15,
            step=0.01,
            help="0.0 = Very stable monthly income | 1.0 = Highly unpredictable income",
        )

        prior_defaults = st.number_input(
            "Prior Unpaid Defaults",
            min_value=0,
            max_value=10,
            value=0,
            step=1,
        )

    submit_button = st.form_submit_button(
        "🚀 Evaluate Loan Application", use_container_width=True
    )

if submit_button:
    payload = {
        "requested_loan_amount": float(requested_loan),
        "monthly_inflow": float(monthly_inflow),
        "monthly_outflow": float(monthly_outflow),
        "inflow_volatility": float(inflow_volatility),
        "prior_defaults": int(prior_defaults),
    }

    try:
        response = requests.post("https://kopascore.onrender.com", json=payload)

        if response.status_code == 200:
            res = response.json()

            st.markdown("---")
            st.subheader("📊 Evaluation Results")

            # Top Level Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("KopaScore", f"{res['kopascore']} / 850")
            m2.metric("Default Probability", f"{res['default_probability'] * 100:.1f}%")
            m3.metric("Risk Category", res["risk_category"])

            # Automatically Calculated Ratios Display
            st.markdown("#### ⚙️ Automated System Calculations")
            c1, c2, c3 = st.columns(3)
            c1.write(f"**Loan to Income Ratio:** `{res['engineered_metrics']['loan_to_income_ratio']}`")
            c2.write(f"**Net Cashflow Ratio:** `{res['engineered_metrics']['net_cashflow_ratio']}`")
            c3.write(f"**Net Cashflow:** KES `{res['engineered_metrics']['calculated_net_cashflow_kes']:,}`")

            # Final Decision Banner
            st.markdown("---")
            if res["decision"] == "APPROVE":
                st.success(f"### ✅ DECISION: APPROVED\n\n**Recommendation:** {res['recommendation']}")
            else:
                st.error(f"### ❌ DECISION: REJECTED\n\n**Recommendation:** {res['recommendation']}")

        else:
            st.error(f"API Error: {response.json().get('detail')}")

    except requests.exceptions.ConnectionError:
        st.error("🔴 Backend API is offline! Run `uvicorn main:app --reload` on port 8000.")