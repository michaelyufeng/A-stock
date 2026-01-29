#!/usr/bin/env python
"""
批量筛选股票脚本

使用StockScreener进行批量筛选，支持预设筛选条件和结果导出。

用法:
    python scripts/run_screening.py --preset strong_momentum --top 20
    python scripts/run_screening.py --preset value_growth --top 50 --output results.csv
    python scripts/run_screening.py --preset capital_inflow --min-score 70 --output results.xlsx
"""

import argparse
import sys
import os
import traceback
import re
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.screening.screener import StockScreener
from src.core.logger import get_logger

logger = get_logger(__name__)

# 常量定义
DEFAULT_TOP_N = 20  # 默认返回TOP 20股票
MIN_TOP_N = 1  # 最小TOP N
MAX_TOP_N = 1000  # 最大TOP N
MIN_SCORE = 60.0  # 默认最低综合评分
DEFAULT_MIN_SCORE_THRESHOLD = 0.0  # 默认最低分数阈值（不过滤）
MAX_SCORE = 100.0  # 最大分数
MAX_WORKERS = 20  # 最大并行工作线程数
MIN_WORKERS = 1   # 最小并行工作线程数

# 预设筛选条件映射（必须与StockScreener中的presets一致）
PRESET_FILTERS = {
    'strong_momentum': '强势动量股',
    'value_growth': '价值成长股',
    'capital_inflow': '资金流入股',
    'low_pe_value': '低PE价值股',
    'high_dividend': '高股息率股',
    'breakout': '突破新高股',
    'oversold_rebound': '超卖反弹股',
    'institutional_favorite': '机构重仓股',
}

# 预设说明
PRESET_DESCRIPTIONS = {
    'strong_momentum': '技术面强势，短期动量充足，资金面良好，适合短线交易',
    'value_growth': '基本面优秀，成长性良好，估值合理，适合价值投资',
    'capital_inflow': '主力资金流入，资金面活跃，适合资金驱动型投资',
    'low_pe_value': 'PE<15，ROE>10%，寻找被低估的优质公司，适合价值投资',
    'high_dividend': '股息率>3%，稳定分红历史，追求稳定现金流，适合长期持有',
    'breakout': '突破20日新高，放量确认，动量延续机会，适合趋势跟踪',
    'oversold_rebound': 'RSI超卖后反弹，均值回归机会，适合短期交易',
    'institutional_favorite': '机构持仓>30%，跟随聪明钱，适合中长期投资',
}


def validate_top_n(top_n: int) -> None:
    """
    验证TOP N参数

    Args:
        top_n: 返回股票数量

    Raises:
        ValueError: 如果参数无效
    """
    if top_n < MIN_TOP_N:
        raise ValueError(
            f"返回股票数量至少为{MIN_TOP_N}只"
        )
    if top_n > MAX_TOP_N:
        raise ValueError(
            f"返回股票数量不能超过{MAX_TOP_N}只"
        )


def validate_preset(preset: str) -> bool:
    """
    验证预设条件是否有效

    Args:
        preset: 预设条件名称

    Returns:
        True表示有效，False表示无效
    """
    if not preset or not isinstance(preset, str):
        return False
    return preset in PRESET_FILTERS


def validate_max_workers(workers: int) -> None:
    """
    验证并行工作线程数

    Args:
        workers: 并行工作线程数

    Raises:
        ValueError: 如果参数无效
    """
    if workers < MIN_WORKERS:
        raise ValueError(f"并行线程数至少为{MIN_WORKERS}")
    if workers > MAX_WORKERS:
        raise ValueError(f"并行线程数不能超过{MAX_WORKERS}")


def validate_stock_pool(stock_pool: Optional[List[str]]) -> None:
    """
    验证股票池参数

    Args:
        stock_pool: 股票代码列表

    Raises:
        ValueError: 如果股票代码格式无效
    """
    if stock_pool is None:
        return

    if not isinstance(stock_pool, list):
        raise ValueError("股票池必须是列表类型")

    if len(stock_pool) == 0:
        raise ValueError("股票池不能为空列表")

    # A股股票代码格式: 6位数字，可能带有市场后缀(.SH/.SZ)
    stock_code_pattern = re.compile(r'^\d{6}(\.SH|\.SZ)?$')

    invalid_codes = []
    for code in stock_pool:
        if not isinstance(code, str):
            invalid_codes.append(str(code))
        elif not stock_code_pattern.match(code):
            invalid_codes.append(code)

    if invalid_codes:
        raise ValueError(
            f"股票池包含无效的股票代码: {', '.join(invalid_codes[:5])}"
            f"{'...' if len(invalid_codes) > 5 else ''}\n"
            f"股票代码格式应为6位数字，可选市场后缀(.SH/.SZ)"
        )


