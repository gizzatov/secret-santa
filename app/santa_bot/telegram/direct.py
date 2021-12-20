import asyncio

from aiogram.utils import exceptions
from loguru import logger

from santa_bot.telegram.handlers import bot


async def send_message(chat_id: int, text: str, disable_notification: bool = False) -> bool:
    """
    Safe messages sender

    :param chat_id:
    :param text:
    :param disable_notification:
    :return:
    """
    try:
        await bot.send_message(chat_id, text, disable_notification=disable_notification)
    except exceptions.BotBlocked:
        logger.error(f'Target [ID:{chat_id}]: blocked by user')
    except exceptions.ChatNotFound:
        logger.error(f'Target [ID:{chat_id}]: invalid user ID')
    except exceptions.RetryAfter as e:
        logger.error(f'Target [ID:{chat_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds.')
        await asyncio.sleep(e.timeout)
        return await send_message(chat_id, text)  # Recursive call
    except exceptions.UserDeactivated:
        logger.error(f'Target [ID:{chat_id}]: user is deactivated')
    except exceptions.TelegramAPIError:
        logger.exception(f'Target [ID:{chat_id}]: failed')
    else:
        logger.info(f'Target [ID:{chat_id}]: success')
        return True
    return False
