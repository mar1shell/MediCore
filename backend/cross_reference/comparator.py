"""Cross-reference — compare chart entities vs spoken entities.

Returns a list of discrepancy flags and an overall match score.
"""

from __future__ import annotations


def compare_entities(chart: dict, spoken: dict) -> dict:
    """Compare *chart* entities against *spoken* entities.

    Returns::

        {
            "flags": [
                {
                    "category": "medications",
                    "type": "missing_in_spoken" | "missing_in_chart" | "value_mismatch",
                    "item": "<entity>",
                    "detail": "<human-readable description>",
                }
            ],
            "match_score": 0.0 – 1.0,
        }
    """
    flags: list[dict] = []
    categories = set(chart.keys()) | set(spoken.keys())

    for category in categories:
        chart_items = _to_set(chart.get(category, []))
        spoken_items = _to_set(spoken.get(category, []))

        for item in chart_items - spoken_items:
            flags.append(
                {
                    "category": category,
                    "type": "missing_in_spoken",
                    "item": item,
                    "detail": f"'{item}' found in chart but not mentioned during voice session.",
                }
            )

        for item in spoken_items - chart_items:
            flags.append(
                {
                    "category": category,
                    "type": "missing_in_chart",
                    "item": item,
                    "detail": f"'{item}' mentioned during voice session but absent from chart.",
                }
            )

    total = sum(
        max(len(_to_set(chart.get(c, []))), len(_to_set(spoken.get(c, []))))
        for c in categories
    )
    match_score = 1.0 - (len(flags) / total) if total else 1.0

    return {"flags": flags, "match_score": round(max(0.0, match_score), 4)}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _to_set(value: list | dict | str | None) -> set[str]:
    """Normalise an entity value to a set of lowercase strings for comparison."""
    if isinstance(value, list):
        return {str(v).lower().strip() for v in value}
    if isinstance(value, dict):
        return {f"{k}:{v}".lower().strip() for k, v in value.items()}
    if isinstance(value, str):
        return {value.lower().strip()}
    return set()
