import json
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.services.mathematics import _curriculum, _validate_question_structure

ALIGNMENT_STATUSES = {
    "candidate_tag",
    "manually_verified",
    "content_verified",
}
MATHEMATICAL_VALIDATION_STATUSES = {
    "not_assessed",
    "unverified",
    "author_checked",
    "independently_verified",
}
CONTENT_STATUSES = {
    "not_started",
    "draft",
    "content_incomplete",
    "content_complete",
    "awaiting_review",
    "reviewed",
    "approved_for_publication",
    "published",
}
ASSESSMENT_STATUSES = {
    "no_assessment",
    "insufficient_assessment",
    "assessment_drafted",
    "assessment_complete",
    "assessment_reviewed",
}
REVIEW_STATUSES = {
    "not_submitted",
    "awaiting_review",
    "changes_requested",
    "reviewed",
    "approved",
}
PUBLICATION_STATUSES = {
    "unpublished",
    "ready_for_publication",
    "published",
    "archived",
}

_REQUIRED_CONTENT_FIELDS = (
    "objectives",
    "prerequisites",
    "intro",
    "sections",
    "definitions",
    "worked_examples",
    "guided_practice",
    "real_world_application",
    "common_mistakes",
    "summary",
    "revision_points",
)


def _normalise(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.casefold()).split())

def _issue(
    rule: str,
    affected: list[str],
    severity: str,
    suggested_correction: str,
) -> dict[str, Any]:
    return {
        "rule": rule,
        "failures": len(affected),
        "affected_records": sorted(set(affected)),
        "severity": severity,
        "suggested_correction": suggested_correction,
    }


def _has_prerequisite_cycle(
    subtopic_ids: set[str], prerequisites: dict[str, list[str]]
) -> list[list[str]]:
    state: dict[str, int] = {}
    cycles: list[list[str]] = []
    stack: list[str] = []

    def visit(subtopic_id: str) -> None:
        state[subtopic_id] = 1
        stack.append(subtopic_id)
        for prerequisite in prerequisites.get(subtopic_id, []):
            if prerequisite not in subtopic_ids:
                continue
            if state.get(prerequisite) == 1:
                start = stack.index(prerequisite)
                cycles.append(stack[start:] + [prerequisite])
            elif state.get(prerequisite, 0) == 0:
                visit(prerequisite)
        stack.pop()
        state[subtopic_id] = 2

    for subtopic_id in sorted(subtopic_ids):
        if state.get(subtopic_id, 0) == 0:
            visit(subtopic_id)
    return cycles


@lru_cache(maxsize=1)
def _register() -> dict[str, Any]:
    path = (
        Path(__file__).resolve().parents[2]
        / "content-packages"
        / "mathematics-curriculum-register.json"
    )
    with path.open(encoding="utf-8") as register_file:
        register = json.load(register_file)
    return register


