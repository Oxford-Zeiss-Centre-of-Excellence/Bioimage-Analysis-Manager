from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from textual.widgets import Input, Markdown, OptionList
from textual.widgets.option_list import Option

if TYPE_CHECKING:
    from ..tui import BAApp


class MethodPreviewMixin:
    """Mixin for method preview and path suggestions."""

    _active_method_input: Optional[str]
    _method_path: str
    _method_path_suggestions: Optional[OptionList]
    _method_path_suggestions_visible: bool
    _method_preview_path: str
    _method_preview_mtime: float | None
    _method_template_used: str
    _project_root: Path

    def _create_method_template(self: "BAApp") -> None:
        try:
            path_input = self.query_one("#method_path", Input)
            method_path = path_input.value.strip() or str(
                self._project_root / "method.md"
            )
            content = (
                "# Methods\n\n"
                "## Overview\n\n"
                "Describe the analysis workflow.\n\n"
                "## Data\n\n"
                "Describe input data and preprocessing.\n\n"
                "## Analysis\n\n"
                "Describe key steps, software, and parameters.\n"
            )
            path = Path(method_path).expanduser().resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            created = False
            if not path.exists():
                path.write_text(content)
                created = True
            path_input.value = str(path)
            self._method_path = str(path)
            self._method_template_used = "default"
            self._load_method_preview()
            if created:
                self.notify("Method template created", severity="information")
            else:
                self.notify("Method template already exists", severity="warning")
        except Exception as exc:
            self.notify(
                f"Template creation failed: {exc}", severity="error", markup=False
            )

    def _load_method_preview(self: "BAApp") -> None:
        try:
            path = self.query_one("#method_path", Input).value.strip()
            if not path:
                return
            method_path = Path(path).expanduser()
            text = method_path.read_text()
            self.query_one("#method_preview", Markdown).update(text)
            self._method_preview_path = str(method_path)
            try:
                self._method_preview_mtime = method_path.stat().st_mtime
            except Exception:
                self._method_preview_mtime = None
        except Exception:
            pass

    def _load_method_preview_if_exists(self: "BAApp", path: str) -> None:
        try:
            method_path = Path(path).expanduser()
            if method_path.is_file():
                text = method_path.read_text()
                self.query_one("#method_preview", Markdown).update(text)
                self._method_preview_path = str(method_path)
                try:
                    self._method_preview_mtime = method_path.stat().st_mtime
                except Exception:
                    self._method_preview_mtime = None
        except Exception:
            pass

    def _poll_method_preview(self: "BAApp") -> None:
        if not self._method_preview_path:
            return
        try:
            method_path = Path(self._method_preview_path)
            if not method_path.exists():
                return
            mtime = method_path.stat().st_mtime
            if self._method_preview_mtime is None or mtime > self._method_preview_mtime:
                self._method_preview_mtime = mtime
                text = method_path.read_text()
                self.query_one("#method_preview", Markdown).update(text)
        except Exception:
            pass

    def _maybe_sync_method_path(self: "BAApp") -> None:
        try:
            current = self.query_one("#method_path", Input).value.strip()
            if current and current != self._method_path:
                self._method_path = current
        except Exception:
            pass

    def _update_method_path_suggestions(
        self: "BAApp", input_id: str, current_value: str
    ) -> None:
        """Update method path suggestions dropdown."""
        try:
            suggestions = self._method_path_suggestions or self.query_one(
                "#method_path_suggestions", OptionList
            )
            suggestions.clear_options()

            if not current_value:
                self._hide_method_path_suggestions()
                return

            path = Path(current_value).expanduser()
            if path.is_dir():
                search_dir = path
                prefix = ""
            else:
                search_dir = path.parent
                prefix = path.name.lower()

            if not search_dir.exists():
                self._hide_method_path_suggestions()
                return

            entries = []
            for entry in sorted(search_dir.iterdir()):
                name = entry.name
                if prefix and not name.lower().startswith(prefix):
                    continue
                if entry.is_dir():
                    entries.append((str(entry), f"📁 {name}/"))
                else:
                    entries.append((str(entry), f"📄 {name}"))
                if len(entries) >= 20:
                    break

            if entries:
                for entry_path, display_name in entries:
                    suggestions.add_option(Option(display_name, id=entry_path))
                suggestions.add_class("visible")
                self._method_path_suggestions_visible = True
                self._active_method_input = input_id
            else:
                self._hide_method_path_suggestions()
        except Exception:
            self._hide_method_path_suggestions()

    def _hide_method_path_suggestions(self: "BAApp") -> None:
        """Hide the method path suggestions dropdown."""
        try:
            suggestions = self._method_path_suggestions or self.query_one(
                "#method_path_suggestions", OptionList
            )
            suggestions.remove_class("visible")
            suggestions.clear_options()
            self._active_method_input = None
            self._method_path_suggestions_visible = False
        except Exception:
            pass
