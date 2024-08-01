import streamlit as st
import pandas as pd
import altair as alt
import pymongo
from PIL import Image

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
    fees_status = st.selectbox("Fees Status", ["Pending", "Paid"])
    add_student_button = st.button("Add Student")

    if add_student_button:
        user = user_col.find_one({"USN": student_usn})
        if not user:
            user_col.insert_one({"USN": student_usn, "Password": student_pswd, "First Name": student_FName,
                                 "Last Name": student_Lname, "Age": student_age, "Gender": student_gen,
                                 "DOB": str(student_dob), "Email": student_mail, "Fees": {"Status": fees_status}})

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

# Function to render fees page
def render_fees_page():
    db = connect_db()
    user_col = db['students']
    username = get_username()['username']
    user = user_col.find_one({"USN": username})

    if user:
        st.subheader("Fees Status")
        fees_status = user.get('Fees', {}).get('Status', 'Pending')
        st.write(f"Current Fees Status: {fees_status}")
    else:
        st.error("User does not exist.")

# Function to add and manage events
def manage_events():
    db = connect_db()
    event_col = db['events']
    st.subheader("Manage Events")
    event_title = st.text_input("Event Title")
    event_date = st.date_input("Event Date")
    event_details = st.text_area("Event Details")
    event_poster = st.file_uploader("Upload Event Poster", type=["jpg", "jpeg", "png"])
    event_link = st.text_input("Event Link")
    add_event_button = st.button("Add Event")

    if add_event_button:
        if event_poster:
            image = Image.open(event_poster)
            poster_url = upload_image_to_cloud(image)  # Placeholder for uploading image function
        else:
            poster_url = ""

        event_col.insert_one({
            "Title": event_title,
            "Date": str(event_date),
            "Details": event_details,
            "Poster URL": poster_url,
            "Link": event_link
        })
        st.success("Event added successfully!")

def upload_image_to_cloud(image):
    # Implement your cloud image upload logic here
    return "URL to the uploaded image"

def render_events_page():
    db = connect_db()
    event_col = db['events']
    st.subheader("Upcoming Events")

    events = event_col.find()
    for event in events:
        st.write(f"**Title:** {event.get('Title', 'N/A')}")
        st.write(f"**Date:** {event.get('Date', 'N/A')}")
        st.write(f"**Details:** {event.get('Details', 'N/A')}")
        if event.get('Poster URL'):
            st.image(event.get('Poster URL'), caption='Event Poster', use_column_width=True)
        if event.get('Link'):
            st.write(f"[More Details]({event.get('Link')})")

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
    menu = st.sidebar.radio("Select Option", ["Add Student", "Add Attendance", "Add Marks", "Manage Events", "View Events", "View Attendance", "View Marks", "View Fees"])

    if menu == "Add Student":
        add_student()
    elif menu == "Add Attendance":
        add_attendance()
    elif menu == "Add Marks":
        add_marks()
    elif menu == "Manage Events":
        manage_events()
    elif menu == "View Events":
        render_events_page()
    elif menu == "View Attendance":
        render_attendance_page(get_username()['username'])
    elif menu == "View Marks":
        render_marks_page(get_username()['username'])
    elif menu == "View Fees":
        render_fees_page()

def render_user_page():
    st.title("Student Dashboard")
    menu = st.sidebar.radio("Select Option", ["View Attendance", "View Marks", "View Fees"])

    if menu == "View Attendance":
        render_attendance_page(get_username()['username'])
    elif menu == "View Marks":
        render_marks_page(get_username()['username'])
    elif menu == "View Fees":
        render_fees_page()

if __name__ == "__main__":
    main()
