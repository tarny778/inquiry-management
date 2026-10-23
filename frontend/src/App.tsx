
import { useEffect, useState } from 'react'
import './App.css'
import InquiryCreate  from './components/inquiries/InquiryCreate'
import InquiryUpdate  from './components/inquiries/InquiryUpdate'
import InquiryView  from './components/inquiries/InquiryView'
import InquiryListPage  from './components/inquiries/InquiryListPage'
import { useInquiryList } from './useInquiryList'
import {
  getInitialInquiries,
  getSearchInquiries,
  getInquiryDetail,
  createNewInquiry,
  editInquiry,
  requestInquiryAccept,
  requestInquiryComplete,
  requestInquiryReopen,
  linkInvestigation,
  createInvestigation,
} from './api/inquiries'
import { ApiError } from './api/client'
import type {
  Inquiry,
  LoginUser,
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

  const [isLinkInvestigationDialogOpen, setIsLinkInvestigationDialogOpen] =
  useState(false)
  const [isCreateInvestigationDialogOpen, setIsCreateInvestigationDialogOpen] =
  useState(false)
  const [existingInvestigationNumber, setExistingInvestigationNumber] =
  useState('')
  const [newInvestigationName, setNewInvestigationName] = useState('')

  // 入力中の検索条件
  const {
    keyword,
    setKeyword,
    statusFilter,
    setStatusFilter,
    categoryFilter,
    setCategoryFilter,
    urgencyFilter,
    setUrgencyFilter,
    receptionistFilter,
    setReceptionistFilter,
    handlerFilter,
    setHandlerFilter,
    receivedFrom,
    setReceivedFrom,
    receivedTo,
    setReceivedTo,
    showAdvancedSearch,
    setShowAdvancedSearch,
    appliedFilters,
    setAppliedFilters,
    clearSearchFilters,
  } = useInquiryList()

  const [error, setError] = useState('')
  const [loginError, setLoginError] = useState('')

  async function refreshCurrentInquiryList(): Promise<boolean> {
    if (listDisplayMode === 'initial') {
      return await loadInquiries(currentPage)
    }

    return await fetchSearchResults(
      appliedFilters,
      currentPage,
    )
  }

  
  // 初期表示では、APIが職員の権限に応じて抽出した一覧を取得する。
  async function loadInquiries(pageNumber = 1) {
    try {
      const result = await getInitialInquiries(pageNumber)

      setInquiries(result.items)
      setTotal(result.total)
      setCurrentPage(pageNumber)
      setListDisplayMode('initial')
      setAuthenticated(true)

      return true
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        return false
      }

      throw error
    }
  }
  
  // 検索条件に基づく検索一覧を取得し画面状態へ反映させる。
  async function fetchSearchResults(
    filters: typeof appliedFilters,
    pageNumber = 1,
  ) {
    setError('')

    try {
      const result = await getSearchInquiries(filters, pageNumber)

      setInquiries(result.items)
      setTotal(result.total)
      setCurrentPage(pageNumber)
      setListDisplayMode('search')
      setSelectedNumbers([])
      setActionMessage('')

      return true
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedNumbers([])
        return false
      }

      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
      return false
    }
  }

  async function handleSearch() {
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
    setLoading(true)

    try {
      await fetchSearchResults(filters, 1)
    } finally {
      setLoading(false)
    }
  }

  // 問い合わせ詳細データを取得する
  async function fetchInquiryDetail(
    inquiryNumber: number,
  ): Promise<InquiryDetail | null> {
    try {
      return await getInquiryDetail(inquiryNumber)
    } catch (error) {
      // セッション切れ
      if (error instanceof ApiError && error.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInquiries([])
        setTotal(0)
        setSelectedInquiry(null)
        return null
      }

      // その他のAPIエラー
      throw error
    }
  }

  // 問い合わせ詳細画面を開く
  async function openInquiryDetail(
    inquiryNumber: number
  ): Promise<boolean> {
    setError('')
    setLoading(true)

    try {
      const detail = await fetchInquiryDetail(inquiryNumber)

      // セッション切れなどで取得できなかった場合
      if (detail === null) {
        return false
      }

      setSelectedInquiry(detail)
      setScreenMode('view')
      return true

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。'
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

  // 問い合わせを新規作成し、画面へ反映
  async function handleCreateInquiry(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (loading) return

    setError('')
    setLoading(true)

    try {
      let inquiryNumber: number

      try {
        inquiryNumber = await createNewInquiry(createForm)
      } catch (error) {
        // セッション切れ
        if (error instanceof ApiError && error.status === 401) {
          setAuthenticated(false)
          setUser(null)
          setInquiries([])
          setTotal(0)
          setSelectedInquiry(null)
          setScreenMode('list')
          return
        }

        throw error
      }

      // 新規登録後は一覧の1ページ目に戻る
      setCurrentPage(1)

      // 登録した問い合わせの詳細を取得する
      setScreenMode('view')
      const inquiryDetail = await fetchInquiryDetail(
        inquiryNumber,
      )

      if (inquiryDetail === null) {
        return
      }

      setSelectedInquiry(inquiryDetail)
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
      let inquiryNumber: number

      try {
        inquiryNumber = await editInquiry(
          selectedInquiry.問い合わせ番号,
          editForm,
        )
      } catch (error) {
        // セッション切れ
        if (error instanceof ApiError && error.status === 401) {
          setAuthenticated(false)
          setUser(null)
          setInquiries([])
          setTotal(0)
          setSelectedInquiry(null)
          setScreenMode('list')
          return
        }

        throw error
      }

      // 編集した問い合わせの詳細を取得する
      setScreenMode('view')
      const inquiryDetail = await fetchInquiryDetail(
        inquiryNumber,
      )

      if (inquiryDetail === null) {
        return
      }

      // 編集した問い合わせをそのまま詳細画面に表示する
      setSelectedInquiry(inquiryDetail)
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

    try {
      try {
        await requestInquiryAccept(
          inquiryNumbers,
        )
      } catch (error) {
        // セッション切れ
        if (error instanceof ApiError && error.status === 401) {
          setAuthenticated(false)
          setUser(null)
          setInquiries([])
          setTotal(0)
          setSelectedNumbers([])
          setSelectedInquiry(null)
          setScreenMode('list')
          return
        }

        throw error
      }

      // 詳細画面からの単一引き受け
      if (returnToDetail) {
        // 引き受け後の詳細を再取得する
        const detail = await fetchInquiryDetail(inquiryNumbers[0])

        if (detail === null) {
          setError(
            '引き受けは完了しましたが、問い合わせ詳細の再取得に失敗しました。',
          )
          return
        }

        setSelectedInquiry(detail)
      }

      const refreshed = await refreshCurrentInquiryList()

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
      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
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

    try {
      try {
        await requestInquiryComplete(
          inquiryNumbers,
        )
      } catch (error) {
        // セッション切れ
        if (error instanceof ApiError && error.status === 401) {
          setAuthenticated(false)
          setUser(null)
          setInquiries([])
          setTotal(0)
          setSelectedNumbers([])
          setSelectedInquiry(null)
          setScreenMode('list')
          return
        }

        throw error
      }

      // 詳細画面からの単一引き受け
      if (returnToDetail) {
        // 完了後の詳細を再取得する
        const detail = await fetchInquiryDetail(inquiryNumbers[0])

        if (detail === null) {
          setError(
            '完了はできましたが、問い合わせ詳細の再取得に失敗しました。',
          )
          return
        }

        setSelectedInquiry(detail)
      }

      const refreshed = await refreshCurrentInquiryList()

      if (!refreshed) {
        setActionMessage(
          '完了はできましたが、一覧の再取得に失敗しました。必要に応じて一覧を再読み込みしてください。',
        )
        return
      }

      setSelectedNumbers([])
      setActionMessage(
        inquiryNumbers.length === 1
          ? '問い合わせを完了しました。'
          : '選択した問い合わせを完了しました。',
      )
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

    try {
      try {
        await requestInquiryReopen(
          inquiryNumber,
        )
      } catch (error) {
        // セッション切れ
        if (error instanceof ApiError && error.status === 401) {
          setAuthenticated(false)
          setUser(null)
          setInquiries([])
          setTotal(0)
          setSelectedNumbers([])
          setSelectedInquiry(null)
          setScreenMode('list')
          return
        }

        throw error
      }

      const detail = await fetchInquiryDetail(inquiryNumber)

      if (detail === null) {
        setError(
          '再開できましたが、問い合わせ詳細の再取得に失敗しました。',
        )
        return
      }

      setSelectedInquiry(detail)

      const refreshed = await refreshCurrentInquiryList()

      if (!refreshed) {
        setActionMessage(
          '再開できましたが、一覧の再取得に失敗しました。必要に応じて一覧を再読み込みしてください。',
        )
        return
      }

      setSelectedNumbers([])
      setActionMessage('問い合わせを完了しました。')
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

    try {
      try {
        await linkInvestigation(
          selectedNumbers,
          investigationNumber,
        )
      } catch (error) {
        // セッション切れ
        if (error instanceof ApiError && error.status === 401) {
          setAuthenticated(false)
          setUser(null)
          setInquiries([])
          setTotal(0)
          setSelectedNumbers([])
          setSelectedInquiry(null)
          setScreenMode('list')
          return
        }

        throw error
      }

      const refreshed = await refreshCurrentInquiryList()

      if (!refreshed) {
        setActionMessage(
          '関連付けはできましたが、一覧の再取得に失敗しました。必要に応じて一覧を再読み込みしてください。',
        )
        return
      }

      setSelectedNumbers([])
      setActionMessage('問い合わせを既存の問題調査に関連付けました。')
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

    try {
      try {
        await createInvestigation(
          selectedNumbers,
          newInvestigationName,
        )
      } catch (error) {
        // セッション切れ
        if (error instanceof ApiError && error.status === 401) {
          setAuthenticated(false)
          setUser(null)
          setInquiries([])
          setTotal(0)
          setSelectedNumbers([])
          setSelectedInquiry(null)
          setScreenMode('list')
          return
        }

        throw error
      }

      const refreshed = await refreshCurrentInquiryList()

      if (!refreshed) {
        setActionMessage(
          '関連付けはできましたが、一覧の再取得に失敗しました。必要に応じて一覧を再読み込みしてください。',
        )
        return
      }

      setSelectedNumbers([])
      setActionMessage('問い合わせを新規の問題調査に関連付けました。')
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
      // 検索条件をすべてクリア
      clearSearchFilters()

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
    clearSearchFilters()

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
        refreshCurrentInquiryList={refreshCurrentInquiryList}
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
    <InquiryListPage
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