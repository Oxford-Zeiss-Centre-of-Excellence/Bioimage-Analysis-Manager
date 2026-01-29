from __future__ import annotations

import asyncio
import shutil
from pathlib import Path
from textual.widgets import ProgressBar, Static


class SyncMixin:
    """Mixin for dataset sync operations."""

    _syncing: bool

    def _start_sync(self, dataset: dict[str, object]) -> None:
        if self._syncing:
            return

        # Check if locally mounted
        if not bool(dataset.get("locally_mounted", False)):
            self.notify("Dataset must be locally mounted to sync", severity="warning")
            return

        source = str(dataset.get("source", "")).strip()
        local = str(dataset.get("local", "")).strip()

        if not source:
            self.notify("Source path is empty", severity="error")
            return
        if not local:
            self.notify("Local path is empty", severity="error")
            return

        source_path = Path(source).expanduser().resolve()
        local_path = Path(local).expanduser().resolve()

        # Check if source and local are the same
        if source_path == local_path:
            self.notify(
                "Local cache is same as source, sync not needed", severity="information"
            )
            return

        # Check if local cache is a symlink pointing to source
        if local_path.exists() and local_path.is_symlink():
            try:
                link_target = local_path.resolve()
                if link_target == source_path:
                    self.notify(
                        "Local cache is linked to source, sync not needed",
                        severity="information",
                    )
                    return
            except Exception:
                pass

        if not source_path.exists():
            self.notify(f"Source path does not exist: {source}", severity="error")
            return

        self._syncing = True
        self.run_worker(self._run_rsync(source, local), exclusive=True)

    async def _run_rsync(self, source: str, local: str) -> None:
        progress_bar = self.query_one("#sync_progress", ProgressBar)
        sync_pct = self.query_one("#sync_pct", Static)
        progress_bar.add_class("visible")
        sync_pct.add_class("visible")
        progress_bar.update(progress=0)
        sync_pct.update("0%")

        try:
            # Check if rsync is available
            if not shutil.which("rsync"):
                self.notify("rsync not found in PATH", severity="error")
                return

            # Run rsync with progress
            source_path = source.rstrip("/") + "/"
            proc = await asyncio.create_subprocess_exec(
                "rsync",
                "-a",
                "--info=progress2",
                "--no-inc-recursive",
                source_path,
                local,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            while True:
                if proc.stdout:
                    line = await proc.stdout.readline()
                else:
                    break

                if not line:
                    break

                # Check for None just to be safe for type checker, though readline checks above
                if line is None:
                    break

                text = line.decode().strip()
                # Parse rsync progress output: "1,234,567  45%  1.23MB/s  0:01:23"
                if "%" in text:
                    try:
                        parts = text.split()
                        for part in parts:
                            if part.endswith("%"):
                                pct = int(part.rstrip("%"))
                                progress_bar.update(progress=pct)
                                sync_pct.update(f"{pct}%")
                                break
                    except (ValueError, IndexError):
                        pass

            await proc.wait()

            if proc.returncode == 0:
                progress_bar.update(progress=100)
                sync_pct.update("100%")
                self.notify("Sync completed successfully", severity="information")
            else:
                stderr = b""
                if proc.stderr:
                    stderr = await proc.stderr.read()
                self.notify(
                    f"Sync failed: {stderr.decode().strip()}",
                    severity="error",
                    markup=False,
                )
        except Exception as e:
            self.notify(f"Sync error: {e}", severity="error", markup=False)
        finally:
            self._syncing = False
            # Hide progress bar after a short delay
            await asyncio.sleep(1)
            progress_bar.remove_class("visible")
            sync_pct.remove_class("visible")
