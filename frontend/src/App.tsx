
import { useEffect, useState } from 'react'
import type { SubmitEvent } from 'react'
import './App.css'

// componentのインポート
import AppHeader from './components/AppHeader'
import PageHeader from './components/PageHeader'

import InquiryCreate  from './components/inquiries/InquiryCreate'
import InquiryUpdate  from './components/inquiries/InquiryUpdate'
import InquiryView  from './components/inquiries/InquiryView'
import InquiryListPage  from './components/inquiries/InquiryListPage'

import InvestigationSearch from './components/investigations/InvestigationSearch'
import InvestigationTable from './components/investigations/investigationTable'
import InvestigationDetailView from './components/investigations/InvestigationDetailView'
import InvestigationUpdate  from './components/investigations/InvestigationUpdate'

// typeのインポート
import type {
  LoginUser,
  InquiryDetail,
  ScreenMode,
  InquiryCreateForm,
  InquiryEditForm,
  Investigation,
  InvestigationFilters,
  InvestigationDetail,
  InvestigationEditForm,
} from './types'

// apiのインポート
import {
  checkSession,
  login,
  logout,
} from './api/auth'
import { ApiError } from './api/client'
import {
  getInquiryDetail,
  createNewInquiry,
  editInquiry,
  requestInquiryAccept,
  requestInquiryComplete,
  requestInquiryReopen,
  linkInvestigation,
  createInvestigation,
} from './api/inquiries'
import {
    getSearchInvestigations,
    getInvestigationDetail,
    updateInvestigation,
    abandonInvestigation,
    requestReactionInvestigation,
    abandonRelatedInvestigation,
    answerRelatedInquiryOk,
    answerRelatedInquiryNg,
  } from './api/investigations'

// カスタムフックのインポート
import { useInquiryList } from './useInquiryList'
import useInvestigationList  from './useInvestigationList'

