from pydantic import StrictStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    gmail_username: StrictStr
    gmail_app_password: StrictStr
    notion_api_key: StrictStr
    notion_data_source_id: StrictStr
    from_email: StrictStr
    subject_prefix: StrictStr | None = None


settings = Settings()  # type: ignore
