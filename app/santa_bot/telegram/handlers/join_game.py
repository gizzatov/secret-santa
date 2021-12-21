from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel
from aiogram_dialog.widgets.text import Const, Format

from santa_bot.db.models import Game, User, Player
from santa_bot.telegram.direct import send_message


class JoinGame(StatesGroup):
    code = State()
    admin = State()
    finish = State()


async def get_dialog_data(dialog_manager: DialogManager, **kwargs):
    dialog_manager.dialog()

    return {
        'admin': dialog_manager.current_context().dialog_data.get('admin'),
        'code': dialog_manager.current_context().dialog_data.get('code'),
        'started_at': dialog_manager.current_context().dialog_data.get('started_at'),
        'submitting_finished_at': dialog_manager.current_context().dialog_data.get('submitting_finished_at'),
        'finished_at': dialog_manager.current_context().dialog_data.get('finished_at'),
    }


async def code_handler(m: Message, dialog: Dialog, manager: DialogManager):
    code = m.text
    if ' ' in code:
        await m.answer('Код не может содержать пробелы')
        await manager.done()
        return

    game = await Game.filter(code=code).prefetch_related('admin').first()
    if not game:
        await m.answer('Игры с таким кодом не существует :(')
        await manager.done()
        return

    if not game.is_running:
        await m.answer('Регистрация в эту игру невозможна (еще не начата, или уже закончена)')
        await manager.done()
        return

    if not game.player_can_leave_or_join:
        await m.answer('Регистрация в эту игру невозможна (игроки уже распределены)')
        await manager.done()
        return

    user = await User.filter(chat_id=m.chat.id).first()
    if await Player.filter(user=user, game=game).exists():
        await m.answer('Вы уже являетесь участником этой игры :)')
        await manager.done()
        return

    manager.current_context().dialog_data['code'] = code
    manager.current_context().dialog_data['admin'] = game.admin.username
    manager.current_context().dialog_data['started_at'] = str(game.started_at.strftime("%d.%m.%Y"))
    manager.current_context().dialog_data['submitting_finished_at'] = str(game.submitting_finished_at.strftime("%d.%m.%Y"))
    manager.current_context().dialog_data['finished_at'] = str(game.finished_at.strftime("%d.%m.%Y"))
    await dialog.next(manager)


async def join_game_start(message: types.Message, dialog_manager: DialogManager):
    await dialog_manager.start(JoinGame.code, mode=StartMode.RESET_STACK)


async def join_game_finish(c: CallbackQuery, button: Button, manager: DialogManager):
    dialog_data = manager.current_context().dialog_data

    code = dialog_data['code']

    game = await Game.filter(code=code).prefetch_related('admin').first()
    user = await User.filter(chat_id=c.message.chat.id).first()

    await Player.create(
        user=user,
        game=game,
    )
    await c.message.answer('Вы успешно зарегистрировались в игре!')
    await manager.done()

    await send_message(chat_id=game.admin.chat_id, text=f'Пользователь @{user.username} присоединился к игре `{code}`')


join_game_dialog = Dialog(
    Window(
        Const('Для того, чтобы присоединиться к игре введите код который вам выдал администратор игры:'),
        Cancel(text=Const('Прервать')),
        MessageInput(code_handler),
        state=JoinGame.code,
    ),
    Window(
        Format(
            'Игра с кодом `{code}` найдена!\n'
            '\n Информация о данной игре:'
            '\n- админ: @{admin}'
            '\n- Игра начнется: {started_at}'
            '\n- Заявки принимаются до: {submitting_finished_at}'
            '\n- Игра завершится: {finished_at}'
            '\nПрисоединиться?'
        ),
        Button(Const('Присоединиться'), on_click=join_game_finish, id='finish'),
        state=JoinGame.finish,
        getter=get_dialog_data,
    )
)