def validate_curriculum_register(
    register: dict[str, Any], curriculum: dict[str, Any]
) -> dict[str, Any]:
    units = register.get("units", [])
    subtopics: dict[str, dict[str, Any]] = {}
    duplicate_titles: dict[str, list[str]] = defaultdict(list)
    duplicate_ids: list[str] = []
    missing_scope: list[str] = []
    missing_profile_fields: list[str] = []
    profiles = register.get("topic_profiles", {})
    invalid_level_units: list[str] = []
    invalid_inventory_records: list[str] = []
    curriculum_unit_ids = {
        unit["id"]
        for level in curriculum.get("levels", [])
        for unit in level.get("units", [])
    }
    curriculum_levels = {level["id"] for level in curriculum.get("levels", [])}
    curriculum_units = {
        unit["id"]: level["id"]
        for level in curriculum.get("levels", [])
        for unit in level.get("units", [])
    }

    expected_subtopics = {
        (unit.get("id", ""), title): unit
        for unit in units
        for title in unit.get("subtopics", [])
    }
    inventory_records = register.get("subtopic_records", [])
    record_ids: set[str] = set()
    recorded_subtopics: set[tuple[str, str]] = set()
    for record in inventory_records:
        identifier = record.get("id", "")
        unit_id = record.get("unit_id", "")
        title = record.get("title", "")
        missing_fields = [
            field
            for field in ("id", "subject", "level_id", "unit_id", "title", "last_updated")
            if not record.get(field)
        ]
        key = (unit_id, title)
        if missing_fields:
            invalid_inventory_records.append(
                f"{identifier or '<missing-id>'}:missing:{','.join(missing_fields)}"
            )
        if record.get("subject") != register.get("subject"):
            invalid_inventory_records.append(identifier or f"{unit_id}/{title}")
        if not identifier or identifier in record_ids:
            duplicate_ids.append(identifier or "<missing-id>")
        record_ids.add(identifier)
        if key not in expected_subtopics:
            invalid_inventory_records.append(identifier or f"{unit_id}/{title}")
        elif record.get("level_id") != expected_subtopics[key].get("level_id"):
            invalid_inventory_records.append(identifier)
        if key in recorded_subtopics:
            invalid_inventory_records.append(identifier or f"{unit_id}/{title}")
        recorded_subtopics.add(key)
        profile = profiles.get(identifier, {})
        scope = profile.get("learning_scope") or record.get("learning_scope")
        outcomes = profile.get("expected_learning_outcomes") or record.get(
            "expected_learning_outcomes", []
        )
        if not scope or not outcomes:
            missing_scope.append(identifier or f"{unit_id}/{title}")
        if identifier.startswith("number-systems/"):
            for field in (
                "definition",
                "learning_scope",
                "expected_learning_outcomes",
                "prerequisite_knowledge",
                "concepts_to_teach",
                "skills",
                "misconceptions",
                "assessment_objectives",
                "blueprint",
            ):
                if not profile.get(field):
                    missing_profile_fields.append(f"{identifier}.{field}")
        duplicate_titles[title.casefold()].append(identifier)

    missing_inventory_records = sorted(
        f"{unit_id}/{title}" for unit_id, title in set(expected_subtopics) - recorded_subtopics
    )
    for unit in units:
        unit_id = unit.get("id", "")
        if (
            unit_id not in curriculum_units
            or unit.get("level_id") not in curriculum_levels
            or curriculum_units.get(unit_id) != unit.get("level_id")
        ):
            invalid_level_units.append(unit_id or "<missing-unit-id>")
    for record in inventory_records:
        identifier = record.get("id", "")
        if identifier in subtopics:
            duplicate_ids.append(identifier)
        subtopics[identifier] = record
    missing_register_units = sorted(
        curriculum_unit_ids - {unit.get("id") for unit in units}
    )

    subtopic_ids = set(subtopics)
    prerequisites = register.get("prerequisites", {})
    invalid_prerequisites = [
        f"{subtopic_id}->{prerequisite}"
        for subtopic_id, required in prerequisites.items()
        for prerequisite in required
        if subtopic_id not in subtopic_ids or prerequisite not in subtopic_ids
    ]
    cycles = _has_prerequisite_cycle(subtopic_ids, prerequisites)
    unspecified_prerequisites = sorted(subtopic_ids - set(prerequisites))

    lesson_by_id: dict[str, dict[str, Any]] = {}
    question_by_id: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {}
    duplicate_lesson_ids: list[str] = []
    duplicate_question_ids: list[str] = []
    for level in curriculum.get("levels", []):
        for unit in level.get("units", []):
            for lesson in unit.get("lessons", []):
                if lesson["id"] in lesson_by_id:
                    duplicate_lesson_ids.append(lesson["id"])
                lesson_by_id[lesson["id"]] = lesson
                for question in lesson.get("questions", []):
                    if question["id"] in question_by_id:
                        duplicate_question_ids.append(question["id"])
                    question_by_id[question["id"]] = (lesson, question)

    unverified_mathematics_questions = [
        question_id
        for question_id, (_, question) in question_by_id.items()
        if question.get("mathematical_validation_status")
        not in {"author_checked", "independently_verified"}
    ]
    actual_lesson_tags = {
        lesson_id: {_normalise(tag) for tag in lesson.get("subtopics", [])}
        for lesson_id, lesson in lesson_by_id.items()
    }
    actual_question_tags = {
        question_id: _normalise(question.get("review_topic", ""))
        for question_id, (_, question) in question_by_id.items()
    }
    invalid_explicit_content_topic_ids = [
        f"{lesson_id}->{subtopic_id}"
        for lesson_id, lesson in lesson_by_id.items()
        for subtopic_id in lesson.get("coverage_subtopic_ids", [])
        if subtopic_id not in subtopic_ids
    ] + [
        f"{question_id}->{question.get('topic_id')}"
        for question_id, (_, question) in question_by_id.items()
        if question.get("topic_id") and question["topic_id"] not in subtopic_ids
    ] + [
        f"{lesson_id}->visual:{subtopic_id}"
        for lesson_id, lesson in lesson_by_id.items()
        for subtopic_id in lesson.get("visual_topic_ids", [])
        if subtopic_id not in subtopic_ids
    ]
    known_lesson_tags = {
        tag for tags in actual_lesson_tags.values() for tag in tags
    }
    known_question_tags = {
        tag for tag in actual_question_tags.values() if tag
    }
    invalid_crosswalk_tags = [
        f"{relation_name}:{subtopic_id}:{tag}"
        for relation_name, available in (
            ("evidence_tags", known_lesson_tags),
            ("question_tags", known_question_tags),
        )
        for subtopic_id, tags in register.get(relation_name, {}).items()
        for tag in tags
        if _normalise(tag) not in available
    ]
    lesson_alignment_records = register.get("lesson_alignments", [])
    question_alignment_records = register.get("question_alignments", [])
    invalid_lesson_references = []
    invalid_question_references = []
    invalid_alignment_statuses = []
    invalid_alignment_metadata = []
    invalid_alignment_source_tags = []
    duplicate_lesson_relations = []
    duplicate_question_relations = []
    lesson_pairs: set[tuple[str, str]] = set()
    question_pairs: set[tuple[str, str]] = set()

    for relation in lesson_alignment_records:
        lesson_id = relation.get("lesson_id", "")
        subtopic_id = relation.get("subtopic_id", "")
        pair = (lesson_id, subtopic_id)
        if lesson_id not in lesson_by_id or subtopic_id not in subtopic_ids:
            invalid_lesson_references.append(f"{lesson_id}->{subtopic_id}")
        if pair in lesson_pairs:
            duplicate_lesson_relations.append(f"{lesson_id}->{subtopic_id}")
        lesson_pairs.add(pair)
        if relation.get("alignment_status") not in ALIGNMENT_STATUSES:
            invalid_alignment_statuses.append(f"{lesson_id}->{subtopic_id}")
        if not all(
            relation.get(field)
            for field in (
                "evidence_type",
                "source_tags",
                "validation_notes",
                "last_validated",
            )
        ):
            invalid_alignment_metadata.append(f"{lesson_id}->{subtopic_id}")
        if lesson_id in actual_lesson_tags and any(
            _normalise(tag) not in actual_lesson_tags[lesson_id]
            for tag in relation.get("source_tags", [])
        ):
            invalid_alignment_source_tags.append(f"{lesson_id}->{subtopic_id}")

    for relation in question_alignment_records:
        question_id = relation.get("question_id", "")
        lesson_id = relation.get("lesson_id", "")
        subtopic_id = relation.get("subtopic_id", "")
        pair = (question_id, subtopic_id)
        question_owner = question_by_id.get(question_id)
        if (
            question_owner is None
            or question_owner[0]["id"] != lesson_id
            or subtopic_id not in subtopic_ids
        ):
            invalid_question_references.append(
                f"{question_id}->{lesson_id}->{subtopic_id}"
            )
        if pair in question_pairs:
            duplicate_question_relations.append(f"{question_id}->{subtopic_id}")
        question_pairs.add(pair)
        if relation.get("alignment_status") not in ALIGNMENT_STATUSES:
            invalid_alignment_statuses.append(f"{question_id}->{subtopic_id}")
        if not all(
            relation.get(field)
            for field in (
                "evidence_type",
                "source_tags",
                "validation_notes",
                "last_validated",
            )
        ):
            invalid_alignment_metadata.append(f"{question_id}->{subtopic_id}")
        if question_id in actual_question_tags and any(
            _normalise(tag) != actual_question_tags[question_id]
            for tag in relation.get("source_tags", [])
        ):
            invalid_alignment_source_tags.append(f"{question_id}->{subtopic_id}")

    invalid_crosswalk_topic_ids = [
        f"{relation_name}:{subtopic_id}"
        for relation_name in ("evidence_tags", "question_tags", "prerequisites")
        for subtopic_id in register.get(relation_name, {})
        if subtopic_id not in subtopic_ids
    ]

    missing_question_objectives = [
        question_id
        for question_id, (_, question) in question_by_id.items()
        if not question.get("learning_objective_ids")
    ]
    questions_with_unregistered_objectives = []
    topic_profiles = register.get("topic_profiles", {})
    for question_id, (_, question) in question_by_id.items():
        topic_id = question.get("topic_id")
        if topic_id not in topic_profiles:
            continue
        allowed_objectives = set(
            topic_profiles[topic_id].get("assessment_objectives", [])
        )
        unregistered_objectives = sorted(
            set(question.get("learning_objective_ids", [])) - allowed_objectives
        )
        if unregistered_objectives:
            questions_with_unregistered_objectives.append(
                f"{question_id}:{','.join(unregistered_objectives)}"
            )
    missing_question_explanations = [
        question_id
        for question_id, (_, question) in question_by_id.items()
        if not question.get("explanation")
    ]
    invalid_question_structures = []
    missing_accepted_answers = []
    invalid_validation_transitions = []
    for question_id, (_, question) in question_by_id.items():
        try:
            _validate_question_structure(question)
        except ValueError as error:
            invalid_question_structures.append(f"{question_id}:{error}")
        if question.get("type") == "short_answer" and not question.get(
            "accepted_answers"
        ):
            missing_accepted_answers.append(question_id)
        validation_status = question.get(
            "mathematical_validation_status", "unverified"
        )
        if validation_status == "author_checked" and (
            question.get("answer_verified") is not True
            or not question.get("validation_working")
        ):
            invalid_validation_transitions.append(question_id)
        if validation_status == "independently_verified" and not question.get(
            "independent_validation_evidence"
        ):
            invalid_validation_transitions.append(question_id)

    explicit_lesson_links = [
        {
            "lesson_id": lesson_id,
            "subtopic_id": subtopic_id,
            "alignment_status": lesson.get("coverage_alignment_status", "candidate_tag"),
        }
        for lesson_id, lesson in lesson_by_id.items()
        for subtopic_id in lesson.get("coverage_subtopic_ids", [])
        if subtopic_id in subtopic_ids
    ]
    explicit_question_links = [
        {
            "question_id": question_id,
            "subtopic_id": question["topic_id"],
        }
        for question_id, (_, question) in question_by_id.items()
        if question.get("topic_id") in subtopic_ids
    ]
    linked_lessons = {lesson_id for lesson_id, _ in lesson_pairs}
    linked_lessons.update(item["lesson_id"] for item in explicit_lesson_links)
    linked_questions = {question_id for question_id, _ in question_pairs}
    linked_questions.update(item["question_id"] for item in explicit_question_links)
    orphaned_lessons = sorted(set(lesson_by_id) - linked_lessons)
    orphaned_questions = sorted(set(question_by_id) - linked_questions)

    prompt_to_questions: dict[str, list[str]] = defaultdict(list)
    for question_id, (_, question) in question_by_id.items():
        prompt = _normalise(question.get("prompt", ""))
        if prompt:
            prompt_to_questions[prompt].append(question_id)
    duplicate_prompts = [
        f"{prompt}: {','.join(sorted(question_ids))}"
        for prompt, question_ids in prompt_to_questions.items()
        if len(question_ids) > 1
    ]

    missing_question_metadata = [
        f"{question_id}.{field}"
        for question_id, (_, question) in question_by_id.items()
        for field in (
            "review_topic",
            "purpose",
            "learning_objective_ids",
            "difficulty",
            "answer_verified",
            "explanation_reviewed",
        )
        if field not in question
        or (
            field not in {"answer_verified", "explanation_reviewed"}
            and not question.get(field)
        )
    ]
    missing_lesson_notation_status = [
        lesson_id
        for lesson_id, lesson in lesson_by_id.items()
        if lesson.get("notation_review_status") not in {"checked", "not_required"}
    ]
    review_statuses = register.get("educator_review_statuses", {})
    publication_statuses = register.get("publication_statuses", {})
    assessment_review_statuses = register.get("assessment_review_statuses", {})
    invalid_review_statuses = [
        f"{subtopic_id}:{value}"
        for subtopic_id, value in review_statuses.items()
        if subtopic_id not in subtopic_ids or value not in REVIEW_STATUSES
    ]
    invalid_publication_statuses = [
        f"{subtopic_id}:{value}"
        for subtopic_id, value in publication_statuses.items()
        if subtopic_id not in subtopic_ids or value not in PUBLICATION_STATUSES
    ]
    invalid_assessment_review_statuses = [
        f"{subtopic_id}:{value}"
        for subtopic_id, value in assessment_review_statuses.items()
        if subtopic_id not in subtopic_ids or value != "assessment_reviewed"
    ]
    invalid_status_combinations = []
    for subtopic_id in subtopic_ids:
        review_status = review_statuses.get(subtopic_id, "not_submitted")
        publication_status = publication_statuses.get(subtopic_id, "unpublished")
        if (
            publication_status in {"ready_for_publication", "published"}
            and review_status != "approved"
        ):
            invalid_status_combinations.append(subtopic_id)
    candidate_links = [
        relation
        for relation in lesson_alignment_records
        if relation.get("alignment_status") == "candidate_tag"
    ] + [
        relation
        for relation in explicit_lesson_links
        if relation["alignment_status"] == "candidate_tag"
    ]
    content_verified_links = [
        relation
        for relation in lesson_alignment_records
        if relation.get("alignment_status") == "content_verified"
    ]

    findings = [
        _issue(
            "duplicate_subtopic_ids",
            duplicate_ids,
            "high",
            "Assign each topic a unique stable ID; do not merge records without curriculum review.",
        ),
        _issue(
            "duplicate_display_names",
            [
                f"{title}:{','.join(sorted(identifiers))}"
                for title, identifiers in duplicate_titles.items()
                if len(identifiers) > 1
            ],
            "low",
            "Confirm that similarly named topics represent different learning objectives "
            "or document an approved merge.",
        ),
        _issue(
            "inventory_record_mismatch",
            invalid_inventory_records + missing_inventory_records,
            "high",
            "Keep one stable-ID record for each unit/topic pair and match its "
            "registered level and unit.",
        ),
        _issue(
            "missing_learning_scope_or_outcomes",
            missing_scope,
            "medium",
            "Add a provisional learning scope and observable outcomes for each topic, "
            "then review them.",
        ),
        _issue(
            "incomplete_number_systems_topic_profiles",
            missing_profile_fields,
            "medium",
            "Complete each Number Systems profile's scope, outcomes, prerequisites, "
            "concepts, skills, misconceptions, assessment objectives and blueprint.",
        ),
        _issue(
            "invalid_level_or_unit_reference",
            invalid_level_units + [f"missing:{item}" for item in missing_register_units],
            "high",
            "Use a level ID and unit ID that exist in the Mathematics learning path.",
        ),
        _issue(
            "unspecified_prerequisite_relationships",
            unspecified_prerequisites,
            "medium",
            "Assess prerequisites explicitly; an absent record must not be interpreted "
            "as no prerequisite.",
        ),
        _issue(
            "invalid_prerequisite_references",
            invalid_prerequisites,
            "high",
            "Correct or remove the broken prerequisite edge after curriculum review.",
        ),
        _issue(
            "invalid_register_crosswalk_topic_ids",
            invalid_crosswalk_topic_ids,
            "high",
            "Use stable subtopic IDs that exist in the registered inventory.",
        ),
        _issue(
            "invalid_explicit_content_topic_ids",
            invalid_explicit_content_topic_ids,
            "high",
            "Correct explicit lesson/question topic IDs to match the stable inventory.",
        ),
        _issue(
            "unmatched_crosswalk_source_tags",
            invalid_crosswalk_tags,
            "high",
            "Correct the crosswalk to use an actual package tag or remove the "
            "unsupported candidate mapping.",
        ),
        _issue(
            "circular_prerequisite_relationships",
            [" -> ".join(cycle) for cycle in cycles],
            "high",
            "Break the prerequisite cycle while preserving pedagogically necessary dependencies.",
        ),
        _issue(
            "invalid_lesson_alignment_references",
            invalid_lesson_references,
            "high",
            "Reference an existing lesson ID and subtopic ID.",
        ),
        _issue(
            "invalid_question_alignment_references",
            invalid_question_references,
            "high",
            "Reference an existing question ID, its owning lesson ID, and an existing subtopic ID.",
        ),
        _issue(
            "duplicate_lesson_or_question_ids",
            duplicate_lesson_ids + duplicate_question_ids,
            "high",
            "Assign unique lesson and question IDs before constructing crosswalk records.",
        ),
        _issue(
            "duplicate_alignment_relationships",
            duplicate_lesson_relations + duplicate_question_relations,
            "medium",
            "Keep one relationship per lesson/question and subtopic pair, retaining "
            "all evidence sources.",
        ),
        _issue(
            "incomplete_alignment_evidence_metadata",
            invalid_alignment_metadata,
            "medium",
            "Record evidence type, validation note, and date for every relationship.",
        ),
        _issue(
            "alignment_source_tag_mismatch",
            invalid_alignment_source_tags,
            "high",
            "Correct the source tag or remove the unsupported relationship; do not "
            "mark it verified.",
        ),
        _issue(
            "invalid_alignment_status",
            invalid_alignment_statuses,
            "high",
            "Use a declared alignment status and keep candidate evidence distinct "
            "from verification.",
        ),
        _issue(
            "unlinked_lessons",
            orphaned_lessons,
            "medium",
            "Review whether each lesson belongs in this subtopic register; do not invent "
            "a link to clear the finding.",
        ),
        _issue(
            "unlinked_questions",
            orphaned_questions,
            "medium",
            "Assign an explicit question alignment only after confirming the item "
            "assesses that subtopic.",
        ),
        _issue(
            "duplicate_question_prompts",
            duplicate_prompts,
            "medium",
            "Review repeated prompts for intentional reuse or replace with distinct "
            "assessment items.",
        ),
        _issue(
            "missing_question_review_metadata",
            missing_question_metadata,
            "medium",
            "Add explicit topic, learning-objective and difficulty metadata before "
            "counting the question as quality-verified.",
        ),
        _issue(
            "questions_without_objectives",
            missing_question_objectives,
            "medium",
            "Associate each question with one or more observable learning objectives.",
        ),
        _issue(
            "questions_with_unregistered_objectives",
            questions_with_unregistered_objectives,
            "medium",
            "Use learning objectives registered for the question's explicitly linked topic.",
        ),
        _issue(
            "questions_without_explanations",
            missing_question_explanations,
            "medium",
            "Provide a correct answer explanation for every learner assessment item.",
        ),
        _issue(
            "invalid_question_answer_structures",
            invalid_question_structures,
            "high",
            "Correct unsupported types, malformed choices, missing answers or other "
            "question structure errors.",
        ),
        _issue(
            "short_answer_questions_without_accepted_answers",
            missing_accepted_answers,
            "medium",
            "List explicitly supported response forms for every short-answer question.",
        ),
        _issue(
            "invalid_validation_status_transitions",
            invalid_validation_transitions,
            "high",
            "Require answer evidence for author checks and independent evidence before "
            "assigning independently_verified.",
        ),
        _issue(
            "unverified_question_mathematics",
            unverified_mathematics_questions,
            "medium",
            "Check calculations and answer keys, record the validation method, and keep "
            "external review separate.",
        ),
        _issue(
            "missing_lesson_notation_review_status",
            missing_lesson_notation_status,
            "medium",
            "Record whether mathematical notation was checked or is not required for the lesson.",
        ),
        _issue(
            "invalid_review_or_publication_status",
            invalid_review_statuses
            + invalid_publication_statuses
            + invalid_assessment_review_statuses,
            "high",
            "Use a declared status and reference an existing subtopic.",
        ),
        _issue(
            "invalid_review_publication_combination",
            invalid_status_combinations,
            "high",
            "Only approved content may be ready for publication or published.",
        ),
        _issue(
            "candidate_alignments_not_manually_verified",
            [f"{item['lesson_id']}->{item['subtopic_id']}" for item in candidate_links],
            "info",
            "Have a qualified reviewer inspect the instructional content and record "
            "a justified alignment decision.",
        ),
    ]
    counts = {
        "total_lessons": len(lesson_by_id),
        "total_questions": len(question_by_id),
        "candidate_lesson_alignments": len(candidate_links),
        "manually_verified_lesson_alignments": sum(
            item.get("alignment_status") == "manually_verified"
            for item in lesson_alignment_records
        ),
        "content_verified_lesson_alignments": len(content_verified_links),
        "subtopics_with_candidate_evidence": len(
            {
                item["subtopic_id"]
                for item in candidate_links
                if item["lesson_id"] in lesson_by_id
                and item["subtopic_id"] in subtopic_ids
            }
        ),
        "subtopics_without_lesson_evidence": len(
            subtopic_ids
            - {
                item["subtopic_id"]
                for item in candidate_links + [
                    relation
                    for relation in lesson_alignment_records
                    if relation.get("alignment_status")
                    in {"manually_verified", "content_verified"}
                ]
                if item.get("lesson_id") in lesson_by_id
                and item.get("subtopic_id") in subtopic_ids
            }
        ),
        "unlinked_lessons": len(orphaned_lessons),
        "unlinked_questions": len(orphaned_questions),
        "duplicate_display_titles": sum(
            len(identifiers) > 1 for identifiers in duplicate_titles.values()
        ),
        "registered_topics_missing_scope_or_outcomes": len(missing_scope),
        "number_systems_topics_missing_profile_fields": len(missing_profile_fields),
        "questions_without_objectives": len(missing_question_objectives),
        "questions_with_unregistered_objectives": len(
            questions_with_unregistered_objectives
        ),
        "questions_without_explanations": len(missing_question_explanations),
        "invalid_question_answer_structures": len(invalid_question_structures),
        "short_answer_questions_without_accepted_answers": len(missing_accepted_answers),
        "invalid_validation_status_transitions": len(invalid_validation_transitions),
        "topics_without_assessed_prerequisite_status": len(unspecified_prerequisites),
        "invalid_lesson_alignments": len(invalid_lesson_references),
        "invalid_question_alignments": len(invalid_question_references),
        "duplicate_question_prompts": len(duplicate_prompts),
        "question_mathematics_validation_counts": dict(
            Counter(
                question.get("mathematical_validation_status", "unverified")
                for _, question in question_by_id.values()
            )
        ),
    }
    return {
        "subject": register.get("subject", "Unknown"),
        "register_version": register.get("register_version", "unknown"),
        "last_updated": register.get("last_updated", "unknown"),
        "status": (
            "issues_found"
            if any(
                item["failures"] and item["severity"] != "info"
                for item in findings
            )
            else "passed_with_notes"
            if any(item["failures"] for item in findings)
            else "passed"
        ),
        "counts": counts,
        "rules": findings,
        "overlap_notes": register.get("inventory_notes", []),
    }


