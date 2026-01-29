"""DeepSeek AI客户端模块"""
import os
import time
from typing import List, Dict, Any, Optional
from openai import OpenAI
from src.core.config_manager import ConfigManager
from src.core.logger import get_logger

logger = get_logger(__name__)


class DeepSeekClient:
    """DeepSeek AI客户端，封装API调用"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化DeepSeek客户端

        Args:
            api_key: API密钥，如果为None则从环境变量DEEPSEEK_API_KEY获取
            base_url: API基础URL，如果为None则从配置或环境变量DEEPSEEK_BASE_URL获取
            timeout: 请求超时时间（秒），默认30秒

        Raises:
            ValueError: 当API key无法获取时
        """
        # 获取API key
        self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
        if not self.api_key:
            raise ValueError("API key必须提供，可以通过参数传入或设置环境变量DEEPSEEK_API_KEY")

        # 获取base_url
        config = ConfigManager()
        self.base_url = (
            base_url
            or os.getenv('DEEPSEEK_BASE_URL')
            or config.get('ai.base_url', 'https://api.deepseek.com')
        )

        self.timeout = timeout

        # 从配置读取默认参数
        self.default_model = config.get('ai.model', 'deepseek-chat')
        self.default_temperature = config.get('ai.temperature', 0.7)
        self.default_max_tokens = config.get('ai.max_tokens', 4000)

        # 初始化OpenAI客户端（DeepSeek API兼容OpenAI接口）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )

        logger.info(f"DeepSeek客户端初始化成功，base_url={self.base_url}")

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 3
    ) -> str:
        """
        调用聊天完成接口

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            model: 模型名称，默认从配置读取
            temperature: 温度参数（0-1），控制随机性，默认从配置读取
            max_tokens: 最大token数，默认从配置读取
            max_retries: 最大重试次数，默认3次

        Returns:
            AI生成的文本内容

        Raises:
            Exception: API调用失败且超过最大重试次数
            TimeoutError: 请求超时
        """
        # 使用默认值
        model = model or self.default_model
        temperature = temperature if temperature is not None else self.default_temperature
        max_tokens = max_tokens or self.default_max_tokens

        logger.info(f"调用DeepSeek API: model={model}, messages_count={len(messages)}")

        last_exception = None
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                content = response.choices[0].message.content
                logger.info(f"DeepSeek API调用成功，返回内容长度={len(content)}")
                return content

            except TimeoutError as e:
                logger.error(f"DeepSeek API请求超时: {e}")
                raise

            except Exception as e:
                last_exception = e
                logger.warning(f"DeepSeek API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    # 指数退避重试
                    sleep_time = 2 ** attempt
                    logger.info(f"等待{sleep_time}秒后重试...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"DeepSeek API调用失败，已达最大重试次数")

        # 所有重试都失败
        raise last_exception

    def analyze_stock(
        self,
        stock_code: str,
        analysis_data: Dict[str, Any],
        model: Optional[str] = None
    ) -> str:
        """
        分析股票（便捷方法）

        Args:
            stock_code: 股票代码
            analysis_data: 分析数据字典，包含技术面、基本面、资金面等数据
            model: 使用的模型，默认使用配置中的模型

        Returns:
            AI分析结果文本

        Raises:
            ValueError: 当股票代码为空或分析数据为空时
        """
        if not stock_code:
            raise ValueError("股票代码不能为空")

        if not analysis_data:
            raise ValueError("分析数据不能为空")

        logger.info(f"开始分析股票 {stock_code}")

        # 构造分析prompt
        prompt = self._build_analysis_prompt(stock_code, analysis_data)

        # 调用chat_completion
        messages = [
            {
                "role": "system",
                "content": "你是一个专业的A股分析师，擅长综合技术面、基本面、资金面等多维度数据进行股票分析。请基于提供的数据给出专业的分析意见。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        result = self.chat_completion(messages, model=model)
        logger.info(f"股票 {stock_code} 分析完成")

        return result

    def _build_analysis_prompt(self, stock_code: str, analysis_data: Dict[str, Any]) -> str:
        """
        构建分析提示词

        Args:
            stock_code: 股票代码
            analysis_data: 分析数据

        Returns:
            构建好的prompt
        """
        prompt_parts = [f"请分析股票 {stock_code}，以下是相关数据：\n"]

        # 技术面分析
        if 'technical' in analysis_data and analysis_data['technical']:
            prompt_parts.append("\n## 技术面分析")
            for key, value in analysis_data['technical'].items():
                prompt_parts.append(f"- {key}: {value}")

        # 基本面分析
        if 'fundamental' in analysis_data and analysis_data['fundamental']:
            prompt_parts.append("\n## 基本面分析")
            for key, value in analysis_data['fundamental'].items():
                prompt_parts.append(f"- {key}: {value}")

        # 资金面分析
        if 'capital' in analysis_data and analysis_data['capital']:
            prompt_parts.append("\n## 资金面分析")
            for key, value in analysis_data['capital'].items():
                prompt_parts.append(f"- {key}: {value}")

        # 其他数据
        for section_name, section_data in analysis_data.items():
            if section_name not in ['technical', 'fundamental', 'capital'] and section_data:
                prompt_parts.append(f"\n## {section_name}")
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        prompt_parts.append(f"- {key}: {value}")
                else:
                    prompt_parts.append(f"- {section_data}")

        prompt_parts.append("\n请基于以上数据，给出专业的分析意见和投资建议。")

        return "\n".join(prompt_parts)
