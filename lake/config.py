import os
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
        https://pydantic-docs.helpmanual.io/#settings
        Exemplo de uso das variaveis de ambiente

        REDIS_HOST: str = "localhost"
        REDIS_PORT: int = 6379
    """

    DEBUG: bool = True
    NAMESPACE: str = "dev"
    BUCKET: str = "datalake"
    CRAWLER_ROLE: str = "arn:aws:iam::904893311111:role/AWSGlueServiceRole-Crawler"

    # class Config:
    #     env_prefix = os.getenv("NAMESPACE", "DEV").upper() + "_"  # defaults to 'APP_'


settings = Settings()
