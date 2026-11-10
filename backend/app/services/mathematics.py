import json
import re
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any


def _validate_question_structure(question: dict[str, Any]) -> None:
    required = ("id", "type", "prompt", "correct_answer", "explanation")
    if any(not question.get(field) for field in required):
        raise ValueError(
            "A Mathematics question needs an ID, type, prompt, answer and explanation."
        )

    question_type = question["type"]
    if question_type not in {"multiple_choice", "numerical", "short_answer"}:
        raise ValueError(f"Mathematics question {question['id']} has an unsupported type.")
    if question_type == "multiple_choice":
        options = question.get("options")
        if (
            not isinstance(options, list)
            or len(options) < 2
            or any(not isinstance(option, str) or not option.strip() for option in options)
            or len(options) != len(set(options))
            or question["correct_answer"] not in options
        ):
            raise ValueError(f"Mathematics question {question['id']} has invalid options.")
    accepted_answers = question.get("accepted_answers", [])
    if not isinstance(accepted_answers, list) or any(
        not isinstance(answer, str) or not answer.strip()
        for answer in accepted_answers
    ):
        raise ValueError(
            f"Mathematics question {question['id']} has invalid accepted answers."
        )
    tolerance = question.get("tolerance")
    if tolerance is not None and (
        isinstance(tolerance, bool)
        or not isinstance(tolerance, (int, float))
        or tolerance < 0
    ):
        raise ValueError(f"Mathematics question {question['id']} has invalid tolerance.")


