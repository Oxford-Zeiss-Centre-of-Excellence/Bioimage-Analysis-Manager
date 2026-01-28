---
name: artifact
description: Register and update artifacts in manifest.yaml. Use when the user asks to track deliverables.
---

# BA Artifact

## Instructions

1. Determine the project root. If the user provides a path, use it; otherwise use the current directory.
2. If the user provided a file path to register, run: `bam artifact --path "<project_root>" --register "<artifact_path>"` (include `--type` or `--status` if provided).
3. If no path was provided, run: `bam artifact --path "<project_root>"` to open the TUI.
4. Read the JSON output from stdout.
5. If `status` is `ok`, report the manifest path and/or updated artifacts. If `status` is `cancelled` or `error`, report that clearly and stop.

## Examples

- User: "Register artifact/figure1.png" → Run `bam artifact --path . --register "artifact/figure1.png"`.
- User: "/ba:artifact" → Run `bam artifact --path .` and let the user update.
