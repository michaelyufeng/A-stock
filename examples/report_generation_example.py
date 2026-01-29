"""
股票报告生成示例

演示如何使用StockReportGenerator生成Markdown格式的股票分析报告
"""
import pandas as pd
from src.reporting.stock_report import StockReportGenerator


def example_basic_report():
    """基础示例：生成简单的股票分析报告"""
    print("=" * 80)
    print("示例 1: 基础报告生成")
    print("=" * 80)

    # 准备分析结果（通常来自 StockRater.analyze_stock()）
    analysis_result = {
        'rating': 'buy',
        'confidence': 8.5,
        'target_price': 15.80,
        'stop_loss': 13.50,
        'reasons': [
            '技术面呈现强势上涨趋势',
            '基本面良好，财务指标健康',
            '主力资金持续流入，市场情绪积极'
        ],
        'risks': [
            '市场整体波动可能影响个股表现',
            '政策和宏观环境变化风险'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出',
            '建议分批建仓，降低单次买入风险'
        ],
        'ai_insights': '综合评分75.2分，建议买入。技术面、基本面和资金面综合表现良好。',
        'scores': {
            'technical': 78.5,
            'fundamental': 72.3,
            'capital': 80.0,
            'overall': 75.2
        }
    }

    # 生成报告
    generator = StockReportGenerator()
    report = generator.generate_report(
        stock_code='000001',
        stock_name='平安银行',
        analysis_result=analysis_result
    )

    print(report)
    print("\n")


def example_report_with_kline_data():
    """示例2：包含K线数据的详细报告"""
    print("=" * 80)
    print("示例 2: 包含K线数据的详细报告")
    print("=" * 80)

    # 准备K线数据（包含技术指标）
    kline_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'close': [14.0, 14.2, 14.5, 14.3, 14.6, 14.8, 15.0, 15.2, 15.1, 15.3],
        'open': [13.9, 14.1, 14.3, 14.2, 14.5, 14.7, 14.9, 15.1, 15.0, 15.2],
        'high': [14.3, 14.5, 14.7, 14.5, 14.8, 15.0, 15.2, 15.4, 15.3, 15.5],
        'low': [13.8, 14.0, 14.2, 14.1, 14.4, 14.6, 14.8, 15.0, 14.9, 15.1],
        'volume': [1000000, 1200000, 1500000, 1100000, 1300000, 1400000, 1600000, 1800000, 1500000, 1700000],
        'MA5': [14.0, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9],
        'MA20': [13.5, 13.6, 13.7, 13.8, 13.9, 14.0, 14.1, 14.2, 14.3, 14.4],
        'MACD': [0.05, 0.08, 0.10, 0.09, 0.11, 0.13, 0.15, 0.17, 0.16, 0.18],
        'MACD_signal': [0.03, 0.05, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14],
        'RSI': [55.0, 58.0, 62.0, 60.0, 63.0, 65.0, 68.0, 70.0, 68.0, 69.0],
        'K': [60.0, 65.0, 70.0, 68.0, 72.0, 75.0, 78.0, 80.0, 78.0, 79.0],
        'D': [55.0, 58.0, 62.0, 65.0, 68.0, 70.0, 72.0, 75.0, 76.0, 77.0],
        'BOLL_UPPER': [15.0, 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.6, 15.8],
        'BOLL_MIDDLE': [14.0, 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.6, 14.8],
        'BOLL_LOWER': [13.0, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.6, 13.8],
        'VOL_MA5': [1000000, 1100000, 1200000, 1250000, 1300000, 1350000, 1400000, 1500000, 1550000, 1600000],
        'ATR': [0.30, 0.32, 0.35, 0.33, 0.36, 0.38, 0.40, 0.42, 0.40, 0.41]
    })

    analysis_result = {
        'rating': 'buy',
        'confidence': 8.8,
        'target_price': 16.50,
        'stop_loss': 14.00,
        'reasons': [
            '股价突破关键阻力位，技术形态良好',
            'MACD金叉向上，多头趋势确立',
            '成交量持续放大，市场参与度高',
            '基本面稳健，业绩增长可期'
        ],
        'risks': [
            '短期涨幅较大，存在回调风险',
            '市场整体波动可能影响个股表现'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出',
            '建议分批建仓，首次建仓不超过30%仓位'
        ],
        'ai_insights': (
            '技术面分析显示，股价呈现完美的上升通道，已突破多个关键阻力位。'
            'MA5向上穿越MA20形成金叉，MACD同步金叉向上，RSI处于健康区间（60-70）。'
            '成交量同步放大，显示市场对后市持乐观态度。\n\n'
            '建议在当前价位（15.30元）附近分批建仓，目标价16.50元，止损价14.00元。'
        ),
        'scores': {
            'technical': 85.0,
            'fundamental': 72.0,
            'capital': 82.0,
            'overall': 80.2
        }
    }

    # 生成包含K线数据的报告
    generator = StockReportGenerator()
    report = generator.generate_report(
        stock_code='600000',
        stock_name='浦发银行',
        analysis_result=analysis_result,
        kline_df=kline_df
    )

    print(report)
    print("\n")


