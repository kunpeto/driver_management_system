/**
 * 部門常數定義
 * 集中管理部門名稱，確保前後端一致性
 */

export const DEPARTMENTS = {
  DANHAI: '淡海',
  ANKENG: '安坑'
}

export const DEPARTMENT_LIST = [
  { value: DEPARTMENTS.DANHAI, label: '淡海' },
  { value: DEPARTMENTS.ANKENG, label: '安坑' }
]

export const DEPARTMENT_OPTIONS = [
  { value: null, label: '全部部門' },
  ...DEPARTMENT_LIST
]

export default DEPARTMENTS
