from playhouse.migrate import SqliteMigrator, migrate
from peewee import SqliteDatabase, FloatField
from models import User, db

migrator = SqliteMigrator(db)

# Add the column
migrate(
    migrator.add_column("user", "blocked_until", FloatField(null=True))
)

# Update existing rows
query = User.update(blocked_until=None).where(User.leveling.is_null(True))
query.execute()
