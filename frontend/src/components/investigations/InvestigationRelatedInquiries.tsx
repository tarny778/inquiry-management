
import type { InvestigationRelatedInquiry } from '../../types'

type InvestigationRelatedInquiriesProps = {
  relatedInquiries: InvestigationRelatedInquiry[]
}

export default function InvestigationRelatedInquiries({
  relatedInquiries,
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
      <h3>関連する問い合わせ問題調査</h3>

      <p>関連件数：{relatedInquiries.length} 件</p>

      <table>
        <thead>
          <tr>
            <th>問い合わせ問題調査番号</th>
            <th>問い合わせ番号</th>
            <th>問い合わせ者</th>
            <th>対応担当者</th>
            <th>関連状態</th>
            <th>調査開始日時</th>
            <th>断念日時</th>
            <th>リアクション被要求日時</th>
            <th>リアクション日時</th>
            <th>リアクション内容</th>
            <th>NGでの移行先問題調査番号</th>
          </tr>
        </thead>

        <tbody>
          {relatedInquiries.length === 0 ? (
            <tr>
              <td colSpan={11}>
                関連する問い合わせ問題調査はありません。
              </td>
            </tr>
          ) : (
            relatedInquiries.map((relatedInquiry) => (
              <tr
                key={relatedInquiry.問い合わせ問題調査番号}
              >
                <td>
                  {relatedInquiry.問い合わせ問題調査番号}
                </td>
                <td>{relatedInquiry.問い合わせ番号}</td>
                <td>{relatedInquiry.問い合わせ者氏名}</td>
                <td>
                  {relatedInquiry.対応担当者氏名}
                </td>
                <td>
                  {statusLabels[
                    relatedInquiry.問い合わせ問題調査状態
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
                  {relatedInquiry.NGでの移行先問題調査番号 ?? '—'}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </section>
  )
}
