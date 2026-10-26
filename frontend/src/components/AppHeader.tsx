
type AppHeaderProps = {
  user?: {
    氏名: string
    職員番号: string
  } | null

  onLogout?: () => void
  loading?: boolean
}

export default function AppHeader({
  user = null,
  onLogout,
  loading = false,
}: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="app-brand">
        <h1>問い合わせ管理システム</h1>
        <span className="app-department">
          情報システム課
        </span>
      </div>

      {user && onLogout && (
        <div className="user-panel">
          <span>
            {user.氏名}（{user.職員番号}）
          </span>

          <button
            type="button"
            className="logout-button"
            onClick={onLogout}
            disabled={loading}
          >
            ログアウト
          </button>
        </div>
      )}
    </header>
  )
}
