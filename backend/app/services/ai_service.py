"""
FixFlow Rule-Based AI Suggestion Service.
Extracts category, priority, and maintenance-friendly summary from issue descriptions.
"""

import re
from typing import Dict, Any, Optional

CATEGORY_KEYWORDS = {
    "Equipment": [
        "projector", "monitor", "screen", "mic", "microphone", "speaker",
        "sound", "ac", "air conditioner", "remote", "lab equipment", "pc",
        "computer", "keyboard", "mouse", "printer", "cpu", "hdmi", "display"
    ],
    "Electrical": [
        "light", "switch", "socket", "fan", "wire", "wiring", "spark",
        "sparking", "shock", "bulb", "tube", "power", "electricity", "trip",
        "mcb", "fuse", "outlet", "voltage", "short circuit"
    ],
    "Plumbing": [
        "tap", "leak", "pipe", "piping", "toilet", "flush", "restroom",
        "washroom", "water", "sink", "drain", "drainage", "faucet", "overflow",
        "clogged", "sewage", "basin"
    ],
    "Cleaning": [
        "dirty", "garbage", "trash", "waste", "smell", "stench", "clean",
        "dust", "litter", "spill", "stain", "mess", "dustbin", "unhygienic", "mud"
    ],
    "Furniture": [
        "chair", "bench", "desk", "table", "board", "whiteboard", "blackboard",
        "podium", "cupboard", "shelf", "drawer", "armrest", "cushion"
    ],
    "Internet": [
        "wifi", "wi-fi", "internet", "network", "lan", "ethernet",
        "connectivity", "router", "signal", "broadband", "slow speed", "offline"
    ],
    "Doors/Windows": [
        "door", "window", "lock", "handle", "hinge", "glass", "latch",
        "shutter", "knob", "bolt", "broken glass", "pane"
    ],
}

PRIORITY_KEYWORDS = {
    "Critical": [
        "spark", "sparking", "shock", "fire", "smoke", "flood", "flooding",
        "gas", "smell gas", "exposed wire", "collapse", "hazard", "danger",
        "emergency", "electrocution", "burning"
    ],
    "High": [
        "not working", "no water", "no wifi", "no internet", "leak", "leaking",
        "broken", "damaged", "blackout", "dead", "unusable", "cracked"
    ],
    "Low": [
        "scratch", "paint", "dust", "dusty", "minor", "cosmetic", "faded",
        "peel", "creak", "squeak", "loose knob"
    ],
}


def generate_suggestions(
    description: str,
    user_category: Optional[str] = None,
    block: Optional[str] = None,
    room: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate category, priority, and summary from description using deterministic rule-based NLP.
    Never raises an unhandled exception.
    """
    try:
        text = (description or "").lower()

        # 1. Category Classification
        category_scores: Dict[str, int] = {cat: 0 for cat in CATEGORY_KEYWORDS}
        total_category_matches = 0

        for cat, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                # Word-boundary matching
                pattern = r"\b" + re.escape(kw) + r"\b"
                matches = len(re.findall(pattern, text))
                if matches > 0:
                    category_scores[cat] += matches
                    total_category_matches += matches

        best_category = "Other"
        max_cat_score = 0
        for cat, score in category_scores.items():
            if score > max_cat_score:
                max_cat_score = score
                best_category = cat

        # 2. Priority Classification
        priority_scores = {"Critical": 0, "High": 0, "Low": 0}
        total_priority_matches = 0

        for prio, keywords in PRIORITY_KEYWORDS.items():
            for kw in keywords:
                pattern = r"\b" + re.escape(kw) + r"\b"
                matches = len(re.findall(pattern, text))
                if matches > 0:
                    priority_scores[prio] += matches
                    total_priority_matches += matches

        # Critical takes precedence if found
        if priority_scores["Critical"] > 0:
            best_priority = "Critical"
        elif priority_scores["High"] > 0:
            best_priority = "High"
        elif priority_scores["Low"] > 0 and priority_scores["High"] == 0:
            best_priority = "Low"
        else:
            best_priority = "Medium"

        # 3. Smart Summary
        # Extract first sentence, strip extra whitespace, trim to 120 chars
        clean_desc = re.sub(r"\s+", " ", description or "").strip()
        sentences = re.split(r"(?<=[.!?])\s+", clean_desc)
        first_sentence = sentences[0] if sentences else clean_desc
        if len(first_sentence) > 120:
            summary = first_sentence[:117].rstrip() + "..."
        else:
            summary = first_sentence or "Campus maintenance issue."

        # 4. Confidence calculation
        # Base 0.30, increments with matched keywords up to 0.95
        confidence = 0.30
        if max_cat_score > 0:
            confidence += 0.25 + min(0.20, (max_cat_score - 1) * 0.05)
        if total_priority_matches > 0:
            confidence += 0.20
        confidence = round(min(0.95, confidence), 2)

        return {
            "category": best_category,
            "priority": best_priority,
            "summary": summary,
            "confidence": confidence,
            "source": "rules",
        }

    except Exception:
        # Fallback safe values if parsing fails
        clean_desc = (description or "").strip()
        return {
            "category": user_category or "Other",
            "priority": "Medium",
            "summary": clean_desc[:120] if clean_desc else "Campus issue reported.",
            "confidence": 0.30,
            "source": "rules",
        }
