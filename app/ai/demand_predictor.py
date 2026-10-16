"""
AI Demand Forecasting.

Aggregates historical bookings per category and projects next-period demand.
Uses a scikit-learn RandomForest when enough history exists, otherwise a
moving-average heuristic. Always returns a prediction per category.
"""
from collections import defaultdict
from datetime import date, timedelta


def predict_demand():
    """
    Returns a list of dicts:
        {'category': str, 'predicted': int, 'historical': int, 'trend': str}
    """
    from app.models import Booking, Device, DeviceCategory

    categories = DeviceCategory.query.all()
    bookings = Booking.query.all()

    # Map device_id -> category name
    dev_cat = {d.id: (d.category.name if d.category else 'Uncategorized')
               for d in Device.query.all()}

    # Monthly counts per category for the last 6 months
    today = date.today()
    months = [(today.replace(day=1) - timedelta(days=30 * i)) for i in range(6)][::-1]

    per_cat_month = defaultdict(lambda: defaultdict(int))
    per_cat_total = defaultdict(int)
    for b in bookings:
        cat = dev_cat.get(b.device_id, 'Uncategorized')
        per_cat_total[cat] += 1
        if b.start_date:
            key = b.start_date.replace(day=1)
            per_cat_month[cat][key] += 1

    predictions = []
    for cat in categories:
        series = [per_cat_month[cat.name].get(m, 0) for m in months]
        historical = per_cat_total.get(cat.name, 0)
        predicted = _forecast(series)
        trend = _trend(series)
        predictions.append({
            'category': cat.name,
            'icon': cat.icon,
            'predicted': predicted,
            'historical': historical,
            'series': series,
            'trend': trend,
        })

    predictions.sort(key=lambda p: p['predicted'], reverse=True)
    return predictions


def _forecast(series):
    if not any(series):
        return 1
    try:
        import numpy as np
        from sklearn.ensemble import RandomForestRegressor

        X = np.arange(len(series)).reshape(-1, 1)
        y = np.array(series)
        if y.sum() >= 4 and len(series) >= 4:
            model = RandomForestRegressor(n_estimators=40, random_state=42)
            model.fit(X, y)
            pred = model.predict([[len(series)]])[0]
            return max(1, int(round(pred)))
    except Exception:
        pass
    # Moving average fallback
    window = series[-3:] if len(series) >= 3 else series
    return max(1, int(round(sum(window) / max(1, len(window)))))


def _trend(series):
    if len(series) < 2:
        return 'steady'
    recent = sum(series[-2:])
    earlier = sum(series[:-2]) / max(1, len(series) - 2)
    if recent > earlier * 1.15:
        return 'rising'
    if recent < earlier * 0.85:
        return 'falling'
    return 'steady'
