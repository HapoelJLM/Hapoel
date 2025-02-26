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

# Streamlit UI
st.title('דוח קהילה ')
st.subheader('אנא להעלות את דוח המשחק המלא')

uploaded_file = st.file_uploader('CSV בחר קובץ', type="csv")

if uploaded_file is not None:
    st.success('!הקובץ הועלה בהצלחה')
    
    # Process uploaded CSV file
    auth, attendance_data, distributed_data = process_attendance_data(uploaded_file)
    attendance_data.reset_index(inplace=True)

    st.subheader(':כמות כרטיסים שהוצאו עבור כל עמותה')
    st.write(distributed_data)

    st.subheader(':כמות אנשים שהגיעו מכל עמותה')
    st.write(attendance_data)

    if attendance_data.empty:
        st.warning("לא נמצאו נתוני הגעה")
        st.stop()  

    st.subheader(" האם ברצונך למחוק שורות מהטבלה?")
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
