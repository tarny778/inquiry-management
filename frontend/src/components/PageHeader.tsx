
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
        <span
          className={`page-section-icon ${
            section === '問い合わせ'
              ? 'inquiry-icon'
              : 'investigation-icon'
          }`}
          aria-hidden="true"
        >
          {section === '問い合わせ' ? (
            <svg viewBox="0 0 24 24" fill="none">
              <path
                d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-5 4v-4.5a2.5 2.5 0 0 1-1-2V5.5Z"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinejoin="round"
              />
              <path
                d="M8 8h8M8 11.5h5"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none">
              <circle
                cx="10.5"
                cy="10.5"
                r="6.5"
                stroke="currentColor"
                strokeWidth="1.8"
              />
              <path
                d="m15.5 15.5 5 5M8 10.5l1.7 1.7 3.3-3.5"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </span>

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
