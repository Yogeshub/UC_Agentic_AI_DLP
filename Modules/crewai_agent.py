import os
import sqlite3
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from fuzzywuzzy import fuzz
import win32com.client

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "groq/llama-3-70b-8192")  # Adjust as needed

DB_FILE = "database.db"

# --- Database helper functions ---

def get_pending_emails():
    print("[DB] Fetching pending emails...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests WHERE status = 'Pending'")
    rows = cursor.fetchall()
    conn.close()
    print(f"[DB] Found {len(rows)} pending emails.")
    return rows

def update_status(request_id: int, status: str, comment: Optional[str] = None):
    print(f"[DB] Updating status for request {request_id} to '{status}'")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    if comment:
        cursor.execute("UPDATE requests SET status = ?, comment = ? WHERE id = ?", (status, comment, request_id))
    else:
        cursor.execute("UPDATE requests SET status = ? WHERE id = ?", (status, request_id))
    conn.commit()
    conn.close()


def get_manager_email(employee_email: str) -> Optional[str]:
    employee_email = employee_email.strip().lower()  # Normalize input
    print(f"[DB] Fetching manager for: '{employee_email}'")

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Debug: Print all employees (remove after testing)
        cursor.execute("SELECT employee_email, manager_email FROM employees")
        print("[DB] All records:", cursor.fetchall())

        # Main query
        cursor.execute("""
            SELECT manager_email FROM employees 
            WHERE lower(trim(employee_email)) = ?
        """, (employee_email,))

        row = cursor.fetchone()
        if row:
            print(f"[DB] Found manager: {row[0]}")
            return row[0]
        else:
            print(f"[DB] No manager found for: '{employee_email}'")
            return None

    except sqlite3.Error as e:
        print(f"[DB] Error: {e}")
        return None
    finally:
        conn.close()

def find_similar_approved(details: str, threshold: int = 85) -> bool:
    print("[DB] Checking for similar approved emails...")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT details FROM requests WHERE status IN ('Approved', 'Auto Approved')")
    approved_bodies = [row[0] for row in cursor.fetchall()]
    conn.close()
    for body in approved_bodies:
        score = fuzz.token_set_ratio(details, body)
        print(f"[Fuzzy] Similarity score: {score}")
        if score >= threshold:
            print("[Fuzzy] Similar email found.")
            return True
    print("[Fuzzy] No similar email found.")
    return False


