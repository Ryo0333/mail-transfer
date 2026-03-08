from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    gmail_username: str
    gmail_app_password: str
    notion_api_key: str
    notion_data_source_id: str
    from_email: str


settings = Settings()  # type: ignore
