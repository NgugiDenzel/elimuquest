from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import admin_user, optional_current_user
from app.db.session import get_db
from app.models import User
from app.models.mathematics import LearnerContentFeedback, MathematicsReviewDecision
from app.schemas.mathematics import (
    LearnerContentFeedbackRequest,
    MathematicsAnswerFeedback,
    MathematicsAnswerRequest,
    MathematicsReviewDecisionRequest,
)
from app.services.mathematics import (
    check_mathematics_answer,
    mathematics_curriculum,
    mathematics_lesson,
)
from app.services.mathematics_coverage import (
    ALIGNMENT_STATUSES,
    CONTENT_STATUSES,
    PUBLICATION_STATUSES,
    REVIEW_STATUSES,
    mathematics_coverage_report,
    mathematics_coverage_validation_report,
    mathematics_number_systems_educator_review_pack,
    mathematics_question_quality_report,
)

router = APIRouter()


@router.get("/mathematics/curriculum")
def mathematics_learning_path():
    return mathematics_curriculum()


def _mathematics_review_decision_map(db: Session) -> dict[tuple[str, str], str]:
    decisions = db.scalars(
        select(MathematicsReviewDecision).order_by(
            MathematicsReviewDecision.created_at,
            MathematicsReviewDecision.id,
        )
    ).all()
    return {
        (decision.item_type, decision.item_id): decision.decision
        for decision in decisions
    }


@router.get("/mathematics/coverage")
def mathematics_coverage(
    level_id: str | None = None,
    unit_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    alignment_status: str | None = None,
    review_status: str | None = None,
    publication_status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    report = mathematics_coverage_report(_mathematics_review_decision_map(db))
    valid_level_ids = {level["id"] for level in report["levels"]}
    valid_unit_ids = {
        unit["id"] for level in report["levels"] for unit in level["units"]
    }
    if level_id is not None and level_id not in valid_level_ids:
        raise HTTPException(status_code=422, detail="Unknown Mathematics level_id")
    if unit_id is not None and unit_id not in valid_unit_ids:
        raise HTTPException(status_code=422, detail="Unknown Mathematics unit_id")
    for name, value, allowed in (
        ("status", status_filter, CONTENT_STATUSES),
        ("alignment_status", alignment_status, ALIGNMENT_STATUSES | {"no_lesson_evidence"}),
        ("review_status", review_status, REVIEW_STATUSES),
        ("publication_status", publication_status, PUBLICATION_STATUSES),
    ):
        if value is not None and value not in allowed:
            raise HTTPException(
                status_code=422,
                detail=f"Unsupported {name}; expected one of {', '.join(sorted(allowed))}",
            )

    items = report["subtopics"]
    if level_id is not None:
        items = [item for item in items if item["level_id"] == level_id]
    if unit_id is not None:
        items = [item for item in items if item["unit_id"] == unit_id]
    if status_filter is not None:
        items = [item for item in items if item["content_status"] == status_filter]
    if alignment_status is not None:
        items = [
            item for item in items if item["alignment_status"] == alignment_status
        ]
    if review_status is not None:
        items = [
            item
            for item in items
            if item["educator_review_status"] == review_status
        ]
    if publication_status is not None:
        items = [
            item
            for item in items
            if item["publication_status"] == publication_status
        ]
    total = len(items)
    start = (page - 1) * page_size
    return {
        **report,
        "items": items[start : start + page_size],
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size,
        },
        "filters": {
            "level_id": level_id,
            "unit_id": unit_id,
            "status": status_filter,
            "alignment_status": alignment_status,
            "review_status": review_status,
            "publication_status": publication_status,
        },
    }


@router.get("/mathematics/coverage/validation")
def mathematics_coverage_validation():
    return mathematics_coverage_validation_report()


@router.get("/mathematics/coverage/questions/quality")
def mathematics_question_quality():
    return mathematics_question_quality_report()


def _number_systems_review_items():
    pack = mathematics_number_systems_educator_review_pack()
    curriculum = mathematics_curriculum()
    topic_ids = {topic["topic_id"] for topic in pack["topics"]}
    lesson_ids = {
        lesson["id"]
        for level in curriculum["levels"]
        for unit in level["units"]
        if unit["id"] == "number-systems"
        for lesson in unit["lessons"]
    }
    question_ids = {
        question["question_id"]
        for topic in pack["topics"]
        for question in topic["questions"]
    } | {question["question_id"] for question in pack["unlinked_questions"]}
    alignment_ids = {
        f"{relationship['lesson_id']}::{topic['topic_id']}"
        for topic in pack["topics"]
        for relationship in topic["lesson_relationships"]
    }
    outcomes = {
        evidence["outcome_id"]: evidence["outcome"]
        for topic in pack["topics"]
        for relationship in topic["lesson_relationships"]
        for evidence in relationship["outcome_evidence"]
    }
    return pack, topic_ids, alignment_ids, lesson_ids, question_ids, outcomes


