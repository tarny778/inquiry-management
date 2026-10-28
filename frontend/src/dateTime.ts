const TOKYO_TIME_ZONE = 'Asia/Tokyo'

export function localDateTimeToApi(value: string): string {
  if (!value) return value
  const withSeconds = value.length === 16 ? `${value}:00` : value
  return `${withSeconds}+09:00`
}

export function apiDateTimeToLocal(value: string | null | undefined): string {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''

  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: TOKYO_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date)
  const fields = Object.fromEntries(parts.map(({ type, value }) => [type, value]))

  return `${fields.year}-${fields.month}-${fields.day}T${fields.hour}:${fields.minute}:${fields.second}`
}

export function formatApiDateTimeInJapan(
  value: string | null | undefined,
): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '日時不明'

  return new Intl.DateTimeFormat('ja-JP', {
    timeZone: TOKYO_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
  }).format(date)
}
