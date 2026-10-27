
import PageHeader from '../PageHeader'
import type { FormEvent } from 'react'
import type { InquiryEditForm } from '../../types'

type InquiryUpdateProps = {
  editForm: InquiryEditForm
  setEditForm: (form: InquiryEditForm) => void
  loading: boolean
  error: string
  onSubmit: (event: FormEvent<HTMLFormElement>) => void
  onCancel: () => void
}

export default function InquiryUpdate({
  editForm,
  setEditForm,
  loading,
  error,
  onSubmit,
  onCancel,
}: InquiryUpdateProps) {
    return (
      <div className="app">

        <main className="main">
          <PageHeader
            section="問い合わせ"
            title="問い合わせ編集"
            actions={
              <button
                className="button-secondary"
                type="button"
                onClick={onCancel}
                disabled={loading}
              >
                ↑ 戻る
              </button>
            }
          />
            {error && (
            <p className="error-message" role="alert">
                {error}
            </p>
            )}

          <form
            className="search-section"
            onSubmit={onSubmit}
          >
            <div className="search-fields">
              <label>
                問い合わせ職員番号 *
                <input
                  value={editForm.問い合わせ職員番号}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
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
                  value={editForm.受付経路}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      受付経路: event.target.value,
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
                  value={editForm.問い合わせ分類}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
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
                  value={editForm.件名}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
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
                  value={editForm.緊急度}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
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
                  value={editForm.受付時の処理}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
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
                  value={editForm.受信日時}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      受信日時: event.target.value,
                    })
                  }
                  required
                  disabled={loading}
                />
              </label>
            </div>

            <label>
              問い合わせ詳細
              <textarea
                value={editForm.問い合わせ詳細}
                onChange={(event) =>
                  setEditForm({
                    ...editForm,
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
  className="button-primary" type="submit" disabled={loading}>
                {loading ? '保存中...' : '保存'}
              </button>
            </div>
          </form>
        </main>
      </div>
    )
}