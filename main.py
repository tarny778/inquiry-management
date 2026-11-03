import logging
from dataclasses import dataclass

from config import settings

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

# ログの基本設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

# ファイル出力用ハンドラー
file_handler = logging.FileHandler("logs/app.log", encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
)

# ルートロガーにファイル出力を追加
logging.getLogger().addHandler(file_handler)

logger = logging.getLogger(__name__)

app = FastAPI()

@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    logger.exception("予期しない例外が発生しました")

    return JSONResponse(
        status_code=500,
        content={"detail": "サーバー内部でエラーが発生しました"},
    )

# フロントエンドからのアクセスを許可する。
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
