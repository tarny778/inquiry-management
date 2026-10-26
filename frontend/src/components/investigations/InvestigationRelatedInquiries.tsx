
import type {
  InvestigationRelatedInquiry,
  LoginUser,
} from '../../types'

type InvestigationRelatedInquiriesProps = {
  relatedInquiries: InvestigationRelatedInquiry[]
  user: LoginUser | null
  investigationState: number
  loading: boolean
  onAbandonRelated: (relationNumber: number) => Promise<void>
  onAnswerOk: (relationId: number) => Promise<void>
  onAnswerNg: (relationId: number) => Promise<void>
}

export default function InvestigationRelatedInquiries({
  relatedInquiries,
  user,
  investigationState,
  loading,
  onAbandonRelated,
  onAnswerOk,
  onAnswerNg,
}: InvestigationRelatedInquiriesProps) {
  const statusLabels: Record<number, string> = {
    1: '調査中',
    2: '断念',
    3: 'リアクション待ち',
    4: 'OK',
    5: 'NG',
  }

  return (
    <section className="list-section">
      <h3>関連する問い合わせ調査</h3>

      <p>関連件数：{relatedInquiries.length} 件</p>

      <table>
        <thead>
          <tr>
            <th>問い合わせ調査番号</th>
            <th>問い合わせ番号</th>
            <th>問い合わせ者</th>
            <th>対応担当者</th>
            <th>関連状態</th>
            <th>調査開始日時</th>
            <th>断念日時</th>
            <th>リアクション被要求日時</th>
            <th>リアクション日時</th>
            <th>リアクション内容</th>
            <th>NGでの移行先調査番号</th>
            <th>個別断念</th>
            <th>OK回答</th>
            <th>NG回答</th>
          </tr>
        </thead>

        <tbody>
          {relatedInquiries.length === 0 ? (
            <tr>
              <td colSpan={14}>
                関連する問い合わせ調査はありません。
              </td>
            </tr>
          ) : (
            relatedInquiries.map((relatedInquiry) => {
              const canAbandonRelated =
                user !== null &&
                investigationState === 1 &&
                relatedInquiry['問い合わせ調査状態'] === 1 &&
                relatedInquiry['対応担当者職員番号'] === user['職員番号']
              const canAnswer = (relatedInquiry: InvestigationRelatedInquiry) =>
                user !== null &&
                investigationState === 2 &&
                relatedInquiry['問い合わせ調査状態'] === 3 &&
                relatedInquiry['問い合わせ職員番号'] === user['職員番号']
              return(
                <tr
                  key={relatedInquiry.問い合わせ調査番号}
                >
                  <td>
                    {relatedInquiry.問い合わせ調査番号}
                  </td>
                  <td>{relatedInquiry.問い合わせ番号}</td>
                  <td>{relatedInquiry.問い合わせ者氏名}</td>
                  <td>
                    {relatedInquiry.対応担当者氏名}
                  </td>
                  <td>
                    {statusLabels[
                      relatedInquiry.問い合わせ調査状態
                    ] ?? '不明'}
                  </td>
                  <td>
                    {relatedInquiry.調査開始日時 ?? '—'}
                  </td>
                  <td>
                    {relatedInquiry.断念日時 ?? '—'}
                  </td>
                  <td>
                    {relatedInquiry.リアクション被要求日時 ?? '—'}
                  </td>
                  <td>
                    {relatedInquiry.リアクション日時 ?? '—'}
                  </td>
                  <td>
                    {relatedInquiry.リアクション内容 ?? '—'}
                  </td>
                  <td>
                    {relatedInquiry.NGでの移行先調査番号 ?? '—'}
                  </td>
                  <td>
                    <button
                      className="button-secondary"
                      type="button"
                      onClick={() =>
                        onAbandonRelated(
                          relatedInquiry['問い合わせ調査番号'],
                        )
                      }
                      disabled={loading || !canAbandonRelated}
                    >
                      個別断念
                    </button>
                  </td>
                  <td>
                    {canAnswer(relatedInquiry) && (
                      <button
                        className="button-success"
                        type="button"
                        disabled={loading}
                        onClick={() =>
                          void onAnswerOk(
                            relatedInquiry['問い合わせ調査番号'],
                          )
                        }
                      >
                        OK
                      </button>
                    )}
                  </td>

                  <td>
                    {canAnswer(relatedInquiry) && (
                      <button
                        className="button-danger"
                        type="button"
                        disabled={loading}
                        onClick={() =>
                          void onAnswerNg(
                            relatedInquiry['問い合わせ調査番号'],
                          )
                        }
                      >
                        NG
                      </button>
                    )}
                  </td>
                </tr>
              )
            })
          )}
        </tbody>
      </table>
    </section>
  )
}
