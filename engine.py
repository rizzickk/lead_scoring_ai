from __future__ import annotations


DEFAULT_INTEREST_RATE = 0.065
DEFAULT_LOAN_TERM_YEARS = 30
DEFAULT_TOTAL_DTI_CAP = 0.43
DEFAULT_HOUSING_DTI_CAP = 0.31

DEFAULT_MONTHLY_TAX = 350.0
DEFAULT_MONTHLY_INSURANCE = 125.0
DEFAULT_MONTHLY_HOA = 0.0


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


def compute_lead_score(
    credit_bucket: str,
    job_tenure_years: float,
    timeline: str,
    preapproved: str,
    loan_type: str,
    rep_agreement_signed: str | None = None,
    rep_agreement_willing: str | None = None,
    low_credit_known_score: int | None = None,
) -> tuple[int, str, float]:

    credit_points_map = {
        "High": 12,
        "Medium": 8,
        "Low": 4,
        "": 0
    }
    credit_points = credit_points_map.get(credit_bucket, 0)

    loan_type_points_map = {
        "Conventional": 10,
        "FHA": 7,
        "VA": 10,
        "": 0
    }
    loan_type_points = loan_type_points_map.get(loan_type, 0)

    financial_strength = min(30, credit_points + loan_type_points)

    if job_tenure_years >= 5:
        tenure_points = 10
    elif job_tenure_years >= 3:
        tenure_points = 8
    elif job_tenure_years >= 1:
        tenure_points = 5
    else:
        tenure_points = 2

    stability = min(10, tenure_points)

    timeline_points_map = {
        "0-3 months": 12,
        "3-6 months": 9,
        "6-12 months": 5,
        "12+ months": 2,
        "": 0
    }
    timeline_points = timeline_points_map.get(timeline, 0)

    preapproved_points = 10 if preapproved == "Yes" else 0

    rep_signed_points = 0
    if rep_agreement_signed == "Yes":
        rep_signed_points = 8
    elif rep_agreement_signed == "No":
        rep_signed_points = 0

    rep_willing_points = 0
    if rep_agreement_willing == "Yes":
        rep_willing_points = 6
    elif rep_agreement_willing == "Unsure":
        rep_willing_points = 3
    elif rep_agreement_willing == "No":
        rep_willing_points = 0

    intent = min(30, timeline_points + preapproved_points + max(rep_signed_points, rep_willing_points))

    fit = 20

    score = financial_strength + stability + intent + fit
    score = max(0, min(100, int(round(score))))

    if score >= 70:
        tier = "A"
        close_probability = 0.75
    elif score >= 57:
        tier = "B"
        close_probability = 0.55
    elif score >= 42:
        tier = "C"
        close_probability = 0.30
    else:
        tier = "D"
        close_probability = 0.10

    if credit_bucket == "Low" and low_credit_known_score and low_credit_known_score < 550:
        score = 40
        tier = "C"
        close_probability = 0.05

    return score, tier, close_probability


def compute_flags(
    estimated_max_payment: float,
    monthly_income: float,
    monthly_debt: float,
    preapproved: str,
    receives_child_support: str | None = None,
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
        flags.append("Not affordable")

    if _safe_div(monthly_debt, monthly_income) > 0.30:
        flags.append("High debt load")

    if preapproved == "No":
        flags.append("Pre-approval recommended")

    if receives_child_support == "Yes":
        notes.append("Receives child support")

    if pays_child_support == "Yes":
        notes.append("Pays child support")

    if rep_agreement_signed == "No":
        flags.append("Representation agreement not signed")
    elif rep_agreement_signed == "Yes":
        flags.append("Representation agreement signed")

    if rep_agreement_signed != "Yes":
        if rep_agreement_willing == "No":
            flags.append("Not willing to sign representation agreement")
        elif rep_agreement_willing == "Unsure":
            flags.append("Unsure about representation agreement")
        elif rep_agreement_willing == "Yes":
            notes.append("Willing to sign representation agreement")

    if low_credit_known_score and low_credit_known_score < 550:
        flags.append("Do not pursue due to credit score below 550")

    return flags, notes