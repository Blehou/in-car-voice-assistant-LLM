"""
evaluation.py

Evaluates recommendation quality using:
- Precision
- Recall
- User feedback (ratings from 1 to 5)

Also logs evaluations and feedback in JSON format for future learning or fine-tuning.
"""

from typing import List, Dict
from pathlib import Path
from datetime import datetime
import json

# Path to log evaluation data
EVAL_LOG = Path("recommendation_engine/evaluation_log.json")


def collect_user_feedback(recommended: List[Dict]) -> Dict[str, int]:
    """
    Ask the user to rate each recommended station from 1 to 5.
    A rating ≥ 4 is considered a "relevant" recommendation.

    Args:
        recommended (List[Dict]): list of recommended station dictionaries

    Returns:
        Dict[str, int]: mapping of station names to user ratings
    """
    feedback = {}
    print("\nPlease rate the following stations from 1 (not good) to 5 (very good):")

    for station in recommended:
        while True:
            try:
                rating = int(input(f"  - {station['name']} (score: {station.get('score', '-')}) → Rating: "))
                if 1 <= rating <= 5:
                    feedback[station["name"]] = rating
                    break
                else:
                    print("Please enter a number from 1 to 5.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    return feedback


def evaluate_recommendations(recommended: List[str], feedback: Dict[str, int]) -> Dict:
    """
    Calculate precision and recall based on user feedback.
    A station is considered relevant if it has a rating ≥ 4.

    Args:
        recommended (List[str]): list of recommended station names
        feedback (Dict[str, int]): station name → user rating (1 to 5)

    Returns:
        Dict: evaluation results with precision, recall, relevant items, and timestamp
    """
    relevant = [name for name, rating in feedback.items() if rating >= 4]

    recommended_set = set(recommended)
    relevant_set = set(relevant)

    true_positives = recommended_set & relevant_set
    precision = len(true_positives) / len(recommended_set) if recommended_set else 0
    recall = len(true_positives) / len(relevant_set) if relevant_set else 0

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "recommended": recommended,
        "feedback": feedback,
        "relevant": relevant,
        "precision": round(precision, 3),
        "recall": round(recall, 3)
    }

    log_evaluation(result)
    return result


def log_evaluation(entry: Dict):
    """
    Save the evaluation result and feedback into a log file for future analysis.

    Args:
        entry (Dict): evaluation result to store
    """
    if not EVAL_LOG.exists():
        with EVAL_LOG.open("w") as f:
            json.dump([entry], f, indent=4)
    else:
        with EVAL_LOG.open("r+") as f:
            data = json.load(f)
            data.append(entry)
            f.seek(0)
            json.dump(data, f, indent=4)
            f.truncate()
