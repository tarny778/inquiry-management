
import type { InvestigationDetail } from '../../types'
import InvestigationInfo from './InvestigationInfo'
import InvestigationRelatedInquiries from './InvestigationRelatedInquiries'

type InvestigationDetailViewProps = {
  investigation: InvestigationDetail
  loading: boolean
  onBack: () => void
  onEdit: () => void
}

export default function InvestigationDetailView({
  investigation,
  loading,
  onBack,
  onEdit,
}: InvestigationDetailViewProps) {
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
        disabled={loading}
      >
        編集
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
