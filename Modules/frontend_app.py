import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
from emp_ui import show_employee_management


DB = "database.db"

# ---------- Navigation ----------
st.sidebar.title("Agentic AI DLP")
st.logo(image="ey-logo-black.png", size="large")

page = st.sidebar.radio(
    "Navigation", ["📧 Request Dashboard", "👥 Employee Management"]
)

if page == "👥 Employee Management":
    show_employee_management()
    st.stop()  # Stop execution here to only show employee UI


# ---------- DB HELPERS ----------
def get_requests_by_status(status):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "SELECT id, employee, datetime, type, details, destination FROM requests WHERE status = ?",
        (status,),
    )
    rows = c.fetchall()
    conn.close()
    return rows

def get_all_pending_requests():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "SELECT id, employee, datetime, type, details, destination, status FROM requests WHERE status != 'Responded' AND status != 'Auto Approved'"
    )
    rows = c.fetchall()
    conn.close()
    return rows

def update_request(id, status, comment):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "UPDATE requests SET status = ?, comment = ? WHERE id = ?",
        (status, comment, id),
    )
    conn.commit()
    conn.close()

# Add this new helper function
def get_requests_by_statuses(statuses):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    placeholders = ','.join(['?'] * len(statuses))
    c.execute(
        f"SELECT id, employee, datetime, type, details, destination, status FROM requests WHERE status IN ({placeholders})",
        statuses
    )
    rows = c.fetchall()
    conn.close()
    return rows

# ---------- UI ----------
st.set_page_config(page_title="Agentic AI DLP", layout="wide")
st.title("📧 Agentic AI DLP Frontend")

# Create a top bar with proper spacing
top_col1, top_col2 = st.columns([1, 4])  # Adjusted column ratios

with top_col1:
    if st.button("🔄 Refresh Data", help="Refresh all data"):
        st.rerun()

tab1, tab2, tab3 = st.tabs(["📌 Pending", "✅ Responded", "🤖 Auto Approved"])

# Custom CSS for consistent row height and styling
st.markdown("""
<style>
    /* Consistent row height */
    div[data-testid="stHorizontalBlock"] {
        align-items: center;
        min-height: 48px !important;
    }

    /* Compact expander styling */
    div[data-testid="stExpander"] {
        margin: 0 !important;
    }

    /* Smaller comment input */
    div[data-testid="stExpander"] .stTextInput input {
        font-size: 12px;
        padding: 4px 8px;
        height: 28px;
    }

    /* Truncate long text */
    .truncate-text {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 200px;
    }
</style>
""", unsafe_allow_html=True)
# ---------- Awaiting Response Tab ----------
with tab1:
    st.subheader("Review Requests")

    # Get all requests except approved statuses
    review_requests = get_requests_by_statuses(["Pending", "Escalated", "NEW", "Needs Revision"])

    if review_requests:
        # Table header with adjusted column widths
        cols = st.columns([0.8, 1.8, 1.8, 0.8, 2.5, 1.8, 0.8, 1.2])
        headers = ["ID", "Employee", "Date/Time", "Type", "Details", "Destination", "Status", "Actions"]

        for col, header in zip(cols, headers):
            col.write(f"**{header}**")

        for row in review_requests:
            id, employee, dt, typ, details, destination, status = row
            cols = st.columns([0.8, 1.8, 1.8, 0.8, 2.5, 1.8, 0.8, 1.2])

            # Data columns with truncated text
            cols[0].write(f'<div class="truncate-text">{id}</div>', unsafe_allow_html=True)
            cols[1].write(f'<div class="truncate-text">{employee}</div>', unsafe_allow_html=True)
            cols[2].write(f'<div class="truncate-text">{dt}</div>', unsafe_allow_html=True)
            cols[3].write(f'<div class="truncate-text">{typ}</div>', unsafe_allow_html=True)
            cols[4].write(f'<div class="truncate-text">{details}</div>', unsafe_allow_html=True)
            cols[5].write(f'<div class="truncate-text">{destination}</div>', unsafe_allow_html=True)
            cols[6].write(f'<div class="truncate-text">{status}</div>', unsafe_allow_html=True)

            # Actions Column
            with cols[7]:
                if status not in ["Approved", "Auto Approved"]:
                    with st.expander("⚙️", expanded=False):
                        comment = st.text_input(
                            "Comments",
                            key=f"comment_{id}",
                            help="Enter comments or action reason"
                        )

                        # Action buttons
                        btn_col1, btn_col2, btn_col3 = st.columns(3)
                        with btn_col1:
                            if st.button("✓", key=f"approve_{id}", help="Approve"):
                                update_request(id, "Approved", comment)
                                st.rerun()
                        with btn_col2:
                            if st.button("✗", key=f"reject_{id}", help="Reject"):
                                update_request(id, "Rejected", comment)
                                st.rerun()
                        # with btn_col3:
                        #     if st.button("↻", key=f"revise_{id}", help="Request Revision"):
                        #         update_request(id, "Needs Revision", comment)
                        #         st.rerun()
                else:
                    st.write("✅", help="Already approved")

    else:
        st.info("✅ No requests needing review")


# ... (rest of the code remains same)

# Add this new helper function
def get_requests_by_statuses(statuses):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    placeholders = ','.join(['?'] * len(statuses))
    c.execute(
        f"SELECT id, employee, datetime, type, details, destination, status FROM requests WHERE status IN ({placeholders})",
        statuses
    )
    rows = c.fetchall()
    conn.close()
    return rows

#
# ---------- Approved Tab ----------
with tab2:
    st.subheader("Responded Requests")
    responded = get_requests_by_status("Approved")
    if responded:
        st.dataframe(
            {
                "ID": [r[0] for r in responded],
                "Employee": [r[1] for r in responded],
                "DateTime": [r[2] for r in responded],
                "Type": [r[3] for r in responded],
                "Details": [r[4] for r in responded],
                "Destination": [r[5] for r in responded],
            }
        )
    else:
        st.info("✅ No responded requests yet!")

# ---------- Auto Approved Tab ----------
with tab3:
    st.subheader("Auto Approved Requests")
    auto = get_requests_by_status("Auto Approved")
    if auto:
        st.dataframe(
            {
                "ID": [r[0] for r in auto],
                "Employee": [r[1] for r in auto],
                "DateTime": [r[2] for r in auto],
                "Type": [r[3] for r in auto],
                "Details": [r[4] for r in auto],
                "Destination": [r[5] for r in auto],
            }
        )
    else:
        st.info("✅ No auto approved requests yet!")




#CSS code for the page
csscode = """
    <style>
    .stApp {
        background-color: #2e2e38;
    }
    .stTextInput>div>div>input {
        background-color: white;
        color: black;
    }
    .stTextInput {
             padding-left:2rem
    }
    .stButton>button {
        background-color: #ffe600;
        color: black;
    }
    .stButton {
            padding: 2rem;
    }
    .st-emotion-cache-1104ytp {

            color:white;
    }
    .st-emotion-cache-wq5ihp {
            color:white
    }
    .stcon1{
            padding: 6 rem;
            }

    .stColumn st-emotion-cache-t74pzu eu6p4el2{
            padding: 4rem;
            }

    .st-emotion-cache-1uixxvy{
            color: white;
            }
    .stMarkdown {
        color: white;
    }
</style>
"""
# Custom CSS for background color
st.markdown(csscode, unsafe_allow_html=True)