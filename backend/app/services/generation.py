import openai
from app.config.settings import OPENAI_API_KEY, CHAT_MODEL, OPENAI_API_URL
import logging
import asyncio

logger = logging.getLogger(__name__)

# 创建同步客户端
client = openai.OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_URL)

class GenerationService:
    def __init__(self):
        self.model = CHAT_MODEL
    
    async def generate_response(self, query: str, context: str) -> str:
        """
        基于上下文生成回答
        
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
            
            # 在线程池中执行同步API调用
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个智能助手，根据以下检索到的文档，用简洁的中文回答用户的问题。如果文档信息不足，请说明并提供通用回答。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"生成回答失败: {e}")
            return f"生成回答时出错: {str(e)}"

generation_service = GenerationService()