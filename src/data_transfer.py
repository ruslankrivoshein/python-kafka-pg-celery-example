import json
import os
import sys

import psycopg2
from kafka import KafkaConsumer
from psycopg2._psycopg import parse_dsn

from models import Report


def put_report_into_db(conn, report: Report):
    with conn.cursor() as cursor:
        cursor.execute(
            f'INSERT INTO {os.environ["REPORT_TABLE_NAME"]} '
            f'(setting_id, response_time, status_code, '
            f'pattern_matched, timestamp) '
            f'VALUES '
            f'(%s, %s, %s, %s, %s)',
            (report.setting_id, report.response_time, report.status_code,
             report.pattern_matched, report.timestamp),
        )

    conn.commit()


def main(conn, consumer):
    for message in consumer:
        message = json.loads(message.value)
        report = Report.parse_obj(message)

        put_report_into_db(conn, report)


if __name__ == '__main__':
    sys.stdout.write('Start consuming\n')

    conn = psycopg2.connect(**parse_dsn(os.environ['POSTGRES_DSN']))

    consumer = KafkaConsumer(
        os.environ['KAFKA_MONITORING_TOPIC'],
        bootstrap_servers=os.environ['KAFKA_BROKER_URLS'],
        security_protocol='SSL',
        ssl_cafile=os.environ['KAFKA_SSL_CAFILE'],
        ssl_certfile=os.environ['KAFKA_SSL_CERTFILE'],
        ssl_keyfile=os.environ['KAFKA_KEYFILE'],
    )

    try:
        main(conn, consumer)
    except:
        sys.stdout.write('\nStop consuming\n')
    finally:
        conn.close()
        consumer.close()
