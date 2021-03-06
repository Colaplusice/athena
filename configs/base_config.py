import os


class Config:
    CACHE_PREFIX = "athena"
    CACHE_HOST = "localhost"
    CACHE_DB = 0
    CACHE_PORT = 6379

    LONG_CACHE_TTL = 1 * 24 * 60 * 60
    SHORT_CACHE_TTL = 10 * 60

    REDIS_HOST = "localhost"
    REDIS_DB = 0
    REDIS_PORT = 6379
    # celery
    # redis 作为消息队列
    BROKER_URL = "redis://localhost:6379/1"
    CELERY_TASK_PROTOCOL = 1
    CELERY_RESULT_BACKEND = "redis://localhost:6379/1"

    CELERY_ACCEPT_CONTENT = ["json"]
    CELERYBEAT_SCHEDULE = {}

    DATABASE_URL = "postgresql://localhost/athena?user=fjl2401&password=newpass"
    REDLOCK_TIMEOUT = 10
    REDLOCK_BLOCKING_TIMEOUT = 5
    # database
    DB_CLIENT_CHARSET = "utf8mb4"
    PW_CONN_PARAMS = {"charset": DB_CLIENT_CHARSET, "stale_timeout": 1800}
    # email
    MAIL_SERVER = "smtp.qq.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USERNAME = "fjl2401@qq.com"
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    EMAIL_LIST = ["fjl2401@163.com", "826077013@qq.com", "441070584@qq.com"]
    SECRET_KEY = "hard to guess"
    MAIL_SENDER = "fjl2401@qq.com"
    MAIL_USE_SSL = True
    DETECTION_METHOD = "hog"
