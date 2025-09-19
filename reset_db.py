from models import db, Country, CountryCache, Event, User, Vote, Setting

# Drop all tables (if they exist)
db.drop_tables([Vote, User, CountryCache, Event, Country, Setting])

# Recreate tables
db.create_tables([CountryCache, Country, Event, User, Vote, Setting])