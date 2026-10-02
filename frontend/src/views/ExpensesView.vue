<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

type Expense = { id: string; title: string; category: string; total_amount: string; status: string; version: number }
const rows = ref<Expense[]>([])
const dialogVisible = ref(false)
const loading = ref(false)
const uploadInput = ref<HTMLInputElement | null>(null)
const uploadReportId = ref('')
const form = reactive({ title: '', category: '差旅费', description: '', amount: 0, tax_amount: 0 })

async function load() {
  const response = await api.get('/expenses')
  rows.value = response.data.data
}

async function create() {
  loading.value = true
  try {
    await api.post('/expenses', { title: form.title, category: form.category, currency: 'CNY', items: [{ description: form.description, amount: form.amount, tax_amount: form.tax_amount }] })
    ElMessage.success('报销草稿已创建')
    dialogVisible.value = false
    Object.assign(form, { title: '', category: '差旅费', description: '', amount: 0, tax_amount: 0 })
    await load()
  } catch (error: any) { ElMessage.error(error.response?.data?.detail || '创建失败') }
  finally { loading.value = false }
}

async function submit(row: Expense) {
  try { await api.post(`/expenses/${row.id}/submit`, { expected_version: row.version }); ElMessage.success('报销单已提交'); await load() }
  catch (error: any) { ElMessage.error(error.response?.data?.detail || '提交失败') }
}

function chooseFile(row: Expense) {
  uploadReportId.value = row.id
  uploadInput.value?.click()
}

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  try {
    const presign = await api.post('/files/presign', { owner_type: 'expense_report', owner_id: uploadReportId.value, file_name: file.name, content_type: file.type, size_bytes: file.size })
    const info = presign.data.data
    const uploaded = await fetch(info.upload_url, { method: 'PUT', headers: { 'Content-Type': file.type }, body: file })
    if (!uploaded.ok) throw new Error('对象存储上传失败')
    await api.post(`/files/${info.file_id}/complete`, {})
    ElMessage.success('附件已上传，OCR 任务已排队')
  } catch (error: any) { ElMessage.error(error.response?.data?.detail || error.message || '附件上传失败') }
  finally { input.value = '' }
}

onMounted(load)
</script>

<template>
  <el-card>
    <template #header><div class="header"><span>我的报销</span><el-button v-permission="'expense:create'" type="primary" @click="dialogVisible = true">新建报销</el-button></div></template>
    <input ref="uploadInput" hidden type="file" accept="image/jpeg,image/png,application/pdf" @change="uploadFile" />
    <el-table :data="rows" stripe><el-table-column prop="title" label="标题" /><el-table-column prop="category" label="类别" /><el-table-column prop="total_amount" label="金额" /><el-table-column prop="status" label="状态" /><el-table-column label="操作" width="220"><template #default="scope"><el-button v-permission="'file:presign'" link type="primary" @click="chooseFile(scope.row)">上传附件</el-button><el-button v-if="scope.row.status === 'DRAFT'" v-permission="'expense:submit'" link type="primary" @click="submit(scope.row)">提交</el-button></template></el-table-column></el-table>
  </el-card>
  <el-dialog v-model="dialogVisible" title="新建报销草稿" width="520px"><el-form label-width="90px"><el-form-item label="标题"><el-input v-model="form.title" /></el-form-item><el-form-item label="类别"><el-input v-model="form.category" /></el-form-item><el-form-item label="明细"><el-input v-model="form.description" /></el-form-item><el-form-item label="金额"><el-input-number v-model="form.amount" :min="0.01" :precision="2" /></el-form-item><el-form-item label="税额"><el-input-number v-model="form.tax_amount" :min="0" :precision="2" /></el-form-item></el-form><template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" :loading="loading" @click="create">保存草稿</el-button></template></el-dialog>
</template>

<style scoped>.header { display: flex; justify-content: space-between; align-items: center; }</style>
