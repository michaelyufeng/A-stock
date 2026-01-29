"""选股筛选器使用示例"""
from src.screening.screener import StockScreener
from src.core.logger import get_logger

logger = get_logger(__name__)


def example_preset_screening():
    """使用预设方案筛选示例"""
    logger.info("=== 使用预设方案筛选 ===")

    screener = StockScreener()

    # 使用强势动量方案筛选
    logger.info("\n1. 强势动量股筛选")
    results = screener.screen(
        stock_pool=['600519', '000001', '600036', '000002', '601318'],
        preset='strong_momentum',
        top_n=3,
        min_score=50,
        parallel=False  # 小股票池使用顺序处理
    )

    if len(results) > 0:
        print("\n强势动量股TOP 3:")
        print(results[['code', 'name', 'score', 'tech_score', 'capital_score', 'reason']].to_string(index=False))
    else:
        print("未找到符合条件的股票")


def example_custom_screening():
    """使用自定义筛选条件示例"""
    logger.info("\n=== 使用自定义筛选条件 ===")

    screener = StockScreener()

    # 自定义筛选条件（重视技术面和资金面）
    custom_filters = {
        'use_fundamental': False,
        'use_capital': True,
        'weights': {
            'technical': 0.6,
            'fundamental': 0.1,
            'capital': 0.3
        }
    }

    logger.info("\n2. 自定义筛选（技术面60% + 资金面30%）")
    results = screener.screen(
        stock_pool=['600519', '000001', '600036'],
        filters=custom_filters,
        top_n=3,
        min_score=60,
        parallel=False
    )

    if len(results) > 0:
        print("\n自定义筛选结果:")
        print(results[['code', 'name', 'score', 'tech_score', 'capital_score', 'reason']].to_string(index=False))
    else:
        print("未找到符合条件的股票")


def example_value_growth_screening():
    """价值成长股筛选示例"""
    logger.info("\n=== 价值成长股筛选 ===")

    screener = StockScreener()

    logger.info("\n3. 价值成长股筛选")
    results = screener.screen(
        stock_pool=['600519', '000001', '600036', '601318'],
        preset='value_growth',
        top_n=3,
        min_score=60,
        parallel=False
    )

    if len(results) > 0:
        print("\n价值成长股TOP 3:")
        print(results[['code', 'name', 'score', 'fundamental_score', 'tech_score', 'reason']].to_string(index=False))
    else:
        print("未找到符合条件的股票")


def example_parallel_screening():
    """并行筛选示例（适合大股票池）"""
    logger.info("\n=== 并行筛选示例 ===")

    screener = StockScreener()

    # 较大的股票池（这里演示用10只）
    large_stock_pool = [
        '600519', '000001', '600036', '000002', '601318',
        '601398', '600000', '601166', '601288', '600016'
    ]

    logger.info("\n4. 并行筛选（10只股票，3个工作线程）")
    results = screener.screen(
        stock_pool=large_stock_pool,
        preset='capital_inflow',
        top_n=5,
        min_score=55,
        parallel=True,
        max_workers=3
    )

    if len(results) > 0:
        print("\n资金流入股TOP 5:")
        print(results[['code', 'name', 'score', 'current_price', 'reason']].to_string(index=False))
    else:
        print("未找到符合条件的股票")


def example_high_score_filter():
    """高评分筛选示例"""
    logger.info("\n=== 高评分筛选 ===")

    screener = StockScreener()

    logger.info("\n5. 高评分筛选（最低70分）")
    results = screener.screen(
        stock_pool=['600519', '000001', '600036', '000002'],
        preset='strong_momentum',
        top_n=10,
        min_score=70,  # 高评分要求
        parallel=False
    )

    if len(results) > 0:
        print(f"\n找到 {len(results)} 只高评分股票:")
        print(results[['code', 'name', 'score', 'reason']].to_string(index=False))
    else:
        print("未找到评分>=70的股票")


if __name__ == '__main__':
    print("=" * 80)
    print("选股筛选器使用示例")
    print("=" * 80)

    try:
        # 1. 预设方案筛选
        example_preset_screening()

        # 2. 自定义筛选
        example_custom_screening()

        # 3. 价值成长股筛选
        example_value_growth_screening()

        # 4. 并行筛选（适合大股票池）
        example_parallel_screening()

        # 5. 高评分筛选
        example_high_score_filter()

        print("\n" + "=" * 80)
        print("示例运行完成！")
        print("=" * 80)

    except Exception as e:
        logger.error(f"运行示例时出错: {e}", exc_info=True)
        print(f"\n错误: {e}")
        print("注意: 示例需要网络连接以获取实时数据")
