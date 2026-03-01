#!/usr/bin/env python
"""
Generate changelog from git commits following conventional commits format.
Usage: python scripts/generate_changelog.py [version]
"""
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path


def get_git_log(version):
    """Get git log since last version tag."""
    try:
        # Find previous version tag
        tags = subprocess.check_output(
            ["git", "tag", "--list", "--sort=-v:refname"],
            text=True
        ).strip().split('\n')

        previous_tag = None
        for tag in tags:
            if tag and tag != f"v{version}":
                previous_tag = tag
                break

        # Get commits since previous tag
        if previous_tag:
            commit_range = f"{previous_tag}..HEAD"
        else:
            commit_range = "HEAD"

        log = subprocess.check_output(
            ["git", "log", commit_range, "--pretty=format:%H|%s|%b"],
            text=True
        ).strip()

        return log
    except subprocess.CalledProcessError:
        return ""


def parse_commits(log):
    """Parse commits into categories."""
    commits = {
        "features": [],
        "fixes": [],
        "breaking": [],
        "docs": [],
        "other": []
    }

    for line in log.split('\n'):
        if not line.strip():
            continue

        parts = line.split('|')
        if len(parts) < 2:
            continue

        sha = parts[0][:7]
        subject = parts[1]
        body = parts[2] if len(parts) > 2 else ""

        # Check for breaking changes
        if "BREAKING CHANGE" in subject or "BREAKING CHANGE" in body:
            commits["breaking"].append({
                "sha": sha,
                "subject": subject
            })
        # Parse conventional commit type
        elif subject.startswith("feat:"):
            commits["features"].append({
                "sha": sha,
                "subject": subject.replace("feat: ", "")
            })
        elif subject.startswith("fix:"):
            commits["fixes"].append({
                "sha": sha,
                "subject": subject.replace("fix: ", "")
            })
        elif subject.startswith("docs:"):
            commits["docs"].append({
                "sha": sha,
                "subject": subject.replace("docs: ", "")
            })
        else:
            commits["other"].append({
                "sha": sha,
                "subject": subject
            })

    return commits


def generate_changelog(version, commits):
    """Generate changelog markdown."""
    changelog = f"""# Changelog

## [v{version}] - {datetime.now().strftime('%Y-%m-%d')}

"""

    if commits["breaking"]:
        changelog += "### ⚠️ Breaking Changes\n\n"
        for commit in commits["breaking"]:
            changelog += f"- {commit['subject']} ([{commit['sha']}](https://github.com/${{repo}}/commit/{commit['sha']}))\n"
        changelog += "\n"

    if commits["features"]:
        changelog += "### ✨ Features\n\n"
        for commit in commits["features"]:
            changelog += f"- {commit['subject']} ([{commit['sha']}](https://github.com/${{repo}}/commit/{commit['sha']}))\n"
        changelog += "\n"

    if commits["fixes"]:
        changelog += "### 🐛 Bug Fixes\n\n"
        for commit in commits["fixes"]:
            changelog += f"- {commit['subject']} ([{commit['sha']}](https://github.com/${{repo}}/commit/{commit['sha']}))\n"
        changelog += "\n"

    if commits["docs"]:
        changelog += "### 📚 Documentation\n\n"
        for commit in commits["docs"]:
            changelog += f"- {commit['subject']} ([{commit['sha']}](https://github.com/${{repo}}/commit/{commit['sha']}))\n"
        changelog += "\n"

    if commits["other"]:
        changelog += "### 🔧 Other Changes\n\n"
        for commit in commits["other"]:
            changelog += f"- {commit['subject']} ([{commit['sha']}](https://github.com/${{repo}}/commit/{commit['sha']}))\n"
        changelog += "\n"

    return changelog


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_changelog.py <version>")
        sys.exit(1)

    version = sys.argv[1]

    # Get git log
    log = get_git_log(version)
    if not log:
        print(f"No commits found for version {version}")
        sys.exit(1)

    # Parse commits
    commits = parse_commits(log)

    # Generate changelog entry
    changelog_entry = generate_changelog(version, commits)

    # Update CHANGELOG.md
    changelog_path = Path("CHANGELOG.md")
    existing_content = ""
    if changelog_path.exists():
        existing_content = changelog_path.read_text()

    # Prepend new changelog entry
    new_content = changelog_entry + "\n" + existing_content
    changelog_path.write_text(new_content)

    print(f"✅ Updated CHANGELOG.md for version {version}")
    print(f"   Features: {len(commits['features'])}")
    print(f"   Fixes: {len(commits['fixes'])}")
    print(f"   Breaking changes: {len(commits['breaking'])}")


if __name__ == "__main__":
    main()
