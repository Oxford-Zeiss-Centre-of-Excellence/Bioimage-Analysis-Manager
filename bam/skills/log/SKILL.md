---
name: log
description: Append a BA worklog entry via TUI or inline message. Use when the user asks to log work or run /ba:log.
---

# BA Log

## Instructions

1. Determine the project root. If the user provides a path, use it; otherwise use the current directory.
2. If the user provided an inline message, run: `bam log --path "<project_root>" --message "<message>"`
3. If the user wants to start a task quickly, run: `bam log --path "<project_root>" -n "<task>"`
4. If the user wants to check out or pause, run: `bam log --path "<project_root>" -o` or `bam log --path "<project_root>" -p`
5. If no inline message or quick action was provided, run: `bam log --path "<project_root>"` to open the TUI.
4. Read the JSON output from stdout.
5. If `status` is `ok`, report the added entry and the `worklog_path`. If `status` is `cancelled` or `error`, report that clearly and stop.

## Examples

- User: "Log that I ran segmentation" → Run `bam log --path . --message "Ran segmentation"`.
- User: "/ba:log" → Run `bam log --path .` and let the user manage tasks in the TUI.
