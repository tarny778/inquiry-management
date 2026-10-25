import { apiRequest } from './client'
// 認証を確認し、ユーザーを取得する
export async function checkSession(
  ): Promise<{
  職員番号: string
  氏名: string
  所属: string
}>{
  return await apiRequest<{
    職員番号: string
    氏名: string
    所属: string
  }>(
    '/api/auth/me',
    {method: 'GET'},
    '認証に失敗しました'
  )
}


// ログインする
export async function login(
  職員番号: string,
  パスワード: string,
): Promise<{
  職員番号: string
  氏名: string
  所属: string
}> {
  return await apiRequest<{
    職員番号: string
    氏名: string
    所属: string
  }>(
    '/api/auth/login',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        職員番号,
        パスワード,
      }),
    },
    'ログインに失敗しました。',
  )
}

// ログアウトする
export async function logout(): Promise<void> {
  await apiRequest(
    '/api/auth/logout',
    {method: 'POST',},
    'ログアウトに失敗しました。',
  )
}