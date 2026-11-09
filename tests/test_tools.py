"""Tests for tools and security checks."""

import pytest
from kairos_code.tools.base import ToolRegistry
from kairos_code.tools.filesystem import FileReadTool, FileWriteTool, FileSearchTool
from kairos_code.tools.terminal import TerminalTool
from kairos_code.security.policy import PolicyEngine
from kairos_code.core.config import SecurityConfig


class TestFilesystemTools:
    @pytest.mark.asyncio
    async def test_read_and_write(self, tmp_path):
        write_tool = FileWriteTool(project_root=str(tmp_path))
        target = tmp_path / "sample.py"
        w_res = await write_tool.execute(path=str(target), content="print('hello')")
        assert w_res.success

        read_tool = FileReadTool(project_root=str(tmp_path))
        r_res = await read_tool.execute(path=str(target))
        assert r_res.success
        assert r_res.output == "print('hello')"

    @pytest.mark.asyncio
    async def test_search_by_pattern(self, tmp_path):
        (tmp_path / "auth.py").write_text("token = 1")
        (tmp_path / "readme.txt").write_text("docs")

        search_tool = FileSearchTool(project_root=str(tmp_path))
        res = await search_tool.execute(pattern="*.py")
        assert res.success
        assert "auth.py" in res.output


class TestTerminalTool:
    @pytest.mark.asyncio
    async def test_safe_execution(self, tmp_path):
        tool = TerminalTool(project_root=str(tmp_path))
        res = await tool.execute(command="echo kairos")
        assert res.success
        assert "kairos" in res.output

    @pytest.mark.asyncio
    async def test_block_dangerous(self, tmp_path):
        tool = TerminalTool(project_root=str(tmp_path))
        res = await tool.execute(command="rm -rf /")
        assert not res.success
        assert "blocked" in res.error.lower()


class TestPolicyEngine:
    def test_secret_redaction(self):
        engine = PolicyEngine(SecurityConfig())
        text = "API_KEY=sk-test123456789 and bearer token123"
        redacted = engine.redact_secrets(text)
        assert "sk-test123456789" not in redacted
