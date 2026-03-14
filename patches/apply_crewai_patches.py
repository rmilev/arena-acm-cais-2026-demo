#!/usr/bin/env python3
"""Apply CrewAI patches required for Bedrock Converse API compatibility.

CrewAI 1.x has two bugs when using the native Bedrock provider:

1. _parse_native_tool_call (crew_agent_executor.py):
   Tool calls from Bedrock use `toolUseId`/`name`/`input` fields, but
   CrewAI only checks OpenAI-style `id`/`function.name`/`function.arguments`.
   Result: tool args arrive as empty {}, every tool call fails validation.

2. _format_messages_for_converse (bedrock/completion.py):
   Each tool result is sent as a separate `user` message, but Bedrock's
   Converse API requires ALL toolResult blocks for a given assistant turn
   in a SINGLE user message. Consecutive same-role messages are rejected.
   Result: "Expected toolResult blocks" error after first tool execution.

Usage:
    python patches/apply_crewai_patches.py          # auto-detect venv
    python patches/apply_crewai_patches.py --check   # dry run, just check status
    python patches/apply_crewai_patches.py --venv /path/to/.venv
"""
import argparse
import os
import sys

# --------------------------------------------------------------------------- #
# Patch 1: crew_agent_executor.py — _parse_native_tool_call
# --------------------------------------------------------------------------- #
PATCH1_FILE = "crewai/agents/crew_agent_executor.py"

# Original code (OpenAI-only):
PATCH1_OLD = '''\
            call_id = (
                tool_call.get("id")
                or f"call_{id(tool_call)}"
            )
            func_info = tool_call.get("function", {})
            func_name = sanitize_tool_name(
                func_info.get("name", "")
            )
            func_args = func_info.get("arguments") or {}'''

# Patched code (OpenAI + Bedrock):
PATCH1_NEW = '''\
            call_id = (
                tool_call.get("id")
                or tool_call.get("toolUseId")
                or f"call_{id(tool_call)}"
            )
            func_info = tool_call.get("function", {})
            func_name = sanitize_tool_name(
                func_info.get("name", "") or tool_call.get("name", "")
            )
            func_args = func_info.get("arguments") or tool_call.get("input", {})'''


# --------------------------------------------------------------------------- #
# Patch 2: bedrock/completion.py — _format_messages_for_converse
# --------------------------------------------------------------------------- #
PATCH2_FILE = "crewai/llms/providers/bedrock/completion.py"

# Original code (separate user message per tool result):
PATCH2_OLD = '''\
            elif role == "tool":
                if not tool_call_id:
                    raise ValueError("Tool message missing required tool_call_id")
                tool_result_block = {
                    "toolResult": {
                        "toolUseId": tool_call_id,
                        "content": [
                            {"text": str(content) if content else ""}
                        ],
                    }
                }
                converse_messages.append(
                    {
                        "role": "user",
                        "content": [tool_result_block],
                    }
                )'''

# Patched code (merge consecutive tool results into one user message):
PATCH2_NEW = '''\
            elif role == "tool":
                if not tool_call_id:
                    raise ValueError("Tool message missing required tool_call_id")
                tool_result_block = {
                    "toolResult": {
                        "toolUseId": tool_call_id,
                        "content": [
                            {"text": str(content) if content else ""}
                        ],
                    }
                }
                # Merge consecutive tool results into one user message
                # (Bedrock requires all toolResults in a single user turn)
                if (
                    converse_messages
                    and converse_messages[-1].get("role") == "user"
                    and any(
                        "toolResult" in block
                        for block in converse_messages[-1].get("content", [])
                    )
                ):
                    converse_messages[-1]["content"].append(tool_result_block)
                else:
                    converse_messages.append(
                        {
                            "role": "user",
                            "content": [tool_result_block],
                        }
                    )'''

PATCHES = [
    ("Patch 1: Bedrock tool call parsing", PATCH1_FILE, PATCH1_OLD, PATCH1_NEW),
    ("Patch 2: Bedrock toolResult merging", PATCH2_FILE, PATCH2_OLD, PATCH2_NEW),
]


def find_site_packages(venv_path: str) -> str:
    """Find site-packages directory in a venv."""
    for root, dirs, _ in os.walk(os.path.join(venv_path, "lib")):
        if "site-packages" in dirs:
            return os.path.join(root, "site-packages")
    raise FileNotFoundError(f"No site-packages found in {venv_path}")


def apply_patch(name: str, filepath: str, old: str, new: str, dry_run: bool) -> str:
    """Apply a single patch. Returns status string."""
    if not os.path.exists(filepath):
        return "SKIP (file not found)"

    with open(filepath, "r") as f:
        content = f.read()

    if new in content:
        return "ALREADY APPLIED"

    if old not in content:
        return "CANNOT APPLY (original code not found — different CrewAI version?)"

    if dry_run:
        return "WOULD APPLY"

    content = content.replace(old, new, 1)
    with open(filepath, "w") as f:
        f.write(content)
    return "APPLIED"


def main():
    parser = argparse.ArgumentParser(description="Apply CrewAI Bedrock patches")
    parser.add_argument("--venv", help="Path to .venv directory")
    parser.add_argument("--check", action="store_true", help="Dry run — check status only")
    args = parser.parse_args()

    # Find venv
    if args.venv:
        venv = args.venv
    elif os.path.isdir(".venv"):
        venv = ".venv"
    else:
        print("ERROR: No .venv found. Run from project root or pass --venv.")
        sys.exit(1)

    try:
        site_packages = find_site_packages(venv)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"Site-packages: {site_packages}")
    print(f"Mode: {'check only' if args.check else 'applying patches'}\n")

    all_ok = True
    for name, relpath, old, new in PATCHES:
        filepath = os.path.join(site_packages, relpath)
        status = apply_patch(name, filepath, old, new, dry_run=args.check)
        icons = {
            "APPLIED": "+", "ALREADY APPLIED": "=", "WOULD APPLY": "?",
            "SKIP (file not found)": "!", "CANNOT APPLY": "!",
        }
        icon = icons.get(status, icons.get(status.split("(")[0].strip(), "?"))
        print(f"  [{icon}] {name}: {status}")
        if "CANNOT" in status or "SKIP" in status:
            all_ok = False

    if all_ok:
        print("\nAll patches OK.")
    else:
        print("\nSome patches could not be applied. Check CrewAI version.")
        sys.exit(1)


if __name__ == "__main__":
    main()
