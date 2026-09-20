"""
FixFlow Duplicate Detection Service.
Detects similar active campus issues based on location, category, Jaccard token similarity,
and SequenceMatcher string similarity.
"""

import re
import difflib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.models import Issue, IssueStatus

STOP_WORDS = {
    "the", "is", "at", "which", "on", "a", "an", "in", "of", "to", "and",
    "for", "with", "it", "this", "that", "my", "our", "there", "are", "was",
    "were", "has", "have", "had", "be", "been", "from", "by", "as", "about"
}


def normalize_text(text: str) -> List[str]:
    """Lowercase, strip non-alphanumeric punctuation, and filter stopwords."""
    if not text:
        return []
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    tokens = [t for t in cleaned.split() if t and t not in STOP_WORDS and len(t) > 1]
    return tokens


def calculate_similarity_score(
    text_a: str,
    text_b: str,
    same_room: bool,
    same_category: bool,
) -> float:
    """
    Computes hybrid similarity score:
    0.6 * Jaccard token overlap + 0.4 * difflib SequenceMatcher ratio,
    with +0.2 bonus for exact room and +0.1 bonus for identical category (capped at 1.0).
    """
    tokens_a = set(normalize_text(text_a))
    tokens_b = set(normalize_text(text_b))

    # 1. Jaccard token overlap
    union = tokens_a | tokens_b
    intersection = tokens_a & tokens_b
    jaccard = (len(intersection) / len(union)) if union else 0.0

    # 2. SequenceMatcher ratio on cleaned string representation
    norm_str_a = " ".join(normalize_text(text_a))
    norm_str_b = " ".join(normalize_text(text_b))
    seq_ratio = difflib.SequenceMatcher(None, norm_str_a, norm_str_b).ratio() if (norm_str_a and norm_str_b) else 0.0

    # Base score
    score = (0.6 * jaccard) + (0.4 * seq_ratio)

    # Bonuses
    if same_room:
        score += 0.20
    if same_category:
        score += 0.10

    return min(1.0, round(score, 3))


def find_duplicate_candidates(
    db: Session,
    category: str,
    block: str,
    description: str,
    room: Optional[str] = None,
    threshold: float = 0.55,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Queries open issues from the last 30 days in the same block,
    scores each against the new description, and returns the top matches with score >= threshold.
    """
    thirty_days_ago = datetime.now() - timedelta(days=30)

    # 1. Candidate SQL filtering
    query = (
        db.query(Issue)
        .filter(Issue.status != IssueStatus.RESOLVED)
        .filter(Issue.block == block)
        .filter(Issue.created_at >= thirty_days_ago)
    )

    if room and room.strip():
        r_str = room.strip()
        query = query.filter((Issue.room == r_str) | (Issue.room.is_(None)) | (Issue.room == ""))

    candidates = query.all()
    scored_results = []

    target_room = (room or "").strip().lower()
    target_cat = (category or "").strip().lower()

    for cand in candidates:
        cand_room = (cand.room or "").strip().lower()
        cand_cat = (cand.category.value if hasattr(cand.category, "value") else str(cand.category)).strip().lower()

        # Check room match
        same_room = False
        if target_room and cand_room and target_room == cand_room:
            same_room = True

        same_category = (target_cat == cand_cat)

        # Combined text for comparison (title + description)
        text_a = f"{cand.title} {cand.description}"
        text_b = description

        score = calculate_similarity_score(
            text_a=text_a,
            text_b=text_b,
            same_room=same_room,
            same_category=same_category,
        )

        if score >= threshold:
            scored_results.append({
                "issue_id": cand.issue_id,
                "title": cand.title,
                "description": cand.description,
                "category": cand.category.value if hasattr(cand.category, "value") else str(cand.category),
                "block": cand.block,
                "building": cand.building,
                "room": cand.room,
                "status": cand.status.value if hasattr(cand.status, "value") else str(cand.status),
                "support_count": cand.support_count,
                "score": score,
            })

    # Sort descending by similarity score
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:limit]
