from sqlalchemy import select

from app.core.config import settings
from app.curriculum.catalog import LEVELS
from app.db.session import SessionLocal
from app.models import Achievement, Lesson, LessonQuestion, Subject, Topic

DEMO_SUBJECTS = [
    {
        "slug": "biology",
        "name": "Biology",
        "code": "BIO",
        "accent": "#34A853",
        "icon": "🧬",
        "topic": "Cell biology",
        "lesson": "Cell Structure & Function",
        "lesson_slug": "cell-structure",
        "content": (
            "Fictional demonstration content: cells are the basic structural and functional "
            "units of living organisms."
        ),
        "questions": [
            (
                "Which structure controls many activities of a eukaryotic cell?",
                ["Nucleus", "Cell wall", "Vacuole"],
                "Nucleus",
                "The nucleus contains genetic material and helps regulate cell activity.",
            ),
            (
                "Which organelle releases energy during aerobic respiration?",
                ["Mitochondrion", "Ribosome", "Chloroplast"],
                "Mitochondrion",
                "Mitochondria are the main site of aerobic respiration.",
            ),
        ],
    },
    {
        "slug": "chemistry",
        "name": "Chemistry",
        "code": "CHE",
        "accent": "#5C7CFA",
        "icon": "⚗️",
        "topic": "Acids and bases",
        "lesson": "Acids & Bases",
        "lesson_slug": "acids-and-bases",
        "content": (
            "Fictional demonstration content: acids and bases have characteristic reactions "
            "and indicators."
        ),
        "questions": [
            (
                "What colour does blue litmus turn in an acid?",
                ["Red", "Green", "Blue"],
                "Red",
                "Acids turn blue litmus paper red.",
            ),
        ],
    },
    {
        "slug": "physics",
        "name": "Physics",
        "code": "PHY",
        "accent": "#FFB703",
        "icon": "🚀",
        "topic": "Motion",
        "lesson": "Motion & Force",
        "lesson_slug": "motion-and-force",
        "content": (
            "Fictional demonstration content: motion describes changes in position over time."
        ),
        "questions": [
            (
                "What is the SI unit of force?",
                ["Newton", "Joule", "Watt"],
                "Newton",
                "Force is measured in newtons (N).",
            ),
        ],
    },
    {
        "slug": "mathematics",
        "name": "Mathematics",
        "code": "MAT",
        "accent": "#F06595",
        "icon": "📐",
        "topic": "Algebra",
        "lesson": "Algebraic Expressions",
        "lesson_slug": "algebraic-expressions",
        "content": (
            "Fictional demonstration content: algebra uses symbols to represent quantities "
            "and relationships."
        ),
        "questions": [
            (
                "Simplify 3x + 2x.",
                ["5x", "6x", "5x²"],
                "5x",
                "Like terms add their coefficients: 3x + 2x = 5x.",
            ),
        ],
    },
]


def seed() -> None:
    if settings.app_env.lower() != "development":
        raise RuntimeError("Development seed is disabled unless APP_ENV=development")
    with SessionLocal.begin() as db:
        for level in LEVELS:
            for definition in level.subjects:
                subject = db.scalar(select(Subject).where(Subject.slug == definition.slug))
                if subject is None:
                    db.add(
                        Subject(
                            slug=definition.slug,
                            name=definition.name,
                            code=definition.code,
                            description=definition.description,
                            accent=definition.accent,
                            icon=definition.icon,
                            curriculum_system=level.system,
                            curriculum_level=level.level,
                            curriculum_version=level.version,
                            source_id=definition.source_id,
                            discipline_group=definition.discipline_group,
                            is_demo=False,
                        )
                    )
        for item in DEMO_SUBJECTS:
            subject = db.scalar(select(Subject).where(Subject.slug == item["slug"]))
            if subject is None:
                subject = Subject(
                    slug=item["slug"],
                    name=item["name"],
                    code=item["code"],
                    accent=item["accent"],
                    icon=item["icon"],
                    description="Fictional, non-official learning demonstration content.",
                    is_demo=True,
                )
                db.add(subject)
                db.flush()
            topic = db.scalar(
                select(Topic).where(Topic.subject_id == subject.id, Topic.slug == item["slug"])
            )
            if topic is None:
                topic = Topic(subject_id=subject.id, slug=item["slug"], name=item["topic"])
                db.add(topic)
                db.flush()
            lesson = db.scalar(select(Lesson).where(Lesson.slug == item["lesson_slug"]))
            if lesson is None:
                lesson = Lesson(
                    topic_id=topic.id,
                    slug=item["lesson_slug"],
                    title=item["lesson"],
                    description="A short fictional demonstration lesson.",
                    content=item["content"],
                    sort_order=1,
                    published=True,
                    content_status="published",
                    is_demo=True,
                )
                db.add(lesson)
                db.flush()
            if not lesson.questions:
                for order, (prompt, options, correct, explanation) in enumerate(item["questions"]):
                    db.add(
                        LessonQuestion(
                            lesson_id=lesson.id,
                            prompt=prompt,
                            options=options,
                            correct_answer=correct,
                            explanation=explanation,
                            sort_order=order,
                        )
                    )
        achievement = db.scalar(select(Achievement).where(Achievement.slug == "first-lesson"))
        if achievement is None:
            db.add(
                Achievement(
                    slug="first-lesson",
                    name="First Steps",
                    description="Complete your first lesson.",
                    xp_threshold=0,
                    lesson_threshold=1,
                )
            )


if __name__ == "__main__":
    seed()
    print("Development demonstration content is ready.")
