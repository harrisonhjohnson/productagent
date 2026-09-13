"""
HYRULE Server - Local API server for HYRULE-Navi TODO sync

Serves HYRULE.html and provides REST API endpoints that reuse TodoManager.
This allows HYRULE to display live TODO data and mark items complete.

IMPORTANT: This server does NOT send Slack notifications - only Navi does.
"""
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import date, timedelta

# Add navi directory to path for imports
NAVI_DIR = Path(__file__).parent
sys.path.insert(0, str(NAVI_DIR))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

import config
from todo_manager import TodoManager

# Initialize FastAPI app
app = FastAPI(title="HYRULE Server", description="TODO sync API for HYRULE")

# The page is served from this same origin, so only it may call the API.
# A stray browser tab on another site gets no cross-origin access to your list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8765", "http://localhost:8765"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Initialize TodoManager WITHOUT Slack notifications
# (Navi handles Slack notifications - we don't want duplicates)
todo_manager = TodoManager(config.TODO_PATH)
todo_manager.slack_notifier = None  # Disable Slack notifications for this instance


# Pydantic models for request/response
class AddTodoRequest(BaseModel):
    text: str
    section: Optional[str] = None
    due_date: Optional[str] = None


class TodoResponse(BaseModel):
    id: Optional[str]
    text: str
    completed: bool
    section: str
    due: Optional[str] = None
    overdue: bool = False
    due_today: bool = False


# Path to HYRULE.html
HYRULE_PATH = NAVI_DIR.parent / "HYRULE.html"


@app.get("/")
async def serve_hyrule():
    """Serve the HYRULE.html file"""
    if not HYRULE_PATH.exists():
        raise HTTPException(status_code=404, detail="HYRULE.html not found")
    return FileResponse(HYRULE_PATH, media_type="text/html")


@app.get("/api/todos")
async def get_todos(include_completed: bool = False):
    """
    Get all TODOs from TODO.md

    Returns list of todos with metadata
    """
    try:
        todos = todo_manager.get_todos(include_completed=include_completed)
        today = date.today()

        result = []
        for todo in todos:
            due_str = todo.get('metadata', {}).get('due')
            is_overdue = False
            is_due_today = False

            if due_str:
                try:
                    due_date = date.fromisoformat(due_str)
                    is_overdue = due_date < today and not todo['completed']
                    is_due_today = due_date == today
                except ValueError:
                    pass

            result.append({
                "id": todo.get('id'),
                "text": todo['text'],
                "completed": todo['completed'],
                "section": todo['section'],
                "due": due_str,
                "overdue": is_overdue,
                "due_today": is_due_today,
            })

        return {"todos": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/todos")
async def add_todo(request: AddTodoRequest):
    """
    Add a new TODO item

    Returns the created TODO with its ID
    """
    try:
        success, todo_id = todo_manager.add_todo(
            text=request.text,
            section=request.section,
            due_date=request.due_date
        )

        if success:
            return {
                "success": True,
                "id": todo_id,
                "message": f"Added TODO [{todo_id}]: {request.text}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to add TODO")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/todos/{todo_id}/complete")
async def complete_todo(todo_id: str):
    """
    Mark a TODO as complete by ID

    Args:
        todo_id: The TODO ID (e.g., "T7X2")
    """
    try:
        success, message = todo_manager.mark_complete(todo_id)

        if success:
            return {"success": True, "message": message}
        else:
            raise HTTPException(status_code=404, detail=message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quick-wins")
async def get_quick_wins():
    """
    Get quick win TODOs (reply, confirm, follow-up, etc.)
    """
    try:
        todos = todo_manager.get_quick_win_todos()

        result = []
        for todo in todos:
            result.append({
                "id": todo.get('id'),
                "text": todo['text'],
                "section": todo['section'],
            })

        return {"todos": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/overdue")
async def get_overdue():
    """
    Get overdue TODOs (past due date, not completed)
    """
    try:
        todos = todo_manager.get_overdue_todos()
        today = date.today()

        result = []
        for todo in todos:
            due_str = todo.get('metadata', {}).get('due')
            days_overdue = 0
            if due_str:
                try:
                    due_date = date.fromisoformat(due_str)
                    days_overdue = (today - due_date).days
                except ValueError:
                    pass

            result.append({
                "id": todo.get('id'),
                "text": todo['text'],
                "section": todo['section'],
                "due": due_str,
                "days_overdue": days_overdue,
            })

        return {"todos": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/due-today")
async def get_due_today():
    """
    Get TODOs due today
    """
    try:
        todos = todo_manager.get_due_today_todos()

        result = []
        for todo in todos:
            result.append({
                "id": todo.get('id'),
                "text": todo['text'],
                "section": todo['section'],
            })

        return {"todos": result, "count": len(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/summary")
async def get_summary():
    """
    Get TODO summary stats
    """
    try:
        grouping = todo_manager.get_grouping_summary()
        all_todos = todo_manager.get_todos(include_completed=True)
        incomplete = todo_manager.get_todos(include_completed=False)

        total = len(all_todos)
        complete = total - len(incomplete)
        percentage = int((complete / total) * 100) if total > 0 else 0

        return {
            "total": total,
            "complete": complete,
            "incomplete": len(incomplete),
            "percentage": percentage,
            "overdue_count": grouping['overdue_count'],
            "due_today_count": grouping['due_today_count'],
            "quick_win_count": grouping['quick_win_count'],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "hyrule-server"}


def main():
    """Run the server"""
    print("=" * 50)
    print("HYRULE Server starting...")
    print(f"HYRULE.html: {HYRULE_PATH}")
    print(f"TODO.md: {todo_manager.todo_path}")
    print("=" * 50)
    print()
    print("Open http://localhost:8765 in your browser")
    print("Press Ctrl+C to stop")
    print()

    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
