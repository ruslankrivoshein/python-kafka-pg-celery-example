import os
import sys

import psycopg2
import typer
from celery import Celery
from celery.schedules import schedule
from psycopg2._psycopg import parse_dsn
from pydantic import ValidationError
from redbeat import RedBeatSchedulerEntry

from dotenv_parser import load_settings
from models import MonitoringSetting

load_settings()
typer_app = typer.Typer()


def get_monitoring_setting(conn, id) -> MonitoringSetting:
    with conn.cursor() as cursor:
        cursor.execute(
            f'SELECT * FROM {os.environ["MONITORING_TABLE_NAME"]} '
            f'WHERE id = %s;',
            (id, ),
        )
        record = cursor.fetchone()

    setting = {}

    for column, value in zip(cursor.description, record):
        setting[column[0]] = value

    return MonitoringSetting.parse_obj(setting)


def insert_setting_into_db(
    conn, setting: MonitoringSetting,
) -> MonitoringSetting:
    with conn.cursor() as cursor:
        cursor.execute(
            f'INSERT INTO {os.environ["MONITORING_TABLE_NAME"]} '
            '(name, url, periodicity, timeout, pattern, headers) '
            'VALUES (%s, %s, %s, %s, %s, %s) '
            'RETURNING id, name;',
            (setting.name, setting.url, setting.periodicity,
             setting.timeout, setting.pattern, setting.headers),
        )

        setting.id, name = cursor.fetchone()

    conn.commit()

    return setting


def create_periodic_monitoring_task(setting: MonitoringSetting):
    with Celery(set_as_current=False) as app:
        app.conf.broker_url = os.environ['CELERY_BROKER_URL']
        app.conf.redbeat_redis_url = os.environ['REDBEAT_BROKER_URL']

        task = RedBeatSchedulerEntry(
            f'monitoring_{setting.id}',
            'tasks.monitor',
            schedule(setting.periodicity),
            (setting.json(),),
            app=app,
        )
        task.save()


@typer_app.command()
def add(
    name: str = typer.Argument(..., help='Name of setting'),
    url: str = typer.Argument(..., help='URL for monitoring'),
    periodicity: int = typer.Option(60, help='How many seconds to wait for '
                                             'the server to do a new request'),
    timeout: int = typer.Option(5, help='How many seconds to wait for '
                                        'the server to do a new request '
                                        'after failed'),
    pattern: str = typer.Option('', help='Regexp to search on site content'),
    http_method: str = typer.Option('GET', help='HTTP method for query'),
    headers: str = typer.Option('{}', help='JSON-string of headers '
                                           'to send every time in request'),
    body: str = typer.Option('{}', help='JSON-string of params for '
                                        'body of request '
                                        'if http_method supports body'),
):
    """
    Register a new monitoring setting
    """
    try:
        setting = MonitoringSetting(
            name=name,
            url=url,
            periodicity=periodicity,
            timeout=timeout,
            pattern=pattern,
            http_method=http_method,
            headers=headers,
            body=body,
        )
    except ValidationError as e:
        sys.stdout.write(str(e) + '\n')

        return

    conn = psycopg2.connect(**parse_dsn(os.environ['POSTGRES_DSN']))

    try:
        setting = insert_setting_into_db(conn, setting)
    except:
        sys.stdout.write('Some error occured during registration. Try later\n')
        return False
    finally:
        conn.close()

    create_periodic_monitoring_task(setting)

    sys.stdout.write(f'You have registered a new setting '
                     f'with name "{setting.name}" and '
                     f'ID {formatted_id(setting.id)}.\n'
                     f'\033[93mKeep this ID to manipulate '
                     f'the task later\033[0m\n')


@typer_app.command()
def remove(id: str = typer.Argument(...)):
    """
    Remove a monitoring setting by ID
    """
    with Celery(set_as_current=False) as app:
        app.conf.broker_url = os.environ['CELERY_BROKER_URL']
        app.conf.redbeat_redis_url = os.environ['REDBEAT_BROKER_URL']

        task = RedBeatSchedulerEntry.from_key('redbeat:monitoring_' + id, app)

        task.delete()

    conn = psycopg2.connect(**parse_dsn(os.environ['POSTGRES_DSN']))

    with conn.cursor() as cursor:
        cursor.execute(f'DELETE FROM {os.environ["MONITORING_TABLE_NAME"]} '
                       f'WHERE id = %s',
                       (id,))

    conn.commit()
    conn.close()

    sys.stdout.write(
        f'Task {formatted_id(id)} was removed\n',
    )


@typer_app.command()
def start(id: str = typer.Argument(...)):
    """
    Start/resume monitoring task by setting ID
    """
    sys.stdout.write('This command is not implemented yet\n')


@typer_app.command()
def stop(id: str = typer.Argument(...)):
    """
    Stop monitoring task by setting ID
    """
    sys.stdout.write('This command is not implemented yet\n')


@typer_app.command('list')
def get_settings_list():
    """
    List of settings
    """
    conn = psycopg2.connect(**parse_dsn(os.environ['POSTGRES_DSN']))

    with conn.cursor() as cursor:
        cursor.execute(
            f'SELECT id, name FROM {os.environ["MONITORING_TABLE_NAME"]};',
        )

        settings = cursor.fetchall()

    conn.close()

    sys.stdout.write('{:^10} {:^20}\n'.format('ID', 'NAME'))
    sys.stdout.write('-' * 31 + '\n')

    for setting in settings:
        sys.stdout.write('{:^10} {:^20}\n'.format(setting[0], setting[1]))


def formatted_id(id) -> str:
    return f'\033[92m{id}\033[0m'


if __name__ == '__main__':
    typer_app()
