# pipeline.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .lexer import tokenize
from .parser import Parser
from .semantic import analyze, SemanticResult
from .error import ArcanaError, ErrorCode, parse_error


@dataclass
class CompileArtifacts:
    """
    One-shot compiler pipeline result.
    - program: AST after parse + semantic normalization
    - warnings: semantic warnings (future use)
    """
    program: object
    warnings: list[str]


def compile_source(src: str, *, max_loop_depth: int = 3) -> CompileArtifacts:
    """
    Full pipeline:
      source -> tokens -> AST -> semantic checks/normalization

    Raises:
      ArcanaParseError / ArcanaSemanticError (both ArcanaError subclasses)
    """
    try:
        toks = tokenize(src)
        # print(f"[arcana: pipeline] tokens = {toks}")
        program = Parser(toks).parse_program()
        sem: SemanticResult = analyze(program, max_loop_depth=max_loop_depth)
        return CompileArtifacts(program=sem.program, warnings=sem.warnings)
    except ArcanaError:
        # Already in unified Arcana error format
        raise
    except SyntaxError as e:
        # Defensive: if something leaked as bare SyntaxError, unify it.
        raise parse_error(ErrorCode.PARSE_INTERNAL, str(e))
    except Exception as e:
        # Last resort: keep the message but mark as internal pipeline error.
        raise parse_error(ErrorCode.PARSE_INTERNAL, f"Internal compiler error: {e}")


def compile_file(path: str, *, encoding: str = "utf-8", max_loop_depth: int = 3) -> CompileArtifacts:
    with open(path, "r", encoding=encoding) as f:
        return compile_source(f.read(), max_loop_depth=max_loop_depth)
