import sqlite3
import streamlit as st
from datetime import datetime

DB = r"C:\Users\GM612CD\PycharmProjects\UC_Agentic_AI_DLP\Modules\database.db"

st.set_page_config(page_title="DLP Requests Manager", layout="wide")

st.sidebar.title("📌 Menu")
menu = st.sidebar.radio("Select Option", ["View All", "Add New", "Edit", "Delete"])

# ---------- Shared function ----------
def get_all_requests():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM requests")
    rows = c.fetchall()
    conn.close()
    return rows

# ---------- View ----------
if menu == "View All":
    st.header("📄 All Requests")
    rows = get_all_requests()
    if rows:
        st.dataframe(
            rows,
            use_container_width=True,
        )
    else:
        st.info("No requests found.")

# ---------- Add New ----------
elif menu == "Add New":
    st.header("➕ Add New Request")

    with st.form("add_request_form"):
        employee = st.text_input("Employee Email")
        req_type = st.selectbox("Request Type", ["Email", "Eeb_upload", "Instant_message"])
        details = st.text_area("Details (Subject/Body)")
        destination = st.text_input("Destination (Recipient/URL)")
        status = st.selectbox("Status", ["Pending", "Auto Approved", "Escalated", "Rejected"])
        comment = st.text_input("Initial Comment (Optional)")

        submitted = st.form_submit_button("Submit Request")

        if submitted:
            if not employee or not details:
                st.error("Employee email and details are required!")
            else:
                conn = sqlite3.connect(DB)
                c = conn.cursor()
                try:
                    c.execute(
                        """INSERT INTO requests 
                        (employee, datetime, type, details, destination, status, comment, attachment) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            employee,
                            datetime.now(),
                            req_type,
                            details,
                            destination,
                            status,
                            comment,
                            None,
                        ),
                    )
                    conn.commit()
                    st.success("Request added successfully!")
                except sqlite3.Error as e:
                    st.error(f"Database error: {e}")
                finally:
                    conn.close()

# ---------- Edit ----------
elif menu == "Edit":
    st.header("✏️ Edit a Request")

    rows = get_all_requests()
    ids = [row[0] for row in rows]

    if not ids:
        st.info("No requests to edit.")
    else:
        selected_id = st.selectbox("Select Request ID", ids)

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM requests WHERE id = ?", (selected_id,))
        request = c.fetchone()
        conn.close()

        if request:
            with st.form("edit_request_form"):
                # Display existing values in editable fields
                employee = st.text_input("Employee Email", value=request[1])

                # Safely get request type (handle unexpected values)
                request_types = ["Email", "Eeb_upload", "Instant_message"]
                current_type = request[3] if request[3] in request_types else "Email"
                req_type = st.selectbox(
                    "Request Type",
                    request_types,
                    index=request_types.index(current_type)
                )

                details = st.text_area("Details (Subject/Body)", value=request[4])
                destination = st.text_input("Destination (Recipient/URL)", value=request[5])

                # Safely get status (handle unexpected values)
                status_options = ["Pending", "Auto Approved", "Escalated", "Rejected"]
                current_status = request[6] if request[6] in status_options else "Pending"
                status = st.selectbox(
                    "Status",
                    status_options,
                    index=status_options.index(current_status)
                )

                comment = st.text_input("Comment", value=request[7] if request[7] else "")

                # Submit button (FIXED: Added proper form_submit_button)
                submitted = st.form_submit_button("Update Request")

                if submitted:
                    if not employee or not details:
                        st.error("Employee email and details are required!")
                    else:
                        conn = sqlite3.connect(DB)
                        c = conn.cursor()
                        try:
                            c.execute(
                                """UPDATE requests SET
                                employee = ?,
                                type = ?,
                                details = ?,
                                destination = ?,
                                status = ?,
                                comment = ?
                                WHERE id = ?""",
                                (
                                    employee,
                                    req_type,
                                    details,
                                    destination,
                                    status,
                                    comment,
                                    selected_id
                                ),
                            )
                            conn.commit()
                            st.success(f"Request ID {selected_id} updated successfully!")
                        except sqlite3.Error as e:
                            st.error(f"Database error: {e}")
                        finally:
                            conn.close()

# ---------- Delete ----------
elif menu == "Delete":
    st.header("🗑️ Delete a Request")

    rows = get_all_requests()
    ids = [row[0] for row in rows]

    if not ids:
        st.info("No requests to delete.")
    else:
        selected_id = st.selectbox("Select Request ID", ids)

        if st.button("Delete Request"):
            conn = sqlite3.connect(DB)
            c = conn.cursor()
            c.execute("DELETE FROM requests WHERE id = ?", (selected_id,))
            conn.commit()
            conn.close()
            st.success(f"Request ID {selected_id} deleted.")