import csv
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path, PureWindowsPath

ROOT = Path(__file__).resolve().parents[2]
DATABASE = ROOT / "backend" / "elimuquest.db"
DOCS = ROOT / "docs"
SOURCE_REGISTER = DOCS / "EDUCATIONAL_SOURCE_REGISTER.csv"


def read_only_database() -> sqlite3.Connection:
    if not DATABASE.is_file():
        raise FileNotFoundError(f"Active database not found: {DATABASE}")
    connection = sqlite3.connect(f"file:{DATABASE.as_posix()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def json_list(value: str | None) -> list:
    if not value:
        return []
    try:
        result = json.loads(value)
    except json.JSONDecodeError:
        return []
    return result if isinstance(result, list) else []


def write_csv(name: str, headers: list[str], rows: list[dict[str, object]]) -> None:
    path = DOCS / name
    with path.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalized_prompt(prompt: str) -> str:
    normalized = unicodedata.normalize("NFKC", prompt).casefold()
    return re.sub(r"\W+", " ", normalized).strip()


def source_clearance(title: str, publisher: str) -> tuple[str, str, str]:
    label = title.casefold()
    notes = publisher.casefold()
    if "original elimuquest" in label:
        return (
            "Original content; no third-party license asserted",
            "Package authoring/provenance record; official curriculum alignment unverified",
            "Original content — provenance documented",
        )
    if "openstax biology" in label:
        return (
            "CC BY-NC-SA 4.0 reported; AI-offering permission restriction reported",
            "Existing register cites OpenStax terms; source text was not reproduced per record",
            "Restricted — permission or conditions required",
        )
    if "university physics volume 1" in label:
        return (
            "CC BY-NC-SA 4.0; prior written permission for generative-AI offerings reported",
            "Volume 1 introduction terms recorded in the existing source register",
            "Restricted — permission or conditions required",
        )
    if "chemistry 2e" in label or (
        "university physics volume 2" in label or "university physics volume 3" in label
    ):
        return (
            "Not independently verified for this book/version",
            "The accessed topic pages did not establish applicable license/AI-offering terms",
            "Unverified",
        )
    if "purdue" in label or "copyright" in notes:
        return (
            "Copyright/reuse terms not established as permission for redistribution",
            "Existing register records a copyright notice; reference-only use is not clearance",
            "Restricted — permission or conditions required",
        )
    if "arena.co.ke" in notes or "user-supplied pdf" in notes:
        return (
            "Not verified",
            "Publisher/reuse license not established in the local source inventory",
            "Unverified",
        )
    if "niddk" in label or "niddk" in notes or "reuse/license terms not assessed" in notes:
        return (
            "Not assessed",
            "Public accessibility does not establish reuse permission",
            "Unverified",
        )
    return (
        "Not verified in this audit",
        "Existing source entry is retained; no additional license evidence was established",
        "Unverified",
    )


def export_lessons(connection: sqlite3.Connection) -> list[dict[str, object]]:
    lessons = connection.execute(
        """
        SELECT l.*, t.name AS topic_name, t.source_reference AS topic_source_reference,
               s.name AS subject_name, s.curriculum_system, s.curriculum_level,
               s.curriculum_version,
               (SELECT COUNT(*) FROM lesson_questions q WHERE q.lesson_id = l.id) AS question_count
        FROM lessons l
        JOIN topics t ON t.id = l.topic_id
        JOIN subjects s ON s.id = t.subject_id
        ORDER BY s.curriculum_system, s.curriculum_level, s.name, t.name, l.sort_order, l.title
        """
    ).fetchall()
    rows = []
    for lesson in lessons:
        published = bool(lesson["published"]) and lesson["content_status"] == "published"
        objectives = json_list(lesson["learning_objectives"])
        explanations = json_list(lesson["explanation_sections"])
        source_recorded = bool(lesson["source_id"] or lesson["source_reference"])
        flags = []
        if not objectives:
            flags.append("missing learning objectives")
        if not explanations:
            flags.append("missing explanation sections")
        if not source_recorded:
            flags.append("no lesson-level source locator")
        if published and (not lesson["reviewer"] or not lesson["reviewed_at"]):
            flags.append("published without reviewer metadata")
        if bool(lesson["published"]) != (lesson["content_status"] == "published"):
            flags.append("publication flag/status mismatch")
        if flags:
            severity = "Medium" if published else "Low"
        else:
            severity = "Not assessed"
        source_status = (
            "Lesson-level source locator recorded; license/alignment review still required"
            if source_recorded
            else "No lesson-level source locator; inspect package provenance and source register"
        )
        recommendation = (
            "Review listed structural/source findings; independently verify accuracy, level, "
            "language, and assessment keys before beta"
            if flags
            else "Complete subject-expert accuracy, language, level, and source review"
        )
        rows.append(
            {
                "lesson_id": lesson["id"],
                "lesson_slug": lesson["slug"],
                "lesson_title": lesson["title"],
                "curriculum_system": lesson["curriculum_system"],
                "level": lesson["curriculum_level"],
                "subject": lesson["subject_name"],
                "topic": lesson["topic_name"],
                "publication_status": lesson["content_status"],
                "published": bool(lesson["published"]),
                "question_count": lesson["question_count"],
                "accuracy_status": "Not independently verified; subject-expert review pending",
                "assessment_status": (
                    "Structural checks recorded in question audit; answer correctness "
                    "not independently verified"
                ),
                "language_status": "Not independently reviewed",
                "source_status": source_status,
                "severity": severity,
                "reviewer_status": (
                    "Reviewer metadata recorded"
                    if lesson["reviewer"] and lesson["reviewed_at"]
                    else "Reviewer metadata absent"
                ),
                "recommended_action": recommendation,
                "remediation_status": "No content changes made during audit",
                "notes": "; ".join(flags)
                or "Automated metadata/structure review only; substantive review remains pending",
            }
        )
    return rows


def export_questions(connection: sqlite3.Connection) -> list[dict[str, object]]:
    records = connection.execute(
        """
        SELECT q.*, l.slug AS lesson_slug, l.title AS lesson_title,
               s.curriculum_system, s.curriculum_level, s.name AS subject_name
        FROM lesson_questions q
        JOIN lessons l ON l.id = q.lesson_id
        JOIN topics t ON t.id = l.topic_id
        JOIN subjects s ON s.id = t.subject_id
        ORDER BY l.slug, q.sort_order, q.id
        """
    ).fetchall()
    duplicates: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for question in records:
        duplicates[normalized_prompt(question["prompt"])].append(question)

    rows = []
    for question in records:
        options = json_list(question["options"])
        prompt_group = duplicates[normalized_prompt(question["prompt"])]
        duplicate_status = (
            f"Exact normalized prompt appears in {len(prompt_group)} lessons: "
            + ", ".join(sorted({item["lesson_slug"] for item in prompt_group}))
            if len(prompt_group) > 1
            else "No exact normalized prompt duplicate found"
        )
        if question["question_type"] == "multiple_choice":
            key_status = (
                "Key matches a listed option structurally; factual correctness not verified"
                if question["correct_answer"].strip().casefold()
                in {option.strip().casefold() for option in options}
                else "Key does not match an option"
            )
        else:
            key_status = "Key present; mathematical/semantic correctness not independently verified"
        explanation_status = (
            "Missing; learner feedback explanation is blank"
            if not (question["explanation"] or "").strip()
            else "Present; logical agreement with the key not independently verified"
        )
        findings = []
        if not (question["explanation"] or "").strip():
            findings.append("missing explanatory feedback")
        if "does not match" in key_status:
            findings.append("answer key not represented in options")
        if len(prompt_group) > 1:
            findings.append("duplicate prompt requires context review")
        rows.append(
            {
                "question_id": question["id"],
                "lesson_id": question["lesson_id"],
                "lesson_slug": question["lesson_slug"],
                "lesson_title": question["lesson_title"],
                "curriculum_system": question["curriculum_system"],
                "level": question["curriculum_level"],
                "subject": question["subject_name"],
                "question_type": question["question_type"],
                "answer_key_validation": key_status,
                "explanation_validation": explanation_status,
                "duplicate_status": duplicate_status,
                "difficulty_level_suitability": "Not independently reviewed",
                "severity": "Medium" if findings else "Not assessed",
                "recommended_action": (
                    "; ".join(findings)
                    + "; verify the key and add useful feedback where appropriate"
                    if findings
                    else "Independently check question accuracy, lesson alignment, and feedback"
                ),
                "remediation_status": "No question changes made during audit",
                "notes": (
                    "; ".join(findings)
                    or (
                        "Structural assessment only; key and distractor correctness "
                        "remain unverified"
                    )
                ),
            }
        )
    return rows


def export_coverage(connection: sqlite3.Connection) -> list[dict[str, object]]:
    records = connection.execute(
        """
        SELECT s.id AS subject_id, s.name AS subject, s.curriculum_system, s.curriculum_level,
               s.curriculum_version, s.source_id AS subject_source_id,
               t.id AS topic_id, t.slug AS topic_slug, t.name AS topic,
               t.source_reference AS topic_source_reference,
               COUNT(DISTINCT l.id) AS lesson_count,
               COUNT(DISTINCT CASE
                   WHEN l.published = 1 AND l.content_status = 'published' THEN l.id END)
                   AS published_count,
               COUNT(DISTINCT CASE WHEN l.published = 0 THEN l.id END) AS draft_count,
               COUNT(DISTINCT q.id) AS question_count
        FROM subjects s
        LEFT JOIN topics t ON t.subject_id = s.id
        LEFT JOIN lessons l ON l.topic_id = t.id
        LEFT JOIN lesson_questions q ON q.lesson_id = l.id
        GROUP BY s.id, t.id
        ORDER BY s.curriculum_system, s.curriculum_level, s.name, t.name
        """
    ).fetchall()
    rows = []
    for record in records:
        topic = record["topic"] or ""
        lessons = record["lesson_count"]
        rows.append(
            {
                "curriculum_system": record["curriculum_system"],
                "level": record["curriculum_level"],
                "subject": record["subject"],
                "curriculum_version": record["curriculum_version"],
                "topic": topic,
                "topic_slug": record["topic_slug"] or "",
                "topic_source_reference": record["topic_source_reference"] or "",
                "expected_scope": "Unknown; no authoritative per-level syllabus audited",
                "coverage_assessment": "Provisional; counts describe database content only",
                "topic_count": 1 if topic else 0,
                "lesson_count": lessons,
                "published_count": record["published_count"],
                "draft_count": record["draft_count"],
                "question_count": record["question_count"],
                "identified_gap": (
                    "No instructional lessons in this topic"
                    if topic and not lessons
                    else "Compare topic and lesson depth against verified curriculum design"
                    if topic
                    else "Subject has no topic structure"
                ),
                "source_and_verification_status": (
                    "Topic source locator recorded; official scope/licensing not independently "
                    "verified"
                    if record["topic_source_reference"]
                    else "No topic source locator; official scope remains unverified"
                ),
                "recommended_priority": (
                    "High: define expected scope and author reviewed material"
                    if not record["published_count"]
                    else "Review against official curriculum design and subject-expert expectations"
                ),
            }
        )
    return rows


def export_sources() -> list[dict[str, object]]:
    with SOURCE_REGISTER.open(encoding="utf-8-sig", newline="") as source_file:
        source_rows = list(csv.DictReader(source_file))
    rows = []
    for source in source_rows:
        title = source.get("Title", "")
        publisher = source.get("Publisher / source body", "")
        license_name, evidence, clearance = source_clearance(title, publisher)
        source_reference = source.get("Source file", "")
        if re.match(r"^[A-Za-z]:[\\/]", source_reference):
            filename = PureWindowsPath(source_reference).name
            source_reference = f"User-supplied local file: {filename}"
        rows.append(
            {
                "source_title": title,
                "curriculum": source.get("Curriculum", ""),
                "level": source.get("Grade/Form", ""),
                "subject": source.get("Subject", ""),
                "canonical_url_or_file": source_reference,
                "author_or_publisher": publisher,
                "access_date": source.get("Access date", ""),
                "relevant_section_or_page": source.get("Relevant section or page", ""),
                "license_name_or_status": license_name,
                "license_evidence": evidence,
                "attribution_and_restrictions": source.get("Validation status", ""),
                "specific_material_used": source.get("Publication status", ""),
                "intended_use": (
                    "Factual reference or documented content provenance; not a reuse grant"
                ),
                "clearance_status": clearance,
                "review_action": (
                    "Obtain written permission or replace affected material before public release"
                    if clearance == "Restricted — permission or conditions required"
                    else "Verify license and provenance before any reuse or external beta"
                    if clearance == "Unverified"
                    else (
                        "Retain the package provenance; independently validate curriculum alignment"
                    )
                ),
            }
        )
    return rows


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    with read_only_database() as connection:
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError(f"Active database integrity check failed: {integrity}")
        lesson_rows = export_lessons(connection)
        question_rows = export_questions(connection)
        coverage_rows = export_coverage(connection)
    source_rows = export_sources()
    write_csv(
        "PHASE_FIVE_CONTENT_AUDIT.csv",
        [
            "lesson_id",
            "lesson_slug",
            "lesson_title",
            "curriculum_system",
            "level",
            "subject",
            "topic",
            "publication_status",
            "published",
            "question_count",
            "accuracy_status",
            "assessment_status",
            "language_status",
            "source_status",
            "severity",
            "reviewer_status",
            "recommended_action",
            "remediation_status",
            "notes",
        ],
        lesson_rows,
    )
    write_csv(
        "PHASE_FIVE_QUESTION_AUDIT.csv",
        [
            "question_id",
            "lesson_id",
            "lesson_slug",
            "lesson_title",
            "curriculum_system",
            "level",
            "subject",
            "question_type",
            "answer_key_validation",
            "explanation_validation",
            "duplicate_status",
            "difficulty_level_suitability",
            "severity",
            "recommended_action",
            "remediation_status",
            "notes",
        ],
        question_rows,
    )
    write_csv(
        "PHASE_FIVE_CURRICULUM_COVERAGE.csv",
        [
            "curriculum_system",
            "level",
            "subject",
            "curriculum_version",
            "topic",
            "topic_slug",
            "topic_source_reference",
            "expected_scope",
            "coverage_assessment",
            "topic_count",
            "lesson_count",
            "published_count",
            "draft_count",
            "question_count",
            "identified_gap",
            "source_and_verification_status",
            "recommended_priority",
        ],
        coverage_rows,
    )
    write_csv(
        "PHASE_FIVE_SOURCE_AND_LICENSING_REGISTER.csv",
        [
            "source_title",
            "curriculum",
            "level",
            "subject",
            "canonical_url_or_file",
            "author_or_publisher",
            "access_date",
            "relevant_section_or_page",
            "license_name_or_status",
            "license_evidence",
            "attribution_and_restrictions",
            "specific_material_used",
            "intended_use",
            "clearance_status",
            "review_action",
        ],
        source_rows,
    )
    print(
        json.dumps(
            {
                "active_database": str(DATABASE),
                "database_integrity": integrity,
                "lesson_rows": len(lesson_rows),
                "question_rows": len(question_rows),
                "coverage_rows": len(coverage_rows),
                "source_rows": len(source_rows),
                "database_open_mode": "read-only",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
