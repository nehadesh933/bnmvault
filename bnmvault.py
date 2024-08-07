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
        st.header(f"Welcome, {user_col.find_one({'USN': get_username()['username']})['First Name']}")
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
        add_event()

    if logout_button:
        set_login_status(False)
        st.experimental_rerun()

def render_attendance_page(usn):
    db = connect_db()
    user_col = db['students']
    user = user_col.find_one({"USN": usn})
    attendance = user.get("Attendance", {})

    if not attendance:
        st.info("No attendance records found.")
        return

    st.subheader("Attendance Overview")

    # Prepare data for Altair chart
    subjects = list(attendance.keys())
    classes_present = [attendance[subject]['Classes Present'] for subject in subjects]
    total_classes = [attendance[subject]['Total Classes'] for subject in subjects]

    # Create a DataFrame for the chart
    attendance_data = pd.DataFrame({
        'Subject': subjects,
        'Classes Present': classes_present,
        'Total Classes': total_classes
    })

    # Calculate attendance percentage for each subject
    attendance_data['Attendance %'] = (attendance_data['Classes Present'] / attendance_data['Total Classes']) * 100

    # Bar chart for attendance percentage
    chart = alt.Chart(attendance_data).mark_bar().encode(
        x='Subject',
        y='Attendance %',
        color='Subject'
    ).properties(
        title='Attendance Percentage by Subject'
    )

    st.altair_chart(chart, use_container_width=True)

def render_marks_page(usn):
    db = connect_db()
    user_col = db['students']
    user = user_col.find_one({"USN": usn})
    marks = user.get("Marks", {})

    if not marks:
        st.info("No academic records found.")
        return

    st.subheader("Academic Overview")

    # Prepare data for Altair chart
    subjects = list(marks.keys())
    marks_obtained = [marks[subject]['Marks Obtained'] for subject in subjects]
    total_marks = [marks[subject]['Total Marks'] for subject in subjects]

    # Create a DataFrame for the chart
    marks_data = pd.DataFrame({
        'Subject': subjects,
        'Marks Obtained': marks_obtained,
        'Total Marks': total_marks
    })

    # Calculate marks percentage for each subject
    marks_data['Marks %'] = (marks_data['Marks Obtained'] / marks_data['Total Marks']) * 100

    # Line chart for academic performance
    chart = alt.Chart(marks_data).mark_line().encode(
        x='Subject',
        y='Marks %',
        color='Subject'
    ).properties(
        title='Academic Performance by Subject'
    )

    st.altair_chart(chart, use_container_width=True)

def render_fees_page(usn):
    db = connect_db()
    user_col = db['students']
    user = user_col.find_one({"USN": usn})
    fees = user.get("Fees", {})

    if not fees:
        st.info("No fee records found.")
        return

    st.subheader("Fee Details")

    fee_status = fees.get("Status", "Pending")
    st.write(f"Fee Status: {fee_status}")

if __name__ == "__main__":
    main()
