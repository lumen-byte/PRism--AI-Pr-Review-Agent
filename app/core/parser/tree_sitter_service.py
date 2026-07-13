import tree_sitter
from typing import Dict, List, Optional, Any
from app.core.logger import logger
from app.core.parser.language_registry import language_registry
from app.core.parser.ast_models import (
    ParsedFile, FunctionNode, ClassNode, ImportNode, CommentNode, ASTSummary
)
import time
import os

class TreeSitterService:
    def __init__(self):
        self._parsers: Dict[str, tree_sitter.Parser] = {}

    def _get_parser(self, language_name: str) -> tree_sitter.Parser | None:
        """Lightweight parser caching."""
        if language_name in self._parsers:
            return self._parsers[language_name]

        lang = language_registry.get_language(language_name)
        if not lang:
            return None

        parser = tree_sitter.Parser(lang)
        self._parsers[language_name] = parser
        return parser

    def parse_source(self, language_name: str, code: str, file_path: str = "unknown") -> Optional[ParsedFile]:
        """Main entry point to parse source code into structured models."""
        start_time = time.time()
        
        parser = self._get_parser(language_name)
        if not parser:
            logger.warning(f"No parser available for language: {language_name}")
            return None

        # Convert code to bytes for tree-sitter
        code_bytes = code.encode("utf-8")
        tree = parser.parse(code_bytes)
        root_node = tree.root_node

        parsed_file = self._extract_ast_components(root_node, code_bytes, language_name, file_path)
        
        execution_time = time.time() - start_time
        logger.info(
            f"Parsed {file_path} ({language_name}) in {execution_time:.3f}s: "
            f"{parsed_file.summary.function_count} functions, "
            f"{parsed_file.summary.class_count} classes, "
            f"{parsed_file.summary.import_count} imports"
        )
        return parsed_file

    def parse_file(self, file_path: str, code: str) -> Optional[ParsedFile]:
        extension = os.path.splitext(file_path)[1]
        language_name = language_registry.get_language_by_extension(extension)
        if not language_name:
            return None
        return self.parse_source(language_name, code, file_path)

    def _extract_ast_components(self, root_node, code_bytes: bytes, language: str, file_path: str) -> ParsedFile:
        functions = self.get_functions(root_node, code_bytes, language)
        classes = self.get_classes(root_node, code_bytes, language)
        imports = self.get_imports(root_node, code_bytes, language)
        comments = self.get_comments(root_node, code_bytes, language)
        
        # Calculate metrics
        total_lines = len(code_bytes.split(b'\\n'))
        blank_lines = len([line for line in code_bytes.split(b'\\n') if not line.strip()])
        
        avg_func_len = 0.0
        if functions:
            total_func_lines = sum((f.end_point[0] - f.start_point[0] + 1) for f in functions)
            avg_func_len = total_func_lines / len(functions)
            
        summary = ASTSummary(
            function_count=len(functions),
            class_count=len(classes),
            import_count=len(imports),
            comment_count=len(comments),
            max_nesting_depth=self._calculate_max_depth(root_node),
            average_function_length=avg_func_len,
            total_lines=total_lines,
            blank_lines=blank_lines
        )

        return ParsedFile(
            file_path=file_path,
            language=language,
            summary=summary,
            classes=classes,
            functions=functions,
            imports=imports,
            comments=comments
        )

    def get_functions(self, root_node, code_bytes: bytes, language: str) -> List[FunctionNode]:
        functions = []
        # Fallback simplistic traversal if we don't use strict language queries
        # In a real production system, use Language.query() with S-expressions
        def traverse(node):
            if "function" in node.type or "method" in node.type:
                name_node = None
                # Very basic heuristic for function names across languages
                for child in node.children:
                    if child.type == "identifier" or child.type == "property_identifier":
                        name_node = child
                        break
                        
                name = self.get_node_text(name_node, code_bytes) if name_node else "anonymous"
                
                functions.append(FunctionNode(
                    name=name,
                    start_point=node.start_point,
                    end_point=node.end_point,
                    body=self.get_node_text(node, code_bytes)
                ))
            for child in node.children:
                traverse(child)
        traverse(root_node)
        return functions

    def get_classes(self, root_node, code_bytes: bytes, language: str) -> List[ClassNode]:
        classes = []
        def traverse(node):
            if "class" in node.type:
                name_node = None
                for child in node.children:
                    if child.type == "identifier":
                        name_node = child
                        break
                name = self.get_node_text(name_node, code_bytes) if name_node else "anonymous"
                
                classes.append(ClassNode(
                    name=name,
                    start_point=node.start_point,
                    end_point=node.end_point,
                    body=self.get_node_text(node, code_bytes)
                ))
            for child in node.children:
                traverse(child)
        traverse(root_node)
        return classes

    def get_imports(self, root_node, code_bytes: bytes, language: str) -> List[ImportNode]:
        imports = []
        def traverse(node):
            if "import" in node.type:
                imports.append(ImportNode(
                    name=node.type,
                    start_point=node.start_point,
                    end_point=node.end_point,
                    body=self.get_node_text(node, code_bytes)
                ))
            for child in node.children:
                traverse(child)
        traverse(root_node)
        return imports

    def get_comments(self, root_node, code_bytes: bytes, language: str) -> List[CommentNode]:
        comments = []
        def traverse(node):
            if "comment" in node.type:
                comments.append(CommentNode(
                    name="comment",
                    start_point=node.start_point,
                    end_point=node.end_point,
                    body=self.get_node_text(node, code_bytes)
                ))
            for child in node.children:
                traverse(child)
        traverse(root_node)
        return comments

    def get_node_text(self, node, code_bytes: bytes) -> str:
        if not node:
            return ""
        return code_bytes[node.start_byte:node.end_byte].decode("utf-8")
        
    def _calculate_max_depth(self, root_node) -> int:
        def traverse(node, current_depth):
            if not node.children:
                return current_depth
            return max(traverse(child, current_depth + 1) for child in node.children)
        return traverse(root_node, 0)

tree_sitter_service = TreeSitterService()
