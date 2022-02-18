import os

import psycopg2
from psycopg2.extensions import parse_dsn

conn = psycopg2.connect(**parse_dsn(os.environ['POSTGRES_DSN']))

with conn.cursor() as cursor:
    cursor.execute(f'CREATE TABLE IF NOT EXISTS '
                   f'{os.environ["MONITORING_TABLE_NAME"]} ('
                   f'id serial PRIMARY KEY,'
                   f'name text NOT NULL,'
                   f'url text,'
                   f'periodicity integer,'
                   f'timeout integer,'
                   f'pattern text,'
                   f'http_method text,'
                   f'headers text,'
                   f'body text);')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS '
                   f'{os.environ["REPORT_TABLE_NAME"]} ('
                   f'setting_id integer REFERENCES '
                   f'{os.environ["MONITORING_TABLE_NAME"]},'
                   f'response_time real NOT NULL,'
                   f'status_code integer NOT NULL,'
                   f'pattern_matched boolean NOT NULL,'
                   f'timestamp timestamptz NOT NULL);')

conn.commit()
conn.close()
