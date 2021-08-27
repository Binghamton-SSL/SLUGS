from apiclient.discovery import build
from google.oauth2 import service_account

# from SLUGS.settings import env
from gig.models import DEPARTMENTS


def prepare_credentials():
    credentials = service_account.Credentials.from_service_account_file(
        "calendar_service_account.json",
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    # designated_creds = credentials.with_subject('bssl@binghamtonsa.org')
    service = build("calendar", "v3", credentials=credentials)
    service.calendarList().list().execute()
    return service


def setupCalendars(gcal_service):
    calendars = {}
    default_tz = "America/New_York"
    cal_list = gcal_service.calendarList().list().execute()
    for cal in cal_list["items"]:
        calendars[cal["summary"]] = cal

    if "BSSL Events" not in calendars:
        event_calendar = {"summary": "BSSL Events", "timeZone": default_tz}
        gcal_service.calendars().insert(body=event_calendar).execute()
        print("Created BSSL Main Calendar")

    if "Tentative Shows" not in calendars:
        tentative_calendar = {"summary": "Tentative Shows", "timeZone": default_tz}
        gcal_service.calendars().insert(body=tentative_calendar).execute()
        print("Created Tentative Event Calendar")
    for dept in DEPARTMENTS:
        if f"{dept[1]} Work Schedule" not in calendars:
            calendar = {"summary": f"{dept[1]} Work Schedule", "timeZone": default_tz}
            gcal_service.calendars().insert(body=calendar).execute()
    listCalendars(gcal_service)
    return True


def listCalendars(gcal_service):
    calendars = {}
    cal_list = gcal_service.calendarList().list().execute()
    for cal in cal_list["items"]:
        calendars[cal["summary"]] = cal
    return calendars
