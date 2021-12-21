import asyncio

import aiocron
from loguru import logger

from santa_bot.db.models import Pair
from santa_bot.telegram.direct import send_message


async def notify_santa():
    for pair in await Pair.filter(is_notified=False).prefetch_related('game', 'target', 'santa', 'game__admin'):
        # Message to santa
        if pair.santa.is_tg_user:
            message_to_santa = (
                f'Ура-ура! Вы тайный санта по игре с кодом {pair.game.code}!'
                f'\nВам необходимо выбрать подарок для {pair.target.full_name} '
                f'{ "(@" + pair.target.username + ")" if pair.target.is_tg_user else ""}'
                f'\nНапишите на подарке вот этот код: {pair.code}. Именно по этому коду {pair.target.full_name} сможет найти свой подарок.'
                f'\nПринесите подарок в точку сбора до {pair.game.finished_at.strftime("%d.%m.%Y")}'
            )
            if pair.target.preferences:
                message_to_santa += (
                    f'\nКстати говоря {pair.target.full_name} имеет предпочтения, можете их учесть, если будет желание:'
                    f'\n{pair.target.preferences if pair.target.preferences else ""}'
                )
            await send_message(pair.santa.chat_id, message_to_santa)
        else:
            message_to_santas_admin = (
                f'По игре с кодом {pair.game.code} выбран тайный санта {pair.santa.full_name}.'
                f'\nК сожалению он не является пользователем телеграм. Вы вносили его вручную. Вот данные, которые помогут его вспомнить:\n{pair.santa.description}'
                f'\nПередайте {pair.santa.full_name} это сообщение:'
                f'\nВам необходимо выбрать подарок для {pair.target.full_name} '
                f'{ "(@" + pair.target.username + ")" if pair.target.is_tg_user else ""}'
                f'\nНапишите на подарке вот этот код: {pair.code}. Именно по этому коду {pair.target.full_name} сможет найти свой подарок.'
                f'\nПринесите подарок в точку сбора до {pair.game.finished_at.strftime("%d.%m.%Y")}'
            )
            if pair.target.preferences:
                message_to_santa += (
                    f'\nКстати говоря {pair.target.full_name} имеет предпочтения, можете их учесть, если будет желание:'
                    f'\n{pair.target.preferences if pair.target.preferences else ""}'
                )
            await send_message(pair.game.admin.chat_id, message_to_santas_admin)

        # Message to target
        if pair.target.is_tg_user:
            message_to_target = (
                f'ОГО! У вас появился тайный санта по игре с кодом {pair.game.code}!'
                f'\nВам стоит поискать свой подарок в точке сбора после {pair.game.finished_at.strftime("%d.%m.%Y")}!'
                f'\nНа подарке будет написан ваш уникальный код {pair.code}, так вы и узнаете свой подарок, удачи!'
            )
            await send_message(pair.target.chat_id, message_to_target)
        else:
            message_to_targets_admin = (
                f'По игре с кодом {pair.game.code} для {pair.target.full_name} был выбран тайный санта.'
                f'\nК сожалению он не является пользователем телеграм. Вы вносили его вручную. Вот данные, которые помогут его вспомнить:\n{pair.target.description}'
                f'\nПередайте {pair.target.full_name} это сообщение:'
                f'\nВам стоит поискать свой подарок в точке сбора после {pair.game.finished_at.strftime("%d.%m.%Y")}!'
                f'\nНа подарке будет написан ваш уникальный код {pair.code}, так вы и узнаете свой подарок, удачи!'
            )
            await send_message(pair.game.admin.chat_id, message_to_targets_admin)

        pair.is_notified = True
        await pair.save()
        logger.info('pair {} was notified', pair.id)

        await asyncio.sleep(0.4)


def start():
    aiocron.crontab('*/1 * * * *', notify_santa)

    logger.info('Tasks were started')
