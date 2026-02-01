<template>
  <div class="schedules-page">
    <h1 class="page-title">班表查詢</h1>

    <!-- 篩選區塊 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-item">
          <label>部門</label>
          <select v-model="filters.department">
            <option value="">全部</option>
            <option value="淡海">淡海</option>
            <option value="安坑">安坑</option>
          </select>
        </div>

        <div class="filter-item">
          <label>年份</label>
          <select v-model="filters.year">
            <option v-for="y in availableYears" :key="y" :value="y">
              {{ y }}
            </option>
          </select>
        </div>

        <div class="filter-item">
          <label>月份</label>
          <select v-model="filters.month">
            <option v-for="m in 12" :key="m" :value="m">
              {{ m }} 月
            </option>
          </select>
        </div>

        <div class="filter-item">
          <label>員工編號</label>
          <input
            v-model="filters.employeeId"
            type="text"
            placeholder="輸入員工編號"
          />
        </div>

        <div class="filter-actions">
          <button class="btn btn-primary" @click="search">
            查詢
          </button>
          <button class="btn btn-secondary" @click="resetFilters">
            重置
          </button>
        </div>
      </div>
    </div>

    <!-- 視圖切換 -->
    <div class="view-toggle">
      <button
        :class="['toggle-btn', { active: viewMode === 'table' }]"
        @click="viewMode = 'table'"
      >
        表格視圖
      </button>
      <button
        :class="['toggle-btn', { active: viewMode === 'calendar' }]"
        @click="viewMode = 'calendar'"
      >
        日曆視圖
      </button>
    </div>

    <!-- 統計區塊 -->
    <div v-if="statistics" class="statistics-section">
      <div class="stat-card">
        <div class="stat-value">{{ statistics.total_records }}</div>
        <div class="stat-label">總班表數</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ statistics.employee_count }}</div>
        <div class="stat-label">員工人數</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ statistics.r_shift_count }}</div>
        <div class="stat-label">R班出勤</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ statistics.overtime_count }}</div>
        <div class="stat-label">延長工時</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ statistics.leave_count }}</div>
        <div class="stat-label">休假數</div>
      </div>
    </div>

    <!-- 表格視圖 -->
    <div v-if="viewMode === 'table'" class="table-view">
      <div v-if="loading" class="loading">載入中...</div>

      <table v-else-if="schedules.length > 0" class="data-table">
        <thead>
          <tr>
            <th>日期</th>
            <th>員工編號</th>
            <th>姓名</th>
            <th>部門</th>
            <th>班別</th>
            <th>類型</th>
            <th>時間</th>
            <th>加班</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="schedule in schedules" :key="schedule.id">
            <td>{{ formatDate(schedule.schedule_date) }}</td>
            <td>{{ schedule.employee_id }}</td>
            <td>{{ schedule.employee_name || '-' }}</td>
            <td>
              <span :class="['dept-badge', schedule.department]">
                {{ schedule.department }}
              </span>
            </td>
            <td class="shift-code">{{ schedule.shift_code }}</td>
            <td>
              <span :class="['shift-type', getShiftTypeClass(schedule.shift_type)]">
                {{ schedule.shift_type || '-' }}
              </span>
            </td>
            <td>
              {{ schedule.start_time || '-' }}
              <span v-if="schedule.start_time && schedule.end_time"> ~ </span>
              {{ schedule.end_time || '' }}
            </td>
            <td>
              <span v-if="schedule.overtime_hours" class="overtime-badge">
                +{{ schedule.overtime_hours }}h
              </span>
              <span v-else>-</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-else class="no-data">
        沒有符合條件的班表資料
      </div>

      <!-- 分頁 -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          class="page-btn"
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
        >
          上一頁
        </button>
        <span class="page-info">
          第 {{ currentPage }} / {{ totalPages }} 頁
          (共 {{ total }} 筆)
        </span>
        <button
          class="page-btn"
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
        >
          下一頁
        </button>
      </div>
    </div>

    <!-- 日曆視圖 -->
    <div v-if="viewMode === 'calendar'" class="calendar-view">
      <div class="calendar-header">
        <button class="nav-btn" @click="navigateMonth(-1)">◀</button>
        <h2>{{ filters.year }} 年 {{ filters.month }} 月</h2>
        <button class="nav-btn" @click="navigateMonth(1)">▶</button>
      </div>

      <div class="calendar-grid">
        <!-- 星期標題 -->
        <div v-for="day in weekdays" :key="day" class="weekday-header">
          {{ day }}
        </div>

        <!-- 日期格子 -->
        <div
          v-for="(cell, index) in calendarCells"
          :key="index"
          :class="['calendar-cell', { 'other-month': !cell.currentMonth }]"
        >
          <div class="cell-date">{{ cell.day }}</div>
          <div v-if="cell.currentMonth" class="cell-schedules">
            <div
              v-for="(schedule, idx) in getSchedulesForDate(cell.date)"
              :key="idx"
              :class="['mini-schedule', getShiftTypeClass(schedule.shift_type)]"
              :title="`${schedule.employee_name || schedule.employee_id}: ${schedule.shift_code}`"
            >
              {{ schedule.employee_id?.slice(-4) }}: {{ schedule.shift_code?.slice(0, 5) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import api from '@/utils/api'

// 狀態
const loading = ref(false)
const schedules = ref([])
const statistics = ref(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)
const viewMode = ref('table')

// 篩選條件
const filters = ref({
  department: '',
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
  employeeId: ''
})

// 計算屬性
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

const weekdays = ['日', '一', '二', '三', '四', '五', '六']

const calendarCells = computed(() => {
  const year = filters.value.year
  const month = filters.value.month
  const firstDay = new Date(year, month - 1, 1)
  const lastDay = new Date(year, month, 0)
  const startDayOfWeek = firstDay.getDay()
  const daysInMonth = lastDay.getDate()

  const cells = []

  // 上個月的天數
  const prevMonthLastDay = new Date(year, month - 1, 0).getDate()
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    cells.push({
      day: prevMonthLastDay - i,
      currentMonth: false,
      date: null
    })
  }

  // 當月天數
  for (let day = 1; day <= daysInMonth; day++) {
    cells.push({
      day,
      currentMonth: true,
      date: `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    })
  }

  // 下個月補足
  const remaining = 42 - cells.length
  for (let i = 1; i <= remaining; i++) {
    cells.push({
      day: i,
      currentMonth: false,
      date: null
    })
  }

  return cells
})

// 方法
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const getShiftTypeClass = (shiftType) => {
  if (!shiftType) return ''
  switch (shiftType) {
    case '早班': return 'early'
    case '中班': return 'middle'
    case '晚班': return 'late'
    case 'R班': return 'r-shift'
    case '休假': return 'leave'
    default: return 'other'
  }
}

const getSchedulesForDate = (dateStr) => {
  if (!dateStr) return []
  return schedules.value.filter(s => s.schedule_date === dateStr).slice(0, 3)
}

const loadSchedules = async () => {
  loading.value = true

  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }

    if (filters.value.department) {
      params.department = filters.value.department
    }

    // 計算日期範圍
    const year = filters.value.year
    const month = filters.value.month
    params.start_date = `${year}-${String(month).padStart(2, '0')}-01`

    const nextMonth = month === 12 ? 1 : month + 1
    const nextYear = month === 12 ? year + 1 : year
    const lastDay = new Date(nextYear, nextMonth - 1, 0).getDate()
    params.end_date = `${year}-${String(month).padStart(2, '0')}-${lastDay}`

    if (filters.value.employeeId) {
      params.employee_id = filters.value.employeeId
    }

    const response = await api.get('/api/schedules', { params })
    schedules.value = response.data.items
    total.value = response.data.total

    // 載入統計資料
    await loadStatistics()
  } catch (error) {
    console.error('載入班表失敗:', error)
  } finally {
    loading.value = false
  }
}

const loadStatistics = async () => {
  if (!filters.value.department) {
    statistics.value = null
    return
  }

  try {
    const response = await api.get('/api/schedules/statistics', {
      params: {
        department: filters.value.department,
        year: filters.value.year,
        month: filters.value.month
      }
    })
    statistics.value = response.data
  } catch (error) {
    console.error('載入統計失敗:', error)
    statistics.value = null
  }
}

// Gemini Review Fix: 查詢時重置分頁
const search = () => {
  currentPage.value = 1
  loadSchedules()
}

const resetFilters = () => {
  filters.value = {
    department: '',
    year: new Date().getFullYear(),
    month: new Date().getMonth() + 1,
    employeeId: ''
  }
  currentPage.value = 1
  loadSchedules()
}

const changePage = (page) => {
  currentPage.value = page
  loadSchedules()
}

const navigateMonth = (delta) => {
  let newMonth = filters.value.month + delta
  let newYear = filters.value.year

  if (newMonth < 1) {
    newMonth = 12
    newYear--
  } else if (newMonth > 12) {
    newMonth = 1
    newYear++
  }

  filters.value.month = newMonth
  filters.value.year = newYear
  loadSchedules()
}

// 生命週期
onMounted(() => {
  loadSchedules()
})

// 監聽視圖模式變更
watch(viewMode, () => {
  if (viewMode.value === 'calendar') {
    // 日曆視圖需要載入更多資料
    pageSize.value = 500
    loadSchedules()
  } else {
    pageSize.value = 50
    loadSchedules()
  }
})
</script>

<style scoped>
.schedules-page {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  margin-bottom: 20px;
  color: var(--color-heading);
}

/* 篩選區塊 */
.filter-section {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-item label {
  font-size: 12px;
  color: var(--color-text-light);
}

.filter-item select,
.filter-item input {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-secondary {
  background: var(--color-background-soft);
  color: var(--color-text);
}

/* 視圖切換 */
.view-toggle {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.toggle-btn {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  border-radius: 4px;
  cursor: pointer;
}

.toggle-btn.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

/* 統計區塊 */
.statistics-section {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat-card {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px 24px;
  text-align: center;
  min-width: 100px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--color-primary);
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-light);
  margin-top: 4px;
}

/* 表格視圖 */
.data-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.data-table th {
  background: var(--color-background-soft);
  font-weight: 500;
}

.dept-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.dept-badge.淡海 {
  background: #e3f2fd;
  color: #1976d2;
}

.dept-badge.安坑 {
  background: #f3e5f5;
  color: #7b1fa2;
}

.shift-code {
  font-family: monospace;
  font-weight: 500;
}

.shift-type {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.shift-type.early { background: #fff3e0; color: #e65100; }
.shift-type.middle { background: #e8f5e9; color: #2e7d32; }
.shift-type.late { background: #e3f2fd; color: #1565c0; }
.shift-type.r-shift { background: #fce4ec; color: #c2185b; }
.shift-type.leave { background: #f5f5f5; color: #757575; }
.shift-type.other { background: #fff8e1; color: #ff8f00; }

.overtime-badge {
  background: #ffecb3;
  color: #ff6f00;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
}

/* 分頁 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid var(--color-border);
  background: var(--color-background);
  border-radius: 4px;
  cursor: pointer;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: var(--color-text-light);
  font-size: 14px;
}

/* 日曆視圖 */
.calendar-view {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 20px;
}

.calendar-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
}

.calendar-header h2 {
  font-size: 18px;
  margin: 0;
}

.nav-btn {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background: var(--color-border);
}

.weekday-header {
  padding: 10px;
  text-align: center;
  background: var(--color-background-soft);
  font-weight: 500;
}

.calendar-cell {
  min-height: 80px;
  padding: 8px;
  background: var(--color-background);
}

.calendar-cell.other-month {
  background: var(--color-background-soft);
  opacity: 0.5;
}

.cell-date {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
}

.cell-schedules {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mini-schedule {
  font-size: 10px;
  padding: 2px 4px;
  border-radius: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mini-schedule.early { background: #fff3e0; }
.mini-schedule.middle { background: #e8f5e9; }
.mini-schedule.late { background: #e3f2fd; }
.mini-schedule.r-shift { background: #fce4ec; }
.mini-schedule.leave { background: #f5f5f5; }

/* 其他 */
.loading,
.no-data {
  text-align: center;
  padding: 40px;
  color: var(--color-text-light);
}
</style>
