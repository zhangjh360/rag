"""
查询重写服务
基于聊天历史,将含有代词和省略成分的查询改写为完整查询
"""

import json
import logging
from typing import List, Dict, Tuple, Optional

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class QueryRewriter:
    """
    查询重写器

    功能:
    - 检测查询中的代词和省略成分
    - 基于聊天历史补全上下文
    - 生成独立、完整的查询语句

    示例:
    - 原查询: "是的"
    - 历史: "您是否需要我提供更多关于他特定技能或项目的详细信息?"
    - 重写后: "是的,请提供张建红的特定技能和项目详细信息"
    """

    def __init__(self, llm_service: LLMService):
        """
        初始化查询重写器

        Args:
            llm_service: LLM服务实例
        """
        self.llm_service = llm_service

    async def rewrite_with_context(
        self,
        current_query: str,
        chat_history: List[Dict[str, str]],
        max_history: int = 5
    ) -> Tuple[str, bool]:
        """
        基于聊天历史重写查询

        Args:
            current_query: 当前用户查询
            chat_history: 聊天历史列表,格式: [{"role": "user", "content": "..."}, ...]
            max_history: 最多使用的历史消息数量(默认5轮)

        Returns:
            (rewritten_query, was_rewritten)
            - rewritten_query: 重写后的查询(如果不需要重写则返回原查询)
            - was_rewritten: 是否进行了重写
        """
        try:
            # 快速判断:如果查询很长且完整,可能不需要重写
            if len(current_query) > 20 and self._looks_complete(current_query):
                logger.debug(f"查询看起来已完整,跳过重写: {current_query}")
                return current_query, False

            # 准备历史上下文(最近的max_history轮对话)
            recent_history = chat_history[-max_history*2:] if chat_history else []

            if not recent_history:
                logger.debug("没有历史上下文,无需重写")
                return current_query, False

            # 格式化历史对话
            history_text = self._format_chat_history(recent_history)

            # 构建重写提示词
            prompt = f"""你是一个智能查询重写助手。用户在多轮对话中提出了新问题,请结合对话历史,将当前查询改写为完整、独立、可直接用于知识库检索的查询。

对话历史:
{history_text}

当前查询: "{current_query}"

请分析:
1. 当前查询是否包含代词(我、他、它、这个、那个等)或省略成分?
2. 当前查询是否是对上一轮助手提问的回应(如"是的"、"对"、"可以"、"不用"等)?
3. 如果是,请结合历史补全为完整查询;如果查询已经完整独立,直接返回原查询

重写原则:
- 保留原查询的意图和语气
- 补充代词指代的具体对象(人名、事物等)
- 将确认性回复("是的"、"对")扩展为明确的需求陈述
- 避免过度扩展,只补充必要的上下文
- 改写后的查询应该可以独立理解,不依赖历史

返回JSON格式:
{{
  "rewritten_query": "改写后的完整查询",
  "was_rewritten": true/false,
  "reasoning": "是否重写的理由(1-2句话)"
}}

示例1:
历史: "助手: 张建红的到岗时间为一周内...您是否需要我提供更多关于他特定技能或项目的详细信息?"
当前: "是的"
正确返回:
{{
  "rewritten_query": "是的,请提供张建红的特定技能和项目详细信息",
  "was_rewritten": true,
  "reasoning": "当前查询是对助手提问的确认回复,需要补全具体需求"
}}

示例2:
历史: "用户: 我是Python后端工程师,有5年经验"
当前: "我还做过什么项目?"
正确返回:
{{
  "rewritten_query": "作为Python后端工程师,我还做过什么项目?",
  "was_rewritten": true,
  "reasoning": "当前查询包含代词'我',需要补充上下文信息"
}}

示例3:
历史: "..."
当前: "FastAPI的依赖注入是如何工作的?"
正确返回:
{{
  "rewritten_query": "FastAPI的依赖注入是如何工作的?",
  "was_rewritten": false,
  "reasoning": "查询已经完整独立,无需重写"
}}
"""

            # 调用LLM
            response = await self.llm_service.get_completion(
                messages=[
                    {"role": "system", "content": "你是一个专业的查询重写助手,负责将多轮对话中的不完整查询改写为独立完整的查询。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 较低温度保证稳定性
                max_tokens=300
            )

            # 解析响应
            content = response['content'].strip()

            # 清理可能的markdown格式
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            # 解析JSON
            result = json.loads(content)

            rewritten_query = result.get('rewritten_query', current_query)
            was_rewritten = result.get('was_rewritten', False)
            reasoning = result.get('reasoning', '')

            if was_rewritten:
                logger.info(
                    f"查询重写成功: '{current_query}' → '{rewritten_query}' "
                    f"(原因: {reasoning})"
                )
            else:
                logger.debug(f"查询无需重写: {current_query} (原因: {reasoning})")

            return rewritten_query, was_rewritten

        except json.JSONDecodeError as e:
            logger.warning(f"解析查询重写结果失败: {e}, 使用原查询")
            return current_query, False

        except Exception as e:
            logger.error(f"查询重写失败: {e}", exc_info=True)
            # 降级: 返回原查询
            return current_query, False

    def _format_chat_history(self, history: List[Dict[str, str]]) -> str:
        """
        格式化聊天历史为文本

        Args:
            history: 历史消息列表

        Returns:
            格式化的历史文本
        """
        formatted = []
        for msg in history:
            role = "用户" if msg['role'] == 'user' else "助手"
            content = msg['content']
            # 限制每条消息长度,避免prompt过长
            if len(content) > 200:
                content = content[:200] + "..."
            formatted.append(f"{role}: {content}")

        return "\n".join(formatted)

    def _looks_complete(self, query: str) -> bool:
        """
        快速判断查询是否看起来已经完整

        启发式规则:
        - 长度 > 20 且包含问号
        - 包含完整的主谓宾结构(简单检测)
        - 不包含明显的代词开头("我"、"他"除外,因为可能是主语)

        Args:
            query: 查询文本

        Returns:
            是否看起来完整
        """
        # 非常短的查询大概率不完整
        if len(query) < 10:
            return False

        # 常见的不完整查询模式
        incomplete_patterns = [
            '是的', '对', '可以', '不用', '好', '嗯', '继续',
            '还有吗', '然后呢', '接着', '下一个'
        ]

        if query.strip() in incomplete_patterns:
            return False

        # 如果查询足够长且包含问号或句号,认为可能完整
        if len(query) > 15 and ('?' in query or '?' in query or '。' in query):
            return True

        return False


def get_query_rewriter(llm_service: LLMService) -> QueryRewriter:
    """
    工厂函数:获取QueryRewriter实例

    Args:
        llm_service: LLM服务实例

    Returns:
        QueryRewriter实例
    """
    return QueryRewriter(llm_service=llm_service)
