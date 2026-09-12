"""
Configurable heuristic analysis thresholds for ProjectLens static analysis engine.
These thresholds are configurable parameters and not universal academic standards.
"""

MAX_FUNCTION_LINES: int = 80
HIGH_COMPLEXITY: float = 10.0
VERY_HIGH_COMPLEXITY: float = 15.0
LOW_TEST_FILE_RATIO: float = 0.05
MIN_DOC_FILE_COUNT: int = 1

# Standard directory exclusion list for project scanning
IGNORED_DIRECTORIES: set[str] = {
    "node_modules",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".git/objects",
    "dist",
    "build",
    "coverage",
    "target",
    ".idea",
    ".vscode",
    ".DS_Store",
    ".next",
    ".nuxt",
    "out",
    "bin",
    "obj",
}

# Standard file extension classifications
SOURCE_EXTENSIONS: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript React",
    ".ts": "TypeScript",
    ".tsx": "TypeScript React",
    ".java": "Java",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".html": "HTML",
    ".css": "CSS",
    ".sql": "SQL",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".rb": "Ruby",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".cs": "C#",
}

DOC_EXTENSIONS: set[str] = {
    ".md", ".markdown", ".rst", ".pdf", ".txt", ".doc", ".docx"
}

CONFIG_EXTENSIONS: set[str] = {
    ".json", ".yaml", ".yml", ".toml", ".xml", ".ini", ".env.example", "Dockerfile", "Makefile"
}
