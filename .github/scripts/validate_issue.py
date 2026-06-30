import os
import subprocess
from pathlib import Path

import anthropic

issue_number = os.environ["ISSUE_NUMBER"]
issue_title = os.environ["ISSUE_TITLE"]
issue_body = os.environ.get("ISSUE_BODY") or ""


def read_file(path, max_chars=4000):
    p = Path(path)
    if not p.exists():
        return None
    content = p.read_text(encoding="utf-8", errors="ignore")
    if len(content) > max_chars:
        content = content[:max_chars] + "\n... [truncated]"
    return content


repo_context = ""
for filename in ["README.md", "CLAUDE.md"]:
    content = read_file(filename)
    if content:
        repo_context += f"\n\n--- {filename} ---\n{content}"

client = anthropic.Anthropic()

tools = [
    {
        "name": "close_invalid_issue",
        "description": "Close an issue that is not a valid bug or meaningful improvement for this repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "Friendly, clear explanation of why this is not a valid issue, with any helpful guidance for the person who filed it."
                }
            },
            "required": ["explanation"]
        }
    },
    {
        "name": "create_fix_pr",
        "description": "Create a pull request to fix a valid issue. Include full file contents for every file that needs to change.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pr_title": {
                    "type": "string",
                    "description": "Short, descriptive PR title."
                },
                "pr_body": {
                    "type": "string",
                    "description": "Description of what the PR fixes and how."
                },
                "branch_name": {
                    "type": "string",
                    "description": "Branch name, e.g. fix/issue-12-typo-in-readme"
                },
                "files": {
                    "type": "array",
                    "description": "Files to create or overwrite. Provide complete file content.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            "required": ["pr_title", "pr_body", "branch_name", "files"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system="""You are an automated issue validator for the Aberdeen Advisors NBA Analytics Assignment repository.

This repo is an intern assignment. It contains:
- NBA Analytics Packet.html: 8-phase assignment guide for interns
- Mock-Dashboard-Reference.html: Power BI dashboard reference mockup
- nba_data_raw.xlsx: Raw NBA player dataset (430+ players, 2024-25 season)
- README.md: Repo overview
- CLAUDE.md: Project context and contributors

A valid issue is one that identifies a real problem: a factual error, broken content, missing critical information, or a clear improvement to the documentation.

An invalid issue is anything that is a question, off-topic, vague, a duplicate, or describes behaviour that is working as intended.

Call close_invalid_issue for invalid issues. Call create_fix_pr for valid ones — include complete file contents in the files array so the fix can be committed directly.""",
    tools=tools,
    messages=[{
        "role": "user",
        "content": f"Issue #{issue_number}: {issue_title}\n\n{issue_body}\n\nRepository context:{repo_context}"
    }]
)

for block in response.content:
    if block.type != "tool_use":
        continue

    if block.name == "close_invalid_issue":
        comment = (
            f"## Issue Review\n\n"
            f"{block.input['explanation']}\n\n"
            f"*Reviewed automatically by Claude. If you think this was closed in error, please reopen with more detail.*"
        )
        subprocess.run(["gh", "issue", "comment", str(issue_number), "--body", comment], check=True)
        subprocess.run(["gh", "issue", "close", str(issue_number), "--reason", "not planned"], check=True)

    elif block.name == "create_fix_pr":
        branch = block.input["branch_name"]
        subprocess.run(["git", "checkout", "-b", branch], check=True)

        for f in block.input["files"]:
            path = Path(f["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f["content"], encoding="utf-8")
            subprocess.run(["git", "add", str(path)], check=True)

        subprocess.run(
            ["git", "commit", "-m", f"fix: {block.input['pr_title']}\n\nFixes #{issue_number}"],
            check=True
        )
        subprocess.run(["git", "push", "origin", branch], check=True)

        pr_body = (
            f"{block.input['pr_body']}\n\n"
            f"Fixes #{issue_number}\n\n"
            f"*This PR was created automatically by Claude. Please review before merging.*"
        )
        subprocess.run([
            "gh", "pr", "create",
            "--title", block.input["pr_title"],
            "--body", pr_body,
            "--base", "main",
            "--head", branch
        ], check=True)

    break
