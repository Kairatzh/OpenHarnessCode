"""Tests for Semantic Programming Layer (SPL) and AST analysis."""

import pytest
from kairos_code.spl.models import (
    SemanticIntent,
    SemanticOperationType,
    EvidenceItem,
    EvidenceStatus,
    CodeExplanation,
)
from kairos_code.spl.ast_analyzer import ASTAnalyzer


class TestASTAnalyzer:
    def test_parse_functions_and_classes(self):
        code = """
import os

class CacheManager:
    \"\"\"Manages cached responses.\"\"\"
    def __init__(self, ttl: int = 300):
        self.ttl = ttl

def get_or_compute(key, compute_fn):
    \"\"\"Fetch or compute result.\"\"\"
    return compute_fn()
"""
        symbols = ASTAnalyzer.parse_symbols(code, file_path="cache.py")
        names = [s.name for s in symbols]

        assert "CacheManager" in names
        assert "get_or_compute" in names
        assert "__init__" in names

    def test_diff_symbols(self):
        old_code = "def existing(): pass"
        new_code = "def existing(): pass\ndef newly_added(a, b): return a + b"

        diff = ASTAnalyzer.diff_symbols(old_code, new_code, file_path="calc.py")
        added = [d for d in diff if d.change_type == "added"]

        assert len(added) == 1
        assert added[0].name == "newly_added"
        assert "a, b" in added[0].signature

    def test_extract_function_calls(self):
        code = """
def run():
    print("test")
    val = fetch_data()
    return parse_json(val)
"""
        calls = ASTAnalyzer.extract_function_calls(code)
        assert "print" in calls
        assert "fetch_data" in calls
        assert "parse_json" in calls


class TestEvidenceTaxonomy:
    def test_evidence_item_status(self):
        item1 = EvidenceItem(
            statement="Function get_cached added",
            status=EvidenceStatus.OBSERVED,
            source="ast:get_cached",
        )
        item2 = EvidenceItem(
            statement="5 unit tests passed",
            status=EvidenceStatus.TESTED,
            source="pytest",
        )
        assert item1.status == EvidenceStatus.OBSERVED
        assert item2.status == EvidenceStatus.TESTED
