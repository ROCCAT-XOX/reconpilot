import { describe, it, expect } from 'vitest'
import {
  formatDate,
  formatDateTime,
  formatDuration,
  severityColor,
  severityBg,
  statusColor,
} from '../utils/formatters'

describe('formatDate', () => {
  it('returns dash for null', () => {
    expect(formatDate(null)).toBe('—')
  })

  it('formats a valid date string', () => {
    const result = formatDate('2024-06-15T10:30:00Z')
    expect(result).toContain('2024')
  })
})

describe('formatDateTime', () => {
  it('returns dash for null', () => {
    expect(formatDateTime(null)).toBe('—')
  })

  it('formats a valid datetime string', () => {
    const result = formatDateTime('2024-06-15T10:30:00Z')
    expect(result).toContain('2024')
  })
})

describe('formatDuration', () => {
  it('returns dash for null', () => {
    expect(formatDuration(null)).toBe('—')
  })

  it('formats seconds', () => {
    expect(formatDuration(45)).toBe('45s')
  })

  it('formats minutes', () => {
    expect(formatDuration(125)).toBe('2m 5s')
  })

  it('formats hours', () => {
    expect(formatDuration(3665)).toBe('1h 1m')
  })
})

describe('severityColor', () => {
  it('returns correct color for critical', () => {
    expect(severityColor('critical')).toContain('red')
  })

  it('returns fallback for unknown', () => {
    expect(severityColor('unknown')).toContain('gray')
  })
})

describe('severityBg', () => {
  it('returns bg classes for high severity', () => {
    expect(severityBg('high')).toContain('orange')
  })
})

describe('statusColor', () => {
  it('returns green for running', () => {
    expect(statusColor('running')).toContain('green')
  })

  it('returns fallback for unknown status', () => {
    expect(statusColor('nonexistent')).toContain('gray')
  })
})
