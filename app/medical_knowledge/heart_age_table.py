"""Heart age estimation using JBS3/QRISK3 method.

The heart age is the age at which someone with all-optimal risk factors
would have the same 10-year CV risk as the user.
"""
from app.medical_knowledge.risk_scores import calc_qrisk3, QRISK3Inputs


def calc_heart_age(
    age: int,
    sex: str,
    cv_risk_pct: float,
    systolic_bp: float,
    total_chol: float,
    hdl_chol: float,
    smoking: bool,
    diabetes: bool,
    ethnicity: str = "white",
) -> int:
    """Estimate heart age using iterative search.

    Finds the age at which a person with optimal risk factors would have
    the same 10-year CV risk as the user.
    """
    # Optimal values
    optimal_bp = 120
    optimal_chol = 150
    optimal_hdl = 60
    optimal_smoking = False
    optimal_diabetes = False

    # Binary search for heart age
    low = age - 20  # Can be 20 years younger
    high = age + 30  # Can be 30 years older
    if low < 30:
        low = 30

    best_age = age

    for _ in range(50):  # Binary search iterations
        mid = (low + high) // 2

        # Calculate CV risk at this age with optimal factors
        try:
            test_inputs = QRISK3Inputs(
                age=mid,
                sex=sex,
                ethnicity=ethnicity,
                smoking=optimal_smoking,
                diabetes=optimal_diabetes,
                family_history_early_chd=False,
                ckd=False,
                afib=False,
                bp_treatment=False,
                systolic_bp=optimal_bp,
                total_hdl_ratio=optimal_chol / optimal_hdl,
                bmi=22.0,
            )
            test_risk = calc_qrisk3(test_inputs)
        except Exception:
            # Fallback calculation
            test_risk = cv_risk_pct * (mid / age) if age > 0 else cv_risk_pct

        if abs(test_risk - cv_risk_pct) < 0.5:
            best_age = mid
            break
        elif test_risk < cv_risk_pct:
            low = mid + 1
        else:
            high = mid - 1
            best_age = mid

    return best_age


def calc_heart_age_gap(heart_age: int, chronological_age: int) -> int:
    """Calculate heart age gap (positive = older heart)."""
    return heart_age - chronological_age


def heart_age_gap_to_penalty(gap: int) -> float:
    """Convert heart age gap to penalty (0-100).

    0 years gap = 0 penalty
    20+ years older = 100 penalty
    """
    if gap <= 0:
        return 0
    return min(gap * 5, 100)  # 20 years = 100 penalty