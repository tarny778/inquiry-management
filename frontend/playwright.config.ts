
import { defineConfig, devices } from '@playwright/test'
import dotenv from 'dotenv'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

// この設定ファイルが置かれているディレクトリ
const __dirname = dirname(fileURLToPath(import.meta.url))

// プロジェクトルートの .env.e2e を読み込む。
// override: true により、シェルに別の環境変数があってもE2E設定を優先する。
const envPath = resolve(__dirname, '../.env.e2e')
const envResult = dotenv.config({
  path: envPath,
  override: true,
})

if (envResult.error) {
  throw new Error(`.env.e2e の読み込みに失敗しました: ${envResult.error.message}`)
}

// E2E環境以外ではテストを起動しない。
if (process.env.APP_ENV !== 'e2e') {
  throw new Error('APP_ENV が e2e ではありません。E2Eテストを中止します。')
}

if (
  process.env.VITE_API_BASE_URL !== 'http://127.0.0.1:8000'
) {
  throw new Error(
    'VITE_API_BASE_URL がE2E用の設定ではありません。'
  )
}

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'html',

  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // E2Eテストの前に、FastAPIとViteを自動起動する。
  // テスト終了後はPlaywrightが両方を停止する。
  webServer: [
    {
      command: 'uvicorn main:app --host 127.0.0.1 --port 8000',
      cwd: resolve(__dirname, '..'),
      url: 'http://127.0.0.1:8000/docs',
      reuseExistingServer: false,
      timeout: 30_000,
    },
    {
      command:
        'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
      cwd: __dirname,
      url: 'http://127.0.0.1:5173',
      reuseExistingServer: false,
      timeout: 30_000,
    },
  ],
})
