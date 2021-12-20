from datetime import date

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Row, SwitchTo, Cancel
from aiogram_dialog.widgets.text import Const

from santa_bot.db.models import Game, User
from santa_bot.telegram.keyboards import CustomCalendar
from santa_bot.telegram.middlewares import set_permission


class NewGame(StatesGroup):
    code = State()
    description = State()
    finish = State()
    started_at = State()
    submitting_finished_at = State()
    finished_at = State()


async def code_handler(m: Message, dialog: Dialog, manager: DialogManager):
    code = m.text
    if ' ' in code:
        return await m.answer('Код не может содержать пробелы')

    if await Game.filter(code=code).exists():
        return await m.answer('Игра с таким кодом уже существует :(')

    manager.current_context().dialog_data['code'] = code
    await m.answer(f'Код установлен: {code}')
    await dialog.next(manager)


async def description_handler(m: Message, dialog: Dialog, manager: DialogManager):
    description = m.text

    manager.current_context().dialog_data['description'] = description
    await m.answer(f'Описание установлено: {description}')
    await dialog.next(manager)

async def started_at_selected(c: types.CallbackQuery, widget, manager: DialogManager, selected_date: date, dialog):
    manager.current_context().dialog_data['started_at'] = selected_date
    await c.message.answer(f'Дата начала сбора заявок: {str(selected_date)}')
    await dialog.next(manager)


async def submitting_finished_at_selected(c: types.CallbackQuery, widget, manager: DialogManager, selected_date: date, dialog):
    manager.current_context().dialog_data['submitting_finished_at'] = selected_date
    await c.message.answer(f'Дата окончания сбора заявок: {str(selected_date)}')
    await dialog.next(manager)


async def finished_at_selected(c: types.CallbackQuery, widget, manager: DialogManager, selected_date: date, dialog):
    manager.current_context().dialog_data['finished_at'] = selected_date
    await c.message.answer(f'Дата окончания игры: {str(selected_date)}')
    await dialog.next(manager)


@set_permission(permission='admin')
async def new_game_start(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(NewGame.code, mode=StartMode.RESET_STACK)


@set_permission(permission='admin')
async def new_game_finish(c: CallbackQuery, button: Button, manager: DialogManager):
    user = await User.filter(chat_id=c.message.chat.id).first()

    dialog_data = manager.current_context().dialog_data

    code = dialog_data['code']
    await Game.create(
        admin=user,
        code=code,
        description=dialog_data['description'],
        started_at=dialog_data['started_at'],
        submitting_finished_at=dialog_data['submitting_finished_at'],
        finished_at=dialog_data['finished_at'],
    )

    await c.message.answer(
        f'Спасибо, можете передать код игрокам: {code}.'
        '\nЧтобы повторить создание игры вызовите команду /new_game'
        '\nЧтобы показать все созданные ранне игры вызовите /owned_games')
    await manager.done()


new_game_dialog = Dialog(
    Window(
        Const('Создаём новую игру. Введите код новой игры (вы выдатите игрокам его):'),
        Cancel(text=Const('Прервать')),
        MessageInput(code_handler),
        state=NewGame.code,
    ),
    Window(
        Const('Зададим описание игры. Описание игры будете видеть только вы, как админ. Это поможет не путаться в кодах:'),
        Row(
            Back(text=Const('Назад')),
            Cancel(text=Const('Прервать')),
        ),
        MessageInput(description_handler),
        state=NewGame.description,
    ),
    Window(
        Const('Зададим дату НАЧАЛА СБОРА ЗАЯВОК:'),
        CustomCalendar(id='calendar', on_click=started_at_selected),
        Row(
            Back(text=Const('Назад')),
            Cancel(text=Const('Прервать')),
        ),
        state=NewGame.started_at,
    ),
    Window(
        Const('Зададим дату ОКОНЧАНИЯ СБОРА ЗАЯВОК:'),
        CustomCalendar(id='calendar', on_click=submitting_finished_at_selected),
        Row(
            Back(text=Const('Назад')),
            Cancel(text=Const('Прервать')),
        ),
        state=NewGame.submitting_finished_at,
    ),
    Window(
        Const('Зададим дату ОКОНЧАНИЯ ИГРЫ:'),
        CustomCalendar(id='calendar', on_click=finished_at_selected),
        Row(
            Back(text=Const('Назад')),
            Cancel(text=Const('Прервать')),
        ),
        state=NewGame.finished_at,
    ),
    Window(
        Const('Это были все вопросы. Вы можете перезапустить опросник или сохранить. Вы сможете в дальнейшем внести изменения в созданную игру:'),
        Row(
            Back(text=Const('Назад')),
            SwitchTo(Const('Перезапустить'), id='restart', state=NewGame.code),
            Button(Const('Сохранить игру'), on_click=new_game_finish, id='finish'),
        ),
        state=NewGame.finish,
    )
)
