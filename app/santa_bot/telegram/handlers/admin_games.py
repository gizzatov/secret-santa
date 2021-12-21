import operator
from datetime import date
from random import randint
from typing import Any

from aiogram import types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, StartMode, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import (Back, Button, Cancel, Next, Row,
                                        Select, SwitchTo)
from aiogram_dialog.widgets.kbd.group import Column
from aiogram_dialog.widgets.text import Const, Format
from santa_bot.db.models import Game, Pair, Player, User
from santa_bot.telegram.keyboards import CustomCalendar
from santa_bot.telegram.middlewares import set_permission


async def get_game_info_dialog_data(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.current_context().start_data

    game = await Game.filter(id=start_data['game_id']).first()
    players_count = await Player.filter(game=game).count()
    return {
        'code': game.code,
        'description': game.description,
        'started_at': game.started_at.strftime("%d.%m.%Y"),
        'submitting_finished_at': game.submitting_finished_at.strftime("%d.%m.%Y"),
        'finished_at': game.finished_at.strftime("%d.%m.%Y"),
        'players_count': players_count,
    }


# Game delete
class DeleteGame(StatesGroup):
    deleted = State()


async def on_delete_game(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data

    game = await Game.filter(id=start_data['game_id']).first()
    if not game.player_can_leave_or_join:
        return await c.answer('Невозможно удалить игру')

    await manager.start(state=DeleteGame.deleted, data={'game_id': start_data['game_id']})


async def on_delete_game_finish(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data
    game = await Game.filter(id=start_data['game_id']).first()
    user_id = game.admin_id
    await game.delete()
    await manager.start(state=MyOwnedGame.game_id, mode=StartMode.RESET_STACK, data={'user_id': user_id})


delete_game_dialog = Dialog(
    Window(
        Format('Вы уверены?'),
        Row(
            Button(Const('Да'), id='yes', on_click=on_delete_game_finish),
            Cancel(text=Const('Назад')),
        ),
        state=DeleteGame.deleted,
    ),
)


# Game edit
class EditGame(StatesGroup):
    description = State()
    started_at = State()
    submitting_finished_at = State()
    finished_at = State()
    finish = State()


async def description_handler(m: Message, dialog: Dialog, manager: DialogManager):
    description = m.text

    manager.current_context().dialog_data['description'] = description
    await m.answer(f'Новое описание установлено: {description}')
    await dialog.next(manager)

async def started_at_selected(c: types.CallbackQuery, widget, manager: DialogManager, selected_date: date, dialog):
    manager.current_context().dialog_data['started_at'] = selected_date
    await c.message.answer(f'Новая дата начала сбора заявок: {str(selected_date.strftime("%d.%m.%Y"))}')
    await dialog.next(manager)


async def submitting_finished_at_selected(c: types.CallbackQuery, widget, manager: DialogManager, selected_date: date, dialog):
    manager.current_context().dialog_data['submitting_finished_at'] = selected_date
    await c.message.answer(f'Новая дата окончания сбора заявок: {str(selected_date.strftime("%d.%m.%Y"))}')
    await dialog.next(manager)


async def finished_at_selected(c: types.CallbackQuery, widget, manager: DialogManager, selected_date: date, dialog):
    manager.current_context().dialog_data['finished_at'] = selected_date
    await c.message.answer(f'Новая дата окончания игры: {str(selected_date.strftime("%d.%m.%Y"))}')
    await dialog.next(manager)


async def on_edit_game(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data
    await manager.start(state=EditGame.description, data={'game_id': start_data['game_id']})


@set_permission(permission='admin')
async def edit_game_finish(c: CallbackQuery, button: Button, manager: DialogManager):
    start_data = manager.current_context().start_data
    game = await Game.filter(id=start_data['game_id']).first()

    dialog_data = manager.current_context().dialog_data

    if 'description' in dialog_data:
        game.description = dialog_data['description']

    if 'started_at' in dialog_data:
        game.started_at = dialog_data['started_at']
    
    if 'submitting_finished_at' in dialog_data:
        game.submitting_finished_at = dialog_data['submitting_finished_at']

    if 'finished_at' in dialog_data:
        game.finished_at = dialog_data['finished_at']

    await game.save()

    await c.message.answer('Изменения внесены!')
    await manager.done()


edit_game_dialog = Dialog(
    Window(
        Format('Текущее описание игры: {description}. \nНовое описание игры:'),
        Row(
            Cancel(text=Const('Прервать')),
            Next(text=Const('Пропустить')),
        ),
        MessageInput(description_handler),
        state=EditGame.description,
        getter=get_game_info_dialog_data,
    ),
    Window(
        Format('Текущая дата начала сбора заявок: {started_at}. \nЗададим дату НАЧАЛА СБОРА ЗАЯВОК:'),
        CustomCalendar(id='calendar', on_click=started_at_selected),
        Row(
            Back(text=Const('Назад')),
            Next(text=Const('Пропустить')),
            Cancel(text=Const('Прервать')),
        ),
        state=EditGame.started_at,
        getter=get_game_info_dialog_data,
    ),
    Window(
        Format('Текущая дата окончания сбора заявок: {submitting_finished_at}. \nЗададим дату ОКОНЧАНИЯ СБОРА ЗАЯВОК:'),
        CustomCalendar(id='calendar', on_click=submitting_finished_at_selected),
        Row(
            Back(text=Const('Назад')),
            Next(text=Const('Пропустить')),
            Cancel(text=Const('Прервать')),
        ),
        state=EditGame.submitting_finished_at,
        getter=get_game_info_dialog_data,
    ),
    Window(
        Format('Текущая дата окончания игры: {finished_at}. \nЗададим дату ОКОНЧАНИЯ ИГРЫ:'),
        CustomCalendar(id='calendar', on_click=finished_at_selected),
        Row(
            Back(text=Const('Назад')),
            Next(text=Const('Пропустить')),
            Cancel(text=Const('Прервать')),
        ),
        state=EditGame.finished_at,
        getter=get_game_info_dialog_data,
    ),
    Window(
        Const('Это были все вопросы. Вы можете перезапустить опросник или сохранить'),
        Row(
            Back(text=Const('Назад')),
            SwitchTo(Const('Перезапустить'), id='restart', state=EditGame.description),
            Button(Const('Сохранить игру'), on_click=edit_game_finish, id='finish'),
        ),
        state=EditGame.finish,
    )
)


# Player add
class AddPlayer(StatesGroup):
    full_name = State()
    preferences = State()
    description = State()
    finish = State()


async def fullname_handler(m: Message, dialog: Dialog, manager: DialogManager):
    full_name = m.text

    manager.current_context().dialog_data['player_full_name'] = full_name
    await m.answer(f'Имя игрока: {full_name}')
    await dialog.next(manager)


async def preferences_handler(m: Message, dialog: Dialog, manager: DialogManager):
    preferences = m.text

    manager.current_context().dialog_data['player_preferences'] = preferences
    await m.answer(f'Предпочтения установлены:\n{preferences}')
    await dialog.next(manager)


async def description_handler(m: Message, dialog: Dialog, manager: DialogManager):
    description = m.text

    manager.current_context().dialog_data['player_description'] = description
    await m.answer(f'Описание установлено: {description}')
    await dialog.next(manager)


@set_permission(permission='admin')
async def on_add_player_game(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data
    await manager.start(state=AddPlayer.full_name, data={'game_id': start_data['game_id']})


@set_permission(permission='admin')
async def add_player_finish(c: CallbackQuery, button: Button, manager: DialogManager):
    start_data = manager.current_context().start_data
    game = await Game.filter(id=start_data['game_id']).first()

    dialog_data = manager.current_context().dialog_data

    user = await User.create(
        is_tg_user=False,
        full_name=dialog_data['player_full_name'],
        preferences=dialog_data['player_preferences'],
        description=dialog_data['player_description'],
    )

    await Player.create(game=game, user=user)

    await c.message.answer('Новый игрок добавлен к игре!')
    await manager.done()


add_player_dialog = Dialog(
    Window(
        Format('Добавление нового игрока (у которого нет телеграма)\nВведите имя игрока:'),
        Cancel(text=Const('Прервать')),
        MessageInput(fullname_handler),
        state=AddPlayer.full_name,
    ),
    Window(
        Format('Введите предпочтения игрока (если они есть):'),
        Cancel(text=Const('Прервать')),
        MessageInput(preferences_handler),
        state=AddPlayer.preferences,
    ),
    Window(
        Format(
            'Введите описание игрока (это поле доступно только админу, '
            'вы можете написать туда контактные данные человека, чтобы понять как с ним связаться):'
        ),
        Cancel(text=Const('Прервать')),
        MessageInput(description_handler),
        state=AddPlayer.description,
    ),
    Window(
        Const('Это были все вопросы. Вы можете перезапустить опросник или сохранить'),
        Row(
            Back(text=Const('Назад')),
            SwitchTo(Const('Перезапустить'), id='restart', state=AddPlayer.full_name),
            Button(Const('Сохранить игрока'), on_click=add_player_finish, id='finish'),
        ),
        state=AddPlayer.finish,
    )
)


# Player delete
class DeletePlayer(StatesGroup):
    deleted = State()


async def on_delete_player(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data

    player = await Player.filter(id=start_data['player_id']).prefetch_related('game').first()
    if not player.game.player_can_leave_or_join:
        return await c.answer('Невозможно удалить пользователя')

    await manager.start(state=DeletePlayer.deleted, data={'player_id': start_data['player_id']})


async def on_delete_player_finish(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data
    player = await Player.filter(id=start_data['player_id']).first()
    game_id = player.game_id
    await player.delete()
    await manager.start(state=PlayersList.player_id, mode=StartMode.RESET_STACK, data={'game_id': game_id})


delete_player_dialog = Dialog(
    Window(
        Format('Вы уверены?'),
        Row(
            Button(Const('Да'), id='yes', on_click=on_delete_player_finish),
            Cancel(text=Const('Назад')),
        ),
        state=DeletePlayer.deleted,
    ),
)


# Player info
class PlayerInfo(StatesGroup):
    player_id = State()


async def get_player_info_dialog_data(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.current_context().start_data

    player = await Player.filter(id=start_data['player_id']).prefetch_related('user').first()
    user = player.user
    return {
        'full_name': user.full_name,
        'username': user.username or '',
        'description': user.description,
        'preferences': user.preferences,
        'is_tg_user': 'ДА' if user.is_tg_user else 'НЕТ',
    }


player_info_dialog = Dialog(
    Window(
        Format(
            'Информация об игроке:\n'
            '\n- Имя: {full_name}'
            '\n- Телеграм Юзернейм: @{username}'
            '\n- Предпочтения: {preferences}'
            '\n- Описание: {description}'
            '\n- Пользователь телеграм: {is_tg_user}'
        ),
        Button(Const('Удалить игрока'), id='player_delete', on_click=on_delete_player),
        Cancel(text=Const('Назад')),
        state=PlayerInfo.player_id,
        getter=get_player_info_dialog_data,
    ),
)


# Players list
class PlayersList(StatesGroup):
    player_id = State()


async def get_player_list_dialog_data(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.current_context().start_data
    game = await Game.filter(id=start_data['game_id']).first()

    players = await Player.filter(game=game).prefetch_related('user').all()

    return {'players': [(p.user.full_name, p.id) for p in players]}


@set_permission(permission='admin')
async def on_player_list(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data
    await manager.start(state=PlayersList.player_id, data={'game_id': start_data['game_id']})


async def on_player_selected(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: int):
    await manager.start(state=PlayerInfo.player_id, data={'player_id': item_id})


players_kbd = Select(
    Format('- {item[0]}'),
    id='s_player',
    item_id_getter=operator.itemgetter(1),
    items='players',
    on_click=on_player_selected,
)


player_list_dialog = Dialog(
    Window(
        Const('Список игроков:'),
        Column(players_kbd),
        Cancel(text=Const('Прервать')),
        state=PlayersList.player_id,
        getter=get_player_list_dialog_data,
    ),
)


# Santas select
@set_permission(permission='admin')
async def on_select_santas(c: CallbackQuery, widget: Any, manager: DialogManager):
    start_data = manager.current_context().start_data
    game = await Game.filter(id=start_data['game_id']).first()

    if not game.status == Game.STATUSES.NEW:
        await manager.done()
        return await c.answer('Санты уже были выбраны')

    santas = await game.players.all()
    if len(santas) <= 1:
        await manager.done()
        return await c.answer('Слишком мало игроков')

    if len(santas) % 2 != 0:
        await manager.done()
        return await c.answer('Нечетное количество игроков. Не могу распределить.')

    targets = santas.copy()

    leftover = None

    targets_in_pair = []
    while santas:
        if len(santas) == 1:
            leftover = santas[0]
            break

        santa = santas.pop(randint(0, len(santas)-1))
        target = santas.pop(randint(0, len(santas)-1))

        targets_in_pair.append(target.id)

        await Pair.create(
            game=game,
            santa_id=santa.user_id,
            target_id=target.user_id,
            code=randint(100000, 999999),
        )

        santa = target
        target = None
        while target is None:
            next_target_id = randint(0, len(targets)-1)
            if targets[next_target_id].id not in targets_in_pair:
                target = targets.pop(next_target_id)
                break

        await Pair.create(
            game=game,
            santa_id=santa.user_id,
            target_id=target.user_id,
            code=randint(100000, 999999),
        )

    game.status = Game.STATUSES.SANTAS_SELECTED
    await game.save()
    await manager.done()
    if leftover:
        await c.message.answer('Санты распределены! Но остался игрок без пары :(')
    else:
        await c.message.answer('Санты распределены!')


# Game info
class OwnedGameInfo(StatesGroup):
    game_id = State()


my_own_game_info_dialog = Dialog(
    Window(
        Format(
            'Информация об игре`{code}`:\n'
            '\n- Описание: {description}'
            '\n- Игроков зарегистрированно: {players_count}'
            '\n- Игра начнется: {started_at}'
            '\n- Заявки принимаются до: {submitting_finished_at}'
            '\n- Игра завершится: {finished_at}'
        ),
        Column(
            Button(Const('Изменить игру'), id='edit_game', on_click=on_edit_game),
            Button(Const('Добавить игрока'), id='add_player', on_click=on_add_player_game),
            Button(Const('Список игроков'), id='player_list', on_click=on_player_list),
            Button(Const('Распределить сант'), id='reveal_santas', on_click=on_select_santas),
            # Button(Const('Раскрыть сант'), id='reveal_santas', on_click=on_reveal_santas),
            Button(Const('Удалить игру'), id='delete_game', on_click=on_delete_game),
        ),
        Cancel(text=Const('Назад')),
        state=OwnedGameInfo.game_id,
        getter=get_game_info_dialog_data,
    ),
)


# Main
class MyOwnedGame(StatesGroup):
    game_id = State()


async def get_own_game_main_dialog_data(dialog_manager: DialogManager, **kwargs):
    start_data = dialog_manager.current_context().start_data

    user = await User.filter(id=start_data['user_id']).first()
    user_games = await Game.filter(admin=user).all()

    games = [(g.code, g.id) for g in user_games]
    return {'games': games}


async def on_game_selected(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: int):
    await manager.start(state=OwnedGameInfo.game_id, data={'game_id': item_id})


@set_permission(permission='admin')
async def my_own_games_start(message: types.Message, dialog_manager: DialogManager):
    user = await User.filter(chat_id=message.chat.id).first()
    await dialog_manager.start(MyOwnedGame.game_id, mode=StartMode.RESET_STACK, data={'user_id': user.id})


games_kbd = Select(
    Format('- {item[0]}'),
    id='s_game',
    item_id_getter=operator.itemgetter(1),
    items='games',
    on_click=on_game_selected,
)


my_own_games_dialog = Dialog(
    Window(
        Const('Список игр в которых вы админ (вы можете управлять ими, нажимая на кнопку игры):'),
        Column(games_kbd),
        Cancel(text=Const('Прервать')),
        state=MyOwnedGame.game_id,
        getter=get_own_game_main_dialog_data,
    ),
)
