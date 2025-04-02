import requests
import base64
import json
import time
import pandas as pd
import math
import os

def get_auth_header(username: str, password: str) -> str:
    auth_string = f"{username}:{password}"
    auth_encoded = base64.b64encode(auth_string.encode()).decode()
    return f"Basic {auth_encoded}"

def build_headers(auth_header: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": auth_header,
        "User-Agent": "Mozilla/5.0"
    }

def build_payload(client_app_id: str, client_api_key: str, client_agency_code: str,
                  from_datetime: str, to_datetime: str,
                  page_size: int, page_number: int) -> dict:
    return {
        "Header": {
            "Client_AppID": client_app_id,
            "Client_APIKey": client_api_key,
            "Client_AgencyCode": client_agency_code,
            "UniqID": 1
        },
        "FromDateTime": from_datetime,
        "ToDateTime": to_datetime,
        "PageSize": page_size,
        "PageNumber": page_number
    }

def fetch_all_data(from_datetime: str, to_datetime: str,
                   client_app_id: str, client_api_key: str, client_agency_code: str,
                   username: str, password: str) -> pd.DataFrame:

    url = "https://fortresarena.ariel.org.il:4443/FGB_WebApplication/HPJBB/Production/API/CRM/TimeAttendanceInformation_Paging/"

    auth_header = get_auth_header(username, password)
    headers = build_headers(auth_header)

    page_size = 100
    page_number = 1
    all_data = []

    while True:
        payload = build_payload(
            client_app_id, client_api_key, client_agency_code,
            from_datetime, to_datetime,
            page_size, page_number
        )

        print(f"Requesting Page {page_number}...")
        print("Payload being sent:")
        print(json.dumps(payload, indent=2))

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

        if not response_json:
            print("Error: Empty response received")
            break

        total_records = response_json.get("statistics", {}).get("numberOfRecords", 0)
        total_pages = math.ceil(total_records / page_size)

        data = response_json.get("data", [])
        if not data:
            print("No more data received, stopping pagination.")
            break

        all_data.extend(data)
        page_number += 1
        time.sleep(10)

        if page_number > total_pages:
            break

    df = pd.DataFrame(all_data)
    required_columns = ['attendanceID', 'attendanceDatetime', 'ticketNumber', 'turnstileName', 'gateCode', 'failureReason']
    df = df[[col for col in required_columns if col in df.columns]]
    return df

if __name__ == "__main__":
    # GitHub Secrets will be injected into env variables
    client_app_id = os.getenv("FGB_CLIENT_APPID")
    client_api_key = os.getenv("FGB_CLIENT_APIKEY")
    client_agency_code = os.getenv("FGB_CLIENT_AGENCYCODE")

    # You manually insert these (non-secret)
    username = "your_username_here"
    password = "your_password_here"

    from_datetime = "2025-03-02 09:00:00.000"
    to_datetime = "2025-03-02 21:00:00.000"

    df = fetch_all_data(
        from_datetime,
        to_datetime,
        client_app_id,
        client_api_key,
        client_agency_code,
        username,
        password
    )

    df.to_csv("fortress_attendance.csv", index=False)
    print("Data saved to fortress_attendance.csv")
