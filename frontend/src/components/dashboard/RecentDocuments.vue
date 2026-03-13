<template>
  <div class="recent-documents">
    <div v-if="documents.length === 0" class="empty-state">
      <el-icon class="empty-icon"><Document /></el-icon>
      <p>暂无文档</p>
    </div>

    <div v-else class="doc-list">
      <div
        v-for="doc in documents"
        :key="doc.id"
        class="doc-item"
        @click="handleDocClick(doc)"
      >
        <div class="doc-icon-wrapper">
          <el-icon class="doc-icon" :class="`type-${getFileTypeIcon(doc.file_type)}`">
            <component :is="getFileTypeIcon(doc.file_type)" />
          </el-icon>
        </div>

        <div class="doc-info">
          <div class="doc-name">{{ doc.filename }}</div>
          <div class="doc-meta">
            <span class="doc-type">{{ getFileTypeLabel(doc.file_type) }}</span>
            <span class="doc-time">{{ doc.relative_time }}</span>
          </div>
        </div>

        <el-icon class="arrow-icon"><ArrowRight /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Document, DocumentCopy, Picture, ArrowRight, Files } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  documents: {
    type: Array,
    default: () => []
  }
})

const router = useRouter()

/**
 * 根据文件类型返回图标组件
 */
const getFileTypeIcon = (fileType) => {
  const type = (fileType || '').toLowerCase()
  if (type === 'pdf') return Document
  if (type === 'txt') return DocumentCopy
  if (['jpg', 'jpeg', 'png', 'gif'].includes(type)) return Picture
  return Files
}

/**
 * 获取文件类型标签
 */
const getFileTypeLabel = (fileType) => {
  const type = (fileType || 'unknown').toUpperCase()
  const labels = {
    'PDF': 'PDF文档',
    'TXT': '文本文件',
    'JPG': '图片',
    'JPEG': '图片',
    'PNG': '图片',
    'GIF': '图片'
  }
  return labels[type] || type
}

/**
 * 处理文档点击
 */
const handleDocClick = (doc) => {
  router.push(`/documents?id=${doc.id}`)
}
</script>

<style lang="scss" scoped>
.recent-documents {
  min-height: 200px;

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    color: var(--tech-text-muted);

    .empty-icon {
      font-size: 48px;
      margin-bottom: 12px;
      opacity: 0.3;
    }

    p {
      font-size: 14px;
      margin: 0;
    }
  }

  .doc-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .doc-item {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid var(--tech-glass-border);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;

    &:hover {
      background: rgba(0, 212, 255, 0.05);
      border-color: var(--tech-border-hover);
      transform: translateX(4px);

      .arrow-icon {
        opacity: 1;
        transform: translateX(4px);
      }
    }

    .doc-icon-wrapper {
      flex-shrink: 0;
      width: 40px;
      height: 40px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      background: rgba(0, 212, 255, 0.1);
      margin-right: 12px;
    }

    .doc-icon {
      font-size: 20px;
      color: var(--tech-neon-blue);

      &.type-Picture {
        color: #10b981;
      }

      &.type-DocumentCopy {
        color: #8b5cf6;
      }
    }

    .doc-info {
      flex: 1;
      min-width: 0;

      .doc-name {
        color: var(--tech-text-primary);
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 4px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .doc-meta {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 12px;
        color: var(--tech-text-muted);

        .doc-type {
          padding: 2px 8px;
          background: rgba(0, 212, 255, 0.1);
          border-radius: 4px;
          font-size: 11px;
        }

        .doc-time {
          &::before {
            content: '• ';
            margin-right: 4px;
          }
        }
      }
    }

    .arrow-icon {
      font-size: 16px;
      color: var(--tech-text-muted);
      opacity: 0;
      transition: all 0.3s ease;
    }
  }
}
</style>
