import os

broker_url = os.environ['CELERY_BROKER_URL']
redbeat_redis_url = os.environ['REDBEAT_BROKER_URL']

imports = ('tasks',)

beat_scheduler = 'redbeat.RedBeatScheduler'
beat_max_loop_interval = 5
