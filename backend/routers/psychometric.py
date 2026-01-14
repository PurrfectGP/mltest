from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.db_models import User, PsychometricResponse
from backend.schemas import (
    PsychometricQuestion,
    QuestionOption,
    QuestionType,
    PsychometricSubmission,
    PsychometricQuestionsResponse,
    PsychometricResultResponse
)
from backend.auth import get_current_user

router = APIRouter(prefix="/api/psychometric", tags=["psychometric"])

# The "Fixed Five" psychometric questions
FIXED_FIVE_QUESTIONS: List[PsychometricQuestion] = [
    PsychometricQuestion(
        id="dinner_check",
        name="Dinner Check",
        scenario="You're out at a nice restaurant with a group of friends celebrating someone's birthday. When the check arrives, you notice it wasn't split evenly - some people ordered much more than others. The birthday person suggests just splitting it equally.",
        question="What do you do?",
        type=QuestionType.MULTIPLE_CHOICE,
        options=[
            QuestionOption(
                id="dc_a",
                text="Speak up and suggest itemizing the bill so everyone pays for what they ordered",
                traits={"assertiveness": 0.8, "fairness": 0.9, "greed": 0.3}
            ),
            QuestionOption(
                id="dc_b",
                text="Stay quiet and pay the equal split to avoid any awkwardness",
                traits={"agreeableness": 0.8, "conflict_avoidance": 0.9, "sloth": 0.4}
            ),
            QuestionOption(
                id="dc_c",
                text="Quietly mention to one friend that the split seems unfair and see if they agree",
                traits={"diplomacy": 0.7, "social_awareness": 0.6, "envy": 0.3}
            ),
            QuestionOption(
                id="dc_d",
                text="Offer to cover a larger portion yourself to keep everyone happy",
                traits={"generosity": 0.9, "pride": 0.5, "people_pleasing": 0.7}
            )
        ]
    ),
    PsychometricQuestion(
        id="tech_meltdown",
        name="Tech Meltdown",
        scenario="You're working on an important project with a tight deadline. Suddenly, your computer crashes and you lose several hours of unsaved work. Your colleague, who was supposed to remind everyone to save regularly, is sitting nearby.",
        question="What's your immediate reaction?",
        type=QuestionType.MULTIPLE_CHOICE,
        options=[
            QuestionOption(
                id="tm_a",
                text="Take a deep breath, accept it happened, and calmly start rebuilding the work",
                traits={"emotional_stability": 0.9, "resilience": 0.8, "sloth": 0.2}
            ),
            QuestionOption(
                id="tm_b",
                text="Feel frustrated and need to vent to someone about what happened",
                traits={"expressiveness": 0.7, "wrath": 0.5, "social_need": 0.6}
            ),
            QuestionOption(
                id="tm_c",
                text="Blame yourself for not saving more often and feel anxious about the deadline",
                traits={"self_criticism": 0.8, "anxiety": 0.7, "conscientiousness": 0.6}
            ),
            QuestionOption(
                id="tm_d",
                text="Feel annoyed at your colleague for not sending that reminder",
                traits={"external_attribution": 0.7, "wrath": 0.6, "envy": 0.4}
            )
        ]
    ),
    PsychometricQuestion(
        id="found_wallet",
        name="Found Wallet",
        scenario="While walking home, you find a wallet on the ground. Inside there's $500 in cash, credit cards, and an ID. The address on the ID shows the owner lives about 20 minutes away in the opposite direction of your home.",
        question="What do you do?",
        type=QuestionType.MULTIPLE_CHOICE,
        options=[
            QuestionOption(
                id="fw_a",
                text="Immediately walk to the address and return the wallet in person",
                traits={"integrity": 0.9, "altruism": 0.8, "conscientiousness": 0.7}
            ),
            QuestionOption(
                id="fw_b",
                text="Take it to the nearest police station and let them handle it",
                traits={"rule_following": 0.8, "practicality": 0.7, "sloth": 0.3}
            ),
            QuestionOption(
                id="fw_c",
                text="Mail the wallet back with a nice note, keeping the cash as a 'finder's fee'",
                traits={"rationalization": 0.6, "greed": 0.7, "partial_integrity": 0.4}
            ),
            QuestionOption(
                id="fw_d",
                text="Try to contact the person via social media to arrange a return",
                traits={"resourcefulness": 0.7, "tech_savvy": 0.6, "social_connection": 0.5}
            )
        ]
    ),
    PsychometricQuestion(
        id="restaurant_choice",
        name="Restaurant Choice",
        scenario="Your friend group is trying to decide where to eat. You really want to try a new place you've been excited about, but others are suggesting the usual spots. One friend seems indifferent, two want the usual, and one seems open to new ideas.",
        question="How do you handle this?",
        type=QuestionType.MULTIPLE_CHOICE,
        options=[
            QuestionOption(
                id="rc_a",
                text="Make a passionate case for why the new place would be amazing for everyone",
                traits={"persuasiveness": 0.8, "enthusiasm": 0.7, "pride": 0.5}
            ),
            QuestionOption(
                id="rc_b",
                text="Suggest the new place but quickly agree with the majority if there's pushback",
                traits={"agreeableness": 0.7, "conflict_avoidance": 0.6, "sloth": 0.4}
            ),
            QuestionOption(
                id="rc_c",
                text="Propose a compromise - usual place today, new place next time with commitment",
                traits={"diplomacy": 0.8, "strategic_thinking": 0.7, "patience": 0.6}
            ),
            QuestionOption(
                id="rc_d",
                text="Go along with whatever everyone else wants - food is food",
                traits={"low_attachment": 0.6, "flexibility": 0.7, "gluttony": 0.2}
            )
        ]
    ),
    PsychometricQuestion(
        id="spontaneous_trip",
        name="Spontaneous Trip",
        scenario="It's Friday afternoon and a friend calls with an unexpected opportunity: a free cabin for the weekend, leaving in 3 hours. You have some loose plans but nothing urgent. The cabin is beautiful but remote with no cell service.",
        question="What's your response?",
        type=QuestionType.MULTIPLE_CHOICE,
        options=[
            QuestionOption(
                id="st_a",
                text="Immediately say yes and start packing - adventure awaits!",
                traits={"spontaneity": 0.9, "openness": 0.8, "lust": 0.4}
            ),
            QuestionOption(
                id="st_b",
                text="Ask for details about who's going, what to bring, and logistics first",
                traits={"conscientiousness": 0.7, "planning": 0.8, "anxiety": 0.4}
            ),
            QuestionOption(
                id="st_c",
                text="Decline - you prefer to have plans in advance and the no-service thing worries you",
                traits={"structure_need": 0.8, "anxiety": 0.6, "sloth": 0.5}
            ),
            QuestionOption(
                id="st_d",
                text="Say maybe, then spend the next hour overthinking before deciding last minute",
                traits={"indecisiveness": 0.8, "anxiety": 0.7, "fomo": 0.6}
            )
        ]
    )
]


