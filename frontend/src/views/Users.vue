<template>
  <div class="users-page">
    <!-- 頁面標題 -->
    <PageHeader title="使用者管理" subtitle="管理系統使用者帳號">
      <template #actions>
        <AppButton type="primary" @click="showCreateDialog = true">
          新增使用者
        </AppButton>
      </template>
    </PageHeader>

    <!-- 篩選區塊 -->
    <div class="filter-section">
      <div class="filter-row">
        <!-- 角色篩選 -->
        <div class="filter-item">
          <select v-model="selectedRole" class="filter-select" @change="fetchUsers">
            <option :value="null">全部角色</option>
            <option value="admin">管理員</option>
            <option value="manager">主管</option>
            <option value="staff">值班台人員</option>
          </select>
        </div>

        <!-- 部門篩選 -->
        <div class="filter-item">
          <select v-model="selectedDepartment" class="filter-select" @change="fetchUsers">
            <option :value="null">全部部門</option>
            <option value="淡海">淡海</option>
            <option value="安坑">安坑</option>
          </select>
        </div>

        <!-- 狀態篩選 -->
        <div class="filter-item">
          <select v-model="selectedActive" class="filter-select" @change="fetchUsers">
            <option :value="null">全部狀態</option>
            <option :value="true">啟用</option>
            <option :value="false">停用</option>
          </select>
        </div>

        <!-- 重置篩選 -->
        <div class="filter-item">
          <AppButton size="small" @click="resetFilters">
            重置
          </AppButton>
        </div>
      </div>
    </div>

    <!-- 使用者列表 -->
    <div class="table-section">
      <LoadingSpinner v-if="loading && users.length === 0" />

      <EmptyState
        v-else-if="users.length === 0"
        message="沒有找到符合條件的使用者"
      />

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>使用者名稱</th>
            <th>顯示名稱</th>
            <th>角色</th>
            <th>部門</th>
            <th>狀態</th>
            <th>最後登入</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="user in users"
            :key="user.id"
            :class="{ inactive: !user.is_active }"
          >
            <td class="username">{{ user.username }}</td>
            <td>{{ user.display_name }}</td>
            <td>
              <span :class="['role-badge', user.role]">
                {{ getRoleLabel(user.role) }}
              </span>
            </td>
            <td>
              <span v-if="user.department" :class="['dept-badge', getDeptClass(user.department)]">
                {{ user.department }}
              </span>
              <span v-else class="no-dept">-</span>
            </td>
            <td>
              <span :class="['status-badge', user.is_active ? 'active' : 'inactive']">
                {{ user.is_active ? '啟用' : '停用' }}
              </span>
            </td>
            <td>{{ formatDate(user.last_login_at) }}</td>
            <td class="actions">
              <AppButton size="small" @click="editUser(user)">
                編輯
              </AppButton>
              <AppButton
                size="small"
                @click="toggleUserStatus(user)"
              >
                {{ user.is_active ? '停用' : '啟用' }}
              </AppButton>
              <AppButton
                size="small"
                @click="openResetPasswordDialog(user)"
              >
                重設密碼
              </AppButton>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 新增/編輯對話框 -->
    <AppModal
      v-model="showCreateDialog"
      :title="editingUser ? '編輯使用者' : '新增使用者'"
      width="500px"
    >
      <UserForm
        :user="editingUser"
        @submit="handleFormSubmit"
        @cancel="closeFormDialog"
      />
    </AppModal>

    <!-- 重設密碼對話框 -->
    <AppModal
      v-model="showResetPasswordDialog"
      title="重設密碼"
      width="400px"
    >
      <div class="reset-password-form" v-if="resetPasswordUser">
        <p class="reset-info">
          確定要重設 <strong>{{ resetPasswordUser.display_name }}</strong> 的密碼？
        </p>
        <div class="form-group">
          <label class="form-label">新密碼</label>
          <input
            type="password"
            v-model="newPassword"
            class="form-input"
            placeholder="請輸入新密碼（至少8位，含大小寫字母和數字）"
          />
        </div>
        <div class="form-group">
          <label class="form-label">確認密碼</label>
          <input
            type="password"
            v-model="confirmPassword"
            class="form-input"
            placeholder="請再次輸入新密碼"
          />
        </div>
        <p v-if="resetPasswordError" class="form-error">{{ resetPasswordError }}</p>
        <div class="form-actions">
          <AppButton @click="closeResetPasswordDialog">取消</AppButton>
          <AppButton type="primary" @click="handleResetPassword" :loading="resetting">
            確認重設
          </AppButton>
        </div>
      </div>
    </AppModal>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/utils/api'
import PageHeader from '@/components/common/PageHeader.vue'
import AppButton from '@/components/common/AppButton.vue'
import AppModal from '@/components/common/AppModal.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import UserForm from '@/components/users/UserForm.vue'

// 響應式狀態
const users = ref([])
const loading = ref(false)

// 篩選
const selectedRole = ref(null)
const selectedDepartment = ref(null)
const selectedActive = ref(null)

// 對話框
const showCreateDialog = ref(false)
const editingUser = ref(null)

// 重設密碼
const showResetPasswordDialog = ref(false)
const resetPasswordUser = ref(null)
const newPassword = ref('')
const confirmPassword = ref('')
const resetPasswordError = ref('')
const resetting = ref(false)

