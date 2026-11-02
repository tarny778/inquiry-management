FROM python:3.12-slim

# Pythonの動作設定
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# コンテナ内の作業場所
WORKDIR /app

# ライブラリ一覧をコピー
COPY requirements.txt .

# Pythonライブラリをインストール
RUN pip install --no-cache-dir -r requirements.txt

# プロジェクトのファイルをコピー
COPY . .

# 使用するポート番号
EXPOSE 8000

# コンテナ起動時にFastAPIを起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]