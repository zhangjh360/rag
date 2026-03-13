<template>
  <el-dropdown trigger="click" @command="handleCommand">
    <el-button size="small" class="settings-button">
      <el-icon><Setting /></el-icon>
      检索设置
    </el-button>
    <template #dropdown>
      <el-dropdown-menu class="retrieval-settings-menu">
        <div class="settings-panel">
          <!-- 检索方法 -->
          <div class="setting-section">
            <div class="section-label">检索方法</div>
            <el-radio-group v-model="localSettings.method" size="small">
              <el-radio label="hybrid">
                <el-icon><MagicStick /></el-icon>
                混合(推荐)
              </el-radio>
              <el-radio label="vector">
                <el-icon><Search /></el-icon>
                向量
              </el-radio>
              <el-radio label="bm25">
                <el-icon><Key /></el-icon>
                BM25
              </el-radio>
            </el-radio-group>
          </div>

          <!-- 检索模式 -->
          <div class="setting-section">
            <div class="section-label">检索模式</div>
            <el-radio-group v-model="localSettings.mode" size="small">
              <el-radio label="auto">
                <el-icon><MagicStick /></el-icon>
                自动
              </el-radio>
              <el-radio label="single">
                <el-icon><Position /></el-icon>
                单领域
              </el-radio>
              <el-radio label="cross">
                <el-icon><Connection /></el-icon>
                跨领域
              </el-radio>
            </el-radio-group>
          </div>

          <!-- 领域选择(单领域模式) -->
          <div class="setting-section" v-if="localSettings.mode === 'single'">
            <div class="section-label">选择领域</div>
            <DomainSelector
              v-model="localSettings.namespace"
              size="small"
              placeholder="选择一个领域"
            />
          </div>

          <!-- 高级设置 -->
          <el-collapse v-model="advancedOpen" class="advanced-settings">
            <el-collapse-item name="advanced">
              <template #title>
                <span class="advanced-title">
                  <el-icon><Tools /></el-icon>
                  高级设置
                </span>
              </template>

              <!-- 返回结果数 -->
              <div class="setting-item">
                <span class="item-label">结果数量</span>
                <el-input-number
                  v-model="localSettings.topK"
                  size="small"
                  :min="1"
                  :max="50"
                  :step="5"
                  class="number-input-fix"
                />
              </div>

              <!-- 混合权重(仅混合模式) -->
              <div class="setting-item" v-if="localSettings.method === 'hybrid'">
                <span class="item-label">
                  混合权重
                  <el-tooltip content="0.0=纯BM25, 1.0=纯向量, 0.5=均衡" placement="top">
                    <el-icon class="help-icon"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </span>
                <el-slider
                  v-model="localSettings.alpha"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  :marks="{ 0: 'BM25', 0.5: '均衡', 1: '向量' }"
                  show-stops
                />
              </div>

              <!-- 相似度阈值(仅向量模式) -->
              <div class="setting-item" v-if="localSettings.method === 'vector'">
                <span class="item-label">相似度阈值</span>
                <el-slider
                  v-model="localSettings.similarityThreshold"
                  :min="0"
                  :max="1"
                  :step="0.05"
                  show-stops
                />
              </div>
            </el-collapse-item>
          </el-collapse>

          <!-- 按钮组 -->
          <div class="setting-actions">
            <el-button size="small" @click="resetSettings">重置</el-button>
            <el-button size="small" type="primary" @click="applySettings">应用</el-button>
          </div>
        </div>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ref, watch } from 'vue'
import {
  Setting,
  Search,
  Key,
  MagicStick,
  Position,
  Connection,
  Tools,
  QuestionFilled
} from '@element-plus/icons-vue'
import DomainSelector from '../domain/DomainSelector.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      method: 'hybrid',
      mode: 'auto',
      namespace: null,
      topK: 10,
      alpha: 0.5,
      similarityThreshold: 0.0
    })
  }
})

const emit = defineEmits(['update:modelValue', 'apply'])

// 本地设置
const localSettings = ref({ ...props.modelValue })
const advancedOpen = ref([])

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  localSettings.value = { ...newVal }
}, { deep: true })

// 重置设置
const resetSettings = () => {
  localSettings.value = {
    method: 'hybrid',
    mode: 'auto',
    namespace: null,
    topK: 10,
    alpha: 0.5,
    similarityThreshold: 0.0
  }
}

// 应用设置
const applySettings = () => {
  emit('update:modelValue', { ...localSettings.value })
  emit('apply', { ...localSettings.value })
}

// 处理命令
const handleCommand = (command) => {
  // 预留命令处理
}
</script>

<style lang="scss" scoped>
// 全局覆盖数字输入框样式 - 使用硬编码颜色确保可见性
:deep(.el-input-number) {
  .el-input__wrapper {
    .el-input__inner {
      color: #f3f4f6 !important;
      -webkit-text-fill-color: #f3f4f6 !important;
    }
  }
}

