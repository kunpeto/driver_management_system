import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useEmployeeStore = defineStore('employee', () => {
  const employees = ref([])
  const loading = ref(false)
  const currentEmployee = ref(null)

  function setEmployees(data) {
    employees.value = data
  }

  function setLoading(status) {
    loading.value = status
  }

  function setCurrentEmployee(employee) {
    currentEmployee.value = employee
  }

  function addEmployee(employee) {
    employees.value.push(employee)
  }

  function updateEmployee(id, updatedData) {
    const index = employees.value.findIndex(emp => emp.id === id)
    if (index !== -1) {
      employees.value[index] = { ...employees.value[index], ...updatedData }
    }
  }

  function removeEmployee(id) {
    employees.value = employees.value.filter(emp => emp.id !== id)
  }

  return {
    employees,
    loading,
    currentEmployee,
    setEmployees,
    setLoading,
    setCurrentEmployee,
    addEmployee,
    updateEmployee,
    removeEmployee
  }
})
