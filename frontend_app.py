import streamlit as st
import sqlite3
from datetime import datetime
from emp_ui import show_employee_management

DB = "database.db"

# ---------- Navigation ----------
st.sidebar.title("Agentic AI DLP")
page = st.sidebar.radio("Navigation", [
    "📧 Request Dashboard",
    "👥 Employee Management"
])

if page == "👥 Employee Management":
    show_employee_management()
    st.stop()  # Stop execution here to only show employee UI

# ---------- DB HELPERS ----------
def get_requests_by_status(status):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, employee, datetime, type, details, destination FROM requests WHERE status = ?", (status,))
    rows = c.fetchall()
    conn.close()
    return rows

def update_request(id, status, comment):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE requests SET status = ?, comment = ? WHERE id = ?", (status, comment, id))
    conn.commit()
    conn.close()

# ---------- UI ----------
st.set_page_config(page_title="Agentic AI DLP", layout="wide")
st.title("📧 Agentic AI DLP Frontend")

tab1, tab2, tab3 = st.tabs(["📌 Pending", "✅ Responded", "🤖 Auto Approved"])

# ---------- Awaiting Response Tab ----------
with tab1:
    st.subheader("Pending")

    pending = get_requests_by_status("Pending")

    if pending:
        # Table header
        cols = st.columns([1, 2, 2, 1, 3, 2, 2])  # adjust widths
        cols[0].write("**ID**")
        cols[1].write("**Employee**")
        cols[2].write("**Date/Time**")
        cols[3].write("**Type**")
        cols[4].write("**Details**")
        cols[5].write("**Destination**")
        cols[6].write("**Action**")

        for row in pending:
            id, employee, dt, typ, details, destination = row

            cols = st.columns([1, 2, 2, 1, 3, 2, 2])

            cols[0].write(id)
            cols[1].write(employee)
            cols[2].write(dt)
            cols[3].write(typ)
            cols[4].write(details)
            cols[5].write(destination)

            with cols[6]:
                with st.form(f"form_{id}"):
                    comment = st.text_input("Comment", key=f"comment_{id}")
                    submitted = st.form_submit_button("✅ Approve")
                    if submitted:
                        update_request(id, "Responded", comment)
                        st.success(f"Approved ID {id} with comment: {comment}")
                        st.rerun()

    else:
        st.info("✅ No pending requests!")

# ---------- Responded Tab ----------
with tab2:
    st.subheader("Responded Requests")
    responded = get_requests_by_status("Responded")
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
