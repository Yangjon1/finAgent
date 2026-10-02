<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const router = useRouter()
const auth = useAuthStore()
function logout() { auth.logout(); router.push('/login') }
</script>

<template>
  <el-container v-if="auth.isAuthenticated" class="shell">
    <el-header><strong>FinAgent</strong><span>企业财税智能审批与合同风控平台</span><span class="spacer" /><span>{{ auth.user?.display_name }}</span><el-button text type="primary" @click="logout">退出</el-button></el-header>
    <el-container>
      <el-aside width="220px"><el-menu default-active="1"><el-menu-item index="1" @click="router.push('/')">工作台</el-menu-item><el-menu-item index="2">我的待办</el-menu-item><el-menu-item v-permission="'expense:read'" index="3" @click="router.push('/expenses')">报销管理</el-menu-item><el-menu-item v-permission="'knowledge:document:index'" index="4" @click="router.push('/knowledge')">知识库</el-menu-item><el-menu-item index="5">合同管理</el-menu-item><el-menu-item index="6">审批中心</el-menu-item><el-menu-item v-permission="'rbac:user:read'" index="7">系统管理</el-menu-item></el-menu></el-aside>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
  <router-view v-else />
</template>

<style scoped>
.shell { min-height: 100vh; background: #f5f7fa; } header { display: flex; align-items: center; gap: 20px; background: #1f2937; color: white; } aside { background: white; } .spacer { flex: 1; }
</style>
