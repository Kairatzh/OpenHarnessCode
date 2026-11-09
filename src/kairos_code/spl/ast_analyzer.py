"""AST analyzer — extracts real syntax symbols, signatures, and call references."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Optional

from kairos_code.spl.models import ASTSymbolChange


class ASTAnalyzer:
    """Analyzes Python code to extract verified symbols and call graphs."""

    @staticmethod
    def parse_symbols(code: str, file_path: str = "") -> list[ASTSymbolChange]:
        """Extract functions, methods, classes, and imports from python code."""
        symbols: list[ASTSymbolChange] = []
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return symbols

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                args = [a.arg for a in node.args.args]
                sig = f"{node.name}({', '.join(args)})"
                doc = ast.get_docstring(node) or ""
                symbols.append(ASTSymbolChange(
                    symbol_type="function",
                    name=node.name,
                    change_type="added",
                    file_path=file_path,
                    signature=sig,
                    docstring=doc,
                ))
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                bases = [ast.unparse(b) for b in node.bases] if hasattr(ast, "unparse") else []
                sig = f"class {node.name}({', '.join(bases)})"
                symbols.append(ASTSymbolChange(
                    symbol_type="class",
                    name=node.name,
                    change_type="added",
                    file_path=file_path,
                    signature=sig,
                    docstring=doc,
                ))
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [alias.name for alias in node.names]
                sig = f"import {', '.join(names)}"
                symbols.append(ASTSymbolChange(
                    symbol_type="import",
                    name=", ".join(names),
                    change_type="added",
                    file_path=file_path,
                    signature=sig,
                ))

        return symbols

    @staticmethod
    def diff_symbols(old_code: str, new_code: str, file_path: str = "") -> list[ASTSymbolChange]:
        """Compare symbols between two versions of code."""
        old_symbols = {s.name: s for s in ASTAnalyzer.parse_symbols(old_code, file_path)}
        new_symbols = {s.name: s for s in ASTAnalyzer.parse_symbols(new_code, file_path)}

        changes: list[ASTSymbolChange] = []

        # Added or modified
        for name, new_sym in new_symbols.items():
            if name not in old_symbols:
                new_sym.change_type = "added"
                changes.append(new_sym)
            elif old_symbols[name].signature != new_sym.signature:
                new_sym.change_type = "modified"
                changes.append(new_sym)

        # Removed
        for name, old_sym in old_symbols.items():
            if name not in new_symbols:
                old_sym.change_type = "removed"
                changes.append(old_sym)

        return changes

    @staticmethod
    def extract_function_calls(code: str) -> list[str]:
        """Find all function calls made in the code."""
        calls = set()
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        calls.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        calls.add(node.func.attr)
        except Exception:
            pass
        return sorted(calls)
