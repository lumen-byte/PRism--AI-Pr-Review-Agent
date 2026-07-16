import re
from typing import Optional


class GitHubMapper:
    def __init__(self):
        pass

    def map_line_to_position(self, patch: str, target_line: int) -> Optional[int]:
        """
        Maps an absolute line number in the file to the corresponding 'position'
        in the GitHub PR diff payload (which is 1-indexed based on the patch lines).
        """
        if not patch:
            return None

        position = 0
        current_file_line = None

        # Split patch into lines
        for patch_line in patch.split("\n"):
            position += 1

            # Check for hunk header e.g., @@ -10,4 +10,5 @@
            hunk_match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", patch_line)
            if hunk_match:
                current_file_line = int(hunk_match.group(1))
                continue

            if current_file_line is None:
                continue

            # Line added or unchanged
            if patch_line.startswith("+") or patch_line.startswith(" "):
                if current_file_line == target_line:
                    return position
                current_file_line += 1

            # Line deleted (we skip these in file lines count)
            elif patch_line.startswith("-"):
                pass

        return None


github_mapper = GitHubMapper()