def validate_output_path(path: str) -> str:
    """
    验证输出路径的安全性，防止路径遍历攻击

    Args:
        path: 输出文件路径

    Returns:
        规范化后的安全路径

    Raises:
        ValueError: 如果路径不安全或格式不支持
    """
    if not path:
        raise ValueError("输出路径不能为空")

    # 转换为绝对路径并解析符号链接
    abs_path = Path(path).resolve()

    # 检查文件扩展名
    allowed_extensions = {'.csv', '.xlsx', '.xls'}
    if abs_path.suffix.lower() not in allowed_extensions:
        raise ValueError(
            f"不支持的文件格式: {abs_path.suffix}\n"
            f"支持的格式: {', '.join(allowed_extensions)}"
        )

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

    # 确保父目录存在
    parent = abs_path.parent
    if not parent.exists():
        raise ValueError(f"输出目录不存在: {parent}")

    return str(abs_path)


def run_screening(
    preset: str,
    top_n: int = DEFAULT_TOP_N,
    min_score: float = DEFAULT_MIN_SCORE_THRESHOLD,
    stock_pool: Optional[List[str]] = None,
    parallel: bool = True,
    max_workers: int = 5
) -> pd.DataFrame:
    """
    执行批量筛选

    Args:
        preset: 预设筛选条件名称
        top_n: 返回TOP N只股票
        min_score: 最低综合评分
        stock_pool: 自定义股票池（None表示全市场）
        parallel: 是否并行处理
        max_workers: 最大并行数

    Returns:
        筛选结果DataFrame

    Raises:
        ValueError: 如果参数无效
        RuntimeError: 如果筛选失败
    """
    # 验证预设
    if not validate_preset(preset):
        available = ', '.join(PRESET_FILTERS.keys())
        raise ValueError(
            f"不支持的预设条件: {preset}\n"
            f"可用预设: {available}"
        )

    # 验证TOP N
    validate_top_n(top_n)

    # 验证最低分数
    if min_score < 0 or min_score > MAX_SCORE:
        raise ValueError(
            f"最低分数必须在0-{MAX_SCORE}之间，当前值: {min_score}"
        )

    # 验证并行工作线程数
    validate_max_workers(max_workers)

    # 验证股票池
    validate_stock_pool(stock_pool)

    logger.info(f"开始批量筛选: 预设={preset}, TOP N={top_n}, 最低分={min_score}")

    try:
        # 创建筛选器
        screener = StockScreener()

        # 执行筛选
        logger.info(f"使用预设: {PRESET_FILTERS[preset]} ({PRESET_DESCRIPTIONS.get(preset, '')})")
        result_df = screener.screen(
            stock_pool=stock_pool,
            preset=preset,
            top_n=top_n,
            min_score=min_score,
            parallel=parallel,
            max_workers=max_workers
        )

        logger.info(f"筛选完成，找到 {len(result_df)} 只股票")
        return result_df

    except Exception as e:
        logger.error(f"筛选失败: {e}")
        raise RuntimeError(f"筛选失败: {e}") from e


def format_results_table(df: pd.DataFrame) -> str:
    """
    格式化筛选结果为表格

    Args:
        df: 筛选结果DataFrame

    Returns:
        格式化的表格字符串

    Raises:
        ValueError: 如果DataFrame缺少必需的列
    """
    if df is None or len(df) == 0:
        return "\n未找到符合条件的股票。\n"

    # 验证必需的列
    required_columns = ['code', 'name', 'score', 'current_price']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"DataFrame缺少必需的列: {', '.join(missing_columns)}\n"
            f"必需列: {', '.join(required_columns)}"
        )

    lines = []
    lines.append("=" * 120)
    lines.append("                                    筛选结果")
    lines.append("=" * 120)
    lines.append("")

    # 表头
    header = (
        f"{'排名':<6}{'代码':<10}{'名称':<12}{'综合评分':<12}"
        f"{'技术面':<12}{'基本面':<12}{'资金面':<12}{'当前价格':<12}{'入选理由':<20}"
    )
    lines.append(header)
    lines.append("-" * 120)

    # 数据行
    for idx, row in df.iterrows():
        rank = idx + 1 if isinstance(idx, int) else idx
        line = (
            f"{rank:<6}{row['code']:<10}{row['name']:<12}"
            f"{row['score']:<12.2f}{row.get('tech_score', 0):<12.2f}"
            f"{row.get('fundamental_score', 0):<12.2f}{row.get('capital_score', 0):<12.2f}"
            f"{row['current_price']:<12.2f}{row.get('reason', ''):<20}"
        )
        lines.append(line)

    lines.append("=" * 120)
    lines.append(f"总计: {len(df)} 只股票")
    lines.append("=" * 120)

    return "\n".join(lines)


def export_results(df: pd.DataFrame, output_path: str) -> None:
    """
    导出筛选结果到文件

    Args:
        df: 筛选结果DataFrame
        output_path: 输出文件路径

    Raises:
        ValueError: 如果路径不安全或格式不支持
        IOError: 如果文件写入失败
    """
    # 验证输出路径
    safe_path = validate_output_path(output_path)
    path = Path(safe_path)

    try:
        # 根据扩展名选择导出格式
        if path.suffix.lower() == '.csv':
            df.to_csv(safe_path, index=False, encoding='utf-8-sig')
            logger.info(f"结果已导出到CSV: {safe_path}")
        elif path.suffix.lower() in ['.xlsx', '.xls']:
            df.to_excel(safe_path, index=False, engine='openpyxl')
            logger.info(f"结果已导出到Excel: {safe_path}")
        else:
            raise ValueError(f"不支持的文件格式: {path.suffix}")

        print(f"\n结果已保存至: {safe_path}")

    except Exception as e:
        logger.error(f"导出结果失败: {e}")
        raise IOError(f"导出结果失败: {e}") from e


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数

    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description='A股批量筛选工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
