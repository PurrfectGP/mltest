from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from enum import Enum


class QuestionType(str, Enum):
    """Types of psychometric questions."""
    MULTIPLE_CHOICE = "multiple_choice"
    SCALE = "scale"
    OPEN_ENDED = "open_ended"


class QuestionOption(BaseModel):
    """Schema for a question option."""
    id: str
    text: str
    traits: Dict[str, float] = Field(
        default_factory=dict,
        description="Trait weights for this option"
    )


class PsychometricQuestion(BaseModel):
    """Schema for a psychometric question."""
    id: str
    name: str
    scenario: str
    question: str
    type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: List[QuestionOption]


class QuestionAnswer(BaseModel):
    """Schema for answering a question."""
    question_id: str
    selected_option_id: Optional[str] = None
    open_response: Optional[str] = None
    scale_value: Optional[int] = Field(None, ge=1, le=10)


class PsychometricSubmission(BaseModel):
    """Schema for submitting all psychometric answers."""
    answers: List[QuestionAnswer]


class PsychometricQuestionsResponse(BaseModel):
    """Schema for returning all questions."""
    questions: List[PsychometricQuestion]
    total: int


class PsychometricResultResponse(BaseModel):
    """Schema for psychometric completion response."""
    success: bool
    message: str
    traits_detected: Dict[str, float] = Field(default_factory=dict)
