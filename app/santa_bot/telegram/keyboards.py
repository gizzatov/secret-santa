from aiogram_dialog.widgets.kbd import Calendar

from datetime import date

from aiogram.types import CallbackQuery
from aiogram_dialog.dialog import Dialog
from aiogram_dialog.manager.protocols import DialogManager


# Constants for managing widget rendering scope
SCOPE_DAYS = 'SCOPE_DAYS'
SCOPE_MONTHS = 'SCOPE_MONTHS'
SCOPE_YEARS = 'SCOPE_YEARS'

# Constants for scrolling months
MONTH_NEXT = '+'
MONTH_PREV = '-'

# Constants for prefixing month and year values
PREFIX_MONTH = 'MONTH'
PREFIX_YEAR = 'YEAR'


class CustomCalendar(Calendar):

    async def process_callback(self,
                               c: CallbackQuery,
                               dialog: Dialog,
                               manager: DialogManager) -> bool:
        prefix = f'{self.widget_id}:'
        if not c.data.startswith(prefix):
            return False
        current_offset = self.get_offset(manager)
        data = c.data[len(prefix):]

        if data == MONTH_NEXT:
            new_offset = date(
                year=current_offset.year + (current_offset.month // 12),
                month=((current_offset.month % 12) + 1),
                day=1,
            )
            self.set_offset(new_offset, manager)

        elif data == MONTH_PREV:
            if current_offset.month == 1:
                new_offset = date(current_offset.year - 1, 12, 1)
                self.set_offset(new_offset, manager)
            else:
                new_offset = date(current_offset.year, (current_offset.month - 1), 1)
                self.set_offset(new_offset, manager)

        elif data in [SCOPE_MONTHS, SCOPE_YEARS]:
            self.set_scope(data, manager)

        elif data.startswith(PREFIX_MONTH):
            data = int(c.data[len(prefix) + len(PREFIX_MONTH):])
            new_offset = date(current_offset.year, data, 1)
            self.set_scope(SCOPE_DAYS, manager)
            self.set_offset(new_offset, manager)

        elif data.startswith(PREFIX_YEAR):
            data = int(c.data[len(prefix) + len(PREFIX_YEAR):])
            new_offset = date(data, 1, 1)
            self.set_scope(SCOPE_MONTHS, manager)
            self.set_offset(new_offset, manager)

        else:
            raw_date = int(data)
            await self.on_click.process_event(
                c, self.managed(manager), manager,
                date.fromtimestamp(raw_date),
                dialog,
            )
        return True
