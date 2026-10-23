
import { useState } from 'react'
import type { InquiryFilters } from './types'

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

  // 詳細検索欄の開閉状態
  const [showAdvancedSearch, setShowAdvancedSearch] = useState(false)

  const clearSearchFilters = () => {
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
  }

  return {
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
  }
}
