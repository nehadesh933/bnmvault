import streamlit as st
import pandas as pd
import altair as alt
import pymongo
from PIL import Image
from collections.abc import MutableMapping
from collections import namedtuple


st.title("BNM VAULT")

def connect_db():
    # Use the MongoDB Atlas connection string
    conn = pymongo.MongoClient("mongodb+srv://nehadesh2003:123@cluster.m0jtccy.mongodb.net/")
    db = conn['bnmvault']  # Use the database name that matches your MongoDB Atlas setup
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

    if user:
        return 1
    else:
        return 0

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

    # Calculate attendance percentage based on classes present and total classes
    attendance_percentage = (classes_present / total_classes) * 100 if total_classes > 0 else 0
    st.write(f"Attendance Percentage: {attendance_percentage:.2f}%")
    num_absent = total_classes - classes_present
    st.write(f"Total Classes Absent: {num_absent: d}")

    add_attendance_button = st.button("Add Attendance")

    if add_attendance_button:
        user = user_col.find_one({"USN": student_usn})
        if user:
            user_col.update_one({"USN": student_usn},
                                {'$set': {f'Attendance.{selected_subject}': {'Classes Present': classes_present,
                                                                             'Total Classes': total_classes}}})
            st.success("Attendance updated successfully!")
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
        # Calculate percentage based on marks obtained and total marks
        user = user_col.find_one({"USN": student_usn})
        if user:
            user_col.update_one({"USN": student_usn},
                                {'$set': {f'Marks.{selected_subject}': {'Marks Obtained': marks_obtained,
                                                                        'Total Marks': total_marks}}})
            st.success("Marks updated successfully!")
        else:
            st.error("User does not exist.")

def main():
    # Check if user is logged in
    logged_in = get_login_status()[0]

    # If the user is not logged in, show the login page
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
    menu_options = ["Add Student", "Add Attendance", "Add Marks", "Search by USN"]
    selected_option = st.sidebar.selectbox("Select an Option", menu_options)

    if selected_option == "Add Student":
        add_student()
    elif selected_option == "Add Attendance":
        add_attendance()
    elif selected_option == "Add Marks":
        add_marks()
    elif selected_option == "Search by USN":
        search_by_usn()

    # Logout button
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
            col1.text_input(f"First Name", value=f"{user['First Name']}", disabled=True)
            col2.text_input(f"Last Name", value=f"{user['Last Name']}", disabled=True)
            col1.text_input(f"Age", value=f"{user['Age']}", disabled=True)
            col2.text_input(f"Gender", value=f"{user['Gender']}", disabled=True)
            col1.text_input(f"DOB", value=f"{user['DOB']}", disabled=True)
            col2.text_input(f"Email", value=f"{user['Email']}", disabled=True)
        else:
            st.error("Student doesn't exist")

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
        # Create buttons for the dashboard
        username = get_username()['username']
        user = user_col.find_one({'USN': username})
        
        # Check if user data is available
        if user:
            st.header(f"Welcome, {user.get('First Name', 'Student')}")
        else:
            st.header("Welcome, User")

        st.subheader("Your Dashboard")
        menu_options = ["Attendance", "Academics", "Fees", "Events"]
        selected_option = st.sidebar.selectbox("Select an Option", menu_options)
        logout_button = st.button("Logout")

        if logout_button:
            set_login_status(False)
            st.experimental_rerun()

    if selected_option == "Attendance":
        display_attendance()

    elif selected_option == "Academics":
        display_academics()

    elif selected_option == "Fees":
        display_fees()

    elif selected_option == "Events":
        display_events()

def display_attendance():
    db = connect_db()
    user_col = db['students']
    st.subheader("Attendance")
    username = get_username()['username']
    user = user_col.find_one({"USN": username})
    # Check if attendance data is available for the user
    if 'Attendance' in user:
        attendance = user['Attendance']
        if attendance:
            # Display attendance details for each subject
            for subject, attn in attendance.items():
                st.write(f"**{subject}:**")
                st.write(f"Classes Present: {attn['Classes Present']}")
                st.write(f"Total Classes: {attn['Total Classes']}")
                if attn['Total Classes'] > 0:
                    percentage = (attn['Classes Present'] / attn['Total Classes']) * 100
                    st.write(f"Attendance Percentage: {percentage:.2f}%")
                else:
                    st.write("Attendance Percentage: N/A")
        else:
            st.write("No attendance records available.")
    else:
        st.write("No attendance records available.")

def display_academics():
    db = connect_db()
    user_col = db['students']
    st.subheader("Academics")
    username = get_username()['username']
    user = user_col.find_one({"USN": username})

    if 'Marks' in user:
        academics = user['Marks']
        if academics:
            # Display academic details for each subject
            for subject, marks in academics.items():
                st.write(f"**{subject}:**")
                st.write(f"Marks Obtained: {marks['Marks Obtained']}")
                st.write(f"Total Marks: {marks['Total Marks']}")
                percentage = (marks['Marks Obtained'] / marks['Total Marks']) * 100
                st.write(f"Percentage: {percentage:.2f}%")
        else:
            st.write("No academic records available.")
    else:
        st.write("No academic records available.")

def display_fees():
    db = connect_db()
    user_col = db['students']
    st.subheader("Fees Status")
    username = get_username()['username']
    user = user_col.find_one({"USN": username})

    if user and 'Fees' in user:
        # Display fee status
        st.write(f"Fees Status: {user['Fees'].get('Status', 'N/A')}")
    else:
        st.write("No fee records available.")

def display_events():
    st.subheader("Events")
    image = Image.open("/path/to/image.jpg")
    st.image(image, caption="Event Poster")
    st.markdown("[Click here for event details](https://event-details-link)")

if __name__ == "__main__":
    main()
