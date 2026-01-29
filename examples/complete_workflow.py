"""
完整工作流示例 - 从分析到回测到监控

展示从筛选、分析、回测到监控的完整量化交易流程：
1. 使用StockScreener批量筛选股票
2. 使用analyze_stock深度分析候选股票
3. 使用BacktestEngine回测策略
4. 将优选股票添加到监控列表
5. 配置MonitoringService实时监控

作者: A-stock量化交易系统
日期: 2026-01-29
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.screening.screener import StockScreener
from src.reporting.stock_report import analyze_stock
from src.backtest.engine import BacktestEngine
from src.strategy.short_term.momentum import MomentumStrategy
from src.monitoring.realtime_watcher import RealTimeWatcher
from src.monitoring.alert_manager import AlertManager
from src.risk.risk_manager import RiskManager
from src.data.akshare_provider import AKShareProvider
from src.core.logger import get_logger

logger = get_logger(__name__)


class QuantTradingWorkflow:
    """量化交易完整工作流"""

    def __init__(self, total_capital=1_000_000):
        """
        初始化工作流

        Args:
            total_capital: 总资金
        """
        self.total_capital = total_capital
        self.screener = StockScreener()
        self.data_provider = AKShareProvider()
        self.risk_manager = RiskManager(total_capital=total_capital)
        self.watcher = RealTimeWatcher(stock_list=[], update_interval=60)
        self.alert_manager = AlertManager()

        # 筛选结果
        self.screening_results = None
        # 分析结果
        self.analysis_results = {}
        # 回测结果
        self.backtest_results = {}
        # 选中的股票
        self.selected_stocks = []

        logger.info(f"工作流初始化完成 - 总资金: {total_capital:,.0f}元")

    def print_separator(self, title):
        """打印分隔线"""
        print("\n" + "=" * 70)
        print(f" {title}")
        print("=" * 70)

    def step1_screen_stocks(self, stock_pool=None, preset='strong_momentum', top_n=20):
        """
        步骤1: 批量筛选股票

        Args:
            stock_pool: 股票池（None表示使用示例股票池）
            preset: 预设筛选策略
            top_n: 返回TOP N只股票

        Returns:
            筛选结果DataFrame
        """
        self.print_separator("步骤1: 批量筛选股票")

        # 使用示例股票池（实际使用时可以用全市场或指数成分股）
        if stock_pool is None:
            stock_pool = [
                '600519',  # 贵州茅台
                '000858',  # 五粮液
                '600036',  # 招商银行
                '601318',  # 中国平安
                '000001',  # 平安银行
                '600000',  # 浦发银行
                '601166',  # 兴业银行
                '600016',  # 民生银行
            ]

        print(f"\n【筛选配置】")
        print(f"  股票池大小: {len(stock_pool)}只")
        print(f"  筛选策略: {preset}")
        print(f"  目标数量: TOP {top_n}")

        # 执行筛选
        print(f"\n【开始筛选】")
        self.screening_results = self.screener.screen(
            stock_pool=stock_pool,
            preset=preset,
            top_n=top_n,
            min_score=60,
            parallel=False  # 小股票池用顺序处理
        )

        # 显示结果
        if len(self.screening_results) > 0:
            print(f"\n【筛选结果】找到 {len(self.screening_results)} 只符合条件的股票:")
            print(self.screening_results[['code', 'name', 'score', 'tech_score', 'reason']].to_string(index=False))
        else:
            print("\n【筛选结果】未找到符合条件的股票")

        return self.screening_results

    def step2_analyze_top_stocks(self, top_k=5, depth='quick'):
        """
        步骤2: 深度分析TOP股票

        Args:
            top_k: 分析前K只股票
            depth: 分析深度（quick/full）

        Returns:
            分析结果字典
        """
        self.print_separator("步骤2: 深度分析TOP股票")

        if self.screening_results is None or len(self.screening_results) == 0:
            print("错误: 没有筛选结果，请先执行步骤1")
            return {}

        # 选择TOP K只股票
        top_stocks = self.screening_results.head(top_k)

        print(f"\n【分析配置】")
        print(f"  分析数量: {len(top_stocks)}只")
        print(f"  分析深度: {depth}")

        print(f"\n【开始分析】")
        for idx, row in top_stocks.iterrows():
            code = row['code']
            name = row['name']

            print(f"\n  分析 {name}({code})...")

            try:
                # 深度分析
                result = analyze_stock(code, depth=depth, save_report=False)

                self.analysis_results[code] = {
                    'name': name,
                    'code': code,
                    'technical_score': result.get('technical_score', 0),
                    'fundamental_score': result.get('fundamental_score', 0),
                    'capital_score': result.get('capital_score', 0),
                    'overall_score': (
                        result.get('technical_score', 0) * 0.4 +
                        result.get('fundamental_score', 0) * 0.4 +
                        result.get('capital_score', 0) * 0.2
                    ),
                    'ai_rating': result.get('ai_rating', 'N/A'),
                    'recommendation': result.get('recommendation', 'N/A')
                }

                print(f"    ✓ 完成 - 综合评分: {self.analysis_results[code]['overall_score']:.1f}")

            except Exception as e:
                logger.error(f"分析{code}失败: {e}")
                print(f"    ✗ 失败: {e}")

        # 显示分析摘要
        if self.analysis_results:
            print(f"\n【分析摘要】")
            for code, result in sorted(
                self.analysis_results.items(),
                key=lambda x: x[1]['overall_score'],
                reverse=True
            ):
                print(f"  {result['name']}({code})")
                print(f"    综合评分: {result['overall_score']:.1f}")
                print(f"    技术面: {result['technical_score']:.1f}")
                print(f"    基本面: {result['fundamental_score']:.1f}")
                print(f"    资金面: {result['capital_score']:.1f}")
                if depth == 'full':
                    print(f"    AI评级: {result['ai_rating']}")

        return self.analysis_results

    def step3_backtest_strategy(self, test_codes=None, days=252):
        """
        步骤3: 回测策略

        Args:
            test_codes: 要回测的股票代码列表（None表示使用分析结果）
            days: 回测天数

        Returns:
            回测结果字典
        """
        self.print_separator("步骤3: 回测策略")

        # 选择要回测的股票
        if test_codes is None:
            if not self.analysis_results:
                print("错误: 没有分析结果，请先执行步骤2")
                return {}
            # 选择综合评分最高的3只
            test_codes = sorted(
                self.analysis_results.keys(),
                key=lambda x: self.analysis_results[x]['overall_score'],
                reverse=True
            )[:3]

        print(f"\n【回测配置】")
        print(f"  回测股票: {len(test_codes)}只")
        print(f"  回测周期: {days}天")
        print(f"  策略: 动量策略")

        # 回测每只股票
        for code in test_codes:
            name = self.analysis_results.get(code, {}).get('name', code)
            print(f"\n  回测 {name}({code})...")

            try:
                # 获取历史数据
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)

                data = self.data_provider.get_stock_data(
                    code,
                    start_date=start_date.strftime('%Y%m%d'),
                    end_date=end_date.strftime('%Y%m%d')
                )

                if data is None or len(data) < 60:
                    print(f"    ✗ 数据不足（{len(data) if data is not None else 0}条）")
                    continue

                # 创建回测引擎
                engine = BacktestEngine(
                    initial_cash=self.total_capital * 0.3,  # 单只股票30%仓位
                    commission=0.0003,
                    stamp_tax=0.001
                )

                # 运行回测
                results = engine.run_backtest(
                    strategy_class=MomentumStrategy,
                    data=data,
                    stock_code=code
                )

                self.backtest_results[code] = {
                    'name': name,
                    'code': code,
                    'total_return': results['total_return'],
                    'sharpe_ratio': results['sharpe_ratio'],
                    'max_drawdown': results['max_drawdown'],
                    'total_trades': results['total_trades'],
                    'win_rate': results['win_rate']
                }

                print(f"    ✓ 完成 - 收益率: {results['total_return']:.2%}, "
                      f"夏普: {results['sharpe_ratio']:.2f}")

            except Exception as e:
                logger.error(f"回测{code}失败: {e}")
                print(f"    ✗ 失败: {e}")

        # 显示回测摘要
        if self.backtest_results:
            print(f"\n【回测摘要】")
            for code, result in sorted(
                self.backtest_results.items(),
                key=lambda x: x[1]['total_return'],
                reverse=True
            ):
                print(f"  {result['name']}({code})")
                print(f"    收益率: {result['total_return']:.2%}")
                print(f"    夏普比率: {result['sharpe_ratio']:.2f}")
                print(f"    最大回撤: {result['max_drawdown']:.2%}")
                print(f"    交易次数: {result['total_trades']}")
                print(f"    胜率: {result['win_rate']:.2%}")

        return self.backtest_results

    def step4_select_stocks(self, min_return=0.0, min_sharpe=0.5):
        """
        步骤4: 选择优质股票

        Args:
            min_return: 最低收益率要求
            min_sharpe: 最低夏普比率要求

        Returns:
            选中的股票列表
        """
        self.print_separator("步骤4: 选择优质股票")

        print(f"\n【筛选标准】")
        print(f"  最低收益率: {min_return:.2%}")
        print(f"  最低夏普比率: {min_sharpe:.2f}")

        # 根据回测结果筛选
        if not self.backtest_results:
            print("\n错误: 没有回测结果，请先执行步骤3")
            return []

        self.selected_stocks = []

        for code, result in self.backtest_results.items():
            # 检查是否满足条件
            if (result['total_return'] >= min_return and
                result['sharpe_ratio'] >= min_sharpe):

                self.selected_stocks.append({
                    'code': code,
                    'name': result['name'],
                    'return': result['total_return'],
                    'sharpe': result['sharpe_ratio'],
                    'max_dd': result['max_drawdown']
                })

        # 显示选中的股票
        if self.selected_stocks:
            print(f"\n【选中股票】共 {len(self.selected_stocks)} 只:")
            for stock in self.selected_stocks:
                print(f"  ✓ {stock['name']}({stock['code']})")
                print(f"    收益率: {stock['return']:.2%}")
                print(f"    夏普比率: {stock['sharpe']:.2f}")
                print(f"    最大回撤: {stock['max_dd']:.2%}")
        else:
            print("\n【选中股票】无股票满足条件")

        return self.selected_stocks

    def step5_setup_monitoring(self):
        """
        步骤5: 设置实时监控

        Returns:
            监控器配置状态
        """
        self.print_separator("步骤5: 设置实时监控")

        if not self.selected_stocks:
            print("错误: 没有选中的股票，请先执行步骤4")
            return False

        print(f"\n【配置监控】")

        # 1. 添加股票到监控列表
        for stock in self.selected_stocks:
            self.watcher.add_stock(stock['code'], stock['name'])
            print(f"  ✓ 添加监控: {stock['name']}({stock['code']})")

        # 2. 配置告警规则
        print(f"\n【配置告警】")

        # 价格异动告警
        self.alert_manager.add_rule(
            name='价格异动',
            condition=lambda quote: abs(quote.get('change_pct', 0)) > 0.05,
            action='MONITOR',
            priority='MEDIUM',
            notification=['console']
        )
        print("  ✓ 价格异动告警 (涨跌幅>5%)")

        # 大幅下跌告警
        self.alert_manager.add_rule(
            name='大幅下跌',
            condition=lambda quote: quote.get('change_pct', 0) < -0.03,
            action='WARNING',
            priority='HIGH',
            notification=['console']
        )
        print("  ✓ 大幅下跌告警 (跌幅>3%)")

        # 突破新高告警
        self.alert_manager.add_rule(
            name='突破新高',
            condition=lambda quote: quote.get('change_pct', 0) > 0.05,
            action='BUY_SIGNAL',
            priority='MEDIUM',
            notification=['console']
        )
        print("  ✓ 突破新高告警 (涨幅>5%)")

        # 3. 显示监控摘要
        watchlist = self.watcher.get_watchlist()
        rules = self.alert_manager.list_rules()

        print(f"\n【监控摘要】")
        print(f"  监控股票: {len(watchlist)}只")
        print(f"  告警规则: {len(rules)}条")
        print(f"  更新间隔: {self.watcher.update_interval}秒")

        return True

    def run_complete_workflow(self):
        """运行完整工作流"""
        self.print_separator("A股量化交易完整工作流")

        print("\n本示例将展示从筛选到监控的完整流程：")
        print("  1. 批量筛选股票")
        print("  2. 深度分析候选股票")
        print("  3. 回测验证策略")
        print("  4. 选择优质股票")
        print("  5. 设置实时监控")

        try:
            # 步骤1: 筛选
            screening_results = self.step1_screen_stocks(
                preset='strong_momentum',
                top_n=10
            )

            if len(screening_results) == 0:
                print("\n工作流终止: 筛选无结果")
                return

            # 步骤2: 分析
            self.step2_analyze_top_stocks(
                top_k=5,
                depth='quick'  # 使用quick避免API调用
            )

            if not self.analysis_results:
                print("\n工作流终止: 分析无结果")
                return

            # 步骤3: 回测
            self.step3_backtest_strategy(days=180)

            if not self.backtest_results:
                print("\n工作流终止: 回测无结果")
                return

            # 步骤4: 选择
            self.step4_select_stocks(
                min_return=0.0,  # 降低要求以确保有结果
                min_sharpe=0.0
            )

            if not self.selected_stocks:
                print("\n工作流终止: 无股票满足条件")
                return

            # 步骤5: 监控
            self.step5_setup_monitoring()

            # 完成
            self.print_separator("工作流完成")
            print("\n✓ 完整工作流执行成功！")
            print("\n【最终结果】")
            print(f"  筛选股票: {len(screening_results)}只")
            print(f"  分析股票: {len(self.analysis_results)}只")
            print(f"  回测股票: {len(self.backtest_results)}只")
            print(f"  选中股票: {len(self.selected_stocks)}只")
            print(f"  监控股票: {len(self.watcher.get_watchlist())}只")

            print("\n【下一步操作建议】")
            print("  1. 查看监控列表: workflow.watcher.get_watchlist()")
            print("  2. 获取实时行情: workflow.watcher.get_all_quotes()")
            print("  3. 检查告警: workflow.alert_manager.check_alerts()")
            print("  4. 风险管理: workflow.risk_manager.get_portfolio_summary()")

        except Exception as e:
            logger.error(f"工作流执行失败: {e}", exc_info=True)
            print(f"\n错误: {e}")

    def generate_summary_report(self):
        """生成工作流摘要报告"""
        self.print_separator("工作流摘要报告")

        print(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n一、筛选阶段")
        if self.screening_results is not None:
            print(f"  筛选股票: {len(self.screening_results)}只")
            if len(self.screening_results) > 0:
                avg_score = self.screening_results['score'].mean()
                print(f"  平均评分: {avg_score:.1f}")
        else:
            print("  未执行")

        print(f"\n二、分析阶段")
        if self.analysis_results:
            print(f"  分析股票: {len(self.analysis_results)}只")
            avg_overall = sum(r['overall_score'] for r in self.analysis_results.values()) / len(self.analysis_results)
            print(f"  平均综合评分: {avg_overall:.1f}")
        else:
            print("  未执行")

        print(f"\n三、回测阶段")
        if self.backtest_results:
            print(f"  回测股票: {len(self.backtest_results)}只")
            avg_return = sum(r['total_return'] for r in self.backtest_results.values()) / len(self.backtest_results)
            avg_sharpe = sum(r['sharpe_ratio'] for r in self.backtest_results.values()) / len(self.backtest_results)
            print(f"  平均收益率: {avg_return:.2%}")
            print(f"  平均夏普比率: {avg_sharpe:.2f}")
        else:
            print("  未执行")

        print(f"\n四、选股结果")
        if self.selected_stocks:
            print(f"  选中股票: {len(self.selected_stocks)}只")
            for stock in self.selected_stocks:
                print(f"    - {stock['name']}({stock['code']}): "
                      f"收益{stock['return']:.2%}, 夏普{stock['sharpe']:.2f}")
        else:
            print("  未选中股票")

        print(f"\n五、监控配置")
        watchlist = self.watcher.get_watchlist()
        rules = self.alert_manager.list_rules()
        print(f"  监控股票: {len(watchlist)}只")
        print(f"  告警规则: {len(rules)}条")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print(" A股量化交易系统 - 完整工作流示例")
    print(" Complete Workflow Example")
    print("=" * 70)

    # 创建工作流
    workflow = QuantTradingWorkflow(total_capital=1_000_000)

    # 运行完整流程
    workflow.run_complete_workflow()

    # 生成摘要报告
    print("\n")
    workflow.generate_summary_report()

    print("\n" + "=" * 70)
    print(" 示例完成")
    print("=" * 70)
    print("\n提示:")
    print("  - 本示例使用小股票池和quick分析以加快演示速度")
    print("  - 实际使用时可以使用更大的股票池和full分析")
    print("  - 参考 docs/BEST_PRACTICES.md 了解更多最佳实践")
    print("  - 参考各模块的使用指南了解详细配置")


if __name__ == '__main__':
    main()
