"""
异步版本的生成服务
使用异步OpenAI客户端，性能更好
"""

import openai
from app.config.settings import OPENAI_API_KEY, CHAT_MODEL, OPENAI_API_URL
import logging

logger = logging.getLogger(__name__)

# 创建异步客户端
async_client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_URL)

class AsyncGenerationService:
    """异步生成服务类"""
    
    def __init__(self):
        self.model = CHAT_MODEL
    
    async def generate_response(self, query: str, context: str) -> str:
        """
        基于上下文生成回答（异步版本）
        
        Args:
            query (str): 用户问题
            context (str): 相关上下文
            
        Returns:
            str: 生成的回答
        """
        try:
            prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请说明你无法从提供的上下文中找到答案。

上下文:
{context}

问题: {query}

请提供详细的回答:"""
            
            # 使用异步客户端直接调用
            response = await async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个智能助手，基于提供的上下文信息回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"生成回答失败: {e}")
            return f"生成回答时出错: {str(e)}"
    
    async def generate_response_with_streaming(self, query: str, context: str):
        """
        流式生成回答（用于实时显示）
        
        Args:
            query (str): 用户问题
            context (str): 相关上下文
            
        Yields:
            str: 回答的片段
        """
        try:
            prompt = f"""基于以下上下文回答问题。如果上下文中没有相关信息，请说明你无法从提供的上下文中找到答案。

上下文:
{context}

问题: {query}

请提供详细的回答:"""
            
            # 流式响应
            stream = await async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个智能助手，基于提供的上下文信息回答问题。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"流式生成回答失败: {e}")
            yield f"生成回答时出错: {str(e)}"

# 创建异步生成服务的全局实例
async_generation_service = AsyncGenerationService()
