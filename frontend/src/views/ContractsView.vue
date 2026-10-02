<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const rows = ref<any[]>([])
const dialogVisible = ref(false)
const form = reactive({ title: '', contract_no: '', content: '' })

async function load() { rows.value = (await api.get('/contracts')).data.data }
async function create() {
  try { await api.post('/contracts', form); ElMessage.success('合同已创建'); dialogVisible.value = false; Object.assign(form, { title: '', contract_no: '', content: '' }); await load() }
  catch (error: any) { ElMessage.error(error.response?.data?.detail || '创建失败') }
}
async function analyze(row: any) {
  try { const result = await api.post(`/contracts/${row.id}/analyze`); ElMessage.success(`分析状态：${result.data.data.status}`) }
  catch (error: any) { ElMessage.error(error.response?.data?.detail || '分析失败') }
}
onMounted(load)
</script>

<template>
  <el-card><template #header><div class="header"><span>合同风险审核</span><el-button v-permission="'contract:create'" type="primary" @click="dialogVisible = true">新建合同</el-button></div></template><el-table :data="rows" stripe><el-table-column prop="title" label="标题" /><el-table-column prop="contract_no" label="合同编号" /><el-table-column prop="status" label="状态" /><el-table-column prop="risk_level" label="风险等级" /><el-table-column label="操作"><template #default="scope"><el-button v-permission="'contract:analyze'" link type="primary" @click="analyze(scope.row)">开始分析</el-button></template></el-table-column></el-table></el-card>
  <el-dialog v-model="dialogVisible" title="新建合同" width="620px"><el-form label-width="90px"><el-form-item label="标题"><el-input v-model="form.title" /></el-form-item><el-form-item label="合同编号"><el-input v-model="form.contract_no" /></el-form-item><el-form-item label="合同正文"><el-input v-model="form.content" type="textarea" :rows="12" /></el-form-item></el-form><template #footer><el-button @click="dialogVisible = false">取消</el-button><el-button type="primary" @click="create">保存</el-button></template></el-dialog>
</template>

<style scoped>.header { display: flex; justify-content: space-between; align-items: center; }</style>
