import requests
import base64
import json
import time
import pandas as pd
import math
from cryptography.fernet import Fernet

def fetch_all_data(from_datetime, to_datetime):
    
    auth_string = f"{username}:{password}"
    auth_encoded = base64.b64encode(auth_string.encode()).decode()
    url = "https://fortresarena.ariel.org.il:4443/FGB_WebApplication/HPJBB/Production/API/CRM/TimeAttendanceInformation_Paging/"
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Basic {auth_encoded}",
        "User-Agent": "Mozilla/5.0"
    }
    
    page_size = 100  
    page_number = 1
    all_data = []
    
    while True:
        payload = {
            "Header": {
                "Client_AppID": "com.HPJBB",
                "Client_APIKey": "37AF541A-C2BC-4578-8303-3D064C622263",
                "Client_AgencyCode": "HPJBB",
                "UniqID": 1
            },
            "FromDateTime": from_datetime,
            "ToDateTime": to_datetime,
            "PageSize": page_size,
            "PageNumber": page_number
        }
    
        print(f"Requesting Page {page_number}...")

        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: Received HTTP {response.status_code}")
            print("Response Text:", response.text)
            break

        try:
            response_json = response.json()
        except ValueError:  
            print("Error: Response is not valid JSON")
            print("Response Text:", response.text)
            break

        if response_json is None:
            print("Error: Empty response received")
            break

        total_records = response_json.get("statistics", {}).get("numberOfRecords", 0)
        total_pages = math.ceil(total_records / page_size)

        data = response_json.get("data", [])
        if not data:
            print("No more data received, stopping pagination.")
            break  # Stop if no more data

        all_data.extend(data)
        page_number += 1
        time.sleep(10)  # Add delay to avoid rate limiting
    
        if page_number > total_pages:
            break

    return pd.DataFrame(all_data)
    
from_datetime = "2025-03-02 09:00:00.000"
to_datetime = "2025-03-02 21:00:00.000"

df_users = fetch_all_data(from_datetime, to_datetime)
df_users = df_users[['attendanceID', 'attendanceDatetime', 'ticketNumber', 'turnstileName', 'gateCode', 'failureReason']]

df_users