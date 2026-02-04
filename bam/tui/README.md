# BAM - Bioimage Analysis Manager (TUI)

A terminal user interface for managing bioimage analysis projects with structured metadata and time tracking.

## Prerequisites

- **Python 3.11+**
- **[uv](https://github.com/astral-sh/uv)** - Fast Python package installer

Install uv if you don't have it:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

### Quick Start (Two Lines)

```bash
git clone https://github.com/Oxford-Zeiss-Centre-of-Excellence/Bioimage-Analysis-Project-Helper.git
cd Bioimage-Analysis-Project-Helper/bam/tui && uv sync && uv run bam
```

### Step-by-Step

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Oxford-Zeiss-Centre-of-Excellence/Bioimage-Analysis-Project-Helper.git
   cd Bioimage-Analysis-Project-Helper/bam/tui
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Run BAM:**
   ```bash
   uv run bam
   ```

## Usage

### Launch the TUI

```bash
uv run bam
```

This opens the interactive terminal interface for managing your bioimage analysis project.

### CLI Commands

#### Validate Manifest

Check if your `manifest.yaml` is valid:

```bash
uv run bam validate
```

Options:
- `--manifest PATH` - Validate a specific manifest file
- `--quiet` - Suppress output (useful for CI/CD)

Exit codes:
- `0` - Validation passed
- `1` - Validation failed

### Project Structure

When you create a new project with BAM, it generates:

```
my-project/
├── manifest.yaml          # Project metadata registry
├── log/
│   └── tasks.yaml        # Time tracking worklog
├── ideas/                # Research ideas (markdown files)
├── doc/
│   └── method.md         # Methods documentation
└── data/                 # (optional) Dataset references
```

## Features

- **Structured Metadata Management** - Edit project metadata through forms instead of raw YAML
- **Task-Based Time Tracking** - Punch-in/punch-out workflow with hierarchical task organization
- **Publication Figure Tracking** - Infinite-tier tree for managing figure elements and sources
- **Artifact Registry** - Track outputs (figures, tables, datasets, models, scripts)
- **Ideas Management** - Organize research ideas as markdown files
- **Manifest Validation** - Automatic schema validation with backup creation

## Manifest Validation

BAM automatically validates your `manifest.yaml` at four critical points:

1. **TUI Startup** - Fails fast if manifest is corrupted
2. **Before Save** - Prevents writing invalid data
3. **On Reload** - Catches external edits
4. **CLI Validate** - Manual/CI checking

### Backup Files

When validation **fails** during save operations, BAM automatically creates a timestamped backup of your last known good manifest:

```
manifest.yaml.2026-02-03T14-30-15.bak.yaml
```

**Important:** Backups are only created when validation fails, not on every successful save. This preserves your working manifest when you attempt to save invalid data.

To restore from a backup:

```bash
cp manifest.yaml.<timestamp>.bak.yaml manifest.yaml
```

## Troubleshooting

### Validation Errors

If you see validation errors:

1. **Check the error message** - BAM shows which fields are invalid
2. **Review recent changes** - Did you manually edit `manifest.yaml`?
3. **Restore from backup** - Look for `.bak.yaml` files in your project directory
4. **Use CLI validate** - Run `uv run bam validate` to see detailed validation output

### Permission Errors

If BAM can't create backups:

```bash
# Check directory permissions
ls -la .

# Ensure you have write access
chmod u+w .
```

### Disk Space Issues

BAM creates backup files only when validation fails. Over time, you may accumulate old backups. To clean them up:

```bash
# Clean old backups (keep recent ones)
find . -name "*.bak.yaml" -mtime +30 -delete
```

## Development

### Running Tests

```bash
uv run pytest
```

### Code Structure

- `ba_tui/cli.py` - Command-line interface entry point
- `ba_tui/tui.py` - Main TUI application
- `ba_tui/models.py` - Pydantic models for manifest schema
- `ba_tui/handlers/` - Business logic for persistence, worklog, etc.
- `ba_tui/screens/` - Modal dialogs and forms
- `ba_tui/tabs/` - Tab content widgets