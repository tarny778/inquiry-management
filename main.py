
import os
from dataclasses import dataclass

from fastapi import FastAPI, Request

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



from routers.inquiries import router as inquiries_router
from routers.investigations import router as investigations_router
from routers.auth import router as auth_router

app.include_router(inquiries_router)
app.include_router(investigations_router)
app.include_router(auth_router)



