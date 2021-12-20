import os

from dotenv import load_dotenv

load_dotenv()

# DB
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT', 5432)

# ORM
TORTOISE_ORM = {
    'connections': {
        'models': {  # this name is equal to app name. it is little hack for tests
            'engine': 'tortoise.backends.asyncpg',
            'credentials': {
                'host': DB_HOST,
                'port': DB_PORT,
                'user': DB_USER,
                'password': DB_PASSWORD,
                'database': DB_NAME,
            }
        },
    },
    'apps': {
        'models': {
            'models': ['santa_bot.db.models', 'aerich.models'],
            'default_connection': 'models',
        }
    },
    'use_tz': True,
    'timezone': 'UTC'
}

API_TOKEN = os.getenv('API_TOKEN')
