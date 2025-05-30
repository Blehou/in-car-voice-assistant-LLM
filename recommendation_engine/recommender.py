"""
recommender.py

Filters, scores, and ranks nearby charging stations using:
- Explicit user preferences (e.g. providers, distance, charging power)
- Implicit preferences from past use
- Past user feedback stored in evaluation_log.json
"""

import json
from pathlib import Path
from typing import List, Dict


PREF_FILE = Path("preferences_database/user_preferences.json")
EVAL_LOG = Path("recommendation_engine/evaluation_log.json")


def load_user_preferences() -> Dict:
    """
    Load user preferences from JSON file.
    
    Returns:
        Dict: user preferences
    """
    with PREF_FILE.open() as f:
        return json.load(f)


def load_feedback_scores() -> Dict[str, float]:
    """
    Load average feedback ratings per station from evaluation logs.

    Returns:
        Dict[str, float]: station name → average rating (1 to 5)
    """
    if not EVAL_LOG.exists():
        return {}

    with EVAL_LOG.open() as f:
        logs = json.load(f)

    scores = {}
    counts = {}
    for entry in logs:
        for station, rating in entry.get("feedback", {}).items():
            scores[station] = scores.get(station, 0) + rating
            counts[station] = counts.get(station, 0) + 1

    return {station: scores[station] / counts[station] for station in scores}


def compute_score(station: Dict, preferences: Dict, feedback_scores: Dict[str, float], _feedback=False) -> float:
    """
    Compute the recommendation score of a station based on user preferences and feedback history.

    Args:
        station (Dict): station data (name, provider, distance_km, charging_power_kw)
        preferences (Dict): user preferences from JSON
        feedback_scores (Dict[str, float]): past average ratings per station
        _feedback (bool): whether to include feedback in scoring

    Returns:
        float: final score (negative if filtered out)
    """
    score = 0.0

    # Preferred providers
    if station["provider"] in preferences["preferred_providers"]:
        score += 1.0

    # Usage history (used before)
    if station["provider"] in [entry["station"] for entry in preferences.get("history", []) if entry["used"]]:
        score += 0.5

    # Filtering by max detour distance
    if station["distance_km"] > preferences["max_detour_km"]:
        return -1.0  # Filter out

    # Avoid conditions (e.g. avoid 'small providers')
    if any(avoid.lower() in station["name"].lower() for avoid in preferences["avoid"]):
        score -= 0.3

    # Charging power match
    if station.get("charging_power_kw", 0) >= preferences["charging_power_min_kw"]:
        score += 0.5

    # Past feedback: rating ∈ [1,5] → offset around neutral (3)
    if _feedback:
        rating = feedback_scores.get(station["name"])
        if rating:
            score += (rating - 3) * 0.3  # ±0.6 max

    # Distance penalty
    score -= 0.05 * station["distance_km"]

    return score


def recommend_places(user_preferences: Dict, nearby_stations: List[Dict]) -> List[Dict]:
    """
    Generate 1 to 3 personalized station recommendations.

    Args:
        user_preferences (Dict): preferences loaded from user_preferences.json
        nearby_stations (List[Dict]): candidate stations with fields: name, provider, distance_km, charging_power_kw

    Returns:
        List[Dict]: top 1–3 scored stations
    """
    feedback_scores = load_feedback_scores()
    scored = []

    for station in nearby_stations:
        score = compute_score(station, user_preferences, feedback_scores)
        if score >= 0:
            station["score"] = round(score, 2)
            scored.append(station)

    top = sorted(scored, key=lambda x: x["score"], reverse=True)
    
    return top
