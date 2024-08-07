import streamlit as st
import pymongo
import pandas as pd
import altair as alt

def connect_db():
    """Connect to MongoDB Atlas."""
    conn = pymongo.MongoClient("mongodb+srv://nehadesh2003:123@cluster.m0jtccy.mongodb.net/")
    db = conn['bnmvault']
    return db

def display_events():
    db = connect_db()
    event_col = db['events']
    
    st.subheader("Upcoming Events")
    
    events = list(event_col.find())
    
    if not events:
        st.info("No events available.")
    else:
        for event in events:
            st.write(f"**Event Name:** {event['Event Name']}")
            st.image(event['Event Poster'], caption=event['Event Name'])

def render_user_page():
    db = connect_db()
    user_col = db['students']
    
    username = get_username()['username']
    user = user_col.find_one({"USN": username})
    
    if not user:
        st.error("User not found.")
        return
    
    st.sidebar.header(f"Welcome, {user['First Name']}")
    menu_options = ["Attendance", "Academics", "Fees", "Events"]
    selected_option = st.sidebar.selectbox("Select an Option", menu_options)
    logout_button = st.sidebar.button("Logout")
    
    if selected_option == "Attendance":
        render_attendance_page(username)
    elif selected_option == "Academics":
        render_marks_page(username)
    elif selected_option == "Fees":
        render_fees_page(username)
    elif selected_option == "Events":
        display_events()
    
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

    subjects = list(attendance.keys())
    classes_present = [attendance[subject]['Classes Present'] for subject in subjects]
    total_classes = [attendance[subject]['Total Classes'] for subject in subjects]

    attendance_data = pd.DataFrame({
        'Subject': subjects,
        'Classes Present': classes_present,
        'Total Classes': total_classes
    })

    attendance_data['Attendance %'] = (attendance_data['Classes Present'] / attendance_data['Total Classes']) * 100

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

    subjects = list(marks.keys())
    marks_obtained = [marks[subject]['Marks Obtained'] for subject in subjects]
    total_marks = [marks[subject]['Total Marks'] for subject in subjects]

    marks_data = pd.DataFrame({
        'Subject': subjects,
        'Marks Obtained': marks_obtained,
        'Total Marks': total_marks
    })

    marks_data['Marks %'] = (marks_data['Marks Obtained'] / marks_data['Total Marks']) * 100

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

def main():
    logged_in = get_login_status()[0]

    if not logged_in:
        render_login_page()
    elif logged_in == 'Student':
        render_user_page()
    elif logged_in == 'Admin':
        render_admin_page()

if __name__ == "__main__":
    main()
