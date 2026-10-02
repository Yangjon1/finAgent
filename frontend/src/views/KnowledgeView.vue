<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '../api/client'

const bases = ref<any[]>([])
const selectedBase = ref('')
const query = ref('')
const hits = ref<any[]>([])
const document = reactive({ title: '', content: '' })

async function loadBases() {
  const response = await api.get('/knowledge/bases')
  bases.value = response.data.data
  if (!selectedBase.value && bases.value.length) selectedBase.value = bases.value[0].id
}

async function indexDocument() {
  if (!selectedBase.value) return ElMessage.warning('请先选择知识库')
  try {
    await api.post(`/knowledge/bases/${selectedBase.value}/documents`, { ...document, source_type: 'TEXT' })
    ElMessage.success('文档已切分并建立索引')
    document.title = ''
    document.content = ''
  } catch (error: any) { ElMessage.error(error.response?.data?.detail || '索引失败') }
}

async function search() {
  const response = await api.post('/knowledge/search', { query: query.value, knowledge_base_id: selectedBase.value, top_k: 5 })
  hits.value = response.data.data.hits
}

onMounted(loadBases)
</script>

<template>
  <el-row :gutter="16"><el-col :span="10"><el-card><template #header>制度文档索引</template><el-form label-width="90px"><el-form-item label="知识库"><el-select v-model="selectedBase" placeholder="选择知识库"><el-option v-for="base in bases" :key="base.id" :label="base.name" :value="base.id" /></el-select></el-form-item><el-form-item label="标题"><el-input v-model="document.title" /></el-form-item><el-form-item label="正文"><el-input v-model="document.content" type="textarea" :rows="10" /></el-form-item><el-button v-permission="'knowledge:document:index'" type="primary" @click="indexDocument">切分并建立索引</el-button></el-form></el-card></el-col><el-col :span="14"><el-card><template #header>知识库检索测试</template><el-input v-model="query" placeholder="例如：差旅住宿费用标准" @keyup.enter="search"><template #append><el-button @click="search">检索</el-button></template></el-input><el-divider /><el-empty v-if="!hits.length" description="暂无检索结果" /><el-card v-for="hit in hits" :key="hit.chunk_id" shadow="never" class="hit"><div><el-tag size="small">score {{ Number(hit.score).toFixed(3) }}</el-tag> {{ hit.title }}</div><p>{{ hit.text }}</p></el-card></el-card></el-col></el-row>
</template>

<style scoped>.hit { margin-bottom: 10px; }.hit p { white-space: pre-wrap; line-height: 1.6; }</style>
