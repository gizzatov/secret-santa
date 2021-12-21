import asyncio

from loguru import logger

from santa_bot import settings
from santa_bot.db.models import init_db
from santa_bot import tasks
from santa_bot.telegram.handlers.main import bot, dp, set_commands
from santa_bot.telegram.middlewares import AdminMiddleware


async def run_bot():
    logger.info('Starting bot')

    await init_db()

    # Установка команд бота
    await set_commands(bot)

    # Запуск поллинга
    await dp.start_polling()


def run_app(devserver=False):
    check_settings()
    loop = asyncio.get_event_loop()
    tasks.start()

    dp.middleware.setup(AdminMiddleware())
    loop.create_task(run_bot())
    loop.run_forever()


def check_settings():
    required_settings = [
        settings.DB_HOST,
        settings.DB_NAME,
        settings.DB_USER,
        settings.DB_PASSWORD,
        settings.API_TOKEN,
        settings.ADMIN_USERNAME,
    ]
    if not all(required_settings):
        logger.error('Some settings are unset')
        raise Exception
    
    logger.info('Settings checking: OK')
