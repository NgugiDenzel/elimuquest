import argparse
import hashlib
import json
import sys
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.schema import ContentPackage, LessonPackage
from app.curriculum.catalog import level_for, subject_for_slug
from app.db.session import SessionLocal
from app.models import Lesson, LessonQuestion, Subject, Topic


class ContentImportError(Exception):
    pass


def _lesson_hash(package: ContentPackage, lesson: LessonPackage) -> str:
    payload = {
        "ai_generated": package.ai_generated,
        "curriculum_system": package.curriculum_system,
        "curriculum_level": package.curriculum_level,
        "curriculum_version": package.curriculum_version,
        "subject_slug": package.subject_slug,
        "topic_slug": package.topic_slug,
        "topic_name": package.topic_name,
        "topic_source_reference": package.topic_source_reference,
        "source_id": package.source_id,
        "is_demo": package.is_demo,
        "lesson": lesson.model_dump(mode="json"),
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def import_content(
    package: ContentPackage, db: Session, *, apply: bool = False
) -> dict[str, object]:
    selection = level_for(package.curriculum_system, package.curriculum_level)
    subject_definition = subject_for_slug(package.subject_slug)
    if selection is None or subject_definition is None:
        raise ContentImportError("Curriculum or subject mapping is not registered")

    subject = db.scalar(
        select(Subject).where(
            Subject.slug == package.subject_slug,
            Subject.curriculum_system == selection.system,
            Subject.curriculum_level == selection.level,
            Subject.curriculum_version == selection.version,
        )
    )
    if subject is None:
        raise ContentImportError("Mapped subject is not seeded in the database")

    topic = db.scalar(
        select(Topic).where(Topic.subject_id == subject.id, Topic.slug == package.topic_slug)
    )
    if topic and (
        topic.name != package.topic_name or topic.source_reference != package.topic_source_reference
    ):
        raise ContentImportError(
            f"Existing topic {package.topic_slug!r} has different metadata; refusing overwrite"
        )
    planned: list[tuple[LessonPackage, str, Lesson | None]] = []
    conflicts: list[str] = []
    for lesson_package in package.lessons:
        digest = _lesson_hash(package, lesson_package)
        existing = db.scalar(select(Lesson).where(Lesson.slug == lesson_package.slug))
        if existing is None:
            planned.append((lesson_package, digest, None))
        elif existing.content_hash == digest:
            planned.append((lesson_package, digest, existing))
        else:
            conflicts.append(lesson_package.slug)
    if conflicts:
        raise ContentImportError(
            "Existing lesson content differs or lacks an import hash; refusing overwrite: "
            + ", ".join(conflicts)
        )

    created = [item for item in planned if item[2] is None]
    unchanged = len(planned) - len(created)
    if apply and created:
        if topic is None:
            topic = Topic(
                subject_id=subject.id,
                slug=package.topic_slug,
                name=package.topic_name,
                source_reference=package.topic_source_reference,
            )
            db.add(topic)
            db.flush()
        for lesson_package, digest, _ in planned:
            if db.scalar(select(Lesson.id).where(Lesson.slug == lesson_package.slug)):
                continue
            lesson = Lesson(
                topic_id=topic.id,
                slug=lesson_package.slug,
                title=lesson_package.title,
                description=lesson_package.description,
                content=lesson_package.content,
                learning_objectives=lesson_package.learning_objectives,
                prerequisites=lesson_package.prerequisites,
                explanation_sections=[
                    section.model_dump() for section in lesson_package.explanation_sections
                ],
                worked_examples=[
                    example.model_dump() for example in lesson_package.worked_examples
                ],
                sort_order=lesson_package.sort_order,
                published=False,
                content_status="draft",
                content_version=lesson_package.content_version,
                content_hash=digest,
                ai_generated=package.ai_generated,
                source_id=package.source_id,
                source_reference=lesson_package.source_reference,
                author=lesson_package.author,
                is_demo=package.is_demo,
            )
            db.add(lesson)
            db.flush()
            db.add_all(
                [
                    LessonQuestion(
                        lesson_id=lesson.id,
                        prompt=question.prompt,
                        options=question.options,
                        correct_answer=question.correct_answer,
                        explanation=question.explanation,
                        question_type=question.question_type,
                        difficulty=question.difficulty,
                        sort_order=question_order,
                    )
                    for question_order, question in enumerate(lesson_package.questions)
                ]
            )

    return {
        "mode": "apply" if apply else "dry-run",
        "created": len(created),
        "unchanged": unchanged,
        "status": "draft",
        "lesson_slugs": [lesson.slug for lesson, _, _ in planned],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and import a curriculum content package."
    )
    parser.add_argument(
        "package",
        type=Path,
        help="Path to a JSON content package or a directory of JSON packages",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist validated content as drafts. Omit for a read-only dry run.",
    )
    args = parser.parse_args()

    try:
        package_paths = (
            sorted(args.package.glob("*.json")) if args.package.is_dir() else [args.package]
        )
        if not package_paths:
            raise ContentImportError(f"No JSON content packages found in {args.package}")
        packages = [
            (path.name, ContentPackage.model_validate_json(path.read_text(encoding="utf-8")))
            for path in package_paths
        ]
        with SessionLocal.begin() as db:
            results = [
                (name, import_content(package, db, apply=args.apply))
                for name, package in packages
            ]
        if args.package.is_dir():
            result = {
                "mode": "apply" if args.apply else "dry-run",
                "packages": len(results),
                "created": sum(item["created"] for _, item in results),
                "unchanged": sum(item["unchanged"] for _, item in results),
                "status": "draft",
                "results": [
                    {"package": name, **item} for name, item in results
                ],
            }
        else:
            result = results[0][1]
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValidationError, ContentImportError) as error:
        print(f"Content import failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
