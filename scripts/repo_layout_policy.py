"""Shared repository layout policy for docs and audit scripts."""

ROOT_ALLOWED_FILES = {
    ".clauderules",
    ".commitlintrc.json",
    ".dockerignore",
    ".env",
    ".env.example",
    ".env.local",
    ".gitattributes",
    ".gitignore",
    ".mcp.core.json",
    ".mcp.json",
    ".mcp.optional.json",
    ".n8nconfig.json",
    ".ngrok.yml",
    ".pre-commit-config.yaml",
    ".semver.yaml",
    ".vercelignore",
    "Dockerfile",
    "Dockerfile.prod",
    "Makefile",
    "AGENTS.md",
    "CODEX.md",
    "DEPLOYMENT_EXECUTION_SCRIPT.sh",
    "GEMINI.md",
    "Procfile",
    "README.md",
    "STATUS.md",
    "CLAUDE.md",
    "access_whitelist.json",
    "app.json",
    "continuous_improvement.sh",
    "deploy-verify.sh",
    "docker-compose.monitoring.yml",
    "docker-compose.production.yml",
    "docker-compose.yml",
    "open_all_pages.bat",
    "orchestrator.py",
    "platform.db",
    "pyproject.toml",
    "pytest.ini",
    "railway.json",
    "requirements-dev.txt",
    "requirements.txt",
    "run.py",
    "run_all_agents.py",
    "start_platform.py",
    "start_server.py",
    "subproject_autopilot.py",
    "team_work_manager.py",
    "vercel.json",
    "verify_m002_phase4_setup.bat",
    "verify_m002_phase4_setup.sh",
}

ROOT_ALLOWED_DIRS = {
    ".agent",
    ".cache",
    ".claude",
    ".deploy",
    ".git",
    ".githooks",
    ".github",
    ".husky",
    ".n8n",
    ".playwright-cli",
    ".pytest_cache",
    ".workspace",
    ".vercel",
    ".vscode",
    ".zap",
    "__pycache__",
    "agent_workspaces",
    "agents",
    "api",
    "artifacts",
    "backend",
    "core",
    "daemon",
    "data",
    "docs",
    "htmlcov",
    "infrastructure",
    "instance",
    "locales",
    "logs",
    "memory",
    "migrations",
    "monitoring",
    "n8n",
    "n8n-comfy",
    "nginx",
    "node_modules",
    "nodejs",
    "nvm",
    "orchestrator",
    "qa-mobile",
    "scripts",
    "shared-intelligence",
    "skills",
    "tests",
    "tmp_logs",
    "web",
}

FIXED_PATHS = (
    "backend/",
    "web/",
    "tests/",
    "scripts/",
    "agents/",
    "daemon/",
    "orchestrator/",
    "shared-intelligence/",
    "n8n/",
    "CLAUDE.md",
    "AGENTS.md",
    "CODEX.md",
    "DEPLOYMENT_EXECUTION_SCRIPT.sh",
    "GEMINI.md",
    "access_whitelist.json",
    "continuous_improvement.sh",
    "deploy-verify.sh",
    "open_all_pages.bat",
    "platform.db",
    "start_server.py",
    "start_platform.py",
    "run.py",
    "verify_m002_phase4_setup.bat",
    "verify_m002_phase4_setup.sh",
)

WORKSPACE_LOCAL_PATHS = (
    ".deploy/",
    ".playwright-cli/",
    ".pytest_cache/",
    ".workspace/",
    ".workspace/logs/",
    ".workspace/reports/",
    ".workspace/root-artifacts/",
    "agent_workspaces/",
    "artifacts/",
    "docs/plans/execution/",
    "htmlcov/",
    "logs/",
    "node_modules/",
    "nodejs/",
    "nvm/",
    "tmp_logs/",
)

TEMP_ROOT_PREFIXES = ("tmp_", "_tmp_")
TEMP_ROOT_SUFFIXES = (".log", ".out", ".err", ".pid", ".lock")

DEPRECATED_PATHS = ()

CANONICAL_DOCS = (
    "README.md",
    "STATUS.md",
    "AGENTS.md",
    "docs/INDEX.md",
    "docs/status/CURRENT.md",
    "docs/status/BACKLOG.md",
    "docs/status/NOTION_SYNC_POLICY.md",
    "docs/ARCHITECTURE.md",
    "docs/PROJECTS.md",
    "docs/TEAM.md",
    "docs/DECISIONS.md",
    "docs/RULES.md",
    "docs/SOFTFACTORY_QUICKSTART.md",
    "docs/TROUBLESHOOTING.md",
    "docs/reference/active-paths.md",
    "docs/reference/repo-layout.md",
)

LINK_CHECK_FILES = (
    "README.md",
    "docs/INDEX.md",
)

DOC_EXCLUDED_PREFIXES = (
    "docs/plans/execution/",
)


def categorize_document(path: str) -> str:
    """Return the logical document category for a repository-relative path."""
    normalized = path.replace("\\", "/")

    if normalized in {"README.md", "STATUS.md"}:
        return "root"
    if normalized.startswith("docs/reference/"):
        return "reference"
    if normalized.startswith("docs/status/"):
        return "status"
    if normalized.startswith("docs/runbooks/"):
        return "runbooks"
    if normalized.startswith("docs/checklists/"):
        return "checklists"
    if normalized.startswith("docs/archive/"):
        return "archive"
    if normalized.startswith("docs/generated/"):
        return "generated"
    if normalized.startswith("docs/plans/active/"):
        return "plans-active"
    if normalized.startswith("docs/plans/"):
        return "plans-legacy"
    if normalized.startswith("docs/standards/"):
        return "standards"
    if normalized.startswith("docs/templates/"):
        return "templates"
    if normalized.startswith("docs/quick-start/"):
        return "quick-start"
    if normalized.startswith("docs/api/"):
        return "api"
    if normalized.startswith("docs/"):
        return "docs"
    return "other"


def is_excluded_document(path: str) -> bool:
    """Return True when the document should be excluded from the active catalog."""
    normalized = path.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in DOC_EXCLUDED_PREFIXES)
