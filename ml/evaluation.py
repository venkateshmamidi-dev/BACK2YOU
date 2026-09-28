"""
Back2You: Machine Learning & Matching Engine Evaluation Module
GDG on Campus — AI/ML & Data Science Problem Statement

This module computes rigorous quantitative evaluation metrics on the benchmark dataset:
- Matching Accuracy
- Precision@1, Precision@3, Precision@5
- False Match Rate (FMR)
- Multi-modal Ablation Experiment: Text-Only vs Image/Attribute-Only vs Combined AI Matching
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path

# Add project root to sys.path
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.services.nlp import generate_text_embedding, calculate_text_similarity
from backend.services.vision import generate_image_embedding, calculate_image_similarity
from backend.services.location import calculate_location_similarity, calculate_time_similarity
from backend.services.matching import calculate_attribute_similarity, evaluate_match_pair

DATASET_PATH = BASE_DIR / "ml" / "dataset" / "test_dataset.json"

def load_dataset() -> Dict[str, Any]:
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_evaluation(mode: str = "combined") -> Dict[str, Any]:
    """
    Runs evaluation over the benchmark dataset.
    mode options:
      - 'combined': Full multi-modal Back2You system (Vision + NLP + Spatial + Temporal + Attributes)
      - 'text_only': NLP semantic description matching only
      - 'visual_attribute_only': Attributes & Visual match only (No NLP)
    """
    data = load_dataset()
    items = data["items"]

    lost_items = [i for i in items if i["type"] == "lost" and i.get("ground_truth_match_id")]
    found_items = [i for i in items if i["type"] == "found"]

    weights_map = {
        "combined": {
            "weight_image": 0.40,
            "weight_text": 0.30,
            "weight_location": 0.15,
            "weight_time": 0.10,
            "weight_attributes": 0.05
        },
        "text_only": {
            "weight_image": 0.0,
            "weight_text": 1.0,
            "weight_location": 0.0,
            "weight_time": 0.0,
            "weight_attributes": 0.0
        },
        "visual_attribute_only": {
            "weight_image": 0.50,
            "weight_text": 0.0,
            "weight_location": 0.20,
            "weight_time": 0.10,
            "weight_attributes": 0.20
        }
    }

    selected_weights = weights_map.get(mode, weights_map["combined"])

    # Precompute embeddings
    cached_embeddings = {}
    for itm in items:
        text_content = f"{itm.get('title', '')} {itm.get('description', '')} {itm.get('brand', '')} {itm.get('color', '')}"
        cached_embeddings[itm["id"]] = {
            "text_embedding": generate_text_embedding(text_content),
            "image_embedding": None  # Handled via attribute & synthetic color visual vectors if no local image file
        }

    p_at_1_hits = 0
    p_at_3_hits = 0
    p_at_5_hits = 0
    false_match_count = 0
    detailed_results = []

    for lost in lost_items:
        target_gt = lost["ground_truth_match_id"]
        candidates_scored = []

        for found in found_items:
            breakdown = evaluate_match_pair(
                lost_item=lost,
                found_item=found,
                lost_embeddings=cached_embeddings.get(lost["id"]),
                found_embeddings=cached_embeddings.get(found["id"]),
                weights_override=selected_weights
            )
            candidates_scored.append({
                "found_id": found["id"],
                "score": breakdown["final_confidence"],
                "breakdown": breakdown
            })

        # Rank descending
        candidates_scored.sort(key=lambda x: x["score"], reverse=True)
        ranked_ids = [c["found_id"] for c in candidates_scored]

        is_p1 = (ranked_ids[0] == target_gt) if len(ranked_ids) > 0 else False
        is_p3 = (target_gt in ranked_ids[:3]) if len(ranked_ids) >= 3 else False
        is_p5 = (target_gt in ranked_ids[:5]) if len(ranked_ids) >= 5 else False

        if is_p1:
            p_at_1_hits += 1
        else:
            # If top match had high confidence >= 0.70 but was incorrect
            if candidates_scored[0]["score"] >= 0.70:
                false_match_count += 1

        if is_p3:
            p_at_3_hits += 1
        if is_p5:
            p_at_5_hits += 1

        top_match_info = candidates_scored[0]
        detailed_results.append({
            "lost_id": lost["id"],
            "lost_title": lost["title"],
            "ground_truth": target_gt,
            "top_predicted": top_match_info["found_id"],
            "top_confidence": top_match_info["score"],
            "matched_correctly_top1": is_p1,
            "matched_in_top3": is_p3
        })

    num_queries = len(lost_items)
    p_at_1 = round(p_at_1_hits / float(num_queries), 3) if num_queries > 0 else 0.0
    p_at_3 = round(p_at_3_hits / float(num_queries), 3) if num_queries > 0 else 0.0
    p_at_5 = round(p_at_5_hits / float(num_queries), 3) if num_queries > 0 else 0.0
    false_match_rate = round(false_match_count / float(num_queries), 3) if num_queries > 0 else 0.0
    accuracy = p_at_1

    return {
        "evaluation_type": "Prototype Evaluation",
        "dataset_name": data["dataset_name"],
        "mode": mode,
        "queries_evaluated": num_queries,
        "total_candidates": len(found_items),
        "accuracy": accuracy,
        "precision_at_1": p_at_1,
        "precision_at_3": p_at_3,
        "precision_at_5": p_at_5,
        "false_match_rate": false_match_rate,
        "detailed_results": detailed_results
    }

def run_ablation_experiment() -> Dict[str, Any]:
    """
    Executes the multi-modal comparison experiment:
    Text-Only vs Visual/Attribute-Only vs Combined AI Matching.
    """
    text_results = run_evaluation(mode="text_only")
    vis_results = run_evaluation(mode="visual_attribute_only")
    combined_results = run_evaluation(mode="combined")

    summary_df = pd.DataFrame([
        {
            "Approach": "Text-Only (NLP)",
            "Precision@1": f"{text_results['precision_at_1'] * 100:.1f}%",
            "Precision@3": f"{text_results['precision_at_3'] * 100:.1f}%",
            "Precision@5": f"{text_results['precision_at_5'] * 100:.1f}%",
            "False Match Rate": f"{text_results['false_match_rate'] * 100:.1f}%"
        },
        {
            "Approach": "Vision + Attributes Only",
            "Precision@1": f"{vis_results['precision_at_1'] * 100:.1f}%",
            "Precision@3": f"{vis_results['precision_at_3'] * 100:.1f}%",
            "Precision@5": f"{vis_results['precision_at_5'] * 100:.1f}%",
            "False Match Rate": f"{vis_results['false_match_rate'] * 100:.1f}%"
        },
        {
            "Approach": "Combined Back2You (Vision + NLP + Location + Time)",
            "Precision@1": f"{combined_results['precision_at_1'] * 100:.1f}%",
            "Precision@3": f"{combined_results['precision_at_3'] * 100:.1f}%",
            "Precision@5": f"{combined_results['precision_at_5'] * 100:.1f}%",
            "False Match Rate": f"{combined_results['false_match_rate'] * 100:.1f}%"
        }
    ])

    return {
        "status": "success",
        "benchmark": "Prototype Evaluation",
        "comparison_table": summary_df.to_dict(orient="records"),
        "raw": {
            "text_only": text_results,
            "visual_attribute_only": vis_results,
            "combined": combined_results
        }
    }

if __name__ == "__main__":
    print("\n=======================================================")
    print(" BACK2YOU: AI/ML MATCHING ENGINE EVALUATION (PROTOTYPE)")
    print("=======================================================\n")
    exp = run_ablation_experiment()
    df = pd.DataFrame(exp["comparison_table"])
    print(df.to_string(index=False))
    print("\nEvaluation successfully completed.\n")
