
import os
from dataclasses import dataclass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

DATABASE_NAME = os.getenv(
    "DATABASE_NAME",
    "inquiry_management",
)


@dataclass
class CurrentUser:
    職員番号: str
    氏名: str
    所属: str


def get_current_user(request: Request) -> CurrentUser:
    """セッションを検証し、ログイン中の職員情報を取得する。"""

    # 関数の呼び出し時にインポートすることで、
    # main.py と routers/auth.py の循環インポートを避ける。
    from routers.auth import authenticate_session

    return authenticate_session(request)


app = FastAPI()

# フロントエンドからのアクセスを許可する。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers.inquiries import router as inquiries_router
from routers.investigations import router as investigations_router
from routers.auth import router as auth_router

app.include_router(inquiries_router)
app.include_router(investigations_router)
app.include_router(auth_router)
