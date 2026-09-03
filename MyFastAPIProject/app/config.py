from pydantic import SecretStr
#for password
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="app/.env",
        env_file_encoding="utf-8",
    )

    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    #for image
    max_upload_size_bytes:int =5 * 1024 * 1024
    #for pagination in FE
    posts_per_page: int=10
#create instance 
settings = Settings() #loaded from .env file