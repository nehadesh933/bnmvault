import streamlit as st
import pandas as pd
import altair as alt
import pymongo
import numpy as np

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

def add_event():
    db = connect_db()
    event_col = db['events']
    st.subheader("Add Event")
    event_name = st.text_input("Event Name")
    event_poster = st.file_uploader("Upload Event Poster (JPG format)", type=["jpg"])

    add_event_button = st.button("Add Event")

    if add_event_button:
        if event_name and event_poster:
            poster_file = event_poster.read()
            event_col.insert_one({"Event Name": event_name, "Event Poster": poster_file})
            st.success("Event added successfully!")
        else:
            st.error("Please provide both event name and poster.")

def render_events_page():
    db = connect_db()
    event_col = db['events']
    st.subheader("Upcoming Events")

    # Fetch all events from the database
    events = list(event_col.find({}))

    if not events:
        st.info("No upcoming events.")
        return

    for event in events:
        st.write(f"**Event Name:** {event['Event Name']}")
        if 'Event Poster' in event:
            poster_file = event['Event Poster']
            st.image(poster_file, use_column_width=True)
        st.write("---")

def calculate_correlation(attendance, marks):
    # Convert the attendance and marks to lists or arrays
    attendance_values = np.array(list(attendance.values()))
    marks_values = np.array(list(marks.values()))
    
    if len(attendance_values) == len(marks_values):
        correlation = np.corrcoef(attendance_values, marks_values)[0, 1]
        return correlation
    else:
        return "Mismatch in data lengths."

def analyze_correlation(usn):
    db = connect_db()
    user_col = db['students']
    
    # Retrieve the student's data based on their USN
    student_data = user_col.find_one({"USN": usn})
    
    if student_data:
        # Extract attendance and marks from the student's data
        attendance = student_data.get("Attendance", {})
        marks = student_data.get("Marks", {})
        
        if attendance and marks:
            # Perform correlation calculation
            correlation = calculate_correlation(attendance, marks)
            return correlation
        else:
            return "Attendance or Marks data not found for this student."
    else:
        return "Student data not found for the given USN."

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
    menu_options = ["Add Student", "Add Attendance", "Add Marks", "Search by USN", "Add Fees Status", "Add Events", "Analyze Correlation"]
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
        add_fees_status()
    elif selected_option == "Add Events":
        add_event()
    elif selected_option == "Analyze Correlation":
        st.subheader("Analyze Correlation")
        usn = st.text_input("Enter Student USN")
        analyze_button = st.button("Analyze Correlation")

        if analyze_button:
            correlation_result = analyze_correlation(usn)
            if isinstance(correlation_result, float):
                st.write(f"Correlation between Attendance and Marks: {correlation_result:.2f}")
            else:
                st.write(correlation_result)

def render_user_page():
    st.title("Student Dashboard")
    username = get_username()['username']
    db = connect_db()
    user_col = db['students']
    student_data = user_col.find_one({"USN": username})

    if student_data:
        st.subheader(f"Welcome, {student_data['First Name']} {student_data['Last Name']}")
        st.write(f"**USN:** {student_data['USN']}")
        st.write(f"**Age:** {student_data['Age']}")
        st.write(f"**Gender:** {student_data['Gender']}")
        st.write(f"**DOB:** {student_data['DOB']}")
        st.write(f"**Email:** {student_data['Email']}")
        st.write(f"**Fees Status:** {student_data['Fees']['Status']}")
        # Add additional student details display here
    else:
        st.error("Student data not found.")

# Initialize the application
if __name__ == "__main__":
    main()
