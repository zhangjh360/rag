"""
LLM服务 - 处理与大语言模型的交互
支持多个提供商动态初始化
"""
import os
import json
import asyncio
from typing import List, Dict, Any, AsyncGenerator, Optional
from openai import AsyncOpenAI
import anthropic
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.config.settings import get_settings
from app.models.chat import ChatMessage
from app.models.llm_models import LLMModel

settings = get_settings()

class LLMService:
    """LLM服务类 - 支持多模型动态初始化"""

    def __init__(self, db: Optional[Session] = None):
        """初始化LLM服务"""
        self.db = db
        # 缓存客户端，避免重复创建
        self._clients = {}
        self.default_model = "GLM-4-Flash-250414" #"gpt-3.5-turbo"

    def _get_client_for_model(self, model_name: str) -> tuple:
        """
        根据模型名称获取对应的客户端

        Returns:
            tuple: (client, model_name, provider)
        """
        # 如果有数据库配置，优先从数据库获取
        if self.db:
            model_config = self.db.execute(
                select(LLMModel).where(LLMModel.name == model_name, LLMModel.is_active == True)
            ).scalar_one_or_none()

            if model_config:
                provider = model_config.provider
                actual_model_name = model_config.model_name
                api_key = model_config.api_key or os.getenv(f"{provider.upper()}_API_KEY")
                base_url = model_config.base_url

                # 生成客户端缓存键
                cache_key = f"{provider}:{model_name}"

                if cache_key not in self._clients:
                    if provider.lower() == "openai":
                        client = AsyncOpenAI(
                            api_key=str(api_key),
                            base_url=base_url or os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
                        )
                    elif provider.lower() == "anthropic":
                        client = anthropic.Anthropic(
                            api_key=api_key,
                            base_url=base_url or os.getenv("ANTHROPIC_API_BASE", "https://api.anthropic.com/v1")
                        )
                    else:   
                        # 为其他提供商预留扩展
                        client = AsyncOpenAI(
                            api_key=api_key,
                            base_url=base_url
                        )

                    self._clients[cache_key] = client

                return self._clients[cache_key], actual_model_name, provider

        # 默认回退到环境变量配置
        cache_key = f"openai:{model_name}"
        if cache_key not in self._clients:
            self._clients[cache_key] = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY"),
                base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            )

        return self._clients[cache_key], model_name, "openai"

    async def get_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        获取LLM响应（非流式）
        """
        try:
            # 获取模型对应的客户端
            model_name = model or self.default_model
            client, actual_model, provider = self._get_client_for_model(model_name)

            # 调用对应提供商的API
            if provider.lower() == "openai":
                response = await client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                return {
                    "content": response.choices[0].message.content,
                    "tokens_used": response.usage.total_tokens,
                    "model": response.model
                }
            elif provider.lower() == "anthropic":
                # Anthropic 提供商暂不支持非流式
                raise ValueError(f"Anthropic 提供商请使用流式接口")
            else:
                # 其他提供商(如 custom)默认使用 OpenAI 协议
                response = await client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=False
                )

                return {
                    "content": response.choices[0].message.content,
                    "tokens_used": response.usage.total_tokens,
                    "model": response.model
                }

        except Exception as e:
            print(f"LLM completion error: {e}")
            raise

    async def stream_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        session_id: str = None,
        db = None
    ) -> AsyncGenerator[str, None]:
        """
        流式生成LLM响应
        """
        try:
            # 获取模型对应的客户端
            model_name = model or self.default_model
            client, actual_model, provider = self._get_client_for_model(model_name)

            # 调用对应提供商的API
            if provider.lower() == "openai":
                stream = await client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
            elif provider.lower() == "anthropic":
                message = client.messages.create(
                    model=actual_model,
                    max_tokens=max_tokens,
                    #system="You are a helpful assistant.",
                    messages= messages,
                    temperature=temperature,
                    stream=False
                )

            else:
                 # 为其他提供商预留扩展
                 # 默认使用OpenAI的流式接口
                stream = await client.chat.completions.create(
                    model=actual_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True
                )
                # raise ValueError(f"不支持的提供商: {provider}")

            full_response = ""
            if provider.lower() == "openai":
                  async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        # 发送SSE格式的数据
                        yield f"data: {json.dumps({'content': content, 'type': 'content'})}\n\n"


            elif provider.lower() == "anthropic":
                for block in message.content:
                    if block.type == "thinking":
                        full_response += block.thinking
                        yield f"data: {json.dumps({'content': block.thinking, 'type': 'thinking'})}\n\n"
                    elif block.type == "text":
                        full_response += block.text
                        # 发送SSE格式的数据
                        yield f"data: {json.dumps({'content': block.text, 'type': 'content'})}\n\n"
            else:
                async for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        # 发送SSE格式的数据
                        yield f"data: {json.dumps({'content': content, 'type': 'content'})}\n\n"

            # 保存完整响应到数据库
            if session_id and db:
                assistant_message = ChatMessage(
                    session_id=session_id,
                    role="assistant",
                    content=full_response,
                    metadata={
                        "model": model_name,
                        "temperature": temperature
                    }
                )
                db.add(assistant_message)
                db.commit()

            # 发送结束信号
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            print(f"Stream completion error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    async def get_embeddings(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """
        获取文本的向量嵌入
        """
        try:
            # 获取默认的OpenAI客户端
            client, _, _ = self._get_client_for_model("gpt-3.5-turbo")
            response = await client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embeddings error: {e}")
            raise

    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数量
        简单估算：平均每4个字符约等于1个token
        """
        return len(text) // 4

    async def summarize_text(self, text: str, max_length: int = 100) -> str:
        """
        文本摘要生成
        """
        messages = [
            {"role": "system", "content": "你是一个专业的文本摘要助手。"},
            {"role": "user", "content": f"请将以下文本总结为不超过{max_length}字的摘要：\n\n{text}"}
        ]

        response = await self.get_completion(
            messages=messages,
            temperature=0.3,
            max_tokens=max_length * 2
        )

        return response["content"]

    async def generate_session_title(self, first_message: str, model: str = None) -> str:
        """
        根据第一条消息生成会话标题

        Args:
            first_message: 用户的第一条消息
            model: 使用的模型,默认使用当前默认模型

        Returns:
            生成的会话标题
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            prompt = f"""请根据用户的问题,生成一个简短、准确的对话标题。

