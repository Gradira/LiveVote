from models import db

db.execute('ALTER DATABASE livevote CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci;')
db.execute('ALTER TABLE your_table_name CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;')
