
import { apiRequest } from './client'
import type {
  InquiryDetail,
  InquiryFilters,
  InquiryListResponse,
  InquiryCreateForm,
  InquiryEditForm,
} from '../types'

// 初期表示用の問い合わせ一覧を取得する
export async function getInitialInquiries(
  pageNumber = 1,
): Promise<InquiryListResponse> {
  const params = new URLSearchParams({
    初期条件: '1',
    page: String(pageNumber),
    page_size: '50',
  })

  return apiRequest<InquiryListResponse>(
    `/api/inquiries?${params.toString()}`,
    { method: 'GET' },
    '問い合わせ一覧の取得に失敗しました。',
  )
}

// 検索条件に基づく問い合わせ一覧を取得する
export async function getSearchInquiries(
  filters: InquiryFilters,
  pageNumber = 1,
): Promise<InquiryListResponse> {
  
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

  return apiRequest<InquiryListResponse>(
    `/api/inquiries?${params.toString()}`,
    { method: 'GET' },
    '問い合わせの検索に失敗しました。',
  )
}

// 問い合わせ詳細データを取得する
export async function getInquiryDetail(
  inquiryNumber: number,
): Promise<InquiryDetail> {
  return apiRequest<InquiryDetail>(
    `/api/inquiries/${inquiryNumber}`,
    { method: 'GET' },
    '問い合わせ詳細の取得に失敗しました。',
  )
}

// 新規に問い合わせを作成する
export async function createNewInquiry(
  createForm: InquiryCreateForm,
): Promise<number>{
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

  const result = await apiRequest<{ 問い合わせ番号: number }>(
    '/api/inquiries',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
    '問い合わせの新規作成に失敗しました。',
  )
  return result.問い合わせ番号
}

// 問い合わせを編集する
export async function editInquiry(
  inquiryNumber: number,
  editForm: InquiryEditForm,
): Promise<number>{
  const payload: Record<string, unknown> = {
    問い合わせ職員番号: editForm.問い合わせ職員番号.trim(),
      受付経路: editForm.受付経路,
      問い合わせ分類: editForm.問い合わせ分類,
      件名: editForm.件名.trim(),
      緊急度: Number(editForm.緊急度),
      受付時の処理: Number(editForm.受付時の処理),
      問い合わせ詳細: editForm.問い合わせ詳細.trim() || null,
      受信日時: editForm.受信日時,
  }

  const result = await apiRequest<{ 問い合わせ番号: number }>(
    `/api/inquiries/${inquiryNumber}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
    '問い合わせの編集に失敗しました。',
  )
  return result.問い合わせ番号
}

// 問い合わせを引き受ける
export async function requestInquiryAccept(
  inquiryNumbers: number[],
): Promise<void> {
  await apiRequest<void>(
    '/api/inquiries/bulk-accept',
    {
      method: 'POST' ,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        問い合わせ番号一覧: inquiryNumbers,
      }),
    },
    '問い合わせの引き受けに失敗しました。',
  )
}

// 問い合わせを完了する
export async function requestInquiryComplete(
  inquiryNumbers: number[],
): Promise<void> {
  await apiRequest<void>(
    '/api/inquiries/bulk-complete',
    {
      method: 'POST' ,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        問い合わせ番号一覧: inquiryNumbers,
      }),
    },
    '問い合わせの完了に失敗しました。',
  )
}

// 問い合わせを再開する
export async function requestInquiryReopen(
  inquiryNumber: number,
): Promise<void> {
  await apiRequest<void>(
    `/api/inquiries/${inquiryNumber}/reopen`,
    {
      method: 'POST' ,
    },
    '問い合わせの再開に失敗しました。',
  )
}

// 問い合わせを既存の問題調査に関連付ける
export async function linkInvestigation(
  selectedNumbers: number[],
  investigationNumber: number,
): Promise<void> {
  await apiRequest<void>(
    '/api/inquiries/bulk-link-investigation',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        問い合わせ番号一覧: selectedNumbers,
        問題調査番号: investigationNumber,
      }),
    },
    "既存の問題調査への関連付けに失敗しました"
  )
}

// 問い合わせを新規の問題調査に関連付ける
export async function createInvestigation(
  selectedNumbers: number[],
  newInvestigationName: string,
): Promise<void> {
  await apiRequest<void>(
    '/api/inquiries/bulk-investigations',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        問い合わせ番号一覧: selectedNumbers,
        問題調査の名称や仮説: newInvestigationName.trim(),
      }),
    },
    "新規の問題調査への関連付けに失敗しました"
  )
}