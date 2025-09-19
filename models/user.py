import datetime
from typing import Literal

from peewee import DoesNotExist, fn

from models import User, Country, Vote, to_dict


def get_top_users(order_key: Literal['leveling', 'total_points', 'total_votes'] = 'leveling', limit: int = 20):
    """
    Generates a list of current top users
    :param order_key:
    :param limit:
    :return:
    """

    key_to_val = {
        'leveling': User.leveling,
        'total_points': User.total_points,
        'total_votes': User.total_votes,
    }

    if order_key not in key_to_val:
        raise ValueError(f'Invalid order key: {order_key}. Must be one of {list(key_to_val.keys())}')

    return [
        user for user in User.select()
        .where(User.blocked_until.is_null() or datetime.datetime.now() > User.blocked_until)
        .order_by(key_to_val[order_key].desc())
        .limit(limit)
    ]

def get_user(user_id: str = None, user_name: str = None) -> User | None:
    if not user_id and not user_name:
        raise ValueError('Either user_id or user_name must be specified.')
    try:
        return User.get((User.user_id == user_id) if user_id else (User.username == user_name))
    except DoesNotExist:
        return None

def get_top_user_country(user: User) -> Country | None:
    query = (
        Vote
        .select(Vote.country, fn.SUM(Vote.vote_count).alias("total_votes"))
        .where((Vote.user == user) & (Vote.redacted == False))
        .group_by(Vote.country)
        .order_by(fn.SUM(Vote.vote_count).desc())
        .limit(1)
    )
    result = query.first()
    return result.country or None

def rank_users() -> list:
    """
    Ranking of top users. As opposed to  get_top_users, this function includes top countries.
    :return:
    """

    user_ranking = list()
    for user in get_top_users():
        user_dict = to_dict(user)
        user_dict['top_country'] = get_top_user_country(user).alpha2
        user_ranking.append(user_dict)
    return user_ranking

def block_user(user_id: str = None, user_name: str = None, block_duration_seconds: int | bool = None) -> bool:
    user = get_user(user_id, user_name)
    if user is None:
        print('User not found!')
        return False
    if block_duration_seconds is False:  # remove all blocks
        user.blocked_until = None
    elif block_duration_seconds is None or block_duration_seconds is True:  # infinite duration
        block_duration_seconds = 60 * 60 * 24 * 365 * 5  # 5 years
        user.blocked_until = (datetime.datetime.now() + datetime.timedelta(seconds=block_duration_seconds)).replace(tzinfo=datetime.timezone.utc)
    user.save()
    return True
