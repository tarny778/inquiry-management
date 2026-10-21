
import { useEffect, useState } from 'react'
import './App.css'

const API_BASE_URL = 'http://localhost:8000'


type Inquiry = {
  問い合わせ番号: number
  件名: string
  状態: '引き受け待ち' | '対応中' | '対応完了'
  問い合わせ職員番号?: string | null
  問い合わせ当時の所属?: string
  受付経路?: string
  問い合わせ分類?: string
  緊急度?: number
  受付担当者?: string | null
  対応担当者?: string | null
  受信日時?: string
}

type LoginUser = {
  職員番号: string
  氏名: string
  所属: string
}

type InquiryListResponse = {
  items: Inquiry[]
  page: number
  page_size: number
  total: number
}

type InquiryDetail = {
  問い合わせ番号: number
  問い合わせ職員番号: string | null
  問い合わせ当時の所属: string | null
  受付経路: string | null
  問い合わせ分類: string | null
  件名: string
  緊急度: number | null
  受付時の処理: string | null
  問い合わせ詳細: string | null
  受付担当者: string | null
  対応担当者: string | null
  受信日時: string | null
  登録日時: string | null
  引き受け日時: string | null
  対応完了日時: string | null
  状態: '引き受け待ち' | '対応中' | '対応完了'
  関連する問題調査番号一覧: number[]
}

type ScreenMode = 'list' | 'new' | 'view' | 'edit'

type InquiryCreateForm = {
  問い合わせ職員番号: string
  受付経路: string
  問い合わせ分類: string
  件名: string
  緊急度: string
  受付時の処理: string
  問い合わせ詳細: string
  受信日時: string
}


type InquiryEditForm = {
  問い合わせ職員番号: string
  受付経路: string
  問い合わせ分類: string
  件名: string
  緊急度: string
  受付時の処理: string
  問い合わせ詳細: string
  受信日時: string
}


function getErrorMessage(data: unknown, fallback: string): string {
  if (
    typeof data === 'object' &&
    data !== null &&
    'detail' in data
  ) {
    const detail = (data as { detail: unknown }).detail

    if (typeof detail === 'string') {
      return detail
    }

    return JSON.stringify(detail)
  }

  return fallback
}

