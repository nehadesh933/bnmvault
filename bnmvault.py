import streamlit as st
import pandas as pd
import altair as alt
import pymongo

st.title("BNM VAULT")

def connect_db():
    """Connect to MongoDB Atlas."""
    conn = pymongo.MongoClient("mongodb+srv://nehadesh2003:123@cluster.m0jtccy.mongodb.net/")
    db = conn['bnmvault']
    return db

# Function to find the current user details and cache the result
@st.cache_resource()
def get_username():
    return {'username': None}

# Function to store the current user details
def set_username(user):
    username = get_username()
    username['username'] = user

# Function to check the login status and cache the result
@st.cache_resource()
def get_login_status():
    return [False]

def student_login(username, password):
    db = connect_db()
    user_collection = db.students
    user = user_collection.find_one({"USN": username, "Password": password})

    return 1 if user else 0

# Function to check admin login credentials
def admin_login(user, username, password):
    return username == user['Username'] and password == user['Password']

def set_login_status(logged_in):
    login_status = get_login_status()
    login_status.clear()
    login_status.append(logged_in)

# Function to add a student
def add_student():
    db = connect_db()
    user_col = db['students']
    st.subheader("Add Student")
    student_usn = st.text_input("USN")
    student_pswd = st.text_input("Password")
    student_FName = st.text_input("First Name")
    student_Lname = st.text_input("Last Name")
    student_age = st.text_input("Age")
    student_gen = st.text_input("Gender")
    student_dob = st.date_input("DOB")
    student_mail = st.text_input("Email")
    add_student_button = st.button("Add Student")

    if add_student_button:
        user = user_col.find_one({"USN": student_usn})
        if not user:
            user_col.insert_one({"USN": student_usn, "Password": student_pswd, "First Name": student_FName,
                                 "Last Name": student_Lname, "Age": student_age, "Gender": student_gen,
                                 "DOB": str(student_dob), "Email": student_mail, "Fees": {"Status": "Pending"}})
            st.success("Student added successfully!")
        else:
            st.error("User already exists.")

# Function to add attendance
def add_attendance():
    db = connect_db()
    user_col = db['students']
    st.subheader("Add Attendance")
    date = st.date_input("Date")
    student_usn = st.text_input("Student USN")
    subject_options = ["Math", "Operating System", "English", "Computer Organization"]
    selected_subject = st.selectbox("Select Subject", subject_options)
    classes_present = st.number_input("Classes Present", min_value=0)
    total_classes = st.number_input("Total Classes", min_value=0)

    attendance_percentage = (classes_present / total_classes) * 100 if total_classes > 0 else 0
    st.write(f"Attendance Percentage: {attendance_percentage:.2f}%")
    num_absent = total_classes - classes_present
    st.write(f"Total Classes Absent: {num_absent}")

    add_attendance_button = st.button("Add Attendance")

    if add_attendance_button:
        user = user_col.find_one({"USN": student_usn})
        if user:
            user_col.update_one({"USN": student_usn},
                                {'$set': {f'Attendance.{selected_subject}': {'Classes Present': classes_present,
                                                                             'Total Classes': total_classes}}})
            st.success("Attendance updated successfully!")
            render_attendance_page(student_usn)  # Call the function to display attendance
        else:
            st.error("User does not exist.")

# Function to add marks
def add_marks():
    db = connect_db()
    user_col = db['students']
    st.subheader("Add Marks")
    student_usn = st.text_input("Student USN")
    subject_options = ["Math", "Operating System", "English", "Computer Organization"]
    selected_subject = st.selectbox("Select Subject", subject_options)
    marks_obtained = st.number_input("Marks Obtained", min_value=0, max_value=100)
    total_marks = st.number_input("Total Marks", min_value=0, max_value=100)
    add_marks_button = st.button("Add Marks")

    if add_marks_button:
        user = user_col.find_one({"USN": student_usn})
        if user:
            user_col.update_one({"USN": student_usn},
                                {'$set': {f'Marks.{selected_subject}': {'Marks Obtained': marks_obtained,
                                                                        'Total Marks': total_marks}}})
            st.success("Marks updated successfully!")
            render_marks_page(student_usn)  # Call the function to display marks
        else:
            st.error("User does not exist.")

def main():
    logged_in = get_login_status()[0]

    if not logged_in:
        render_login_page()
    elif logged_in == 'Student':
        render_user_page()
    elif logged_in == 'Admin':
        render_admin_page()

def render_login_page():
    db = connect_db()
    user_collection = db.students
    st.title("Login Portal")

    login_option = st.radio("Select User Type", ["Student", "Admin"])

    if login_option == "Student":
        st.subheader("Student Login")
        username = st.text_input("USN")
        password = st.text_input("Password", type="password")
        submitted = st.button("Login")

        if submitted:
            user = user_collection.find_one({"USN": username})
            if user and student_login(username, password):
                set_username(username)
                set_login_status('Student')
                st.experimental_rerun()
            else:
                st.error("Invalid student credentials")

    elif login_option == "Admin":
        st.subheader("Admin Login")
        admin_username = st.text_input("Admin Username")
        admin_password = st.text_input("Admin Password", type="password")
        admin_submitted = st.button("Login as Admin")

        if admin_submitted:
            user = user_collection.find_one({"Username": admin_username})
            if user and admin_login(user, admin_username, admin_password):
                st.success("Admin login successful!")
                set_login_status('Admin')
                st.experimental_rerun()
            else:
                st.error("Invalid admin credentials")

