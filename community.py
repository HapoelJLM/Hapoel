import streamlit as st
import pandas as pd
from datetime import datetime
import io
import requests
from simple_salesforce import Salesforce

def process_attendance_data(csv_file):
    auth = pd.read_csv(csv_file)

    auth['Fan/Company'] = auth['First name'] + ' ' + auth['Last name']

    auth = auth[['Fan/Company', 'assign using  ID number', 'User Id', 'CloseLink reservation name', 'Attendance']]
    auth = auth.dropna(subset=['CloseLink reservation name'])

    auth['User Id'] = auth['User Id'].fillna(0).astype(int)

    distributed = auth.groupby('CloseLink reservation name').size().reset_index(name='Count')
    distributed = distributed.rename(columns={'CloseLink reservation name': 'שם העמותה'})
    distributed = distributed.rename(columns={'Count': 'כמות כרטיסים שהוצאו'})

    attendance = auth.groupby('CloseLink reservation name')['Attendance'].apply(lambda x: (x == 'Yes').sum()).reset_index()
    attendance.columns = ['CloseLink reservation name', 'count']
    attendance = attendance.rename(columns={'CloseLink reservation name': 'שם העמותה'})
    attendance = attendance.rename(columns={'count': 'כמות אנשים שהגיעו מכל עמותה'})

    return auth, attendance, distributed

# Function to fetch marketing allowed data from Salesforce
def fetch_marketing_allowed_from_salesforce(auth_df):
    sf = Salesforce(username='gil@hapoel.co.il', password='G!l123!@#(:)', security_token='EDzK6fZg9oaOdeAn8bFMwVyYY')

    instance_url = sf.base_url.split('/services/data')[0]

    headers = {
        'Authorization': f'Bearer {sf.session_id}',
        'Content-Type': 'application/json'
    }

    user_ids = auth_df['User Id'].dropna().unique()
    results = []

    for user_id in user_ids:
        soql_query = f"SELECT Id, Name, Account.Name, Marketing_Allowed__c FROM Contact WHERE HJBC_ID__c = '{user_id}'"
        query_url = f"{instance_url}/services/data/v57.0/query?q={soql_query}"

        response = requests.get(query_url, headers=headers)

        if response.status_code == 200:
            contacts = response.json().get("records", [])
            for record in contacts:
                marketing_allowed = record.get("marketing_allowed__c")
                if marketing_allowed:  # Only add if the checkbox is checked
                    results.append({
                        "User Id": user_id,
                        "Contact Name": record.get("Name", "N/A"),
                        "Account Name": record.get("Account", {}).get("Name", "N/A"),
                        "Marketing Allowed": marketing_allowed
                    })
        else:
            st.error(f"Error fetching data for User ID {user_id}: {response.text}")

    salesforce_data = pd.DataFrame(results)
    filtered_data = salesforce_data.dropna(subset=['Marketing Allowed'])

    return filtered_data


