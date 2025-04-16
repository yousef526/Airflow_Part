import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def update_env_file(file_path, updates):
    lines = []
    found_keys = set()

    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                if '=' in line:
                    key = line.split('=')[0].strip()
                    if key in updates:
                        lines.append(f"{key}={updates[key]}\n")
                        found_keys.add(key)
                    else:
                        lines.append(line)
                else:
                    lines.append(line)

    for k, v in updates.items():
        if k not in found_keys:
            lines.append(f"{k}={v}\n")

    with open(file_path, 'w') as f:
        f.writelines(lines)


# API credentials
def apiCall(company_name):
    months_lis = ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    api_key = os.getenv('API_KEY')
    YEAR = os.getenv('Year')
    month_no = os.getenv('month_no')
    month = f"{YEAR}-{month_no}"

    

    interval = int(os.getenv("interval")) # in minutes
    sceduled_time = os.getenv("sceduled_time")

    company_name = company_name # just add one company for simplicity

    response = requests.get(url=f"https://www.alphavantage.co/query?function={sceduled_time}&symbol={company_name}&interval={interval}min&month={month}&outputsize=full&apikey={api_key}")
    print(response.json())


    with open("/opt/airflow/dags/StockMarketScripts/data.json","w") as f1:
        json.dump(indent=4,obj=response.json() ,fp=f1)

    ind = months_lis.index(month_no)
    if int(YEAR) == datetime.now().year and ind+1 == datetime.now().month:
        pass
    else:
        if ind == 11:
            new_month = months_lis[0]
            new_year = str(int(YEAR) + 1)
        else:
            new_month = months_lis[ind + 1]
            new_year = YEAR

        update_env_file('/opt/airflow/dags/StockMarketScripts/.env', {
        'month_no': new_month,
        'Year': new_year
        })



# we can pull more data for many years and for each 
# and save the year we should start next time 
""" 
for month in months_lis:
    month = f"{YEAR}-{month}"
    response = requests.get(url=f"https://www.alphavantage.co/query?function={sceduled_time}&symbol={company_name}&interval={interval}min&month={month}&outputsize=full&apikey={api_key}")
    print(response.json())


os.putenv("Year", str(int(YEAR) + 1)) """