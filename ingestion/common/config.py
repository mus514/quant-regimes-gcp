import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from google.cloud import secretmanager


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f'Missiing env variable " {name}')
    return value




@dataclass
class Settings:
    project_id: str = field(default_factory=lambda: _env("GCP_PROJECT"))
    raw_bucket: str = field(default_factory=lambda: _env("RAW_BUCKET"))
    start_date: str = field(default_factory=lambda: _env("START_DATE", "1990-01-01"))
    lookback_days: int = field(default_factory=lambda: int(_env("LOOKBCK_DAYS", "30")))
    full_refresh: bool = field(default_factory=lambda: _env("FULL_REFRESH", "false").lower() == "true")
    sheet_id: str = field(default_factory=lambda: _env("SHEET_ID", ""))

    @property
    def effective_start(self) -> str:
        if self.full_refresh:
            return self.start_date
        return (date.today() - timedelta(days=self.lookback_days)).isoformat()

    @property
    def end(self) -> str:
        return date.today().isoformat()


def get_secret(project_id: str, name: str) -> str:
    if os.environ.get(name):
        return os.environ[name]

    client = secretmanager.SecretManagerServiceClient()
    path = f'projects/{project_id}/secrets/{name}/versions/latest'
    return client.access_secret_version(request={'name': path}).payload.data.decode()