def _review_dashboard(
    pack: dict[str, Any],
    topic_ids: set[str],
    alignment_ids: set[str],
    lesson_ids: set[str],
    question_ids: set[str],
    outcomes: dict[str, str],
    latest: dict[tuple[str, str], MathematicsReviewDecision],
) -> dict[str, Any]:
    def count(item_type: str, identifiers: set[str], decision: str | None = None) -> int:
        return sum(
            latest.get((item_type, identifier)) is not None
            and (
                latest[(item_type, identifier)].decision != "pending_review"
                if decision is None
                else latest[(item_type, identifier)].decision == decision
            )
            for identifier in identifiers
        )

    item_sets = {
        "topic": topic_ids,
        "alignment": alignment_ids,
        "lesson": lesson_ids,
        "outcome": set(outcomes),
        "question": question_ids,
    }
    total_items = sum(len(items) for items in item_sets.values())
    reviewed = sum(
        count(item_type, identifiers)
        for item_type, identifiers in item_sets.items()
    )
    return {
        "total_topics": len(topic_ids),
        "total_lessons": len(lesson_ids),
        "lessons_awaiting_review": len(lesson_ids) - count("lesson", lesson_ids),
        "alignments_total": len(alignment_ids),
        "alignments_approved": count("alignment", alignment_ids, "approved"),
        "alignments_awaiting_review": len(alignment_ids)
        - count("alignment", alignment_ids),
        "learning_outcomes_total": len(outcomes),
        "learning_outcomes_approved": count("outcome", set(outcomes), "approved"),
        "learning_outcomes_requiring_revision": count(
            "outcome", set(outcomes), "revision_requested"
        )
        + count("outcome", set(outcomes), "rejected"),
        "questions_total": len(question_ids),
        "questions_awaiting_review": len(question_ids) - count("question", question_ids),
        "questions_approved": count("question", question_ids, "approved"),
        "questions_requiring_correction": count(
            "question", question_ids, "revision_requested"
        )
        + count("question", question_ids, "rejected"),
        "unresolved_mathematical_issues": sum(
            event.mathematical_error_flag and event.decision != "approved"
            for event in latest.values()
        ),
        "reviewed_items": reviewed,
        "total_review_items": total_items,
        "review_completion_percent": round(reviewed * 100 / total_items)
        if total_items
        else 0,
    }


@router.get("/admin/mathematics/number-systems/review")
def number_systems_educator_review(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
):
    pack, topic_ids, alignment_ids, lesson_ids, question_ids, outcomes = (
        _number_systems_review_items()
    )
    decisions = db.scalars(
        select(MathematicsReviewDecision)
        .options(joinedload(MathematicsReviewDecision.reviewer))
        .order_by(MathematicsReviewDecision.created_at, MathematicsReviewDecision.id)
    ).all()
    latest: dict[tuple[str, str], MathematicsReviewDecision] = {}
    for event in decisions:
        latest[(event.item_type, event.item_id)] = event

    def review_state(item_type: str, item_id: str) -> dict[str, Any]:
        event = latest.get((item_type, item_id))
        if event is None:
            return {
                "decision": "pending_review",
                "reviewer": None,
                "reviewed_at": None,
                "comments": "",
                "correction": "",
                "mathematical_error_flag": False,
            }
        return {
            "decision": event.decision,
            "reviewer": event.reviewer.email,
            "reviewed_at": event.created_at,
            "comments": event.comments,
            "correction": event.correction,
            "mathematical_error_flag": event.mathematical_error_flag,
        }

    for topic in pack["topics"]:
        topic["review_state"] = review_state("topic", topic["topic_id"])
        for relationship in topic["lesson_relationships"]:
            relationship["review_state"] = review_state(
                "lesson", relationship["lesson_id"]
            )
            relationship["alignment_review_state"] = review_state(
                "alignment",
                f"{relationship['lesson_id']}::{topic['topic_id']}",
            )
            for evidence in relationship["outcome_evidence"]:
                evidence["review_state"] = review_state(
                    "outcome", evidence["outcome_id"]
                )
        for question in topic["questions"]:
            question["review_state"] = review_state(
                "question", question["question_id"]
            )
    for question in pack["unlinked_questions"]:
        question["review_state"] = review_state("question", question["question_id"])

    history = [
        {
            "id": str(event.id),
            "item_type": event.item_type,
            "item_id": event.item_id,
            "decision": event.decision,
            "comments": event.comments,
            "correction": event.correction,
            "mathematical_error_flag": event.mathematical_error_flag,
            "reviewer": event.reviewer.email,
            "previous_state": event.previous_state,
            "new_state": event.new_state,
            "created_at": event.created_at,
        }
        for event in reversed(decisions)
    ]
    return {
        "dashboard": _review_dashboard(
            pack, topic_ids, alignment_ids, lesson_ids, question_ids, outcomes, latest
        ),
        "review_pack": pack,
        "history": history,
    }


