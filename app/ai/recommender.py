"""
AI Hardware Recommender.

Scores catalog devices against a free-text need (e.g. "laptop for python and
machine learning") using TF-IDF cosine similarity over each device's
name + tags + brand + specs, with a light boost for availability. Falls back
to keyword overlap if scikit-learn is unavailable.
"""


def _device_corpus(device):
    specs = device.specs or {}
    spec_text = ' '.join(f"{k} {v}" for k, v in specs.items())
    cat = device.category.name if device.category else ''
    return ' '.join(str(x) for x in [
        device.name, device.brand, device.model, device.tags, cat, spec_text
    ] if x).lower()


def _keyword_score(query, corpus):
    q_terms = {t for t in query.lower().replace(',', ' ').split() if len(t) > 1}
    if not q_terms:
        return 0.0
    hits = sum(1 for t in q_terms if t in corpus)
    return hits / len(q_terms)


def recommend_devices(query, devices, top_n=6):
    """
    Return a list of {'device': Device, 'match': int 0-100, 'reason': str},
    highest match first.
    """
    devices = list(devices)
    if not devices:
        return []

    query = (query or '').strip()
    if not query:
        # No query -> surface available devices as gentle suggestions.
        ranked = sorted(devices, key=lambda d: d.status != 'available')
        return [{'device': d, 'match': 0, 'reason': 'Popular campus pick'}
                for d in ranked[:top_n]]

    corpora = [_device_corpus(d) for d in devices]
    scores = None

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vec = TfidfVectorizer(stop_words='english')
        matrix = vec.fit_transform(corpora + [query.lower()])
        sims = cosine_similarity(matrix[-1], matrix[:-1])[0]
        scores = list(sims)
    except Exception:
        scores = [_keyword_score(query, c) for c in corpora]

    results = []
    for dev, raw in zip(devices, scores):
        match = int(round(min(1.0, raw) * 100))
        # Light availability boost so usable gear ranks higher on ties.
        if dev.status == 'available':
            match = min(100, match + 5)
        if match <= 0:
            match = max(match, _keyword_score(query, _device_corpus(dev)) and 12 or 0)
        reason = _explain(query, dev)
        results.append({'device': dev, 'match': match, 'reason': reason})

    results.sort(key=lambda r: r['match'], reverse=True)
    # Keep meaningful matches, but always return something.
    meaningful = [r for r in results if r['match'] > 0]
    return (meaningful or results)[:top_n]


def _explain(query, device):
    q_terms = {t for t in query.lower().replace(',', ' ').split() if len(t) > 2}
    tags = set((device.tags or '').lower().replace(',', ' ').split())
    overlap = sorted(q_terms & tags)
    if overlap:
        return "Matches: " + ', '.join(overlap[:4])
    if device.status == 'available':
        return "Available now and well-suited to your request"
    return "Related to your request"
