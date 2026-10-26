type InquiryBulkActionProps = {
  loading: boolean  
  selectedNumbers: number[]
  handleBulkAccept: () => Promise<void>
  handleBulkComplete: () => Promise<void>
  setIsLinkInvestigationDialogOpen: (open: boolean) => void
  setIsCreateInvestigationDialogOpen: (open: boolean) => void
}

export default function InquiryBulkAction({
  loading,
  selectedNumbers,
  handleBulkAccept,
  handleBulkComplete,
  setIsLinkInvestigationDialogOpen,
  setIsCreateInvestigationDialogOpen,
}: InquiryBulkActionProps) {
  return (
    <div className="bulk-toolbar">
        <span className="selected-count">
            選択中：{selectedNumbers.length}件
        </span>

        <div className="bulk-buttons">
            <button
            className="button-primary"
            type="button"
            onClick={() => void handleBulkAccept()}
            disabled={selectedNumbers.length === 0 || loading}
            >
            {loading ? '処理中...' : '引き受け'}
            </button>

            
            <div className="bulk-investigation-actions">
            <button
                type="button"
                onClick={() => setIsLinkInvestigationDialogOpen(true)}
                disabled={selectedNumbers.length === 0 || loading}
            >
                既存の調査に関連付け
            </button>

            <button
                type="button"
                onClick={() => setIsCreateInvestigationDialogOpen(true)}
                disabled={selectedNumbers.length === 0 || loading}
            >
                新しい調査を作成・関連付け
            </button>
            </div>


            
            <button
            className="button-primary"
            type="button"
            onClick={() => void handleBulkComplete()}
            disabled={selectedNumbers.length === 0 || loading}
            >
            {loading ? '処理中...' : '対応完了'}
            </button>

        </div>
    </div>
  )
}
