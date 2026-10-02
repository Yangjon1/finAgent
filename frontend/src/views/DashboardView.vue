<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const apiStatus = ref('未检查')
async function checkApi() {
  try { await api.get('/health'); apiStatus.value = '正常'; ElMessage.success('后端连接正常') }
  catch { apiStatus.value = '不可用'; ElMessage.error('后端暂不可用') }
}
</script>

<template>
  <el-card><template #header>工作台</template><el-descriptions :column="1" border><el-descriptions-item label="当前用户">{{ auth.user?.display_name }}（{{ auth.user?.username }}）</el-descriptions-item><el-descriptions-item label="角色">{{ auth.user?.roles.join('、') }}</el-descriptions-item><el-descriptions-item label="API 状态">{{ apiStatus }}</el-descriptions-item></el-descriptions><el-button type="primary" class="check" @click="checkApi">检查后端健康状态</el-button><el-button v-permission="'rbac:user:create'" class="check" @click="ElMessage.info('用户管理将在下一迭代接入')">新建用户</el-button></el-card>
</template>

<style scoped>.check { margin-top: 20px; }</style>
