#!/usr/bin/env python3
"""
Generate components overview README for workflows repository.
Scans all workflow files and generates a comprehensive overview.
"""

#!/usr/bin/env python3
"""
Generate components overview README for workflows repository.
Scans all workflow files and generates a comprehensive overview.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    import yaml
except ImportError:
    print("Warning: PyYAML not installed. Install with: pip install pyyaml")
    yaml = None

REPO_ROOT = Path(__file__).parent.parent.parent


def load_workflow_manifest(workflow_file: Path) -> Optional[Dict]:
    """Load and parse workflow YAML file."""
    if not workflow_file.exists():
        return None

    if yaml is None:
        # Fallback: parse basic info without YAML library
        try:
            with open(workflow_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Extract basic info using regex
                import re
                name_match = re.search(r'name:\s*["\']?([^"\'\n]+)', content)
                name = name_match.group(1).strip() if name_match else workflow_file.stem
                return {
                    "name": name,
                    "file": workflow_file.name,
                    "path": str(workflow_file.relative_to(REPO_ROOT)),
                    "description": name,
                    "trigger": "Unknown",
                    "steps_count": 0,
                }
        except Exception as e:
            print(f"Warning: Failed to load workflow from {workflow_file}: {e}")
            return None

    try:
        with open(workflow_file, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if not content:
                return None

            # Extract workflow metadata
            workflow_info = {
                "name": content.get("name", workflow_file.stem),
                "file": workflow_file.name,
                "path": str(workflow_file.relative_to(REPO_ROOT)),
                "description": content.get("description") or content.get("name", ""),
                "trigger": None,
                "steps_count": 0,
            }

            # Extract trigger information
            if "trigger" in content:
                trigger = content["trigger"]
                if isinstance(trigger, dict):
                    if "event" in trigger:
                        workflow_info["trigger"] = f"Event: {trigger['event']}"
                    elif "schedule" in trigger:
                        workflow_info["trigger"] = f"Schedule: {trigger['schedule']}"
                    else:
                        workflow_info["trigger"] = "Custom trigger"
                else:
                    workflow_info["trigger"] = str(trigger)

            # Count steps
            if "steps" in content:
                workflow_info["steps_count"] = len(content["steps"])

            return workflow_info
    except (yaml.YAMLError, IOError) as e:
        print(f"Warning: Failed to load workflow from {workflow_file}: {e}")
        return None


def load_repo_manifest() -> Optional[Dict]:
    """Load repository manifest.json if it exists."""
    manifest_path = REPO_ROOT / "manifest.json"
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def get_workflow_files() -> List[Path]:
    """Get all workflow YAML files."""
    workflows = []
    for item in REPO_ROOT.rglob("*.yaml"):
        if item.name.startswith("."):
            continue
        # Skip workflow files in .github directory
        if ".github" in str(item):
            continue
        workflows.append(item)

    for item in REPO_ROOT.rglob("*.yml"):
        if item.name.startswith("."):
            continue
        if ".github" in str(item):
            continue
        if item not in workflows:  # Avoid duplicates
            workflows.append(item)

    return sorted(workflows, key=lambda x: x.name.lower())


def generate_overview() -> str:
    """Generate the components overview README."""
    workflow_files = get_workflow_files()
    workflows = []

    for workflow_file in workflow_files:
        workflow_info = load_workflow_manifest(workflow_file)
        if workflow_info:
            workflows.append(workflow_info)

    # Sort by name
    workflows.sort(key=lambda x: x["name"].lower())

    repo_manifest = load_repo_manifest()
    repo_name = repo_manifest.get("name", "faneX-ID Workflows") if repo_manifest else "faneX-ID Workflows"
    repo_description = (
        repo_manifest.get("description", "Official faneX-ID Workflow Store")
        if repo_manifest
        else "Official faneX-ID Workflow Store"
    )

    # Generate README
    lines = [
        f"# {repo_name}",
        "",
        repo_description,
        "",
        "---",
        "",
        "## 📋 Available Workflows",
        "",
        f"**Total: {len(workflows)} workflows**",
        "",
        "| Name | Trigger | Steps | File |",
        "|------|---------|-------|------|",
    ]

    for workflow in workflows:
        name = workflow["name"]
        trigger = workflow.get("trigger", "-")
        steps = str(workflow.get("steps_count", 0))
        file_path = workflow["path"]

        # Escape pipe characters in markdown table
        name = name.replace("|", "\\|")
        trigger = trigger.replace("|", "\\|")

        lines.append(f"| {name} | {trigger} | {steps} | [`{workflow['file']}`]({file_path}) |")

    lines.extend([
        "",
        "## 📂 Repository Structure",
        "",
        "*   Each workflow is a YAML file containing:",
        "    *   `trigger` — When the workflow should run",
        "    *   `steps` — Actions to execute",
        "    *   `conditions` — Optional conditional logic",
        "",
        "## 🚀 Getting Started",
        "",
        "To use these workflows, import them into your faneX-ID instance via the Workflow Editor.",
        "",
        "## 🤝 Contributing",
        "",
        "We welcome contributions! Please refer to the [📚 Workflow Development Guide](https://github.com/faneX-ID/core/blob/main/docs/WORKFLOW_EXAMPLES.md) before submitting Pull Requests.",
        "",
        "## 📝 License",
        "",
        "This project is licensed under the GNU Affero General Public License v3.0 (AGPL-3.0) - see the [LICENSE](LICENSE) file for details.",
        "",
        f"---",
        f"",
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}*",
    ])

    return "\n".join(lines)


def main():
    """Main function."""
    overview = generate_overview()
    readme_path = REPO_ROOT / "README.md"

    # Write README
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(overview)

    print(f"✅ Generated workflows overview with {len(get_workflow_files())} workflows")
    print(f"📝 Updated {readme_path}")


if __name__ == "__main__":
    main()

