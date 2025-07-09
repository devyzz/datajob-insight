from _common.config.settings import CommonSettings
import os

class Settings(CommonSettings):
    APP_NAME: str = "Web Dashboard Service"

    class Config(CommonSettings.Config):
        pass

settings = Settings() 