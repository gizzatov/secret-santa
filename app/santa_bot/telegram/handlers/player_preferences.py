from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Row
from aiogram_dialog.widgets.text import Const, Format

from santa_bot.db.models import User


class MyPreferences(StatesGroup):
    preference = State()
    finish = State()


async def get_my_preferences_dialog_data(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.current_context().start_data
    user = await User.filter(id=start_data['user_id']).first()
    return {'preferences': user.preferences or ''}


async def edit_preferences_start(message: types.Message, dialog_manager: DialogManager):
    user = await User.filter(chat_id=message.chat.id).first()
    await dialog_manager.start(MyPreferences.preference, mode=StartMode.RESET_STACK, data={'user_id': user.id})


async def edit_preferences_finish(c: CallbackQuery, button: Button, manager: DialogManager):
    start_data = manager.current_context().start_data
    user = await User.filter(id=start_data['user_id']).first()

    dialog_data = manager.current_context().dialog_data

    user.preferences = dialog_data['preferences']
    await user.save()

    await c.message.answer('Изменения внесены!')
    await manager.done()


async def edit_preference_handler(m: Message, dialog: Dialog, manager: DialogManager):
    preferences = m.text

    manager.current_context().dialog_data['preferences'] = preferences
    await m.answer(f'Новые предпочтения установлены:\n{preferences}')
    await dialog.next(manager)


edit_preferences_dialog = Dialog(
    Window(
        Format(
            'В этом разделе вы можете установить свои предпочтения, которые ваш тайный санта может учесть во время подбора подарка.'
            '\nНа данный момент выставленны следующие предпочтения, напишите новые, если есть необходимость:\n{preferences}\n'
        ),
        MessageInput(edit_preference_handler),
        Cancel(text=Const('Прервать')),
        state=MyPreferences.preference,
        getter=get_my_preferences_dialog_data,
    ),
    Window(
        Const('Сохранить изменения?'),
        Row(
            Back(text=Const('Назад')),
            Button(Const('Сохранить'), on_click=edit_preferences_finish, id='finish'),
        ),
        state=MyPreferences.finish,
    )
)
