from dataclasses import dataclass
from environs import Env


@dataclass
class DatabaseConfig:
    database: str
    db_host: str
    db_user: str
    db_password: str
    db_port: int


@dataclass
class TgBot:
    token: str
    admin_ids: list[int]


@dataclass
class Config:
    tg_bot: TgBot
    db: DatabaseConfig


def load_config() -> Config:
    env: Env = Env()
    env.read_env()

    config = Config(
        tg_bot=TgBot(
            token=env("BOT_TOKEN"), admin_ids=[6191665532, 513680694]
        ),  # 513680694
        db=DatabaseConfig(
            database=env("POSTGRES_DB"),
            db_host=env("POSTGRES_HOST"),
            db_user=env("POSTGRES_USER"),
            db_password=env("POSTGRES_PASSWORD"),
            db_port=env.int("POSTGRES_PORT"),
        ),
    )
    return config
