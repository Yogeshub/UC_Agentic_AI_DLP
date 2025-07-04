# import sqlite3, time, os, httpx
# from datetime import datetime, timedelta
# from langchain_groq import ChatGroq
# from langchain_core.prompts import ChatPromptTemplate
# from dotenv import load_dotenv
# from langchain.tools import StructuredTool
# from langchain.agents import AgentExecutor, create_openai_functions_agent
# from langchain_core.prompts import ChatPromptTemplate
# from langchain import hub
# import os
# import re
#
# load_dotenv()
#
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# CHAT_MODEL = os.getenv("CHAT_MODEL")
#
# DB = "database.db"
#
# http_client = httpx.Client(verify=False)
#
# from db_utils import (
#     get_pending_emails,
#     get_manager_email,
#     update_status,
#     is_older_than_24hrs
# )
#
# import smtplib
#
# # ------------------------------
# # Example similarity checker (placeholder)
# def check_similarity(details):
#     """
#     Check if the email details match previous emails to detect duplicates.
#     Returns 'DUPLICATE' if similar, else 'NEW'.
#     """
#     print(f"[Tool] check_similarity called with: {details}")
#     if "repeat" in details.lower():
#         print("[Tool] Marked as DUPLICATE")
#         return "DUPLICATE"
#     print("[Tool] Marked as NEW")
#     return "NEW"
#
# # ------------------------------
# # Example sensitivity checker (placeholder)
# def check_sensitivity(details, attachment=None):
#     """
#     Check if the email content or attachment contains sensitive information.
#     Returns True if sensitive content is found, else False.
#     """
#     print(f"[Tool] check_sensitivity called with: {details} and attachment: {attachment}")
#     sensitive_words = ["confidential", "secret", "salary"]
#     if any(word in details.lower() for word in sensitive_words):
#         print("[Tool] Found sensitive content!")
#         return True
#     print("[Tool] Not sensitive")
#     return False
#
# def mark_status(email_id, status):
#     """Update the status of the email in DB."""
#     print(f"[Tool] Updating status for ID {email_id} to {status}")
#     update_status(email_id, status)
#     return f"Status updated to {status}"
#
# # ------------------------------
# # Escalation mailer
# def send_escalation_email(employee, manager_manager_email, request_id):
#     """
#     Send an escalation email to the manager's manager if a request is pending over 24 hrs.
#     """
#     subject = f"[ESCALATION] Approval pending for request {request_id}"
#     body = f"The request ID {request_id} from {employee} is pending over 24 hrs. Please review urgently."
#     print(f"Escalation Email → To: {manager_manager_email}\nSubject: {subject}\nBody: {body}\n")
#     # Here you’d connect real SMTP
#     return f"Escalation mail sent to {manager_manager_email}"
#
# # ------------------------------
# # Tool Wrappers
# tools = [
#     StructuredTool.from_function(check_similarity),
#     StructuredTool.from_function(check_sensitivity),
#     StructuredTool.from_function(mark_status),
#     StructuredTool.from_function(send_escalation_email),
# ]
#
# system_instructions = """
# You are a DLP Automation Agent. You MUST always use the tools.
#
# For every request:
# - First call `check_similarity` on the email details.
# - If result is DUPLICATE: call `mark_status` with 'Auto Approved'.
# - If result is NEW: call `check_sensitivity` on details.
#   - If NOT sensitive: call `mark_status` with 'Auto Approved'.
#   - If sensitive: DO NOTHING. Manager will review.
# - If the request is older than 24 hrs: always call `send_escalation_email` to escalate.
#
# Always explain each step and use the tools!
# """
#
# # ------------------------------
# # Agent
# llm = ChatGroq(groq_api_key=GROQ_API_KEY, model=CHAT_MODEL,http_client=http_client)
# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_instructions),
#     ("human", "{input}\n{agent_scratchpad}")
# ])
# agent = create_openai_functions_agent(llm, tools, prompt)
# agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
#
# # ------------------------------
# # Orchestration Loop
# # def run_agentic_ai():
# #     requests = get_pending_emails()
# #     print(f"[Main] Found {len(requests)} requests: {requests}")
# #     for r in requests:
# #         id, employee, dt, typ, details, dest, status, comment, attachment = r
# #         if is_older_than_24hrs(dt):
# #             _, manager_manager = get_manager_email(employee)
# #             input_txt = f"This request ID {id} is older than 24 hrs. Escalate to manager's manager {manager_manager}."
# #             print(f"[Main] Invoking escalation for: {input_txt}")
# #             result = agent_executor.invoke({"input": input_txt})
# #             print(f"[Main] Result: {result}")
# #         else:
# #             input_txt = f"Check request ID {id} for similarity and sensitivity. Details: {details}. Attachment: {attachment if attachment else 'None'}"
# #             print(f"[Main] Invoking checks for: {input_txt}")
# #             result = agent_executor.invoke({"input": input_txt})
# #             print(f"[Main] Result: {result}")
#
# def run_agentic_ai():
#     requests = get_pending_emails()
#     print(f"[Main] Found {len(requests)} requests.")
#     for r in requests:
#         id, employee, dt, typ, details, dest, status, comment, attachment = r
#
#         if is_older_than_24hrs(dt):
#             _, manager_manager = get_manager_email(employee)
#             input_txt = f"""
# This request ID {id} is older than 24 hrs.
# Escalate to manager's manager: {manager_manager}.
# """
#         else:
#             input_txt = f"""
# Check request ID {id}.
# Details: {details}
# Attachment: {attachment if attachment else 'None'}
# """
#
#         print(f"[Main] Sending to agent:\n{input_txt}")
#         result = agent_executor.invoke({"input": input_txt})
#         print(f"[Main] Agent result: {result}")
#
#
# if __name__ == "__main__":
#     run_agentic_ai()

