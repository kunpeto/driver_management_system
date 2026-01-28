/**
 * 檢查使用者是否有特定角色
 */
export function hasRole(user, roles) {
  if (!user || !user.role) return false
  return roles.includes(user.role)
}

/**
 * 檢查使用者是否可以編輯特定部門的資料
 */
export function canEditDepartment(user, department) {
  if (!user) return false

  // Admin 可編輯所有部門
  if (user.role === 'admin') return true

  // Staff 只能編輯自己的部門
  if (user.role === 'staff') {
    return user.department === department
  }

  // Manager 無編輯權限
  return false
}

/**
 * 檢查使用者是否為 Admin
 */
export function isAdmin(user) {
  return user?.role === 'admin'
}

/**
 * 檢查使用者是否為 Staff
 */
export function isStaff(user) {
  return user?.role === 'staff'
}

/**
 * 檢查使用者是否為 Manager
 */
export function isManager(user) {
  return user?.role === 'manager'
}