def render_admin_page():
    st.title("Admin Dashboard")
    menu_options = ["Add Student", "Add Attendance", "Add Marks", "Search by USN", "Add Fees Status"]
    selected_option = st.sidebar.selectbox("Select an Option", menu_options)

    if selected_option == "Add Student":
        add_student()
    elif selected_option == "Add Attendance":
        add_attendance()
    elif selected_option == "Add Marks":
        add_marks()
    elif selected_option == "Search by USN":
        search_by_usn()
    elif selected_option == "Add Fees Status":
        render_fees_page

    if st.sidebar.button("Logout"):
        set_login_status(False)
        st.experimental_rerun()

def search_by_usn():
    db = connect_db()
    user_col = db['students']
    usn = st.text_input("Enter USN to search")
    submit = st.button("Search")
    if submit:
        user = user_col.find_one({"USN": usn})
        if user:
            st.subheader(f"Student details of {user['First Name']}")
            col1, col2 = st.columns(2)
            col1.text_input("First Name", value=f"{user['First Name']}", disabled=True)
            col2.text_input("Last Name", value=f"{user['Last Name']}", disabled=True)
            col1.text_input("Age", value=f"{user['Age']}", disabled=True)
            col2.text_input("Gender", value=f"{user['Gender']}", disabled=True)
            col1.text_input("DOB", value=f"{user['DOB']}", disabled=True)
            col2.text_input("Email", value=f"{user['Email']}", disabled=True)
        else:
            st.error("Student does not exist")

def render_user_page():
    db = connect_db()
    user_col = db['students']
    
    st.markdown(
        """
    <style>
    section[data-testid="stSidebar"] div.stButton button {
    width: 300px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header(f"Welcome, {user_col.find({'USN': get_username()['username']})[0]['First Name']}")
        st.subheader(" Your Dashboard")
        menu_options = ["Attendance", "Academics", "Fees", "Events"]
        selected_option = st.sidebar.selectbox("Select an Option", menu_options)
        logout_button = st.button("Logout")

    if selected_option == "Attendance":
        render_attendance_page(get_username()['username'])
    elif selected_option == "Academics":
        render_marks_page(get_username()['username'])
    elif selected_option == "Fees":
        render_fees_page()
    elif selected_option == "Events":
        st.write("Upcoming events will be listed here.")

    if logout_button:
        set_login_status(False)
        st.experimental_rerun()

def render_attendance_page(username):
    db = connect_db()
    user_col = db['students']
    user = user_col.find_one({"USN": username})
    
    if user:
        st.subheader("Attendance Records")
        attendance_data = user.get('Attendance', {})
        if not attendance_data:
            st.write("No attendance records found.")
        else:
            data = []
            for subject, records in attendance_data.items():
                data.append({
                    'Subject': subject,
                    'Classes Present': records.get('Classes Present', 0),
                    'Total Classes': records.get('Total Classes', 0)
                })
            df = pd.DataFrame(data)
            chart = alt.Chart(df).mark_bar().encode(
                x='Subject:N',
                y='Classes Present:Q',
                color='Subject:N'
            ).properties(
                title='Classes Present per Subject'
            )
            st.altair_chart(chart, use_container_width=True)
    else:
        st.error("User does not exist.")

def render_marks_page(username):
    db = connect_db()
    user_col = db['students']
    user = user_col.find_one({"USN": username})

    if user:
        st.subheader("Marks Records")
        marks_data = user.get('Marks', {})
        if not marks_data:
            st.write("No marks records found.")
        else:
            data = []
            for subject, records in marks_data.items():
                data.append({
                    'Subject': subject,
                    'Marks Obtained': records.get('Marks Obtained', 0),
                    'Total Marks': records.get('Total Marks', 0)
                })
            df = pd.DataFrame(data)
            chart = alt.Chart(df).mark_bar().encode(
                x='Subject:N',
                y='Marks Obtained:Q',
                color='Subject:N'
            ).properties(
                title='Marks Obtained per Subject'
            )
            st.altair_chart(chart, use_container_width=True)
    else:
        st.error("User does not exist.")

def render_fees_page():
    db = connect_db()
    user_col = db['students']
    username = get_username()['username']
    user = user_col.find_one({"USN": username})

    if get_login_status()[0] == 'Admin':
        st.subheader("Update Fees Status")
        student_usn = st.text_input("Student USN")
        fees_status = st.selectbox("Fees Status", ["Pending", "Paid"])
        update_fees_button = st.button("Update Fees Status")

        if update_fees_button:
            if student_usn:
                user = user_col.find_one({"USN": student_usn})
                if user:
                    user_col.update_one({"USN": student_usn}, {'$set': {"Fees.Status": fees_status}})
                    st.success("Fees status updated successfully!")
                else:
                    st.error("Student does not exist.")
            else:
                st.error("Please enter a student USN.")
    else:
        if user:
            st.subheader("Fees Status")
            fees_status = user.get('Fees', {}).get('Status', 'Pending')
            st.write(f"Current Fees Status: {fees_status}")
        else:
            st.error("User does not exist.")

if __name__ == "__main__":
    main()