def example_save_report_to_file():
    """示例3：保存报告到文件"""
    print("=" * 80)
    print("示例 3: 保存报告到文件")
    print("=" * 80)

    analysis_result = {
        'rating': 'hold',
        'confidence': 6.5,
        'target_price': 14.50,
        'stop_loss': 13.00,
        'reasons': [
            '综合指标显示震荡整理，建议观望',
            '技术面处于平衡状态'
        ],
        'risks': [
            '横盘整理期间可能出现方向选择',
            '需关注市场和个股基本面变化'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出'
        ],
        'ai_insights': '综合评分58分，建议持有观望。当前处于震荡整理阶段，建议等待明确方向信号。',
        'scores': {
            'technical': 55.0,
            'fundamental': 60.0,
            'capital': 58.0,
            'overall': 58.0
        }
    }

    # 生成并保存报告
    generator = StockReportGenerator()
    report = generator.generate_report(
        stock_code='601398',
        stock_name='工商银行',
        analysis_result=analysis_result,
        save_to_file=True,
        output_path='./reports/stock_report_601398.md'
    )

    print("报告已保存到: ./reports/stock_report_601398.md")
    print("\n报告内容预览:")
    print(report[:500] + "...\n")


def example_sell_rating_report():
    """示例4：卖出评级报告"""
    print("=" * 80)
    print("示例 4: 卖出评级报告")
    print("=" * 80)

    analysis_result = {
        'rating': 'sell',
        'confidence': 7.8,
        'target_price': 12.60,
        'stop_loss': 13.72,
        'reasons': [
            '技术面走弱，下跌趋势明显',
            '多项技术指标发出卖出信号',
            '主力资金流出，市场情绪悲观',
            '成交量萎缩，市场参与度低'
        ],
        'risks': [
            '继续持有可能面临进一步下跌风险',
            '建议及时止损，避免损失扩大',
            '市场整体环境不利于反弹'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出',
            'T+1限制下，需提前规划卖出时机',
            '跌停风险较大，建议尽早离场'
        ],
        'ai_insights': (
            '综合评分35分，强烈建议卖出。\n\n'
            '技术面：股价跌破多条均线支撑，MACD死叉向下，RSI进入超卖区。'
            '虽然短期可能存在反弹，但整体趋势向下，不建议抄底。\n\n'
            '资金面：主力资金连续流出，显示机构投资者看空后市。'
            '散户资金也在持续离场，市场情绪极度悲观。\n\n'
            '建议：立即止损离场，等待市场企稳后再考虑介入。'
        ),
        'scores': {
            'technical': 30.0,
            'fundamental': 38.0,
            'capital': 35.0,
            'overall': 35.0
        }
    }

    generator = StockReportGenerator()
    report = generator.generate_report(
        stock_code='600519',
        stock_name='贵州茅台',
        analysis_result=analysis_result
    )

    print(report)
    print("\n")


def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 24 + "股票报告生成器使用示例" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")
    print("\n")

    # 运行所有示例
    example_basic_report()
    example_report_with_kline_data()
    example_save_report_to_file()
    example_sell_rating_report()

    print("=" * 80)
    print("所有示例运行完成！")
    print("=" * 80)


if __name__ == '__main__':
    main()
