from _common.config.settings import CommonSettings
import os

class Settings(CommonSettings):
    APP_NAME: str = "Web JobPosting Service"

    class Config(CommonSettings.Config):
        pass # 특별히 오버라이드 할 내용이 없다면 pass


settings = Settings()