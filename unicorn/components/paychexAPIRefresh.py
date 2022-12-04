from django_unicorn.components import UnicornView
import requests
from employee.models import Employee
from SLUGS.settings import PAYCHEX_API_KEY, PAYCHEX_API_SECRET, PAYCHEX_COMPANY_ID, PAYCHEX_ORG


class PaychexapirefreshView(UnicornView):
    api_key = PAYCHEX_API_KEY
    api_secret = PAYCHEX_API_SECRET
    token = ""
    state = "w"
    statusMessages = []

    def update_from_API(self):
        try:
            self.state = "i"
            self.init_keys()
            self.refresh_employees()
            self.state = "s"
        except:
            self.statusMessages.append({"type": "e", "text": "Could not sync PayChex Employee IDs, Exiting."})

    def init_keys(self):
        try:
            # Send a request to the Paychex API to get a token
            url = "https://api.paychex.com/auth/oauth/v2/token"
            payload = {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.api_secret,
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            response = requests.request("POST", url, headers=headers, data=payload)
            self.token = response.json()["access_token"]
            self.statusMessages.append({"type": "s", "text": "Got token from Paychex API. Fetching Employees..."})
        except:
            self.statusMessages.append({"type": "e", "text": f"PayChex API credentials could not be fetched."})
            raise Exception("PayChex API creds could not be fetched")
    
    def refresh_employees(self):
        url = f"https://api.paychex.com/companies/{PAYCHEX_COMPANY_ID}/workers"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        response = requests.request("GET", url, headers=headers)
        for employee in response.json()["content"]:
            if employee["organization"]["organizationId"] == PAYCHEX_ORG:
                emp = Employee.objects.filter(first_name__iexact=employee["name"]["givenName"], last_name__iexact=employee["name"]["familyName"])
                if emp.count() > 0:
                    if emp.count() > 1:
                        self.statusMessages.append({"type": "e", "text": f"Multiple employees found for {employee['name']['givenName']} {employee['name']['familyName']}"})
                    emp = emp.first()
                    if emp.paychex_flex_workerID is None or emp.paychex_flex_workerID == "":
                        emp.paychex_flex_workerID = employee["employeeId"]
                        emp.save()
                        self.statusMessages.append({"type": "i", "text": f"Updated {emp}"})
                    else:
                        self.statusMessages.append({"type": "i", "text": f"{emp} already has a workerID of {emp.paychex_flex_workerID}"})
                else:
                    if (employee["currentStatus"]["statusType"] == "ACTIVE"):
                        self.statusMessages.append({"type": "e", "text": f"No employee found for {employee['name']['givenName']} {employee['name']['familyName']}, FlexID: {employee['employeeId']}"})
        for employee in Employee.objects.filter(paychex_flex_workerID=None, is_active=True):
            self.statusMessages.append({"type": "e", "text": f"Employee {employee} has no FlexID in PayChex...."})
        self.statusMessages.append({"type": "s", "text": "Done!"})