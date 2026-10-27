
import type { InvestigationDetail,LoginUser } from '../../types'

import PageHeader from '../PageHeader'
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
  onAbandonRelated: (relationNumber: number) => Promise<void>
  onAnswerRelatedInquiryOk: (relationId: number) => Promise<void>
  onAnswerRelatedInquiryNg: (relationId: number) => Promise<void>
  onOpenInquiry: (inquiryNumber: number) => void
}

export default function InvestigationDetailView({
  investigation,
  user,
  loading,
  onBack,
  onEdit,
  onAbandon,
  onRequestReaction,
  onAbandonRelated,
  onAnswerRelatedInquiryOk,
  onAnswerRelatedInquiryNg,
  onOpenInquiry,
}: InvestigationDetailViewProps) {
  
  const canAbandon =
    user !== null &&
    investigation['調査状態'] === 1 &&
    investigation['関連する問い合わせ調査'].length > 0 &&
    investigation['関連する問い合わせ調査'].every(
      (item) =>
        item['対応担当者職員番号'] === user['職員番号'],
    )
  return (
    <div className="app">

      <main className="main">
        
        <PageHeader
          section="問題調査"
          title="調査詳細"
          actions={
            <>
              {user?.所属 === '情報システム課' && (
                <button
                  className="button-primary"
                  type="button"
                  onClick={onEdit}
                  disabled={loading || !canAbandon}
                >
                  編集
                </button>
              )}
              {user?.所属 === '情報システム課' && (
                <button
                  className="button-primary"
                  type="button"
                  onClick={onRequestReaction}
                  disabled={loading || !canAbandon}
                >
                  リアクション要求
                </button>
              )}
              {user?.所属 === '情報システム課' && (
                <button
                  className="button-secondary"
                  type="button"
                  onClick={onAbandon}
                  disabled={loading || !canAbandon}
                >
                  断念
                </button>
              )}

              <button
                className="button-secondary"
                type="button"
                onClick={onBack}
                disabled={loading}
              >
                ↑ 一覧に戻る
              </button>
            </>
          }
        />

        <InvestigationInfo
          investigation={investigation}
        />

        <InvestigationRelatedInquiries
          relatedInquiries={
            investigation.関連する問い合わせ調査
          }
          user={user}
          investigationState={investigation.調査状態}
          loading={loading}
          onAbandonRelated={onAbandonRelated}
          onAnswerOk={onAnswerRelatedInquiryOk}
          onAnswerNg={onAnswerRelatedInquiryNg}
          onOpenInquiry={onOpenInquiry}
        />
      </main>
    </div>
  )
}