st.markdown(
    """
    <style>
    .stApp {
        color: white;
        text-shadow: 2px 2px 4px black;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: white !important;
        text-shadow: 2px 2px 4px black !important;
    }

    a {
        color: cyan !important;
        font-weight: bold;
    }

   /* File uploader label styling */
    div[data-testid="stFileUploader"] label {
        color: white !important;
        text-shadow: 2px 2px 4px black !important;
        font-weight: bold;
        font-size: 24px !important; /* Makes text bigger */
        text-align: center !important;
        display: flex;
    }

    /* Style the file uploader box and center it */
    div[data-testid="stFileUploader"] section {
        padding: 8px !important;  /* Reduce padding for a thin appearance */
        border: 2px solid white !important;  /* Add a clean white border */
        border-radius: 25px !important;  /* Rounded edges to mimic a search bar */
        background-color: rgba(255, 255, 255, 0.2) !important; /* Semi-transparent background */
        width: 400px !important; /* Adjust width */
        height: 40px !important; /* Make it thinner */
        text-align: center !important;
        justify-content: center !important;
        align-items: center !important;
        display: flex !important;
        margin: auto !important;  /* Center the uploader */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit UI
st.markdown("<h1 style='text-align: center;'> דוח קהילה</h1>", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://raw.githubusercontent.com/gil-hapoel/social-icons/main/HAP08989.JPG");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.markdown("<h2 style='text-align: right;'>הוראות כיצד להוריד את הדוח הרצוי ממערכת רובוטיקט</h2>", unsafe_allow_html=True)

# Step 1: Login
st.markdown("<h4 style='text-align: right;'>בעזרת הלינק Roboticket התחבר/י למערכת</h4>", unsafe_allow_html=True)
st.markdown(
    "<h4 style='text-align: right;'><a href='https://tickets.hapoel.co.il/Boxoffice' target='_blank'>https://tickets.hapoel.co.il/Boxoffice</a></h4>", 
    unsafe_allow_html=True
)
st.image("https://raw.githubusercontent.com/gil-hapoel/social-icons/main/Screenshot%202025-02-26%20at%2017.19.22.png", use_container_width=True)

# Step 2: Reports section
st.markdown("<h4 style='text-align: right;'>לחצ/י על האייקון של הדוחות</h4>", unsafe_allow_html=True)
st.image("https://raw.githubusercontent.com/gil-hapoel/social-icons/main/Screenshot%202025-02-26%20at%2017.26.51.png", use_container_width=True)

#  Step 3: Games Authorization Report
st.markdown("<h4 style='text-align: right;'>Games authorization report לחצ/י על</h4>", unsafe_allow_html=True)
st.image("https://raw.githubusercontent.com/gil-hapoel/social-icons/main/Screenshot%202025-02-26%20at%2017.29.20.png", use_container_width=True)

# Step 4: Select the game
st.markdown("<h4 style='text-align: right;'>בחר/י את המשחק הרצוי</h4>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: right;'>GETEVENTS אם אינך רואה את המשחק, לחצ/י על כפתור</h4>", unsafe_allow_html=True)
st.image("https://raw.githubusercontent.com/gil-hapoel/social-icons/main/Screenshot%202025-02-26%20at%2017.30.33.png", use_container_width=True)

# Step 5: Download the report
st.markdown("<h4 style='text-align: right;'>לאחר מציאת המשחק הרצוי, לחצ/י על הכפתור האמצעי כדי להוריד את הדוח</h4>", unsafe_allow_html=True)
st.image("https://raw.githubusercontent.com/gil-hapoel/social-icons/main/Screenshot%202025-02-26%20at%2017.32.40.png", use_container_width=True)

st.markdown("<h4 style='text-align: right;'>אנא העלה/י את דוח המשחק המלא</h4>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 1])  # Adjust column sizes
with col1:
    st.write("")  # Empty space
with col2:
    st.write("")  # Empty space
with col3:
    uploaded_file = st.file_uploader('CSV בחר/י קובץ', type="csv")

if uploaded_file is not None:
    col1, col2, col3 = st.columns([1, 1, 2])  # Create 3 columns
    with col1:
        st.write("")  # Empty space for alignment
    with col2:
        st.write("")  # Another empty space
    with col3:
        st.success('!הקובץ הועלה בהצלחה')
    
    # Process uploaded CSV file
    auth, attendance_data, distributed_data = process_attendance_data(uploaded_file)

    st.markdown("<h4 style='text-align: right;'>:כמות הכרטיסים שכל עמותה ביקשה</h4>", unsafe_allow_html=True)
    st.write(distributed_data)

    st.markdown("<h4 style='text-align: right;'>:כמות האנשים שהגיעו מכל עמותה</h4>", unsafe_allow_html=True)
    st.write(attendance_data)

    if attendance_data.empty:
        st.warning("לא נמצאו נתוני הגעה")
        st.stop()  

    if "delete_done" not in st.session_state:
        st.session_state.delete_done = False

    st.markdown("<h4 style='text-align: right;'>?האם ברצונך למחוק שורות מהטבלה</h4>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([2, 1, 1])  # Adjust column widths
    with col1:
        st.write("")  # Empty space
    with col2:
        st.write("")  # Empty space
    with col3:
        delete_mode = st.radio(":בחר באחת מהאפשרויות", ["לא למחוק", "למחוק שורות מסוימות"])

    if delete_mode == "למחוק שורות מסוימות":
        delete_indices = st.text_input("הכנס מספרי שורות למחיקה (מופרדים בפסיק)", "")

        if delete_indices:
            try:
                # Convert input into a list of integers
                indices_to_delete = [int(i.strip()) for i in delete_indices.split(",")]

                # Check if indices exist in DataFrame
                if all(i in attendance_data.index for i in indices_to_delete):
                    # Remove rows based on index
                    attendance_data = attendance_data.drop(indices_to_delete).reset_index(drop=True)

                    st.success("✅ השורות שנבחרו נמחקו בהצלחה!")
                    st.write(attendance_data)  # Show updated table
                else:
                    st.error("אחת או יותר מהשורות שסיפקת אינה קיימת. נסה שוב.")
            except ValueError:
                st.error("יש להכניס מספרים מופרדים בפסיק בלבד.")

    attendance_data = auth.groupby(['Fan/Company', 'User Id', 'CloseLink reservation name'])['Attendance'].apply(lambda x: (x == 'Yes').sum()).reset_index()
    attendance_data.columns = ['Fan/Company', 'User Id', 'CloseLink reservation name', 'count']
    attendance_data = attendance_data[attendance_data['count'] > 0]

    # Fetch Salesforce Data
    st.markdown("<h2 style='text-align: right;'>SF מתחבר למערכת</h2>", unsafe_allow_html=True)
    with st.spinner('Fetching marketing allowed data...'):
        filtered_data = fetch_marketing_allowed_from_salesforce(auth)

    if not filtered_data.empty:
        col1, col2, col3 = st.columns([1, 1, 2])  # Create 3 columns
        with col1:
            st.write("")  # Empty space for alignment
        with col2:
            st.write("")  # Another empty space
        with col3:
            st.success("התבצע בהצלחה SF החיבור מול")

        # Merge attendance with Salesforce data
        merged = attendance_data.merge(filtered_data, on='User Id', how='inner')
        merged = merged[['Fan/Company', 'User Id', 'CloseLink reservation name', 'Marketing Allowed']]
        merged = merged.rename(columns={'Fan/Company': 'שם מלא'})
        merged = merged.rename(columns={'CloseLink reservation name': 'שם העמותה'})
        merged = merged.rename(columns={'Marketing Allowed': 'אישור דיוור'})
        # merged = merged.rename(columns={'Phone': 'מספר טלפון'})
        # merged = merged.rename(columns={'MailingAddress': 'כתובת מייל'})

        st.markdown("<h4 style='text-align: right;'>אנשים שהגיעו למשחק ואישרו דיוור</h4>", unsafe_allow_html=True)
        st.write(merged)
    else:
        st.warning("SF לא נמצאו נתונים תואמים במערכת")
