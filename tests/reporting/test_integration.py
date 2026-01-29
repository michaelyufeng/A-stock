"""集成测试：StockRater + StockReportGenerator"""
import pytest
import pandas as pd
from src.reporting.stock_report import StockReportGenerator


@pytest.fixture
def sample_kline_data():
    """样本K线数据"""
    return pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=30),
        'close': [14.0 + i * 0.1 for i in range(30)],
        'open': [13.9 + i * 0.1 for i in range(30)],
        'high': [14.2 + i * 0.1 for i in range(30)],
        'low': [13.8 + i * 0.1 for i in range(30)],
        'volume': [1000000 + i * 10000 for i in range(30)]
    })


@pytest.fixture
def sample_financial_data():
    """样本财务数据"""
    return pd.DataFrame({
        'roe': [15.5, 16.2, 16.8],
        'gross_margin': [35.2, 36.1, 36.5],
        'net_profit': [1000000000, 1100000000, 1200000000],
        'revenue': [5000000000, 5500000000, 6000000000],
        'debt_ratio': [45.3, 44.8, 44.2],
        'current_ratio': [1.5, 1.6, 1.7],
        'pe_ratio': [12.5, 12.0, 11.8],
        'pb_ratio': [1.8, 1.7, 1.7]
    })


@pytest.fixture
def sample_money_flow_data():
    """样本资金流向数据"""
    return pd.DataFrame({
        'main_net_inflow': [50000000, 60000000, 70000000, 80000000, 90000000],
        'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
    })


def test_end_to_end_report_generation(sample_kline_data):
    """端到端测试：生成完整报告"""
    # 模拟完整的分析结果
    analysis_result = {
        'rating': 'buy',
        'confidence': 8.5,
        'target_price': 17.00,
        'stop_loss': 15.30,
        'reasons': [
            '技术面呈现强势上涨趋势，MA5向上穿越MA20形成金叉',
            '基本面良好，ROE持续增长，财务指标健康',
            '主力资金持续流入，市场情绪积极',
            '资金流向信号显示买入机会'
        ],
        'risks': [
            '市场整体波动可能影响个股表现',
            '政策和宏观环境变化风险'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出',
            '建议分批建仓，降低单次买入风险'
        ],
        'ai_insights': '综合评分75.2分，建议买入。技术面、基本面和资金面综合表现良好，信心度8.5/10。'
                      '从技术面看，股价突破关键阻力位，成交量放大，MACD金叉向上，RSI处于健康区间。'
                      '基本面上，公司盈利能力稳定增长，ROE保持在15%以上，负债率控制良好。'
                      '资金面显示主力资金持续流入，市场情绪积极。'
                      '建议关注买入时机，分批建仓以降低风险。止损价设定在15.30元，目标价17.00元。',
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
        analysis_result=analysis_result,
        kline_df=sample_kline_data
    )

    # 验证报告生成成功
    assert isinstance(report, str)
    assert len(report) > 0

    # 验证报告包含所有关键部分
    assert '# 股票分析报告 - 000001 平安银行' in report
    assert '## 📊 投资决策' in report
    assert '买入' in report
    assert '17.00' in report
    assert '## 💡 核心理由' in report
    assert '## ⚠️ 风险提示' in report
    assert '## 📈 详细分析' in report
    assert '### 技术面分析' in report
    assert '### 基本面分析' in report
    assert '### 资金面分析' in report
    assert '## 🤖 AI综合分析' in report
    assert '## 📊 综合评分' in report
    assert '免责声明' in report

    # 验证评分正确
    assert '78.5' in report
    assert '72.3' in report
    assert '80.0' in report
    assert '75.2' in report

    # 打印报告（用于手动检查）
    print("\n" + "="*80)
    print("生成的报告示例：")
    print("="*80)
    print(report)
    print("="*80)


def test_save_and_load_report(sample_kline_data, tmp_path):
    """测试保存和加载报告"""
    analysis_result = {
        'rating': 'hold',
        'confidence': 6.5,
        'target_price': 14.50,
        'stop_loss': 13.00,
        'reasons': ['综合指标显示震荡整理，建议观望'],
        'risks': ['横盘整理期间可能出现方向选择'],
        'a_share_risks': ['T+1交易制度限制，当日买入次日才能卖出'],
        'ai_insights': '综合评分58分，建议持有观望。',
        'scores': {
            'technical': 55.0,
            'fundamental': 60.0,
            'capital': 58.0,
            'overall': 58.0
        }
    }

    # 生成并保存报告
    generator = StockReportGenerator()
    output_path = tmp_path / "test_report.md"

    report = generator.generate_report(
        stock_code='600000',
        stock_name='浦发银行',
        analysis_result=analysis_result,
        kline_df=sample_kline_data,
        save_to_file=True,
        output_path=str(output_path)
    )

    # 验证文件存在
    assert output_path.exists()

    # 验证文件内容
    saved_content = output_path.read_text(encoding='utf-8')
    assert saved_content == report
    assert '浦发银行' in saved_content
    assert '持有' in saved_content


