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
        "name": "answer_and_close",
        "description": (
            "Answer a technical or how-to question from an intern and close the issue. "
            "Use for questions about Excel, Power BI, DAX, NBA stats concepts, data cleaning, "
            "Python, the assignment tasks, or anything that can be answered directly from knowledge."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": (
                        "A clear, friendly, step-by-step answer written for a high school or early college student. "
                        "Use simple language. Avoid jargon unless you explain it. Be encouraging and specific."
                    )
                }
            },
            "required": ["answer"]
        }
    },
    {
        "name": "escalate_to_coordinator",
        "description": (
            "Leave a submission or logistics question open for the program coordinator to answer. "
            "Use ONLY for questions about: deadlines, where or how to submit work, grading, "
            "who to email deliverables to, program schedule, or other administrative logistics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "acknowledgment": {
                    "type": "string",
                    "description": (
                        "A short, warm comment for the intern letting them know their question "
                        "has been received and the coordinator will respond soon. Keep it brief and reassuring."
                    )
                }
            },
            "required": ["acknowledgment"]
        }
    },
    {
        "name": "create_fix_pr",
        "description": (
            "Create a pull request to fix a real error or omission in the repository files. "
            "Use only when there is a genuine mistake in the repo content that requires a code or text change."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pr_title": {"type": "string"},
                "pr_body": {"type": "string"},
                "branch_name": {
                    "type": "string",
                    "description": "e.g. fix/issue-12-typo-in-readme"
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
    },
    {
        "name": "close_as_invalid",
        "description": "Close an issue that is spam, completely off-topic, or entirely unintelligible.",
        "input_schema": {
            "type": "object",
            "properties": {
                "explanation": {
                    "type": "string",
                    "description": "Friendly explanation written for a high school or early college student."
                }
            },
            "required": ["explanation"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    system="""You are a helpful assistant for the Aberdeen Advisors NBA Analytics Internship Program. \
You triage GitHub issues raised by high school and early college interns working on an NBA analytics assignment.

The assignment has interns:
- Exploring and cleaning NBA player data in Excel (430+ players, 2024-25 season)
- Calculating KPIs — especially Win Shares per $10M ("Bang for Buck")
- Building a 3-tab Power BI dashboard
- Presenting a player recommendation to fictional GMs with a $30M budget

Choose exactly ONE tool based on the issue type:

1. answer_and_close — Technical or how-to questions (Excel formulas, Power BI, DAX measures, \
NBA stats concepts, data cleaning steps, assignment task questions, etc.). \
Write your answer as if explaining to a smart 17-year-old: clear, encouraging, \
step-by-step where helpful. No jargon without explanation.

2. escalate_to_coordinator — Submission and logistics questions ONLY \
(deadlines, where/how to hand in work, grading, who to contact, program schedule). \
Post a brief acknowledgment and leave the issue open for the coordinator.

3. create_fix_pr — There is an actual error in a repo file that needs fixing \
(wrong information, broken content, missing section, etc.).

4. close_as_invalid — Spam or completely unintelligible. Use this sparingly.""",
    tools=tools,
    messages=[{
        "role": "user",
        "content": f"Issue #{issue_number}: {issue_title}\n\n{issue_body}\n\nRepository context:{repo_context}"
    }]
)

for block in response.content:
    if block.type != "tool_use":
        continue

    if block.name == "answer_and_close":
        comment = (
            f"## Hey! Here's your answer\n\n"
            f"{block.input['answer']}\n\n"
            f"---\n"
            f"*Answered automatically. If this didn't fully help, reopen the issue with more detail "
            f"and the coordinator will follow up.*"
        )
        subprocess.run(["gh", "issue", "comment", str(issue_number), "--body", comment], check=True)
        subprocess.run(["gh", "issue", "close", str(issue_number), "--reason", "completed"], check=True)

    elif block.name == "escalate_to_coordinator":
        comment = (
            f"{block.input['acknowledgment']}\n\n"
            f"---\n"
            f"*This has been flagged for the program coordinator — you'll hear back shortly.*"
        )
        subprocess.run(["gh", "issue", "comment", str(issue_number), "--body", comment], check=True)
        subprocess.run(
            ["gh", "issue", "edit", str(issue_number), "--add-assignee", "preetishrath"],
            check=True
        )
        github_output = os.environ.get("GITHUB_OUTPUT", "")
        if github_output:
            with open(github_output, "a") as f:
                f.write("action=escalate\n")

    elif block.name == "create_fix_pr":
        branch = block.input["branch_name"]
        subprocess.run(["git", "checkout", "-b", branch], check=True)

        for file in block.input["files"]:
            path = Path(file["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file["content"], encoding="utf-8")
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

    elif block.name == "close_as_invalid":
        comment = (
            f"## Issue Review\n\n"
            f"{block.input['explanation']}\n\n"
            f"---\n"
            f"*If you think this was closed in error, reopen it with more detail.*"
        )
        subprocess.run(["gh", "issue", "comment", str(issue_number), "--body", comment], check=True)
        subprocess.run(["gh", "issue", "close", str(issue_number), "--reason", "not planned"], check=True)

    break