@lru_cache(maxsize=1)
def _curriculum() -> dict[str, Any]:
    content_dir = (
        Path(__file__).resolve().parents[2]
        / "content-packages"
    )
    with (content_dir / "mathematics-learning-pack.json").open(
        encoding="utf-8"
    ) as content_file:
        curriculum = json.load(content_file)
    with (content_dir / "mathematics-learning-sequences.json").open(
        encoding="utf-8"
    ) as expansion_file:
        expansion = json.load(expansion_file)
    with (content_dir / "mathematics-number-systems-phase-b.json").open(
        encoding="utf-8"
    ) as phase_b_file:
        phase_b = json.load(phase_b_file)
    with (content_dir / "mathematics-number-systems-assessment-phase-b.json").open(
        encoding="utf-8"
    ) as question_file:
        question_pack = json.load(question_file)

    units = {
        unit["id"]: unit
        for level in curriculum["levels"]
        for unit in level["units"]
    }
    if len(units) != 8:
        raise ValueError("The Mathematics learning pack must define eight unique units.")
    for level in curriculum["levels"]:
        for unit in level["units"]:
            for lesson in unit["lessons"]:
                lesson.update(expansion["lesson_metadata"].get(lesson["id"], {}))
                for question in lesson["questions"]:
                    question.update(
                        expansion.get("question_metadata", {}).get(question["id"], {})
                    )
                    question.setdefault(
                        "mathematical_validation_status", "unverified"
                    )
                    question.setdefault("answer_verified", False)
                    question.setdefault("explanation_reviewed", False)
                    question.setdefault("educator_review_status", "not_submitted")
    for unit_expansion in expansion["units"]:
        unit = units.get(unit_expansion["unit_id"])
        if unit is None:
            raise ValueError(
                f"Mathematics expansion references unknown unit {unit_expansion['unit_id']}."
            )
        unit["lessons"].extend(unit_expansion["lessons"])
    for level in curriculum["levels"]:
        for unit in level["units"]:
            for lesson in unit["lessons"]:
                for question in lesson["questions"]:
                    question.update(
                        expansion.get("question_metadata", {}).get(question["id"], {})
                    )
    for lesson in phase_b["lessons"]:
        lesson["coverage_subtopic_ids"] = sorted(
            set(lesson.get("coverage_subtopic_ids", []))
            | {question["topic_id"] for question in lesson["questions"]}
        )
        lesson["coverage_alignment_status"] = "candidate_tag"
        lesson["coverage_alignment_note"] = (
            "Explicit stable topic IDs are candidate evidence only; instructional "
            "alignment and lesson quality have not been independently reviewed."
        )
        lesson["source_references"] = phase_b["source_references"]
        for question in lesson["questions"]:
            objective_ids = question.pop("learning_objective_ids", None)
            if not objective_ids:
                objective_ids = [question.pop("learning_objective_id")]
            question["learning_objective_ids"] = objective_ids
            question["mathematical_validation_status"] = "author_checked"
            question["answer_verified"] = True
            question["explanation_reviewed"] = False
            question["educator_review_status"] = "not_submitted"
            question.setdefault("validation_working", question["explanation"])
        if lesson.get("visual", {}).get("type") == "power_model":
            visual = lesson["visual"]
            if (
                not isinstance(visual.get("base"), int)
                or visual["base"] < 1
                or visual.get("exponent") not in {2, 3}
            ):
                raise ValueError(
                    f"Mathematics lesson {lesson['id']} has an unsupported power visual."
                )
    phase_b_unit = next(
        unit
        for unit in units.values()
        if unit["id"] == "number-systems"
    )
    phase_b_unit["lessons"].extend(phase_b["lessons"])
    lessons_by_id = {
        lesson["id"]: lesson
        for level in curriculum["levels"]
        for unit in level["units"]
        for lesson in unit["lessons"]
    }
    for question_set in question_pack["lesson_question_sets"]:
        lesson = lessons_by_id.get(question_set["lesson_id"])
        if lesson is None:
            raise ValueError(
                f"Assessment package references unknown lesson {question_set['lesson_id']}."
            )
        for question in question_set["questions"]:
            question["topic_id"] = question.get("topic_id", question_set["topic_id"])
            question["review_topic"] = question["topic_id"].rsplit("/", 1)[-1].replace("-", " ")
            objective_ids = question.pop("learning_objective_ids", None)
            if not objective_ids:
                objective_ids = [question.pop("learning_objective_id")]
            question["learning_objective_ids"] = objective_ids
            question["mathematical_validation_status"] = "author_checked"
            question["answer_verified"] = True
            question["explanation_reviewed"] = False
            question["educator_review_status"] = "not_submitted"
            question["alignment_status"] = "candidate_tag"
            question["purpose"] = question.get("purpose", "practice")
            lesson["questions"].append(question)

    lesson_ids: set[str] = set()
    question_ids: set[str] = set()
    required_lesson_fields = {
        "id",
        "title",
        "subtopics",
        "duration_minutes",
        "intro",
        "objectives",
        "prerequisites",
        "sections",
        "definitions",
        "worked_examples",
        "real_world_application",
        "common_mistakes",
        "summary",
        "questions",
    }
    for level in curriculum["levels"]:
        for unit in level["units"]:
            if not unit["lessons"]:
                raise ValueError(f"Mathematics unit {unit['id']} has no lessons.")
            for lesson in unit["lessons"]:
                lesson.setdefault("guided_practice", [])
                lesson.setdefault("revision_points", [])
                missing = required_lesson_fields - lesson.keys()
                if missing:
                    raise ValueError(
                        f"Mathematics lesson {lesson['id']} is missing: "
                        + ", ".join(sorted(missing))
                    )
                if lesson["id"] in lesson_ids:
                    raise ValueError(f"Duplicate Mathematics lesson ID: {lesson['id']}.")
                lesson_ids.add(lesson["id"])
                for question in lesson["questions"]:
                    question.setdefault(
                        "mathematical_validation_status", "unverified"
                    )
                    question.setdefault("answer_verified", False)
                    question.setdefault("explanation_reviewed", False)
                    question.setdefault("educator_review_status", "not_submitted")
                    _validate_question_structure(question)
                    if question["id"] in question_ids:
                        raise ValueError(
                            f"Duplicate Mathematics question ID: {question['id']}."
                        )
                    question_ids.add(question["id"])
                    if question.get("mathematical_validation_status") not in {
                        "unverified",
                        "author_checked",
                        "independently_verified",
                    }:
                        raise ValueError(
                            f"Mathematics question {question['id']} has an invalid "
                            "mathematical validation status."
                        )
                    if question.get("educator_review_status") not in {
                        "not_submitted",
                        "awaiting_review",
                        "reviewed",
                        "approved",
                    }:
                        raise ValueError(
                            f"Mathematics question {question['id']} has an invalid "
                            "educator review status."
                        )
                    if question["type"] == "short_answer" and not question.get(
                        "accepted_answers"
                    ):
                        raise ValueError(
                            f"Mathematics short-answer question {question['id']} "
                            "needs explicit accepted answers."
                        )
                    if question.get("mathematical_validation_status") == "author_checked" and (
                        question.get("answer_verified") is not True
                        or not question.get("validation_working")
                    ):
                        if question.get("phase_b_answer_check_id") is None:
                            raise ValueError(
                                f"Author-checked question {question['id']} needs "
                                "answer-validation evidence."
                            )
    curriculum["coverage_note"] = (
        "This introductory pathway has lessons across all eight units. Phase B adds "
        "unreviewed Number Systems drafts that remain candidate content. It is not a "
        "complete Mathematics curriculum: deeper practice and subject-expert "
        "review remain necessary, especially for simultaneous and quadratic equations, "
        "transformations, advanced trigonometry, statistical inference, conditional "
        "probability and calculus applications."
    )
    return curriculum


