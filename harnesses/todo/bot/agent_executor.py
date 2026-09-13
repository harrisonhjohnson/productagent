"""
Agent Executor for NAVI - Generate and execute TODO-based agents

This module provides:
1. TODO-to-Agent: Generate plans for TODOs using Claude Code in plan mode
2. Plan approval and execution flow
3. Full Claude Code capabilities for execution (file editing, bash, Slack MCP, etc.)
"""
import os
import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple, List
try:
    from config import USER_NAME
except ImportError:  # pragma: no cover
    USER_NAME = "you"

logger = logging.getLogger(__name__)

# Claude CLI path - configurable via environment variable
CLAUDE_PATH = os.getenv("CLAUDE_PATH", os.path.expanduser("~/.local/bin/claude"))

# Pinned so bot runs never inherit the interactive /model (which may be a
# capped premium tier). Override with CLAUDE_MODEL for a one-off.
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")

# Plans directory - persists across bot restarts
PLANS_DIR = os.path.expanduser("~/work/agent-plans")


class AgentExecutor:
    """
    Handles TODO-to-Agent planning and execution.

    User flow:
    1. /agent TXXX - Generate plan for TODO
    2. /approve TXXX - Execute approved plan
    3. /plans - List pending plans
    """

    def __init__(self, todo_manager):
        """
        Initialize agent executor.

        Args:
            todo_manager: TodoManager instance for TODO operations
        """
        self.todo_manager = todo_manager
        self.pending_plans = {}  # In-memory cache, backed by filesystem

        # Ensure plans directory exists
        os.makedirs(PLANS_DIR, exist_ok=True)

        logger.info("AgentExecutor initialized")

    def generate_agent_prompt(self, todo: dict) -> str:
        """
        Build context-rich prompt for Claude agent in plan mode.

        Gathers:
        - TODO text and metadata
        - Due date if present
        """
        todo_id = todo.get('id', 'UNKNOWN')
        todo_text = todo.get('text', '')
        metadata = todo.get('metadata', {})

        context_parts = [
            "# TODO Context",
            f"**ID:** {todo_id}",
            f"**Task:** {todo_text}",
            ""
        ]

        # Due date if present
        if metadata.get('due'):
            context_parts.append(f"**Due Date:** {metadata['due']}")
            context_parts.append("")

        context = "\n".join(context_parts)

        prompt = f"""You are an agent helping {USER_NAME} complete a TODO item.

{context}

## Your Task
Create a detailed plan to accomplish this TODO. You have full Claude Code capabilities:
- Edit files, run bash commands, access ~/TODO.md

## Plan Requirements
Provide a structured plan with:
1. **Goal** - One sentence summary
2. **Steps** - Numbered, specific actions
3. **Expected Outcome** - What success looks like
4. **Estimated Effort** - Quick (5 min), Medium (15-30 min), or Deep (1+ hour)

## Guidelines
- For confirmations/follow-ups, draft the actual message content
- If a task involves code changes, identify the specific files
- Consider dependencies (what needs to happen first)

Start your plan now:"""

        return prompt

    def invoke_plan_mode(self, todo_id: str) -> Tuple[bool, str]:
        """
        Run Claude in plan mode and return structured plan.

        Args:
            todo_id: The TODO ID to generate a plan for

        Returns:
            Tuple of (success: bool, plan_text_or_error: str)
        """
        # Get the TODO
        todos = self.todo_manager.get_todos(include_completed=False)
        todo = next((t for t in todos if t.get('id') == todo_id.upper()), None)

        if not todo:
            return False, f"TODO {todo_id} not found"

        # Generate prompt
        prompt = self.generate_agent_prompt(todo)

        try:
            # Run Claude in plan mode (read-only, no edits)
            result = subprocess.run(
                [CLAUDE_PATH, "-p", "--model", CLAUDE_MODEL, prompt],
                capture_output=True,
                text=True,
                timeout=300,  # 5 min for planning
                env={**os.environ, "CLAUDE_CODE_PERMISSION_MODE": "plan"}
            )

            if result.returncode != 0:
                error_msg = result.stderr or "Claude command failed"
                logger.error(f"Agent planning error: {error_msg}")
                return False, f"Agent error: {error_msg[:500]}"

            plan = result.stdout or "No plan generated"

            # Store plan
            self.pending_plans[todo_id.upper()] = {
                "todo_id": todo_id.upper(),
                "todo_text": todo.get('text', ''),
                "plan": plan,
                "created": datetime.now().isoformat(),
                "status": "pending"
            }
            self._save_plan(todo_id.upper())

            logger.info(f"Generated plan for TODO {todo_id}")
            return True, plan

        except subprocess.TimeoutExpired:
            logger.error(f"Agent planning timed out for {todo_id}")
            return False, "Agent timed out (5 min limit)"
        except FileNotFoundError:
            logger.error(f"Claude CLI not found at {CLAUDE_PATH}")
            return False, f"Claude CLI not found at {CLAUDE_PATH}"
        except Exception as e:
            logger.error(f"Error generating plan: {e}")
            return False, f"Error: {str(e)}"

    def approve_plan(self, todo_id: str) -> Tuple[bool, str]:
        """
        Execute an approved plan with full Claude Code capabilities.

        Args:
            todo_id: The TODO ID whose plan to execute

        Returns:
            Tuple of (success: bool, result_or_error: str)
        """
        # Load plan from memory or disk
        plan_data = self.pending_plans.get(todo_id.upper()) or self._load_plan(todo_id.upper())

        if not plan_data:
            return False, f"No pending plan for {todo_id}"

        if plan_data.get('status') != 'pending':
            return False, f"Plan for {todo_id} already executed (status: {plan_data.get('status')})"

        # Build execution prompt
        prompt = f"""Execute this plan for TODO {todo_id}:

{plan_data['plan']}

## Execution Guidelines
- Execute each step in order
- Report what you did for each step
- If a step fails, note it but continue with remaining steps
- For Slack messages, use the Slack MCP to send them
- For file edits, make the changes directly

You have full permissions. Execute the plan now and report results."""

        try:
            # Run Claude with full permissions
            result = subprocess.run(
                [CLAUDE_PATH, "-p", "--dangerously-skip-permissions", "--model", CLAUDE_MODEL, prompt],
                capture_output=True,
                text=True,
                timeout=600  # 10 min for execution
            )

            execution_result = result.stdout or "Execution completed (no output)"

            # Update plan status
            plan_data['status'] = 'executed'
            plan_data['executed_at'] = datetime.now().isoformat()
            plan_data['result'] = execution_result
            plan_data['exit_code'] = result.returncode
            self._save_plan(todo_id.upper())

            if result.returncode != 0:
                logger.warning(f"Plan execution for {todo_id} returned non-zero: {result.returncode}")
            else:
                logger.info(f"Plan executed for TODO {todo_id}")

            return True, execution_result

        except subprocess.TimeoutExpired:
            plan_data['status'] = 'timeout'
            self._save_plan(todo_id.upper())
            logger.error(f"Plan execution timed out for {todo_id}")
            return False, "Execution timed out (10 min limit)"
        except Exception as e:
            plan_data['status'] = 'error'
            plan_data['error'] = str(e)
            self._save_plan(todo_id.upper())
            logger.error(f"Execution error for {todo_id}: {e}")
            return False, f"Execution error: {str(e)}"

    def cancel_plan(self, todo_id: str) -> Tuple[bool, str]:
        """
        Cancel a pending plan.

        Args:
            todo_id: The TODO ID whose plan to cancel

        Returns:
            Tuple of (success: bool, message: str)
        """
        plan_data = self.pending_plans.get(todo_id.upper()) or self._load_plan(todo_id.upper())

        if not plan_data:
            return False, f"No plan found for {todo_id}"

        plan_data['status'] = 'cancelled'
        plan_data['cancelled_at'] = datetime.now().isoformat()
        self._save_plan(todo_id.upper())

        logger.info(f"Cancelled plan for TODO {todo_id}")
        return True, f"Plan for {todo_id} cancelled"

    def get_plan(self, todo_id: str) -> Optional[dict]:
        """Get plan data for a TODO."""
        return self.pending_plans.get(todo_id.upper()) or self._load_plan(todo_id.upper())

    def get_pending_plans(self) -> List[dict]:
        """Get all pending plans."""
        plans = []

        try:
            for filename in os.listdir(PLANS_DIR):
                if filename.endswith('.json'):
                    plan = self._load_plan(filename.replace('.json', ''))
                    if plan and plan.get('status') == 'pending':
                        plans.append(plan)
        except Exception as e:
            logger.error(f"Error listing plans: {e}")

        # Sort by creation date (newest first)
        plans.sort(key=lambda p: p.get('created', ''), reverse=True)

        return plans

    def _save_plan(self, todo_id: str):
        """Save plan to filesystem."""
        plan_data = self.pending_plans.get(todo_id)
        if plan_data:
            path = os.path.join(PLANS_DIR, f"{todo_id}.json")
            try:
                with open(path, 'w') as f:
                    json.dump(plan_data, f, indent=2)
                logger.debug(f"Saved plan to {path}")
            except Exception as e:
                logger.error(f"Failed to save plan: {e}")

    def _load_plan(self, todo_id: str) -> Optional[dict]:
        """Load plan from filesystem."""
        path = os.path.join(PLANS_DIR, f"{todo_id}.json")

        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    plan_data = json.load(f)
                    self.pending_plans[todo_id] = plan_data
                    return plan_data
            except Exception as e:
                logger.error(f"Failed to load plan from {path}: {e}")

        return None

    def format_plan_summary(self, plan_data: dict, max_plan_length: int = 2000) -> str:
        """
        Format plan data for Telegram display.

        Args:
            plan_data: Plan dict from storage
            max_plan_length: Max characters for plan preview

        Returns:
            Formatted string for Telegram
        """
        todo_id = plan_data.get('todo_id', '?')
        todo_text = plan_data.get('todo_text', 'Unknown task')
        plan = plan_data.get('plan', 'No plan content')
        status = plan_data.get('status', 'unknown')

        # Truncate plan if too long
        if len(plan) > max_plan_length:
            plan = plan[:max_plan_length] + "\n\n... (truncated)"

        lines = [
            f"**Plan for {todo_id}**",
            f"Task: {todo_text[:100]}",
            f"Status: {status}",
            "",
            plan,
            "",
            "---",
        ]

        if status == 'pending':
            lines.append(f"'/approve {todo_id}' to execute | '/cancel {todo_id}' to abort")
        elif status == 'executed':
            lines.append(f"Executed at: {plan_data.get('executed_at', 'unknown')}")

        return "\n".join(lines)
