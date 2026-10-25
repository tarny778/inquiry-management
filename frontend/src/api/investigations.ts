import { apiRequest } from './client'
import type {
  InvestigationDetail,
  InvestigationListResponse,
  InvestigationFilters,
  InvestigationEditForm,
} from '../types'

// 検索条件に基づく問題調査一覧を取得する
export async function getSearchInvestigations(
  filters: InvestigationFilters,
  pageNumber = 1,
): Promise<InvestigationListResponse> {
  const params = new URLSearchParams({
    page: String(pageNumber),
    page_size: '50',
  })

  if (filters.investigationNumber.trim()) {
    params.set('問題調査番号', filters.investigationNumber.trim())
  }

  if (filters.inquiryNumber.trim()) {
    params.set('問い合わせ番号', filters.inquiryNumber.trim())
  }

  if (filters.requesterStaffNumber.trim()) {
    params.set('問い合わせ職員番号', filters.requesterStaffNumber.trim())
  }

  if (filters.handlerStaffNumber.trim()) {
    params.set('対応担当者職員番号', filters.handlerStaffNumber.trim())
  }

  if (filters.inquiryStatus) {
    params.set('問い合わせ状態', filters.inquiryStatus)
  }

  if (filters.investigationStatus) {
    params.set('問題調査状態', filters.investigationStatus)
  }

  if (filters.keyword.trim()) {
    params.set('問題調査の名称や仮説', filters.keyword.trim())
  }

  return apiRequest<InvestigationListResponse>(
    `/api/investigations?${params.toString()}`,
    { method: 'GET' },
    '問題調査の検索に失敗しました。',
  )
}

// 問題調査の詳細データを取得する
export async function getInvestigationDetail(
  investigationNumber: number,
): Promise<InvestigationDetail> {
  return apiRequest<InvestigationDetail>(
    `/api/investigations/${investigationNumber}`,
    { method: 'GET' },
    '問題調査の詳細取得に失敗しました。',
  )
}

// 問題調査を編集する
export async function updateInvestigation(
  investigationNumber: number,
  form: InvestigationEditForm,
): Promise<InvestigationDetail> {
  const payload = {
    ...form,
    対応案策定予定日時:
      form.対応案策定予定日時 || null,
    進捗更新の次回更新予定日時:
      form.進捗更新の次回更新予定日時 || null,
  }

  return apiRequest<InvestigationDetail>(
    `/api/investigations/${investigationNumber}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
    '問題調査の編集に失敗しました。',
  )
}

// 問題調査を断念する
export async function abandonInvestigation(
  investigationNumber: number,
): Promise<void> {
  await apiRequest<void>(
    `/api/investigations/${investigationNumber}/abandon`,
    { method: 'POST' },
    '問題調査の断念に失敗しました。',
  )
}

// 問題調査にリアクション要求する
export async function requestReactionInvestigation(
  investigationNumber: number,
): Promise<void> {
  await apiRequest<void>(
    `/api/investigations/${investigationNumber}/request-reaction`,
    { method: 'POST' },
    '問題調査のリアクション要求に失敗しました。',
  )
}