预设筛选条件:
  strong_momentum        - 强势动量股（技术面强势，短期动量充足，资金面良好）
  value_growth           - 价值成长股（基本面优秀，成长性良好，估值合理）
  capital_inflow         - 资金流入股（主力资金流入，资金面活跃）
  low_pe_value           - 低PE价值股（PE<15，ROE>10%，寻找被低估的优质公司）
  high_dividend          - 高股息率股（股息率>3%，稳定分红历史，追求稳定现金流）
  breakout               - 突破新高股（突破20日新高，放量确认，动量延续机会）
  oversold_rebound       - 超卖反弹股（RSI超卖后反弹，均值回归机会）
  institutional_favorite - 机构重仓股（机构持仓>30%，跟随聪明钱）

示例:
  # 筛选强势动量股（TOP 20）
  python scripts/run_screening.py --preset strong_momentum

  # 筛选价值成长股（TOP 50）
  python scripts/run_screening.py --preset value_growth --top 50

  # 筛选低PE价值股并导出到CSV
  python scripts/run_screening.py --preset low_pe_value --output results.csv

  # 筛选高股息股并导出到Excel
  python scripts/run_screening.py --preset high_dividend --min-score 70 --output dividend_stocks.xlsx

  # 筛选突破新高股（短线机会）
  python scripts/run_screening.py --preset breakout --top 30

  # 筛选超卖反弹股（短期交易）
  python scripts/run_screening.py --preset oversold_rebound

  # 筛选机构重仓股（长期投资）
  python scripts/run_screening.py --preset institutional_favorite --top 50

  # 快速筛选（不并行处理）
  python scripts/run_screening.py --preset value_growth --no-parallel
        """
    )

    parser.add_argument(
        '--preset',
        required=True,
        choices=list(PRESET_FILTERS.keys()),
        help='预设筛选条件'
    )

    parser.add_argument(
        '--top',
        type=int,
        default=DEFAULT_TOP_N,
        help=f'返回TOP N只股票（默认: {DEFAULT_TOP_N}）'
    )

    parser.add_argument(
        '--min-score',
        type=float,
        default=DEFAULT_MIN_SCORE_THRESHOLD,
        help=f'最低综合评分（默认: {DEFAULT_MIN_SCORE_THRESHOLD}）'
    )

    parser.add_argument(
        '--output',
        help='导出结果到文件（支持.csv、.xlsx格式）'
    )

    parser.add_argument(
        '--no-parallel',
        action='store_true',
        help='禁用并行处理（速度较慢但资源占用少）'
    )

    parser.add_argument(
        '--max-workers',
        type=int,
        default=5,
        help=f'最大并行工作线程数（默认: 5，范围: {MIN_WORKERS}-{MAX_WORKERS}）'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细输出'
    )

    return parser.parse_args()


def main():
    """主函数"""
    # 解析参数
    args = parse_arguments()

    # 打印欢迎信息
    print("=" * 120)
    print("                                A股批量筛选系统")
    print("=" * 120)
    print(f"预设条件: {args.preset} - {PRESET_FILTERS[args.preset]}")
    print(f"说明: {PRESET_DESCRIPTIONS.get(args.preset, '无')}")
    print(f"返回数量: TOP {args.top}")
    print(f"最低分数: {args.min_score}")
    print(f"并行处理: {'否' if args.no_parallel else '是'}")
    if args.output:
        print(f"输出文件: {args.output}")
    print("=" * 120)
    print()

    try:
        # 执行筛选
        print("开始筛选，请稍候...")
        print("提示: 批量筛选可能需要较长时间，请耐心等待...\n")

        result_df = run_screening(
            preset=args.preset,
            top_n=args.top,
            min_score=args.min_score,
            parallel=not args.no_parallel,
            max_workers=args.max_workers
        )

        # 显示结果
        print(format_results_table(result_df))

        # 导出结果
        if args.output:
            export_results(result_df, args.output)

        # 输出统计信息
        if len(result_df) > 0:
            print(f"\n筛选统计:")
            print(f"  平均综合评分: {result_df['score'].mean():.2f}")
            print(f"  最高综合评分: {result_df['score'].max():.2f}")
            print(f"  最低综合评分: {result_df['score'].min():.2f}")

        print("\n筛选完成")

    except ValueError as e:
        print(f"\n参数错误: {e}")
        logger.error(f"参数错误: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)

    except Exception as e:
        print(f"\n筛选失败: {e}")
        logger.error(f"筛选失败: {e}")
        if args.verbose:
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
