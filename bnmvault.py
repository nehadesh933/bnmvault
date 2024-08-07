import streamlit as st
import pandas as pd
import altair as alt
import pymongo
from datetime import datetime

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
        render_fees_page()

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
        render_fees_page(get_username()['username'])
    elif selected_option == "Events":
        st.write("Display events here")

    if logout_button:
        set_login_status(False)
        st.experimental_rerun()

# Function to render the attendance page
def render_attendance_page(username):
    db = connect_db()
    user_collection = db.students

    user = user_collection.find_one({"USN": username})

    st.subheader("Attendance Details")
    attendance_data = user.get("Attendance", {})

    for subject, attendance in attendance_data.items():
        classes_present = attendance.get("Classes Present", 0)
        total_classes = attendance.get("Total Classes", 0)
        attendance_percentage = (classes_present / total_classes) * 100 if total_classes > 0 else 0
        num_absent = total_classes - classes_present

        st.markdown(f"**{subject}**")
        st.write(f"Classes Present: {classes_present}")
        st.write(f"Total Classes: {total_classes}")
        st.write(f"Attendance Percentage: {attendance_percentage:.2f}%")
        st.write(f"Total Classes Absent: {num_absent}")
        st.write("---")

def render_marks_page(username):
    db = connect_db()
    user_collection = db.students
    user = user_collection.find_one({"USN": username})
    st.subheader("Academic Marks")
    marks = user.get('Marks', {})
    subjects = list(marks.keys())

    subject_selector = st.selectbox("Select Subject", subjects)

    if subject_selector:
        subject_marks = marks[subject_selector]
        marks_obtained = subject_marks['Marks Obtained']
        total_marks = subject_marks['Total Marks']

        col1, col2 = st.columns(2)
        col1.metric("Marks Obtained", marks_obtained)
        col2.metric("Total Marks", total_marks)

        st.write("---")

def render_fees_page(username):
    db = connect_db()
    user_collection = db.students
    user = user_collection.find_one({"USN": username})
    st.subheader("Fee Payment Status")

    # Display fee status and payment date
    fee_status = user.get('Fees', {}).get('Status', 'Not Updated')
    payment_date = user.get('Fees', {}).get('Payment Date', 'Not Available')
    st.write(f"Current Fee Status: {fee_status}")
    st.write(f"Payment Date: {payment_date}")

    update_fee_status = st.checkbox("Update Fee Status")

    if update_fee_status:
        fee_options = ["Paid", "Pending"]
        selected_status = st.radio("Fee Status", fee_options)

        if selected_status:
            current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            user_collection.update_one({"USN": username},
                                       {'$set': {'Fees.Status': selected_status,
                                                 'Fees.Payment Date': current_datetime}})
            st.success("Fee status updated successfully!")
            st.experimental_rerun()

if __name__ == '__main__':
    main()
