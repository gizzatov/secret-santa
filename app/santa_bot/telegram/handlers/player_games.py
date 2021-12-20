import operator
from typing import Any

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Row, Select
from aiogram_dialog.widgets.kbd.group import Column
from aiogram_dialog.widgets.text import Const, Format
from santa_bot.db.models import Player, User


class LeaveGame(StatesGroup):
    leave = State()


async def on_game_leave(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data

    player = await Player.filter(id=start_data['player_id']).prefetch_related('game', 'game__admin').first()

    if player.game.player_can_leave_or_join:
        await manager.start(state=LeaveGame.leave, data={'player_id': start_data['player_id']})
    else:
        await manager.done()
        await c.message.answer(f'Вы не можете покинуть игру. Игроки уже распределены. Обратитесь к @{player.game.admin.username}')


async def on_game_leave_finish(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data
    player = await Player.filter(id=start_data['player_id']).first()
    user_id = player.user_id
    await player.delete()
    await manager.start(state=MyActiveGame.game_id, mode=StartMode.RESET_STACK, data={'user_id': user_id})


leave_game_dialog = Dialog(
    Window(
        Format('Вы уверены?'),
        Row(
            Button(Const('Да'), id='yes', on_click=on_game_leave_finish),
            Cancel(text=Const('Назад')),
        ),
        state=LeaveGame.leave,
    ),
)


class ActiveGameInfo(StatesGroup):
    game_id = State()


async def get_game_info__dialog_data(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.current_context().start_data

    player = await Player.filter(id=start_data['player_id']).prefetch_related('game', 'game__admin').first()
    game = player.game
    return {
        'admin': game.admin.username,
        'code': game.code,
        'started_at': game.started_at,
        'submitting_finished_at': game.submitting_finished_at,
        'finished_at': game.finished_at,
    }


my_game_info_dialog = Dialog(
    Window(
        Format(
            'Информация об игре`{code}`:\n'
            '\n- админ: @{admin}'
            '\n- Игра начнется: {started_at}'
            '\n- Заявки принимаются до: {submitting_finished_at}'
            '\n- Игра завершится: {finished_at}'
        ),
        Button(Const('Выйти из игры'), id='leave', on_click=on_game_leave),
        Cancel(text=Const('Назад')),
        state=ActiveGameInfo.game_id,
        getter=get_game_info__dialog_data,
    ),
)


class MyActiveGame(StatesGroup):
    game_id = State()


async def get_my_games_main_dialog_data(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.current_context().start_data

    user = await User.filter(id=start_data['user_id']).first()
    user_games = await Player.filter(user=user).prefetch_related('game').all()

    games = [(ug.game.code, ug.id) for ug in user_games]
    return {
        'games': games,
    }


async def on_my_game_selected(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: int):
    await manager.start(state=ActiveGameInfo.game_id, data={'player_id': item_id})


async def my_games_start(message: types.Message, dialog_manager: DialogManager):
    user = await User.filter(chat_id=message.chat.id).first()
    await dialog_manager.start(MyActiveGame.game_id, mode=StartMode.RESET_STACK, data={'user_id': user.id})


games_kbd = Select(
    Format('- {item[0]}'),
    id='active_game',
    item_id_getter=operator.itemgetter(1),
    items='games',
    on_click=on_my_game_selected,
)


my_games_dialog = Dialog(
    Window(
        Const('Список игр в которых вы зарегистрированны (вы можете управлять ими, нажимая на кнопку игры):'),
        Column(games_kbd),
        Cancel(text=Const('Прервать')),
        state=MyActiveGame.game_id,
        getter=get_my_games_main_dialog_data,
    ),
)
