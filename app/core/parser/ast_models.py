from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class BaseASTNode(BaseModel):
    name: str
    start_point: tuple[int, int]  # (row, column)
    end_point: tuple[int, int]
    body: str

class CommentNode(BaseASTNode):
    pass

class ImportNode(BaseASTNode):
    module: Optional[str] = None
    names: List[str] = Field(default_factory=list)

class FunctionNode(BaseASTNode):
    docstring: Optional[str] = None
    parameters: List[str] = Field(default_factory=list)
    complexity: Optional[int] = None

class ClassNode(BaseASTNode):
    docstring: Optional[str] = None
    methods: List[FunctionNode] = Field(default_factory=list)
    base_classes: List[str] = Field(default_factory=list)

class ASTSummary(BaseModel):
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    comment_count: int = 0
    max_nesting_depth: int = 0
    average_function_length: float = 0.0
    total_lines: int = 0
    blank_lines: int = 0

class ParsedFile(BaseModel):
    file_path: str
    language: str
    summary: ASTSummary
    classes: List[ClassNode] = Field(default_factory=list)
    functions: List[FunctionNode] = Field(default_factory=list)
    imports: List[ImportNode] = Field(default_factory=list)
    comments: List[CommentNode] = Field(default_factory=list)
    
    # We might not serialize the entire raw AST tree structure 
    # to avoid context window explosion in LangGraph.
    # The models above extract the core concepts for the AI agents.