def extract_text_from_attachment(filepath: str) -> str:

    if not filepath or not os.path.exists(filepath):
        print(f"[Attachment] File not found: {filepath}")
        return ""

    ext = os.path.splitext(filepath)[1].lower()
    text = ""

    try:
        if ext == ".txt":
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
        elif ext == ".pdf":
            import PyPDF2
            with open(filepath, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif ext == ".docx":
            # import docx
            # doc = docx.Document(filepath)
            import docx2txt
            text = docx2txt.process(filepath)  # Returns raw text
            print(text)
            # text = "\n".join(p.text for p in text.paragraphs)
        else:
            print(f"[Attachment] Unsupported file type: {ext}")
    except Exception as e:
        print(f"[Attachment] Error extracting text: {e}")

    return text

# --- Tool Input Schemas and Classes ---

class SimilarityInput(BaseModel):
    details: str = Field(..., description="Email content")
    request_id: int = Field(..., description="Request ID")

class SimilarityTool(BaseTool):
    name: str = "check_similarity"
    description: str = "Check if email is duplicate. Returns 'DUPLICATE' or 'NEW'."
    args_schema : type = SimilarityInput

    def _run(self, details: str, request_id: int) -> str:
        print(f"[Tool] Running SimilarityTool for request {request_id}")
        if find_similar_approved(details):
            update_status(request_id, "Auto Approved", "Duplicate of approved request")
            return "DUPLICATE"
        return "NEW"

class SensitivityInput(BaseModel):
    details: str = Field(..., description="Email content")
    attachment: Optional[str] = Field(None, description="Attachment file path")

class SensitivityTool(BaseTool):
    name: str = "check_sensitivity"
    description: str = "Check if email or attachment contains sensitive content."
    args_schema : type = SensitivityInput

    def _run(self, details: str, attachment: Optional[str] = None) -> bool:
        print(f"[Tool] Running SensitivityTool")
        sensitive_keywords = ["confidential", "secret", "salary", "ssn", "passport",
        "credit card", "bank account", "private", "restricted", "internal use only",
        "proprietary", "classified", "do not distribute", "personal data", "Account Number"]
        if any(word in details.lower() for word in sensitive_keywords):
            print("[Tool] Sensitive content found in text.")
            return True
        # Add attachment sensitivity check if needed
        if attachment:
            file_path = attachment.split("::")[0]
            print("[Tool] Attachment present.")
            attachment_text = extract_text_from_attachment(file_path)
            if any(word in attachment_text.lower() for word in sensitive_keywords):
                print("[Tool] Sensitive content found in attachment.")
                return True

        print("[Tool] No sensitive content found.")
        return False

class AutoApproveInput(BaseModel):
    request_id: int = Field(..., description="Request ID")

class AutoApproveTool(BaseTool):
    name: str = "auto_approve"
    description: str = "Auto-approve the request."
    args_schema: type = AutoApproveInput

    def _run(self, request_id: int) -> str:
        print(f"[Tool] Running AutoApproveTool for request {request_id}")
        update_status(request_id, "Auto Approved", "No sensitive content detected")
        return "Auto Approved"

class EscalateInput(BaseModel):
    employee: str = Field(..., description="Employee email")
    request_id: int = Field(..., description="Request ID")

class EscalateTool(BaseTool):
    name: str = "escalate"
    description: str = "Send escalation email to manager."
    args_schema : type = EscalateInput

    def _run(self, employee: str, request_id: int) -> str:
        print(f"[Tool] Running EscalateTool for request {request_id}")
        manager_email = get_manager_email(employee)
        if not manager_email:
            update_status(request_id, "Escalation Failed", "Manager email not found")
            return "Manager email not found"
        try:
            outlook = win32com.client.Dispatch("Outlook.Application")
            mail = outlook.CreateItem(0)
            mail.To = manager_email
            mail.Subject = f"DLP Escalation: Request {request_id}"
            mail.Body = (
                f"Dear Manager,\n\n"
                f"Request {request_id} from employee {employee} requires manual review.\n\n"
                "Please approve or reject this request using the DLP Streamlit dashboard:\n"
                "http://localhost:8501\n\n"
                "Regards,\nDLP Automation Agent"
            )
            mail.Send()
            update_status(request_id, "Escalated", "Escalation sent to manager")
            print("[Tool] Escalation email sent successfully.")
            return "Escalation email sent successfully"
        except Exception as e:
            update_status(request_id, "Escalation Failed", f"Error sending email: {str(e)}")
            print(f"[Tool] Escalation failed: {str(e)}")
            return f"Escalation failed: {str(e)}"

# --- LLM Setup ---

llm = LLM(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0,
    http_client_args={"verify": False}  # Disable SSL verification if needed
)

# --- Agents ---

duplicate_checker = Agent(
    role="Duplicate Checker",
    goal="Identify duplicate or previously approved requests",
    backstory="Detects if the current request is a duplicate of any previously approved requests.",
    tools=[SimilarityTool()],
    llm=llm,
    verbose=True
)

sensitivity_checker = Agent(
    role="Sensitivity Checker",
    goal="Detect sensitive content in requests",
    backstory="Analyzes email content and attachments to identify sensitive information.",
    tools=[SensitivityTool()],
    llm=llm,
    verbose=True
)

approval_manager = Agent(
    role="Approval Manager",
    goal="Auto-approve safe requests or escalate sensitive ones",
    backstory="Approves safe requests and escalates sensitive requests to managers.",
    tools=[AutoApproveTool(), EscalateTool()],
    llm=llm,
    verbose=True
)

# --- Workflow ---

def process_request(request: Dict[str, Any]):
    print(f"\n[Workflow] Processing request ID {request['id']}")

    # 1. Check duplicates
    duplicate_result = duplicate_checker.tools[0]._run(details=request["details"], request_id=request["id"])
    print(f"[Workflow] Duplicate check result: {duplicate_result}")
    if duplicate_result == "DUPLICATE":
        print(f"[Workflow] Request {request['id']} auto-approved as duplicate.")
        return

    # 2. Check sensitivity
    sensitive = sensitivity_checker.tools[0]._run(details=request["details"], attachment=request.get("attachment"))
    print(f"[Workflow] Sensitivity check result: {'Sensitive' if sensitive else 'Not sensitive'}")
    if not sensitive:
        approval_manager.tools[0]._run(request_id=request["id"])  # auto_approve
        print(f"[Workflow] Request {request['id']} auto-approved (no sensitive content).")
        return

    # 3. Escalate sensitive requests
    escalation_result = approval_manager.tools[1]._run(employee=request["employee"], request_id=request["id"])
    print(f"[Workflow] Request {request['id']} escalated: {escalation_result}")

def run_agentic_ai():
    print("[Main] Starting DLP Agent...")
    pending_requests = get_pending_emails()
    if not pending_requests:
        print("[Main] No pending requests found.")
        return

    print(f"[Main] Found {len(pending_requests)} requests to process")
    for req in pending_requests:
        request = {
            "id": req[0],
            "employee": req[1],
            "datetime": req[2],
            "type": req[3],
            "details": req[4],
            "destination": req[5],
            "attachment": req[8] if len(req) > 8 else None
        }
        try:
            process_request(request)
        except Exception as e:
            print(f"[Error] Failed processing request {request['id']}: {str(e)}")
            update_status(request["id"], "Error in processing")

if __name__ == "__main__":
    run_agentic_ai()
