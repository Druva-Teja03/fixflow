from fastapi import APIRouter
from backend.app.schemas import AISuggestRequest, AISuggestResponse
from backend.app.services.ai_service import generate_suggestions

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/suggest", response_model=AISuggestResponse)
def suggest_classification(payload: AISuggestRequest):
    """
    Suggests category, priority, and summary based on issue description using rule-based NLP.
    Never fails or blocks submission.
    """
    result = generate_suggestions(
        description=payload.description,
        user_category=payload.category,
        block=payload.block,
        room=payload.room,
    )
    return AISuggestResponse(**result)
