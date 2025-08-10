######################################################################
# recommender.py

# Filters, scores, and ranks nearby charging stations using:
# - Explicit user preferences (e.g. providers, distance, charging power)
# - Implicit preferences from past use
# - Past user feedback stored in evaluation_log.json 
# 
# Functions:
#
### - load_feedback_scores
### - compute_score
### - recommend_places
######################################################################

import json
from pathlib import Path
from typing import List, Dict


PREF_FILE = Path("preferences_database/user_preferences.json")
EVAL_LOG = Path("recommendation_engine/evaluation_log.json")


def load_feedback_scores() -> Dict[str, Dict[str, float]]:
    """
    Load average feedback ratings and counts per POI from evaluation logs.

    Returns:
        Dict[str, Dict]: {
            poi_name: {
                "avg_rating": float (1 to 5),
                "count": int (number of times recommended and rated)
            }
        }
    """
    if not EVAL_LOG.exists():
        return {}

    with EVAL_LOG.open() as f:
        content = f.read().strip()
        if not content:
            return {}
        logs = json.loads(content)

    scores = {}
    counts = {}

    for entry in logs:
        feedback = entry.get("feedback", {})
        poi_name = feedback.get("point_of_interest")
        rating = feedback.get("rating")

        if poi_name and isinstance(rating, (int, float)):
            scores[poi_name] = scores.get(poi_name, 0) + rating
            counts[poi_name] = counts.get(poi_name, 0) + 1

    return {
        poi: {
            "avg_rating": round(scores[poi] / counts[poi], 2),
            "count": counts[poi]
        }
        for poi in scores
    }



def compute_score(point_of_interest: Dict, preferences: Dict, feedback_scores: Dict[str, Dict[str, float]], POI_type: str = "stations", _feedback=False) -> float:
    """
    Compute the recommendation score of a point of interest based on user preferences and feedback history.

    Args:
        point_of_interest (Dict): the point of interest (e.g. station, restaurant, hobby)
        preferences (Dict): user preferences from JSON
        feedback_scores (Dict[str, float]): past average ratings per station
        POI_type (str): type of point of interest (e.g. "stations", "restaurants", "hobbies")
        _feedback (bool): whether to include feedback in scoring

    Returns:
        float: final score (negative if filtered out)
    """
    score = 0.0
    
    if POI_type == "stations":
        station = point_of_interest
        prefs = preferences["stations"]

        # Preferred providers
        if station["provider"] in prefs["preferred_providers"]:
            score += 1.0

        # Filtering by max detour distance
        if station["distance_km"] > prefs["max_detour_km"]:
            return -1.0  # Filter out

        # Avoid conditions (e.g. avoid 'small providers')
        if any(avoid.lower() in station["name"].lower() for avoid in prefs["avoid"]):
            score -= 0.3

        # Charging power match
        if station.get("charging_power_kw", 0) >= prefs["charging_power_min_kw"]:
            score += 0.5

        # Past feedback: rating ∈ [1,5] → offset around neutral (3)
        if _feedback:
            rating = feedback_scores.get(station["name"], {}).get("avg_rating", 0)
            if rating:
                score += (rating - 3) * 0.3  # ±0.6 max

        # Distance penalty
        score -= 0.05 * station["distance_km"]
    
    elif POI_type == "restaurants":
        restaurant = point_of_interest
        prefs = preferences["restaurants"]

        # Filter: too far from allowed detour
        if restaurant["distance_km"] > prefs["max_distance_from_route_km"]:
            return -1.0  # filtered out

        # Rating score
        rating = restaurant.get("rating", 0)
        if rating >= prefs["min_rating"]:
            score += (rating - prefs["min_rating"]) * 1.0  # up to +1.0 if perfect match

        # Price level match (1 = cheap, 2 = moderate, 3 = expensive)
        budget_map = {"cheap": 1, "moderate": 2, "expensive": 3}
        max_price = budget_map.get(prefs["average_budget"], 2)
        if "price_level" in restaurant:
            if restaurant["price_level"] <= max_price:
                score += 0.5 # within budget
            else:
                return -1.0  # too expensive → filtered

        # Opening status
        if restaurant.get("open_now") is True:
            score += 0.7
        elif restaurant.get("open_now") is False:
            score -= 0.8

        # Distance penalty
        score -= 0.05 * restaurant["distance_km"]

        # Feedback history (if enabled)
        if _feedback:
            rating = feedback_scores.get(restaurant["name"], {}).get("avg_rating", 0)
            if rating:
                score += (rating - 3) * 0.3
    
    elif POI_type == "hobbies":
        hobby = point_of_interest
        prefs = preferences["hobbies"]

        # Filter: too far from allowed detour
        if hobby["distance_km"] > prefs["max_distance_from_route_km"]:
            return -1.0  # filtered out

        # Rating score
        rating = hobby.get("rating", 0)
        if rating >= prefs["min_rating"]:
            score += (rating - prefs["min_rating"]) * 1.0  # up to +1.0 if perfect match
        
        # Price level match (1 = cheap, 2 = moderate, 3 = expensive)
        budget_map = {"cheap": 1, "moderate": 2, "expensive": 3}
        max_price = budget_map.get(prefs["max_budget_per_activity"], 2)
        if "price_level" in hobby:
            if hobby["price_level"] <= max_price:
                score += 0.5 # within budget
            else:
                return -1.0  # too expensive → filtered

        # Opening status
        if hobby.get("open_now") is True:
            score += 0.7
        elif hobby.get("open_now") is False:
            score -= 0.8

        # Distance penalty
        score -= 0.05 * hobby["distance_km"]

        # Feedback history (if enabled)
        if _feedback:
            rating = feedback_scores.get(hobby["name"], {}).get("avg_rating", 0)
            if rating:
                score += (rating - 3) * 0.3

    return score


