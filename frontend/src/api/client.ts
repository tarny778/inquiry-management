const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// API通信で発生したエラー
export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// APIのエラーレスポンスからメッセージを取得する
function getErrorMessage(data: unknown, fallback: string): string {
  if (
    typeof data === 'object' &&
    data !== null &&
    'detail' in data
  ) {
    const detail = (data as { detail: unknown }).detail

    if (typeof detail === 'string') {
      return detail
    }

    return JSON.stringify(detail)
  }

  return fallback
}

// HTTP通信の共通処理
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  fallback = 'API通信に失敗しました。',
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    credentials: 'include',
    ...options,
  })

  const data: unknown = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(
      response.status,
      getErrorMessage(data, fallback),
    )
  }

  return data as T
}
