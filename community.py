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

    attendance = auth.groupby(['Fan/Company', 'User Id', 'CloseLink reservation name'])['Attendance'].apply(lambda x: (x == 'Yes').sum()).reset_index()
    attendance.columns = ['Fan/Company', 'User Id', 'CloseLink reservation name', 'count']
    attendance = attendance[attendance['count'] > 0]

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

# Streamlit UI
st.title('דוח קהילה ')
st.subheader('אנא להעלות את דוח המשחק המלא')

uploaded_file = st.file_uploader('CSV בחר קובץ', type="csv")

if uploaded_file is not None:
    st.success('!הקובץ הועלה בהצלחה')
    
    # Process uploaded CSV file
    auth, attendance_data, distributed_data = process_attendance_data(uploaded_file)
    st.subheader(':כמות כרטיסים שהוצאו')
    st.write(distributed_data)

    # Fetch Salesforce Data
    st.subheader('SF מתחבר למערכת')
    with st.spinner('Fetching marketing allowed data...'):
        filtered_data = fetch_marketing_allowed_from_salesforce(auth)

    if not filtered_data.empty:
        st.success("התבצע בהצלחה SF החיבור מול")

        # Merge attendance with Salesforce data
        merged = attendance_data.merge(filtered_data, on='User Id', how='inner')
        merged = merged[['Fan/Company', 'Account Name', 'User Id', 'CloseLink reservation name', 'Marketing Allowed']]

        st.subheader("אנשים שהגיעו למשחק ואישרו דיוור")
        st.write(merged)
    else:
        st.warning("לא נמצאו נתונים תואמים במערכת Salesforce.")
