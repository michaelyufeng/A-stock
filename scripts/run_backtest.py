#!/usr/bin/env python
"""
策略回测脚本

使用BacktestEngine运行策略回测，支持自定义参数和结果导出。

用法:
    python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01
    python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --end 2023-12-31
    python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --plot
    python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --output report.txt
"""

import argparse
import sys
import os
import re
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Type, Tuple

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data.akshare_provider import AKShareProvider
from src.backtest.engine import BacktestEngine
from src.strategy.base_strategy import BaseStrategy
from src.strategy.short_term.momentum import MomentumStrategy
from src.core.logger import get_logger
from src.core.constants import DEFAULT_CAPITAL

logger = get_logger(__name__)

# 常量定义
MIN_CAPITAL = 10000.0  # 最小初始资金 10,000 元
MAX_CAPITAL = 100000000.0  # 最大初始资金 1 亿元
MIN_DATE = datetime(2000, 1, 1)  # 最早支持的日期
STOCK_CODE_PATTERN = re.compile(r'^\d{6}$')  # A股代码格式: 6位数字

# 策略映射表
STRATEGY_MAP = {
    'momentum': MomentumStrategy,
    # 可以在这里添加更多策略
    # 'value': ValueStrategy,
    # 'breakout': BreakoutStrategy,
}


def validate_stock_code(code: str) -> bool:
    """
    验证A股股票代码格式

    Args:
        code: 股票代码

    Returns:
        True表示格式正确，False表示格式错误
    """
    if not code or not isinstance(code, str):
        return False
    return STOCK_CODE_PATTERN.match(code) is not None


def validate_capital(capital: float) -> None:
    """
    验证初始资金参数

    Args:
        capital: 初始资金

    Raises:
        ValueError: 如果资金参数无效
    """
    if capital < MIN_CAPITAL:
        raise ValueError(
            f"初始资金不能低于 {MIN_CAPITAL:,.0f} 元"
        )
    if capital > MAX_CAPITAL:
        raise ValueError(
            f"初始资金不能超过 {MAX_CAPITAL:,.0f} 元"
        )


def validate_output_path(path: str) -> str:
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

    # 定义安全目录（包括它们的实际路径）
    safe_dirs = [
        cwd,
        Path.home(),
        Path('/tmp').resolve(),  # 解析符号链接
        Path('/var/folders').resolve() if Path('/var/folders').exists() else None,  # macOS临时目录
    ]
    # 过滤掉None值
    safe_dirs = [d for d in safe_dirs if d is not None]

    # 检查路径是否在安全目录下
    is_safe = False
    try:
        # 首先尝试检查是否在当前目录下
        abs_path.relative_to(cwd)
        is_safe = True
    except ValueError:
        # 如果不在当前目录下，检查是否在其他安全目录下
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

    # 检查文件扩展名（可选的额外安全检查）
    allowed_extensions = {'.txt', '.png', '.jpg', '.jpeg', '.pdf', '.csv', '.json'}
    if abs_path.suffix.lower() not in allowed_extensions:
        logger.warning(
            f"不常见的文件扩展名: {abs_path.suffix}，"
            f"建议使用: {', '.join(allowed_extensions)}"
        )

    # 确保父目录存在
    parent = abs_path.parent
    if not parent.exists():
        raise ValueError(f"输出目录不存在: {parent}")

    return str(abs_path)


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数

    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description='A股策略回测工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本回测
  python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01

  # 指定结束日期
  python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --end 2023-12-31

  # 自定义初始资金
  python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --capital 500000

  # 生成图表
  python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --plot

  # 导出结果
  python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01 --output report.txt

