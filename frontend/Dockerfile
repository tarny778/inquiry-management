
FROM node:24-slim

# コンテナ内の作業場所
WORKDIR /app

# ライブラリ一覧をコピー
COPY package*.json ./

# ライブラリをインストール
RUN npm ci

# フロントエンドのファイルをコピー
COPY . .

# Viteが使用するポート番号
EXPOSE 5173

# 開発用サーバーを起動
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
