
import { useState } from 'react'

export default function useInvestigationList() {
  // 入力中の検索条件
  const [investigationNumber, setInvestigationNumber] = useState('')
  const [inquiryNumber, setInquiryNumber] = useState('')
  const [requesterStaffNumber, setRequesterStaffNumber] = useState('')
  const [handlerStaffNumber, setHandlerStaffNumber] = useState('')
  const [inquiryStatus, setInquiryStatus] = useState('')
  const [investigationStatus, setInvestigationStatus] = useState('')
  const [keyword, setKeyword] = useState('')

  // 最後に検索ボタンを押したときの条件
  const [appliedFilters, setAppliedFilters] = useState({
    investigationNumber: '',
    inquiryNumber: '',
    requesterStaffNumber: '',
    handlerStaffNumber: '',
    inquiryStatus: '',
    investigationStatus: '',
    keyword: '',
  })

  // 検索条件をクリアする
  const clearSearchFilters = () => {
    setInvestigationNumber('')
    setInquiryNumber('')
    setRequesterStaffNumber('')
    setHandlerStaffNumber('')
    setInquiryStatus('')
    setInvestigationStatus('')
    setKeyword('')

    setAppliedFilters({
      investigationNumber: '',
      inquiryNumber: '',
      requesterStaffNumber: '',
      handlerStaffNumber: '',
      inquiryStatus: '',
      investigationStatus: '',
      keyword: '',
    })
  }

  return {
    investigationNumber,
    setInvestigationNumber,
    inquiryNumber,
    setInquiryNumber,
    requesterStaffNumber,
    setRequesterStaffNumber,
    handlerStaffNumber,
    setHandlerStaffNumber,
    inquiryStatus,
    setInquiryStatus,
    investigationStatus,
    setInvestigationStatus,
    keyword,
    setKeyword,
    appliedFilters,
    setAppliedFilters,
    clearSearchFilters,
  }
}