支持的策略: {}
        """.format(', '.join(STRATEGY_MAP.keys()))
    )

    parser.add_argument(
        '--strategy',
        required=True,
        choices=list(STRATEGY_MAP.keys()),
        help='策略名称'
    )

    parser.add_argument(
        '--code',
        required=True,
        help='股票代码（如: 600519）'
    )

    parser.add_argument(
        '--start',
        required=True,
        help='回测开始日期（格式: YYYY-MM-DD）'
    )

    parser.add_argument(
        '--end',
        help='回测结束日期（格式: YYYY-MM-DD），默认为今天'
    )

    parser.add_argument(
        '--capital',
        type=float,
        default=DEFAULT_CAPITAL,
        help=f'初始资金（默认: {DEFAULT_CAPITAL:,.0f}）'
    )

    parser.add_argument(
        '--plot',
        action='store_true',
        help='生成可视化图表'
    )

    parser.add_argument(
        '--output',
        help='导出结果报告到文件'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细输出'
    )

    return parser.parse_args()


def validate_date_format(date_str: str) -> bool:
    """
    验证日期格式和范围

    Args:
        date_str: 日期字符串

    Returns:
        True表示格式正确且在有效范围内，False表示格式错误或超出范围
    """
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')

        # 验证日期范围
        if date < MIN_DATE:
            logger.warning(f"日期早于支持的最早日期 {MIN_DATE.strftime('%Y-%m-%d')}: {date_str}")
            return False

        if date > datetime.now():
            logger.warning(f"日期晚于今天: {date_str}")
            return False

        return True
    except ValueError:
        return False


def validate_date_range(start_date: str, end_date: str):
    """
    验证日期范围

    Args:
        start_date: 开始日期
        end_date: 结束日期

    Raises:
        ValueError: 如果日期范围无效
    """
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')

    if start >= end:
        raise ValueError(f"开始日期必须早于结束日期: {start_date} >= {end_date}")


def get_default_dates() -> tuple:
    """
    获取默认日期范围（最近一年）

    Returns:
        (start_date, end_date) 元组
    """
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    return start_date, end_date


def get_strategy_class(strategy_name: str) -> Type[BaseStrategy]:
    """
    根据策略名称获取策略类

    Args:
        strategy_name: 策略名称

    Returns:
        策略类

    Raises:
        ValueError: 如果策略不存在
    """
    if strategy_name not in STRATEGY_MAP:
        available = ', '.join(STRATEGY_MAP.keys())
        raise ValueError(
            f"不支持的策略: {strategy_name}\n"
            f"可用策略: {available}"
        )

    return STRATEGY_MAP[strategy_name]


def fetch_backtest_data(code: str, start_date: str, end_date: str) -> Any:
    """
    获取回测数据

    Args:
        code: 股票代码
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        K线数据DataFrame

    Raises:
        ValueError: 如果数据为空
        Exception: 如果数据获取失败
    """
    logger.info(f"获取股票数据: {code} ({start_date} ~ {end_date})")

    try:
        provider = AKShareProvider()

        # 转换日期格式 (YYYY-MM-DD -> YYYYMMDD)
        start_akshare = start_date.replace('-', '')
        end_akshare = end_date.replace('-', '')

        # 获取数据
        data = provider.get_daily_kline(
            code=code,
            start_date=start_akshare,
            end_date=end_akshare,
            adjust='qfq'  # 前复权
        )

        if data is None or len(data) == 0:
            raise ValueError(
                f"未获取到数据: {code}\n"
                f"请检查股票代码是否正确，或日期范围是否有效"
            )

        logger.info(f"成功获取 {len(data)} 条K线数据")

        # 数据不足警告
        if len(data) < 30:
            logger.warning(
                f"数据量较少（{len(data)}条），可能影响回测准确性。"
                f"建议使用至少30天以上的数据。"
            )

        return data

    except Exception as e:
        logger.error(f"数据获取失败: {e}")
        raise


def run_backtest(
    strategy: str,
    code: str,
    start: str,
    end: Optional[str] = None,
    capital: float = DEFAULT_CAPITAL
) -> Tuple[Dict[str, Any], Optional[BacktestEngine]]:
    """
    运行回测

    Args:
        strategy: 策略名称
        code: 股票代码
        start: 开始日期
        end: 结束日期（可选）
        capital: 初始资金

    Returns:
        (回测结果字典, 回测引擎实例) 元组

    Raises:
        ValueError: 如果参数无效
        Exception: 如果回测失败
    """
    # 验证股票代码格式
    if not validate_stock_code(code):
        raise ValueError(
            f"无效的股票代码: {code}\n"
            f"A股代码必须是6位数字（如: 600519）"
        )

    # 验证初始资金
    validate_capital(capital)

    # 使用默认结束日期
    if end is None:
        end = datetime.now().strftime('%Y-%m-%d')

    # 验证日期格式
    if not validate_date_format(start):
        raise ValueError(f"开始日期格式错误或超出范围: {start}，应为YYYY-MM-DD且不早于2000年")
    if not validate_date_format(end):
        raise ValueError(f"结束日期格式错误或超出范围: {end}，应为YYYY-MM-DD且不晚于今天")

    # 验证日期范围
    validate_date_range(start, end)

    # 获取策略类
    strategy_class = get_strategy_class(strategy)

    # 获取数据
    data = fetch_backtest_data(code, start, end)

    # 创建回测引擎
    engine = BacktestEngine(initial_cash=capital)

    # 运行回测
    logger.info("=" * 60)
    logger.info(f"开始回测: {strategy} @ {code}")
    logger.info(f"日期范围: {start} ~ {end}")
    logger.info(f"初始资金: ¥{capital:,.0f}")
    logger.info("=" * 60)

    result = engine.run_backtest(
        strategy_class=strategy_class,
        data=data,
        start_date=start,
        end_date=end,
        stock_code=code
    )

    # 返回结果和引擎实例（分离而不是混在一起）
    return result, engine


def format_results(result: Dict[str, Any], verbose: bool = True) -> str:
    """
    格式化回测结果

    Args:
        result: 回测结果字典
        verbose: 是否显示详细信息

    Returns:
        格式化的字符串
    """
    lines = []
    lines.append("")
    lines.append("=" * 70)
    lines.append("                        回测结果摘要")
    lines.append("=" * 70)

    # 基本信息
    lines.append(f"初始资金: ¥{result['initial_value']:,.2f}")
    lines.append(f"最终资金: ¥{result['final_value']:,.2f}")
    lines.append(f"总收益率: {result['total_return']:.2%}")

    # 风险指标
    lines.append("-" * 70)
    lines.append(f"夏普比率: {result['sharpe_ratio']:.4f}")
    lines.append(f"最大回撤: {result['max_drawdown']:.2%}")

    # 交易统计
    lines.append("-" * 70)
    lines.append(f"总交易次数: {result['total_trades']}")
    lines.append(f"胜率: {result['win_rate']:.2%}")

    # 详细指标（verbose模式）
    if verbose and 'metrics' in result:
        metrics = result['metrics']
        lines.append("-" * 70)
        lines.append("详细指标:")
        lines.append(f"  年化收益: {metrics.get('annual_return', 0):.2%}")
        lines.append(f"  波动率: {metrics.get('volatility', 0):.2%}")
        lines.append(f"  索提诺比率: {metrics.get('sortino_ratio', 0):.4f}")
        lines.append(f"  Calmar比率: {metrics.get('calmar_ratio', 0):.4f}")
        lines.append(f"  盈亏比: {metrics.get('profit_loss_ratio', 0):.2f}")
        lines.append(f"  平均持仓: {metrics.get('avg_holding_days', 0):.1f}天")
        lines.append(f"  最大连胜: {metrics.get('max_consecutive_wins', 0)}次")
        lines.append(f"  最大连亏: {metrics.get('max_consecutive_losses', 0)}次")
        lines.append(f"  总费用: ¥{metrics.get('total_fees', 0):,.2f}")
        lines.append(f"  费用占比: {metrics.get('fee_percentage', 0):.2%}")

    lines.append("=" * 70)

    return "\n".join(lines)


def save_results(result: Dict[str, Any], output_path: str, verbose: bool = False):
    """
    保存结果到文件

    Args:
        result: 回测结果
        output_path: 输出文件路径
        verbose: 是否显示详细错误信息

    Raises:
        ValueError: 如果输出路径不安全
    """
    # 验证输出路径
    safe_path = validate_output_path(output_path)

    try:
        with open(safe_path, 'w', encoding='utf-8') as f:
            # 写入摘要
            if 'summary' in result and result['summary']:
                f.write(result['summary'])
                f.write("\n\n")

            # 写入格式化结果
            f.write(format_results(result, verbose=True))

            # 写入交易记录
            if 'trades' in result and len(result['trades']) > 0:
                f.write("\n\n")
                f.write("=" * 70)
                f.write("\n                        交易记录\n")
                f.write("=" * 70)
                f.write("\n")

                for i, trade in enumerate(result['trades'], 1):
                    f.write(f"\n交易 #{i}:\n")
                    for key, value in trade.items():
                        f.write(f"  {key}: {value}\n")

        logger.info(f"结果已保存至: {safe_path}")
        print(f"\n[OK] 结果已保存至: {safe_path}")

    except Exception as e:
        logger.error(f"保存结果失败: {e}")
        print(f"\n[ERROR] 保存结果失败: {e}")
        if verbose:
            traceback.print_exc()
        raise


def plot_backtest_results(engine: BacktestEngine, output_path: str, verbose: bool = False):
    """
    绘制回测结果图表

    Args:
        engine: 回测引擎实例
        output_path: 输出图表路径
        verbose: 是否显示详细错误信息

    Raises:
        ValueError: 如果输出路径不安全
    """
    # 验证输出路径
    safe_path = validate_output_path(output_path)

    try:
        engine.plot_results(safe_path)
        logger.info(f"图表已保存至: {safe_path}")
        print(f"\n[OK] 图表已保存至: {safe_path}")
    except Exception as e:
        logger.error(f"绘制图表失败: {e}")
        print(f"\n[ERROR] 绘制图表失败: {e}")
        if verbose:
            traceback.print_exc()
        raise


def main():
    """主函数"""
    # 解析参数
    args = parse_arguments()

    # 打印欢迎信息
    print("=" * 70)
    print("                   A股策略回测系统")
    print("=" * 70)
    print(f"策略: {args.strategy}")
    print(f"股票: {args.code}")
    print(f"开始日期: {args.start}")
    print(f"结束日期: {args.end or '今天'}")
    print(f"初始资金: ¥{args.capital:,.0f}")
    print("=" * 70)
    print()

    try:
        # 运行回测（返回结果和引擎实例）
        result, engine = run_backtest(
            strategy=args.strategy,
            code=args.code,
            start=args.start,
            end=args.end,
            capital=args.capital
        )

        # 显示结果
        print(format_results(result, verbose=args.verbose))

        # 导出结果
        if args.output:
            save_results(result, args.output, verbose=args.verbose)

        # 生成图表
        if args.plot:
            chart_path = args.output.replace('.txt', '.png') if args.output else 'backtest_chart.png'
            plot_backtest_results(engine, chart_path, verbose=args.verbose)

        print("\n[OK] 回测完成")

    except ValueError as e:
        print(f"\n[ERROR] 参数错误: {e}")
        logger.error(f"参数错误: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    except Exception as e:
        print(f"\n[ERROR] 回测失败: {e}")
        logger.error(f"回测失败: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
