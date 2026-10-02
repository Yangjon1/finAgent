<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'Admin@123456' })

async function submit() {
  loading.value = true
  try { await auth.login(form.username, form.password); ElMessage.success('登录成功'); await router.push('/') }
  catch (error: any) { ElMessage.error(error.response?.data?.detail || '登录失败') }
  finally { loading.value = false }
}
</script>

<template>
  <div class="login-page"><el-card class="login-card"><template #header><strong>FinAgent 企业财税平台</strong></template><el-form :model="form" @submit.prevent="submit"><el-form-item label="用户名"><el-input v-model="form.username" autocomplete="username" /></el-form-item><el-form-item label="密码"><el-input v-model="form.password" type="password" show-password autocomplete="current-password" /></el-form-item><el-button class="submit" type="primary" native-type="submit" :loading="loading">登录</el-button></el-form></el-card></div>
</template>

<style scoped>.login-page { min-height: 100vh; display: grid; place-items: center; background: #f5f7fa; }.login-card { width: 420px; }.submit { width: 100%; }</style>
