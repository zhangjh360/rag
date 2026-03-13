"""
Reranker 服务单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.reranker_service import RerankerService, get_reranker
from app.models.document import DocumentChunk


@pytest.fixture
def mock_chunks():
    """创建模拟的文档块"""
    chunks = []
    for i in range(5):
        chunk = Mock(spec=DocumentChunk)
        chunk.id = i + 1
        chunk.document_id = 1
        chunk.chunk_index = i
        chunk.content = f"这是第 {i+1} 个测试文档块的内容,包含一些示例文本"
        chunk.metadata = {}
        chunk.namespace = "test_domain"
        chunks.append(chunk)
    return chunks


@pytest.fixture
async def reranker_service():
    """创建 Reranker 服务实例"""
    service = RerankerService(
        model_name="BAAI/bge-reranker-v2-m3",
        max_length=512,
        batch_size=32
    )
    # 不初始化模型(单元测试不需要真实模型)
    service._initialized = True
    service.model = Mock()
    return service


class TestRerankerService:
    """Reranker 服务测试"""

    def test_initialization(self):
        """测试服务初始化"""
        service = RerankerService(
            model_name="test-model",
            max_length=256,
            batch_size=16
        )

        assert service.model_name == "test-model"
        assert service.max_length == 256
        assert service.batch_size == 16
        assert service._initialized == False

    @pytest.mark.asyncio
    async def test_rerank_empty_list(self, reranker_service):
        """测试空列表重排"""
        result = await reranker_service.rerank(
            query="测试查询",
            chunks=[],
            top_k=5
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_rerank_single_chunk(self, reranker_service, mock_chunks):
        """测试单个文档块重排"""
        single_chunk = mock_chunks[:1]

        result = await reranker_service.rerank(
            query="测试查询",
            chunks=single_chunk,
            top_k=5,
            return_scores=False
        )

        assert len(result) == 1
        assert result[0] == single_chunk[0]

    @pytest.mark.asyncio
    async def test_rerank_with_scores(self, reranker_service, mock_chunks):
        """测试返回分数的重排"""
        # Mock 模型预测结果
        mock_scores = [0.9, 0.7, 0.8, 0.6, 0.5]
        reranker_service.model.predict = Mock(return_value=mock_scores)

        result = await reranker_service.rerank(
            query="测试查询",
            chunks=mock_chunks,
            top_k=3,
            return_scores=True
        )

        # 验证结果
        assert len(result) == 3
        assert all(isinstance(item, tuple) for item in result)
        assert all(len(item) == 2 for item in result)

        # 验证排序 (分数从高到低)
        scores = [score for _, score in result]
        assert scores == sorted(scores, reverse=True)
        assert result[0][1] == 0.9  # 最高分

    @pytest.mark.asyncio
    async def test_rerank_without_scores(self, reranker_service, mock_chunks):
        """测试不返回分数的重排"""
        mock_scores = [0.9, 0.7, 0.8, 0.6, 0.5]
        reranker_service.model.predict = Mock(return_value=mock_scores)

        result = await reranker_service.rerank(
            query="测试查询",
            chunks=mock_chunks,
            top_k=3,
            return_scores=False
        )

        # 验证结果
        assert len(result) == 3
        assert all(isinstance(item, Mock) for item in result)
        # 验证排序 (第一个应该是分数最高的 chunk)
        assert result[0].id == 1  # 分数 0.9 对应 chunk id=1

    @pytest.mark.asyncio
    async def test_rerank_top_k(self, reranker_service, mock_chunks):
        """测试 top_k 参数"""
        mock_scores = [0.9, 0.7, 0.8, 0.6, 0.5]
        reranker_service.model.predict = Mock(return_value=mock_scores)

        # top_k = 2
        result = await reranker_service.rerank(
            query="测试查询",
            chunks=mock_chunks,
            top_k=2
        )
        assert len(result) == 2

        # top_k = None (返回全部)
        result = await reranker_service.rerank(
            query="测试查询",
            chunks=mock_chunks,
            top_k=None
        )
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_batch_inference(self, reranker_service, mock_chunks):
        """测试批量推理"""
        mock_scores = [0.9, 0.7, 0.8, 0.6, 0.5]
        reranker_service.model.predict = Mock(return_value=mock_scores)

        # 设置较小的批量大小
        reranker_service.batch_size = 2

        result = await reranker_service.rerank(
            query="测试查询",
            chunks=mock_chunks,
            top_k=5
        )

        # 验证 predict 被调用(批量处理)
        assert reranker_service.model.predict.called

        # 验证结果长度
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_rerank_batch(self, reranker_service, mock_chunks):
        """测试批量 Rerank"""
        queries = ["查询1", "查询2", "查询3"]
        chunks_list = [mock_chunks[:3], mock_chunks[1:4], mock_chunks[2:5]]

        # Mock 分数
        reranker_service.model.predict = Mock(side_effect=[
            [0.9, 0.7, 0.8],
            [0.6, 0.5, 0.7],
            [0.8, 0.9, 0.6]
        ])

        results = await reranker_service.rerank_batch(
            queries=queries,
            chunks_list=chunks_list,
            top_k=2
        )

        # 验证结果
        assert len(results) == 3
        for result in results:
            assert len(result) == 2  # top_k=2

    @pytest.mark.asyncio
    async def test_score_pairs(self, reranker_service):
        """测试计算相关性分数"""
        pairs = [
            ("查询1", "内容1"),
            ("查询2", "内容2"),
            ("查询3", "内容3")
        ]

        mock_scores = [0.9, 0.7, 0.8]
        reranker_service.model.predict = Mock(return_value=mock_scores)

        scores = await reranker_service.score_pairs(pairs)

        assert len(scores) == 3
        assert scores == [0.9, 0.7, 0.8]

    @pytest.mark.asyncio
    async def test_error_handling(self, reranker_service, mock_chunks):
        """测试错误处理和降级"""
        # 模拟模型推理错误
        reranker_service.model.predict = Mock(side_effect=Exception("模型错误"))

        result = await reranker_service.rerank(
            query="测试查询",
            chunks=mock_chunks,
            top_k=3
        )

        # 应该返回原始结果(降级)
        assert len(result) == 3
        assert all(isinstance(item, Mock) for item in result)

    def test_ensure_initialized_error(self):
        """测试未初始化的错误"""
        service = RerankerService()
        service._initialized = False

        with pytest.raises(RuntimeError, match="Reranker 模型未初始化"):
            service._ensure_initialized()

    def test_get_model_info(self, reranker_service):
        """测试获取模型信息"""
        info = reranker_service.get_model_info()

        assert info["model_name"] == "BAAI/bge-reranker-v2-m3"
        assert info["max_length"] == 512
        assert info["batch_size"] == 32
        assert info["initialized"] == True


class TestGlobalReranker:
    """全局 Reranker 实例测试"""

    def test_get_reranker_singleton(self):
        """测试单例模式"""
        # 清除全局实例
        import app.services.reranker_service as reranker_module
        reranker_module._reranker_instance = None

        # 获取实例
        reranker1 = get_reranker()
        reranker2 = get_reranker()

        # 验证是同一个实例
        assert reranker1 is reranker2

    def test_get_reranker_parameters(self):
        """测试 get_reranker 参数"""
        import app.services.reranker_service as reranker_module
        reranker_module._reranker_instance = None

        reranker = get_reranker(
            model_name="custom-model",
            max_length=256,
            batch_size=16
        )

        assert reranker.model_name == "custom-model"
        assert reranker.max_length == 256
        assert reranker.batch_size == 16


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
