
import type { SubmitEvent } from 'react'
import type {
  InvestigationDetail,
  InvestigationEditForm,
} from '../../types'

type InvestigationUpdateProps = {
  investigation: InvestigationDetail
  editForm: InvestigationEditForm
  setEditForm: React.Dispatch<
    React.SetStateAction<InvestigationEditForm>
  >
  onSubmit: (event: SubmitEvent<HTMLFormElement>) => void
  onCancel: () => void
  loading: boolean
}

export default function InvestigationUpdate({
  investigation,
  editForm,
  setEditForm,
  onSubmit,
  onCancel,
  loading,
}: InvestigationUpdateProps) {
  return (
    <section className="detail-section">
      <h2>調査の編集</h2>
      <p>調査番号：{investigation.調査番号}</p>

      <form onSubmit={onSubmit}>
        <div className="form-group">
          <label htmlFor="investigation-name">
            名称や仮説
          </label>
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
        </div>

        <div className="form-group">
          <label htmlFor="investigation-cause">
            原因・仮説
          </label>
          <textarea
            id="investigation-cause"
            value={editForm.原因・仮説}
            onChange={(event) =>
              setEditForm({
                ...editForm,
                原因・仮説: event.target.value,
              })
            }
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="investigation-it-response">
            情シス側での対応
          </label>
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
        </div>

        <div className="form-group">
          <label htmlFor="investigation-requester-response">
            問い合わせ者側で必要な対応
          </label>
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
        </div>

        <div className="form-group">
          <label htmlFor="investigation-plan-date">
            対応案策定予定日時
          </label>
          <input
            id="investigation-plan-date"
            type="datetime-local"
            value={editForm.対応案策定予定日時}
            onChange={(event) =>
              setEditForm({
                ...editForm,
                対応案策定予定日時: event.target.value,
              })
            }
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="investigation-next-update">
            進捗更新の次回更新予定日時
          </label>
          <input
            id="investigation-next-update"
            type="datetime-local"
            value={editForm.進捗更新の次回更新予定日時}
            onChange={(event) =>
              setEditForm({
                ...editForm,
                進捗更新の次回更新予定日時: event.target.value,
              })
            }
            disabled={loading}
          />
        </div>

        <div className="form-actions">
          <button
            type="submit"
            disabled={loading}
          >
            {loading ? '保存中...' : '保存'}
          </button>

          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
          >
            キャンセル
          </button>
        </div>
      </form>
    </section>
  )
}
