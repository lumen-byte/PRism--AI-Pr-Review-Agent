import os
from typing import Any, Dict, List, Tuple

# Common ignored directories and patterns
IGNORED_DIRS = {
    "node_modules",
    "dist",
    "build",
    "coverage",
    "venv",
    ".venv",
    "env",
    ".git",
    ".idea",
    ".vscode",
    "__pycache__",
    "out",
    "target",
    "vendor",
}

# Common binary and media extensions
IGNORED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".webp",
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".tar",
    ".gz",
    ".rar",
    ".7z",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".pyc",
    ".class",
    ".jar",
}

# Language mapping by extension
LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".go": "Go",
    ".java": "Java",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".ini": "INI",
    ".xml": "XML",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".sass": "SASS",
    ".sh": "Shell",
    ".bash": "Shell",
    ".sql": "SQL",
    ".rs": "Rust",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".dart": "Dart",
    ".r": "R",
    ".scala": "Scala",
}


class DiffParser:
    @staticmethod
    def classify_file(filename: str) -> Tuple[bool, str, str]:
        """
        Classifies a file based on its path and extension.
        Returns: (is_ignored, reason_if_ignored, language)
        """
        # 1. Check directories
        parts = filename.split("/")
        for part in parts[:-1]:
            if part in IGNORED_DIRS:
                return True, f"Ignored directory: {part}", "Unknown"

        # 2. Check filenames
        basename = parts[-1]
        if basename.lower() in {
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "poetry.lock",
        }:
            return True, "Generated lock file", "JSON/YAML"

        # Docker files might not have extensions
        if basename == "Dockerfile" or basename.startswith("Dockerfile."):
            return False, "", "Docker"

        if basename == "Makefile":
            return False, "", "Makefile"

        # 3. Check extensions
        ext = os.path.splitext(basename)[1].lower()
        if ext in IGNORED_EXTENSIONS:
            return True, f"Ignored extension: {ext}", "Binary/Media"

        # Determine language
        language = LANGUAGE_MAP.get(ext, "Unknown")

        return False, "", language

    @classmethod
    def parse_files(cls, changed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parses the changed files payload from GitHub.
        Returns classified lists and overall statistics.
        """
        parsed_files = []
        reviewable_files = []
        ignored_files = []

        diff_statistics = {
            "total_additions": 0,
            "total_deletions": 0,
            "total_changes": 0,
            "total_files": len(changed_files),
            "reviewable_count": 0,
            "ignored_count": 0,
        }

        language_breakdown = {}

        for file_data in changed_files:
            filename = file_data.get("filename", "")
            status = file_data.get("status", "unknown")
            additions = file_data.get("additions", 0)
            deletions = file_data.get("deletions", 0)
            changes = file_data.get("changes", 0)
            patch = file_data.get("patch", "")

            diff_statistics["total_additions"] += additions
            diff_statistics["total_deletions"] += deletions
            diff_statistics["total_changes"] += changes

            is_ignored, ignore_reason, language = cls.classify_file(filename)

            # Skip huge diffs (e.g. > 10,000 changes)
            if not is_ignored and changes > 10000:
                is_ignored = True
                ignore_reason = "Diff too large"

            # Skip files with no patch (e.g. renamed without changes) unless they are strictly renames
            if not is_ignored and not patch and status not in ("renamed", "removed"):
                is_ignored = True
                ignore_reason = "No patch available"

            # Deleted files are generally ignored for deep review unless specific checks are needed
            if status == "removed":
                is_ignored = True
                ignore_reason = "File deleted"

            file_info = {
                "file_path": filename,
                "extension": os.path.splitext(filename)[1].lower(),
                "status": status,
                "additions": additions,
                "deletions": deletions,
                "changes": changes,
                "patch_length": len(patch) if patch else 0,
                "language": language,
                "patch": patch,
            }

            parsed_files.append(file_info)

            if is_ignored:
                file_info["ignore_reason"] = ignore_reason
                ignored_files.append(file_info)
                diff_statistics["ignored_count"] += 1
            else:
                reviewable_files.append(file_info)
                diff_statistics["reviewable_count"] += 1

                # Track languages only for reviewable files
                if language != "Unknown":
                    language_breakdown[language] = (
                        language_breakdown.get(language, 0) + 1
                    )

        return {
            "parsed_files": parsed_files,
            "reviewable_files": reviewable_files,
            "ignored_files": ignored_files,
            "diff_statistics": diff_statistics,
            "language_breakdown": language_breakdown,
        }
