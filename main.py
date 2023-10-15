from sqlalchemy import URL, create_engine

import os
postgres_engine_url: URL = URL.create(
        drivername='postgresql+psycopg2',
        username=os.getenv('tg_bot'),
        host=os.getenv('DATABASE_HOST'),
        database=os.getenv('DATABASE_NAME'),
        port=os.getenv('DATABASE_PORT'),
        password=os.getenv('DATABASE_USER_PASSWORD')
    )

engine = create_engine(postgres_engine_url)

with engine.connect():
    pass