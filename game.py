from playhouse.shortcuts import model_to_dict

from cache import preset_countries, recalc_cache
from models import *
from models.country import rank_countries
from models.event import get_latest_events, _compute_power_milestones
from models.user import rank_users
from models.vote import get_latest_votes


class Game:
    """
    Basic interface for database interaction
    Supports usage with the `with` operator
    """

    def __init__(self, db_name: str = 'livevote') -> None:
        self.db_name = db_name

    def __enter__(self):
        # db.init(self.db_name)
        db.connect(reuse_if_open=True)

        # Setup environment
        print('Preseting countries...')
        preset_countries()
        print('Recalculating caches...')
        recalc_cache()  # refreshing caches...
        print('Creating tables...')
        db.create_tables([Setting, CountryCache, Event, User, Country, Vote], safe=True)
        print('Setup done!')

        return self

    def __exit__(self, typ, val, tb):
        if not db.is_closed():
            db.close()
        return False

    @property
    def country_data(self) -> dict:
        return {
            cc.alpha2: {'votes': cc.votes, 'points': cc.points}
            for cc in CountryCache.select()
        }

    @staticmethod
    def get_country(alpha2: str) -> dict[str, int] | None:
        try:
            cc = CountryCache.get(CountryCache.alpha2 == alpha2)
            return {'votes': cc.votes, 'points': cc.points}
        except CountryCache.DoesNotExist:
            return None

    def __getitem__(self, item_id):
        return self.get_country(item_id)

def register_vote(vote: Vote) -> list[Event]:
    """
    Main function to register a vote. Create all Votes directly from the model, then simply call this function.
    :param vote:
    :return:
    """

    created_events: list[Event] = []
    if vote.user.blocked_until is not None:
        if not (datetime.datetime.now() > vote.user.blocked_until):  # block has expired
            vote.redacted = True
            vote.save()
        else:
            vote.user.blocked_until = None
            vote.user.save()

    # ignore redacted votes
    if vote.redacted:
        return created_events
    user = vote.user  # User instance (peewee ForeignKey -> model instance)
    country = vote.country  # Country instance
    cache = country.cache  # CountryCache instance (where votes/points are stored)

    # read old values
    old_user_level = float(user.leveling or 0)
    old_user_total_votes = float(user.total_votes or 0)
    old_user_total_points = float(user.total_points or 0)
    old_country_votes = int(cache.votes or 0)
    old_country_points = int(cache.points or 0)

    # compute new values
    new_user_level = old_user_level + float(vote.xp_gain or 0)
    new_user_total_votes = old_user_total_votes + float(vote.vote_count or 0)
    new_user_total_points = old_user_total_points + float(vote.points or 0)
    new_country_votes = old_country_votes + int(vote.vote_count or 0)
    new_country_points = old_country_points + int(vote.points or 0)

    """print(old_user_level, new_user_level)
    print(old_user_total_votes, new_user_total_votes)
    print(old_user_total_points, new_user_total_points)
    print(new_country_votes, new_country_votes)
    print(new_country_points, new_country_points)"""

    # Wrap updates + event creation in transaction to avoid partial updates
    with db.atomic():
        user.latest_vote = vote.timestamp
        # persist updated counters
        user.leveling = new_user_level
        user.total_votes = new_user_total_votes
        user.total_points = new_user_total_points
        user.save()
        cache.votes = new_country_votes
        cache.points = new_country_points
        cache.save()

        # --- USER LEVEL MILESTONES ---
        # example sequence: 10, 100, 1000, ... => base=10, start_power=1
        user_milestones = _compute_power_milestones(old_user_level, new_user_level, base=10)
        for m in user_milestones:
            ev = Event.create(
                type="user_level_up",
                user=user,
                country=None,
                milestone=m
            )
            created_events.append(ev)

        # --- COUNTRY POINTS MILESTONES ---
        # example: 1_000_000, 10_000_000, ... => base=10, start_power=6
        country_point_milestones = _compute_power_milestones(old_country_points, new_country_points, base=10, minimum=1000)
        for m in country_point_milestones:
            ev = Event.create(
                type="country_points",
                user=user,
                country=country,
                milestone=m
            )
            created_events.append(ev)

        # --- COUNTRY VOTES MILESTONES ---
        # example: 100, 1000, 10000, ... => base=10, start_power=2
        """country_vote_milestones = self._compute_power_milestones(old_country_votes, new_country_votes, base=10)
        for m in country_vote_milestones:
            ev = Event.create(
                type="country_votes",
                user=user,
                country=country,
                milestone=m
            )
            created_events.append(ev)"""

    return created_events


def gen_status_report() -> dict:
    """
    Generates status report as dict for clients
    :return:
    """

    return to_dict({
        'type': 'status',
        'country_ranking': rank_countries(),
        'user_ranking': rank_users(),
        'latest_votes': get_latest_votes(),
        'latest_events': get_latest_events()
    })

def gen_vote_report(vote: Vote, events: list[Event] = None) -> dict:
    """
    Generates vote update report as dict for clients
    :return:
    """

    events = events or []
    return to_dict({
        'type': 'update',
        'vote': model_to_dict(vote),
        'events': [model_to_dict(event) for event in events]
    })