def _percentage(numerator: int, denominator: int) -> int:
    return round(numerator * 100 / denominator) if denominator else 0


def _distribution(
    records: list[dict[str, Any]], field: str, statuses: set[str]
) -> dict[str, dict[str, int]]:
    counts = Counter(item[field] for item in records)
    total = len(records)
    return {
        status: {
            "count": counts.get(status, 0),
            "percent": _percentage(counts.get(status, 0), total),
        }
        for status in sorted(statuses)
    }


def _metrics(records: list[dict[str, Any]], question_target: int) -> dict[str, Any]:
    total = len(records)
    alignment = _distribution(records, "alignment_status", {
        "no_lesson_evidence",
        "candidate_tag",
        "manually_verified",
        "content_verified",
    })
    content = _distribution(records, "content_status", CONTENT_STATUSES)
    assessment = _distribution(records, "assessment_status", ASSESSMENT_STATUSES)
    review = _distribution(records, "educator_review_status", REVIEW_STATUSES)
    publication = _distribution(records, "publication_status", PUBLICATION_STATUSES)
    mathematical_validation = _distribution(
        records, "mathematical_validation_status", MATHEMATICAL_VALIDATION_STATUSES
    )
    instructional_evidence = Counter(
        item.get("instructional_evidence_status", "not_supported")
        for item in records
    )
    content_complete = content["content_complete"]["count"]
    assessment_complete = assessment["assessment_complete"]["count"]
    reviewed = review["reviewed"]["count"] + review["approved"]["count"]
    published = publication["published"]["count"]
    return {
        "total_subtopics": total,
        "alignment_status_counts": alignment,
        "content_status_counts": content,
        "assessment_status_counts": assessment,
        "educator_review_status_counts": review,
        "publication_status_counts": publication,
        "mathematical_validation_status_counts": mathematical_validation,
        "instructional_evidence_status_counts": dict(instructional_evidence),
        "content_complete": content_complete,
        "partial": content["draft"]["count"],
        "not_started": content["not_started"]["count"],
        "assessment_complete": assessment_complete,
        "assessment_incomplete": total - assessment_complete,
        "reviewed": reviewed,
        "awaiting_review": review["awaiting_review"]["count"],
        "published": published,
        "content_completion_percent": _percentage(content_complete, total),
        "assessment_completion_percent": _percentage(assessment_complete, total),
        "expert_review_percent": _percentage(reviewed, total),
        "question_target_per_subtopic": question_target,
    }


