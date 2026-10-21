export type Inquiry = {
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

export type LoginUser = {
  職員番号: string
  氏名: string
  所属: string
}

export type InquiryListResponse = {
  items: Inquiry[]
  page: number
  page_size: number
  total: number
}

export type InquiryDetail = {
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

export type ScreenMode = 'list' | 'new' | 'view' | 'edit'

export type InquiryCreateForm = {
  問い合わせ職員番号: string
  受付経路: string
  問い合わせ分類: string
  件名: string
  緊急度: string
  受付時の処理: string
  問い合わせ詳細: string
  受信日時: string
}


export type InquiryEditForm = {
  問い合わせ職員番号: string
  受付経路: string
  問い合わせ分類: string
  件名: string
  緊急度: string
  受付時の処理: string
  問い合わせ詳細: string
  受信日時: string
}

export type InquiryFilters = {
  keyword: string
  status: string
  category: string
  urgency: string
  receptionist: string
  handler: string
  receivedFrom: string
  receivedTo: string
}