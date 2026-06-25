from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "广告审核宝"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./data/ad_audit.db"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "ad-audit-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024

    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    VECTOR_DIMENSION: int = 512

    OFFICIAL_WHITELIST: dict = {
        "SG": [
            "https://www.csa.org.sg",
            "https://www.mci.gov.sg",
        ],
        "MY": [
            "https://www.kpdnhep.gov.my",
        ],
        "TH": ["https://www.consumerprotection.go.th"],
        "AU": ["https://adstandards.com.au"],
        "JP": ["https://www.caa.go.jp"],
        "KR": ["https://www.mcst.go.kr"],
        "IN": ["https://consumeraffairs.nic.in"],
    }

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