def build_curriculum_coverage_report(
    register: dict[str, Any],
    curriculum: dict[str, Any],
    review_decisions: dict[tuple[str, str], str] | None = None,
) -> dict[str, Any]:
    review_decisions = review_decisions or {}
    validation = validate_curriculum_register(register, curriculum)
    subtopic_records: dict[str, dict[str, Any]] = {}
    topic_profiles = register.get("topic_profiles", {})

    for record in register.get("subtopic_records", []):
        identifier = record["id"]
        profile = topic_profiles.get(identifier, {})
        subtopic_records[identifier] = {
            "id": identifier,
            "subject": record.get("subject", register.get("subject", "Unknown")),
            "level_id": record.get("level_id", ""),
            "unit_id": record.get("unit_id", ""),
            "name": record.get("title", ""),
            "description": profile.get("definition") or record.get("description"),
            "definition": profile.get("definition"),
            "prerequisite_ids": register.get("prerequisites", {}).get(identifier, []),
            "prerequisite_status": (
                "specified"
                if identifier in register.get("prerequisites", {})
                else "not_assessed"
            ),
            "required_prior_knowledge": profile.get("prerequisite_knowledge", []),
            "concepts_to_teach": profile.get("concepts_to_teach", []),
            "skills": profile.get("skills", []),
            "common_misconceptions": profile.get("misconceptions", []),
            "learning_scope": profile.get("learning_scope")
            or record.get("learning_scope"),
            "learning_outcomes": profile.get("expected_learning_outcomes")
            or record.get("expected_learning_outcomes", []),
            "assessment_objectives": profile.get("assessment_objectives", []),
            "assessment_blueprint": profile.get("blueprint", {}),
            "topic_scope_status": (
                "complete"
                if all(
                    profile.get(field)
                    for field in (
                        "definition",
                        "learning_scope",
                        "expected_learning_outcomes",
                        "prerequisite_knowledge",
                        "concepts_to_teach",
                        "skills",
                        "misconceptions",
                        "assessment_objectives",
                        "blueprint",
                    )
                )
                else "incomplete"
            ),
            "topic_profile_status": (
                "complete"
                if all(
                    profile.get(field)
                    for field in (
                        "definition",
                        "learning_scope",
                        "expected_learning_outcomes",
                        "prerequisite_knowledge",
                        "concepts_to_teach",
                        "skills",
                        "misconceptions",
                        "assessment_objectives",
                        "blueprint",
                    )
                )
                else "incomplete"
            ),
            "lesson_alignments": [],
            "question_alignments": [],
        }

    lessons = {
        lesson["id"]: lesson
        for level in curriculum.get("levels", [])
        for unit in level.get("units", [])
        for lesson in unit.get("lessons", [])
    }
    questions: dict[str, tuple[str, dict[str, Any]]] = {}
    for lesson_id, lesson in lessons.items():
        for question in lesson.get("questions", []):
            questions[question["id"]] = (lesson_id, question)

    valid_lesson_alignments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    valid_question_alignments: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for relation in register.get("lesson_alignments", []):
        if (
            relation.get("lesson_id") in lessons
            and relation.get("subtopic_id") in subtopic_records
            and relation.get("alignment_status") in ALIGNMENT_STATUSES
        ):
            valid_lesson_alignments[relation["subtopic_id"]].append(relation)
    for relation in register.get("question_alignments", []):
        owner = questions.get(relation.get("question_id"))
        if (
            owner is not None
            and owner[0] == relation.get("lesson_id")
            and relation.get("subtopic_id") in subtopic_records
            and relation.get("alignment_status") in ALIGNMENT_STATUSES
        ):
            valid_question_alignments[relation["subtopic_id"]].append(relation)
    for lesson_id, lesson in lessons.items():
        for subtopic_id in lesson.get("coverage_subtopic_ids", []):
            if subtopic_id in subtopic_records:
                valid_lesson_alignments[subtopic_id].append(
                    {
                        "lesson_id": lesson_id,
                        "subtopic_id": subtopic_id,
                        "evidence_type": "explicit_stable_topic_id",
                        "alignment_status": lesson.get(
                            "coverage_alignment_status", "candidate_tag"
                        ),
                        "source_tags": [],
                        "validation_notes": lesson.get(
                            "coverage_alignment_note",
                            "Explicit stable topic ID; alignment requires review.",
                        ),
                        "last_validated": lesson.get(
                            "last_validated", register.get("last_updated", "")
                        ),
                    }
                )
    alignment_audits = {
        (review["lesson_id"], topic_id): review
        for review in register.get("lesson_alignment_audit", [])
        for topic_id in review.get("candidate_topic_ids", [])
    }
    for (lesson_id, subtopic_id), review in alignment_audits.items():
        if lesson_id not in lessons or subtopic_id not in subtopic_records:
            continue
        if not any(
            relation["lesson_id"] == lesson_id
            for relation in valid_lesson_alignments[subtopic_id]
        ):
            valid_lesson_alignments[subtopic_id].append(
                {
                    "lesson_id": lesson_id,
                    "subtopic_id": subtopic_id,
                    "evidence_type": "lesson_content_audit",
                    "alignment_status": review.get("alignment_status", "candidate_tag"),
                    "source_tags": review.get("section_titles", []),
                    "validation_notes": review.get("validation_notes", ""),
                    "last_validated": register.get("last_updated", ""),
                }
            )
    for subtopic_id, relations in valid_lesson_alignments.items():
        enriched_relations = []
        for relation in relations:
            audit = alignment_audits.get((relation["lesson_id"], subtopic_id), {})
            lesson = lessons[relation["lesson_id"]]
            alignment_id = f"{relation['lesson_id']}::{subtopic_id}"
            alignment_decision = review_decisions.get(
                ("alignment", alignment_id), "pending_review"
            )
            lesson_decision = review_decisions.get(
                ("lesson", relation["lesson_id"]), "pending_review"
            )
            alignment_status = (
                "content_verified"
                if alignment_decision == "approved"
                and relation["alignment_status"] == "content_verified"
                else "manually_verified"
                if alignment_decision == "approved"
                else relation["alignment_status"]
            )
            section_title_set = set(audit.get("section_titles", []))
            evidence_quotes = [
                {"section_title": section["title"], "text": section["body"]}
                for section in lesson.get("sections", [])
                if section.get("title") in section_title_set
            ]
            outcome_review = [
                {
                    "outcome_id": (
                        f"{subtopic_id}::{relation['lesson_id']}::outcome::{index}"
                    ),
                    "outcome": outcome,
                    "status": review_decisions.get(
                        (
                            "outcome",
                            f"{subtopic_id}::{relation['lesson_id']}::outcome::{index}",
                        ),
                        "pending_review",
                    ),
                    "reviewer_decision": review_decisions.get(
                        (
                            "outcome",
                            f"{subtopic_id}::{relation['lesson_id']}::outcome::{index}",
                        ),
                        "pending_review",
                    ),
                    "reviewer_comments": "",
                }
                for index, outcome in enumerate(
                    subtopic_records[subtopic_id]["learning_outcomes"]
                )
            ]
            enriched_relations.append({
                **relation,
                "alignment_status": alignment_status,
                "alignment_review_decision": alignment_decision,
                "lesson_review_decision": lesson_decision,
                "audit_status": (
                    "instructionally_supported"
                    if alignment_decision == "approved"
                    else "requires_revision"
                    if alignment_decision == "revision_requested"
                    else "not_supported"
                    if alignment_decision == "rejected"
                    else "partially_supported"
                    if evidence_quotes and audit.get("instructional_evidence")
                    else "candidate_tag"
                ),
                "outcome_coverage_status": (
                    "reviewed"
                    if outcome_review
                    and all(
                        item["reviewer_decision"] in {"approved", "rejected"}
                        for item in outcome_review
                    )
                    else "requires_educator_review"
                ),
                "outcomes_addressed": audit.get("outcomes_addressed", []),
                "outcomes_partially_addressed": audit.get(
                    "outcomes_partially_addressed", []
                ),
                "outcomes_missing": audit.get("outcomes_missing", []),
                "outcomes_pending_review": [
                    outcome
                    for outcome in subtopic_records[subtopic_id][
                        "learning_outcomes"
                    ]
                    if outcome
                    not in {
                        *audit.get("outcomes_addressed", []),
                        *audit.get("outcomes_partially_addressed", []),
                        *audit.get("outcomes_missing", []),
                    }
                ],
                "outcome_review": outcome_review,
                "evidence_quotes": evidence_quotes,
                "instructional_evidence": audit.get("instructional_evidence", []),
                "section_titles": audit.get("section_titles", []),
                "missing_instructional_content": audit.get(
                    "missing_instructional_content", []
                ),
                "requires_educator_review": True,
            })
        valid_lesson_alignments[subtopic_id] = enriched_relations
    for question_id, (lesson_id, question) in questions.items():
        subtopic_id = question.get("topic_id")
        if subtopic_id in subtopic_records:
            question_decision = review_decisions.get(
                ("question", question_id), "pending_review"
            )
            valid_question_alignments[subtopic_id].append(
                {
                    "question_id": question_id,
                    "lesson_id": lesson_id,
                    "subtopic_id": subtopic_id,
                    "evidence_type": "explicit_stable_topic_id",
                    "alignment_status": (
                        "manually_verified"
                        if question_decision == "approved"
                        else question.get("alignment_status", "candidate_tag")
                    ),
                    "educator_review_decision": question_decision,
                    "source_tags": [question.get("review_topic", "")],
                    "validation_notes": (
                        "Explicit stable topic ID is candidate evidence only; "
                        "question relevance and correctness need review."
                    ),
                    "last_validated": register.get("last_updated", ""),
                }
            )

    question_target = register.get("assessment_question_target", 8)
    review_statuses = register.get("educator_review_statuses", {})
    publication_statuses = register.get("publication_statuses", {})
    for subtopic_id, item in subtopic_records.items():
        lesson_relations = valid_lesson_alignments.get(subtopic_id, [])
        question_relations = valid_question_alignments.get(subtopic_id, [])
        item["lesson_alignments"] = lesson_relations
        item["instructional_evidence_status"] = (
            "partially_supported"
            if any(relation.get("audit_status") == "partially_supported"
                   for relation in lesson_relations)
            else "candidate" if lesson_relations else "not_supported"
        )
        item["instructional_outcome_coverage_status"] = (
            "requires_educator_review"
            if lesson_relations
            else "not_assessed"
        )
        item["candidate_lesson_ids"] = sorted(
            {relation["lesson_id"] for relation in lesson_relations}
        )
        item["question_alignments"] = question_relations
        item["question_ids"] = sorted(
            {relation["question_id"] for relation in question_relations}
        )
        item["question_count"] = len(item["question_ids"])

        relation_statuses = {relation["alignment_status"] for relation in lesson_relations}
        if "content_verified" in relation_statuses:
            alignment_status = "content_verified"
        elif "manually_verified" in relation_statuses:
            alignment_status = "manually_verified"
        elif lesson_relations:
            alignment_status = "candidate_tag"
        else:
            alignment_status = "no_lesson_evidence"
        item["alignment_status"] = alignment_status

        quality_questions = [
            questions[question_id][1]
            for question_id in item["question_ids"]
            if question_id in questions
        ]
        question_validation_statuses = {
            question.get("mathematical_validation_status", "unverified")
            for question in quality_questions
        }
        if not quality_questions:
            item["mathematical_validation_status"] = "not_assessed"
        elif "unverified" in question_validation_statuses:
            item["mathematical_validation_status"] = "unverified"
        elif question_validation_statuses == {"independently_verified"}:
            item["mathematical_validation_status"] = "independently_verified"
        else:
            item["mathematical_validation_status"] = "author_checked"
        verified_question_ids = {
            relation["question_id"]
            for relation in question_relations
            if relation["alignment_status"] in {"manually_verified", "content_verified"}
        }
        all_prompts = [
            _normalise(question.get("prompt", "")) for question in quality_questions
        ]
        prompts_are_distinct = len(all_prompts) == len(set(all_prompts))
        question_objective_ids = {
            objective_id
            for question in quality_questions
            for objective_id in question.get("learning_objective_ids", [])
        }
        expected_objective_ids = set(item["assessment_objectives"])
        uncovered_objective_ids = sorted(expected_objective_ids - question_objective_ids)
        unregistered_objective_ids = sorted(question_objective_ids - expected_objective_ids)
        purpose_counts = Counter(
            question.get("purpose", "missing") for question in quality_questions
        )
        blueprint = item["assessment_blueprint"]
        blueprint_coverage = {
            purpose: {
                "required": required_count,
                "actual": purpose_counts.get(purpose, 0),
                "covered": purpose_counts.get(purpose, 0) >= required_count,
            }
            for purpose, required_count in blueprint.items()
        }
        accepted_answers_complete = all(
            question.get("type") != "short_answer"
            or bool(question.get("accepted_answers"))
            for question in quality_questions
        )
        question_structures_valid = True
        for question in quality_questions:
            try:
                _validate_question_structure(question)
            except ValueError:
                question_structures_valid = False
                break
        supported_types_only = all(
            question.get("type") in {"multiple_choice", "numerical", "short_answer"}
            for question in quality_questions
        )
        validation_metadata_complete = all(
            question.get("mathematical_validation_status")
            in {"author_checked", "independently_verified"}
            and question.get("answer_verified") is True
            and question.get("validation_working")
            for question in quality_questions
        )
        all_questions_independently_verified = all(
            question.get("mathematical_validation_status")
            == "independently_verified"
            and bool(question.get("independent_validation_evidence"))
            for question in quality_questions
        )
        all_questions_educator_approved = bool(quality_questions) and all(
            review_decisions.get(("question", question["id"])) == "approved"
            for question in quality_questions
        )
        question_quality_ready = (
            bool(quality_questions)
            and len(verified_question_ids) == len(item["question_ids"])
            and all(
                question.get("prompt")
                and question.get("correct_answer")
                and question.get("explanation")
                and question.get("review_topic")
                and question.get("learning_objective_ids")
                and question.get("difficulty")
                and question.get("answer_verified") is True
                and question.get("mathematical_validation_status")
                in {"author_checked", "independently_verified"}
                and question.get("explanation_reviewed") is True
                for question in quality_questions
            )
            and len({question.get("difficulty") for question in quality_questions}) >= 2
            and question_structures_valid
            and supported_types_only
            and accepted_answers_complete
            and validation_metadata_complete
            and not uncovered_objective_ids
            and not unregistered_objective_ids
            and all_questions_independently_verified
            and all_questions_educator_approved
            and all(value["covered"] for value in blueprint_coverage.values())
        )
        if not item["question_ids"]:
            assessment_status = "no_assessment"
        elif item["question_count"] < question_target:
            assessment_status = "insufficient_assessment"
        elif not question_quality_ready or not prompts_are_distinct:
            assessment_status = "assessment_drafted"
        else:
            assessment_status = "assessment_complete"
        if (
            assessment_status == "assessment_complete"
            and register.get("assessment_review_statuses", {}).get(subtopic_id)
            == "assessment_reviewed"
        ):
            assessment_status = "assessment_reviewed"
        item["assessment_status"] = assessment_status
        item["assessment_quality_issues"] = []
        if item["question_count"] < question_target:
            item["assessment_quality_issues"].append(
                f"Requires {question_target} distinct aligned questions; "
                f"{item['question_count']} are currently linked."
            )
        if quality_questions and not question_quality_ready:
            item["assessment_quality_issues"].append(
                "Assessment quality gates are incomplete: check objective coverage, "
                "answer metadata, reviewed explanations, difficulty variation, answer "
                "formats and the purpose blueprint."
            )
        if uncovered_objective_ids:
            item["assessment_quality_issues"].append(
                "Assessment objectives are not all covered by linked question objectives."
            )
        if unregistered_objective_ids:
            item["assessment_quality_issues"].append(
                "Some linked questions reference objectives not registered for this topic."
            )
        if not accepted_answers_complete:
            item["assessment_quality_issues"].append(
                "At least one short-answer question has no explicit accepted answers."
            )
        if not question_structures_valid or not supported_types_only:
            item["assessment_quality_issues"].append(
                "At least one linked question has an invalid or unsupported answer structure."
            )
        if not validation_metadata_complete:
            item["assessment_quality_issues"].append(
                "At least one linked question lacks an author/independent validation state "
                "or answer-check evidence."
            )
        if not all_questions_independently_verified:
            item["assessment_quality_issues"].append(
                "Independent mathematical verification evidence is incomplete."
            )
        if not all_questions_educator_approved:
            item["assessment_quality_issues"].append(
                "Each linked question requires its own approved educator review."
            )
        if any(not value["covered"] for value in blueprint_coverage.values()):
            item["assessment_quality_issues"].append(
                "The four-purpose assessment blueprint is not met."
            )
        if not prompts_are_distinct:
            item["assessment_quality_issues"].append(
                "Duplicate prompt text is present among linked questions."
            )
        if item["question_ids"] and len(verified_question_ids) < len(item["question_ids"]):
            item["assessment_quality_issues"].append(
                "Some question-to-topic links still require manual alignment verification."
            )
        purposes = {question.get("purpose") for question in quality_questions}
        item["question_purpose_counts"] = {
            purpose: purpose_counts.get(purpose, 0)
            for purpose in ("practice", "knowledge_check", "application", "higher_reasoning")
        }
        item["assessment_blueprint_coverage"] = blueprint_coverage
        item["learning_objective_ids_assessed"] = sorted(question_objective_ids)
        item["uncovered_assessment_objective_ids"] = uncovered_objective_ids
        item["unregistered_question_objective_ids"] = unregistered_objective_ids
        item["learning_outcome_coverage_status"] = (
            "complete"
            if not uncovered_objective_ids and not unregistered_objective_ids
            else "incomplete"
        )
        item["practice_question_coverage"] = purpose_counts.get("practice", 0)
        item["knowledge_check_coverage"] = purpose_counts.get("knowledge_check", 0)
        item["application_question_coverage"] = purpose_counts.get("application", 0)
        item["higher_reasoning_question_coverage"] = purpose_counts.get(
            "higher_reasoning", 0
        )
        item["question_quality_status"] = (
            "structurally_valid"
            if question_structures_valid
            and supported_types_only
            and accepted_answers_complete
            and not unregistered_objective_ids
            else "quality_issues_found"
        )
        item["practice_status"] = (
            "present" if "practice" in purposes else "not_assessed"
        )
        item["knowledge_check_status"] = (
            "present" if "knowledge_check" in purposes else "not_assessed"
        )

        if not lesson_relations:
            content_status = "not_started"
        else:
            verified_relations = [
                relation
                for relation in lesson_relations
                if relation.get("alignment_review_decision") == "approved"
                and relation.get("lesson_review_decision") == "approved"
            ]
            topic_review_approved = (
                review_decisions.get(("topic", subtopic_id)) == "approved"
            )
            relation_reviews_resolved = all(
                relation.get("alignment_review_decision")
                in {"approved", "rejected"}
                for relation in lesson_relations
            )
            every_outcome_approved = all(
                any(
                    relation.get("alignment_review_decision") == "approved"
                    and any(
                        outcome.get("outcome") == outcome_text
                        and outcome.get("reviewer_decision") == "approved"
                        for outcome in relation.get("outcome_review", [])
                    )
                    for relation in lesson_relations
                )
                for outcome_text in item["learning_outcomes"]
            )
            verified_lessons = [
                lessons[relation["lesson_id"]]
                for relation in verified_relations
                if relation["alignment_status"] in {"manually_verified", "content_verified"}
            ]
            explicitly_covered = [
                lesson
                for lesson in verified_lessons
                if subtopic_id in lesson.get("coverage_subtopic_ids", [])
            ]
            mandatory_fields_present = bool(explicitly_covered) and all(
                all(
                    lesson.get(field)
                    for field in _REQUIRED_CONTENT_FIELDS
                    if field != "definitions"
                )
                and "definitions" in lesson
                and len(lesson.get("sections", [])) >= 2
                and len(lesson.get("objectives", [])) >= 2
                and len(lesson.get("prerequisites", [])) >= 1
                and len(lesson.get("worked_examples", [])) >= 2
                and len(lesson.get("guided_practice", [])) >= 1
                and len(lesson.get("revision_points", [])) >= 2
                and len(lesson.get("common_mistakes", [])) >= 1
                and lesson.get("questions")
                and lesson.get("notation_review_status") in {"checked", "not_required"}
                for lesson in explicitly_covered
            )
            if (
                not explicitly_covered
                or not mandatory_fields_present
                or item["topic_scope_status"] != "complete"
                or not item["learning_outcomes"]
                or item["practice_status"] != "present"
                or item["knowledge_check_status"] != "present"
                or not topic_review_approved
                or not relation_reviews_resolved
                or not every_outcome_approved
            ):
                content_status = "content_incomplete"
            elif not item["question_ids"]:
                content_status = "content_incomplete"
            else:
                content_status = "content_complete"

        topic_decision = review_decisions.get(("topic", subtopic_id))
        review_status = (
            "approved"
            if topic_decision == "approved"
            else "awaiting_review"
            if topic_decision is not None
            else review_statuses.get(subtopic_id, "not_submitted")
        )
        publication_status = publication_statuses.get(subtopic_id, "unpublished")
        if review_status not in REVIEW_STATUSES:
            review_status = "not_submitted"
        if publication_status not in PUBLICATION_STATUSES:
            publication_status = "unpublished"
        if content_status == "content_complete":
            if publication_status == "published":
                content_status = "published"
            elif publication_status == "ready_for_publication" or review_status == "approved":
                content_status = "approved_for_publication"
            elif review_status == "reviewed":
                content_status = "reviewed"
            elif review_status == "awaiting_review":
                content_status = "awaiting_review"
        item["content_status"] = content_status
        item["lesson_content_status"] = content_status
        item["educator_review_status"] = review_status
        item["publication_status"] = publication_status
        item["last_updated"] = register.get("last_updated", "")
        item["known_gaps"] = []
        if alignment_status == "no_lesson_evidence":
            item["known_gaps"].append("No lesson alignment evidence is recorded.")
        elif alignment_status == "candidate_tag":
            item["known_gaps"].append(
                "Candidate lesson tags are not manually verified against instructional content."
            )
        if item["prerequisite_status"] == "not_assessed":
            item["known_gaps"].append("Prerequisite relationships have not been assessed.")
        if not item["learning_scope"] or not item["learning_outcomes"]:
            item["known_gaps"].append(
                "A learning scope and expected outcomes have not been recorded."
            )
        item["known_gaps"].extend(item["assessment_quality_issues"])
        if review_status == "not_submitted":
            item["known_gaps"].append("No qualified educator review has been submitted.")
        if publication_status == "unpublished":
            item["known_gaps"].append("No CMS publication record is present.")

    invalid_content_review_statuses = [
        item["id"]
        for item in subtopic_records.values()
        if (
            item["educator_review_status"] in {"awaiting_review", "reviewed", "approved"}
            and item["content_status"]
            not in {
                "awaiting_review",
                "reviewed",
                "approved_for_publication",
                "published",
            }
        )
    ]
    invalid_assessment_review_statuses = [
        item["id"]
        for item in subtopic_records.values()
        if item["assessment_status"] == "assessment_reviewed"
        and (
            item["question_count"] < question_target
            or item["assessment_quality_issues"]
        )
    ]
    validation["rules"].extend(
        [
            _issue(
                "review_status_without_content_completion",
                invalid_content_review_statuses,
                "high",
                "Only submit complete, aligned content for educator review.",
            ),
            _issue(
                "assessment_review_status_without_completion",
                invalid_assessment_review_statuses,
                "high",
                "Assessment review can be recorded only after the assessment meets "
                "its completion criteria.",
            ),
        ]
    )
    validation["status"] = (
        "issues_found"
        if any(
            rule["failures"] and rule["severity"] != "info"
            for rule in validation["rules"]
        )
        else "passed_with_notes"
        if any(rule["failures"] for rule in validation["rules"])
        else "passed"
    )

    unit_reports: list[dict[str, Any]] = []
    level_reports: list[dict[str, Any]] = []
    for level in curriculum.get("levels", []):
        level_units = []
        for source_unit in level.get("units", []):
            unit_subtopics = [
                item
                for item in subtopic_records.values()
                if item["unit_id"] == source_unit["id"]
                and item["level_id"] == level["id"]
            ]
            unit_report = {
                "id": source_unit["id"],
                "level_id": level["id"],
                "title": source_unit["title"],
                **_metrics(unit_subtopics, question_target),
                "subtopics": unit_subtopics,
            }
            level_units.append(unit_report)
            unit_reports.append(unit_report)
        level_subtopics = [
            item for unit in level_units for item in unit["subtopics"]
        ]
        level_reports.append(
            {
                "id": level["id"],
                "title": level["title"],
                **_metrics(level_subtopics, question_target),
                "units": level_units,
            }
        )

    all_subtopics = list(subtopic_records.values())
    summary = _metrics(all_subtopics, question_target)
    summary.update(
        {
            "total_levels": len(level_reports),
            "total_units": len(unit_reports),
            "total_lessons": len(lessons),
            "total_questions": len(questions),
            "lessons_served_by_static_pack": len(lessons),
            "questions_explicitly_aligned": len(
                {
                    question_id
                    for item in all_subtopics
                    for question_id in item["question_ids"]
                }
            ),
            "unlinked_lessons": validation["counts"]["unlinked_lessons"],
            "unlinked_questions": validation["counts"]["unlinked_questions"],
            "lessons_awaiting_review": sum(
                item["educator_review_status"] == "awaiting_review"
                for item in all_subtopics
            ),
            "fully_curriculum_complete": sum(
                item["content_status"]
                in {
                    "content_complete",
                    "reviewed",
                    "approved_for_publication",
                    "published",
                }
                and item["assessment_status"]
                in {"assessment_complete", "assessment_reviewed"}
                and item["alignment_status"]
                in {"manually_verified", "content_verified"}
                for item in all_subtopics
            ),
            "publication_readiness": (
                "ready"
                if all_subtopics
                and all(
                    item["publication_status"] == "ready_for_publication"
                    for item in all_subtopics
                )
                else "not_ready_for_publication"
            ),
        }
    )

    gap_units = sorted(
        (
            {
                "unit_id": unit["id"],
                "title": unit["title"],
                "incomplete_subtopics": unit["total_subtopics"] - unit["content_complete"],
                "not_started": unit["not_started"],
                "assessment_incomplete": unit["assessment_incomplete"],
            }
            for unit in unit_reports
        ),
        key=lambda item: (-item["incomplete_subtopics"], -item["not_started"], item["title"]),
    )
    return {
        "subject": register.get("subject", "Unknown"),
        "register_version": register.get("register_version", "unknown"),
        "last_updated": register.get("last_updated", ""),
        "assessment_question_target": question_target,
        "completion_policy": register.get("completion_policy", {}),
        "review_checklist": register.get("review_checklist", []),
        "summary": summary,
        "levels": level_reports,
        "subtopics": all_subtopics,
        "largest_gaps": gap_units,
        "validation": validation,
    }


