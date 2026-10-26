
import type { ReactNode } from 'react'

type PageHeaderProps = {
  section: '問い合わせ' | '問題調査'
  title: string
  actions?: ReactNode
}

export default function PageHeader({
  section,
  title,
  actions,
}: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-heading">
        <span className="page-section-label">
          {section}
        </span>
        <h2>{title}</h2>
      </div>

      {actions && (
        <div className="page-header-actions">
          {actions}
        </div>
      )}
    </div>
  )
}
