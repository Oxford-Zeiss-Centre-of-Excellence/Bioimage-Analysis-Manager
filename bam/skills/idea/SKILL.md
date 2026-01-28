---
name: idea
description: Create a BA idea entry via TUI. Use when the user asks to create or capture a new idea.
---

# BA Idea

## Instructions

1. Determine the project root. If the user provides a path, use it; otherwise use the current directory.
2. If the user provided a title, run: `bam idea --path "<project_root>" --title "<title>"`
3. If no title was provided, run: `bam idea --path "<project_root>"` to open the TUI.
4. Read the JSON output from stdout.
5. If `status` is `ok`, report the created `idea_path`. If `status` is `cancelled` or `error`, report that clearly and stop.

## Examples

- User: "Capture an idea about GPU acceleration" → Run `bam idea --path . --title "GPU acceleration"`.
- User: "/ba:idea" → Run `bam idea --path .` and let the user fill the form.
