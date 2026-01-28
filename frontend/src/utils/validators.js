/**
 * 驗證員工編號格式：^\d{4}[A-Z]\d{4}$
 * 例如：1011M0095
 */
export function validateEmployeeId(employeeId) {
  const regex = /^\d{4}[A-Z]\d{4}$/
  return regex.test(employeeId)
}

/**
 * 從員工編號解析入職年月
 * 格式：1011M0095 → 2021-11
 */
export function parseHireYearMonth(employeeId) {
  if (!validateEmployeeId(employeeId)) {
    return null
  }

  const yearCode = employeeId.substring(0, 2) // "10"
  const monthCode = employeeId.substring(2, 4) // "11"

  // 年份從 2000 年開始計算
  const year = 2000 + parseInt(yearCode, 10)
  const month = monthCode.padStart(2, '0')

  return `${year}-${month}`
}

/**
 * 驗證 Email 格式
 */
export function validateEmail(email) {
  if (!email) return true // 選填欄位
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return regex.test(email)
}

/**
 * 驗證電話號碼（台灣格式）
 */
export function validatePhone(phone) {
  if (!phone) return true // 選填欄位
  // 允許格式：09xxxxxxxx 或 (02)xxxxxxxx 或 02-xxxxxxxx
  const regex = /^(09\d{8}|0\d{1,2}-?\d{6,8}|\(\d{2}\)\d{6,8})$/
  return regex.test(phone)
}

/**
 * 驗證密碼強度（至少 8 字元，包含英文與數字）
 */
export function validatePassword(password) {
  if (!password || password.length < 8) return false
  const hasLetter = /[a-zA-Z]/.test(password)
  const hasNumber = /\d/.test(password)
  return hasLetter && hasNumber
}
