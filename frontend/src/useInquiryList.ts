
import { useState } from 'react'
import { ApiError } from './api/client'
import {
  getInitialInquiries,
  getSearchInquiries,
} from './api/inquiries'
import type {
  Inquiry,
  InquiryFilters,
} from './types'

// 一覧取得の結果
export type InquiryListResult =
  | { ok: true }
  | { ok: false; reason: 'unauthorized' }
  | { ok: false; reason: 'error'; error: unknown }

const emptyFilters: InquiryFilters = {
  keyword: '',
  status: '',
  category: '',
  urgency: '',
  receptionist: '',
  handler: '',
  receivedFrom: '',
  receivedTo: '',
}

export function useInquiryList() {
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
    useState<InquiryFilters>(emptyFilters)

  // 詳細検索欄の開閉状態
  const [showAdvancedSearch, setShowAdvancedSearch] =
    useState(false)

  // 取得した一覧の状態
  const [inquiries, setInquiries] = useState<Inquiry[]>([])
  const [total, setTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)

  // 現在表示している一覧の取得条件
  const [listDisplayMode, setListDisplayMode] =
    useState<'initial' | 'search'>('initial')

  // API取得失敗時の共通処理
  function handleFetchError(error: unknown): InquiryListResult {
    if (error instanceof ApiError && error.status === 401) {
      setInquiries([])
      setTotal(0)
      setCurrentPage(1)
      setListDisplayMode('initial')

      return { ok: false, reason: 'unauthorized' }
    }

    return { ok: false, reason: 'error', error }
  }

  // 取得に成功したときだけ一覧状態を更新する
  function applyListResult(
    result: {
      items: Inquiry[]
      total: number
      page: number
    },
    mode: 'initial' | 'search',
  ) {
    setInquiries(result.items)
    setTotal(result.total)
    setCurrentPage(result.page)
    setListDisplayMode(mode)
  }

  // 初期条件による一覧を取得する
  async function loadInitialInquiries(
    pageNumber = 1,
  ): Promise<InquiryListResult> {
    try {
      const result = await getInitialInquiries(pageNumber)

      applyListResult(result, 'initial')

      return { ok: true }
    } catch (error) {
      return handleFetchError(error)
    }
  }

  // 検索条件による一覧を取得する
  async function searchInquiries(
    filters: InquiryFilters,
    pageNumber = 1,
  ): Promise<InquiryListResult> {
    try {
      const result = await getSearchInquiries(
        filters,
        pageNumber,
      )

      setAppliedFilters(filters)
      applyListResult(result, 'search')

      return { ok: true }
    } catch (error) {
      return handleFetchError(error)
    }
  }

  // 現在表示している一覧を、同じ条件・同じページで再取得する
  async function refreshCurrentInquiryList():
    Promise<InquiryListResult> {
    if (listDisplayMode === 'initial') {
      return loadInitialInquiries(currentPage)
    }

    return searchInquiries(appliedFilters, currentPage)
  }

  // 指定したページを、現在の一覧条件で取得する
  async function goToPage(
    pageNumber: number,
  ): Promise<InquiryListResult> {
    const pageSize = 50
    const lastPage = Math.max(1, Math.ceil(total / pageSize))

    if (
      !Number.isInteger(pageNumber) ||
      pageNumber < 1 ||
      pageNumber > lastPage
    ) {
      return { ok: true }
    }

    if (listDisplayMode === 'initial') {
      return loadInitialInquiries(pageNumber)
    }

    return searchInquiries(appliedFilters, pageNumber)
  }

  // 一覧データをクリアする（認証切れなど）
  function clearInquiryList() {
    setInquiries([])
    setTotal(0)
    setCurrentPage(1)
    setListDisplayMode('initial')
  }

  // 現在ページを1ページ目に戻す
  function resetCurrentPage() {
    setCurrentPage(1)
  }

  // 検索条件をクリアする
  function clearSearchFilters() {
    setKeyword('')
    setStatusFilter('')
    setCategoryFilter('')
    setUrgencyFilter('')
    setReceptionistFilter('')
    setHandlerFilter('')
    setReceivedFrom('')
    setReceivedTo('')
    setAppliedFilters(emptyFilters)
  }

  return {
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
    clearInquiryList,
    resetCurrentPage,
    clearSearchFilters,

    // 一覧の状態
    inquiries,
    total,
    currentPage,
    listDisplayMode,

    // 一覧の取得・更新・ページ切り替え
    loadInitialInquiries,
    searchInquiries,
    refreshCurrentInquiryList,
    goToPage,
  }
}
