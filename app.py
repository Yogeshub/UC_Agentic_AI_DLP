import streamlit as st
from db_utils import insert_email, get_pending_emails, update_status, save_to_memory
from agentic_ai import create_graph

st.title("📧 Groq Agentic DLP Demo")

if st.button("Insert Dummy"):
    insert_email("vendor@abc.com", "external@xyz.com", "Specs", "Contains client salary info.")
    st.success("Inserted.")

graph = create_graph()

pending = get_pending_emails()

for row in pending:
    id, sender, recipient, subject, body, status, created = row
    st.write(f"### {subject} | ID: {id}")
    st.write(body)

    result = graph.invoke({"messages": [{"role": "user", "content": body}]})
    output = result["messages"][-1].content

    st.write(f"Agent decision: {output}")

    if "True" in output:
        update_status(id, "Auto-Approved")
        save_to_memory(body)
        st.success("✅ Auto-approved.")
    elif "Sensitive" in output:
        st.warning("⚠️ Escalate to manager.")
    elif "Safe" in output:
        if st.button(f"Approve {id}"):
            update_status(id, "Approved")
            save_to_memory(body)
            st.success("✅ Approved.")
