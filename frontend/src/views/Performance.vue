<template>
  <div class="performance-page">
    <div class="page-header">
      <h1><i class="fas fa-tachometer-alt"></i> 性能监控</h1>
      <p>实时监控系统性能和查询统计</p>
    </div>

    <!-- 系统健康状态 -->
    <div class="health-status-section">
      <SystemHealth />
    </div>

    <!-- 性能统计图表 -->
    <div class="stats-section">
      <PerformanceStats />
    </div>

    <!-- 快捷操作 -->
    <div class="actions-section">
      <el-card class="action-card">
        <template #header>
          <div class="card-header">
            <span><i class="fas fa-tools"></i> 维护操作</span>
          </div>
        </template>
        <div class="action-buttons">
          <el-button type="primary" @click="showCleanupDialog">
            <i class="fas fa-broom"></i> 清理旧日志
          </el-button>
          <el-button @click="viewRetentionPolicy">
            <i class="fas fa-info-circle"></i> 保留策略
          </el-button>
          <el-button @click="refreshAll">
            <i class="fas fa-sync-alt"></i> 刷新数据
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 清理日志对话框 -->
    <el-dialog v-model="cleanupDialogVisible" title="清理旧日志" width="500px">
      <el-form :model="cleanupForm" label-width="120px">
        <el-form-item label="保留天数">
          <el-input-number v-model="cleanupForm.days" :min="1" :max="365" />
          <div class="form-tip">将删除 {{ cleanupForm.days }} 天前的日志</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="cleanupDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCleanup" :loading="cleaning">
          确定清理
        </el-button>
      </template>
    </el-dialog>

    <!-- 保留策略对话框 -->
    <el-dialog v-model="retentionDialogVisible" title="日志保留策略" width="600px">
      <div v-if="retentionData" class="retention-info">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="默认保留期">
            {{ retentionData.default_retention_days }} 天
          </el-descriptions-item>
          <el-descriptions-item label="自动清理">
            {{ retentionData.storage_info?.auto_cleanup ? '启用' : '禁用' }}
          </el-descriptions-item>
          <el-descriptions-item label="数据压缩">
            {{ retentionData.storage_info?.compression_enabled ? '启用' : '禁用' }}
          </el-descriptions-item>
        </el-descriptions>

        <h4 style="margin-top: 20px;">各时间段日志数量</h4>
        <el-table :data="retentionData.retention_data" stripe style="width: 100%">
          <el-table-column prop="label" label="时间范围" width="150" />
          <el-table-column prop="count" label="日志数量" />
          <el-table-column prop="hours" label="小时数" />
        </el-table>
      </div>
      <div v-else class="loading-container">
        <el-loading :fullscreen="false" />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import PerformanceStats from '../components/performance/PerformanceStats.vue'
import SystemHealth from '../components/performance/SystemHealth.vue'
import performanceService from '../services/performanceService'

// 对话框状态
const cleanupDialogVisible = ref(false)
const retentionDialogVisible = ref(false)
const cleaning = ref(false)

// 表单数据
const cleanupForm = ref({
  days: 30
})

const retentionData = ref(null)

// 显示清理对话框
const showCleanupDialog = () => {
  cleanupDialogVisible.value = true
}

// 执行清理
const handleCleanup = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 ${cleanupForm.value.days} 天前的日志吗?此操作不可恢复!`,
      '确认清理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    cleaning.value = true
    const response = await performanceService.cleanupLogs({ days: cleanupForm.value.days })

    if (response.success) {
      ElMessage.success(`成功清理 ${response.data.deleted_count} 条日志`)
      cleanupDialogVisible.value = false
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清理日志失败')
      console.error('清理失败:', error)
    }
  } finally {
    cleaning.value = false
  }
}

// 查看保留策略
const viewRetentionPolicy = async () => {
  retentionDialogVisible.value = true
  retentionData.value = null

  try {
    const response = await performanceService.getLogRetention()
    if (response.success) {
      retentionData.value = response.data
    }
  } catch (error) {
    ElMessage.error('获取保留策略失败')
    console.error('获取保留策略失败:', error)
  }
}

// 刷新所有数据
const refreshAll = () => {
  ElMessage.info('刷新功能将在子组件中实现')
  // 这里可以通过事件总线或状态管理触发子组件刷新
}
</script>

<style scoped>
.performance-page {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
  min-height: 100%;
  overflow-y: auto;
  padding-bottom: 60px;
}

.page-header {
  margin-bottom: 32px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  color: var(--tech-neon-blue);
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-header p {
  margin: 0;
  color: var(--tech-text-secondary);
  font-size: 14px;
}

.health-status-section {
  margin-bottom: 32px;
}

.stats-section {
  margin-bottom: 32px;
}

.actions-section {
  margin-bottom: 32px;
}

.action-card {
  background: var(--tech-glass-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--tech-glass-border);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--tech-text-primary);
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.form-tip {
  font-size: 12px;
  color: var(--tech-text-secondary);
  margin-top: 8px;
}

.retention-info h4 {
  margin: 0 0 12px 0;
  color: var(--tech-text-primary);
  font-size: 16px;
  font-weight: 500;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .performance-page {
    padding: 16px;
  }

  .page-header h1 {
    font-size: 24px;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
  }
}
</style>