@lru_cache(maxsize=1)
def _topic_assessment_objectives() -> dict[str, list[str]]:
    register_path = (
        Path(__file__).resolve().parents[2]
        / "content-packages"
        / "mathematics-curriculum-register.json"
    )
    with register_path.open(encoding="utf-8") as register_file:
        register = json.load(register_file)
    return {
        topic_id: profile.get("assessment_objectives", [])
        for topic_id, profile in register.get("topic_profiles", {}).items()
        if topic_id.startswith("number-systems/")
    }


def mathematics_curriculum() -> dict[str, Any]:
    source = _curriculum()
    lessons = [
        lesson
        for level in source["levels"]
        for unit in level["units"]
        for lesson in unit["lessons"]
    ]
    return {
        "subject": source["subject"],
        "title": source["title"],
        "content_status": source["content_status"],
        "review_status": source["review_status"],
        "total_lessons": len(lessons),
        "total_questions": sum(len(lesson["questions"]) for lesson in lessons),
        "source": source["source"],
        "coverage_note": source["coverage_note"],
        "topic_assessment_objectives": _topic_assessment_objectives(),
        "levels": [
            {
                **{key: value for key, value in level.items() if key != "units"},
                "units": [
                    {
                        **{key: value for key, value in unit.items() if key != "lessons"},
                        "lessons": [
                            {
                                key: lesson[key]
                                for key in (
                                    "id",
                                    "title",
                                    "subtopics",
                                    "duration_minutes",
                                    "objectives",
                                    "phase_b_status",
                                )
                                if key in lesson
                            }
                            for lesson in unit["lessons"]
                        ],
                    }
                    for unit in level["units"]
                ],
            }
            for level in source["levels"]
        ],
    }


def mathematics_lesson(lesson_id: str) -> dict[str, Any] | None:
    for level in _curriculum()["levels"]:
        for unit in level["units"]:
            for lesson in unit["lessons"]:
                if lesson["id"] == lesson_id:
                    return {
                        **{
                            key: value
                            for key, value in lesson.items()
                            if key not in {"questions"}
                        },
                        "unit_id": unit["id"],
                        "unit_title": unit["title"],
                        "level_id": level["id"],
                        "level_title": level["title"],
                        "questions": [
                            {
                                **{
                                    key: value
                                    for key, value in question.items()
                                    if key not in {
                                        "correct_answer",
                                        "accepted_answers",
                                        "tolerance",
                                        "explanation",
                                        "answer_verified",
                                        "explanation_reviewed",
                                        "mathematical_validation_status",
                                    }
                                },
                                "review_topic": question.get(
                                    "review_topic",
                                    lesson["subtopics"][0],
                                ),
                                "purpose": question.get(
                                    "purpose",
                                    "practice" if index == 0 else "knowledge_check",
                                ),
                            }
                            for index, question in enumerate(lesson["questions"])
                        ],
                    }
    return None


def _normalise_answer(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold().replace("−", "-")


def _as_fraction(value: str) -> Fraction | None:
    try:
        return Fraction(value.strip())
    except (ValueError, ZeroDivisionError):
        return None


def check_mathematics_answer(
    lesson_id: str, question_id: str, answer: str
) -> dict[str, Any] | None:
    for level in _curriculum()["levels"]:
        for unit in level["units"]:
            for lesson in unit["lessons"]:
                if lesson["id"] != lesson_id:
                    continue
                question = next(
                    (item for item in lesson["questions"] if item["id"] == question_id),
                    None,
                )
                if question is None:
                    return None
                accepted = [
                    question["correct_answer"],
                    *question.get("accepted_answers", []),
                ]
                correct = _normalise_answer(answer) in {
                    _normalise_answer(value) for value in accepted
                }
                expected_numeric = _as_fraction(question["correct_answer"])
                submitted_numeric = _as_fraction(answer)
                tolerance = question.get("tolerance")
                if (
                    not correct
                    and expected_numeric is not None
                    and submitted_numeric is not None
                    and tolerance is not None
                ):
                    correct = abs(expected_numeric - submitted_numeric) <= Fraction(
                        str(tolerance)
                    )
                return {
                    "question_id": question_id,
                    "correct": correct,
                    "correct_answer": question["correct_answer"],
                    "explanation": question["explanation"],
                    "topic_id": question.get("topic_id"),
                    "review_topic": question.get(
                        "review_topic",
                        lesson["subtopics"][0],
                    ),
                    "purpose": question.get("purpose", "knowledge_check"),
                }
    return None
