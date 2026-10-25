
import type { InvestigationDetail,LoginUser } from '../../types'
import InvestigationInfo from './InvestigationInfo'
import InvestigationRelatedInquiries from './InvestigationRelatedInquiries'

type InvestigationDetailViewProps = {
  investigation: InvestigationDetail
  user: LoginUser | null
  loading: boolean
  onBack: () => Promise<void>
  onEdit: () => void
  onAbandon:() => Promise<void>
  onRequestReaction:() => Promise<void>
}

export default function InvestigationDetailView({
  investigation,
  user,
  loading,
  onBack,
  onEdit,
  onAbandon,
  onRequestReaction,
}: InvestigationDetailViewProps) {
  
  const canAbandon =
    user !== null &&
    investigation['問題調査状態'] === 1 &&
    investigation['関連する問い合わせ問題調査'].length > 0 &&
    investigation['関連する問い合わせ問題調査'].every(
      (item) =>
        item['対応担当者職員番号'] === user['職員番号'],
    )
  return (
    <div>
      <h2>問題調査詳細</h2>

      <button
        type="button"
        onClick={onBack}
        disabled={loading}
      >
        問題調査一覧へ戻る
      </button>

      <button
        type="button"
        onClick={onEdit}
        disabled={loading || !canAbandon}
      >
        編集
      </button>

      <button
        type="button"
        onClick={onAbandon}
        disabled={loading || !canAbandon}
      >
        断念
      </button>

      <button
        type="button"
        onClick={onRequestReaction}
        disabled={loading || !canAbandon}
      >
        リアクション要求
      </button>

      <InvestigationInfo
        investigation={investigation}
      />

      <InvestigationRelatedInquiries
        relatedInquiries={
          investigation.関連する問い合わせ問題調査
        }
      />
    </div>
  )
}
