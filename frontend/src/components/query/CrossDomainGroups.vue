<template>
  <div class="cross-domain-groups">
    <div class="groups-header">
      <h4 class="groups-title">
        <el-icon><Connection /></el-icon>
        跨领域检索结果
      </h4>
      <span class="groups-count">{{ groups.length }} 个领域</span>
    </div>

    <div class="groups-list">
      <el-collapse v-model="activeGroups" accordion>
        <el-collapse-item
          v-for="group in sortedGroups"
          :key="group.namespace"
          :name="group.namespace"
        >
          <template #title>
            <div class="group-title">
              <DomainBadge
                :namespace="group.namespace"
                :display-name="group.displayName"
              />
              <el-tag size="small" type="info" class="count-tag">
                {{ group.count }} 个结果
              </el-tag>
            </div>
          </template>

          <div class="group-content">
            <div
              v-for="(result, index) in group.results"
              :key="result.chunkId"
              class="group-result-item"
            >
              <div class="result-header">
                <span class="result-index">#{{ index + 1 }}</span>
                <el-tag type="info" size="small" class="score-tag">
                  {{ (result.score * 100).toFixed(1) }}%
                </el-tag>
              </div>

              <div class="result-content">
                <p class="content-text" v-html="highlightText(result.content, query)"></p>
              </div>

              <div class="result-footer">
                <span class="document-title">
                  <el-icon><Document /></el-icon>
                  {{ result.documentTitle }}
                </span>
                <span class="chunk-index" v-if="result.chunkIndex !== null">
                  块 #{{ result.chunkIndex }}
                </span>
              </div>
            </div>

            <!-- 显示更多按钮 -->
            <div class="show-more" v-if="group.count > group.results.length">
              <el-button size="small" text @click="loadMoreResults(group)">
                查看更多 ({{ group.count - group.results.length }} 个)
              </el-button>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Connection, Document } from '@element-plus/icons-vue'
import DomainBadge from '../domain/DomainBadge.vue'
import { highlightKeywords } from '@/services/queryService'

const props = defineProps({
  groups: {
    type: Array,
    default: () => []
  },
  query: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['load-more'])

// 默认展开第一个领域
const activeGroups = ref(props.groups[0]?.namespace || '')

// 按结果数量排序
const sortedGroups = computed(() => {
  return [...props.groups].sort((a, b) => b.count - a.count)
})

// 高亮文本
const highlightText = (text, query) => {
  return highlightKeywords(text, query)
}

// 加载更多结果
const loadMoreResults = (group) => {
  emit('load-more', group)
}
</script>

<style lang="scss" scoped>
.cross-domain-groups {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);

  .groups-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--tech-glass-border);

    .groups-title {
      font-size: 16px;
      font-weight: 600;
      color: var(--tech-text-primary);
      margin: 0;
      display: flex;
      align-items: center;
      gap: 8px;
      background: linear-gradient(135deg, var(--tech-neon-blue), var(--tech-neon-purple));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;

      .el-icon {
        font-size: 18px;
        color: var(--tech-neon-blue);
      }
    }

    .groups-count {
      font-size: 13px;
      color: var(--tech-text-secondary);
      padding: 4px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--tech-glass-border);
      border-radius: 4px;
    }
  }

  .groups-list {
    :deep(.el-collapse) {
      border: none;
      background: transparent;

      .el-collapse-item {
        margin-bottom: 12px;
        border: 1px solid var(--tech-glass-border);
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.02);
        overflow: hidden;
        transition: all 0.3s ease;

        &:hover {
          border-color: var(--tech-border-hover);
          background: rgba(255, 255, 255, 0.05);
        }

        &.is-active {
          border-color: var(--tech-neon-blue);
          box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.2);
        }
      }

      .el-collapse-item__header {
        height: auto;
        padding: 12px 16px;
        background: transparent;
        border: none;
        color: var(--tech-text-primary);
        font-weight: 500;

        &:hover {
          background: rgba(255, 255, 255, 0.03);
        }

        .el-icon {
          color: var(--tech-neon-blue);
        }
      }

      .el-collapse-item__wrap {
        background: transparent;
        border: none;
      }

      .el-collapse-item__content {
        padding: 0 16px 16px;
        color: var(--tech-text-primary);
      }
    }

    .group-title {
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;

      .count-tag {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--tech-glass-border);
      }
    }

    .group-content {
      .group-result-item {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid var(--tech-glass-border);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        transition: all 0.3s ease;

        &:last-child {
          margin-bottom: 0;
        }

        &:hover {
          border-color: var(--tech-border-hover);
          background: rgba(255, 255, 255, 0.05);
          transform: translateX(4px);
        }

        .result-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 8px;

          .result-index {
            font-size: 13px;
            font-weight: 600;
            color: var(--tech-neon-purple);
          }

          .score-tag {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--tech-glass-border);
            font-size: 12px;
          }
        }

        .result-content {
          margin-bottom: 8px;

          .content-text {
            font-size: 13px;
            line-height: 1.5;
            color: var(--tech-text-primary);
            margin: 0;

            :deep(mark.highlight) {
              background: rgba(0, 212, 255, 0.2);
              color: var(--tech-neon-blue);
              padding: 2px 4px;
              border-radius: 2px;
              font-weight: 600;
            }
          }
        }

        .result-footer {
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 12px;
          color: var(--tech-text-secondary);

          .document-title {
            display: flex;
            align-items: center;
            gap: 4px;

            .el-icon {
              font-size: 13px;
            }
          }

          .chunk-index {
            padding: 2px 6px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--tech-glass-border);
            border-radius: 3px;
            font-size: 11px;
          }
        }
      }

      .show-more {
        text-align: center;
        margin-top: 12px;
        padding-top: 12px;
        border-top: 1px solid var(--tech-glass-border);

        .el-button {
          color: var(--tech-neon-blue);
          font-weight: 500;

          &:hover {
            color: var(--tech-neon-purple);
            background: rgba(0, 212, 255, 0.1);
          }
        }
      }
    }
  }
}
</style>
