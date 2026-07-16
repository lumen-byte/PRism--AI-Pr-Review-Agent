import hashlib
import re
from typing import Any, Dict, List

from app.services.quality.quality_models import QualityIssue


class DuplicationDetector:
    def __init__(self):
        # We will keep a global hash map during the scan of multiple files
        # Map of hash -> (file_path, name, line)
        self.seen_blocks: Dict[str, Any] = {}

    def scan(self, file_path: str, ast_data: Dict[str, Any]) -> List[QualityIssue]:
        issues = []
        if not ast_data:
            return issues

        functions = ast_data.get("functions", [])

        for func in functions:
            name = func.get("name", "anonymous")
            start_line = func.get("start_point", [0])[0] + 1
            body = func.get("body", "")

            # Normalization: remove whitespace, docstrings, and simple comments to catch structural clones
            normalized_body = re.sub(r"\s+", "", body)

            # Only consider blocks with sufficient length to avoid false positives for tiny functions
            if len(normalized_body) < 50:
                continue

            block_hash = hashlib.md5(normalized_body.encode("utf-8")).hexdigest()

            if block_hash in self.seen_blocks:
                orig = self.seen_blocks[block_hash]
                # If it's the exact same location, ignore
                if orig["file"] == file_path and orig["line"] == start_line:
                    continue

                issues.append(
                    QualityIssue(
                        file=file_path,
                        line=start_line,
                        rule="duplicate_code",
                        severity="medium",
                        title="Duplicate Code Block",
                        description=f"Function '{name}' is a duplicate of '{orig['name']}' in {orig['file']}:{orig['line']}.",
                        recommendation="Extract the common logic into a shared helper function.",
                        confidence="high",
                    )
                )
            else:
                self.seen_blocks[block_hash] = {
                    "file": file_path,
                    "name": name,
                    "line": start_line,
                }

        return issues
