from typing import Literal

import country_converter
import pycountry
from countryinfo import CountryInfo

from errors import InvalidCountry
from models import Country, CountryCache

def get_or_create(query: str) -> Country:
    info = get_country_data(query)
    if not info:
        raise InvalidCountry(f'Could not find country info for "{query}"')
    # Ensure CountryCache exists first
    cache, _ = CountryCache.get_or_create(
        alpha2=info['alpha2'],
        defaults={'votes': 0, 'points': 0}
    )
    country, created = Country.get_or_create(
        alpha2=info['alpha2'],
        defaults={
            'alpha3': info['alpha3'],
            'name': info['name'],
            'cache': cache  # <- must reference existing cache
        }
    )
    # Optionally update alpha3/name if changed
    updated = False
    if country.alpha3 != info['alpha3']:
        country.alpha3 = info['alpha3']
        updated = True
    if country.name != info['name']:
        country.name = info['name']
        updated = True
    if updated:
        country.save()
    return country

def get_country_data(query: str) -> dict | None:
    country = (
        pycountry.countries.get(alpha_2=query.upper())
        or pycountry.countries.get(alpha_3=query.upper())
        or pycountry.countries.get(name=query.title())
    )
    if not country:
        # Try flexible search
        for c in pycountry.countries:
            if query.lower() in (c.name.lower(), getattr(c, 'official_name', '').lower()):
                country = c
                break
    if not country:
        return None

    # Attempt to get continent/region via countryinfo
    continent = None
    try:
        ci = CountryInfo(country.name)
        continent = ci.info().get('region')
    except Exception:
        pass

    # Use the most natural/common country name
    natural_name = country_converter.convert(names=country.name, to='name_short')

    return {
        'alpha2': country.alpha_2,
        'alpha3': country.alpha_3,
        'name': natural_name,
        'continent': continent,
    }

def rank_countries(by: Literal['points', 'votes'] = 'points') -> list[Country]:
    return [
        country for country in
        Country.select(Country, CountryCache)
        .join(CountryCache)
        .order_by(getattr(CountryCache, by).desc())
    ]
    """return [
        {
            # 'rank': i + 1,
            'country': {'alpha2': country.alpha2, 'alpha3': country.alpha3, 'name': country.name},
            'points': country.cache.points,
            'votes': country.cache.votes,
        }
        for i, country in enumerate(query)
    ]"""