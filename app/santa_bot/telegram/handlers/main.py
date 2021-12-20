from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram_dialog import DialogRegistry
from santa_bot.db.models import Game, User
from santa_bot.telegram.handlers import bot
from santa_bot.telegram.handlers.admin_games import (delete_game_dialog,
                                                     edit_game_dialog,
                                                     my_own_game_info_dialog,
                                                     my_own_games_dialog,
                                                     my_own_games_start, add_player_dialog, player_list_dialog, player_info_dialog, delete_player_dialog)
from santa_bot.telegram.handlers.join_game import (join_game_dialog,
                                                   join_game_start)
from santa_bot.telegram.handlers.new_game import (new_game_dialog,
                                                  new_game_start)
from santa_bot.telegram.handlers.player_games import (leave_game_dialog,
                                                      my_game_info_dialog,
                                                      my_games_dialog,
                                                      my_games_start)
from santa_bot.telegram.handlers.player_preferences import (
    edit_preferences_dialog, edit_preferences_start)
from santa_bot.telegram.middlewares import set_permission

storage = MemoryStorage()

dp = Dispatcher(bot, storage=storage)

registry = DialogRegistry(dp)


RULES = (
    'Правила игры:'
    '\n- администратор игры выдает вам код, с которым вы можете зарегистрироваться в этой игре'
    '\n- вы можете участвовать в нескольких играх'
    '\n- у каждой игры могут быть свои даты проведения'
    '\n- есть дата начала игры, дата завершения подачи заявок (регистрации) и дата окончания игры'
    '\n- вы можете покинуть игру до того как санты будут распределены. в случае если не сможете принять участие, по каким-то причинам'
    '\n- до того как игра начата или после того как санты в игре были распределены - в игру больше не вступить'
    '\n- после даты окончания сборы заявок каждому из вас будет назначен тайный санта'
    '\n- вы можете установить пожелания, например попросить не дарить вам что-то на что у вас может быть аллергия. санта может учесть эти пожелания, но это на его усмотрение :)'
    '\n- если у кого-то из игроков нет учетной записи телеграм, то попросите администратора внести этого игрока в игру вручную. у него будет такая возможность.'
    '\n- каждый из игроков является как тайным сантой, так и получателем. у каждого получателя всего один санта в игре'
    '\n- когда вы санта - вам придет сообщение с кодом игры и юзернеймом (и именем) человека, которому вы должны будете подарить подарок. а так же вам придет уникальный номер, по которому получатель сможет найти свой подарок.'
    '\n- пожалуйста, не сообщайте получателю что вы его тайный санта. так интереснее :)'
    '\n- администратор скажет вам куда следует принести и оставить подарок'
    '\n- на подарке следует написать уникальный код, который пришлет вам бот'
    '\n- сумма подарка оговоривается внутри группы, например с администратором'
    '\n- когда вы получатель - когда игра придет к завершению - вам придет уникальный код. он будет написан на подарке, и по нему вы сможете найти его в куче других подарков :)'
    '\n- дальше мы пытаемся угадать кто был чьим сантой :D'
    '\n- администратор может раскрыть имена сант, тогда всем придет сообщение о том, кто был их тайным сантой :)'
)


async def set_commands(bot: Bot):
    commands = [
        types.BotCommand(command='/start', description='Старт работы с ботом'),
        types.BotCommand(command='/register', description='Принять участие в игре'),
        types.BotCommand(command='/games', description='Список игр в которых вы учавствуете'),
        types.BotCommand(command='/preferences', description='Предпочтения для подарков'),
        types.BotCommand(command='/rules', description='Правила игры'),
        types.BotCommand(command='/game_info', description='Отображение информации о текущей игре. Команда доступна только из группы.'),
    ]
    await bot.set_my_commands(commands)


async def throttled_message(*args, **kwargs):
    message = args[0]
    await message.answer('Помедленнее. Я не успеваю 🥵')


@dp.message_handler(ChatTypeFilter(chat_type={types.chat.ChatType.PRIVATE}), commands=['start', 'help'])
@dp.throttled(throttled_message, rate=2)
async def start(message: types.Message):
    if not await User.filter(chat_id=message.chat.id).exists():
        await User.create(
            chat_id=message.chat.id,
            username=message.chat.username,
            full_name=message.chat.full_name,
        )

    help_message = 'Чтобы принять участие в игре введите команду /register\n\n' + RULES

    await message.answer(help_message)


