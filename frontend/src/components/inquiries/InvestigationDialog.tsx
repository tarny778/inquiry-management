type InvestigationDailogProps = {
  loading: boolean  
  selectedNumbers: number[]
  handleBulkLinkInvestigation: () => Promise<void>
  handleBulkCreateInvestigation: () => Promise<void>

  isLinkInvestigationDialogOpen: boolean
  setIsLinkInvestigationDialogOpen: (open: boolean) => void
  isCreateInvestigationDialogOpen: boolean
  setIsCreateInvestigationDialogOpen: (open: boolean) => void

  existingInvestigationNumber: string
  setExistingInvestigationNumber: (value: string) => void
  newInvestigationName: string
  setNewInvestigationName: (value: string) => void
}

export default function InvestigationDailog({
  loading,
  selectedNumbers,
  handleBulkLinkInvestigation,
  handleBulkCreateInvestigation,
  isLinkInvestigationDialogOpen,
  setIsLinkInvestigationDialogOpen,
  isCreateInvestigationDialogOpen,
  setIsCreateInvestigationDialogOpen,

  existingInvestigationNumber,
  setExistingInvestigationNumber,
  newInvestigationName,
  setNewInvestigationName,
}: InvestigationDailogProps) {
  return (
    <>
    {/* 既存の調査への関連付けダイアログ */}
    {isLinkInvestigationDialogOpen && (
    <div className="modal-overlay">
        <section
        className="input-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="link-investigation-title"
        >
        <h2 id="link-investigation-title">
            既存の調査に関連付け
        </h2>

        <label htmlFor="existing-investigation-number">
            調査番号
        </label>

        <input
            id="existing-investigation-number"
            type="number"
            min={1}
            step={1}
            value={existingInvestigationNumber}
            onChange={(event) =>
            setExistingInvestigationNumber(event.target.value)
            }
            placeholder="例：1"
            disabled={loading}
            autoFocus
        />

        <div className="dialog-actions">
            <button
            type="button"
            onClick={() => setIsLinkInvestigationDialogOpen(false)}
            disabled={loading}
            >
            キャンセル
            </button>

            <button
            type="button"
            onClick={async () => {
                try {
                await handleBulkLinkInvestigation()
                } finally {
                setIsLinkInvestigationDialogOpen(false)
                }
            }}
            disabled={
                selectedNumbers.length === 0 ||
                loading ||
                existingInvestigationNumber.trim() === '' ||
                !Number.isInteger(Number(existingInvestigationNumber)) ||
                Number(existingInvestigationNumber) < 1
            }
            >
            {loading ? '処理中...' : '関連付ける'}
            </button>
        </div>
        </section>
    </div>
    )}

    {/* 新しい調査の作成・関連付けダイアログ */}
    {isCreateInvestigationDialogOpen && (
    <div className="modal-overlay">
        <section
        className="input-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="create-investigation-title"
        >
        <h2 id="create-investigation-title">
            新しい調査を作成・関連付け
        </h2>

        <label htmlFor="new-investigation-name">
            調査の名称・仮説（30文字以内）
        </label>

        <input
            id="new-investigation-name"
            type="text"
            value={newInvestigationName}
            onChange={(event) =>
            setNewInvestigationName(event.target.value)
            }
            maxLength={30}
            placeholder="例：メール送信エラーの原因調査"
            disabled={loading}
            autoFocus
        />

        <div className="dialog-actions">
            <button
            type="button"
            onClick={() => setIsCreateInvestigationDialogOpen(false)}
            disabled={loading}
            >
            キャンセル
            </button>

            <button
            type="button"
            onClick={async () => {
                try {
                await handleBulkCreateInvestigation()
                } finally {
                setIsCreateInvestigationDialogOpen(false)
                }
            }}
            disabled={
                selectedNumbers.length === 0 ||
                loading ||
                !newInvestigationName.trim() ||
                newInvestigationName.trim().length > 30
            }
            >
            {loading ? '処理中...' : '作成・関連付ける'}
            </button>
        </div>
        </section>
    </div>
    )}
    </>

  )
}