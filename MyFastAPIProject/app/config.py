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
#Email Configuration Settings
    reset_token_expire_minutes: int = 30
    mail_server: str = "localhost"
    mail_port: int = 587
    mail_username: str = ""
    mail_password: SecretStr = SecretStr("")
    mail_from: str = "noreply@example.com"
    mail_use_tls: bool = True
    frontend_url: str = "http://localhost:8000"
#create instance 
settings = Settings() #loaded from .env file