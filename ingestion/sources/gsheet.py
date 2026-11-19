import google.auth
import gspread
import pandas as pd

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly",
          "https://www.googleapis.com/auth/drive.readonly"]


def fetch_tabs(sheet_id: str) -> dict[str, pd.DataFrame]:
    creds, _ = google.auth.default(scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    return {ws.title: pd.DataFrame(ws.get_all_records()) for ws in sh.worksheets()}