:deep(.number-input-fix) {
  input {
    color: #f3f4f6 !important;
    -webkit-text-fill-color: #f3f4f6 !important;
  }
}

.settings-button {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--tech-glass-border);
  color: var(--tech-text-primary);
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: var(--tech-border-hover);
    color: var(--tech-neon-blue);
  }

  .el-icon {
    margin-right: 4px;
  }
}

:deep(.retrieval-settings-menu) {
  background: var(--tech-glass-bg);
  border: 1px solid var(--tech-glass-border);
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  padding: 0;

  // 确保所有输入框文字颜色正确
  .el-input__inner {
    color: var(--tech-text-primary) !important;
  }

  .el-input-number .el-input__inner {
    color: var(--tech-text-primary) !important;
  }

  .settings-panel {
    padding: 16px;
    min-width: 380px;
    max-width: 450px;

    .setting-section {
      margin-bottom: 20px;

      &:last-child {
        margin-bottom: 0;
      }

      .section-label {
        font-size: 13px;
        font-weight: 600;
        color: var(--tech-text-primary);
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 6px;
      }

      .el-radio-group {
        width: 100%;
        display: flex;
        flex-direction: column;
        gap: 8px;

        .el-radio {
          margin: 0;
          padding: 8px 12px;
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid var(--tech-glass-border);
          border-radius: 6px;
          transition: all 0.3s ease;

          &:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--tech-border-hover);
          }

          &.is-checked {
            background: rgba(0, 212, 255, 0.1);
            border-color: var(--tech-neon-blue);
          }

          .el-icon {
            margin-right: 6px;
            font-size: 14px;
          }
        }
      }
    }

    .advanced-settings {
      margin-bottom: 16px;
      border: none;
      background: transparent;

      :deep(.el-collapse-item) {
        border: 1px solid var(--tech-glass-border);
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.02);

        .el-collapse-item__header {
          background: transparent;
          border: none;
          padding: 8px 12px;
          color: var(--tech-text-primary);
          font-size: 13px;

          .advanced-title {
            display: flex;
            align-items: center;
            gap: 6px;

            .el-icon {
              color: var(--tech-neon-purple);
            }
          }
        }

        .el-collapse-item__wrap {
          background: transparent;
          border: none;
        }

        .el-collapse-item__content {
          padding: 12px;
          border-top: 1px solid var(--tech-glass-border);
        }
      }

      .setting-item {
        margin-bottom: 16px;

        &:last-child {
          margin-bottom: 0;
        }

        .item-label {
          font-size: 12px;
          color: var(--tech-text-secondary);
          margin-bottom: 8px;
          display: flex;
          align-items: center;
          gap: 4px;

          .help-icon {
            font-size: 14px;
            color: var(--tech-text-tertiary);
            cursor: help;

            &:hover {
              color: var(--tech-neon-blue);
            }
          }
        }

        .el-input-number {
          width: 100%;
        }

        // 覆盖数字输入框的文字颜色
        :deep(.el-input-number) {
          .el-input__wrapper {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--tech-glass-border);

            .el-input__inner {
              color: var(--tech-text-primary) !important;
              background: transparent;
            }
          }

          .el-input-number__decrease,
          .el-input-number__increase {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--tech-glass-border);
            color: var(--tech-text-secondary);

            &:hover {
              background: rgba(255, 255, 255, 0.08);
              color: var(--tech-text-primary);
            }
          }
        }

        // 针对添加了class的数字输入框
        :deep(.number-input-fix) {
          .el-input__wrapper {
            .el-input__inner {
              color: #f3f4f6 !important;
              -webkit-text-fill-color: #f3f4f6 !important;
            }
          }
        }

        :deep(.el-slider) {
          margin-top: 8px;

          .el-slider__runway {
            background: rgba(255, 255, 255, 0.1);
          }

          .el-slider__bar {
            background: linear-gradient(90deg, var(--tech-neon-blue), var(--tech-neon-purple));
          }

          .el-slider__button {
            border-color: var(--tech-neon-blue);
            background: var(--tech-glass-bg);

            &:hover {
              transform: scale(1.2);
            }
          }

          .el-slider__marks-text {
            font-size: 11px;
            color: var(--tech-text-secondary);
          }
        }
      }
    }

    .setting-actions {
      display: flex;
      gap: 12px;
      padding-top: 16px;
      border-top: 1px solid var(--tech-glass-border);

      .el-button {
        flex: 1;

        &:first-child {
          background: rgba(255, 255, 255, 0.02);
          border-color: var(--tech-glass-border);
          color: var(--tech-text-secondary);

          &:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: var(--tech-border-hover);
            color: var(--tech-text-primary);
          }
        }

        &[type="primary"] {
          background: linear-gradient(135deg, var(--tech-neon-blue), var(--tech-neon-purple));
          border: none;
          color: #fff;
          font-weight: 600;

          &:hover {
            opacity: 0.9;
            box-shadow: 0 0 12px rgba(0, 212, 255, 0.4);
          }
        }
      }
    }
  }
}
</style>
