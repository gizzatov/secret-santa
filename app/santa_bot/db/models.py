from datetime import datetime
from enum import Enum

import ujson
from tortoise import Tortoise, fields
from tortoise.models import Model

from santa_bot import settings


async def init_db():
    await Tortoise.init(config=settings.TORTOISE_ORM)


class BaseModel(Model):
    id = fields.IntField(pk=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return str(self.id)

    async def lock(self) -> Model:
        return await self.__class__.select_for_update(nowait=False).get(pk=self.id)


class User(BaseModel):
    chat_id = fields.CharField(max_length=100, null=True, unique=True)
    username = fields.CharField(max_length=100, null=True)
    full_name = fields.CharField(max_length=150)
    is_active = fields.BooleanField(default=True)
    is_moderator = fields.BooleanField(default=False)
    is_tg_user = fields.BooleanField(default=True)
    preferences = fields.TextField(default='')
    description = fields.TextField(max_length=300, default='')
    extra = fields.JSONField(encoder=ujson.dumps, decoder=ujson.loads, default={})

    class Meta:
        table = 'users'


class GameStatus(Enum):
    NEW = 'new'
    SANTAS_SELECTED = 'santas_selected'
    SANTAS_REVEALED = 'santas_revealed'


class Game(BaseModel):
    STATUSES = GameStatus

    admin = fields.ForeignKeyField('models.User', related_name='admins')
    code = fields.CharField(max_length=100, unique=True)
    group_chat_id = fields.CharField(max_length=100, null=True, unique=True)
    description = fields.TextField(max_length=300, default='')
    started_at = fields.DateField(auto_now=False)
    submitting_finished_at = fields.DateField(auto_now=False)
    finished_at = fields.DateField(auto_now=False)
    status = fields.CharEnumField(max_length=20, enum_type=STATUSES, default=STATUSES.NEW)
    extra = fields.JSONField(encoder=ujson.dumps, decoder=ujson.loads, default={})

    class Meta:
        table = 'games'

    @property
    def is_running(self):
        today = datetime.utcnow().date()

        if today < self.started_at:
            return False

        if today > self.submitting_finished_at:
            return False

        if today > self.finished_at:
            return False

        return True

    @property
    def player_can_leave_or_join(self):
        if self.status == self.STATUSES.NEW:
            return True

        return False


class Player(BaseModel):
    user = fields.ForeignKeyField('models.User', related_name='players')
    game = fields.ForeignKeyField('models.Game', related_name='players')
    extra = fields.JSONField(encoder=ujson.dumps, decoder=ujson.loads, default={})

    class Meta:
        table = 'players'


class Pair(BaseModel):
    game = fields.ForeignKeyField('models.Game', related_name='pairs')
    santa = fields.ForeignKeyField('models.User', related_name='santas')
    target = fields.ForeignKeyField('models.User', related_name='targets')
    code = fields.CharField(max_length=100, unique=True)
    is_revealed = fields.BooleanField(default=False)
    is_notified = fields.BooleanField(default=False)
    extra = fields.JSONField(encoder=ujson.dumps, decoder=ujson.loads, default={})

    class Meta:
        table = 'pairs'
        unique_together=(
            ('game', 'santa', 'target'),
        )