function App() {
  const [職員番号, set職員番号] = useState('')
  const [パスワード, setパスワード] = useState('')
  const [user, setUser] = useState<LoginUser | null>(null)
  const initialConditionDescription =
  user?.所属 === '情報システム課'
    ? '引き受け待ちの全件と、自分が対応中の問い合わせ'
    : '自分が問い合わせたもののうち、対応完了前の問い合わせ'

  const [authenticated, setAuthenticated] = useState(false)
  const [checkingSession, setCheckingSession] = useState(true)
  const [loading, setLoading] = useState(false)

  const [inquiries, setInquiries] = useState<Inquiry[]>([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedInquiry, setSelectedInquiry] =
    useState<InquiryDetail | null>(null)

  const [screenMode, setScreenMode] = useState<ScreenMode>('list')
  const [createForm, setCreateForm] = useState<InquiryCreateForm>({
    問い合わせ職員番号: '',
    受付経路: '電話',
    問い合わせ分類: '分類A',
    件名: '',
    緊急度: '2',
    受付時の処理: '2',
    問い合わせ詳細: '',
    受信日時: '',
  })
  const [editForm, setEditForm] = useState<InquiryEditForm>({
    問い合わせ職員番号: '',
    受付経路: '電話',
    問い合わせ分類: '分類A',
    件名: '',
    緊急度: '2',
    受付時の処理: '2',
    問い合わせ詳細: '',
    受信日時: '',
  })

  // 初期条件：初期表示はチェックあり
  const [initialCondition, setInitialCondition] = useState(true)
  // 一覧がどこから取得されたか
  const [listDisplayMode, setListDisplayMode] = useState<
    'initial' | 'search'
  >('initial')
  const listDescription = initialCondition
    ? initialConditionDescription
    : listDisplayMode === 'initial'
      ? '初期条件による結果（検索ボタンを押すと更新）'
      : '検索結果'

  // 一括操作の対象として選択された問い合わせ番号
  const [selectedNumbers, setSelectedNumbers] = useState<number[]>([])

  // 一括操作ボタンの画面確認用メッセージ
  const [actionMessage, setActionMessage] = useState('')

  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false)

  const [isLinkInvestigationDialogOpen, setIsLinkInvestigationDialogOpen] =
  useState(false)
  const [isCreateInvestigationDialogOpen, setIsCreateInvestigationDialogOpen] =
  useState(false)
  const [existingInvestigationNumber, setExistingInvestigationNumber] =
  useState('')
  const [newInvestigationName, setNewInvestigationName] = useState('')

  // 入力中の検索条件
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [urgencyFilter, setUrgencyFilter] = useState('')
  const [receptionistFilter, setReceptionistFilter] = useState('')
  const [handlerFilter, setHandlerFilter] = useState('')
  const [receivedFrom, setReceivedFrom] = useState('')
  const [receivedTo, setReceivedTo] = useState('')

  // 最後に検索ボタンを押したときの条件
  const [appliedFilters, setAppliedFilters] = useState({
    keyword: '',
    status: '',
    category: '',
    urgency: '',
    receptionist: '',
    handler: '',
    receivedFrom: '',
    receivedTo: '',
  })

  const [error, setError] = useState('')
  const [loginError, setLoginError] = useState('')

  // 初期表示では、APIが職員の権限に応じて抽出した一覧を取得する。
  async function loadInquiries(pageNumber = 1) {
    const response = await fetch(
      `${API_BASE_URL}/api/inquiries?初期条件=1&page=${pageNumber}&page_size=50`,
      {
        method: 'GET',
        credentials: 'include',
      },
    )

    const data = await response.json().catch(() => null)

    if (response.status === 401) {
      setAuthenticated(false)
      setUser(null)
      setInquiries([])
      setTotal(0)
      return false
    }

    if (!response.ok) {
      throw new Error(
        getErrorMessage(data, '問い合わせ一覧の取得に失敗しました。'),
      )
    }

    const result = data as InquiryListResponse

    setInquiries(result.items)
    setTotal(result.total)
    setCurrentPage(pageNumber)
    setListDisplayMode('initial')
    setAuthenticated(true)

    return true
  }

  async function fetchSearchResults(
    filters: typeof appliedFilters,
    pageNumber = 1,
  ) {
    setError('')
    setLoading(true)

    try {
      const params = new URLSearchParams({
        初期条件: '2',
        page: String(pageNumber),
        page_size: '50',
      })

      if (filters.keyword.trim()) {
        params.set('件名', filters.keyword.trim())
      }

      if (filters.status) {
        params.append('状態', filters.status)
      }

      if (filters.category) {
        params.set('問い合わせ分類', filters.category)
      }

      if (filters.urgency) {
        params.set('緊急度', filters.urgency)
      }

      if (filters.receptionist.trim()) {
        params.set('受付担当者', filters.receptionist.trim())
      }

      if (filters.handler.trim()) {
        params.set('対応担当者', filters.handler.trim())
      }

      if (filters.receivedFrom) {
        params.set(
          '受信日時開始',
          `${filters.receivedFrom}T00:00:00`,
        )
      }

      if (filters.receivedTo) {
        params.set(
          '受信日時終了',
          `${filters.receivedTo}T23:59:59.999999`,
        )
      }

      const response = await fetch(
        `${API_BASE_URL}/api/inquiries?${params.toString()}`,
        {
          method: 'GET',
          credentials: 'include',
        },
      )

      const data = await response.json().catch(() => null)

      if (response.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedNumbers([])
        return false
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, '問い合わせの検索に失敗しました。'),
        )
      }

      const result = data as InquiryListResponse

      setInquiries(result.items)
      setTotal(result.total)
      setCurrentPage(pageNumber)
      setListDisplayMode('search')
      setSelectedNumbers([])
      setActionMessage('')
      return true
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
      return false
    } finally {
      setLoading(false)
    }
  }

  function handleSearch() {
    const filters = {
      keyword: keyword.trim(),
      status: statusFilter,
      category: categoryFilter,
      urgency: urgencyFilter,
      receptionist: receptionistFilter.trim(),
      handler: handlerFilter.trim(),
      receivedFrom,
      receivedTo,
    }

    setAppliedFilters(filters)
    void fetchSearchResults(filters, 1)
  }

  async function openInquiryDetail(
    inquiryNumber: number,
  ): Promise<boolean> {
    setError('')
    setLoading(true)

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/inquiries/${inquiryNumber}`,
        {
          method: 'GET',
          credentials: 'include',
        },
      )

      const data = await response.json().catch(() => null)

      if (response.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedInquiry(null)
        return false
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, '問い合わせ詳細の取得に失敗しました。'),
        )
      }

      setSelectedInquiry(data as InquiryDetail)
      setScreenMode('view')
      return true
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
      return false
    } finally {
      setLoading(false)
    }
  }

  function openInquiryEdit() {
    if (!selectedInquiry) return

    setEditForm({
      問い合わせ職員番号:
        selectedInquiry.問い合わせ職員番号 ?? '',
      受付経路:
        selectedInquiry.受付経路 ?? '電話',
      問い合わせ分類:
        selectedInquiry.問い合わせ分類 ?? '分類A',
      件名:
        selectedInquiry.件名,
      緊急度:
        String(selectedInquiry.緊急度 ?? 2),
      受付時の処理:
        String(selectedInquiry.受付時の処理 ?? '2'),
      問い合わせ詳細:
        selectedInquiry.問い合わせ詳細 ?? '',
      受信日時:
        selectedInquiry.受信日時 ?? '',
    })

    setScreenMode('edit')
  }

  function openNewInquiry() {
    setError('')
    setSelectedInquiry(null)
    setCreateForm({
      問い合わせ職員番号: '',
      受付経路: '電話',
      問い合わせ分類: '分類A',
      件名: '',
      緊急度: '2',
      受付時の処理: '2',
      問い合わせ詳細: '',
      受信日時: '',
    })
    setScreenMode('new')
  }

  async function handleCreateInquiry(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (loading) return

    setError('')
    setLoading(true)

    try {
      const payload: Record<string, unknown> = {
        問い合わせ職員番号: createForm.問い合わせ職員番号.trim(),
        受付経路: createForm.受付経路,
        問い合わせ分類: createForm.問い合わせ分類,
        件名: createForm.件名.trim(),
        緊急度: Number(createForm.緊急度),
        受付時の処理: Number(createForm.受付時の処理),
        問い合わせ詳細: createForm.問い合わせ詳細.trim() || null,
      }

      if (createForm.受付経路 !== '電話') {
        payload.受信日時 = createForm.受信日時
      }

      const response = await fetch(`${API_BASE_URL}/api/inquiries`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      const data = await response.json().catch(() => null)

      if (response.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedInquiry(null)
        setScreenMode('list')
        return
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, '問い合わせの登録に失敗しました。'),
        )
      }

      const inquiryNumber = data?.問い合わせ番号

      if (typeof inquiryNumber !== 'number') {
        throw new Error('登録は完了しましたが、問い合わせ番号を取得できませんでした。')
      }

      // 新規登録後は一覧の1ページ目に戻る
      setCurrentPage(1)

      setScreenMode('view')
      await openInquiryDetail(inquiryNumber)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setLoading(false)
    }
  }


  async function handleUpdateInquiry(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (loading || !selectedInquiry) return

    setError('')
    setLoading(true)

    try {
      const payload = {
        問い合わせ職員番号: editForm.問い合わせ職員番号.trim(),
        受付経路: editForm.受付経路,
        問い合わせ分類: editForm.問い合わせ分類,
        件名: editForm.件名.trim(),
        緊急度: Number(editForm.緊急度),
        受付時の処理: Number(editForm.受付時の処理),
        問い合わせ詳細: editForm.問い合わせ詳細.trim() || null,
        受信日時: editForm.受信日時 || null,
      }

      const response = await fetch(
        `${API_BASE_URL}/api/inquiries/${selectedInquiry.問い合わせ番号}`,
        {
          method: 'PUT',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        },
      )

      const data = await response.json().catch(() => null)

      if (response.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedInquiry(null)
        setScreenMode('list')
        return
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, '問い合わせの更新に失敗しました。'),
        )
      }

      // 更新後の詳細を再取得する
      await openInquiryDetail(selectedInquiry.問い合わせ番号)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleBulkAccept() {
    if (selectedNumbers.length === 0 || loading) {
      return
    }

    const confirmed = window.confirm(
      `選択した ${selectedNumbers.length} 件の問い合わせを引き受けますか？`,
    )

    if (!confirmed) {
      return
    }

    await acceptInquiries(selectedNumbers)
  }

  async function handleAcceptInquiry(inquiryNumber: number) {
    if (loading) {
      return
    }

    const confirmed = window.confirm(
      `問い合わせ番号 ${inquiryNumber} を引き受けますか？`,
    )

    if (!confirmed) {
      return
    }

    await acceptInquiries([inquiryNumber],true)
  }

  async function acceptInquiries(
    inquiryNumbers: number[],
    returnToDetail = false,
  ) {
    if (inquiryNumbers.length === 0 || loading) {
      return
    }

    setError('')
    setActionMessage('')
    setLoading(true)

    let acceptSucceeded = false

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/inquiries/bulk-accept`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            問い合わせ番号一覧: inquiryNumbers,
          }),
        },
      )

      const data = await response.json().catch(() => null)

      if (response.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedNumbers([])
        setSelectedInquiry(null)
        setScreenMode('list')
        return
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, '問い合わせの引き受けに失敗しました。'),
        )
      }

      acceptSucceeded = true

      // 詳細画面からの単一引き受け
      if (returnToDetail) {
        const refreshed = await openInquiryDetail(inquiryNumbers[0])

        if (!refreshed) {
          setError(
            '引き受けは完了しましたが、問い合わせ詳細の再取得に失敗しました。',
          )
          return
        }

        setActionMessage('問い合わせを引き受けました。')
        return
      }

      // 一覧画面からの引き受け
      let refreshed: boolean

      if (listDisplayMode === 'initial') {
        refreshed = await loadInquiries(currentPage)
      } else {
        refreshed = await fetchSearchResults(appliedFilters, currentPage)
      }

      if (!refreshed) {
        setActionMessage(
          '引き受けは完了しましたが、一覧の再取得に失敗しました。必要に応じて一覧を再読み込みしてください。',
        )
        return
      }

      setSelectedNumbers([])
      setActionMessage(
        inquiryNumbers.length === 1
          ? '問い合わせを引き受けました。'
          : '選択した問い合わせを引き受けました。',
      )
    } catch (err) {
      if (acceptSucceeded) {
        setError(
          err instanceof Error
            ? `引き受けは完了しましたが、画面の更新に失敗しました。${err.message}`
            : '引き受けは完了しましたが、画面の更新に失敗しました。',
        )
      } else {
        setError(
          err instanceof Error
            ? err.message
            : 'サーバーに接続できません。',
        )
      }
    } finally {
      setLoading(false)
    }
  }


  async function handleBulkComplete() {
    if (selectedNumbers.length === 0 || loading) {
      return
    }

    const confirmed = window.confirm(
      `選択した ${selectedNumbers.length} 件の問い合わせを対応完了にしますか？`,
    )

    if (!confirmed) {
      return
    }

    await completeInquiries(selectedNumbers)
  }

  async function handleCompleteInquiry(inquiryNumber: number) {
    if (loading) {
      return
    }

    const confirmed = window.confirm(
      `問い合わせ番号 ${inquiryNumber} を対応完了にしますか？`,
    )

    if (!confirmed) {
      return
    }

    await completeInquiries([inquiryNumber], true)
  }

  async function completeInquiries(
    inquiryNumbers: number[],
    returnToDetail = false,
  ) {
    if (inquiryNumbers.length === 0 || loading) {
      return
    }

    setError('')
    setActionMessage('')
    setLoading(true)

    let completeSucceeded = false

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/inquiries/bulk-complete`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            問い合わせ番号一覧: inquiryNumbers,
          }),
        },
      )

      const data = await response.json().catch(() => null)

      if (response.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedNumbers([])
        setSelectedInquiry(null)
        setScreenMode('list')
        return
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, '問い合わせの対応完了に失敗しました。'),
        )
      }

      completeSucceeded = true

      // 詳細画面からの個別完了
      if (returnToDetail) {
        const refreshed = await openInquiryDetail(inquiryNumbers[0])

        if (!refreshed) {
          setError(
            '対応完了しましたが、問い合わせ詳細の再取得に失敗しました。',
          )
          return
        }

        setActionMessage('問い合わせを対応完了にしました。')
        return
      }

      // 一覧画面からの完了
      let refreshed: boolean

      if (listDisplayMode === 'initial') {
        refreshed = await loadInquiries(currentPage)
      } else {
        refreshed = await fetchSearchResults(appliedFilters, currentPage)
      }

      if (!refreshed) {
        setActionMessage(
          '対応完了しましたが、一覧の再取得に失敗しました。必要に応じて一覧を再読み込みしてください。',
        )
        return
      }

      setSelectedNumbers([])
      setActionMessage(
        inquiryNumbers.length === 1
          ? '問い合わせを対応完了にしました。'
          : '選択した問い合わせを対応完了にしました。',
      )
    } catch (err) {
      if (completeSucceeded) {
        setError(
          err instanceof Error
            ? `対応完了しましたが、画面の更新に失敗しました。${err.message}`
            : '対応完了しましたが、画面の更新に失敗しました。',
        )
      } else {
        setError(
          err instanceof Error
            ? err.message
            : 'サーバーに接続できません。',
        )
      }
    } finally {
      setLoading(false)
    }
  }


  async function handleReopenInquiry(inquiryNumber: number) {
    if (loading) {
      return
    }

    const confirmed = window.confirm(
      `問い合わせ番号 ${inquiryNumber} を再開しますか？`,
    )

    if (!confirmed) {
      return
    }

    setError('')
    setActionMessage('')
    setLoading(true)

    let reopenSucceeded = false

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/inquiries/${inquiryNumber}/reopen`,
        {
          method: 'POST',
          credentials: 'include',
        },
      )

      const data = await response.json().catch(() => null)

      if (response.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedNumbers([])
        setSelectedInquiry(null)
        setScreenMode('list')
        return
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, '問い合わせの再開に失敗しました。'),
        )
      }

      reopenSucceeded = true

      const refreshed = await openInquiryDetail(inquiryNumber)

      if (!refreshed) {
        setError(
          '再開しましたが、問い合わせ詳細の再取得に失敗しました。',
        )
        return
      }

      setActionMessage('問い合わせを再開しました。')
    } catch (err) {
      setError(
        err instanceof Error
          ? reopenSucceeded
            ? `再開しましたが、画面の更新に失敗しました。${err.message}`
            : err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setLoading(false)
    }
  }



  async function handleBulkLinkInvestigation() {
    const investigationNumber = Number(existingInvestigationNumber)

    if (
      selectedNumbers.length === 0 ||
      loading ||
      !Number.isInteger(investigationNumber) ||
      investigationNumber < 1
    ) {
      return
    }

    const confirmed = window.confirm(
      `選択した ${selectedNumbers.length} 件の問い合わせを、問題調査番号 ${investigationNumber} に関連付けますか？`,
    )

    if (!confirmed) {
      return
    }

    setError('')
    setActionMessage('')
    setLoading(true)

    let linkSucceeded = false

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/inquiries/bulk-link-investigation`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            問い合わせ番号一覧: selectedNumbers,
            問題調査番号: investigationNumber,
          }),
        },
      )

      const data = await response.json().catch(() => null)

      if (response.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedNumbers([])
        return
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            data,
            '既存の問題調査への関連付けに失敗しました。',
          ),
        )
      }

      linkSucceeded = true

      let refreshed: boolean

      if (listDisplayMode === 'initial') {
        refreshed = await loadInquiries(currentPage)
      } else {
        refreshed = await fetchSearchResults(appliedFilters, currentPage)
      }

      if (!refreshed) {
        setActionMessage(
          `問題調査番号 ${investigationNumber} への関連付けは完了しましたが、一覧の再取得に失敗しました。必要に応じて一覧を再読み込みしてください。`,
        )
        return
      }

      setSelectedNumbers([])
      setExistingInvestigationNumber('')

      setActionMessage(
        `問題調査番号 ${data?.問題調査番号 ?? investigationNumber} に、${data?.関連付け件数 ?? selectedNumbers.length} 件の問い合わせを関連付けました。`,
      )
    } catch (err) {
      if (linkSucceeded) {
        setError(
          err instanceof Error
            ? `関連付けは完了しましたが、一覧の更新に失敗しました。${err.message}`
            : '関連付けは完了しましたが、一覧の更新に失敗しました。',
        )
      } else {
        setError(
          err instanceof Error
            ? err.message
            : 'サーバーに接続できません。',
        )
      }
    } finally {
      setLoading(false)
    }
  }



  async function handleBulkCreateInvestigation() {
    if (
      selectedNumbers.length === 0 ||
      loading ||
      !newInvestigationName.trim()
    ) {
      return
    }

    const confirmed = window.confirm(
      `選択した ${selectedNumbers.length} 件の問い合わせに、新しい問題調査「${newInvestigationName.trim()}」を作成して関連付けますか？`,
    )

    if (!confirmed) {
      return
    }

    setError('')
    setActionMessage('')
    setLoading(true)

    let createSucceeded = false

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/inquiries/bulk-investigations`,
        {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            問い合わせ番号一覧: selectedNumbers,
            問題調査の名称や仮説: newInvestigationName.trim(),
          }),
        },
      )

      const data = await response.json().catch(() => null)

      if (response.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedNumbers([])
        return
      }

      if (!response.ok) {
        throw new Error(
          getErrorMessage(
            data,
            '新しい問題調査の作成・関連付けに失敗しました。',
          ),
        )
      }

      createSucceeded = true

      let refreshed: boolean

      if (listDisplayMode === 'initial') {
        refreshed = await loadInquiries(currentPage)
      } else {
        refreshed = await fetchSearchResults(appliedFilters, currentPage)
      }

      if (!refreshed) {
        setActionMessage(
          `問題調査を作成して ${selectedNumbers.length} 件に関連付けましたが、一覧の再取得に失敗しました。必要に応じて一覧を再読み込みしてください。`,
        )
        return
      }

      setSelectedNumbers([])
      setNewInvestigationName('')
      setActionMessage(
        `新しい問題調査を作成し、${data?.関連付け件数 ?? selectedNumbers.length} 件の問い合わせに関連付けました。問題調査番号：${data?.問題調査番号 ?? '不明'}`,
      )
    } catch (err) {
      if (createSucceeded) {
        setError(
          err instanceof Error
            ? `問題調査の作成・関連付けは完了しましたが、一覧の更新に失敗しました。${err.message}`
            : '問題調査の作成・関連付けは完了しましたが、一覧の更新に失敗しました。',
        )
      } else {
        setError(
          err instanceof Error
            ? err.message
            : 'サーバーに接続できません。',
        )
      }
    } finally {
      setLoading(false)
    }
  }




  const handleInitialConditionChange = async (checked: boolean) => {
    // なし → あり：確認後に初期条件で再検索
    if (checked) {
      const confirmed = window.confirm(
        `「${initialConditionDescription}」という条件で絞った問い合わせを表示します。よろしいですか？`
      )

      // キャンセルならチェック状態を変更しない
      if (!confirmed) {
        return
      }

      // 検索条件をすべてクリア
      setKeyword('')
      setStatusFilter('')
      setCategoryFilter('')
      setUrgencyFilter('')
      setReceptionistFilter('')
      setHandlerFilter('')

      setAppliedFilters({
        keyword: '',
        status: '',
        category: '',
        urgency: '',
        receptionist: '',
        handler: '',
        receivedFrom: '',
        receivedTo: '',
      })

      setError('')
      setActionMessage('')
      setInitialCondition(true)

      // 初期条件1で一覧を取り直す
      setLoading(true)
      try {
        await loadInquiries()
      } finally {
        setLoading(false)
      }

      return
    }

    // あり → なし：一覧はそのまま維持
    setInitialCondition(false)
  }

  const clearSearch = () => {
    setKeyword('')
    setStatusFilter('')
    setCategoryFilter('')
    setUrgencyFilter('')
    setReceptionistFilter('')
    setHandlerFilter('')
    setReceivedFrom('')
    setReceivedTo('')

    setAppliedFilters({
      keyword: '',
      status: '',
      category: '',
      urgency: '',
      receptionist: '',
      handler: '',
      receivedFrom: '',
      receivedTo: '',
    })

    setSelectedNumbers([])
    setActionMessage('')
    setError('')
  }



  // ページを開いたとき、既存セッションがあれば一覧を取得する。
  useEffect(() => {
    let cancelled = false

    async function checkSession() {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/inquiries?初期条件=1&page=1&page_size=50`,
          { credentials: 'include' },
        )

        const data = await response.json().catch(() => null)

        if (cancelled) return

        if (response.status === 401) {
          setAuthenticated(false)
          return
        }

        if (!response.ok) {
          throw new Error(
            getErrorMessage(data, '問い合わせ一覧の取得に失敗しました。'),
          )
        }

        const result = data as InquiryListResponse
        setInquiries(result.items)
        setTotal(result.total)
        setAuthenticated(true)
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'サーバーに接続できません。',
          )
        }
      } finally {
        if (!cancelled) {
          setCheckingSession(false)
        }
      }
    }

    void checkSession()

    return () => {
      cancelled = true
    }
  }, [])

  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoginError('')
    setError('')
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          職員番号,
          パスワード,
        }),
      })

      const data = await response.json().catch(() => null)

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, 'ログインに失敗しました。'),
        )
      }

      setUser({
        職員番号: data.職員番号,
        氏名: data.氏名,
        所属: data.所属,
      })

      setパスワード('')

      const loaded = await loadInquiries()

      if (!loaded) {
        setLoginError(
          'ログイン後の認証を確認できませんでした。再度ログインしてください。',
        )
        return
      }
    } catch (err) {
      setLoginError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleLogout() {
    setError('')
    setLoading(true)

    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      })

      const data = await response.json().catch(() => null)

      if (!response.ok) {
        throw new Error(
          getErrorMessage(data, 'ログアウトに失敗しました。'),
        )
      }

      setAuthenticated(false)
      setUser(null)
      setInquiries([])
      setTotal(0)
      setKeyword('')
      setStatusFilter('')
      set職員番号('')
      setパスワード('')
      setLoginError('')
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'ログアウトに失敗しました。',
      )
    } finally {
      setLoading(false)
    }
  }

  if (checkingSession) {
    return (
      <div className="app">
        <header className="header">
          <h1>問い合わせ管理システム</h1>
          <p>情報システム課</p>
        </header>
        <main className="main">
          <p>ログイン状態を確認しています...</p>
        </main>
      </div>
    )
  }

  if (!authenticated) {
    return (
      <div className="login-page">
        <header className="header">
          <h1>問い合わせ管理システム</h1>
          <p>情報システム課</p>
        </header>

        <main className="login-card">
          <h2>ログイン</h2>
          <p className="description">
            職員番号とパスワードを入力してください。
          </p>

          <form onSubmit={handleLogin}>
            <label className="login-field">
              職員番号
              <input
                type="text"
                autoComplete="username"
                value={職員番号}
                onChange={(event) => set職員番号(event.target.value)}
                required
              />
            </label>

            <label className="login-field">
              パスワード
              <input
                type="password"
                autoComplete="current-password"
                value={パスワード}
                onChange={(event) => setパスワード(event.target.value)}
                required
              />
            </label>

            {loginError && (
              <p className="error-message" role="alert">
                {loginError}
              </p>
            )}

            {error && (
              <p className="error-message" role="alert">
                {error}
              </p>
            )}

            <button type="submit" disabled={loading}>
              {loading ? 'ログイン中...' : 'ログイン'}
            </button>
          </form>
        </main>
      </div>
    )
  }
  // 新規作成画面
  if (screenMode === 'new') {
    return (
      <div className="app">
        <header className="app-header">
          <h1>問い合わせ管理システム</h1>
          <span className="app-department">情報システム課</span>

          <div className="user-panel">
            {user && <span>{user.氏名}（{user.職員番号}）</span>}
            <button
              type="button"
              className="logout-button"
              onClick={handleLogout}
              disabled={loading}
            >
              ログアウト
            </button>
          </div>
        </header>

        <main className="main">
          <div className="list-header">
            <h2>問い合わせ新規登録</h2>
            <button
              type="button"
              onClick={() => setScreenMode('list')}
              disabled={loading}
            >
              一覧に戻る
            </button>
          </div>

          {error && (
            <p className="error-message" role="alert">{error}</p>
          )}

          <form
            className="search-section"
            onSubmit={handleCreateInquiry}
          >
            <div className="search-fields">
              <label>
                問い合わせ職員番号 *
                <input
                  value={createForm.問い合わせ職員番号}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      問い合わせ職員番号: event.target.value,
                    })
                  }
                  maxLength={20}
                  required
                  disabled={loading}
                />
              </label>

              <label>
                受付経路 *
                <select
                  value={createForm.受付経路}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      受付経路: event.target.value,
                      受信日時: '',
                    })
                  }
                  disabled={loading}
                >
                  <option value="電話">電話</option>
                  <option value="メール">メール</option>
                  <option value="フォーム">フォーム</option>
                </select>
              </label>

              <label>
                問い合わせ分類 *
                <select
                  value={createForm.問い合わせ分類}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      問い合わせ分類: event.target.value,
                    })
                  }
                  disabled={loading}
                >
                  <option value="分類A">分類A</option>
                  <option value="分類B">分類B</option>
                  <option value="分類C">分類C</option>
                </select>
              </label>

              <label>
                件名 *
                <input
                  value={createForm.件名}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      件名: event.target.value,
                    })
                  }
                  maxLength={100}
                  required
                  disabled={loading}
                />
              </label>

              <label>
                緊急度 *
                <select
                  value={createForm.緊急度}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      緊急度: event.target.value,
                    })
                  }
                  disabled={loading}
                >
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                </select>
              </label>

              <label>
                受付時の処理 *
                <select
                  value={createForm.受付時の処理}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      受付時の処理: event.target.value,
                    })
                  }
                  disabled={loading}
                >
                  <option value="1">即時解決</option>
                  <option value="2">要調査</option>
                  <option value="3">他所属案内</option>
                </select>
              </label>

              <label>
                受信日時
                <input
                  type="datetime-local"
                  value={createForm.受信日時}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      受信日時: event.target.value,
                    })
                  }
                  required={createForm.受付経路 !== '電話'}
                  disabled={loading || createForm.受付経路 === '電話'}
                />
                {createForm.受付経路 === '電話' && (
                  <span className="initial-condition-description">
                    電話の場合は登録時に自動設定されます。
                  </span>
                )}
              </label>
            </div>

            <label>
              問い合わせ詳細
              <textarea
                value={createForm.問い合わせ詳細}
                onChange={(event) =>
                  setCreateForm({
                    ...createForm,
                    問い合わせ詳細: event.target.value,
                  })
                }
                maxLength={1000}
                rows={5}
                disabled={loading}
              />
            </label>

            <div className="bulk-buttons">
              <button
                type="button"
                onClick={() => setScreenMode('list')}
                disabled={loading}
              >
                キャンセル
              </button>

              <button type="submit" disabled={loading}>
                {loading ? '登録中...' : '登録する'}
              </button>
            </div>
          </form>
        </main>
      </div>
    )
  }

  // 編集画面
  if (screenMode === 'edit' && selectedInquiry !== null) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>問い合わせ管理システム</h1>
          <span className="app-department">情報システム課</span>
        </header>

        <main className="main">
          <div className="list-header">
            <h2>問い合わせ編集</h2>
          </div>

          <form
            className="search-section"
            onSubmit={handleUpdateInquiry}
          >
            <div className="search-fields">
              <label>
                問い合わせ職員番号 *
                <input
                  value={editForm.問い合わせ職員番号}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      問い合わせ職員番号: event.target.value,
                    })
                  }
                  maxLength={20}
                  required
                  disabled={loading}
                />
              </label>

              <label>
                受付経路 *
                <select
                  value={editForm.受付経路}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      受付経路: event.target.value,
                    })
                  }
                  disabled={loading}
                >
                  <option value="電話">電話</option>
                  <option value="メール">メール</option>
                  <option value="フォーム">フォーム</option>
                </select>
              </label>

              <label>
                問い合わせ分類 *
                <select
                  value={editForm.問い合わせ分類}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      問い合わせ分類: event.target.value,
                    })
                  }
                  disabled={loading}
                >
                  <option value="分類A">分類A</option>
                  <option value="分類B">分類B</option>
                  <option value="分類C">分類C</option>
                </select>
              </label>

              <label>
                件名 *
                <input
                  value={editForm.件名}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      件名: event.target.value,
                    })
                  }
                  maxLength={100}
                  required
                  disabled={loading}
                />
              </label>

              <label>
                緊急度 *
                <select
                  value={editForm.緊急度}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      緊急度: event.target.value,
                    })
                  }
                  disabled={loading}
                >
                  <option value="1">1</option>
                  <option value="2">2</option>
                  <option value="3">3</option>
                </select>
              </label>

              <label>
                受付時の処理 *
                <select
                  value={editForm.受付時の処理}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      受付時の処理: event.target.value,
                    })
                  }
                  disabled={loading}
                >
                  <option value="1">即時解決</option>
                  <option value="2">要調査</option>
                  <option value="3">他所属案内</option>
                </select>
              </label>

              <label>
                受信日時
                <input
                  type="datetime-local"
                  value={editForm.受信日時}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      受信日時: event.target.value,
                    })
                  }
                  required
                  disabled={loading}
                />
              </label>
            </div>

            <label>
              問い合わせ詳細
              <textarea
                value={editForm.問い合わせ詳細}
                onChange={(event) =>
                  setEditForm({
                    ...editForm,
                    問い合わせ詳細: event.target.value,
                  })
                }
                maxLength={1000}
                rows={5}
                disabled={loading}
              />
            </label>

            <div className="bulk-buttons">
              <button
                type="button"
                onClick={() => setScreenMode('view')}
                disabled={loading}
              >
                キャンセル
              </button>

              <button type="submit" disabled={loading}>
                {loading ? '更新中...' : '更新する'}
              </button>
            </div>
          </form>
        </main>
      </div>
    )
  }

  // 詳細画面
  // 詳細画面
  if (selectedInquiry !== null) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>問い合わせ管理システム</h1>
          <span className="app-department">情報システム課</span>

          <div className="user-panel">
            {user && (
              <span>
                {user.氏名}（{user.職員番号}）
              </span>
            )}

            <button
              type="button"
              className="logout-button"
              onClick={handleLogout}
              disabled={loading}
            >
              ログアウト
            </button>
          </div>
        </header>

        <main className="main">
          <div className="list-header">
            <h2>問い合わせ詳細</h2>
            <button
              type="button"
              onClick={async () => {
                setSelectedInquiry(null)
                setScreenMode('list')

                if (listDisplayMode === 'initial') {
                  await loadInquiries(currentPage)
                } else {
                  await fetchSearchResults(appliedFilters, currentPage)
                }
              }}
              disabled={loading}
            >
              一覧に戻る
            </button>
            <button
              type="button"
              onClick={openInquiryEdit}
              disabled={loading || selectedInquiry.状態 === '対応完了'}
            >
              編集
            </button>
            <button
              type="button"
              onClick={() =>
                handleAcceptInquiry(selectedInquiry.問い合わせ番号)}
              disabled={loading || selectedInquiry.状態 !== '引き受け待ち'}
            >
              {loading ? '処理中...' : '引き受け'}
            </button>
            <button
              type="button"
              onClick={() =>
                handleCompleteInquiry(selectedInquiry.問い合わせ番号)}
              disabled={loading || selectedInquiry.状態 !== '対応中'}
            >
              {loading ? '処理中...' : '対応完了'}
            </button>
            <button
              type="button"
              onClick={() =>
                handleReopenInquiry(selectedInquiry.問い合わせ番号)}
              disabled={loading || selectedInquiry.状態 !== '対応完了'}
            >
              {loading ? '処理中...' : '再開'}
            </button>
          </div>

          {error && (
            <p className="error-message" role="alert">
              {error}
            </p>
          )}

          <section className="list-section">
            <h3>
              問い合わせ番号：{selectedInquiry.問い合わせ番号}
            </h3>

            <dl className="inquiry-detail">
              <dt>状態</dt>
              <dd>{selectedInquiry.状態}</dd>

              <dt>件名</dt>
              <dd>{selectedInquiry.件名}</dd>

              <dt>問い合わせ職員番号</dt>
              <dd>{selectedInquiry.問い合わせ職員番号 || '—'}</dd>

              <dt>問い合わせ当時の所属</dt>
              <dd>{selectedInquiry.問い合わせ当時の所属 || '—'}</dd>

              <dt>受付経路</dt>
              <dd>{selectedInquiry.受付経路 || '—'}</dd>

              <dt>問い合わせ分類</dt>
              <dd>{selectedInquiry.問い合わせ分類 || '—'}</dd>

              <dt>緊急度</dt>
              <dd>{selectedInquiry.緊急度 ?? '—'}</dd>

              <dt>受付時の処理</dt>
              <dd>{selectedInquiry.受付時の処理 || '—'}</dd>

              <dt>問い合わせ詳細</dt>
              <dd>{selectedInquiry.問い合わせ詳細 || '—'}</dd>

              <dt>受付担当者</dt>
              <dd>{selectedInquiry.受付担当者 || '—'}</dd>

              <dt>対応担当者</dt>
              <dd>{selectedInquiry.対応担当者 || '—'}</dd>

              <dt>受信日時</dt>
              <dd>{selectedInquiry.受信日時 || '—'}</dd>

              <dt>登録日時</dt>
              <dd>{selectedInquiry.登録日時 || '—'}</dd>

              <dt>引き受け日時</dt>
              <dd>{selectedInquiry.引き受け日時 || '—'}</dd>

              <dt>対応完了日時</dt>
              <dd>{selectedInquiry.対応完了日時 || '—'}</dd>

              <dt>関連する問題調査番号</dt>
              <dd>
                {selectedInquiry.関連する問題調査番号一覧.length > 0
                  ? selectedInquiry.関連する問題調査番号一覧.join('、')
                  : 'なし'}
              </dd>
            </dl>
          </section>
        </main>
      </div>
    )
  }

  // 一覧画面
  return (
    <div className="app">
      <header className="app-header">
        <h1>問い合わせ管理システム</h1>
        <span className="app-department">情報システム課</span>

        <div className="user-panel">
          {user && (
            <span>
              {user.氏名}（{user.職員番号}）
            </span>
          )}
          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
            disabled={loading}
          >
            ログアウト
          </button>
        </div>
      </header>

      <main className="main">
        <div className="list-header">
          <h2>問い合わせ一覧</h2>

          <span className="list-description">
            問い合わせを検索・確認できます。
          </span>

          {user?.所属 === '情報システム課' && (
            <button
              type="button"
              onClick={openNewInquiry}
              disabled={loading}
            >
              ＋ 新規登録
            </button>
          )}
        </div>

        {error && (
          <div className="modal-overlay">
            <section
              className="error-dialog"
              role="alertdialog"
              aria-modal="true"
              aria-labelledby="error-dialog-title"
              aria-describedby="error-dialog-message"
            >
              <h2 id="error-dialog-title">エラー</h2>

              <p id="error-dialog-message">
                {error}
              </p>

              <button
                type="button"
                onClick={() => setError('')}
                autoFocus
              >
                閉じる
              </button>
            </section>
          </div>
        )}

      
        <section className="search-section">
          <h3>検索条件</h3>

          <div className="initial-condition">
            <label>
              <input
                type="checkbox"
                checked={initialCondition}
                onChange={(event) =>
                  handleInitialConditionChange(event.target.checked)
                }
                disabled={loading}
              />
              初期条件
            </label>

            <span className="initial-condition-description">
              {initialCondition
                ? initialConditionDescription
                : '検索条件を指定して検索ボタンを押してください'}
            </span>
          </div>

          <fieldset
            className={`search-condition-fields ${
              initialCondition ? 'initial-condition-active' : ''
            }`}
            disabled={initialCondition || loading}
          >
            <div className="search-fields">
              <label className="search-subject">
                キーワード（件名）
                <input
                  type="text"
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                  placeholder="件名の一部を入力"
                />
              </label>

              <label className="search-category">
                問い合わせ分類
                <select
                  value={categoryFilter}
                  onChange={(event) => setCategoryFilter(event.target.value)}
                >
                  <option value="">すべて</option>
                  <option value="分類A">分類A</option>
                  <option value="分類B">分類B</option>
                  <option value="分類C">分類C</option>
                </select>
              </label>
              
              <label className="search-status">
                対応状態
                <select
                  value={statusFilter}
                  onChange={(event) => setStatusFilter(event.target.value)}
                >
                  <option value="">すべて</option>
                  <option value="引き受け待ち">引き受け待ち</option>
                  <option value="対応中">対応中</option>
                  <option value="対応完了">対応完了</option>
                </select>
              </label>

            </div>

            <button
              type="button"
              className="advanced-search-toggle"
              aria-expanded={showAdvancedSearch}
              onClick={() => setShowAdvancedSearch(!showAdvancedSearch)}
            >
              {showAdvancedSearch ? '▼' : '▶'} 詳細検索
            </button>

            {showAdvancedSearch && (
              <div className="advanced-search-fields">
                <label className="advanced-urgency">
                  緊急度
                  <select
                    value={urgencyFilter}
                    onChange={(event) => setUrgencyFilter(event.target.value)}
                  >
                    <option value="">すべて</option>
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                  </select>
                </label>

                <label className="advanced-receptionist">
                  受付担当者（職員番号）
                  <input
                    type="text"
                    value={receptionistFilter}
                    onChange={(event) =>
                      setReceptionistFilter(event.target.value)
                    }
                    placeholder="職員番号"
                  />
                </label>

                <label className="advanced-handler">
                  対応担当者（職員番号）
                  <input
                    type="text"
                    value={handlerFilter}
                    onChange={(event) => setHandlerFilter(event.target.value)}
                    placeholder="職員番号"
                  />
                </label>

                <label className="advanced-start-date">
                  受付日（開始）
                  <input
                    type="date"
                    value={receivedFrom}
                    onChange={(event) => setReceivedFrom(event.target.value)}
                  />
                </label>

                <label className="advanced-end-date">
                  受付日（終了）
                  <input
                    type="date"
                    value={receivedTo}
                    onChange={(event) => setReceivedTo(event.target.value)}
                  />
                </label>
              </div>
            )}
          </fieldset>

          <div className="search-buttons">
            <button
              type="button"
              onClick={handleSearch}
              disabled={initialCondition || loading}
            >
              {loading ? '検索中...' : '検索'}
            </button>

            <button
              type="button"
              className="clear-button"
              onClick={clearSearch}
              disabled={initialCondition || loading}
            >
              クリア
            </button>
          </div>
        </section>

          
        <section className="list-section">
          <div className="list-heading">
            <h3>問い合わせ一覧</h3>
            <p className="list-source">
              <strong>表示中の一覧：</strong>
              {listDescription}
            </p>
            <p className="list-count">
              表示中：{inquiries.length}件
              （全件数：{total}件、最大50件取得）
            </p>
          </div>

          <div className="bulk-toolbar">
            <span className="selected-count">
              選択中：{selectedNumbers.length}件
            </span>

            <div className="bulk-buttons">
              <button
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
                  既存の問題調査に関連付け
                </button>

                <button
                  type="button"
                  onClick={() => setIsCreateInvestigationDialogOpen(true)}
                  disabled={selectedNumbers.length === 0 || loading}
                >
                  新しい問題調査を作成・関連付け
                </button>
              </div>


              
              <button
                type="button"
                onClick={() => void handleBulkComplete()}
                disabled={selectedNumbers.length === 0 || loading}
              >
                {loading ? '処理中...' : '対応完了'}
              </button>

            </div>
          </div>

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

          <div className="pagination">
            <button
              type="button"
              onClick={async () => {
                const nextPage = currentPage - 1

                if (nextPage < 1 || loading) return

                setSelectedNumbers([])
                setActionMessage('')

                if (listDisplayMode === 'initial') {
                  await loadInquiries(nextPage)
                } else {
                  await fetchSearchResults(appliedFilters, nextPage)
                }
              }}
              disabled={currentPage <= 1 || loading}
            >
              前へ
            </button>

            <span>
              {currentPage} / {Math.max(1, Math.ceil(total / 50))} ページ
            </span>

            <button
              type="button"
              onClick={async () => {
                const nextPage = currentPage + 1
                const totalPages = Math.ceil(total / 50)

                if (nextPage > totalPages || loading) return

                setSelectedNumbers([])
                setActionMessage('')

                if (listDisplayMode === 'initial') {
                  await loadInquiries(nextPage)
                } else {
                  await fetchSearchResults(appliedFilters, nextPage)
                }
              }}
              disabled={
                currentPage >= Math.ceil(total / 50) || loading
              }
            >
              次へ
            </button>
          </div>
        </section>


      </main>
  
      {/* 既存の問題調査への関連付けダイアログ */}
      {isLinkInvestigationDialogOpen && (
        <div className="modal-overlay">
          <section
            className="input-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="link-investigation-title"
          >
            <h2 id="link-investigation-title">
              既存の問題調査に関連付け
            </h2>

            <label htmlFor="existing-investigation-number">
              問題調査番号
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

      {/* 新しい問題調査の作成・関連付けダイアログ */}
      {isCreateInvestigationDialogOpen && (
        <div className="modal-overlay">
          <section
            className="input-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-investigation-title"
          >
            <h2 id="create-investigation-title">
              新しい問題調査を作成・関連付け
            </h2>

            <label htmlFor="new-investigation-name">
              問題調査の名称・仮説（30文字以内）
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
    </div>
  )
}

export default App