@router.get("/questions", response_model=PsychometricQuestionsResponse)
async def get_questions(
    current_user: User = Depends(get_current_user)
):
    """Get all Fixed Five psychometric questions."""
    return PsychometricQuestionsResponse(
        questions=FIXED_FIVE_QUESTIONS,
        total=len(FIXED_FIVE_QUESTIONS)
    )


@router.post("/submit", response_model=PsychometricResultResponse)
async def submit_answers(
    submission: PsychometricSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit answers to psychometric questions."""
    # Validate all questions are answered
    question_ids = {q.id for q in FIXED_FIVE_QUESTIONS}
    answered_ids = {a.question_id for a in submission.answers}

    missing = question_ids - answered_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing answers for questions: {', '.join(missing)}"
        )

    # Build question lookup
    question_lookup = {q.id: q for q in FIXED_FIVE_QUESTIONS}

    # Aggregate traits from answers
    aggregated_traits = {}

    for answer in submission.answers:
        question = question_lookup.get(answer.question_id)
        if not question:
            continue

        # Find selected option
        selected_option = None
        for opt in question.options:
            if opt.id == answer.selected_option_id:
                selected_option = opt
                break

        if not selected_option:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid option for question {answer.question_id}"
            )

        # Store response in database
        db_response = PsychometricResponse(
            user_id=current_user.id,
            question_id=answer.question_id,
            selected_option_id=answer.selected_option_id,
            traits_extracted=selected_option.traits
        )
        db.add(db_response)

        # Aggregate traits
        for trait, weight in selected_option.traits.items():
            if trait not in aggregated_traits:
                aggregated_traits[trait] = []
            aggregated_traits[trait].append(weight)

    # Calculate average trait scores
    trait_scores = {}
    for trait, weights in aggregated_traits.items():
        trait_scores[trait] = round(sum(weights) / len(weights), 2)

    # Update user progress
    current_user.psychometric_complete = True
    db.commit()

    return PsychometricResultResponse(
        success=True,
        message="Psychometric assessment completed successfully",
        traits_detected=trait_scores
    )


@router.get("/status")
async def get_psychometric_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get psychometric completion status for current user."""
    responses = db.query(PsychometricResponse).filter(
        PsychometricResponse.user_id == current_user.id
    ).all()

    return {
        "complete": current_user.psychometric_complete,
        "questions_answered": len(responses),
        "total_questions": len(FIXED_FIVE_QUESTIONS)
    }
