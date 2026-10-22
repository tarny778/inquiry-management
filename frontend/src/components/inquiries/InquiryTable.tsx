import type {
  Inquiry,
} from '../../types'


type InquiryTableProps = {
  loading: boolean
  inquiries: Inquiry[]
  selectedNumbers: number[]
  setSelectedNumbers: (
    value: number[] | ((current: number[]) => number[]),
  ) => void
  openInquiryDetail: (inquiryNumber: number) => void
  actionMessage: string
  setActionMessage: (message: string) => void
}

export default function InquiryTable({
  loading,
  inquiries,
  selectedNumbers,
  setSelectedNumbers,
  openInquiryDetail,
  actionMessage,
  setActionMessage,
}: InquiryTableProps) {
  return (
    <div>
    {actionMessage && (
        <p className="action-message" role="status">
            {actionMessage}
        </p>
    )}

    {inquiries.length === 0 ? (
        <p>該当する問い合わせはありません。</p>
    ) : (
        <table className="inquiry-table">
            <colgroup>
            <col className="col-check" />
            <col className="col-number" />
            <col className="col-category" />
            <col className="col-subject" />
            <col className="col-urgency" />
            <col className="col-handler" />
            <col className="col-status" />
            </colgroup>

            <thead>
            <tr>
                <th>
                <input
                    type="checkbox"
                    aria-label="表示中の問い合わせをすべて選択"
                    checked={
                    inquiries.length > 0 &&
                    inquiries.every((item) =>
                        selectedNumbers.includes(item.問い合わせ番号)
                    )
                    }
                    onChange={(event) => {
                    const visibleNumbers = inquiries.map(
                        (item) => item.問い合わせ番号
                    )

                    setSelectedNumbers((current) =>
                        event.target.checked
                        ? Array.from(new Set([...current, ...visibleNumbers]))
                        : current.filter(
                            (number) => !visibleNumbers.includes(number)
                            )
                    )
                    setActionMessage('')
                    }}
                />
                </th>
                <th>番号</th>
                <th>分類</th>
                <th>件名</th>
                <th>緊急度</th>
                <th>対応担当者</th>
                <th>状態</th>
            </tr>
            </thead>

            <tbody>
            {inquiries.map((inquiry) => (
                <tr key={inquiry.問い合わせ番号}>
                <td className="check-cell">
                    <input
                    type="checkbox"
                    aria-label={`問い合わせ番号 ${inquiry.問い合わせ番号} を選択`}
                    checked={selectedNumbers.includes(
                        inquiry.問い合わせ番号
                    )}
                    onChange={(event) => {
                        setSelectedNumbers((current) =>
                        event.target.checked
                            ? [...current, inquiry.問い合わせ番号]
                            : current.filter(
                                (number) =>
                                number !== inquiry.問い合わせ番号
                            )
                        )
                        setActionMessage('')
                    }}
                    />
                </td>

                <td className="number-cell">
                    <button
                    type="button"
                    className="link-button"
                    onClick={() => openInquiryDetail(inquiry.問い合わせ番号)}
                    disabled={loading}
                    >
                    {inquiry.問い合わせ番号}
                    </button>
                </td>

                <td>{inquiry.問い合わせ分類 || '—'}</td>

                <td className="subject-cell">
                    <button
                    type="button"
                    className="link-button"
                    onClick={() => openInquiryDetail(inquiry.問い合わせ番号)}
                    disabled={loading}
                    >
                    {inquiry.件名}
                    </button>
                </td>

                <td>
                    {inquiry.緊急度 == null
                    ? '—'
                    : inquiry.緊急度}
                </td>

                <td className="handler-cell">
                    {inquiry.対応担当者 || '未割当'}
                </td>

                <td>
                    <span
                    className={`status ${
                        inquiry.状態 === '引き受け待ち'
                        ? 'waiting'
                        : inquiry.状態 === '対応中'
                            ? 'in-progress'
                            : 'completed'
                    }`}
                    >
                    {inquiry.状態}
                    </span>
                </td>
                </tr>
            ))}
            </tbody>
        </table>
    )}
    </div>
  )
}
        