def mathematics_question_quality_report() -> dict[str, Any]:
    curriculum = _curriculum()
    topic_profiles = _register().get("topic_profiles", {})
    lessons = {
        lesson["id"]: (unit, lesson)
        for level in curriculum.get("levels", [])
        for unit in level.get("units", [])
        for lesson in unit.get("lessons", [])
    }
    prompts: dict[str, list[str]] = defaultdict(list)
    questions: list[dict[str, Any]] = []
    for lesson_id, (unit, lesson) in lessons.items():
        for question in lesson.get("questions", []):
            normalized_prompt = _normalise(question.get("prompt", ""))
            if normalized_prompt:
                prompts[normalized_prompt].append(question["id"])
            questions.append(
                {
                    "lesson_id": lesson_id,
                    "unit_id": unit["id"],
                    "question": question,
                }
            )

    items = []
    for entry in questions:
        question = entry["question"]
        question_id = question["id"]
        normalized_prompt = _normalise(question.get("prompt", ""))
        duplicate_ids = sorted(
            item
            for item in prompts.get(normalized_prompt, [])
            if item != question_id
        )
        issues = []
        for field in ("prompt", "correct_answer", "explanation", "review_topic"):
            if not question.get(field):
                issues.append(f"missing_{field}")
        for field in ("learning_objective_ids", "difficulty", "purpose"):
            if not question.get(field):
                issues.append(f"missing_{field}")
        if question.get("answer_verified") is not True:
            issues.append("answer_not_verified")
        if question.get("explanation_reviewed") is not True:
            issues.append("explanation_not_reviewed")
        if question.get("mathematical_validation_status") not in {
            "author_checked",
            "independently_verified",
        }:
            issues.append("mathematics_unverified")
        if duplicate_ids:
            issues.append("duplicate_prompt")
        if question.get("type") == "short_answer" and not question.get(
            "accepted_answers"
        ):
            issues.append("missing_accepted_answers")
        try:
            _validate_question_structure(question)
            answer_structure_valid = True
        except ValueError:
            answer_structure_valid = False
            issues.append("invalid_answer_structure")
        if question.get("mathematical_validation_status") == "author_checked" and (
            question.get("answer_verified") is not True
            or not question.get("validation_working")
        ):
            issues.append("missing_author_check_evidence")
        if (
            question.get("mathematical_validation_status") == "independently_verified"
            and not question.get("independent_validation_evidence")
        ):
            issues.append("missing_independent_review_evidence")
        if question.get("educator_review_status", "not_submitted") != "approved":
            issues.append("educator_review_pending")
        allowed_objectives = set(
            topic_profiles.get(question.get("topic_id"), {}).get(
                "assessment_objectives", []
            )
        )
        if question.get("topic_id") in topic_profiles and not set(
            question.get("learning_objective_ids", [])
        ).issubset(allowed_objectives):
            issues.append("objective_not_registered_for_topic")

        if (
            any(issue.startswith("missing_") for issue in issues)
            or duplicate_ids
            or not answer_structure_valid
            or "objective_not_registered_for_topic" in issues
        ):
            quality_status = "incomplete"
        elif question.get("mathematical_validation_status") == "unverified":
            quality_status = "unverified_pending_validation"
        elif question.get("explanation_reviewed") is not True:
            quality_status = "author_checked_pending_explanation_review"
        elif question.get("educator_review_status", "not_submitted") != "approved":
            quality_status = "quality_checked_pending_educator_review"
        else:
            quality_status = "reviewed"

        items.append(
            {
                "question_id": question_id,
                "lesson_id": entry["lesson_id"],
                "unit_id": entry["unit_id"],
                "topic_id": question.get("topic_id"),
                "review_topic": question.get("review_topic"),
                "alignment_status": question.get("alignment_status", "candidate_tag"),
                "question_type": question.get("type"),
                "difficulty": question.get("difficulty"),
                "purpose": question.get("purpose"),
                "learning_objective_ids": question.get("learning_objective_ids", []),
                "mathematical_validation_status": question.get(
                    "mathematical_validation_status", "unverified"
                ),
                "answer_structure_valid": answer_structure_valid,
                "answer_verified": question.get("answer_verified") is True,
                "has_answer_validation_working": bool(
                    question.get("validation_working")
                ),
                "explanation_reviewed": question.get("explanation_reviewed") is True,
                "educator_review_status": question.get(
                    "educator_review_status", "not_submitted"
                ),
                "duplicate_question_ids": duplicate_ids,
                "quality_status": quality_status,
                "issues": issues,
            }
        )

    return {
        "subject": "Mathematics",
        "scope": "All questions in the learner Mathematics package.",
        "answer_keys_included": False,
        "prompt_text_included": False,
        "total_questions": len(items),
        "author_checked": sum(
            item["mathematical_validation_status"] == "author_checked"
            for item in items
        ),
        "independently_verified": sum(
            item["mathematical_validation_status"] == "independently_verified"
            for item in items
        ),
        "mathematics_unverified": sum(
            item["mathematical_validation_status"] == "unverified"
            for item in items
        ),
        "educator_review_pending": sum(
            item["educator_review_status"] != "approved" for item in items
        ),
        "educator_reviewed": sum(
            item["educator_review_status"] in {"reviewed", "approved"}
            for item in items
        ),
        "educator_review_status_counts": dict(
            Counter(item["educator_review_status"] for item in items)
        ),
        "assessment_purpose_counts": dict(
            Counter(item["purpose"] or "missing" for item in items)
        ),
        "difficulty_counts": dict(
            Counter(item["difficulty"] or "missing" for item in items)
        ),
        "invalid_answer_structures": sum(
            not item["answer_structure_valid"] for item in items
        ),
        "questions_without_objectives": sum(
            not item["learning_objective_ids"] for item in items
        ),
        "questions_with_unregistered_objectives": sum(
            "objective_not_registered_for_topic" in item["issues"]
            for item in items
        ),
        "quality_status_counts": dict(
            Counter(item["quality_status"] for item in items)
        ),
        "duplicate_prompt_questions": sum(bool(item["duplicate_question_ids"]) for item in items),
        "duplicate_prompt_groups": sum(
            len(question_ids) > 1 for question_ids in prompts.values()
        ),
        "items": items,
    }

