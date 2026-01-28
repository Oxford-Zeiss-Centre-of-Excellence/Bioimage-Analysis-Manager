---
name: init
description: Initialize a BA project (manifest + folders + data symlink). Use when the user asks to start a BA project or run /ba:init.
---

# BA Init

## Instructions

1. Determine the project root. If the user provides a path, use it; otherwise use the current directory.
2. Run: `bam init --path "<project_root>"`
3. Read the JSON output from stdout.
4. If `status` is `ok`, report the manifest path and any `data_link_warning`. If `status` is `cancelled` or `error`, report that clearly and stop.

## Examples

- User: "Start a new BA project in this folder" → Run `bam init --path .` and report results.
- User: "/ba:init --path /data/project" → Run `bam init --path /data/project` and report results.
