import datetime

import pytest
import requests
from pydantic import ValidationError

from dotenv_parser import load_settings
from models import MonitoringSetting, Report
from tasks import do_request

load_settings()


class MockResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.elapsed = datetime.timedelta(seconds=1)
        self.text = ''


@pytest.fixture
def setting():
    return MonitoringSetting(
        id=1,
        user_id=1,
        name='Google',
        url='https://google.com',
        periodicity=50,
    )


def test_correct_report_after_successful_request_to_website(
    monkeypatch, setting,
):
    def mock_request(*args, **kwargs):
        return MockResponse(200)

    monkeypatch.setattr(requests, 'request', mock_request)

    report = do_request(setting)

    assert report == Report(
        setting_id=setting.id,
        response_time=1.0,
        status_code=200,
        pattern_matched=True,
        timestamp=report.timestamp,
    )


def test_exceptions_on_models_validation():
    with pytest.raises(ValidationError):
        MonitoringSetting(name='test', url='bad url')

    with pytest.raises(ValidationError):
        MonitoringSetting(name='test', url='http://good.url', periodicity=20)

    with pytest.raises(ValidationError):
        MonitoringSetting(name='test', url='http://good.url', periodicity=-5)

    with pytest.raises(ValidationError):
        MonitoringSetting(name='test', url='http://good.url', timeout=0)
