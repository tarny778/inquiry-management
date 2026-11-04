
import type {
  InvestigationRelatedInquiry,
  LoginUser,
} from '../../types'
import { formatApiDateTimeInJapan } from '../../dateTime'

type InvestigationRelatedInquiriesProps = {
  relatedInquiries: InvestigationRelatedInquiry[]
  user: LoginUser | null
  investigationState: number
  loading: boolean
  onAbandonRelated: (relationNumber: number) => Promise<void>
  onAnswerOk: (relationId: number) => Promise<void>
  onAnswerNg: (relationId: number) => Promise<void>
  onOpenInquiry: (inquiryNumber: number) => void
  onOpenInvestigation: (investigationNumber: number) => void
}

export default function InvestigationRelatedInquiries({
  relatedInquiries,
  user,
  investigationState,
  loading,
  onAbandonRelated,
  onAnswerOk,
  onAnswerNg,
  onOpenInquiry,
  onOpenInvestigation,
}: InvestigationRelatedInquiriesProps) {
  const statusLabels: Record<number, string> = {
    1: '調査中',
    2: '断念',
    3: 'リアクション待ち',
    4: 'OK',
    5: 'NG',
  }

  const statusClasses: Record<number, string> = {
    1: 'investigating',
    2: 'abandoned',
    3: 'reaction-waiting',
    4: 'related-ok',
    5: 'related-ng',
  }

  return (
    <section className="list-section">
      <h3>関連する問い合わせ調査：{relatedInquiries.length} 件</h3>

      <div className="related-inquiries-table-wrap">
        <table className="related-inquiries-table">
          <colgroup>
            <col className="col-relation-number" />
            <col className="col-inquiry-number" />
            <col className="col-requester" />
            <col className="col-handler" />
            <col className="col-related-status" />
            <col className="col-reaction" />
            <col className="col-next-investigation" />
            <col className="col-abandon-date" />
          </colgroup>

          <thead>
            <tr>
              <th>問い合わせ調査番号</th>
              <th>問い合わせ番号</th>
              <th>問い合わせ者</th>
              <th>対応担当者</th>
              <th>関連状態</th>
              <th>リアクション内容日時</th>
              <th>NGでの移行先調査番号</th>
              <th>個別断念日時</th>
            </tr>
          </thead>

          <tbody>
            {relatedInquiries.length === 0 ? (
              <tr>
                <td colSpan={8} className="related-inquiries-empty">
                  関連する問い合わせ調査はありません。
                </td>
              </tr>
            ) : (
              relatedInquiries.map((relatedInquiry) => {
                const relationNumber =
                  relatedInquiry['問い合わせ調査番号']

                const relationState =
                  relatedInquiry['問い合わせ調査状態']

                const canAbandonRelated =
                  user !== null &&
                  investigationState === 1 &&
                  relationState === 1 &&
                  relatedInquiry['対応担当者職員番号'] ===
                    user['職員番号']

                const canAnswer =
                  user !== null &&
                  investigationState === 2 &&
                  relationState === 3 &&
                  relatedInquiry['問い合わせ職員番号'] ===
                    user['職員番号']

                const hasReaction =
                  relatedInquiry['リアクション日時'] !== null ||
                  relatedInquiry['リアクション内容'] !== null

                return (
                  <tr key={relationNumber}>
                    <td className="related-number-cell">
                      {relationNumber}
                    </td>

                    <td className="related-number-cell">
                      <button
                        className="link-button"
                        type="button"
                        onClick={() =>
                          onOpenInquiry(relatedInquiry['問い合わせ番号'])
                        }
                        disabled={loading}
                      >
                        {relatedInquiry['問い合わせ番号']}
                      </button>
                    </td>

                    <td>{relatedInquiry['問い合わせ職員番号']}</td>

                    <td>{relatedInquiry['対応担当者職員番号']}</td>

                    <td>
                      <span
                        className={`related-status ${
                          statusClasses[relationState] ?? 'unknown'
                        }`}
                      >
                        {statusLabels[relationState] ?? '不明'}
                      </span>
                    </td>

                    <td className="related-reaction-cell">
                      {hasReaction ? (
                        <div className="related-reaction-details">
                          <span>
                            {formatApiDateTimeInJapan(relatedInquiry['リアクション日時'])}
                          </span>
                          <span>
                            {{
                              '1': 'OK',
                              '2': 'NG',
                            }[String(relatedInquiry['リアクション内容'])] ??
                              relatedInquiry['リアクション内容'] ??
                              '内容なし'}
                          </span>
                        </div>
                      ) : canAnswer ? (
                        <div className="related-reaction-actions">
                          <button
                            className="button-success"
                            type="button"
                            disabled={loading}
                            onClick={() => void onAnswerOk(relationNumber)}
                          >
                            OK
                          </button>

                          <button
                            className="button-danger"
                            type="button"
                            disabled={loading}
                            onClick={() => void onAnswerNg(relationNumber)}
                          >
                            NG
                          </button>
                        </div>
                      ) : (
                        '—'
                      )}
                    </td>

                    <td className="related-number-cell">
                      {relatedInquiry['NGでの移行先調査番号'] ? (
                        <button
                          className="link-button"
                          type="button"
                          onClick={() =>
                            onOpenInvestigation(
                              relatedInquiry['NGでの移行先調査番号']!
                            )
                          }
                          disabled={loading}
                        >
                          {relatedInquiry['NGでの移行先調査番号']}
                        </button>
                        ):'-'
                      }
                    </td>

                    <td className="related-abandon-cell">
                      {relatedInquiry['断念日時'] !== null ? (
                        formatApiDateTimeInJapan(relatedInquiry['断念日時'])
                      ) : canAbandonRelated ? (
                        <button
                          className="button-secondary"
                          type="button"
                          disabled={loading}
                          onClick={() => void onAbandonRelated(relationNumber)}
                        >
                          断念
                        </button>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </section>
  )
}
