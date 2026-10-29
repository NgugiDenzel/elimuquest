from dataclasses import dataclass


@dataclass(frozen=True)
class SubjectDefinition:
    slug: str
    code: str
    name: str
    icon: str
    accent: str
    description: str
    source_id: str
    discipline_group: str | None = None


@dataclass(frozen=True)
class LevelDefinition:
    system: str
    level: str
    version: str
    label: str
    source_id: str
    subjects: tuple[SubjectDefinition, ...]


LEVELS = (
    LevelDefinition(
        system="CBC_CBE",
        level="Grade 6",
        version="KICD-G6-VERSION-UNVERIFIED",
        label="Grade 6 · CBC/CBE",
        source_id="KICD-G6-DESIGNS",
        subjects=(
            SubjectDefinition(
                "mathematics-grade-6",
                "M6",
                "Mathematics",
                "📐",
                "#F06595",
                "Grade 6 Mathematics learning area.",
                "KICD-G6-DESIGNS",
            ),
            SubjectDefinition(
                "english-grade-6",
                "E6",
                "English",
                "📖",
                "#5C7CFA",
                "Grade 6 English learning area.",
                "KICD-G6-DESIGNS",
            ),
            SubjectDefinition(
                "kiswahili-grade-6",
                "K6",
                "Kiswahili",
                "🗣️",
                "#27C07C",
                "Grade 6 Kiswahili learning area.",
                "KICD-G6-DESIGNS",
            ),
            SubjectDefinition(
                "science-technology-grade-6",
                "ST6",
                "Science & Technology",
                "🔬",
                "#F5B942",
                "Grade 6 Science and Technology learning area.",
                "KICD-G6-DESIGNS",
            ),
        ),
    ),
    LevelDefinition(
        system="CBC_CBE",
        level="Grade 9",
        version="KICD-G9-2024-07",
        label="Grade 9 · CBC/CBE",
        source_id="KICD-G9-DESIGNS",
        subjects=(
            SubjectDefinition(
                "mathematics-grade-9",
                "M9",
                "Mathematics",
                "📐",
                "#F06595",
                "Grade 9 Mathematics learning area.",
                "KICD-G9-DESIGNS",
            ),
            SubjectDefinition(
                "english-grade-9",
                "E9",
                "English",
                "📖",
                "#5C7CFA",
                "Grade 9 English learning area.",
                "KICD-G9-DESIGNS",
            ),
            SubjectDefinition(
                "kiswahili-grade-9",
                "K9",
                "Kiswahili",
                "🗣️",
                "#27C07C",
                "Grade 9 Kiswahili learning area.",
                "KICD-G9-DESIGNS",
            ),
            SubjectDefinition(
                "integrated-science-grade-9",
                "IS9",
                "Integrated Science",
                "🧪",
                "#F5B942",
                "Grade 9 Integrated Science learning area.",
                "KICD-G9-DESIGNS",
            ),
        ),
    ),
    LevelDefinition(
        system="8_4_4",
        level="Form 4",
        version="KICD-844-VERSION-UNVERIFIED",
        label="Form 4 · 8-4-4",
        source_id="KICD-844",
        subjects=(
            SubjectDefinition(
                "mathematics-form-4",
                "M4",
                "Mathematics",
                "📐",
                "#F06595",
                "Form 4 Mathematics.",
                "KICD-844",
            ),
            SubjectDefinition(
                "english-form-4", "E4", "English", "📖", "#5C7CFA", "Form 4 English.", "KICD-844"
            ),
            SubjectDefinition(
                "kiswahili-form-4",
                "K4",
                "Kiswahili",
                "🗣️",
                "#27C07C",
                "Form 4 Kiswahili.",
                "KICD-844",
            ),
            SubjectDefinition(
                "chemistry-form-4",
                "CH4",
                "Chemistry",
                "⚗️",
                "#F5B942",
                "Form 4 Chemistry.",
                "KICD-844",
            ),
            SubjectDefinition(
                "physics-form-4", "PH4", "Physics", "🚀", "#9F7AEA", "Form 4 Physics.", "KICD-844"
            ),
        ),
    ),
)

LEVEL_BY_SELECTION = {(item.system, item.level): item for item in LEVELS}
SOURCE_IDS = frozenset(item.source_id for item in LEVELS)


def level_for(system: str, level: str) -> LevelDefinition | None:
    return LEVEL_BY_SELECTION.get((system, level))


def subject_for_slug(slug: str) -> tuple[LevelDefinition, SubjectDefinition] | None:
    for level in LEVELS:
        for subject in level.subjects:
            if subject.slug == slug:
                return level, subject
    return None


def curriculum_options() -> list[dict[str, object]]:
    return [
        {
            "system": level.system,
            "level": level.level,
            "label": level.label,
            "version": level.version,
            "subjects": [
                {
                    "id": subject.slug,
                    "name": subject.name,
                    "icon": subject.icon,
                    "discipline_group": subject.discipline_group,
                }
                for subject in level.subjects
            ],
        }
        for level in LEVELS
    ]
