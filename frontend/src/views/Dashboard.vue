<template>
  <div class="dashboard">
    <!-- 页面标题 -->
    <div class="page-header mb-12">
      <div class="header-content">
        <div>
          <h1 class="text-3xl font-bold" style="color: #00d4ff; text-shadow: 0 0 15px rgba(0, 212, 255, 0.6);">
            智能控制台
          </h1>
          <p class="text-gray-400 mt-2">系统概览与快速操作</p>
        </div>
        <div class="header-actions">
          <el-button
            @click="handleRefresh"
            :loading="loading"
            :icon="Refresh"
            circle
            class="refresh-button"
          />
          <span v-if="lastUpdateTime" class="update-time">
            最后更新: {{ formattedUpdateTime }}
          </span>
          <el-tag v-if="wsConnected" type="success" size="small" effect="dark">
            <el-icon><Connection /></el-icon> 实时推送
          </el-tag>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; margin-bottom: 3rem;">
      <StatsCard
        title="文档总数"
        :value="stats.documents.total"
        :icon="Document"
        color="blue"
        :trend="stats.documents.trend_percent"
        :subtitle="`近7天: ${stats.documents.recent_7days}个`"
      />
      <StatsCard
        title="对话会话"
        :value="stats.sessions.total"
        :icon="ChatDotRound"
        color="purple"
        :trend="stats.sessions.trend_percent"
        :subtitle="`近7天活跃: ${stats.sessions.active_7days}个`"
      />
      <StatsCard
        title="总查询数"
        :value="stats.queries.total"
        :icon="Search"
        color="green"
        :trend="stats.queries.trend_percent"
        :subtitle="`近7天: ${stats.queries.recent_7days}次`"
      />
      <StatsCard
        title="活跃用户"
        :value="stats.users.active"
        :icon="User"
        color="yellow"
        :subtitle="`总用户: ${stats.users.total}人`"
      />
    </div>

    <!-- 活动图表 -->
    <div class="grid grid-cols-1 mb-8">
      <div class="tech-card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-tech-text-primary">
            <el-icon class="mr-2"><TrendCharts /></el-icon>
            系统活动趋势 (最近7天)
          </h2>
        </div>
        <div class="card-body">
          <ActivityChart :data="activityTimeline" />
        </div>
      </div>
    </div>

    <!-- 最近内容区域 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- 最近文档 -->
      <div class="tech-card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-tech-text-primary">
            <el-icon class="mr-2"><Document /></el-icon>
            最近文档
          </h2>
        </div>
        <div class="card-body">
          <RecentDocuments :documents="recentDocuments" />
        </div>
      </div>

      <!-- 活跃对话 -->
      <div class="tech-card">
        <div class="card-header">
          <h2 class="text-lg font-semibold text-tech-text-primary">
            <el-icon class="mr-2"><ChatDotRound /></el-icon>
            活跃对话
          </h2>
        </div>
        <div class="card-body">
          <ActiveSessions :sessions="activeSessions" />
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="tech-card">
      <div class="card-header">
        <h2 class="text-lg font-semibold text-tech-text-primary">
          <el-icon class="mr-2"><Pointer /></el-icon>
          快捷操作
        </h2>
      </div>
      <div class="card-body">
        <div class="grid grid-cols-4 gap-4">
          <QuickAction
            :icon="Upload"
            label="上传文档"
            description="添加知识库文档"
            @click="navigateTo('/documents')"
          />
          <QuickAction
            :icon="ChatDotRound"
            label="开始对话"
            description="智能问答助手"
            @click="navigateTo('/chat')"
          />
          <QuickAction
            :icon="Setting"
            label="系统配置"
            description="管理系统设置"
            @click="navigateTo('/settings')"
          />
          <QuickAction
            :icon="Clock"
            label="历史记录"
            description="查看查询历史"
            @click="navigateTo('/history')"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import {
  Document,
  ChatDotRound,
  Search,
  User,
  Upload,
  Setting,
  Clock,
  Refresh,
  Connection,
  TrendCharts,
  Pointer
} from '@element-plus/icons-vue'

import StatsCard from '../components/dashboard/StatsCard.vue'
import QuickAction from '../components/dashboard/QuickAction.vue'
import ActivityChart from '../components/dashboard/ActivityChart.vue'
import RecentDocuments from '../components/dashboard/RecentDocuments.vue'
import ActiveSessions from '../components/dashboard/ActiveSessions.vue'

import { useDashboard } from '../composables/useDashboard'

const router = useRouter()

// 使用Dashboard Composable
const {
  loading,
  stats,
  activityTimeline,
  recentDocuments,
  activeSessions,
  lastUpdateTime,
  wsConnected,
  formattedUpdateTime,
  refresh
} = useDashboard()

// 手动刷新
const handleRefresh = () => {
  refresh()
}

// 导航
const navigateTo = (path) => {
  router.push(path)
}
</script>

<style lang="scss" scoped>
.dashboard {
  padding: 24px;
  max-width: 1400px;
  margin: 0 auto;
  height: calc(100vh - 64px - 48px);
  overflow-y: auto;
  overflow-x: auto;

  // 自定义滚动条
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

.page-header {
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 12px;

    .refresh-button {
      background: rgba(0, 212, 255, 0.1);
      border: 1px solid rgba(0, 212, 255, 0.3);
      color: var(--tech-neon-blue);

      &:hover {
        background: rgba(0, 212, 255, 0.2);
        border-color: var(--tech-neon-blue);
        transform: rotate(180deg);
      }
    }

    .update-time {
      font-size: 12px;
      color: var(--tech-text-muted);
    }
  }
}

.stats-grid {
  @media (max-width: 1024px) {
    grid-template-columns: repeat(2, 1fr) !important;
  }

  @media (max-width: 640px) {
    grid-template-columns: 1fr !important;
  }
}

.tech-card {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

  &:hover {
    box-shadow: var(--tech-shadow-glow);
    border-color: var(--tech-border-hover);
  }

  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--tech-glass-border);
    background: rgba(255, 255, 255, 0.02);

    h2 {
      display: flex;
      align-items: center;
      margin: 0;
    }
  }

  .card-body {
    padding: 20px;
  }
}
</style>
