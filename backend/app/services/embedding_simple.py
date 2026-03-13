"""
简化的嵌入服务
不依赖langchain，仅使用本地计算
"""
import numpy as np
from app.config.settings import EMBEDDING_BACKEND
from app.config.logging_config import get_app_logger
from typing import List, Optional
import hashlib
import json

logger = get_app_logger()

class SimpleEmbeddingService:
    """
    简化的嵌入服务
    使用简单的哈希和模拟向量来替代真实的嵌入
    """

    def __init__(self, backend: str = "simple"):
        self.backend = backend
        logger.info(f"Embedding service initialized with backend: {backend}")

    def _text_to_vector(self, text: str) -> List[float]:
        """
        将文本转换为向量（简化版）
        使用文本的哈希值生成固定维度的向量
        """
        # 使用MD5哈希生成种子
        hash_object = hashlib.md5(text.encode())
        hash_hex = hash_object.hexdigest()

        # 生成固定长度的向量（128维）
        vector = []
        for i in range(0, len(hash_hex), 2):
            # 将16进制字符转换为0-255的值
            hex_pair = hash_hex[i:i+2]
            if len(hex_pair) == 2:
                value = int(hex_pair, 16) / 255.0  # 归一化到0-1
                vector.append(value)

        # 如果向量长度不够，重复填充
        while len(vector) < 128:
            vector.extend(vector[:min(128 - len(vector), len(vector))])

        return vector[:128]

    def embed_query(self, text: str) -> List[float]:
        """
        为查询文本生成嵌入向量
        """
        try:
            return self._text_to_vector(text)
        except Exception as e:
            logger.error(f"Error embedding query: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        为文档列表生成嵌入向量
        """
        try:
            return [self._text_to_vector(text) for text in texts]
        except Exception as e:
            logger.error(f"Error embedding documents: {e}")
            raise

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算两个向量之间的余弦相似度
        """
        try:
            # 转换为numpy数组
            a = np.array(vec1)
            b = np.array(vec2)

            # 计算余弦相似度
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

# 创建全局实例
embedding_service = SimpleEmbeddingService(backend=EMBEDDING_BACKEND or "simple")