def recommend_places(user_preferences: Dict, nearby_POIs: List[Dict], POI_type: str = "stations", _feedback: bool = False) -> List[Dict]:
    """
    Generate 1 to 3 personalized recommendations according to the point of interest of the user.

    Args:
        user_preferences (Dict): preferences loaded from user_preferences.json
        nearby_POIs (List[Dict]): candidate points of interest with fields: name, provider, distance_km, charging_power_kw
        POI_type (str): type of point of interest (e.g. "stations", "restaurants", "hobbies")

    Returns:
        List[Dict]: top scored points of interest
    """
    feedback_scores = load_feedback_scores()
    scored = []
    top = []

    if POI_type == "stations":
        for poi in nearby_POIs:
            score = compute_score(poi, user_preferences, feedback_scores, POI_type=POI_type, _feedback=_feedback)
            if score >= 0:
                poi["score"] = round(score, 2)
                scored.append(poi)

        top = sorted(scored, key=lambda x: x["score"], reverse=True)

    elif POI_type in ["restaurants", "hobbies"]:
        for poi in nearby_POIs:
            score = compute_score(poi, user_preferences, feedback_scores, POI_type=POI_type, _feedback=_feedback)
            if score >= 0:
                poi["score"] = round(score, 2)
                scored.append(poi)

        top = sorted(scored, key=lambda x: x["score"], reverse=True)
    
    return top

if __name__ == "__main__":
    feedback = load_feedback_scores()
    # print("Feedback scores loaded:")
    # print(feedback)

    # Example usage
    poi = {'name': 'Cranfield University', 'provider': 'BP Pulse (UK)', 'distance_km': 0.21, 'charging_power_kw': 50}
    # feedback_scores = {
    #     'Cranfield University': {'avg_rating': 4.5, 'count': 10}
    # }
    user_preferences = {
        "stations": {
            "fuel_type": "electric",
            "preferred_providers": ["BP Pulse(UK)", "Ionity", "TotalEnergies"],
            "max_detour_km": 7,
            "avoid": ["highway stations"],
            "charging_power_min_kw": 50,
            "history": []
        },
        "restaurants": {
            "preferred_cuisine_types": [ "African", "Italian", "European", "Asian"],
            "special_needs": ["vegan", "halal"],
            "desired_ambiance": "romantic",
            "average_budget": "moderate",
            "min_rating": 4.2,
            "blacklisted_restaurants": ["McDonald's", "Buffalo Grill"],
            "reservation_preference": True
        },
        "hobbies": {
            "preferred_activity_types": ["museum", "cinema", "bowling"],
            "indoor_or_outdoor": "both",
            "max_budget_per_activity": "moderate",
            "easy_access_or_parking": "yes",
            "min_rating": 4.0,
            "availability": "yes",
            "history": []
        }
    }

    score = compute_score(poi, user_preferences, feedback, POI_type="stations", _feedback=True)
    print(f"Score for {poi['name']}: {score}")