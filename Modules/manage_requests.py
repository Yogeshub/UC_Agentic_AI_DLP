import sqlite3
import streamlit as st

DB = r"C:\Users\GM612CD\PycharmProjects\UC_Agentic_AI_DLP\Modules\database.db"

st.set_page_config(page_title="DLP Requests Manager", layout="wide")

st.sidebar.title("📌 Menu")
menu = st.sidebar.radio("Select Option", ["View All", "Edit", "Delete"])

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

        if request:
            new_status = st.selectbox("Update Status", ["Pending", "Auto Approved", "Escalated", "Rejected"], index=0)
            new_comment = st.text_input("Add/Update Comment", value=request[7] if len(request) > 7 else "")

            if st.button("Update Request"):
                c.execute(
                    "UPDATE requests SET status = ?, comment = ? WHERE id = ?",
                    (new_status, new_comment, selected_id),
                )
                conn.commit()
                st.success(f"Request ID {selected_id} updated.")
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

