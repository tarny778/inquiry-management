
import { useEffect, useState } from 'react'
import './App.css'
import InquiryCreate  from './components/inquiries/InquiryCreate'
import InquiryUpdate  from './components/inquiries/InquiryUpdate'
import InquiryView  from './components/inquiries/InquiryView'
import InquiryList  from './components/inquiries/InquiryList'
import type {
  Inquiry,
  LoginUser,
  InquiryFilters,
  InquiryListResponse,
  InquiryDetail,
  ScreenMode,
  InquiryCreateForm,
  InquiryEditForm,
} from './types'

const API_BASE_URL = 'http://localhost:8000'


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
  const [appliedFilters, setAppliedFilters] =
  useState<InquiryFilters>({
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
    console.log(
      '編集対象の受信日時:',
      selectedInquiry.受信日時,
    )

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
        (selectedInquiry.受信日時 ?? '').split('.')[0],
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
      <InquiryCreate
        userName={user?.氏名}
        userNumber={user?.職員番号}
        createForm={createForm}
        setCreateForm={setCreateForm}
        loading={loading}
        error={error}
        onSubmit={handleCreateInquiry}
        onCancel={() => setScreenMode('list')}
        onLogout={handleLogout}
      />
    )
  }

  // 編集画面
  if (screenMode === 'edit' && selectedInquiry !== null) {
    return (
      <InquiryUpdate
        userName={user?.氏名}
        userNumber={user?.職員番号}
        editForm={editForm}
        setEditForm={setEditForm}
        loading={loading}
        error={error}
        onSubmit={handleUpdateInquiry}
        onCancel={() => setScreenMode('view')}
        onLogout={handleLogout}
      />
    )
  }

  // 詳細画面
  if (selectedInquiry !== null) {
    return (
      <InquiryView
        user={user}
        selectedInquiry={selectedInquiry}
        setSelectedInquiry={setSelectedInquiry}
        setScreenMode={setScreenMode}
        loading={loading}
        error={error}
        listDisplayMode={listDisplayMode}
        currentPage={currentPage}
        appliedFilters={appliedFilters}
        loadInquiries={loadInquiries}
        fetchSearchResults={fetchSearchResults}
        openInquiryEdit={openInquiryEdit}
        handleAcceptInquiry={handleAcceptInquiry}
        handleCompleteInquiry={handleCompleteInquiry}
        handleReopenInquiry={handleReopenInquiry}
        onLogout={handleLogout}
      />
    )
  }

  // 一覧画面
  return (
    <InquiryList
      user={user}
      loading={loading}
      error={error}
      setError={setError}
      inquiries={inquiries}
      total={total}
      currentPage={currentPage}
      listDisplayMode={listDisplayMode}
      listDescription={listDescription}
      appliedFilters={appliedFilters}
      loadInquiries={loadInquiries}
      fetchSearchResults={fetchSearchResults}
      handleLogout={handleLogout}
      openNewInquiry={openNewInquiry}
      openInquiryDetail={openInquiryDetail}
      handleInitialConditionChange={handleInitialConditionChange}
      initialCondition={initialCondition}
      initialConditionDescription={initialConditionDescription}
      keyword={keyword}
      setKeyword={setKeyword}
      categoryFilter={categoryFilter}
      setCategoryFilter={setCategoryFilter}
      statusFilter={statusFilter}
      setStatusFilter={setStatusFilter}
      urgencyFilter={urgencyFilter}
      setUrgencyFilter={setUrgencyFilter}
      receptionistFilter={receptionistFilter}
      setReceptionistFilter={setReceptionistFilter}
      handlerFilter={handlerFilter}
      setHandlerFilter={setHandlerFilter}
      receivedFrom={receivedFrom}
      setReceivedFrom={setReceivedFrom}
      receivedTo={receivedTo}
      setReceivedTo={setReceivedTo}
      showAdvancedSearch={showAdvancedSearch}
      setShowAdvancedSearch={setShowAdvancedSearch}
      handleSearch={handleSearch}
      clearSearch={clearSearch}
      selectedNumbers={selectedNumbers}
      setSelectedNumbers={setSelectedNumbers}
      actionMessage={actionMessage}
      setActionMessage={setActionMessage}
      handleBulkAccept={handleBulkAccept}
      handleBulkComplete={handleBulkComplete}
      handleBulkLinkInvestigation={handleBulkLinkInvestigation}
      handleBulkCreateInvestigation={handleBulkCreateInvestigation}
      isLinkInvestigationDialogOpen={isLinkInvestigationDialogOpen}
      setIsLinkInvestigationDialogOpen={setIsLinkInvestigationDialogOpen}
      isCreateInvestigationDialogOpen={isCreateInvestigationDialogOpen}
      setIsCreateInvestigationDialogOpen={setIsCreateInvestigationDialogOpen}
      existingInvestigationNumber={existingInvestigationNumber}
      setExistingInvestigationNumber={setExistingInvestigationNumber}
      newInvestigationName={newInvestigationName}
      setNewInvestigationName={setNewInvestigationName}
    />
  )
}

export default App