### Langraph version of AI Agent

import os, httpx
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import tools_condition, ToolNode
from langchain.tools import StructuredTool
from db_utils import (
    get_pending_emails,
    get_manager_email,
    update_status,
    is_older_than_24hrs,
)
from doc_checker import classify_document


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHAT_MODEL = os.getenv("CHAT_MODEL")


http_client = httpx.Client(verify=False)


# ------------------------------
# Tools with print logs
def check_similarity(details):
    """Detect duplicate mails. Return DUPLICATE or NEW."""
    print(f"[Tool] check_similarity called: {details[:30]}")
    if "repeat" in details.lower():
        print("[Tool] DUPLICATE")
        return "DUPLICATE"
    print("[Tool] NEW")
    return "NEW"


# def check_sensitivity(details, attachment=None):
#     """Detect sensitive content. Return True/False."""
#     print(f"[Tool] check_sensitivity called: {details[:30]}")
#     sensitive_words = ["confidential", "secret", "salary"]
#     if any(w in details.lower() for w in sensitive_words):
#         print("[Tool] SENSITIVE")
#         return True
#     print("[Tool] Not Sensitive")
#     return False
def check_sensitivity(details, attachment=None):
    """
    Detect sensitive content in text and optional attachment.
    Return True if sensitive info is found.
    """
    print(f"[Tool] check_sensitivity called: {details[:30]}")

    # 1️⃣ Text check
    sensitive_words = ["confidential", "secret", "salary"]
    text_sensitive = any(w in details.lower() for w in sensitive_words)

    # 2️⃣ Attachment check
    file_sensitive = False
    if attachment:
        try:
            print(f"[Tool] Checking attachment: {attachment}")
            result = classify_document(attachment)
            file_sensitive = result["sensitive"]
            print(f"[Tool] Attachment classified as sensitive: {file_sensitive}")
        except Exception as e:
            print(f"[Tool] Error reading attachment: {e}")

    # 3️⃣ Final verdict
    if text_sensitive or file_sensitive:
        print("[Tool] Result: SENSITIVE")
        return True

    print("[Tool] Result: Not Sensitive")
    return False


def mark_status(email_id, status):
    """Update status of a mail in DB."""
    print(f"[Tool] Updating ID {email_id} to {status}")
    update_status(email_id, status)
    return f"Updated {email_id} to {status}"


def send_escalation_email(employee, manager_manager_email, request_id):
    """Send escalation email."""
    print(f"[Tool] Escalating request {request_id} to {manager_manager_email}")
    return f"Escalated to {manager_manager_email}"


tools = [
    StructuredTool.from_function(check_similarity),
    StructuredTool.from_function(check_sensitivity),
    StructuredTool.from_function(mark_status),
    StructuredTool.from_function(send_escalation_email),
]

# ------------------------------
# System instructions
sys_msg = SystemMessage(
    content="""
You are a DLP Automation Agent. You MUST always use tools.

For each request:
- Call `check_similarity` first.
- If DUPLICATE → call `mark_status` with 'Auto Approved'.
- If NEW → call `check_sensitivity`.
  - If NOT sensitive → call `mark_status` with 'Auto Approved'.
  - If sensitive → do nothing.
- If request older than 24hrs → call `send_escalation_email`.

"""
)

# ------------------------------
# LLM with tools bound
llm = ChatGroq(groq_api_key=GROQ_API_KEY, model=CHAT_MODEL, http_client=http_client)
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)


# ------------------------------
# Assistant Node
def assistant(state: MessagesState):
    result = llm_with_tools.invoke([sys_msg] + state["messages"])
    return {"messages": [result]}


# ------------------------------
# Create graph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")
graph = builder.compile()


# ------------------------------
# Run
def run_agentic_ai():
    requests = get_pending_emails()
    for r in requests:
        id, employee, dt, typ, details, dest, status, comment, attachment = r
        if is_older_than_24hrs(dt):
            _, manager_manager = get_manager_email(employee)
            user_msg = (
                f"Escalate request ID {id} to manager's manager {manager_manager}."
            )
        else:
            user_msg = f"Process request ID {id}: Check similarity, then sensitivity. Details: {details[:50]}..."
        print(f"[Main] Sending: {user_msg}")

        result = graph.invoke(
            {"messages": [{"role": "user", "content": user_msg}]},
            config={"recursion_limit": 5},
        )
        print(f"[Main] Result: {result}")


if __name__ == "__main__":
    run_agentic_ai()