@dp.message_handler(commands=['rules'])
@dp.throttled(throttled_message, rate=2)
async def rules(message: types.Message):
    await message.answer(RULES)


# -- Admin private chat --
@dp.message_handler(ChatTypeFilter(chat_type={types.chat.ChatType.PRIVATE}), commands=['admin'])
@dp.throttled(throttled_message, rate=2)
@set_permission(permission='admin')
async def admin(message: types.Message):
    """
    Admin panel
    """

    answer = (
        'GODMODE ON 😈'
        '\nСписок админских команд:'
        '\n- /new_game - менеджер создания игры'
        '\n- /owned_games - менеджер существующих игр'
        '\n- /link_group - менеджер существующих игр'
    )

    await message.answer(answer)


@dp.message_handler(ChatTypeFilter(chat_type={types.chat.ChatType.GROUP, types.chat.ChatType.SUPERGROUP}), commands=['link_group'])
@dp.throttled(throttled_message, rate=2)
@set_permission(permission='admin')
async def link_group(message: types.Message):
    user = await User.filter(chat_id=message.from_user['id']).first()
    code = message.get_args()
    if not code:
        return await message.answer(
            'Укажите код игры, чтобы связать эту группу с игрой. К каждой группе можно привязать всего одну игру'
        )

    game = await Game.filter(code=code, admin=user, group_chat_id__isnull=True).first()
    if not game:
        return await message.answer('Игра не найдена :(')

    game.group_chat_id = message.chat.id
    await game.save()

    await message.answer('Группа прилинкована.\nДоступна команда /game_info')


@dp.message_handler(ChatTypeFilter(chat_type={types.chat.ChatType.GROUP, types.chat.ChatType.SUPERGROUP}), commands=['game_info'])
@dp.throttled(throttled_message, rate=2)
async def get_game_info(message: types.Message):
    game = await Game.filter(group_chat_id=message.chat.id).prefetch_related('admin').first()
    if not game:
        return message.answer('Группа не прилинкована к игре.')

    today = datetime.utcnow().date()
    submitting_finished_at_days = (game.submitting_finished_at - today).days
    finished_at_days = (game.finished_at - today).days

    answer = (
        f'Код игры: {game.code}'
        f'\nАдмин игры: @{game.admin.username}'
        f'\nИгроков зарегистрированно: {await game.players.all().count()}'
        f'\nДо приема заявок на участие в игре осталось: {submitting_finished_at_days if bool(submitting_finished_at_days) else 0} день/дней'
        f'\nДо окончания игры осталось: {finished_at_days if bool(finished_at_days) else 0} день/дней'
    )

    await message.answer(answer)


dp.register_message_handler(join_game_start, ChatTypeFilter(chat_type={types.chat.ChatType.PRIVATE}), commands=['register'])
registry.register(join_game_dialog)

dp.register_message_handler(edit_preferences_start, ChatTypeFilter(chat_type={types.chat.ChatType.PRIVATE}), commands=['preferences'])
registry.register(edit_preferences_dialog)

dp.register_message_handler(my_games_start, ChatTypeFilter(chat_type={types.chat.ChatType.PRIVATE}), commands=['games'])
registry.register(my_games_dialog)
registry.register(my_game_info_dialog)
registry.register(leave_game_dialog)

dp.register_message_handler(new_game_start, ChatTypeFilter(chat_type={types.chat.ChatType.PRIVATE}), commands=['new_game'])
registry.register(new_game_dialog)

dp.register_message_handler(my_own_games_start, ChatTypeFilter(chat_type={types.chat.ChatType.PRIVATE}), commands=['owned_games'])
registry.register(my_own_games_dialog)
registry.register(my_own_game_info_dialog)
registry.register(delete_game_dialog)
registry.register(edit_game_dialog)
registry.register(add_player_dialog)
registry.register(player_list_dialog)
registry.register(player_info_dialog)
registry.register(delete_player_dialog)