@router.post("/admin/mathematics/number-systems/review-decisions", status_code=201)
def submit_number_systems_review_decision(
    payload: MathematicsReviewDecisionRequest,
    db: Session = Depends(get_db),
    reviewer: User = Depends(admin_user),
):
    _, topic_ids, alignment_ids, lesson_ids, question_ids, outcomes = (
        _number_systems_review_items()
    )
    valid_ids = {
        "topic": topic_ids,
        "alignment": alignment_ids,
        "lesson": lesson_ids,
        "outcome": set(outcomes),
        "question": question_ids,
    }[payload.item_type]
    if payload.item_id not in valid_ids:
        raise HTTPException(status_code=404, detail="Number Systems review item not found")
    if payload.decision in {"revision_requested", "rejected"} and not (
        payload.comments.strip() or payload.correction.strip()
    ):
        raise HTTPException(
            status_code=422,
            detail="Add a comment or correction when requesting changes or rejecting an item",
        )
    if payload.mathematical_error_flag and not (
        payload.comments.strip() or payload.correction.strip()
    ):
        raise HTTPException(
            status_code=422,
            detail="Describe the suspected mathematical error or correction",
        )
    previous = db.scalar(
        select(MathematicsReviewDecision)
        .where(
            MathematicsReviewDecision.item_type == payload.item_type,
            MathematicsReviewDecision.item_id == payload.item_id,
        )
        .order_by(
            MathematicsReviewDecision.created_at.desc(),
            MathematicsReviewDecision.id.desc(),
        )
        .limit(1)
    )
    previous_state = previous.decision if previous else "pending_review"
    allowed_transitions = {
        "pending_review": {"approved", "revision_requested", "rejected"},
        "approved": {"pending_review", "revision_requested", "rejected"},
        "revision_requested": {"pending_review", "approved", "rejected"},
        "rejected": {"pending_review", "revision_requested"},
    }
    if payload.decision not in allowed_transitions[previous_state]:
        raise HTTPException(
            status_code=409,
            detail=f"Review decision cannot transition from {previous_state} to {payload.decision}",
        )
    event = MathematicsReviewDecision(
        item_type=payload.item_type,
        item_id=payload.item_id,
        decision=payload.decision,
        comments=payload.comments.strip(),
        correction=payload.correction.strip(),
        mathematical_error_flag=payload.mathematical_error_flag,
        previous_state=previous_state,
        new_state=payload.decision,
        reviewer_id=reviewer.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {
        "id": str(event.id),
        "item_type": event.item_type,
        "item_id": event.item_id,
        "decision": event.decision,
        "comments": event.comments,
        "correction": event.correction,
        "mathematical_error_flag": event.mathematical_error_flag,
        "reviewer": reviewer.email,
        "previous_state": event.previous_state,
        "new_state": event.new_state,
        "created_at": event.created_at,
    }


@router.post("/mathematics/feedback", status_code=201)
def submit_number_systems_feedback(
    payload: LearnerContentFeedbackRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(optional_current_user),
):
    lesson = mathematics_lesson(payload.lesson_id)
    if lesson is None or lesson.get("unit_id") != "number-systems":
        raise HTTPException(status_code=404, detail="Number Systems lesson not found")
    if payload.question_id and not any(
        question["id"] == payload.question_id for question in lesson.get("questions", [])
    ):
        raise HTTPException(
            status_code=404, detail="Question not found for this Number Systems lesson"
        )
    feedback = LearnerContentFeedback(
        user_id=user.id if user else None,
        lesson_id=payload.lesson_id,
        question_id=payload.question_id,
        category=payload.category,
        message=payload.message.strip(),
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return {"id": str(feedback.id), "status": "received"}


@router.get("/admin/mathematics/number-systems/feedback")
def number_systems_feedback_inbox(
    db: Session = Depends(get_db),
    _: User = Depends(admin_user),
):
    items = db.scalars(
        select(LearnerContentFeedback)
        .options(joinedload(LearnerContentFeedback.user))
        .order_by(
            LearnerContentFeedback.created_at.desc(),
            LearnerContentFeedback.id.desc(),
        )
    ).all()
    return {
        "items": [
            {
                "id": str(item.id),
                "lesson_id": item.lesson_id,
                "question_id": item.question_id,
                "category": item.category,
                "message": item.message,
                "submitted_by": item.user.email if item.user else "guest",
                "created_at": item.created_at,
            }
            for item in items
        ],
        "count": len(items),
    }


@router.get("/mathematics/lessons/{lesson_id}")
def mathematics_lesson_detail(lesson_id: str):
    lesson = mathematics_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Mathematics lesson not found")
    return lesson


@router.post(
    "/mathematics/lessons/{lesson_id}/answers",
    response_model=MathematicsAnswerFeedback,
)
def check_mathematics_guest_answer(
    lesson_id: str,
    payload: MathematicsAnswerRequest,
):
    result = check_mathematics_answer(lesson_id, payload.question_id, payload.answer)
    if result is None:
        raise HTTPException(status_code=404, detail="Question not found for this lesson")
    return result
