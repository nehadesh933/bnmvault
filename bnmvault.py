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
#
def calculate_correlation(x, y):
    """Calculate Pearson correlation coefficient between two lists of values."""
    if len(x) != len(y) or len(x) == 0:
        return "Insufficient data"
    
    # Convert lists to numpy arrays
    x = np.array(x)
    y = np.array(y)
    
    # Calculate the Pearson correlation coefficient
    correlation_matrix = np.corrcoef(x, y)
    correlation_coefficient = correlation_matrix[0, 1]
    
    # Convert the coefficient to percentage
    correlation_percentage = correlation_coefficient * 100
    
    return f"{correlation_percentage:.2f}%"

import pandas as pd
import numpy as np

def analyze_correlation():
    db = connect_db()
    user_col = db['students']
    
    students = list(user_col.find({}))  # Get all student records

    results = []

    for student in students:
        usn = student.get("USN")
        marks = student.get("Marks", {})
        attendance = student.get("Attendance", {})

        # Find common subjects
        common_subjects = set(marks.keys()).intersection(set(attendance.keys()))
        
        if not common_subjects:
            correlation = "No common subjects"
        else:
            marks_values = []
            attendance_values = []

            for subject in common_subjects:
                marks_info = marks[subject]
                attendance_info = attendance[subject]

                # Compute percentages
                if marks_info['Total Marks'] > 0 and attendance_info['Total Classes'] > 0:
                    marks_percentage = (marks_info['Marks Obtained'] / marks_info['Total Marks']) * 100
                    attendance_percentage = (attendance_info['Classes Present'] / attendance_info['Total Classes']) * 100
                    marks_values.append(marks_percentage)
                    attendance_values.append(attendance_percentage)

            # Calculate correlation
            if marks_values and attendance_values:
                correlation = calculate_correlation(attendance_values, marks_values)
            else:
                correlation = "Insufficient data"

        results.append({"USN": usn, "Correlation": correlation})

    # Create a DataFrame for display
    results_df = pd.DataFrame(results)

    # Define styling for the DataFrame
    def highlight_correlation(val):
        if isinstance(val, str) and "No common subjects" in val:
            return 'background-color: #6c757d'  # Dark gray
        elif isinstance(val, str) and "Insufficient data" in val:
            return 'background-color: #343a40'  # Darker gray
        elif isinstance(val, str) and 'nan%' in val:
            return 'background-color: #343a40'  # Darker gray
        elif isinstance(val, str) and '%' in val:
            correlation_value = float(val.strip('%'))
            if correlation_value > 75:
                return 'background-color: #28a745'  # Dark green
            elif correlation_value > 50:
                return 'background-color: #17a2b8'  # Dark blue
            else:
                return 'background-color: #dc3545'  # Dark red
        return ''

    st.subheader("Correlation Analysis")
    styled_df = results_df.style.applymap(highlight_correlation, subset=['Correlation'])
    st.dataframe(styled_df)

#
#

def list_students_under_risk():
    db = connect_db()
    user_col = db['students']

    # Fetch all student records
    students = list(user_col.find({}))

    nsar_list = []  # List for students with insufficient attendance
    nssr_list = []  # List for students with insufficient marks

    for student in students:
        usn = student.get("USN")
        attendance = student.get("Attendance", {})
        marks = student.get("Marks", {})

        # Check for insufficient attendance
        attendance_below_threshold = any(
            (att_info['Classes Present'] / att_info['Total Classes'] * 100) < 85
            for att_info in attendance.values()
        )
        if attendance_below_threshold:
            nsar_list.append(usn)

        # Check for insufficient marks
        marks_below_threshold = any(
            (marks_info['Marks Obtained'] / marks_info['Total Marks'] * 100) < 40
            for marks_info in marks.values()
        )
        if marks_below_threshold:
            nssr_list.append(usn)

    # Create DataFrames for display
    nsar_df = pd.DataFrame(nsar_list, columns=["USN"])
    nssr_df = pd.DataFrame(nssr_list, columns=["USN"])

    st.subheader("Not Sufficient Attendance Requirements (NSAR)")
    if not nsar_df.empty:
        st.dataframe(nsar_df, width=300)
    else:
        st.write("No students found with insufficient attendance.")

    st.subheader("Not Sufficient Students Results (NSSR)")
    if not nssr_df.empty:
        st.dataframe(nssr_df, width=300)
    else:
        st.write("No students found with insufficient results.")
