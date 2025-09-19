import json
import datetime
import os
from typing import Any
from dotenv import dotenv_values

from playhouse.shortcuts import model_to_dict as _model_to_dict
from peewee import *

db_config = dotenv_values()
db = MySQLDatabase(
    db_config['DB_NAME'],
    user=db_config['DB_USER'],
    password=db_config['DB_PASSWD'],
    host=db_config['DB_HOST'],
    port=int(db_config['DB_PORT'])
)

def to_dict(model: Model | dict | list | tuple) -> dict:
    """
    This function converts datetime.datetime objects to isoformat, which the default model_to_dict does not
    :param model:
    :return:
    """

    def convert(value: Any):
        if isinstance(value, datetime.datetime):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: convert(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert(v) for v in value]
        elif isinstance(value, tuple):
            return tuple([convert(v) for v in value])
        elif isinstance(value, Model):
            return convert(_model_to_dict(value, recurse=True))
        return value

    return convert(model)

class BaseModel(Model):
    class Meta:
        database = db

    def __iter__(self):
        for key, value in to_dict(self).items():
            yield key, value

    def to_json(self, *args, **kwargs):
        return json.dumps(dict(self), *args, **kwargs)

class Setting(BaseModel):
    key = CharField(primary_key=True)
    value = TextField()

class CountryCache(BaseModel):
    alpha2 = CharField(primary_key=True, unique=True)
    votes = IntegerField(default=0)
    points = IntegerField(default=0)

class User(BaseModel):
    user_id = CharField(unique=True, primary_key=True)
    channel_url = CharField()
    username = CharField()
    image_url = CharField()
    is_mod = CharField(default=False)

    leveling = FloatField(default=0)
    total_votes = FloatField(default=0)
    total_points = FloatField(default=0)
    blocked_until = DateTimeField(default=None, null=True)
    latest_vote = DateTimeField(default=None, null=True)

class Country(BaseModel):
    alpha2 = CharField(unique=True, primary_key=True)
    alpha3 = CharField(unique=True)
    name = CharField()
    cache = ForeignKeyField(CountryCache, backref='countries', on_delete='CASCADE', unique=True)

class Event(BaseModel):
    event_id = AutoField()
    type = CharField() # e.g. "user_level_up", "country_points", "country_votes"
    user = ForeignKeyField(User, null=True, backref="events")
    country = ForeignKeyField(Country, null=True, backref="events", on_delete="CASCADE")
    milestone = IntegerField()
    timestamp = DateTimeField(default=datetime.datetime.now)

class Vote(BaseModel):
    vote_id = AutoField()
    user = ForeignKeyField(User, backref="votes")
    country = ForeignKeyField(Country, backref="votes", on_delete="CASCADE")
    vote_count = IntegerField(default=1)
    points = IntegerField(default=0)
    xp_gain = FloatField(default=0.04)
    redacted = BooleanField(default=False)
    timestamp = DateTimeField(default=datetime.datetime.now())

    class Meta:
        indexes = (
            (('user', 'country', 'timestamp'), False),
        )
