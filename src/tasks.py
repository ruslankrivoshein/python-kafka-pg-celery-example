import html
import json
import os
import re
from datetime import datetime

import requests
from celery import Celery
from kafka import KafkaProducer

import celeryconfig
from models import MonitoringSetting, Report

celery_app = Celery()
celery_app.config_from_object(celeryconfig)


def get_timestamp():
    return datetime.now().astimezone().isoformat()


def do_request(setting: MonitoringSetting) -> Report:
    response = requests.request(
        method=setting.http_method,
        url=setting.url,
        headers=json.loads(setting.headers),
        json=json.loads(setting.body),
    )

    rx = re.compile(setting.pattern)

    pattern_matched = (True
                       if rx.search(html.unescape(response.text))
                       else False)

    return Report(
        setting_id=setting.id,
        response_time=response.elapsed.total_seconds(),
        status_code=response.status_code,
        pattern_matched=pattern_matched,
        timestamp=get_timestamp(),
    )


@celery_app.task
def monitor(setting):
    setting = MonitoringSetting.parse_obj(json.loads(setting))

    report = do_request(setting)

    producer = KafkaProducer(
        bootstrap_servers=os.environ['KAFKA_BROKER_URLS'],
        compression_type='gzip',
        security_protocol='SSL',
        ssl_cafile=os.environ['KAFKA_SSL_CAFILE'],
        ssl_certfile=os.environ['KAFKA_SSL_CERTFILE'],
        ssl_keyfile=os.environ['KAFKA_KEYFILE'],
    )

    producer.send(
        os.environ['KAFKA_MONITORING_TOPIC'],
        str.encode(report.json()),
    )
