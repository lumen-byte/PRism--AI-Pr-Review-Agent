import tree_sitter
import tree_sitter_javascript
import tree_sitter_json
import tree_sitter_markdown
import tree_sitter_python
import tree_sitter_typescript
import tree_sitter_yaml

from app.core.logger import logger


class LanguageRegistry:
    def __init__(self):
        self._registry = {}
        self._initialize_parsers()

    def _initialize_parsers(self):
        try:
            self._registry["python"] = tree_sitter.Language(
                tree_sitter_python.language()
            )
        except Exception as e:
            logger.warning(f"Failed to load Python parser: {e}")

        try:
            self._registry["javascript"] = tree_sitter.Language(
                tree_sitter_javascript.language()
            )
        except Exception as e:
            logger.warning(f"Failed to load JavaScript parser: {e}")

        try:
            self._registry["typescript"] = tree_sitter.Language(
                tree_sitter_typescript.language_typescript()
            )
            self._registry["tsx"] = tree_sitter.Language(
                tree_sitter_typescript.language_tsx()
            )
        except Exception as e:
            logger.warning(f"Failed to load TypeScript/TSX parsers: {e}")

        try:
            self._registry["json"] = tree_sitter.Language(tree_sitter_json.language())
        except Exception as e:
            logger.warning(f"Failed to load JSON parser: {e}")

        try:
            self._registry["yaml"] = tree_sitter.Language(tree_sitter_yaml.language())
        except Exception as e:
            logger.warning(f"Failed to load YAML parser: {e}")

        try:
            self._registry["markdown"] = tree_sitter.Language(
                tree_sitter_markdown.language()
            )
        except Exception as e:
            logger.warning(f"Failed to load Markdown parser: {e}")

    def get_language(self, language_name: str) -> tree_sitter.Language | None:
        return self._registry.get(language_name.lower())

    def get_language_by_extension(self, extension: str) -> str | None:
        """Map file extension to tree-sitter language name."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "tsx",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".md": "markdown",
        }
        return ext_map.get(extension.lower())


language_registry = LanguageRegistry()