def test_markdown_rendering_quality(sample_kline_data):
    """测试Markdown渲染质量"""
    analysis_result = {
        'rating': 'sell',
        'confidence': 7.5,
        'target_price': 12.50,
        'stop_loss': 13.80,
        'reasons': [
            '技术面走弱，下跌趋势明显',
            '主力资金流出，市场情绪悲观'
        ],
        'risks': [
            '继续持有可能面临进一步下跌风险',
            '建议及时止损，避免损失扩大'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出',
            'T+1限制下，需提前规划卖出时机'
        ],
        'ai_insights': '综合评分35分，建议卖出。多项指标显示下行风险。',
        'scores': {
            'technical': 30.0,
            'fundamental': 38.0,
            'capital': 35.0,
            'overall': 35.0
        }
    }

    generator = StockReportGenerator()
    report = generator.generate_report(
        stock_code='601398',
        stock_name='工商银行',
        analysis_result=analysis_result,
        kline_df=sample_kline_data
    )

    # 验证Markdown语法正确
    # 1. 标题层级
    assert report.count('# 股票分析报告') == 1
    assert '##' in report  # 二级标题存在
    assert '###' in report  # 三级标题存在

    # 2. 列表
    assert '1. ' in report  # 有序列表
    assert '- ' in report   # 无序列表

    # 3. 表格
    assert '|' in report
    assert '|---' in report or '| ---' in report

    # 4. 粗体
    assert '**' in report

    # 5. 分隔线
    assert '---' in report

    # 6. Emoji
    assert '📊' in report
    assert '💡' in report
    assert '⚠️' in report
    assert '📈' in report
    assert '🤖' in report


def test_comprehensive_stock_analysis_workflow():
    """综合测试：完整的股票分析工作流"""
    # 这个测试演示了从数据准备到报告生成的完整流程

    # 1. 准备数据
    kline_df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=20),
        'close': [15.0, 15.2, 15.5, 15.3, 15.8, 16.0, 16.2, 16.5, 16.3, 16.8,
                  17.0, 17.2, 17.5, 17.3, 17.8, 18.0, 18.2, 18.5, 18.3, 18.8],
        'open': [14.9, 15.1, 15.4, 15.2, 15.7, 15.9, 16.1, 16.4, 16.2, 16.7,
                 16.9, 17.1, 17.4, 17.2, 17.7, 17.9, 18.1, 18.4, 18.2, 18.7],
        'high': [15.3, 15.4, 15.7, 15.5, 16.0, 16.2, 16.4, 16.7, 16.5, 17.0,
                 17.2, 17.4, 17.7, 17.5, 18.0, 18.2, 18.4, 18.7, 18.5, 19.0],
        'low': [14.8, 15.0, 15.3, 15.1, 15.6, 15.8, 16.0, 16.3, 16.1, 16.6,
                16.8, 17.0, 17.3, 17.1, 17.6, 17.8, 18.0, 18.3, 18.1, 18.6],
        'volume': [1000000 + i * 50000 for i in range(20)]
    })

    # 2. 模拟分析结果
    analysis_result = {
        'rating': 'buy',
        'confidence': 9.0,
        'target_price': 20.50,
        'stop_loss': 17.00,
        'reasons': [
            '股价连续创新高，上升趋势明确',
            '成交量持续放大，市场参与度高',
            '技术指标全面向好，买入信号强烈',
            '基本面优秀，业绩持续增长',
            '主力资金大幅流入，机构看好'
        ],
        'risks': [
            '短期涨幅较大，存在回调风险',
            '市场整体波动可能影响个股表现',
            '政策和宏观环境变化风险'
        ],
        'a_share_risks': [
            'T+1交易制度限制，当日买入次日才能卖出',
            '建议分批建仓，降低单次买入风险',
            '涨幅较大，需警惕涨停板限制'
        ],
        'ai_insights': '【强烈推荐买入】\n\n'
                      '综合评分85.5分，是近期最值得关注的投资标的之一。\n\n'
                      '技术面分析：股价呈现完美的上升通道，已连续突破多个关键阻力位。'
                      '成交量同步放大，显示市场对后市持乐观态度。MACD、RSI、KDJ等多个技术指标均发出强烈买入信号。\n\n'
                      '基本面分析：公司业绩优秀，ROE稳定在18%以上，净利润同比增长25%。'
                      '资产负债率控制良好，现金流充裕，具有良好的成长性。\n\n'
                      '资金面分析：主力资金连续5日净流入超过5亿元，显示机构投资者高度看好。'
                      '北向资金也在持续加仓，外资对该股的配置意愿强烈。\n\n'
                      '投资建议：建议在18.50-19.00元区间分批建仓，首次建仓不超过总仓位的30%。'
                      '目标价位20.50元，预期涨幅约10%。止损价设定在17.00元，严格执行止损纪律。\n\n'
                      '风险提示：短期涨幅较大，建议控制仓位，避免追高。密切关注市场整体走势和个股基本面变化。',
        'scores': {
            'technical': 88.0,
            'fundamental': 85.0,
            'capital': 90.0,
            'overall': 85.5
        }
    }

    # 3. 生成报告
    generator = StockReportGenerator()
    report = generator.generate_report(
        stock_code='000001',
        stock_name='平安银行',
        analysis_result=analysis_result,
        kline_df=kline_df
    )

    # 4. 验证报告质量
    assert isinstance(report, str)
    assert len(report) > 1000  # 报告应该有足够的内容

    # 验证关键信息存在
    assert '平安银行' in report
    assert '买入' in report
    assert '9.0/10' in report
    assert '20.50' in report
    assert '17.00' in report
    assert '85.5' in report

    # 验证报告结构完整
    sections_count = report.count('##')
    assert sections_count >= 6  # 至少应该有6个二级标题

    print("\n" + "="*80)
    print("综合分析报告示例：")
    print("="*80)
    print(report)
    print("="*80)
