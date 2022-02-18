import os


def _build_dict(dotenv):
    return {
        n[0]: n[1]
        for n in [
            row.split('=') for row in dotenv.read().split('\n') if row
        ]
    }


def load_settings():
    try:
        with open('.env', 'r') as dotenv:
            settings = _build_dict(dotenv)
    except FileNotFoundError:
        with open('../.env', 'r') as dotenv:
            settings = _build_dict(dotenv)

    for name in settings.keys():
        os.environ[name] = settings[name]
