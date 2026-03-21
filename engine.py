from __future__ import annotations


DEFAULT_INTEREST_RATE = 0.065
DEFAULT_LOAN_TERM_YEARS = 30
DEFAULT_TOTAL_DTI_CAP = 0.43
DEFAULT_HOUSING_DTI_CAP = 0.31

DEFAULT_MONTHLY_TAX = 350.0
DEFAULT_MONTHLY_INSURANCE = 125.0
DEFAULT_MONTHLY_HOA = 0.0

CLOSE_PROBABILITY = {"A": 0.75, "B": 0.55, "C": 0.30, "D": 0.10}


def _safe_div(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator


def _mortgage_pv(monthly_payment: float, annual_rate: float, years: int) -> float:
    if monthly_payment <= 0 or years <= 0:
        return 0.0

    monthly_rate = annual_rate / 12
    n = years * 12

    if monthly_rate == 0:
        return monthly_payment * n

    return monthly_payment * (1 - (1 + monthly_rate) ** (-n)) / monthly_rate


def get_market_assumptions(
    interest_rate: float | None = None,
    loan_term_years: int | None = None,
    monthly_tax: float | None = None,
    monthly_insurance: float | None = None,
    monthly_hoa: float | None = None,
) -> dict:
    rate = interest_rate if interest_rate not in (None, 0) else DEFAULT_INTEREST_RATE
    term = loan_term_years if loan_term_years not in (None, 0) else DEFAULT_LOAN_TERM_YEARS
    tax = monthly_tax if monthly_tax not in (None,) else DEFAULT_MONTHLY_TAX
    ins = monthly_insurance if monthly_insurance not in (None,) else DEFAULT_MONTHLY_INSURANCE
    hoa = monthly_hoa if monthly_hoa not in (None,) else DEFAULT_MONTHLY_HOA

    return {
        "interest_rate": rate,
        "loan_term_years": int(term),
        "monthly_tax": float(tax),
        "monthly_insurance": float(ins),
        "monthly_hoa": float(hoa),
        "total_dti_cap": DEFAULT_TOTAL_DTI_CAP,
        "housing_dti_cap": DEFAULT_HOUSING_DTI_CAP,
    }


def compute_affordability(
    annual_income: float,
    annual_debt_payments: float,
    down_payment: float,
    interest_rate: float | None = None,
    loan_term_years: int | None = None,
    tax: float | None = None,
    insurance: float | None = None,
    hoa: float | None = None,
    loan_type: str | None = None,
) -> dict:
    assumptions = get_market_assumptions(
        interest_rate=interest_rate,
        loan_term_years=loan_term_years,
        monthly_tax=tax,
        monthly_insurance=insurance,
        monthly_hoa=hoa,
    )

    monthly_income = annual_income / 12 if annual_income > 0 else 0.0
    monthly_debt = annual_debt_payments / 12 if annual_debt_payments > 0 else 0.0

    max_housing_by_total_dti = max(
        0.0,
        monthly_income * assumptions["total_dti_cap"] - monthly_debt
    )

    max_housing_by_housing_dti = max(
        0.0,
        monthly_income * assumptions["housing_dti_cap"]
    )

    estimated_max_housing_payment = min(
        max_housing_by_total_dti,
        max_housing_by_housing_dti
    )

    max_principal_interest_payment = max(
        0.0,
        estimated_max_housing_payment
        - assumptions["monthly_tax"]
        - assumptions["monthly_insurance"]
        - assumptions["monthly_hoa"]
    )

    maximum_loan_amount = _mortgage_pv(
        monthly_payment=max_principal_interest_payment,
        annual_rate=assumptions["interest_rate"],
        years=assumptions["loan_term_years"],
    )

    max_home_price = maximum_loan_amount + down_payment
    comfort_price = max_home_price * 0.90
    stretch_price = max_home_price * 1.05

    return {
        "monthly_income": monthly_income,
        "monthly_debt": monthly_debt,
        "interest_rate": assumptions["interest_rate"],
        "loan_term_years": assumptions["loan_term_years"],
        "monthly_tax": assumptions["monthly_tax"],
        "monthly_insurance": assumptions["monthly_insurance"],
        "monthly_hoa": assumptions["monthly_hoa"],
        "max_housing_by_total_dti": max_housing_by_total_dti,
        "max_housing_by_housing_dti": max_housing_by_housing_dti,
        "max_payment": estimated_max_housing_payment,
        "max_pi_payment": max_principal_interest_payment,
        "loan_amount": maximum_loan_amount,
        "max_home_price": max_home_price,
        "comfort_price": comfort_price,
        "stretch_price": stretch_price,
    }


def compute_disposition(
    rep_agreement_signed: str,
    low_credit_known_score: int | None,
    estimated_max_payment: float,
    monthly_income: float,
    monthly_debt: float,
    preapproved: str,
    rep_agreement_willing: str,
) -> str:
    if rep_agreement_signed == "Yes":
        return "Low Priority"
    if low_credit_known_score and low_credit_known_score < 550:
        return "Low Priority"

    if estimated_max_payment <= 0:
        return "Nurture"
    if monthly_income > 0 and _safe_div(monthly_debt, monthly_income) > 0.30:
        return "Nurture"
    if preapproved == "No":
        return "Nurture"
    if rep_agreement_willing in ("No", "Unsure"):
        return "Nurture"

    return "Active Opportunity"


def compute_priority_score(
    credit_bucket: str,
    loan_type: str,
    timeline: str,
    preapproved: str,
    job_tenure_years: float,
    rep_agreement_willing: str,
    disposition: str,
) -> int:
    credit_points = {"High": 25, "Medium": 17, "Low": 8, "": 0}.get(credit_bucket, 0)
    loan_points = {"Conventional": 18, "VA": 18, "FHA": 13, "Unsure": 10, "": 0}.get(loan_type, 0)
    timeline_points = {
        "0-3 months": 20, "3-6 months": 15, "6-12 months": 8, "12+ months": 3, "": 0
    }.get(timeline, 0)
    preapproved_points = 17 if preapproved == "Yes" else 0

    if job_tenure_years >= 5:
        tenure_points = 12
    elif job_tenure_years >= 3:
        tenure_points = 9
    elif job_tenure_years >= 1:
        tenure_points = 6
    else:
        tenure_points = 3

    willing_points = {"Yes": 8, "Unsure": 3, "No": 0}.get(rep_agreement_willing, 0)

    score = credit_points + loan_points + timeline_points + preapproved_points + tenure_points + willing_points

    if disposition == "Low Priority":
        score = min(score, 25)
    elif disposition == "Nurture":
        score = min(score, 65)

    return max(0, min(100, score))


def compute_tier(score: int) -> str:
    if score >= 80:
        return "A"
    elif score >= 60:
        return "B"
    elif score >= 40:
        return "C"
    else:
        return "D"


def compute_recommended_next_step(
    disposition: str,
    flags: list[str],
    comfort_price: float,
    max_price: float,
) -> str:
    flags_lower = [f.lower() for f in flags]

    if disposition == "Low Priority":
        if "credit score below typical lender minimums" in flags_lower:
            return "Credit may limit near-term financing options. Recommend lender consultation before beginning an active search."
        return "Buyer has indicated existing representation. Verify status before proceeding."

    if "financing range not yet established" in flags_lower:
        return "Search not recommended at this stage. Connect buyer with a lender to establish a financing baseline first."

    if "elevated monthly obligations" in flags_lower:
        return "Existing obligations may affect financing options. Recommend a lender review before significant time investment."

    if "pre-approval recommended" in flags_lower:
        return "Make a lender introduction the first next step before beginning an active search."

    if any(f in flags_lower for f in [
        "not willing to sign representation agreement",
        "unsure about representation agreement"
    ]):
        return "Discuss buyer representation expectations before moving into an active search."

    return (
        f"Buyer appears ready to begin an active search. "
        f"Focus near the comfort range (${round(comfort_price):,} – ${round(max_price):,})."
    )


def compute_flags(
    estimated_max_payment: float,
    monthly_income: float,
    monthly_debt: float,
    preapproved: str,
    pays_child_support: str | None = None,
    rep_agreement_signed: str | None = None,
    rep_agreement_willing: str | None = None,
    low_credit_known_score: int | None = None,
) -> tuple[list[str], list[str]]:

    flags: list[str] = []
    notes: list[str] = []

    if monthly_income <= 0:
        flags.append("Income missing or invalid")
        return flags, notes

    if estimated_max_payment <= 0:
        flags.append("Financing range not yet established")

    if _safe_div(monthly_debt, monthly_income) > 0.30:
        flags.append("Elevated monthly obligations — lender review recommended")

    if preapproved == "No":
        flags.append("Pre-approval recommended")

    if pays_child_support == "Yes":
        notes.append("Pays child support")

    if rep_agreement_signed == "Yes":
        flags.append("Buyer has indicated existing representation")
    else:
        if rep_agreement_willing == "No":
            flags.append("Not willing to sign representation agreement")
        elif rep_agreement_willing == "Unsure":
            flags.append("Unsure about representation agreement")
        elif rep_agreement_willing == "Yes":
            notes.append("Willing to sign representation agreement")

    if low_credit_known_score and low_credit_known_score < 550:
        flags.append("Credit score below typical lender minimums — financing prep recommended")

    return flags, notes
