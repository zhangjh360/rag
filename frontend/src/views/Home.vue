<template>
  <div class="home">
    <!-- 文档上传区域 -->
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <span>文档上传</span>
        </div>
      </template>
      
      <el-upload
        class="upload-area"
        drag
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        accept=".pdf,.txt"
      >
        <el-icon class="el-icon--upload"><Upload /></el-icon>
        <div class="el-upload__text">
          拖拽文件到此处或 <em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传 PDF 或 TXT 文件
          </div>
        </template>
      </el-upload>
      
      <el-button
        type="primary"
        :loading="uploading"
        @click="uploadFile"
        :disabled="!selectedFile"
        style="margin-top: 10px;"
      >
        上传文档
      </el-button>
    </el-card>

    <!-- 文档列表 -->
    <el-card class="documents-card">
      <template #header>
        <div class="card-header">
          <span>已上传文档 ({{ documents.length }})</span>
        </div>
      </template>
      
      <el-table :data="documents" style="width: 100%">
        <el-table-column prop="filename" label="文件名" />
        <el-table-column prop="created_at" label="上传时间" />
        <el-table-column prop="metadata.type" label="类型" />
      </el-table>
    </el-card>

    <!-- 查询区域 -->
    <el-card class="query-card">
      <template #header>
        <div class="card-header">
          <span>智能查询</span>
        </div>
      </template>
      
      <div class="query-input">
        <el-input
          v-model="queryInput"
          type="textarea"
          :rows="3"
          placeholder="请输入您的问题..."
          @keyup.enter="handleQuery"
        />
        <el-button
          type="primary"
          :loading="loading"
          @click="handleQuery"
          style="margin-top: 10px;"
        >
          查询
        </el-button>
      </div>
      
      <!-- 查询结果 -->
      <div v-if="currentResponse" class="query-result">
        <h4>回答：</h4>
        <div class="response-content">{{ currentResponse }}</div>
        
        <h4>相关文档：</h4>
        <el-collapse>
          <el-collapse-item
            v-for="(source, index) in currentSources"
            :key="index"
            :title="source.filename"
            :name="index"
          >
            <div class="source-content">
              <p><strong>相似度:</strong> {{ (source.similarity * 100).toFixed(2) }}%</p>
              <p><strong>内容预览:</strong></p>
              <p>{{ source.content_preview }}</p>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { useRagStore } from '../store/ragStore'
import { ElMessage } from 'element-plus'

const store = useRagStore()
const queryInput = ref('')
const selectedFile = ref(null)
const fileList = ref([])

const loading = computed(() => store.loading)
const uploading = computed(() => store.uploading)
const documents = computed(() => store.documents)
const currentResponse = computed(() => store.currentResponse)
const currentSources = computed(() => store.currentSources)

const handleFileChange = (file) => {
  selectedFile.value = file.raw
  fileList.value = [file]
}

const uploadFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }
  
  try {
    await store.uploadDocument(selectedFile.value)
    ElMessage.success('文档上传成功')
    selectedFile.value = null
    fileList.value = []
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  }
}

const handleQuery = async () => {
  if (!queryInput.value.trim()) {
    ElMessage.warning('请输入查询内容')
    return
  }
  
  try {
    await store.queryDocuments(queryInput.value)
    ElMessage.success('查询完成')
  } catch (error) {
    ElMessage.error('查询失败: ' + error.message)
  }
}

onMounted(() => {
  store.fetchDocuments()
})
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  height: calc(100vh - 64px - 48px); /* minus header height and padding */
  overflow-y: auto;
  overflow-x: auto; /* allow horizontal scroll */

  /* custom scrollbar */
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgba(0, 212, 255, 0.3);
    border-radius: 4px;

    &:hover {
      background: rgba(0, 212, 255, 0.5);
    }
  }
}

.upload-card,
.documents-card,
.query-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  width: 100%;
}

.query-input {
  margin-bottom: 20px;
}

.query-result {
  margin-top: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.response-content {
  margin: 10px 0;
  padding: 10px;
  background-color: white;
  border-radius: 4px;
  border-left: 4px solid #409EFF;
}

.source-content {
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}
</style>