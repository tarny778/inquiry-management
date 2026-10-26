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
  関連する調査番号一覧: number[]
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

export type Investigation = {
  調査番号: number
  調査の名称: string
  調査状態: number
  対応担当者職員氏名: string | null
  関連問い合わせ件数: number
  自分の問い合わせを含む: boolean
}

export type InvestigationListResponse = {
  items: Investigation[]
  page: number
  page_size: number
  total: number
}

export type InvestigationRelatedInquiry = {
  "問い合わせ調査番号": number
  "問い合わせ番号": number
  "問い合わせ者氏名": string
  "対応担当者氏名": string
  "問い合わせ調査状態": number
  "調査開始日時": string | null
  "断念日時": string | null
  "リアクション被要求日時": string | null
  "リアクション日時": string | null
  "リアクション内容": string | null
  "NGでの移行先調査番号": number | null
  "問い合わせ職員番号": string
  "対応担当者職員番号": string | null
}

export type InvestigationDetail = {
  "調査番号": number
  "調査の名称": string
  "原因・仮説": string | null
  "情シス側での対応": string | null
  "問い合わせ者側で必要な対応": string | null
  "調査状態": number
  "調査開始日時": string | null
  "対応案策定予定日時": string | null
  "進捗更新の次回更新予定日時": string | null
  "リアクション要求日時": string | null
  "調査断念日時": string | null
  "最新移行先の調査番号": number
  "自分の問い合わせを含む": boolean
  "関連する問い合わせ調査": InvestigationRelatedInquiry[]
}

// 調査一覧の検索条件
export type InvestigationFilters = {
  investigationNumber: string
  inquiryNumber: string
  requesterStaffNumber: string
  handlerStaffNumber: string
  inquiryStatus: string
  investigationStatus: string
  keyword: string
}


export type InvestigationEditForm = {
  "調査の名称": string
  "原因・仮説": string
  "情シス側での対応": string
  "問い合わせ者側で必要な対応": string
  "対応案策定予定日時": string
  "進捗更新の次回更新予定日時": string
}
