"""
AI Student Risk & Trust Profiler.

Builds a risk score (0-100, higher = riskier) per student from:
  - overdue / late returns
  - recorded damage inspections
  - unpaid fines
Returns a band (low / medium / high) used by the Admin Risk Radar.
"""


def assess_student_risk(user):
    from app.models import Rental, Fine, ReturnInspection

    rentals = Rental.query.filter_by(user_id=user.id).all()
    fines = Fine.query.filter_by(user_id=user.id).all()

    total_rentals = len(rentals)
    overdue = sum(1 for r in rentals if r.status == 'overdue')
    late_returns = 0
    for r in rentals:
        if r.returned_at and r.due_date:
            if r.returned_at.date() > r.due_date:
                late_returns += 1

    rental_ids = [r.id for r in rentals]
    damage_events = 0
    if rental_ids:
        damage_events = ReturnInspection.query.filter(
            ReturnInspection.rental_id.in_(rental_ids),
            ReturnInspection.ai_damage_detected.is_(True)
        ).count()

    unpaid_fines = [f for f in fines if f.status == 'pending']
    unpaid_total = sum(f.amount for f in unpaid_fines)

    score = 0
    score += overdue * 20
    score += late_returns * 10
    score += damage_events * 25
    score += min(30, unpaid_total / 100.0)
    score = int(min(100, round(score)))

    if score >= 60:
        band = 'high'
    elif score >= 25:
        band = 'medium'
    else:
        band = 'low'

    return {
        'user': user,
        'risk_score': score,
        'band': band,
        'total_rentals': total_rentals,
        'overdue': overdue,
        'late_returns': late_returns,
        'damage_events': damage_events,
        'unpaid_fine_amount': round(unpaid_total, 2),
        'trust_score': max(0, 100 - score),
    }


def assess_all_students():
    from app.models import User
    students = User.query.filter_by(role='student').all()
    profiles = [assess_student_risk(s) for s in students]
    profiles.sort(key=lambda p: p['risk_score'], reverse=True)
    return profiles