#


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
        if student_usn:
            user = user_col.find_one({"USN": student_usn})
            if user:
                user_col.update_one({"USN": student_usn},
                                    {'$set': {f'Marks.{selected_subject}': {'Marks Obtained': marks_obtained,
                                                                            'Total Marks': total_marks}}})
                st.success("Marks updated successfully!")
                render_marks_page(student_usn)  # Call the function to display marks
            else:
                st.error("User does not exist.")
        else:
            st.error("Please enter a valid USN.")


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
    menu_options = ["Add Student", "Add Attendance", "Add Marks", "Search by USN", "Add Fees Status", "Add Events",
                    "Analyze Corelation", "List of Students under Risk"]
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
        add_fees()
    elif selected_option == "Add Events":
        add_event()
    elif selected_option == "Analyze Corelation":
        analyze_correlation()
    elif selected_option == "List of Students under Risk":
        list_students_under_risk()

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
        render_events_page()

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

    # Check for any subjects with attendance below 85%
    low_attendance_subjects = attendance_data[attendance_data['Attendance %'] < 85]

    if not low_attendance_subjects.empty:
        st.subheader("Submit Leave Note")
        leave_date = st.date_input("Date of Leave")
        leave_letter = st.file_uploader("Upload Leave Letter (PDF format)", type=["pdf"])
        
        if st.button("Submit Leave Note"):
            if leave_date and leave_letter:
                # Save PDF to database or a storage service (e.g., S3)
                leave_letter_data = leave_letter.read()
                leave_notes_collection = db['leave_notes']
                leave_notes_collection.insert_one({
                    "USN": usn,
                    "Date of Leave": str(leave_date),
                    "Leave Letter": leave_letter_data
                })
                st.success("Leave note submitted successfully!")
            else:
                st.error("Please provide both date and leave letter.")


def render_marks_page(usn):
    db = connect_db()
    user_col = db['students']
    user = user_col.find_one({"USN": usn})
    
    if not user:
        st.error("User not found.")
        return

    marks = user.get("Marks", {})
    if not marks:
        st.info("No academic records found.")
        return

    st.subheader("Academic Overview")

    # Prepare data for Altair chart
    subjects = list(marks.keys())
    marks_obtained = [marks[subject]['Marks Obtained'] for subject in subjects]
    total_marks = [marks[subject]['Total Marks'] for subject in subjects]

    # Adjust the marks to be displayed out of 50
    adjusted_marks_obtained = [mark / total * 50 for mark, total in zip(marks_obtained, total_marks)]
    adjusted_total_marks = [50] * len(subjects)  # Total marks will be 50 for normalization

    # Create a DataFrame for the chart
    marks_data = pd.DataFrame({
        'Subject': subjects,
        'Marks Obtained (Adjusted)': adjusted_marks_obtained,
        'Total Marks (Adjusted)': adjusted_total_marks,
        'Marks %': [(mark / 50) * 100 for mark in adjusted_marks_obtained]  # Percentage based on 50
    })

    # Line chart for marks obtained
    line_chart = alt.Chart(marks_data).mark_line(point=True).encode(
        x='Subject',
        y='Marks Obtained (Adjusted)',
        color=alt.value('blue'),
        tooltip=['Subject', 'Marks Obtained (Adjusted)', 'Marks %']
    ).properties(
        title='Marks Obtained by Subject'
    )

    st.altair_chart(line_chart, use_container_width=True)

def add_fees():
    db = connect_db()
    user_col = db['students']
    
    st.subheader("Add or Update Fees")

    # Inputs
    student_usn = st.text_input("Student USN")
    fee_amount = st.number_input("Fee Amount", min_value=0.0, format="%.2f")
    fee_status = st.selectbox("Fee Status", ["Pending", "Paid", "Partial"])

    # Button to submit the fee details
    add_fees_button = st.button("Submit Fee Details")

    if add_fees_button:
        if not student_usn:
            st.error("Please enter a student USN.")
            return

        # Find the user by USN
        user = user_col.find_one({"USN": student_usn})
        if user:
            # Update or add fee details
            user_col.update_one(
                {"USN": student_usn},
                {'$set': {
                    'Fees': {
                        'Amount': fee_amount,
                        'Status': fee_status
                    }
                }}
            )
            st.success("Fee details updated successfully!")
        else:
            st.error("User does not exist.")

def render_fees_page(usn):
    db = connect_db()
    user_col = db['students']
    user = user_col.find_one({"USN": usn})
    fees = user.get("Fees", {})

    if not fees:
        st.info("No fee records found.")
        return

    st.subheader("Fee Details")

    fee_amount = fees.get("Amount", "Not Available")
    fee_status = fees.get("Status", "Not Available")

    st.write(f"Fee Amount: ${fee_amount:.2f}")
    st.write(f"Fee Status: {fee_status}")


if __name__ == "__main__":
    main()

