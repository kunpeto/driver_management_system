/**
 * 前端單元測試範例
 *
 * 使用 Vitest 進行測試
 */

import { describe, it, expect, vi } from 'vitest'

describe('基礎測試', () => {
  it('應該正確執行', () => {
    expect(1 + 1).toBe(2)
  })

  it('字串測試', () => {
    const str = 'hello world'
    expect(str).toContain('world')
  })

  it('陣列測試', () => {
    const arr = [1, 2, 3]
    expect(arr).toHaveLength(3)
    expect(arr).toContain(2)
  })

  it('物件測試', () => {
    const obj = { name: '測試', value: 100 }
    expect(obj).toHaveProperty('name')
    expect(obj.value).toBeGreaterThan(50)
  })
})

describe('API 模擬測試', () => {
  it('應該正確模擬 fetch', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'test' })
    })

    global.fetch = mockFetch

    const response = await fetch('/api/test')
    const data = await response.json()

    expect(mockFetch).toHaveBeenCalled()
    expect(data).toEqual({ data: 'test' })
  })
})

describe('日期處理測試', () => {
  it('應該正確格式化日期', () => {
    const date = new Date('2026-01-15')
    const formatted = date.toISOString().split('T')[0]
    expect(formatted).toBe('2026-01-15')
  })

  it('應該正確計算季度', () => {
    const getQuarter = (month) => Math.ceil(month / 3)

    expect(getQuarter(1)).toBe(1)
    expect(getQuarter(3)).toBe(1)
    expect(getQuarter(4)).toBe(2)
    expect(getQuarter(7)).toBe(3)
    expect(getQuarter(10)).toBe(4)
    expect(getQuarter(12)).toBe(4)
  })
})

describe('驗證邏輯測試', () => {
  it('應該驗證員工編號格式', () => {
    const validateEmployeeId = (id) => {
      // 格式: YYMMX0XXX (如 1011M0095)
      const pattern = /^\d{4}[MF]0\d{3}$/
      return pattern.test(id)
    }

    expect(validateEmployeeId('1011M0095')).toBe(true)
    expect(validateEmployeeId('1140F0001')).toBe(true)
    expect(validateEmployeeId('invalid')).toBe(false)
    expect(validateEmployeeId('1011X0095')).toBe(false)
  })

  it('應該驗證密碼強度', () => {
    const validatePassword = (password) => {
      if (password.length < 8) return false
      if (!/[a-z]/.test(password)) return false
      if (!/[A-Z]/.test(password)) return false
      if (!/[0-9]/.test(password)) return false
      return true
    }

    expect(validatePassword('Abc12345')).toBe(true)
    expect(validatePassword('abc12345')).toBe(false) // 無大寫
    expect(validatePassword('ABCD1234')).toBe(false) // 無小寫
    expect(validatePassword('Abcdefgh')).toBe(false) // 無數字
    expect(validatePassword('Ab1')).toBe(false) // 太短
  })
})

describe('考核分數計算測試', () => {
  it('應該正確計算累計加重倍率', () => {
    const getCumulativeMultiplier = (count) => {
      if (count <= 1) return 1.0
      if (count === 2) return 1.5
      if (count === 3) return 2.0
      return 2.5
    }

    expect(getCumulativeMultiplier(1)).toBe(1.0)
    expect(getCumulativeMultiplier(2)).toBe(1.5)
    expect(getCumulativeMultiplier(3)).toBe(2.0)
    expect(getCumulativeMultiplier(4)).toBe(2.5)
    expect(getCumulativeMultiplier(10)).toBe(2.5)
  })

  it('應該正確計算責任係數', () => {
    const getResponsibilityCoefficient = (faultCount) => {
      if (faultCount <= 2) return 0.3 // 次要責任
      if (faultCount <= 5) return 0.7 // 主要責任
      return 1.0 // 完全責任
    }

    expect(getResponsibilityCoefficient(0)).toBe(0.3)
    expect(getResponsibilityCoefficient(2)).toBe(0.3)
    expect(getResponsibilityCoefficient(3)).toBe(0.7)
    expect(getResponsibilityCoefficient(5)).toBe(0.7)
    expect(getResponsibilityCoefficient(6)).toBe(1.0)
    expect(getResponsibilityCoefficient(9)).toBe(1.0)
  })

  it('應該正確計算最終扣分', () => {
    const calculateFinalPoints = (basePoints, responsibilityCoef, cumulativeMultiplier) => {
      return basePoints * responsibilityCoef * cumulativeMultiplier
    }

    // 第一次 R04 違規，4 項疏失（主要責任）
    expect(calculateFinalPoints(-3.0, 0.7, 1.0)).toBe(-2.1)

    // 第三次 R04 違規，6 項疏失（完全責任）
    expect(calculateFinalPoints(-3.0, 1.0, 2.0)).toBe(-6.0)
  })
})

describe('月度獎勵判定測試', () => {
  it('應該正確判定 +M02 資格', () => {
    const isEligibleForM02 = (categories) => {
      // +M02: R+S 類無扣分
      return !categories.some(cat => cat === 'R' || cat === 'S')
    }

    expect(isEligibleForM02([])).toBe(true)
    expect(isEligibleForM02(['D'])).toBe(true)
    expect(isEligibleForM02(['D', 'W'])).toBe(true)
    expect(isEligibleForM02(['R'])).toBe(false)
    expect(isEligibleForM02(['S'])).toBe(false)
    expect(isEligibleForM02(['D', 'R'])).toBe(false)
  })

  it('應該正確判定 +M03 資格', () => {
    const isEligibleForM03 = (categories) => {
      // +M03: 所有類別無扣分
      return categories.length === 0
    }

    expect(isEligibleForM03([])).toBe(true)
    expect(isEligibleForM03(['D'])).toBe(false)
    expect(isEligibleForM03(['R', 'S'])).toBe(false)
  })

  it('應該正確計算月度獎勵總分', () => {
    const calculateMonthlyReward = (hasFullAttendance, categories) => {
      let total = 0

      // +M01 全勤
      if (hasFullAttendance) total += 3

      // +M02 行車零違規
      if (!categories.some(cat => cat === 'R' || cat === 'S')) total += 1

      // +M03 全項目零違規
      if (categories.length === 0) total += 2

      return total
    }

    // 全勤 + 無任何扣分
    expect(calculateMonthlyReward(true, [])).toBe(6) // +M01(3) + +M02(1) + +M03(2)

    // 全勤 + 只有 D 類扣分
    expect(calculateMonthlyReward(true, ['D'])).toBe(4) // +M01(3) + +M02(1)

    // 全勤 + 有 R 類扣分
    expect(calculateMonthlyReward(true, ['R'])).toBe(3) // +M01(3) only

    // 無全勤 + 無任何扣分
    expect(calculateMonthlyReward(false, [])).toBe(3) // +M02(1) + +M03(2)
  })
})
