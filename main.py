import os
from dataclasses import dataclass

from fastapi import FastAPI

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "inquiry_management",
)

@dataclass
class CurrentUser:
    職員番号: str
    氏名: str
    所属: str

def get_current_user() -> CurrentUser:
    """認証導入前の仮実装。開発用の操作者を返す。"""
    return CurrentUser(
        職員番号="J0001",
        氏名="情シス太郎",
        所属="情報システム課",
    )

app = FastAPI()

from routers.inquiries import router as inquiries_router

app.include_router(inquiries_router)





