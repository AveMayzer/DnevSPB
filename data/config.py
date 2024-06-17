import os

from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
PGUSER = os.getenv("PGUSER")
ADMIN = os.getenv('ADMIN')
PGPASSWORD = os.getenv('PGPASSWORD')
PGHOST = os.getenv('PGHOST')
PGDATABASE = os.getenv("PGDATABASE")
POSTGRES_URI = f'postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}/{PGDATABASE}'