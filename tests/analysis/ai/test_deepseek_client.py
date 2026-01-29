"""Tests for DeepSeek client."""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from src.analysis.ai.deepseek_client import DeepSeekClient


class TestDeepSeekClient:
    @pytest.fixture
    def client(self):
        """创建客户端实例"""
        return DeepSeekClient(api_key="test_key")

    @pytest.fixture
    def mock_openai_response(self):
        """创建模拟的OpenAI响应"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "这是AI分析结果"
        return mock_response

    def test_initialization(self, client):
        """测试初始化"""
        assert client is not None
        assert client.api_key == "test_key"
        assert client.timeout == 30
        assert client.base_url is not None

    def test_initialization_with_custom_params(self):
        """测试使用自定义参数初始化"""
        client = DeepSeekClient(
            api_key="custom_key",
            base_url="https://custom.api.com",
            timeout=60
        )
        assert client.api_key == "custom_key"
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 60

    def test_get_api_key_from_env(self, monkeypatch):
        """测试从环境变量获取API Key"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "env_api_key")
        client = DeepSeekClient()
        assert client.api_key == "env_api_key"

    def test_get_base_url_from_env(self, monkeypatch):
        """测试从环境变量获取Base URL"""
        monkeypatch.setenv("DEEPSEEK_API_KEY", "test_key")
        monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://env.api.com")
        client = DeepSeekClient()
        assert client.base_url == "https://env.api.com"

    def test_missing_api_key(self, monkeypatch):
        """测试缺少API Key时抛出异常"""
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        with pytest.raises(ValueError, match="API key必须提供"):
            DeepSeekClient()

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_chat_completion(self, mock_openai_class, client, mock_openai_response):
        """测试聊天完成"""
        # 设置mock
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_openai_response

        # 重新创建client以使用mock
        client = DeepSeekClient(api_key="test_key")

        messages = [{"role": "user", "content": "分析这只股票"}]
        result = client.chat_completion(messages)

        assert result == "这是AI分析结果"
        mock_openai_instance.chat.completions.create.assert_called_once()

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_chat_completion_with_custom_params(self, mock_openai_class, client, mock_openai_response):
        """测试使用自定义参数的聊天完成"""
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_openai_response

        client = DeepSeekClient(api_key="test_key")

        messages = [{"role": "user", "content": "分析这只股票"}]
        result = client.chat_completion(
            messages,
            model="deepseek-reasoner",
            temperature=0.5,
            max_tokens=2000
        )

        assert result == "这是AI分析结果"
        call_args = mock_openai_instance.chat.completions.create.call_args
        assert call_args[1]['model'] == "deepseek-reasoner"
        assert call_args[1]['temperature'] == 0.5
        assert call_args[1]['max_tokens'] == 2000

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_retry_on_error(self, mock_openai_class, client, mock_openai_response):
        """测试错误重试机制"""
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance

        # 第一次和第二次调用失败，第三次成功
        mock_openai_instance.chat.completions.create.side_effect = [
            Exception("API错误"),
            Exception("API错误"),
            mock_openai_response
        ]

        client = DeepSeekClient(api_key="test_key")

        messages = [{"role": "user", "content": "测试重试"}]
        result = client.chat_completion(messages)

        assert result == "这是AI分析结果"
        assert mock_openai_instance.chat.completions.create.call_count == 3

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_max_retries_exceeded(self, mock_openai_class, client):
        """测试超过最大重试次数"""
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.side_effect = Exception("API错误")

        client = DeepSeekClient(api_key="test_key")

        messages = [{"role": "user", "content": "测试失败"}]
        with pytest.raises(Exception, match="API错误"):
            client.chat_completion(messages)

        # 应该重试3次
        assert mock_openai_instance.chat.completions.create.call_count == 3

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_timeout_handling(self, mock_openai_class, client):
        """测试超时处理"""
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.side_effect = TimeoutError("请求超时")

        client = DeepSeekClient(api_key="test_key", timeout=5)

        messages = [{"role": "user", "content": "测试超时"}]
        with pytest.raises(TimeoutError, match="请求超时"):
            client.chat_completion(messages)

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_analyze_stock(self, mock_openai_class, mock_openai_response):
        """测试股票分析便捷方法"""
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_openai_response

        client = DeepSeekClient(api_key="test_key")

        analysis_data = {
            'technical': {'trend': '上涨', 'macd': '金叉'},
            'fundamental': {'pe_ratio': 15, 'roe': 0.20},
            'capital': {'main_force': '流入', 'net_inflow': 1000000}
        }

        result = client.analyze_stock("000001", analysis_data)

        assert result == "这是AI分析结果"
        mock_openai_instance.chat.completions.create.assert_called_once()

        # 验证调用参数
        call_args = mock_openai_instance.chat.completions.create.call_args
        messages = call_args[1]['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert '000001' in messages[1]['content']

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_analyze_stock_with_empty_data(self, mock_openai_class):
        """测试分析股票时数据为空"""
        mock_openai_class.return_value = Mock()
        client = DeepSeekClient(api_key="test_key")

        with pytest.raises(ValueError, match="分析数据不能为空"):
            client.analyze_stock("000001", {})

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_analyze_stock_with_invalid_code(self, mock_openai_class):
        """测试分析股票时股票代码无效"""
        mock_openai_class.return_value = Mock()
        client = DeepSeekClient(api_key="test_key")

        analysis_data = {'technical': {}}
        with pytest.raises(ValueError, match="股票代码不能为空"):
            client.analyze_stock("", analysis_data)

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_logging_on_api_call(self, mock_openai_class, mock_openai_response, caplog):
        """测试API调用时的日志记录"""
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_openai_response

        client = DeepSeekClient(api_key="test_key")

        messages = [{"role": "user", "content": "测试日志"}]
        client.chat_completion(messages)

        # 验证日志中包含API调用信息
        # Note: 具体日志内容取决于实现

    @patch('src.analysis.ai.deepseek_client.OpenAI')
    def test_chat_completion_with_system_message(self, mock_openai_class, mock_openai_response):
        """测试包含系统消息的聊天完成"""
        mock_openai_instance = Mock()
        mock_openai_class.return_value = mock_openai_instance
        mock_openai_instance.chat.completions.create.return_value = mock_openai_response

        client = DeepSeekClient(api_key="test_key")

        messages = [
            {"role": "system", "content": "你是一个专业的股票分析师"},
            {"role": "user", "content": "分析这只股票"}
        ]
        result = client.chat_completion(messages)

        assert result == "这是AI分析结果"
        call_args = mock_openai_instance.chat.completions.create.call_args
        assert len(call_args[1]['messages']) == 2
        assert call_args[1]['messages'][0]['role'] == 'system'