def mathematics_question_validation_review_report() -> dict[str, Any]:
    curriculum = _curriculum()
    items = [
        {
            "question_id": question["id"],
            "lesson_id": lesson["id"],
            "topic_id": question.get("topic_id"),
            "prompt": question["prompt"],
            "question_type": question["type"],
            "options": question.get("options", []),
            "expected_answer": question["correct_answer"],
            "accepted_answers": question.get("accepted_answers", []),
            "explanation": question["explanation"],
            "validation_working": question.get("validation_working"),
            "learning_objective_ids": question.get("learning_objective_ids", []),
            "difficulty": question.get("difficulty"),
            "purpose": question.get("purpose"),
            "mathematical_validation_status": question.get(
                "mathematical_validation_status", "unverified"
            ),
            "answer_verified": question.get("answer_verified") is True,
            "explanation_reviewed": question.get("explanation_reviewed") is True,
            "independent_validation_evidence": question.get(
                "independent_validation_evidence"
            ),
            "educator_review_status": question.get(
                "educator_review_status", "not_submitted"
            ),
            "educator_review_record": question.get("educator_review_record"),
            "review_decision": "pending",
            "reviewer_identity": None,
            "review_date": None,
            "reviewer_comments": "",
        }
        for level in curriculum.get("levels", [])
        for unit in level.get("units", [])
        for lesson in unit.get("lessons", [])
        for question in lesson.get("questions", [])
    ]
    return {
        "report_id": "mathematics-question-validation-review",
        "status": "review_ready_not_independently_reviewed",
        "scope": "All question items in the learner Mathematics package.",
        "contains_answer_keys": True,
        "not_for_learner_api": True,
        "independent_verification_claimed": False,
        "educator_review_claimed": False,
        "total_questions": len(items),
        "mathematical_validation_status_counts": dict(
            Counter(item["mathematical_validation_status"] for item in items)
        ),
        "educator_review_status_counts": dict(
            Counter(item["educator_review_status"] for item in items)
        ),
        "items": items,
    }


