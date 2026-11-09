"""Sanity check and test runner for KAIROS Code."""

import os
import sys

# Ensure src is on python path
repo_root = os.path.abspath(os.path.dirname(__file__))
src_dir = os.path.join(repo_root, "src")
sys.path.insert(0, src_dir)

print(f"[*] Python version: {sys.version}")
print(f"[*] Repo root: {repo_root}")
print(f"[*] Adding to sys.path: {src_dir}")

try:
    import kairos_code
    print(f"[+] Loaded kairos_code v{kairos_code.__version__}")

    from kairos_code.core import (
        Task,
        TaskStatus,
        HarnessConfig,
        ComponentRegistry,
        EventBus,
        EventType,
    )
    print("[+] Core models and config loaded")

    from kairos_code.runtime.prompt_registry import PromptRegistry
    from kairos_code.runtime.agent import AgentRuntime
    print("[+] Runtime & PromptRegistry loaded")

    from kairos_code.orchestrator.engine import Orchestrator
    from kairos_code.orchestrator.workflows import FeatureDevelopmentWorkflow, BugfixWorkflow
    print("[+] Orchestrator & Workflows loaded")

    from kairos_code.tools.base import ToolRegistry
    from kairos_code.tools.filesystem import FileReadTool, FileWriteTool, FileSearchTool
    from kairos_code.tools.terminal import TerminalTool
    from kairos_code.tools.git import GitTool
    print("[+] Tools subsystem loaded")

    from kairos_code.self_mod.customize import SelfModificationEngine
    print("[+] Self-Modification Engine loaded")

    from kairos_code.vibe.engine import VibeEngine
    print("[+] Vibe Mode Engine loaded")

    from kairos_code.storage.sqlite_store import SQLiteStore
    print("[+] SQLite storage loaded")

    # Verify Component Registry
    reg = ComponentRegistry()
    comps = reg.list_all()
    print(f"[+] Component Registry introspected {len(comps)} subsystems:")
    for c in comps:
        print(f"    - {c.id:<20} [{c.category}] -> {c.interface}")

    # Verify Self-Modification inspection
    self_mod = SelfModificationEngine(repo_root, reg)
    arch = self_mod.inspect_architecture()
    print(f"[+] Self-mod architecture inspection: {len(arch['active_components'])} active components")

    # Verify prompt assembly
    prompt_reg = PromptRegistry()
    prompt_reg.load_builtin_prompts(os.path.join(src_dir, "kairos_code", "prompts"))
    agents = prompt_reg.list_agents()
    print(f"[+] Prompt registry loaded agents: {agents}")

    print("\n[SUCCESS] ALL KAIROS CODE ARCHITECTURE CHECKS PASSED!")

except Exception as e:
    import traceback
    print(f"\n[ERROR] Failed: {e}")
    traceback.print_exc()
    sys.exit(1)
