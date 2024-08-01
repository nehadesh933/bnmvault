import streamlit as st
import pandas as pd
import altair as alt
import pymongo
from PIL import Image

st.title("BNM VAULT")

def connect_db():
    conn = pymongo.MongoClient("mongodb://localhost:27017/")
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
    connect_db()
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

    if selected_option == "Attendance":
        render_attendance_page(user_col)
    elif selected_option == "Academics":
        render_academic_results_page(user_col)
    elif selected_option == "Fees":
        render_fees_page(user_col)
    elif selected_option == "Events":
        render_events_page()

    if logout_button:
        set_login_status(False)
        st.experimental_rerun()

def render_attendance_page(user_col):
    st.title("Attendance")
    usn = get_username()['username']
    user = user_col.find_one({"USN": usn})

    if user:
        if "Attendance" in user:
            attendance_data = user["Attendance"]
            st.subheader("Attendance Details")

            # Create a DataFrame from the attendance data
            attendance_df = pd.DataFrame(attendance_data).T
            st.dataframe(attendance_df)

            attendance_summary = {
                subject: (attendance_info['Classes Present'] / attendance_info['Total Classes']) * 100
                for subject, attendance_info in attendance_data.items()
            }

            attendance_df['Attendance Percentage'] = attendance_df.apply(
                lambda row: (row['Classes Present'] / row['Total Classes']) * 100, axis=1)

            # Display the attendance summary chart
            st.subheader("Attendance Summary")
            attendance_summary_chart = alt.Chart(attendance_df.reset_index()).mark_bar().encode(
                x='index',
                y='Attendance Percentage',
                tooltip=['index', 'Classes Present', 'Total Classes', 'Attendance Percentage']
            )
            st.altair_chart(attendance_summary_chart, use_container_width=True)

            total_classes_present = sum(info['Classes Present'] for info in attendance_data.values())
            total_classes = sum(info['Total Classes'] for info in attendance_data.values())
            total_attendance_percentage = (total_classes_present / total_classes) * 100

            st.write(f"Overall Attendance Percentage: {total_attendance_percentage:.2f}%")
        else:
            st.warning("No attendance data available.")
    else:
        st.error("User does not exist.")

def render_academic_results_page(user_col):
    st.title("Academic Results")
    usn = get_username()['username']
    user = user_col.find_one({"USN": usn})

    if user:
        if "Marks" in user:
            marks_data = user["Marks"]
            st.subheader("Marks Details")

            # Create a DataFrame from the marks data
            marks_df = pd.DataFrame(marks_data).T
            st.dataframe(marks_df)

            # Add a percentage column to the marks DataFrame
            marks_df['Percentage'] = marks_df.apply(
                lambda row: (row['Marks Obtained'] / row['Total Marks']) * 100, axis=1)

            # Display the marks chart
            st.subheader("Marks Summary")
            marks_summary_chart = alt.Chart(marks_df.reset_index()).mark_bar().encode(
                x='index',
                y='Percentage',
                tooltip=['index', 'Marks Obtained', 'Total Marks', 'Percentage']
            )
            st.altair_chart(marks_summary_chart, use_container_width=True)

            # Calculate the total percentage
            total_marks_obtained = sum(info['Marks Obtained'] for info in marks_data.values())
            total_marks = sum(info['Total Marks'] for info in marks_data.values())
            total_percentage = (total_marks_obtained / total_marks) * 100

            st.write(f"Overall Percentage: {total_percentage:.2f}%")
        else:
            st.warning("No academic results available.")
    else:
        st.error("User does not exist.")

def render_fees_page(user_col):
    st.title("Fees")
    usn = get_username()['username']
    user = user_col.find_one({"USN": usn})

    if user:
        st.subheader("Fees Details")
        fees_status = user.get("Fees", {}).get("Status", "Pending")
        st.write(f"Fees Status: {fees_status}")
    else:
        st.error("User does not exist.")

def render_events_page():
    st.title("Events")
    st.subheader("Upcoming Events")

    events = [
        {"name": "Cultural Fest", "date": "2024-08-15", "description": "A celebration of cultural diversity with performances and activities."},
        {"name": "Tech Symposium", "date": "2024-09-10", "description": "Showcase of innovative tech projects by students."},
        {"name": "Sports Meet", "date": "2024-10-05", "description": "Inter-college sports competitions."}
    ]

    for event in events:
        st.write(f"**{event['name']}**")
        st.write(f"**Date:** {event['date']}")
        st.write(f"**Description:** {event['description']}")
        st.markdown("---")

if __name__ == "__main__":
    main()
