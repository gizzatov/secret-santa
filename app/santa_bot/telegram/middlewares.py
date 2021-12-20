from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler, current_handler

from santa_bot.db.models import User


class AdminMiddleware(BaseMiddleware):

    async def on_process_message(self, message: types.Message, data: dict):
        handler = current_handler.get()

        if handler:
            permission = getattr(handler, 'bot_permission', None)
            if permission == 'admin':

                if message.chat.type == 'private':
                    chat_id = message.chat.id
                else:
                    chat_id = message.from_user['id']

                user = await User.filter(chat_id=chat_id).first()
                if not user or (user and not user.is_moderator):
                    answer = 'А ты хитрый. Но я хитрее 🤫'
                    await message.answer(answer)
                    raise CancelHandler()


def set_permission(permission: str):
    """
    Decorator for configuring permission for different handlers

    :param permission:
    :return:
    """

    def decorator(func):
        setattr(func, 'bot_permission', permission)
        return func

    return decorator
