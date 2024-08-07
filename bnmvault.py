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

def analyze_correlation(usn):
    db = connect_db()
    user_col = db['students']

    # Fetch attendance data
    user = user_col.find_one({"USN": usn})
    attendance = user.get("Attendance", {})
    marks = user.get("Marks", {})

    if not attendance or not marks:
        st.info("Insufficient data for correlation analysis.")
        return

    # Prepare data for correlation analysis
    subjects = list(attendance.keys())
    attendance_data = []
    marks_data = []

    for subject in subjects:
        if subject in marks:
            attendance_classes_present = attendance[subject]['Classes Present']
            attendance_total_classes = attendance[subject]['Total Classes']
            marks_obtained = marks[subject]['Marks Obtained']
            total_marks = marks[subject]['Total Marks']

            attendance_percentage = (attendance_classes_present / attendance_total_classes) * 100
            marks_percentage = (marks_obtained / total_marks) * 100

            attendance_data.append(attendance_percentage)
            marks_data.append(marks_percentage)

    if not attendance_data or not marks_data:
        st.info("No data available for correlation analysis.")
        return

    # Calculate correlation
    df = pd.DataFrame({
        'Attendance %': attendance_data,
        'Marks %': marks_data
    })
    correlation = df.corr().iloc[0, 1]

    st.subheader("Correlation Analysis")
    st.write(f"Correlation between Attendance Percentage and Marks Percentage: {correlation:.2f}")

    if correlation > 0:
        st.write("There is a positive correlation between attendance and marks.")
    elif correlation < 0:
        st.write("There is a negative correlation between attendance and marks.")
    else:
        st.write("There is no significant correlation between attendance and marks.")

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
    menu_option = st.sidebar.selectbox("Menu", ["Add Student", "Add Attendance", "Add Marks", "Add Event", "View Events", "Analyze Correlation"])

    if menu_option == "Add Student":
        add_student()
    elif menu_option == "Add Attendance":
        add_attendance()
    elif menu_option == "Add Marks":
        add_marks()
    elif menu_option == "Add Event":
        add_event()
    elif menu_option == "View Events":
        render_events_page()
    elif menu_option == "Analyze Correlation":
        username = get_username()['username']
        analyze_correlation(username)

def render_user_page():
    st.title("Student Dashboard")
    username = get_username()['username']
    menu_option = st.sidebar.selectbox("Menu", ["View Attendance", "View Marks", "Analyze Correlation"])

    if menu_option == "View Attendance":
        render_attendance_page(username)
    elif menu_option == "View Marks":
        render_marks_page(username)
    elif menu_option == "Analyze Correlation":
        analyze_correlation(username)

def render_attendance_page(username):
    db = connect_db()
    user_col = db['students']
    st.subheader("View Attendance")
    user = user_col.find_one({"USN": username})

    if user:
        attendance = user.get("Attendance", {})
        if attendance:
            df = pd.DataFrame.from_dict(attendance, orient='index')
            df.reset_index(inplace=True)
            df.columns = ['Subject', 'Classes Present', 'Total Classes']
            st.write(df)
        else:
            st.info("No attendance data available.")
    else:
        st.error("User not found.")

def render_marks_page(username):
    db = connect_db()
    user_col = db['students']
    st.subheader("View Marks")
    user = user_col.find_one({"USN": username})

    if user:
        marks = user.get("Marks", {})
        if marks:
            df = pd.DataFrame.from_dict(marks, orient='index')
            df.reset_index(inplace=True)
            df.columns = ['Subject', 'Marks Obtained', 'Total Marks']
            st.write(df)
        else:
            st.info("No marks data available.")
    else:
        st.error("User not found.")

if __name__ == "__main__":
    main()
