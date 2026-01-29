"""HTML报告生成器"""
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from src.core.logger import get_logger

logger = get_logger(__name__)


class HTMLReporter:
    """HTML格式股票分析报告生成器，生成响应式HTML报告"""

    def __init__(self):
        """初始化HTML报告生成器"""
        logger.info("Initializing HTMLReporter...")

        # 设置Jinja2模板环境
        template_dir = Path(__file__).parent / 'templates'
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(['html', 'xml']),  # 启用自动转义防止XSS
            trim_blocks=True,
            lstrip_blocks=True
        )

        logger.info(f"Template directory: {template_dir}")

    def generate_report(
        self,
        stock_code: str,
        stock_name: str,
        analysis_result: Dict[str, Any],
        save_to_file: bool = False,
        output_path: Optional[str] = None
    ) -> str:
        """
        生成HTML格式的股票分析报告

        Args:
            stock_code: 股票代码（如 "000001"）
            stock_name: 股票名称（如 "平安银行"）
            analysis_result: StockRater.analyze_stock()的结果
            save_to_file: 是否保存到文件
            output_path: 保存文件的路径

        Returns:
            HTML格式的报告字符串

        Raises:
            ValueError: 如果输出路径不安全
        """
        logger.info(f"Generating HTML report for {stock_code} {stock_name}...")

        # 准备模板数据
        template_data = self._prepare_template_data(
            stock_code, stock_name, analysis_result
        )

        # 渲染模板
        template = self.env.get_template('stock_analysis.html')
        html_content = template.render(**template_data)

        # 保存到文件
        if save_to_file:
            self._save_to_file(html_content, stock_code, output_path)

        logger.info(f"HTML report generated successfully for {stock_code}")
        return html_content

    def _prepare_template_data(
        self,
        stock_code: str,
        stock_name: str,
        analysis_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        准备模板渲染所需的数据

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            analysis_result: 分析结果

        Returns:
            模板数据字典
        """
        scores = analysis_result['scores']
        is_quick = (scores.get('fundamental', 0) == 0)

        # 评级翻译
        rating = analysis_result['rating']
        rating_cn = self._translate_rating(rating)

        # 分数等级
        technical_score = scores['technical']
        fundamental_score = scores.get('fundamental', 0.0)
        capital_score = scores['capital']
        overall_score = scores['overall']

        template_data = {
            # 基本信息
            'stock_code': stock_code,
            'stock_name': stock_name,
            'analysis_date': self._format_timestamp(),
            'current_year': datetime.now().year,
            'is_quick_mode': is_quick,

            # 评级和评分
            'rating': rating,
            'rating_cn': rating_cn,
            'confidence': analysis_result['confidence'],
            'target_price': f"{analysis_result['target_price']:.2f}",
            'stop_loss': f"{analysis_result['stop_loss']:.2f}",

            # 各维度评分
            'technical_score': f"{technical_score:.2f}",
            'fundamental_score': f"{fundamental_score:.2f}",
            'capital_score': f"{capital_score:.2f}",
            'overall_score': f"{overall_score:.2f}",

            # 评分等级CSS类
            'technical_score_class': self._get_score_class(technical_score),
            'fundamental_score_class': self._get_score_class(fundamental_score),
            'capital_score_class': self._get_score_class(capital_score),

            # 原因和风险
            'reasons': analysis_result.get('reasons', []),
            'risks': analysis_result.get('risks', []),
            'a_share_risks': analysis_result.get('a_share_risks', []),

            # AI分析
            'ai_insights': analysis_result.get('ai_insights', '暂无分析。'),
        }

        return template_data

    def _translate_rating(self, rating: str) -> str:
        """
        翻译评级为中文

        Args:
            rating: 英文评级

        Returns:
            中文评级
        """
        rating_map = {
            'buy': '买入',
            'hold': '持有',
            'sell': '卖出'
        }
        return rating_map.get(rating.lower(), rating)

    def _get_score_class(self, score: float) -> str:
        """
        根据分数获取CSS类名

        Args:
            score: 分数（0-100）

        Returns:
            CSS类名
        """
        if score >= 80:
            return 'score-excellent'
        elif score >= 65:
            return 'score-good'
        elif score >= 45:
            return 'score-fair'
        else:
            return 'score-poor'

    def _format_timestamp(self) -> str:
        """
        格式化当前时间戳

        Returns:
            格式化的时间字符串
        """
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def _save_to_file(
        self,
        html_content: str,
        stock_code: str,
        output_path: Optional[str] = None
    ) -> None:
        """
        保存HTML报告到文件

        Args:
            html_content: HTML内容
            stock_code: 股票代码
            output_path: 输出路径

        Raises:
            ValueError: 如果输出路径不安全
        """
        if output_path is None:
            # 使用默认路径
            output_path = Path.cwd() / f'stock_report_{stock_code}.html'
        else:
            output_path = Path(output_path)

        # 验证输出路径安全性
        safe_path = self._validate_output_path(str(output_path))

        # 确保父目录存在
        Path(safe_path).parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        Path(safe_path).write_text(html_content, encoding='utf-8')
        logger.info(f"HTML report saved to {safe_path}")

    def _validate_output_path(self, path: str) -> str:
        """
        验证输出路径的安全性，防止路径遍历攻击

        Args:
            path: 输出文件路径

        Returns:
            规范化后的安全路径

        Raises:
            ValueError: 如果路径不安全
        """
        if not path:
            raise ValueError("输出路径不能为空")

        # 转换为绝对路径并解析符号链接
        abs_path = Path(path).resolve()

        # 检查是否包含路径遍历
        cwd = Path.cwd().resolve()

        # 定义安全目录
        safe_dirs = [
            cwd,
            Path.home(),
            Path('/tmp').resolve(),
            Path('/var/folders').resolve() if Path('/var/folders').exists() else None,
        ]
        safe_dirs = [d for d in safe_dirs if d is not None]

        # 检查路径是否在安全目录下
        is_safe = False
        try:
            abs_path.relative_to(cwd)
            is_safe = True
        except ValueError:
            for safe_dir in safe_dirs:
                try:
                    abs_path.relative_to(safe_dir)
                    is_safe = True
                    break
                except ValueError:
                    continue

        if not is_safe:
            raise ValueError(
                f"不安全的输出路径: {path}\n"
                f"路径必须在当前工作目录、用户主目录或系统临时目录下"
            )

        # 检查文件扩展名
        allowed_extensions = {'.html', '.htm'}
        if abs_path.suffix.lower() not in allowed_extensions:
            logger.warning(
                f"不常见的文件扩展名: {abs_path.suffix}，"
                f"建议使用: {', '.join(allowed_extensions)}"
            )

        return str(abs_path)
