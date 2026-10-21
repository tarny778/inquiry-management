
import type { InquiryCreateForm } from '../../types'

type InquiryCreateProps = {
  userName: string | undefined
  userNumber: string | undefined
  createForm: InquiryCreateForm
  setCreateForm: (form: InquiryCreateForm) => void
  loading: boolean
  error: string
  onSubmit: (event: React.FormEvent<HTMLFormElement>) => void
  onCancel: () => void
  onLogout: () => void
}

export default function InquiryCreate({
  userName,
  userNumber,
  createForm,
  setCreateForm,
  loading,
  error,
  onSubmit,
  onCancel,
  onLogout,
}: InquiryCreateProps) {
  return (
    <div className="app">
      <header className="app-header">
        <h1>問い合わせ管理システム</h1>
        <span className="app-department">情報システム課</span>

        <div className="user-panel">
          {userName && (
            <span>
              {userName}（{userNumber}）
            </span>
          )}
          <button
            type="button"
            className="logout-button"
            onClick={onLogout}
            disabled={loading}
          >
            ログアウト
          </button>
        </div>
      </header>

      <main className="main">
        <div className="list-header">
          <h2>問い合わせ新規登録</h2>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
          >
            一覧に戻る
          </button>
        </div>

        {error && (
          <p className="error-message" role="alert">
            {error}
          </p>
        )}

        <form className="search-section" onSubmit={onSubmit}>
          <div className="search-fields">
            <label>
              問い合わせ職員番号 *
              <input
                value={createForm.問い合わせ職員番号}
                onChange={(event) =>
                  setCreateForm({
                    ...createForm,
                    問い合わせ職員番号: event.target.value,
                  })
                }
                maxLength={20}
                required
                disabled={loading}
              />
            </label>

            <label>
              受付経路 *
              <select
                value={createForm.受付経路}
                onChange={(event) =>
                  setCreateForm({
                    ...createForm,
                    受付経路: event.target.value,
                    受信日時: '',
                  })
                }
                disabled={loading}
              >
                <option value="電話">電話</option>
                <option value="メール">メール</option>
                <option value="フォーム">フォーム</option>
              </select>
            </label>

            <label>
              問い合わせ分類 *
              <select
                value={createForm.問い合わせ分類}
                onChange={(event) =>
                  setCreateForm({
                    ...createForm,
                    問い合わせ分類: event.target.value,
                  })
                }
                disabled={loading}
              >
                <option value="分類A">分類A</option>
                <option value="分類B">分類B</option>
                <option value="分類C">分類C</option>
              </select>
            </label>

            <label>
              件名 *
              <input
                value={createForm.件名}
                onChange={(event) =>
                  setCreateForm({
                    ...createForm,
                    件名: event.target.value,
                  })
                }
                maxLength={100}
                required
                disabled={loading}
              />
            </label>

            <label>
              緊急度 *
              <select
                value={createForm.緊急度}
                onChange={(event) =>
                  setCreateForm({
                    ...createForm,
                    緊急度: event.target.value,
                  })
                }
                disabled={loading}
              >
                <option value="1">1</option>
                <option value="2">2</option>
                <option value="3">3</option>
              </select>
            </label>

            <label>
              受付時の処理 *
              <select
                value={createForm.受付時の処理}
                onChange={(event) =>
                  setCreateForm({
                    ...createForm,
                    受付時の処理: event.target.value,
                  })
                }
                disabled={loading}
              >
                <option value="1">即時解決</option>
                <option value="2">要調査</option>
                <option value="3">他所属案内</option>
              </select>
            </label>

            <label>
              受信日時
              <input
                type="datetime-local"
                value={createForm.受信日時}
                onChange={(event) =>
                  setCreateForm({
                    ...createForm,
                    受信日時: event.target.value,
                  })
                }
                required={createForm.受付経路 !== '電話'}
                disabled={loading || createForm.受付経路 === '電話'}
              />
              {createForm.受付経路 === '電話' && (
                <span className="initial-condition-description">
                  電話の場合は登録時に自動設定されます。
                </span>
              )}
            </label>
          </div>

          <label>
            問い合わせ詳細
            <textarea
              value={createForm.問い合わせ詳細}
              onChange={(event) =>
                setCreateForm({
                  ...createForm,
                  問い合わせ詳細: event.target.value,
                })
              }
              maxLength={1000}
              rows={5}
              disabled={loading}
            />
          </label>

          <div className="bulk-buttons">
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
            >
              キャンセル
            </button>

            <button type="submit" disabled={loading}>
              {loading ? '登録中...' : '登録する'}
            </button>
          </div>
        </form>
      </main>
    </div>
  )
}
