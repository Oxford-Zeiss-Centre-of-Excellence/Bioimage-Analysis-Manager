from __future__ import annotations

from __future__ import annotations

from datetime import date
from pathlib import Path

from .models import Artifact, Manifest


def templates_root() -> Path:
    return Path(__file__).resolve().parents[2] / "templates"


def ensure_directories(project_root: Path) -> None:
    for name in ("doc", "artifact", "log", "ideas"):
        (project_root / name).mkdir(parents=True, exist_ok=True)


def ensure_worklog(project_root: Path) -> Path:
    log_dir = project_root / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = log_dir / "worklog.yaml"
    if not yaml_path.exists():
        yaml_path.write_text("entries: []\n")

    md_path = log_dir / "worklog.md"
    if not md_path.exists():
        template_path = templates_root() / "worklog.md"
        if template_path.exists():
            md_path.write_text(template_path.read_text())
        else:
            md_path.write_text("# Worklog\n\n")
    return md_path


def ensure_log_types_template(project_root: Path) -> Path:
    templates_dir = project_root / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    target = templates_dir / "log-types.yaml"
    if not target.exists():
        source = templates_root() / "log-types.yaml"
        if source.exists():
            target.write_text(source.read_text())
    return target


def slugify(text: str) -> str:
    slug = []
    for char in text.strip().lower():
        if char.isalnum():
            slug.append(char)
        elif slug and slug[-1] != "-":
            slug.append("-")
    return "".join(slug).strip("-") or "idea"


def render_template(name: str, context: dict[str, str]) -> str:
    template_path = templates_root() / name
    if not template_path.exists():
        return ""
    return template_path.read_text().format(**context)


def create_idea_file(project_root: Path, title: str, priority: str, problem: str, approach: str) -> Path:
    ideas_dir = project_root / "ideas"
    ideas_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    idea_path = ideas_dir / f"{slug}.md"
    today = date.today().isoformat()
    content = render_template(
        "idea.md",
        {
            "title": title.strip() or "Untitled Idea",
            "priority": priority.strip() or "medium",
            "created": today,
            "updated": today,
            "problem": problem.strip() or "Describe the problem.",
            "approach": approach.strip() or "Outline the proposed approach.",
        },
    )
    if not content:
        content = f"# {title}\n"
    idea_path.write_text(content)
    return idea_path


def register_artifact(
    manifest: Manifest,
    *,
    path: str,
    artifact_type: str,
    status: str,
) -> Manifest:
    artifact = Artifact(
        path=path,
        type=artifact_type or "unknown",
        status=status or "draft",
        created=date.today(),
    )
    manifest.artifacts.append(artifact)
    return manifest


def ensure_data_symlink(project_root: Path, target: Path) -> str | None:
    link_path = project_root / "data"
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_symlink() and link_path.resolve() == target.resolve():
            return None
        return "data link already exists and was left unchanged"
    try:
        link_path.symlink_to(target)
    except OSError as exc:
        return f"failed to create data symlink: {exc}"
    return None
