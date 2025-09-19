import pycountry
from peewee import fn

from models import db, Vote, CountryCache, Country
from models.country import get_country_data


"""def apply_to_cache(vote: Vote) -> None:
    cache, _ = CountryCache.get_or_create(alpha2=vote.country, defaults={'points': 0, 'votes': 0})
    cache.points += vote.points
    cache.votes += vote.vote_count
    cache.save()"""

def preset_countries() -> None:
    for country in pycountry.countries:
        # Use get_country_data to retrieve enriched info (alpha2, alpha3, name, continent, etc)
        info = get_country_data(country.alpha_2)
        if not info:
            continue  # skip if info could not be found
        # Create CountryCache if not exists
        cache, _ = CountryCache.get_or_create(
            alpha2=info['alpha2'],
            defaults={'votes': 0, 'points': 0}
        )
        # Prepare defaults, only use keys that exist in the Country model
        defaults = {
            'alpha3': info.get('alpha3'),
            'name': info.get('name'),
            'cache': cache
        }
        # Optionally include continent if it's a column in Country
        if hasattr(Country, 'continent') and info.get('continent'):
            defaults['continent'] = info.get('continent')
        # Create Country if not exists
        country_obj, _ = Country.get_or_create(
            alpha2=info['alpha2'],
            defaults=defaults
        )

def recalc_cache() -> None:
    with db.atomic():
        if CountryCache.table_exists():
            # Set all votes and points to 0 instead of deleting
            CountryCache.update(votes=0, points=0).execute()
        if not Vote.table_exists():
            return  # exit if vote table is empty
        # For each country, sum votes and points
        query = (Vote
                 .select(Vote.country,
                         fn.COUNT(Vote.vote_id).alias('vote_count'),
                         fn.SUM(Vote.points).alias('points_sum'))
                 .where(Vote.redacted == False)
                 .group_by(Vote.country))
        for row in query:
            # Try to update existing cache entry, else create
            updated = (CountryCache
                       .update(votes=row.vote_count, points=row.points_sum or 0)
                       .where(CountryCache.alpha2 == row.country.alpha2)
                       .execute())
            if not updated:
                CountryCache.create(
                    alpha2=row.country.alpha2,
                    votes=row.vote_count,
                    points=row.points_sum or 0
                )