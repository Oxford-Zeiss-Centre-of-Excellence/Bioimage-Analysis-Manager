# Bioimage Analysis Manager (BAM)

A powerful manager for bioimage analysis workflows, combining LLM agent plugin with a standalone Terminal User Interface (TUI) for seamless project management, work logging, and artifact tracking.

## Features

- **Project scaffolding** — standardized structure for bioimage analysis
- **Manifest-driven metadata** — data sources, tools, billing, timelines
- **Lab notebook logging** — timestamped one-liners for work tracking
- **Idea management** — prioritized proposals with status tracking
- **Artifact lifecycle** — from draft to delivered
- **Centralized hub** — cross-project visibility and analytics

## Requirements

- [uv](https://docs.astral.sh/uv/) — Python package manager

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Installation

### 1. Clone the repository

Keep a local copy for version-tracked updates:

```bash
cd <repo-dir>
git clone git@github.com:Oxford-Zeiss-Centre-of-Excellence/Bioimage-Analysis-Manager.git

### 2. Install CLI globally

```bash
cd Bioimage-Analysis-Manager
uv tool install ./bam/tui
```

Verify:

```bash
bam --help
```

### 3. Install Claude Code plugin

Symlink the plugin for Claude Code discovery:

```bash
mkdir -p ~/.claude/plugins
ln -s <repo-dir>/Bioimage-Analysis-Manager/bam ~/.claude/plugins/bam
```

Hub directory (`~/.ba-hub/`) is created automatically on first use.

### Updating

```bash
cd <repo-dir>/Bioimage-Analysis-Manager
git pull
uv tool install --reinstall ./bam/tui
```

### Development install

For local development with live changes:

```bash
cd <repo-dir>/Bioimage-Analysis-Manager/bam/tui
uv tool install -e .
```

## Configuration

BAM supports customizable configuration for dropdown options, lists, and preferences throughout the application.

### Configuration Locations

Configuration is loaded in order of priority (highest to lowest):

1. **Project-level**: `<project>/.bam/config.yaml` (project-specific overrides)
2. **System-wide**: `~/.bam/config.yaml` (user-specific preferences)
3. **Defaults**: Built-in defaults from `bam/tui/ba_tui/config_defaults.yaml`

### Configuration Template

The complete configuration template with all available options can be found at:
```
bam/tui/ba_tui/config_defaults.yaml
```

### Customizing Configuration

1. **Copy the template**:
   ```bash
   # For system-wide config
   mkdir -p ~/.bam
   cp bam/tui/ba_tui/config_defaults.yaml ~/.bam/config.yaml
   
   # For project-level config
   mkdir -p <project>/.bam
   cp bam/tui/ba_tui/config_defaults.yaml <project>/.bam/config.yaml
   ```

2. **Edit the config file** to customize values:
   ```yaml
   # Example: Customize cluster options
   clusters:
     - BMRC
     - ARC
     - CCB
     - My Custom Cluster
     - Other
   
   # Example: Add custom software tools
   software_tools:
     - Fiji/ImageJ
     - napari
     - My Custom Tool
   ```

### Configurable Options

The following options can be customized:

- **Hardware/Clusters**: `clusters`, `compute_locations`
- **Data**: `endpoints`, `data_formats`, `data_size_units`
- **Status Options**: `project_status`, `milestone_status`, `publication_status`, `archive_status`, etc.
- **Imaging**: `imaging_modalities`, `image_quality`
- **Tools**: `programming_languages`, `software_tools`, `environment_types`, `cluster_packages`
- **Tasks**: `task_categories`, `task_subcategories`, `task_difficulty`, `run_status`
- **Artifacts**: `artifact_types`, `artifact_status`, `figure_element_sources`
- **Collaborators**: `collaborator_roles`

See `config_defaults.yaml` for the complete list and format of each option.

## Plugin Structure

```
bam/                         # Plugin root (creates bam: namespace)
├── skills/
│   ├── init/
│   │   └── SKILL.md        # → /bam:init
│   └── log/
│       └── SKILL.md        # → /bam:log
├── templates/              # Shared templates
└── tui/                    # Python TUI application
    ├── pyproject.toml
    └── ba_tui/
```

## Usage

### Slash Commands (Claude Code)

| Command | Description |
|---------|-------------|
| `/bam:init` | Initialize project with TUI manifest editor |
| `/bam:init --path /path` | Initialize at specific path |
| `/bam:log` | Add timestamped work log entry (TUI) |
| `/bam:log "message"` | Add entry directly (skips TUI) |
| `/bam:idea` | Create idea file from template |
| `/bam:artifact` | Register or update artifacts |
| `/bam:hub register` | Register project with hub |
| `/bam:hub list` | List all registered projects |
| `/bam:hub report` | Generate work report |

### Natural Language (Claude auto-triggers)

Claude Code automatically invokes skills when your prompt matches:

| Prompt example | Triggers |
|----------------|----------|
| "Start a new BA project here" | `/bam:init` |
| "Initialize bioimage analysis project" | `/bam:init` |
| "Log that I finished segmentation" | `/bam:log` |
| "Add to my worklog: tested new threshold" | `/bam:log` |

### CLI (runs anywhere after global install)

```bash
# Open main menu (choose init or log)
bam

# Initialize project
bam init
bam init --path /path/to/project

# Add log entry
bam log
bam log --message "Completed segmentation analysis"

# From Claude Code (! prefix runs bash)
! bam
! bam log --message "Done"
```

### JSON Output

All commands output JSON for easy parsing:

```json
{
  "status": "ok",
  "manifest_path": "/path/to/project/manifest.yaml",
  "data_link_warning": null
}
```

| `status` | Meaning |
|----------|---------|
| `ok` | Success |
| `cancelled` | User cancelled TUI |
| `error` | Error occurred (check `message` field) |

## Configuration

### Data Source Endpoints

Customize the endpoint dropdown options by creating `~/.config/bam/endpoints.yaml`:

```yaml
endpoints:
  - Local
  - I Drive
  - MSD CEPH
  - RFS
  - HDD1
  - My Custom Drive
```

Default endpoints if no config file exists: `Local`, `I Drive`, `MSD CEPH`, `RFS`, `HDD1`

The "Other" option is always available for custom text input.

## Generated Project Structure

After `bam init`:

```
my-project/
├── manifest.yaml       # Project metadata
├── data -> /local/path # Symlink to data cache
├── doc/
│   └── method.md
├── artifact/
│   └── results.md
├── log/
│   └── worklog.md
├── ideas/
└── README.md
```

## Development

```bash
uv tool install --editable bam/tui
bam --help
```
