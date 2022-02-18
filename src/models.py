from datetime import datetime
from typing import Optional

from pydantic import AnyHttpUrl, conint
from pydantic.main import BaseModel


class MonitoringSetting(BaseModel):
    id: Optional[int]
    name: str
    url: AnyHttpUrl
    periodicity: Optional[conint(ge=30)] = 60
    timeout: Optional[conint(ge=3)] = 5
    pattern: Optional[str] = ''
    http_method: Optional[str] = 'GET'
    headers: Optional[str] = '{}'
    body: Optional[str] = '{}'


class Report(BaseModel):
    setting_id: int
    response_time: float
    status_code: int
    pattern_matched: bool
    timestamp: datetime
