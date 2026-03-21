import uuid
import streamlit as st
from engine import (
    compute_affordability, compute_disposition, compute_priority_score,
    compute_tier, compute_flags, compute_recommended_next_step, CLOSE_PROBABILITY
)
from pdf_report import generate_report_bytes
from database import create_table, insert_lead
from storage import upload_pdf_and_get_signed_url
from emailer import send_agent_email

st.set_page_config(page_title="Home Readiness Form", layout="centered")

st.markdown("""
<style>
button[data-testid="stNumberInputStepUp"],
button[data-testid="stNumberInputStepDown"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)

create_table()

AGENTS = {
    "8f4c2d91b7e3a4f1": {
        "name": "Ricardo",
        "emails": [
            "ricardo@rsautomationep.com",
            # "ricardo_villalobos_@outlook.com"
        ],
        "active": True
    }
}

agent_param = st.query_params.get("a", "unknown")
agent = agent_param[0] if isinstance(agent_param, list) else agent_param

agent_record = AGENTS.get(agent)

if not agent_record or not agent_record["active"]:
    st.error("This intake link is inactive.")
    st.stop()

agent_emails = agent_record["emails"]

st.title("Home Readiness Form")
st.write("Complete the short form below so your agent can review your information and follow up with next steps.")

if "step" not in st.session_state:
    st.session_state.step = 1

defaults = {
    "buyer_name": "",
    "buyer_phone": "",
    "buyer_email": "",
    "timeline": "",
    "preapproved": "",
    "rep_agreement_signed": "",
    "rep_agreement_willing": "",
    "income": 0.0,
    "debt": 0.0,
    "down_payment": 0.0,
    "income_raw": "",
    "debt_raw": "",
    "down_payment_raw": "",
    "receives_child_support": "",
    "pays_child_support": "",
    "loan_type": "",
    "credit_bucket": "",
    "low_credit_known_score": 0,
    "job_tenure": 0.0,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

progress_map = {
    1: 0.33,
    2: 0.66,
    3: 1.00
}

st.progress(progress_map[st.session_state.step])
st.caption(f"Step {st.session_state.step} of 3")

# STEP 1
if st.session_state.step == 1:
    st.subheader("1. About You")

    st.session_state.buyer_name = st.text_input(
        "Full name",
        value=st.session_state.buyer_name,
        placeholder="Jane Smith"
    )

    st.session_state.buyer_phone = st.text_input(
        "Phone number",
        value=st.session_state.buyer_phone,
        placeholder="(555) 867-5309"
    )

    st.session_state.buyer_email = st.text_input(
        "Email address",
        value=st.session_state.buyer_email,
        placeholder="email@gmail.com"
    )

    timeline_options = ["", "0-3 months", "3-6 months", "6-12 months", "12+ months"]
    st.session_state.timeline = st.selectbox(
        "When are you hoping to buy?",
        timeline_options,
        index=timeline_options.index(st.session_state.timeline)
        if st.session_state.timeline in timeline_options else 0
    )

    preapproved_options = ["", "Yes", "No"]
    st.session_state.preapproved = st.selectbox(
        "Have you already been pre-approved by a lender?",
        preapproved_options,
        index=preapproved_options.index(st.session_state.preapproved)
        if st.session_state.preapproved in preapproved_options else 0
    )

    rep_signed_options = ["", "Yes", "No"]
    st.session_state.rep_agreement_signed = st.selectbox(
        "Have you already signed a representation agreement with an agent?",
        rep_signed_options,
        index=rep_signed_options.index(st.session_state.rep_agreement_signed)
        if st.session_state.rep_agreement_signed in rep_signed_options else 0
    )

    rep_willing_options = ["", "Yes", "No", "Unsure"]
    st.session_state.rep_agreement_willing = st.selectbox(
        "If needed, would you be willing to sign a representation agreement?",
        rep_willing_options,
        index=rep_willing_options.index(st.session_state.rep_agreement_willing)
        if st.session_state.rep_agreement_willing in rep_willing_options else 0
    )

    col1, col2 = st.columns([1, 1])
    with col2:
        if st.button("Next", use_container_width=True):
            missing = []
            if not st.session_state.buyer_name.strip():
                missing.append("Full name")
            if not st.session_state.buyer_phone.strip():
                missing.append("Phone number")
            if not st.session_state.buyer_email.strip():
                missing.append("Email address")
            if not st.session_state.timeline:
                missing.append("Timeline")
            if not st.session_state.preapproved:
                missing.append("Pre-approval status")
            if not st.session_state.rep_agreement_signed:
                missing.append("Representation agreement status")
            if not st.session_state.rep_agreement_willing:
                missing.append("Representation agreement willingness")

            if missing:
                st.error("Please complete: " + ", ".join(missing))
            else:
                st.session_state.step = 2
                st.rerun()

# STEP 2
elif st.session_state.step == 2:
    st.subheader("2. Financial Snapshot")

    def _parse_currency(raw):
        try:
            return max(0.0, float(raw.replace("$", "").replace(",", "").strip()))
        except (ValueError, AttributeError):
            return 0.0

    st.text_input("Estimated annual household income", placeholder="$0.00", key="income_raw")
    st.session_state.income = _parse_currency(st.session_state.income_raw)

    st.text_input("Total monthly debt payments", placeholder="$0.00", key="debt_raw")
    st.session_state.debt = _parse_currency(st.session_state.debt_raw)

    st.text_input("Estimated down payment available", placeholder="$0.00", key="down_payment_raw")
    st.session_state.down_payment = _parse_currency(st.session_state.down_payment_raw)

    yes_no_options = ["", "Yes", "No"]

    st.session_state.receives_child_support = st.selectbox(
        "Do you receive child support?",
        yes_no_options,
        index=yes_no_options.index(st.session_state.receives_child_support)
        if st.session_state.receives_child_support in yes_no_options else 0
    )

    st.session_state.pays_child_support = st.selectbox(
        "Do you pay child support?",
        yes_no_options,
        index=yes_no_options.index(st.session_state.pays_child_support)
        if st.session_state.pays_child_support in yes_no_options else 0
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()

    with col2:
        if st.button("Next ", use_container_width=True):
            missing = []
            if st.session_state.income <= 0:
                missing.append("Estimated annual household income")
            if not st.session_state.receives_child_support:
                missing.append("Child support received indicator")
            if not st.session_state.pays_child_support:
                missing.append("Child support paid indicator")

            if missing:
                st.error("Please complete: " + ", ".join(missing))
            else:
                st.session_state.step = 3
                st.rerun()

# STEP 3
elif st.session_state.step == 3:
    st.subheader("3. Purchase Goals")

    loan_options = ["", "Conventional", "FHA", "VA"]
    st.session_state.loan_type = st.selectbox(
        "Loan type",
        loan_options,
        index=loan_options.index(st.session_state.loan_type)
        if st.session_state.loan_type in loan_options else 0
    )

    credit_options = ["", "High", "Medium", "Low"]
    st.session_state.credit_bucket = st.selectbox(
        "Credit score range",
        credit_options,
        index=credit_options.index(st.session_state.credit_bucket)
        if st.session_state.credit_bucket in credit_options else 0
    )

    if st.session_state.credit_bucket == "Low":
        prior = st.session_state.low_credit_known_score
        default_score = int(prior) if isinstance(prior, (int, float)) and prior >= 300 else 550
        st.session_state.low_credit_known_score = st.number_input(
            "If known, what is your approximate credit score?",
            min_value=300,
            max_value=850,
            step=1,
            value=default_score
        )
    else:
        st.session_state.low_credit_known_score = 0

    st.session_state.job_tenure = st.number_input(
        "Years at current job",
        min_value=0.0,
        step=0.5,
        value=float(st.session_state.job_tenure),
        format="%.1f"
    )

    st.markdown("### Review")
    st.write(f"**Name:** {st.session_state.buyer_name}")
    st.write(f"**Phone:** {st.session_state.buyer_phone}")
    st.write(f"**Email:** {st.session_state.buyer_email}")
    st.write(f"**Timeline:** {st.session_state.timeline}")
    st.write(f"**Pre-approved:** {st.session_state.preapproved}")
    st.write(f"**Representation agreement signed:** {st.session_state.rep_agreement_signed}")
    st.write(f"**Willing to sign representation agreement:** {st.session_state.rep_agreement_willing}")
    st.write(f"**Estimated income:** ${st.session_state.income:,.0f}")
    st.write(f"**Monthly debt payments:** ${st.session_state.debt:,.0f}")
    st.write(f"**Down payment:** ${st.session_state.down_payment:,.0f}")
    st.write(f"**Receives child support:** {st.session_state.receives_child_support}")
    st.write(f"**Pays child support:** {st.session_state.pays_child_support}")
    st.write(f"**Years at current job:** {st.session_state.job_tenure:.1f}")
    st.write(f"**Credit score range:** {st.session_state.credit_bucket}")
    if st.session_state.credit_bucket == "Low" and st.session_state.low_credit_known_score:
        st.write(f"**Approximate credit score:** {st.session_state.low_credit_known_score}")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Back ", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

    with col2:
        if st.button("Submit Information", use_container_width=True):
            missing = []
            if not st.session_state.loan_type:
                missing.append("Loan type")
            if not st.session_state.credit_bucket:
                missing.append("Credit score range")

            if missing:
                st.error("Please complete: " + ", ".join(missing))
            else:
                results = compute_affordability(
                    annual_income=st.session_state.income,
                    annual_debt_payments=st.session_state.debt * 12,
                    down_payment=st.session_state.down_payment,
                    loan_type=st.session_state.loan_type
                )

                monthly_income = st.session_state.income / 12
                monthly_debt = st.session_state.debt

                disposition = compute_disposition(
                    rep_agreement_signed=st.session_state.rep_agreement_signed,
                    low_credit_known_score=st.session_state.low_credit_known_score,
                    estimated_max_payment=results["max_payment"],
                    monthly_income=monthly_income,
                    monthly_debt=monthly_debt,
                    preapproved=st.session_state.preapproved,
                    rep_agreement_willing=st.session_state.rep_agreement_willing,
                )

                priority_score = compute_priority_score(
                    credit_bucket=st.session_state.credit_bucket,
                    loan_type=st.session_state.loan_type,
                    timeline=st.session_state.timeline,
                    preapproved=st.session_state.preapproved,
                    job_tenure_years=st.session_state.job_tenure,
                    rep_agreement_willing=st.session_state.rep_agreement_willing,
                    disposition=disposition,
                )

                tier = compute_tier(priority_score)

                flags, notes = compute_flags(
                    estimated_max_payment=results["max_payment"],
                    monthly_income=monthly_income,
                    monthly_debt=monthly_debt,
                    preapproved=st.session_state.preapproved,
                    receives_child_support=st.session_state.receives_child_support,
                    pays_child_support=st.session_state.pays_child_support,
                    rep_agreement_signed=st.session_state.rep_agreement_signed,
                    rep_agreement_willing=st.session_state.rep_agreement_willing,
                    low_credit_known_score=st.session_state.low_credit_known_score,
                )

                recommended_next_step = compute_recommended_next_step(
                    disposition=disposition,
                    flags=flags,
                    comfort_price=results["comfort_price"],
                    max_price=results["max_home_price"],
                )

                probability = CLOSE_PROBABILITY[tier]

                pdf_bytes = generate_report_bytes(
                    st.session_state.buyer_name,
                    st.session_state.buyer_phone,
                    st.session_state.buyer_email,
                    disposition,
                    priority_score,
                    tier,
                    results["max_home_price"],
                    results["comfort_price"],
                    results["stretch_price"],
                    flags,
                    notes,
                    recommended_next_step,
                )

                file_name = f"{uuid.uuid4().hex}.pdf"
                report_path, report_url = upload_pdf_and_get_signed_url(pdf_bytes, file_name)

                insert_lead(
                    agent,
                    st.session_state.buyer_name,
                    st.session_state.buyer_phone,
                    priority_score,
                    tier,
                    probability,
                    results["max_home_price"],
                    report_url
                )

                if agent_emails:
                    try:
                        send_agent_email(
                            agent_emails,
                            st.session_state.buyer_name,
                            st.session_state.buyer_phone,
                            st.session_state.buyer_email,
                            disposition,
                            priority_score,
                            tier,
                            recommended_next_step,
                            results["max_home_price"],
                            report_url
                        )
                        
                    except Exception as e:
                        st.error(f"Email failed: {e}")
                else:
                    st.error("No agent email resolved from URL parameter.")

                st.success("Thank you. Your information has been submitted successfully.")
                st.write("An agent will review your information and follow up shortly.")