要求:
1. 长度控制在8-25个汉字
2. 准确概括用户问题的核心内容
3. 使用简洁明了的语言
4. 不要包含标点符号、引号、emoji
5. 只返回标题文本,不要有任何解释或额外内容

示例:
用户: "Python中如何实现异步编程?"
标题: Python异步编程实现

用户: "RAG系统的架构设计有哪些要点?"
标题: RAG系统架构设计

现在,请为以下问题生成标题:
用户问题: {first_message}

标题:"""

            messages = [
                {"role": "user", "content": prompt}
            ]

            response = await self.get_completion(
                messages=messages,
                model=model or self.default_model,
                temperature=0.3,  # 降低温度以获得更确定的结果
                max_tokens=60
            )

            title = response.get("content", "").strip()

            # 清理标题: 去除引号、多余空格等
            title = title.replace('"', '').replace("'", '').replace('「', '').replace('」', '').strip()

            # 去除可能的"标题:"前缀
            if title.startswith("标题:") or title.startswith("标题："):
                title = title[3:].strip()

            # 限制长度
            if len(title) > 30:
                title = title[:30]
            elif len(title) < 2:
                # 标题太短,使用用户消息前缀
                title = first_message[:20]

            logger.info(f"生成会话标题成功: {title}")
            return title

        except Exception as e:
            logger.error(f"生成会话标题失败: {e}")
            # 失败时返回用户消息的前20个字符
            fallback_title = first_message[:20] if len(first_message) > 20 else first_message
            return fallback_title