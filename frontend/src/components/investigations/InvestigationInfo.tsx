
import { formatApiDateTimeInJapan } from '../../dateTime'
import type { InvestigationDetail } from '../../types'

type InvestigationInfoProps = {
  investigation: InvestigationDetail
}
export default function InvestigationInfo({
  investigation,
}: InvestigationInfoProps) {
  const statusLabels: Record<number, string> = {
    1: '調査中',
    2: 'リアクション要求済み',
    3: '調査断念',
  }

  return (
    <section className="detail-section">
      <h3 className="investigation-detail-title">
        調査番号：{investigation.調査番号}
      </h3>

      <dl className="investigation-detail">
        <div className="investigation-detail-item investigation-detail-full">
          <dt>調査の名称</dt>
          <dd>{investigation.調査の名称 || '未設定'}</dd>
        </div>

        <div className="investigation-detail-item">
          <dt>調査状態</dt>
          <dd>
            {statusLabels[investigation.調査状態] ?? '不明'}
          </dd>
        </div>

        <div className="investigation-detail-item">
          <dt>調査開始日時</dt>
          <dd>{formatApiDateTimeInJapan(investigation.調査開始日時)}</dd>
        </div>

        <div className="investigation-detail-item investigation-detail-full">
          <dt>原因・仮説</dt>
          <dd>{investigation['原因・仮説'] ?? '未設定'}</dd>
        </div>

        <div className="investigation-detail-item investigation-detail-full">
          <dt>情シス側での対応</dt>
          <dd>{investigation.情シス側での対応 ?? '未設定'}</dd>
        </div>

        <div className="investigation-detail-item investigation-detail-full">
          <dt>問い合わせ者側で必要な対応</dt>
          <dd>
            {investigation.問い合わせ者側で必要な対応 ?? '未設定'}
          </dd>
        </div>

        <div className="investigation-detail-item">
          <dt>対応案策定予定日時</dt>
          <dd>{formatApiDateTimeInJapan(investigation.対応案策定予定日時)}</dd>
        </div>

        <div className="investigation-detail-item">
          <dt>進捗更新の次回更新予定日時</dt>
          <dd>
            {formatApiDateTimeInJapan(investigation.進捗更新の次回更新予定日時)}
          </dd>
        </div>

        <div className="investigation-detail-item">
          <dt>リアクション要求日時</dt>
          <dd>{formatApiDateTimeInJapan(investigation.リアクション要求日時)}</dd>
        </div>

        <div className="investigation-detail-item">
          <dt>最新移行先の調査番号</dt>
          <dd>{investigation.最新移行先の調査番号 ?? '—'}</dd>
        </div>

        <div className="investigation-detail-item investigation-detail-full">
          <dt>調査断念日時</dt>
          <dd>{formatApiDateTimeInJapan(investigation.調査断念日時)}</dd>
        </div>
      </dl>
    </section>
  )
}
