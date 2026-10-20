"""Turn content/ into search chunks, one per unit of meaning.

Each experience bullet is its own chunk, prefixed with company, title and dates, so a chunk
still makes sense when it is retrieved on its own. Profile sections, skill groups and
project paragraphs are one chunk each.
"""

import uuid
from dataclasses import dataclass, field

from api import content
from api.content import date_range, plain

ID_NAMESPACE = uuid.UUID("6f1d4c2e-8a57-4b0e-9c1d-2b7e5f3a9d10")


@dataclass
class Chunk:
    text: str
    file: str
    section: str  # profile, about, experience, skills or project
    label: str  # company for experience, otherwise a title
    dates: str = ""
    index: int = 0  # position within its file, used for the stable ID
    extra: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        """Same file and position always give the same ID, so re-ingesting is repeatable."""
        return str(uuid.uuid5(ID_NAMESPACE, f"{self.file}#{self.index}"))

    @property
    def payload(self) -> dict:
        return {
            "text": self.text,
            "file": self.file,
            "section": self.section,
            "label": self.label,
            "dates": self.dates,
            **self.extra,
        }


def profile_chunks() -> list[Chunk]:
    profile = content.load_profile()
    file = profile["file"]
    texts = [
        f"Profile: {profile['name']}, {profile['headline']}. Based in {profile['location']}. "
        f"Languages: {', '.join(profile['languages'])}.",
        f"Profile summary: {profile['summary']}",
        f"Contact details for {profile['name']}: email {profile['email']}, "
        f"LinkedIn {profile['linkedin']}, GitHub {profile['github']}.",
    ]
    if profile.get("relocation") or profile.get("available"):
        texts.append(
            f"Availability for new roles: {profile.get('relocation', '')}. "
            f"Available to start from {profile['available']}."
        )
    for section in profile["sections"]:
        items = [plain(item) for item in section["bullets"] + section["paragraphs"]]
        texts.append(f"{section['heading']}: " + " ".join(items))
    return [
        Chunk(text=text, file=file, section="profile", label="Profile", index=i)
        for i, text in enumerate(texts)
    ]


def experience_chunks() -> list[Chunk]:
    chunks = []
    for role in content.load_experience():
        dates = date_range(role["start"], role["end"], separator=" to ")
        prefix = f"{role['company']}, {role['title']}, {dates}"
        current = " This is Blessing's current role." if role["end"] == "present" else ""
        texts = [
            f"{prefix}: worked as {role['title']} at {role['company']} "
            f"(location: {role['location']}).{current} Tools used: {', '.join(role['tags'])}.",
            *(f"{prefix}: {paragraph}" for paragraph in role["intro"]),
            *(f"{prefix}: {bullet}" for bullet in role["bullets"]),
        ]
        if role.get("case_study"):
            steps = " ".join(f"{item['label']}: {item['text']}" for item in role["case_study"])
            texts.append(f"{prefix}: case study. {steps}")
        chunks += [
            Chunk(
                text=text,
                file=role["file"],
                section="experience",
                label=role["company"],
                dates=dates,
                index=i,
                extra={"company": role["company"]},
            )
            for i, text in enumerate(texts)
        ]
    return chunks


def skills_chunks() -> list[Chunk]:
    return [
        Chunk(
            text=f"Skills, {group['label']}: {', '.join(group['tools'])}",
            file="content/skills.md",
            section="skills",
            label=f"Skills: {group['label']}",
            index=i,
        )
        for i, group in enumerate(content.load_skills())
    ]


def project_chunks() -> list[Chunk]:
    chunks = []
    for project in content.load_projects():
        dates = date_range(project["start"], project["end"], separator=" to ")
        prefix = f"{project['title']} ({project['type']}, {dates})"
        facts = [f"tools used: {', '.join(project['tags'])}."]
        if project.get("status_label"):
            facts.append(f"Status: {project['status_label'].lower()}.")
        if project.get("result"):
            facts.append(f"Result: {project['result']}.")
        if project.get("url"):
            facts.append(f"Live at {project['url']}.")
        if project.get("github"):
            facts.append(f"Code: {project['github']}.")
        texts = [
            f"{prefix}: " + " ".join(facts),
            *(f"{prefix}: {paragraph}" for paragraph in project["paragraphs"]),
            *(f"{prefix}: {bullet}" for bullet in project["bullets"]),
        ]
        chunks += [
            Chunk(
                text=text,
                file=project["file"],
                section="project",
                label=project["title"],
                dates=dates,
                index=i,
                extra={"title": project["title"]},
            )
            for i, text in enumerate(texts)
        ]
    return chunks


def about_chunks() -> list[Chunk]:
    """One chunk per paragraph of the About page, prefixed with its section heading."""
    about = content.load_page("about")
    chunks = []
    for section in about["sections"]:
        heading = section["heading"] or about.get("title", "About")
        for paragraph in section["paragraphs"]:
            chunks.append(
                Chunk(
                    # The heading, not "About Blessing": a name in every chunk made them all
                    # match any question that mentions Blessing.
                    text=f"{heading}: {paragraph}",
                    file=about["file"],
                    section="about",
                    label=f"About: {heading}",
                    index=len(chunks),
                )
            )
    return chunks


def build_chunks() -> list[Chunk]:
    return (
        profile_chunks() + about_chunks() + experience_chunks() + skills_chunks() + project_chunks()
    )
