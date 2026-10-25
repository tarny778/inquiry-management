
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
      <h3>問題調査情報</h3>

      <table>
        <tbody>
          <tr>
            <th>問題調査番号</th>
            <td>{investigation.問題調査番号}</td>
          </tr>
          <tr>
            <th>名称や仮説</th>
            <td>{investigation.問題調査の名称や仮説}</td>
          </tr>
          <tr>
            <th>問題の原因</th>
            <td>{investigation.問題の原因 ?? '未設定'}</td>
          </tr>
          <tr>
            <th>情シス側での対応</th>
            <td>{investigation.情シス側での対応 ?? '未設定'}</td>
          </tr>
          <tr>
            <th>問い合わせ者側で必要な対応</th>
            <td>{investigation.問い合わせ者側で必要な対応 ?? '未設定'}</td>
          </tr>
          <tr>
            <th>問題調査状態</th>
            <td>
              {statusLabels[investigation.問題調査状態] ?? '不明'}
            </td>
          </tr>
          <tr>
            <th>調査開始日時</th>
            <td>{investigation.調査開始日時 ?? '未設定'}</td>
          </tr>
          <tr>
            <th>対応案策定予定日時</th>
            <td>{investigation.対応案策定予定日時 ?? '未設定'}</td>
          </tr>
          <tr>
            <th>進捗更新の次回更新予定日時</th>
            <td>
              {investigation.進捗更新の次回更新予定日時 ?? '未設定'}
            </td>
          </tr>
          <tr>
            <th>リアクション要求日時</th>
            <td>{investigation.リアクション要求日時 ?? '未設定'}</td>
          </tr>
          <tr>
            <th>問題調査断念日時</th>
            <td>{investigation.問題調査断念日時 ?? '未設定'}</td>
          </tr>
          <tr>
            <th>最新移行先の問題調査番号</th>
            <td>{investigation.最新移行先の問題調査番号}</td>
          </tr>
        </tbody>
      </table>
    </section>
  )
}