def mathematics_number_systems_question_audit_report() -> dict[str, Any]:
    curriculum = _curriculum()
    topic_profiles = _register().get("topic_profiles", {})
    prompt_owners: dict[str, list[str]] = defaultdict(list)
    entries = []
    for level in curriculum.get("levels", []):
        for unit in level.get("units", []):
            if unit.get("id") != "number-systems":
                continue
            for lesson in unit.get("lessons", []):
                for question in lesson.get("questions", []):
                    prompt_owners[_normalise(question.get("prompt", ""))].append(
                        question["id"]
                    )
                    entries.append((lesson, question))

    items = []
    for lesson, question in entries:
        question_id = question["id"]
        topic_id = question.get("topic_id")
        objective_ids = question.get("learning_objective_ids", [])
        registered_objectives = set(
            topic_profiles.get(topic_id, {}).get("assessment_objectives", [])
        )
        unregistered_objectives = sorted(set(objective_ids) - registered_objectives)
        duplicate_ids = sorted(
            question_id_item
            for question_id_item in prompt_owners.get(
                _normalise(question.get("prompt", "")), []
            )
            if question_id_item != question_id
        )
        structural_issues = []
        try:
            _validate_question_structure(question)
        except ValueError as error:
            structural_issues.append(str(error))
        if not objective_ids:
            structural_issues.append("missing_learning_objective_ids")
        if not question.get("difficulty"):
            structural_issues.append("missing_difficulty")
        if not question.get("purpose"):
            structural_issues.append("missing_assessment_purpose")
        if unregistered_objectives:
            structural_issues.append(
                f"objectives_not_registered_for_topic:{','.join(unregistered_objectives)}"
            )
        if duplicate_ids:
            structural_issues.append(f"duplicate_prompt_with:{','.join(duplicate_ids)}")
        if question.get("type") == "short_answer" and not question.get(
            "accepted_answers"
        ):
            structural_issues.append("missing_accepted_answers")
        if not question.get("validation_working"):
            structural_issues.append("missing_author_calculation_notes")

        validation_status = question.get(
            "mathematical_validation_status", "unverified"
        )
        items.append(
            {
                "question_id": question_id,
                "lesson_id": lesson["id"],
                "topic_id": topic_id,
                "learning_objective_ids": objective_ids,
                "question_type": question.get("type"),
                "difficulty": question.get("difficulty"),
                "purpose": question.get("purpose"),
                "prompt": question.get("prompt"),
                "options": question.get("options", []),
                "expected_answer": question.get("correct_answer"),
                "accepted_answers": question.get("accepted_answers", []),
                "explanation": question.get("explanation"),
                "original_validation_status": validation_status,
                "revised_validation_status": validation_status,
                "mathematical_correctness_assessment": (
                    "not_independently_rechecked_in_phase_d"
                ),
                "answer_key_assessment": (
                    "existing_author_check_carried_forward; independent verification pending"
                    if validation_status == "author_checked"
                    else "unverified; author and independent checks pending"
                ),
                "explanation_assessment": "human instructional review pending",
                "distractor_assessment": (
                    "human plausibility and single-correct-answer review pending"
                    if question.get("type") == "multiple_choice"
                    else "not_applicable"
                ),
                "alignment_assessment": (
                    "topic and objective metadata are structurally registered"
                    if topic_id in topic_profiles and not unregistered_objectives
                    else "topic/objective alignment requires review"
                ),
                "identified_issue": structural_issues,
                "correction_made": "",
                "reviewer_decision_required": True,
                "reviewer_decision": "pending_review",
                "reviewer_identity": None,
                "review_date": None,
                "reviewer_comments": "",
                "author_calculation_notes": question.get("validation_working", ""),
                "audit_provenance": (
                    "Phase D structural and metadata screening only; existing author "
                    "status retained; no independent verification claimed."
                ),
            }
        )

    return {
        "report_id": "mathematics-number-systems-question-audit-phase-d",
        "status": "review_ready_not_independently_reviewed",
        "scope": "Number Systems Unit 1 only; answer keys are reviewer-only.",
        "contains_answer_keys": True,
        "not_for_learner_api": True,
        "total_questions": len(items),
        "source_author_checked": sum(
            item["original_validation_status"] == "author_checked"
            for item in items
        ),
        "source_unverified": sum(
            item["original_validation_status"] == "unverified" for item in items
        ),
        "independently_verified": 0,
        "educator_reviewed": 0,
        "structural_issues": sum(bool(item["identified_issue"]) for item in items),
        "questions_requiring_independent_review": len(items),
        "items": items,
    }