// 生命週期
onMounted(() => {
  fetchUsers()
})

// 取得使用者列表
async function fetchUsers() {
  loading.value = true

  try {
    const params = {}
    if (selectedRole.value) params.role = selectedRole.value
    if (selectedDepartment.value) params.department = selectedDepartment.value
    if (selectedActive.value !== null) params.is_active = selectedActive.value

    const response = await api.get('/api/users', { params })
    users.value = response.data.items

  } catch (err) {
    console.error('取得使用者列表失敗:', err)
    alert('取得使用者列表失敗：' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

// 重置篩選
function resetFilters() {
  selectedRole.value = null
  selectedDepartment.value = null
  selectedActive.value = null
  fetchUsers()
}

// 角色標籤
function getRoleLabel(role) {
  const labels = {
    admin: '管理員',
    manager: '主管',
    staff: '值班台人員'
  }
  return labels[role] || role
}

// 部門樣式
function getDeptClass(department) {
  return department === '淡海' ? 'danhai' : 'ankeng'
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-TW')
}

// 編輯使用者
function editUser(user) {
  editingUser.value = user
  showCreateDialog.value = true
}

// 關閉表單對話框
function closeFormDialog() {
  editingUser.value = null
  showCreateDialog.value = false
}

// 處理表單提交
async function handleFormSubmit(formData) {
  try {
    if (editingUser.value) {
      await api.put(`/api/users/${editingUser.value.id}`, formData)
    } else {
      await api.post('/api/users', formData)
    }
    closeFormDialog()
    fetchUsers()
  } catch (err) {
    console.error('儲存使用者失敗:', err)
    alert('儲存失敗：' + (err.response?.data?.detail || err.message))
  }
}

// 切換使用者狀態
async function toggleUserStatus(user) {
  const action = user.is_active ? '停用' : '啟用'
  if (!confirm(`確定要${action}使用者「${user.display_name}」？`)) return

  try {
    if (user.is_active) {
      await api.post(`/api/users/${user.id}/deactivate`)
    } else {
      await api.post(`/api/users/${user.id}/activate`)
    }
    fetchUsers()
  } catch (err) {
    console.error('切換使用者狀態失敗:', err)
    alert('操作失敗：' + (err.response?.data?.detail || err.message))
  }
}

// 開啟重設密碼對話框
function openResetPasswordDialog(user) {
  resetPasswordUser.value = user
  newPassword.value = ''
  confirmPassword.value = ''
  resetPasswordError.value = ''
  showResetPasswordDialog.value = true
}

// 關閉重設密碼對話框
function closeResetPasswordDialog() {
  resetPasswordUser.value = null
  showResetPasswordDialog.value = false
}

// 處理重設密碼
async function handleResetPassword() {
  resetPasswordError.value = ''

  if (!newPassword.value) {
    resetPasswordError.value = '請輸入新密碼'
    return
  }

  if (newPassword.value.length < 8) {
    resetPasswordError.value = '密碼長度至少需要 8 個字元'
    return
  }

  if (newPassword.value !== confirmPassword.value) {
    resetPasswordError.value = '兩次輸入的密碼不一致'
    return
  }

  resetting.value = true

  try {
    await api.post(`/api/users/${resetPasswordUser.value.id}/reset-password`, {
      new_password: newPassword.value
    })
    alert('密碼重設成功')
    closeResetPasswordDialog()
  } catch (err) {
    console.error('重設密碼失敗:', err)
    resetPasswordError.value = err.response?.data?.detail || '重設密碼失敗'
  } finally {
    resetting.value = false
  }
}
</script>

<style scoped>
.users-page {
  padding: 20px;
}

.filter-section {
  background: var(--color-background-soft);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-background);
  min-width: 120px;
}

.table-section {
  background: var(--color-background);
  border-radius: 8px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.data-table th {
  background: var(--color-background-soft);
  font-weight: 600;
}

.data-table tr:hover {
  background: var(--color-background-soft);
}

.data-table tr.inactive {
  opacity: 0.6;
}

.username {
  font-family: monospace;
  font-weight: 500;
}

.role-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.admin {
  background: #fce4ec;
  color: #c2185b;
}

.role-badge.manager {
  background: #e8f5e9;
  color: #388e3c;
}

.role-badge.staff {
  background: #e3f2fd;
  color: #1976d2;
}

.dept-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.dept-badge.danhai {
  background: #e3f2fd;
  color: #1976d2;
}

.dept-badge.ankeng {
  background: #fff3e0;
  color: #f57c00;
}

.no-dept {
  color: var(--color-text-light);
}

.status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.active {
  background: #e8f5e9;
  color: #388e3c;
}

.status-badge.inactive {
  background: #f5f5f5;
  color: #757575;
}

.actions {
  display: flex;
  gap: 8px;
}

.reset-password-form {
  padding: 16px 0;
}

.reset-info {
  margin-bottom: 20px;
  color: var(--color-text);
}

.form-group {
  margin-bottom: 16px;
}

.form-label {
  display: block;
  font-weight: 500;
  font-size: 14px;
  color: var(--color-text);
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-background);
  font-size: 14px;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-error {
  color: #ef5350;
  font-size: 12px;
  margin: 0;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 20px;
}
</style>