// 共通関数のインポート
import { apiDateTimeToLocal } from './dateTime'


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

  // カスタムフックを宣言
  const inquiryList = useInquiryList()
  const {
    // 検索条件
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
    clearSearchFilters,

    // 一覧の状態
    inquiries,
    total,
    currentPage,
    listDisplayMode,

    // 一覧の取得・更新
    loadInitialInquiries,
    searchInquiries,
    refreshCurrentInquiryList: refreshInquiryList,
    goToPage,
    clearInquiryList,
    resetCurrentPage,
  } = inquiryList

  const listDescription = initialCondition
    ? initialConditionDescription
    : listDisplayMode === 'initial'
      ? '初期条件による結果（検索ボタンを押すと更新）'
      : '検索結果'

  const [error, setError] = useState('')
  const [loginError, setLoginError] = useState('')

  // 以下は調査画面用のstate
  // 問い合わせ画面と調査画面の切り替え
  const [mainScreen, setMainScreen] =
    useState<'inquiry' | 'investigation'>('inquiry')
  const [investigationScreenMode, setInvestigationScreenMode] =
    useState<'list' | 'view' | 'edit'>('list')
  const investigationList = useInvestigationList()
  const [investigations, setInvestigations] = useState<Investigation[]>([])
  const [investigationTotal, setInvestigationTotal] = useState(0)
  const [investigationCurrentPage, setInvestigationCurrentPage] = useState(1)
  const [investigationLoading,setInvestigationLoading] = useState(false)
  const [selectedInvestigation, setSelectedInvestigation] =
    useState<InvestigationDetail | null>(null)
  const [investigationEditForm, setInvestigationEditForm] =
    useState<InvestigationEditForm>({
      '調査の名称': '',
      '原因・仮説': '',
      '情シス側での対応': '',
      '問い合わせ者側で必要な対応': '',
      '対応案策定予定日時': '',
      '進捗更新の次回更新予定日時': '',
    })
  const [
    hasInitializedInvestigationList,
    setHasInitializedInvestigationList,
  ] = useState(false)


  
  // 現在表示している一覧を再取得する
  async function refreshCurrentInquiryList(): Promise<boolean> {
    const wasSearch = listDisplayMode === 'search'
    const result = await refreshInquiryList()

    if (result.ok) {
      if (wasSearch) {
        setError('')
        setSelectedNumbers([])
        setActionMessage('')
      }

      return true
    }

    if (result.reason === 'unauthorized') {
      setAuthenticated(false)
      setUser(null)

      if (wasSearch) {
        setSelectedNumbers([])
      }

      return false
    }

    if (wasSearch) {
      setError(
        result.error instanceof Error
          ? result.error.message
          : 'サーバーに接続できません。',
      )

      return false
    }

    // 初期条件による取得で発生したエラーは、
    // これまでどおり呼び出し元へ伝える
    throw result.error
  }


  
  // 初期条件による一覧を取得する
  async function loadInquiries(pageNumber = 1): Promise<boolean> {
    const result = await loadInitialInquiries(pageNumber)

    if (result.ok) {
      setAuthenticated(true)
      return true
    }

    if (result.reason === 'unauthorized') {
      setAuthenticated(false)
      setUser(null)
      return false
    }

    // 従来どおり、通常エラーは呼び出し元へ伝える
    throw result.error
  }

  
  
  // 検索条件に基づく一覧を取得し、画面状態へ反映する
  async function fetchSearchResults(
    filters: typeof appliedFilters,
    pageNumber = 1,
  ): Promise<boolean> {
    setError('')

    const result = await searchInquiries(filters, pageNumber)

    if (result.ok) {
      setSelectedNumbers([])
      setActionMessage('')
      return true
    }

    if (result.reason === 'unauthorized') {
      setAuthenticated(false)
      setUser(null)
      setSelectedNumbers([])
      return false
    }

    setError(
      result.error instanceof Error
        ? result.error.message
        : 'サーバーに接続できません。',
    )
    return false
  }

  async function handlePageChange(
    pageNumber: number,
  ): Promise<void> {
    if (loading) return

    setSelectedNumbers([])
    setActionMessage('')
    setLoading(true)

    try {
      const result = await goToPage(pageNumber)

      if (result.ok) {
        setError('')
        return
      }

      if (result.reason === 'unauthorized') {
        setAuthenticated(false)
        setUser(null)
        setSelectedNumbers([])
        return
      }

      setError(
        result.error instanceof Error
          ? result.error.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setLoading(false)
    }
  }


  
  // 検索ボタンが押された際に、検索条件をまとめて検索する
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

    setLoading(true)

    try {
      await fetchSearchResults(filters, 1)
    } finally {
      setLoading(false)
    }
  }


  

  // 問い合わせ番号で、問い合わせ詳細データを取得する
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
        clearInquiryList()
        setSelectedInquiry(null)
        return null
      }

      // その他のAPIエラー
      throw error
    }
  }

  // クリックされた時、問い合わせ詳細画面を開く
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

  // 問い合わせ一覧へ移動し、現在の表示条件で一覧を再取得する
  async function handleOpenInquiryList() {
    setError('')
    setMainScreen('inquiry')
    setSelectedNumbers([])
    setActionMessage('')
    setLoading(true)

    try {
      await refreshCurrentInquiryList()
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

  // 関連する問い合わせの詳細画面を開く
  async function openRelatedInquiry(
    inquiryNumber: number,
  ) {
    setError('')
    setLoading(true)

    try {
      const detail = await fetchInquiryDetail(inquiryNumber)

      if (detail === null) {
        return
      }

      setSelectedInquiry(detail)
      setSelectedInvestigation(null)
      setScreenMode('view')
      setMainScreen('inquiry')
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : '問い合わせ詳細の取得に失敗しました。',
      )
    } finally {
      setLoading(false)
    }
  }

  // 問い合わせ現状をフォームにセットし、編集画面を開く
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
        受信日時: apiDateTimeToLocal(selectedInquiry.受信日時),
      })

    setScreenMode('edit')
  }

  // 新規登録フォームを開く
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

  // 問い合わせを新規作成apiへ投げ、１ページ目へ戻り、作成した新規の詳細取得を呼ぶ
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
          clearInquiryList()
          setSelectedInquiry(null)
          setScreenMode('list')
          return
        }

        throw error
      }

      // 新規登録後は一覧の1ページ目に戻る
      resetCurrentPage()

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

  // 更新apiに投げ、編集した詳細取得を呼ぶ
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
          clearInquiryList()
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

  // 一括引き受けボタンにて、引き受けを呼ぶ
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

  // 個別引き受けボタンにて、引き受けを呼ぶ
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

  // ローディングにし、引き受けapiへ投げ、詳細取得と一覧取得を呼ぶ
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
          clearInquiryList()
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

  // 一括完了ボタンにて、完了を呼ぶ
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

  // 個別完了ボタンにて、完了を呼ぶ
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

  // ローディングし、完了apiに投げ、詳細取得と一覧取得を呼ぶ
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
          clearInquiryList()
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

  // 再開apiへ投げ、詳細取得を呼ぶ
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
          clearInquiryList()
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
      setActionMessage('問い合わせを再開しました。')
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

  // ローディング、既存関連付けapi投げ、一覧取得呼ぶ
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
      `選択した ${selectedNumbers.length} 件の問い合わせを、調査番号 ${investigationNumber} に関連付けますか？`,
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
          clearInquiryList()
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
      setActionMessage('問い合わせを既存の調査に関連付けました。')
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

  // ローディング、新規関連付けapiなげ、詳細取得
  async function handleBulkCreateInvestigation() {
    if (
      selectedNumbers.length === 0 ||
      loading ||
      !newInvestigationName.trim()
    ) {
      return
    }

    const confirmed = window.confirm(
      `選択した ${selectedNumbers.length} 件の問い合わせに、新しい調査「${newInvestigationName.trim()}」を作成して関連付けますか？`,
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
          clearInquiryList()
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
      setActionMessage('問い合わせを新規の調査に関連付けました。')
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

  // 初期条件ありにクリックにて、一覧取得を呼ぶ
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

  
  // ページを開いたとき、既存セッションがあれば職員情報と一覧を取得する。
  useEffect(() => {
    let cancelled = false

    async function checkExistingSession() {
      try {
        // セッションを確認し、ログイン職員情報を取得する。
        const user = await checkSession()

        if (cancelled) return

        setUser(user)
        setAuthenticated(true)

        // セッション確認後に問い合わせ一覧を取得する。
        const result = await loadInitialInquiries(1)

        if (cancelled) return

        if (!result.ok) {
          if (result.reason === 'unauthorized') {
            setAuthenticated(false)
            setUser(null)
            clearInquiryList()
            return
          }

          setError(
            result.error instanceof Error
              ? result.error.message
              : 'サーバーに接続できません。',
          )
        }
      } catch (err) {
        if (cancelled) return

        if (err instanceof ApiError && err.status === 401) {
          setAuthenticated(false)
          setUser(null)
          clearInquiryList()
          return
        }

        setError(
          err instanceof Error
            ? err.message
            : 'サーバーに接続できません。',
        )
      } finally {
        if (!cancelled) {
          setCheckingSession(false)
        }
      }
    }

    void checkExistingSession()

    return () => {
      cancelled = true
    }
  }, [])

  // 以下調査関連のファンクション
  // 検索条件とページ番号に基づき、一覧を再読み込み
  async function fetchInvestigationSearchResults(
    filters: InvestigationFilters,
    pageNumber = 1,
  ) {
    setError('')

    try {
      const result = await getSearchInvestigations(
        filters,
        pageNumber,
      )

      setInvestigations(result.items)
      setInvestigationTotal(result.total)
      setInvestigationCurrentPage(pageNumber)

      return true
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setInvestigations([])
        setInvestigationTotal(0)
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

  // 検索ボタンを押した時に、検索条件をセットし、一覧読み込みを呼ぶ
  async function handleSearchInvestigations() {
    const filters = {
      investigationNumber:
        investigationList.investigationNumber.trim(),
      inquiryNumber:
        investigationList.inquiryNumber.trim(),
      requesterStaffNumber:
        investigationList.requesterStaffNumber.trim(),
      handlerStaffNumber:
        investigationList.handlerStaffNumber.trim(),
      inquiryStatus:
        investigationList.inquiryStatus,
      investigationStatus:
        investigationList.investigationStatus,
      keyword:
        investigationList.keyword.trim(),
    }

    investigationList.setAppliedFilters(filters)
    setInvestigationLoading(true)

    try {
      await fetchInvestigationSearchResults(filters, 1)
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 検索条件をまっさらにするのみ
  function clearInvestigationSearch() {
    investigationList.clearSearchFilters()
    setInvestigations([])
    setInvestigationTotal(0)
    setInvestigationCurrentPage(1)
  }

  // 初期条件ボタン：確認後に初期条件を適用する
  async function handleApplyInitialInvestigationCondition() {
    if (!user) {
      return
    }

    const msgShozoku =
      user.所属 === '情報システム課'
        ? '対応担当者'
        : '問い合わせ者'

    const confirmed = window.confirm(
      `初期条件での検索として、${msgShozoku}が操作者本人で、` +
      '問い合わせ状態が「対応中」の問い合わせに関連する調査を検索しますか？',
    )

    if (!confirmed) {
      return
    }

    await applyInitialInvestigationCondition()
  }

  // 初期条件を設定して検索する（確認メッセージなし）
  async function applyInitialInvestigationCondition() {
    if (!user) {
      return
    }

    const isInformationSystems =
      user.所属 === '情報システム課'

    const filters = {
      investigationNumber: '',
      inquiryNumber: '',
      requesterStaffNumber: isInformationSystems
        ? ''
        : user.職員番号,
      handlerStaffNumber: isInformationSystems
        ? user.職員番号
        : '',
      inquiryStatus: '対応中',
      investigationStatus: '',
      keyword: '',
    }

    // 入力欄に初期条件を反映する
    investigationList.setInvestigationNumber('')
    investigationList.setInquiryNumber('')
    investigationList.setRequesterStaffNumber(
      filters.requesterStaffNumber,
    )
    investigationList.setHandlerStaffNumber(
      filters.handlerStaffNumber,
    )
    investigationList.setInquiryStatus(filters.inquiryStatus)
    investigationList.setInvestigationStatus('')
    investigationList.setKeyword('')

    // 検索条件を確定する
    investigationList.setAppliedFilters(filters)

    // 初期条件で1ページ目を検索する
    setInvestigationLoading(true)

    try {
      await fetchInvestigationSearchResults(filters, 1)
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 調査一覧のページを切り替える
  async function handleInvestigationPageChange(
    pageNumber: number,
  ) {
    const totalPages = Math.ceil(investigationTotal / 50)

    if (
      pageNumber < 1 ||
      pageNumber > totalPages ||
      investigationLoading
    ) {
      return
    }

    setInvestigationLoading(true)

    try {
      await fetchInvestigationSearchResults(
        investigationList.appliedFilters,
        pageNumber,
      )
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 調査の詳細を取得する
  async function handleSelectInvestigation(
    investigationNumber: number,
  ) {
    setError('')
    setInvestigationLoading(true)

    try {
      const result = await getInvestigationDetail(
        investigationNumber,
      )

      setSelectedInvestigation(result)
      setInvestigationScreenMode('view')
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setSelectedInvestigation(null)
        return
      }

      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 調査一覧へ移動する、初回かどうか判定し、現在の検索条件で調査を取得を呼ぶ
  async function handleOpenInvestigations() {
    setError('')
    setSelectedNumbers([])
    setActionMessage('')
    setMainScreen('investigation')

    // 初回だけ初期条件を適用する
    if (!hasInitializedInvestigationList) {
      setHasInitializedInvestigationList(true)
      await applyInitialInvestigationCondition()
      return
    }

    // 2回目以降は現在の検索条件で再取得する
    setInvestigationLoading(true)

    try {
      await fetchInvestigationSearchResults(
        investigationList.appliedFilters,
        investigationCurrentPage,
      )
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 関連する調査の詳細画面を開く、調査番号で調査を取得
  async function openRelatedInvestigation(
    investigationNumber: number,
  ) {
    setError('')
    setInvestigationLoading(true)

    try {
      const detail = await getInvestigationDetail(
        investigationNumber,
      )

      setSelectedInvestigation(detail)
      setSelectedInquiry(null)
      setInvestigationScreenMode('view')
      setMainScreen('investigation')
    } catch (err) {
      // セッション切れ
      if (err instanceof ApiError && err.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setSelectedInvestigation(null)
        setSelectedInquiry(null)
        return
      }

      // その他のAPIエラー
      setError(
        err instanceof Error
          ? err.message
          : '調査詳細の取得に失敗しました。',
      )
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 調査の内容を更新する
  const handleSaveInvestigation = async (
    event: SubmitEvent<HTMLFormElement>,
  ) => {
    event.preventDefault()

    if (selectedInvestigation === null) {
      setError('調査の詳細データがありません。')
      return
    }

    try {
      setInvestigationLoading(true)
      setError('')

      // ① 編集内容を API に送信する
      await updateInvestigation(
        selectedInvestigation.調査番号,
        investigationEditForm,
      )

      // ② 保存後の最新の詳細情報を取得する
      const updatedInvestigation = await getInvestigationDetail(
        selectedInvestigation.調査番号,
      )

      // ③ 詳細情報を更新する
      setSelectedInvestigation(updatedInvestigation)

      // ④ 詳細画面に戻る
      setInvestigationScreenMode('view')
    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : '調査の保存に失敗しました。',
      )
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 調査を断念する
  async function handleAbandonInvestigation(
    investigationNumber: number,
  ) {
    if (investigationLoading) {
      return
    }

    setError('')
    setInvestigationLoading(true)

    try {
      // 断念APIを呼び出す
      await abandonInvestigation(investigationNumber)

      // 断念後の詳細を再取得する
      const detail = await getInvestigationDetail(
        investigationNumber,
      )

      setSelectedInvestigation(detail)
    } catch (err) {
      // セッション切れ
      if (err instanceof ApiError && err.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setSelectedInvestigation(null)
        setInvestigationScreenMode('list')
        return
      }

      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 調査にリアクション要求する
  async function handleRequestReactionInvestigation(
    investigationNumber: number,
  ) {
    if (investigationLoading) {
      return
    }

    setError('')
    setInvestigationLoading(true)

    try {
      // リアクション要求APIを呼び出す
      await requestReactionInvestigation(investigationNumber)

      // 断念後の詳細を再取得する
      const detail = await getInvestigationDetail(
        investigationNumber,
      )

      setSelectedInvestigation(detail)
    } catch (err) {
      // セッション切れ
      if (err instanceof ApiError && err.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setSelectedInvestigation(null)
        setInvestigationScreenMode('list')
        return
      }

      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 問い合わせ調査を個別断念する
  async function handleAbandonRelatedInvestigation(
    relationNumber: number,
  ) {
    if (investigationLoading || !selectedInvestigation) {
      return
    }

    const confirmed = window.confirm(
      `問い合わせ調査番号 ${relationNumber} を個別断念しますか？`,
    )

    if (!confirmed) {
      return
    }

    setError('')
    setInvestigationLoading(true)

    try {
      // 個別断念APIを呼び出す
      await abandonRelatedInvestigation(relationNumber)

      // 詳細情報を再取得する
      // 関連一覧も最新状態になる
      const detail = await getInvestigationDetail(
        selectedInvestigation['調査番号'],
      )

      setSelectedInvestigation(detail)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setSelectedInvestigation(null)
        setInvestigationScreenMode('list')
        return
      }

      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setInvestigationLoading(false)
    }
  }


  // 問い合わせ調査にOKと回答する
  async function handleAnswerRelatedInquiryOk(
    relationId: number,
  ) {
    if (investigationLoading || !selectedInvestigation) {
      return
    }

    setError('')
    setInvestigationLoading(true)

    try {
      await answerRelatedInquiryOk(relationId)

      // 詳細情報を再取得する
      const detail = await getInvestigationDetail(
        selectedInvestigation['調査番号'],
      )

      setSelectedInvestigation(detail)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setSelectedInvestigation(null)
        setInvestigationScreenMode('list')
        return
      }

      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setInvestigationLoading(false)
    }
  }

  // 問い合わせ調査にNGと回答する
  async function handleAnswerRelatedInquiryNg(
    relationId: number,
  ) {
    if (investigationLoading || !selectedInvestigation) {
      return
    }

    setError('')
    setInvestigationLoading(true)

    try {
      await answerRelatedInquiryNg(relationId)

      // 詳細情報を再取得する
      const detail = await getInvestigationDetail(
        selectedInvestigation['調査番号'],
      )

      setSelectedInvestigation(detail)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setAuthenticated(false)
        setUser(null)
        setSelectedInvestigation(null)
        setInvestigationScreenMode('list')
        return
      }

      setError(
        err instanceof Error
          ? err.message
          : 'サーバーに接続できません。',
      )
    } finally {
      setInvestigationLoading(false)
    }
  }



  async function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoginError('')
    setError('')
    setLoading(true)

    try {
      const data = await login(職員番号, パスワード)

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
      await logout()

      setAuthenticated(false)
      setUser(null)
      clearInquiryList()
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
        <AppHeader />

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

            <button
  className="button-primary" type="submit" disabled={loading}>
              {loading ? 'ログイン中...' : 'ログイン'}
            </button>
          </form>
        </main>
      </div>
    )
  }
  // 調査関連画面
  if (mainScreen === 'investigation') {
    // 詳細画面
    if (investigationScreenMode === 'view') {
      if (selectedInvestigation === null) {
        return (
          <div>
            <p>調査の詳細データがありません。</p>
            <button
              className="button-secondary"
              type="button"
              onClick={() => setInvestigationScreenMode('list')}
            >
              ← 調査一覧へ戻る
            </button>
          </div>
        )
      }
      return (
        <div>
        <AppHeader
          user={user}
          onLogout={handleLogout}
          loading={loading || investigationLoading}
        />
        <InvestigationDetailView
          investigation={selectedInvestigation}
          user={user}
          loading={investigationLoading}
          onBack={async () => {
            setInvestigationLoading(true)

            try {
              await fetchInvestigationSearchResults(
                investigationList.appliedFilters,
                investigationCurrentPage,
              )
              setInvestigationScreenMode('list')
            } finally {
              setInvestigationLoading(false)
            }
          }}
          onEdit={() => {
            setInvestigationEditForm({
              '調査の名称':
                selectedInvestigation['調査の名称'],
              '原因・仮説':
                selectedInvestigation['原因・仮説'] ?? '',
              '情シス側での対応':
                selectedInvestigation['情シス側での対応'] ?? '',
              '問い合わせ者側で必要な対応':
                selectedInvestigation['問い合わせ者側で必要な対応'] ?? '',
              '対応案策定予定日時':
                apiDateTimeToLocal(selectedInvestigation['対応案策定予定日時']),
              '進捗更新の次回更新予定日時':
                apiDateTimeToLocal(selectedInvestigation['進捗更新の次回更新予定日時']),
            })

            setInvestigationScreenMode('edit')
          }}
          onAbandon={() =>
            handleAbandonInvestigation(
              selectedInvestigation['調査番号'],
            )
          }
          onRequestReaction={() =>
            handleRequestReactionInvestigation(
              selectedInvestigation['調査番号'],
            )
          }
          onAbandonRelated={(relationNumber) =>
            handleAbandonRelatedInvestigation(relationNumber)
          }
          onAnswerRelatedInquiryOk={(relationNumber) =>
            handleAnswerRelatedInquiryOk(relationNumber)
          }
          onAnswerRelatedInquiryNg={(relationNumber) =>
            handleAnswerRelatedInquiryNg(relationNumber)
          }
          onOpenInquiry={openRelatedInquiry}
          onOpenInvestigation={openRelatedInvestigation}
        />
        </div>
      )
    }

    // 編集画面を表示する
    if (investigationScreenMode === 'edit') {
      if (selectedInvestigation === null) {
        return (
          <div>
            <p>調査の詳細データがありません。</p>
            <button
              className="button-secondary"
              type="button"
              onClick={() => setInvestigationScreenMode('list')}
            >
              ← 調査一覧へ戻る
            </button>
          </div>
        )
      }
      return(
        <div>
        <AppHeader
          user={user}
          onLogout={handleLogout}
          loading={loading || investigationLoading}
        />
        <InvestigationUpdate
          investigation={selectedInvestigation}
          editForm={investigationEditForm}
          setEditForm={setInvestigationEditForm}
          onSubmit={handleSaveInvestigation}
          onCancel={() => setInvestigationScreenMode('view')}
          loading={investigationLoading}
          user={user}
        />
        </div>
      )
    }
    // 一覧画面
    return (
      <div className="app">
        <AppHeader
          user={user}
          onLogout={handleLogout}
          loading={loading || investigationLoading}
        />

        <main className="main">
          <PageHeader
            section="問題調査"
            title="調査一覧"
            actions={
              <button
                className="button-secondary"
                type="button"
                onClick={handleOpenInquiryList}
                disabled={investigationLoading}
              >
                ← 問い合わせ一覧へ
              </button>
            }
          />

          <InvestigationSearch
            loading={investigationLoading}
            investigationNumber={investigationList.investigationNumber}
            setInvestigationNumber={investigationList.setInvestigationNumber}
            inquiryNumber={investigationList.inquiryNumber}
            setInquiryNumber={investigationList.setInquiryNumber}
            requesterStaffNumber={investigationList.requesterStaffNumber}
            setRequesterStaffNumber={investigationList.setRequesterStaffNumber}
            handlerStaffNumber={investigationList.handlerStaffNumber}
            setHandlerStaffNumber={investigationList.setHandlerStaffNumber}
            inquiryStatus={investigationList.inquiryStatus}
            setInquiryStatus={investigationList.setInquiryStatus}
            investigationStatus={investigationList.investigationStatus}
            setInvestigationStatus={investigationList.setInvestigationStatus}
            keyword={investigationList.keyword}
            setKeyword={investigationList.setKeyword}
            handleSearch={handleSearchInvestigations}
            clearSearch={clearInvestigationSearch}
            onApplyInitialCondition={handleApplyInitialInvestigationCondition}
          />
          <InvestigationTable
            loading={investigationLoading}
            currentPage={investigationCurrentPage}
            total={investigationTotal}
            investigations={investigations}
            onPreviousPage={() =>
              void handleInvestigationPageChange(
                investigationCurrentPage - 1,
              )
            }
            onNextPage={() =>
              void handleInvestigationPageChange(
                investigationCurrentPage + 1,
              )
            }
            onSelectInvestigation={handleSelectInvestigation}
          />
        </main>
      </div>
    )
  }
  // 問い合わせ関連画面
  // 新規作成画面
  if (screenMode === 'new' && mainScreen ==='inquiry') {
    return (
      <div>
        <AppHeader
          user={user}
          onLogout={handleLogout}
          loading={loading || investigationLoading}
        />
      <InquiryCreate
        createForm={createForm}
        setCreateForm={setCreateForm}
        loading={loading}
        error={error}
        onSubmit={handleCreateInquiry}
        onCancel={() => setScreenMode('list')}
      />
      </div>
    )
  }

  // 編集画面
  if (screenMode === 'edit' && selectedInquiry !== null) {
    return (
      <div>
        <AppHeader
          user={user}
          onLogout={handleLogout}
          loading={loading || investigationLoading}
        />
      <InquiryUpdate
        editForm={editForm}
        setEditForm={setEditForm}
        loading={loading}
        error={error}
        onSubmit={handleUpdateInquiry}
        onCancel={() => setScreenMode('view')}
      />
      </div>
    )
  }

  // 詳細画面
  if (selectedInquiry !== null) {
    return (
      <div>
        <AppHeader
          user={user}
          onLogout={handleLogout}
          loading={loading || investigationLoading}
        />
      <InquiryView
        user={user}
        selectedInquiry={selectedInquiry}
        setSelectedInquiry={setSelectedInquiry}
        setScreenMode={setScreenMode}
        loading={loading}
        setLoading={setLoading}
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
        onOpenInvestigation={openRelatedInvestigation}
      />
      </div>
    )
  }

  // 一覧画面
  return (
    <div>
        <AppHeader
          user={user}
          onLogout={handleLogout}
          loading={loading || investigationLoading}
        />
    <InquiryListPage
      user={user}
      loading={loading}
      error={error}
      setError={setError}
      inquiries={inquiries}
      total={total}
      currentPage={currentPage}
      listDescription={listDescription}
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
      onOpenInvestigations={handleOpenInvestigations}
      handlePageChange={handlePageChange}
    />
    </div>
  )
}


export default App