def mathematics_number_systems_educator_review_pack() -> dict[str, Any]:
    register = _register()
    curriculum = _curriculum()
    profiles = register.get("topic_profiles", {})
    audits = register.get("lesson_alignment_audit", [])
    lessons = {
        lesson["id"]: lesson
        for level in curriculum.get("levels", [])
        for unit in level.get("units", [])
        for lesson in unit.get("lessons", [])
        if unit["id"] == "number-systems"
    }

    def question_review_item(lesson: dict[str, Any], question: dict[str, Any]):
        return {
            "question_id": question["id"],
            "lesson_id": lesson["id"],
            "topic_id": question.get("topic_id"),
            "learning_objective_ids": question.get("learning_objective_ids", []),
            "difficulty": question.get("difficulty"),
            "purpose": question.get("purpose"),
            "question_type": question["type"],
            "prompt": question["prompt"],
            "options": question.get("options", []),
            "expected_answer": question["correct_answer"],
            "accepted_answers": question.get("accepted_answers", []),
            "explanation": question["explanation"],
            "author_calculation_notes": question.get("validation_working"),
            "mathematical_validation_status": question.get(
                "mathematical_validation_status", "unverified"
            ),
            "educator_review_status": question.get(
                "educator_review_status", "not_submitted"
            ),
            "review_decision": "pending",
            "reviewer_identity": None,
            "review_date": None,
            "reviewer_comments": "",
        }

    topic_items = []
    linked_question_ids: set[str] = set()
    for topic_id, profile in profiles.items():
        relationships = []
        for audit in audits:
            if topic_id not in audit.get("candidate_topic_ids", []):
                continue
            lesson = lessons.get(audit["lesson_id"])
            if lesson is None:
                continue
            relevant_sections = [
                section
                for section in lesson.get("sections", [])
                if section.get("title") in audit.get("section_titles", [])
            ]
            topic_question_refs = [
                question
                for question in lesson.get("questions", [])
                if question.get("topic_id") == topic_id
            ]
            outcome_evidence = []
            for outcome_index, outcome in enumerate(
                profile.get("expected_learning_outcomes", [])
            ):
                outcome_evidence.append(
                    {
                        "outcome_id": (
                            f"{topic_id}::{lesson['id']}::outcome::{outcome_index}"
                        ),
                        "outcome": outcome,
                        "evidence_status": "candidate_reference_only",
                        "adequacy": "requires_educator_review",
                        "evidence_references": {
                            "lesson_sections": [
                                section["title"] for section in relevant_sections
                            ],
                            "worked_example_indices": list(
                                range(len(lesson.get("worked_examples", [])))
                            ),
                            "guided_practice_indices": list(
                                range(len(lesson.get("guided_practice", [])))
                            ),
                            "independent_practice_question_ids": [
                                question["id"] for question in topic_question_refs
                            ],
                        },
                        "reviewer_decision": "pending",
                        "reviewer_comments": "",
                    }
                )
            relationships.append(
                {
                    "lesson_id": lesson["id"],
                    "lesson_title": lesson["title"],
                    "alignment_status": audit.get("alignment_status", "candidate"),
                    "audit_status": "partially_supported",
                    "outcome_coverage_status": "requires_educator_review",
                    "learning_outcomes": outcome_evidence,
                    "outcomes_addressed": audit.get("outcomes_addressed", []),
                    "outcomes_partially_addressed": audit.get(
                        "outcomes_partially_addressed", []
                    ),
                    "outcomes_missing": audit.get("outcomes_missing", []),
                    "outcomes_pending_review": [
                        outcome
                        for outcome in profile.get(
                            "expected_learning_outcomes", []
                        )
                        if outcome
                        not in {
                            *audit.get("outcomes_addressed", []),
                            *audit.get("outcomes_partially_addressed", []),
                            *audit.get("outcomes_missing", []),
                        }
                    ],
                    "evidence_quotes": [
                        {
                            "section_title": section["title"],
                            "text": section["body"],
                        }
                        for section in relevant_sections
                    ],
                    "lesson_objectives": lesson.get("objectives", []),
                    "prerequisites": lesson.get("prerequisites", []),
                    "definitions": lesson.get("definitions", []),
                    "lesson_sections": lesson.get("sections", []),
                    "worked_examples": lesson.get("worked_examples", []),
                    "guided_practice": lesson.get("guided_practice", []),
                    "revision_points": lesson.get("revision_points", []),
                    "real_world_application": lesson.get(
                        "real_world_application", ""
                    ),
                    "visual": lesson.get("visual"),
                    "common_mistakes": lesson.get("common_mistakes", []),
                    "summary": lesson.get("summary", ""),
                    "notation_review_status": lesson.get(
                        "notation_review_status", "not_recorded"
                    ),
                    "instructional_dimensions": {
                        "learning_objectives": bool(lesson.get("objectives")),
                        "prerequisite_knowledge": bool(lesson.get("prerequisites")),
                        "conceptual_explanations": len(
                            lesson.get("sections", [])
                        ) >= 2,
                        "definitions": bool(lesson.get("definitions")),
                        "worked_examples": len(
                            lesson.get("worked_examples", [])
                        ) >= 2,
                        "worked_reasoning": all(
                            len(example.get("steps", [])) >= 2
                            for example in lesson.get("worked_examples", [])
                        ),
                        "guided_practice": bool(lesson.get("guided_practice")),
                        "independent_practice": bool(lesson.get("questions")),
                        "real_world_application": bool(
                            lesson.get("real_world_application")
                        ),
                        "misconceptions": bool(lesson.get("common_mistakes")),
                        "lesson_summary": bool(lesson.get("summary")),
                        "notation_review_status": lesson.get(
                            "notation_review_status", "not_recorded"
                        ),
                    },
                    "missing_instructional_content": audit.get(
                        "missing_instructional_content", []
                    ),
                    "outcome_evidence": outcome_evidence,
                    "validation_notes": audit.get("validation_notes", ""),
                    "review_decision": "pending",
                    "reviewer_identity": None,
                    "review_date": None,
                    "reviewer_comments": "",
                }
            )
        questions = [
            question_review_item(lesson, question)
            for lesson in lessons.values()
            for question in lesson.get("questions", [])
            if question.get("topic_id") == topic_id
        ]
        linked_question_ids.update(
            question["question_id"] for question in questions
        )
        topic_items.append(
            {
                "topic_id": topic_id,
                "topic_name": next(
                    (
                        record["title"]
                        for record in register.get("subtopic_records", [])
                        if record["id"] == topic_id
                    ),
                    topic_id.rsplit("/", 1)[-1],
                ),
                "definition": profile.get("definition"),
                "learning_scope": profile.get("learning_scope"),
                "expected_learning_outcomes": profile.get(
                    "expected_learning_outcomes", []
                ),
                "prerequisite_knowledge": profile.get(
                    "prerequisite_knowledge", []
                ),
                "concepts_to_teach": profile.get("concepts_to_teach", []),
                "misconceptions": profile.get("misconceptions", []),
                "assessment_objectives": profile.get(
                    "assessment_objectives", []
                ),
                "assessment_blueprint": profile.get("blueprint", {}),
                "topic_review_decision": "pending",
                "topic_reviewer_identity": None,
                "topic_review_date": None,
                "topic_reviewer_comments": "",
                "lesson_relationships": relationships,
                "questions": questions,
            }
        )

    unlinked_questions = [
        question_review_item(lesson, question)
        for lesson in lessons.values()
        for question in lesson.get("questions", [])
        if question.get("id") not in linked_question_ids
    ]
    for question in unlinked_questions:
        question["topic_assignment_decision"] = "remain_unlinked_pending_scope"
        question["topic_assignment_note"] = (
            "The item assesses rational repeating decimals, which is not one "
            "of the 20 registered Number Systems topics. Do not force a link."
            if question["question_id"] == "math-numbers-q1"
            else "No registered topic relationship has been approved."
        )

    return {
        "pack_id": "mathematics-number-systems-educator-review-phase-c",
        "status": "review_ready_pending_human_review",
        "contains_answer_keys": True,
        "not_for_learner_api": True,
        "educator_review_claimed": False,
        "independent_verification_claimed": False,
        "review_workflow": {
            "sequence": [
                "Review one topic profile and its outcomes.",
                "Inspect each listed lesson excerpt and decide whether each outcome is taught.",
                "Review each linked question, answer and explanation.",
                "Record reviewer identity, date, decision and comments before changing any status.",
            ],
            "allowed_decisions": [
                "approved",
                "rejected",
                "revision_requested",
            ],
            "allowed_outcome_decisions": [
                "addressed",
                "partially_addressed",
                "missing",
            ],
            "pending_decisions_are_not_approvals": True,
            "no_review_api_or_educator_identity_provider_available": True,
        },
        "topic_count": len(topic_items),
        "linked_question_count": sum(
            len(topic["questions"]) for topic in topic_items
        ),
        "unlinked_question_count": len(unlinked_questions),
        "topics": topic_items,
        "unlinked_questions": unlinked_questions,
    }


def mathematics_coverage_report(
    review_decisions: dict[tuple[str, str], str] | None = None,
) -> dict[str, Any]:
    return build_curriculum_coverage_report(
        _register(), _curriculum(), review_decisions=review_decisions
    )


def mathematics_coverage_validation_report() -> dict[str, Any]:
    return validate_curriculum_register(_register(), _curriculum())
