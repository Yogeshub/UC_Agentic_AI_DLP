import streamlit as st
from emp_db_ops import DatabaseManager

def show_employee_management():
    db = DatabaseManager()

    st.title("👥 Employee Management Portal")

    tab1, tab2, tab3, tab4 = st.tabs([
        "➕ Add Relationship",
        "📋 View All",
        "✏️ Update",
        "🗑️ Delete"
    ])

    # ➕ Add Relationship
    with tab1:
        st.subheader("Add New Employee-Manager Relationship")
        with st.form("add_form", clear_on_submit=True):
            emp_email = st.text_input("Employee Email", help="Company email address")
            mgr_email = st.text_input("Manager Email", help="Manager's company email")

            if st.form_submit_button("Add Relationship"):
                if emp_email and mgr_email:
                    if db.add_employee(emp_email, mgr_email):
                        st.success("Relationship added successfully!")
                    else:
                        st.error("Employee already exists in database")
                else:
                    st.warning("Both emails are required")

    # 📋 View All
    with tab2:
        st.subheader("Current Employee-Manager Relationships")
        employees = db.get_all_employees()

        if employees:
            st.dataframe(
                employees,
                column_config={
                    "employee_email": "Employee Email",
                    "manager_email": "Manager Email"
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No employee relationships found in database")

    # ✏️ Update
    with tab3:
        st.subheader("Update Manager for Employee")
        employees = db.get_all_employees()

        if employees:
            employee_emails = [e["employee_email"] for e in employees]
            selected_emp = st.selectbox(
                "Select Employee",
                employee_emails,
                index=None
            )

            if selected_emp:
                current_manager = next(
                    (e["manager_email"] for e in employees if e["employee_email"] == selected_emp),
                    ""
                )

                with st.form("update_form"):
                    new_manager = st.text_input(
                        "New Manager Email",
                        value=current_manager
                    )

                    if st.form_submit_button("Update Relationship"):
                        if db.update_employee(selected_emp, new_manager):
                            st.success("Relationship updated successfully!")
                            st.rerun()
                        else:
                            st.error("Update failed")
        else:
            st.info("No employees available to update")

    # 🗑️ Delete
    with tab4:
        st.subheader("Remove Employee Relationship")
        employees = db.get_all_employees()

        if employees:
            employee_emails = [e["employee_email"] for e in employees]
            selected_emp = st.selectbox(
                "Select Employee to Remove",
                employee_emails,
                index=None
            )

            if selected_emp:
                if st.button("Confirm Deletion", type="primary"):
                    if db.delete_employee(selected_emp):
                        st.success("Employee removed successfully!")
                        st.rerun()
                    else:
                        st.error("Deletion failed")
        else:
            st.info("No employees available to delete")
