from configs.base_config import Config


class TestConfig(Config):
    DATABASE_URL = 'postgresql://localhost/athena_test?user=fjl2401&password=newpass'
    DEBUG = True
