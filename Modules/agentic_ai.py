import os
import httpx
import win32com.client
from dotenv import load_dotenv
from typing import Dict, Optional, Any
from pydantic import BaseModel, Field

from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq
from langchain.tools import BaseTool

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL", "mixtral-8x7b-32768")
http_client = httpx.Client(verify=False)

# ------------------------------ Tool Input Schemas and Implementations

class SimilarityInput(BaseModel):
    details: str = Field(..., description="Email content to check")
    request_id: int = Field(..., description="Request ID")

class SimilarityTool(BaseTool):
    name = "check_similarity"
    description = "Check if email is duplicate. Returns 'DUPLICATE' or 'NEW'."
    args_schema = SimilarityInput

    def _run(self, details: str, request_id: int) -> str:
        from db_utils import find_duplicate_request, update_status, save_to_memory
        if find_duplicate_request(details):
            update_status(request_id, "Auto Approved")
            save_to_memory(details)
            return "DUPLICATE"
        return "NEW"


class SensitivityInput(BaseModel):
    details: str = Field(..., description="Email content to check")
    attachment: Optional[str] = Field(None, description="Attachment file path")

class SensitivityTool(BaseTool):
    name = "check_sensitivity"
    description = "Check for sensitive content. Returns True if sensitive, False otherwise."
    args_schema = SensitivityInput

    def _run(self, details: str, attachment: Optional[str] = None) -> bool:
        from doc_checker import classify_document
        sensitive_words = ["confidential", "secret", "salary", "ssn", "passport"]
        text_sensitive = any(w in details.lower() for w in sensitive_words)
        file_sensitive = False
        if attachment:
            try:
                result = classify_document(attachment)
                file_sensitive = result.get("sensitive", False)
            except Exception:
                file_sensitive = True  # Assume sensitive if error reading attachment
        return text_sensitive or file_sensitive


class StatusInput(BaseModel):
    request_id: int = Field(..., description="Request ID")
    status: str = Field(..., description="New status to set")
    comments: Optional[str] = Field(None, description="Optional comments")

class StatusTool(BaseTool):
    name = "mark_status"
    description = "Update request status and comments in database."
    args_schema = StatusInput

    def _run(self, request_id: int, status: str, comments: Optional[str] = None) -> str:
        from db_utils import update_status
        update_status(request_id, status)
        # Assuming you have a function to update comments if needed; else skip
        if comments:
            from db_utils import update_comments
            update_comments(request_id, comments)
        return f"Status updated to {status}"


class EscalationInput(BaseModel):
    employee: str = Field(..., description="Employee name")
    manager_email: str = Field(..., description="Manager's email")
    request_id: int = Field(..., description="Request ID")

class EscalationTool(BaseTool):
    name = "send_escalation_email"
    description = "Send escalation email via Outlook."
    args_schema = EscalationInput

    def _run(self, employee: str, manager_email: str, request_id: int) -> str:
        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.To = manager_email
            mail.Subject = f"DLP Escalation: Request {request_id}"
            mail.Body = f"Request {request_id} from employee {employee} requires manual review."
            mail.Send()
            return "Escalation email sent successfully"
        except Exception as e:
            return f"Escalation failed: {str(e)}"


# ------------------------------ Agent Creation

def create_agents():
    llm = ChatGroq(
        temperature=0,
        model_name=CHAT_MODEL,
        groq_api_key=GROQ_API_KEY,
        http_client=http_client
    )

    def make_tool(tool_instance: BaseTool) -> dict:
        return {
            "name": tool_instance.name,
            "func": tool_instance._run,
            "description": tool_instance.description
        }

    similarity_tool = SimilarityTool()
    sensitivity_tool = SensitivityTool()
    status_tool = StatusTool()
    escalation_tool = EscalationTool()

    duplicate_checker = Agent(
        role="Duplicate Email Detector",
        goal="Identify duplicate requests",
        backstory="Detects if a request is a duplicate of approved requests",
        tools=[make_tool(similarity_tool)],
        llm=llm,
        verbose=True
    )

    sensitivity_analyzer = Agent(
        role="Content Sensitivity Analyzer",
        goal="Detect sensitive content in emails",
        backstory="Checks email body and attachments for sensitive info",
        tools=[make_tool(sensitivity_tool)],
        llm=llm,
        verbose=True
    )

    approval_manager = Agent(
        role="DLP Approval Manager",
        goal="Approve safe requests or escalate sensitive ones",
        backstory="Handles approval and escalation workflows",
        tools=[make_tool(status_tool), make_tool(escalation_tool)],
        llm=llm,
        verbose=True
    )

    return duplicate_checker, sensitivity_analyzer, approval_manager


# ------------------------------ Task Creation

def create_tasks(request: Dict[str, Any], agents: tuple):
    duplicate_checker, sensitivity_analyzer, approval_manager = agents

    tasks = [
        Task(
            description=f"Check if request ID {request['id']} is a duplicate",
            agent=duplicate_checker,
            expected_output="DUPLICATE or NEW",
            context=request
        ),
        Task(
            description=f"Analyze request ID {request['id']} for sensitive content",
            agent=sensitivity_analyzer,
            expected_output="True if sensitive, False otherwise",
            context=request
        ),
        Task(
            description=f"Approve or escalate request ID {request['id']}",
            agent=approval_manager,
            expected_output="Confirmation of approval or escalation",
            context=request
        )
    ]
    return tasks


# ------------------------------ Main Processing Logic

def process_request(request: Dict[str, Any]):
    from db_utils import get_manager_email, update_status

    agents = create_agents()
    tasks = create_tasks(request, agents)
    crew = Crew(
        agents=list(agents),
        tasks=tasks,
        process=Process.sequential,
        verbose=2
    )
    result = crew.kickoff()
    print(f"Processed request {request['id']}: {result}")

    # After tasks run, check if manual review is needed
    # If yes, get manager email and send escalation
    # This can be part of approval_manager tool or handled here as needed


def run_agentic_ai():
    print("Starting DLP Agent...")
    from db_utils import get_pending_emails, update_status, get_manager_email

    pending_requests = get_pending_emails()
    if not pending_requests:
        print("No pending requests found.")
        return

    print(f"Found {len(pending_requests)} requests to process")

    for req in pending_requests:
        try:
            request = {
                "id": req[0],
                "employee": req[1],
                "datetime": req[2],
                "type": req[3],
                "details": req[4],
                "destination": req[5],
                "attachment": req[8] if len(req) > 8 else None
            }
            process_request(request)
        except Exception as e:
            print(f"[Error] Failed processing request {req[0]}: {str(e)}")
            update_status(req[0], "Error in processing")


if __name__ == "__main__":
    run_agentic_ai()
