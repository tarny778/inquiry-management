
import type { SubmitEvent } from 'react'
import type {
  InvestigationDetail,
  InvestigationEditForm,
  LoginUser,
} from '../../types'

import PageHeader from '../PageHeader'

type InvestigationUpdateProps = {
  investigation: InvestigationDetail
  editForm: InvestigationEditForm
  setEditForm: React.Dispatch<
    React.SetStateAction<InvestigationEditForm>
  >
  onSubmit: (event: SubmitEvent<HTMLFormElement>) => void
  onCancel: () => void
  loading: boolean
  user: LoginUser | null
  error: string
}

export default function InvestigationUpdate({
  investigation,
  editForm,
  setEditForm,
  onSubmit,
  onCancel,
  loading,
  error,
}: InvestigationUpdateProps) {
  return (
    <div className="app">

      <main className="main">
        <section className="detail-section">
          <PageHeader
            section="問題調査"
            title="調査編集"
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
          <p>調査番号：{investigation.調査番号}</p>

          
          <form onSubmit={onSubmit}>
            <div className="form-fields">
              <label
                className="form-field-wide"
                htmlFor="investigation-name"
              >
                調査の名称
                <textarea
                  id="investigation-name"
                  value={editForm.調査の名称}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      調査の名称: event.target.value,
                    })
                  }
                  required
                  disabled={loading}
                />
              </label>

              <label
                className="form-field-wide"
                htmlFor="investigation-cause"
              >
                原因・仮説
                <textarea
                  id="investigation-cause"
                  value={editForm['原因・仮説']}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      '原因・仮説': event.target.value,
                    })
                  }
                  disabled={loading}
                />
              </label>

              <label
                className="form-field-wide"
                htmlFor="investigation-it-response"
              >
                情シス側での対応
                <textarea
                  id="investigation-it-response"
                  value={editForm.情シス側での対応}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      情シス側での対応: event.target.value,
                    })
                  }
                  disabled={loading}
                />
              </label>

              <label
                className="form-field-wide"
                htmlFor="investigation-requester-response"
              >
                問い合わせ者側で必要な対応
                <textarea
                  id="investigation-requester-response"
                  value={editForm.問い合わせ者側で必要な対応}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      問い合わせ者側で必要な対応: event.target.value,
                    })
                  }
                  disabled={loading}
                />
              </label>

              <label
                className="form-field-wide"
                htmlFor="investigation-plan-date"
              >
                対応案策定予定日時
                <input
                  id="investigation-plan-date"
                  type="datetime-local"
                  step={1}
                  value={editForm.対応案策定予定日時}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      対応案策定予定日時: event.target.value,
                    })
                  }
                  disabled={loading}
                />
              </label>

              <label
                className="form-field-wide"
                htmlFor="investigation-next-update"
              >
                進捗更新の次回更新予定日時
                <input
                  id="investigation-next-update"
                  type="datetime-local"
                  step={1}
                  value={editForm.進捗更新の次回更新予定日時}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      進捗更新の次回更新予定日時: event.target.value,
                    })
                  }
                  disabled={loading}
                />
              </label>
            </div>

            <div className="form-actions">
              <button
                className="button-primary"
                type="submit"
                disabled={loading}
              >
                {loading ? '保存中...' : '保存'}
              </button>
            </div>
          </form>

        </section>
      </main>
    </div>
  )
}
