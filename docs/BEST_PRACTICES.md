# A股量化交易系统最佳实践指南

## 目录

1. [股票分析最佳实践](#股票分析最佳实践)
2. [批量筛选最佳实践](#批量筛选最佳实践)
3. [策略回测最佳实践](#策略回测最佳实践)
4. [实时监控最佳实践](#实时监控最佳实践)
5. [风险管理最佳实践](#风险管理最佳实践)
6. [完整工作流程](#完整工作流程)
7. [常见陷阱和注意事项](#常见陷阱和注意事项)

---

## 股票分析最佳实践

### 1. 如何选择分析深度

#### Quick分析（快速模式）
**适用场景：**
- 初步筛选大量股票
- 快速了解基本情况
- 对AI分析需求不高

**优点：**
- 速度快，不消耗API额度
- 适合批量处理
- 获取基础技术和财务指标

**示例：**
```python
from src.reporting.stock_report import analyze_stock

# 快速分析
result = analyze_stock('600519', depth='quick')
print(result['technical_score'])  # 技术面评分
print(result['fundamental_score'])  # 基本面评分
```

#### Full分析（完整模式）
**适用场景：**
- 深度研究目标股票
- 需要AI综合评级
- 制定交易决策前

**优点：**
- 提供AI综合分析
- 包含投资建议和风险提示
- 生成完整的分析报告

**示例：**
```python
# 完整分析（需要DeepSeek API）
result = analyze_stock('600519', depth='full')
print(result['ai_rating'])  # AI评级
print(result['recommendation'])  # 投资建议
```

### 2. 如何解读分析结果

#### 评分体系理解

**技术面评分（0-100分）：**
- **80-100分**: 强势，技术指标优秀，适合短期交易
- **60-79分**: 中性偏强，技术面健康
- **40-59分**: 中性，观察为主
- **0-39分**: 弱势，技术面较差

**基本面评分（0-100分）：**
- **80-100分**: 优秀企业，财务健康，成长性好
- **60-79分**: 良好，基本面稳健
- **40-59分**: 一般，需要关注财务风险
- **0-39分**: 较差，财务状况堪忧

**资金面评分：**
- **70-100分**: 主力资金流入，市场关注度高
- **50-69分**: 资金平衡
- **0-49分**: 资金流出，谨慎观察

#### AI评级解读

AI综合评级考虑多个维度：
- 技术面趋势
- 基本面质量
- 行业景气度
- 市场情绪

**评级说明：**
- **强力推荐**: 多维度优秀，值得重点关注
- **推荐**: 总体良好，可以考虑建仓
- **中性**: 观察为主，等待更好时机
- **不推荐**: 存在明显风险，建议规避

### 3. 如何结合多个维度判断

#### 短期交易策略
**重点关注：**
1. 技术面评分 > 70
2. 资金面评分 > 70
3. MACD金叉、RSI在合理区间

**决策流程：**
```python
def is_short_term_buy(analysis_result):
    """判断是否适合短期买入"""
    # 技术面要强
    if analysis_result['technical_score'] < 70:
        return False

    # 资金面要好
    if analysis_result['capital_score'] < 70:
        return False

    # MACD要金叉
    tech_data = analysis_result['technical_analysis']
    if tech_data.get('macd_signal') != '金叉':
        return False

    return True
```

#### 中长期投资策略
**重点关注：**
1. 基本面评分 > 70
2. ROE > 15%
3. 营收和利润增长稳定
4. 行业前景良好

**决策流程：**
```python
def is_long_term_buy(analysis_result):
    """判断是否适合中长期投资"""
    # 基本面要好
    if analysis_result['fundamental_score'] < 70:
        return False

    # ROE要高
    fundamental = analysis_result['fundamental_analysis']
    if fundamental.get('roe', 0) < 15:
        return False

    # 成长性要好
    if fundamental.get('revenue_growth', 0) < 10:
        return False

    return True
```

#### 价值与成长平衡策略
结合基本面、技术面和资金面：

```python
def balanced_decision(analysis_result):
    """平衡型投资决策"""
    scores = {
        'technical': analysis_result['technical_score'],
        'fundamental': analysis_result['fundamental_score'],
        'capital': analysis_result['capital_score']
    }

    # 综合评分
    total_score = (
        scores['technical'] * 0.3 +
        scores['fundamental'] * 0.5 +
        scores['capital'] * 0.2
    )

    # 没有明显短板
    if min(scores.values()) < 50:
        return 'HOLD', '存在明显短板'

    if total_score >= 75:
        return 'BUY', '综合表现优秀'
    elif total_score >= 60:
        return 'HOLD', '综合表现良好，观察'
    else:
        return 'SELL', '综合表现不佳'
```

---

## 批量筛选最佳实践

### 1. 如何选择合适的筛选策略

#### 预设策略对比

| 策略名称 | 适用场景 | 权重配置 | 预期收益/风险 |
|---------|---------|---------|--------------|
| strong_momentum | 短期交易、追涨 | 技术60% + 资金20% | 高收益/高风险 |
| value_growth | 中长期投资 | 基本面60% + 技术30% | 稳健收益/中低风险 |
| capital_inflow | 热点追踪 | 资金40% + 技术40% | 中高收益/中高风险 |

#### 选择建议

**短线交易者：**
```python
# 使用强势动量策略
results = screener.screen(
    preset='strong_momentum',
    top_n=10,
    min_score=75  # 要求高分
)
```

**价值投资者：**
```python
# 使用价值成长策略
results = screener.screen(
    preset='value_growth',
    top_n=20,
    min_score=70
)
```

**热点追踪者：**
```python
# 使用资金流入策略
results = screener.screen(
    preset='capital_inflow',
    top_n=15,
    min_score=65
)
```

### 2. 如何设置合理的筛选条件

#### 股票池选择

**全市场筛选（慎用）：**
```python
# 仅在性能足够且时间充裕时使用
results = screener.screen(
    stock_pool=None,  # 全市场
    parallel=True,
    max_workers=8,  # 使用多线程
    min_score=80  # 提高评分门槛
)
```

**推荐：使用指数成分股：**
```python
# 沪深300成分股
hs300_codes = ['600519', '000001', '600036', ...]

# 中证500成分股
zz500_codes = ['600809', '002271', ...]

results = screener.screen(
    stock_pool=hs300_codes,
    preset='value_growth',
    top_n=30
)
```

**推荐：按行业筛选：**
```python
# 只筛选某个行业
tech_sector_codes = ['600519', '000858', ...]  # 消费行业

results = screener.screen(
    stock_pool=tech_sector_codes,
    preset='strong_momentum'
)
```

#### 评分门槛设置

**严格筛选（精选）：**
```python
results = screener.screen(
    preset='value_growth',
    min_score=80,  # 高门槛
    top_n=10  # 少量精选
)
```

**宽松筛选（广撒网）：**
```python
results = screener.screen(
    preset='capital_inflow',
    min_score=60,  # 中等门槛
    top_n=50  # 大量候选
)
```

#### 自定义权重

根据个人投资风格调整权重：

```python
# 激进型：重技术+资金
aggressive_filters = {
    'use_fundamental': False,
    'use_capital': True,
    'weights': {
        'technical': 0.7,
        'fundamental': 0.0,
        'capital': 0.3
    }
}

# 稳健型：重基本面
conservative_filters = {
    'use_fundamental': True,
    'use_capital': False,
    'weights': {
        'technical': 0.2,
        'fundamental': 0.8,
        'capital': 0.0
    }
}

# 平衡型：均衡权重
balanced_filters = {
    'use_fundamental': True,
    'use_capital': True,
    'weights': {
        'technical': 0.33,
        'fundamental': 0.34,
        'capital': 0.33
    }
}
```

### 3. 如何处理筛选结果

#### 结果分析

```python
# 获取筛选结果
results = screener.screen(preset='strong_momentum', top_n=20)

# 1. 查看综合评分分布
print("评分分布：")
print(results['score'].describe())

# 2. 按技术面排序
tech_sorted = results.sort_values('tech_score', ascending=False)
print("\n技术面TOP 5:")
print(tech_sorted.head()[['code', 'name', 'tech_score']])

# 3. 按基本面排序
fund_sorted = results.sort_values('fundamental_score', ascending=False)
print("\n基本面TOP 5:")
print(fund_sorted.head()[['code', 'name', 'fundamental_score']])

# 4. 查看入选理由
for _, row in results.head().iterrows():
    print(f"\n{row['name']}({row['code']})")
    print(f"  理由: {row['reason']}")
```

#### 二次筛选

```python
# 在结果基础上进一步筛选
results = screener.screen(preset='value_growth', top_n=50)

# 筛选技术面和基本面都好的
excellent = results[
    (results['tech_score'] >= 70) &
    (results['fundamental_score'] >= 80)
]

# 筛选价格在合理区间的
reasonable_price = results[
    (results['current_price'] >= 10) &
    (results['current_price'] <= 100)
]
```

#### 导出结果

```python
# 导出到CSV
results.to_csv('screening_results.csv', index=False, encoding='utf-8-sig')

# 导出到Excel
results.to_excel('screening_results.xlsx', index=False)

# 只导出关键字段
key_columns = ['code', 'name', 'score', 'current_price', 'reason']
results[key_columns].to_csv('screening_simple.csv', index=False)
```

---

## 策略回测最佳实践

### 1. 回测时间周期选择

#### 最小回测周期

**建议：至少1年数据**
```python
# 计算1年前的日期
from datetime import datetime, timedelta
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

results = engine.run_backtest(
    strategy_class=MyStrategy,
    data=data,
    start_date=start_date.strftime('%Y-%m-%d'),
    end_date=end_date.strftime('%Y-%m-%d')
)
```

**不同策略的周期要求：**

| 策略类型 | 最小周期 | 推荐周期 | 原因 |
|---------|---------|---------|------|
| 短线交易 | 3个月 | 6-12个月 | 需要足够的交易样本 |
| 波段交易 | 6个月 | 1-2年 | 覆盖多个波段周期 |
| 趋势跟踪 | 1年 | 2-3年 | 包含完整牛熊周期 |
| 价值投资 | 2年 | 3-5年 | 验证长期表现 |

#### 包含不同市场环境

**推荐：覆盖牛市、熊市、震荡市**

```python
# 2015-2016: 牛转熊
# 2017-2018: 震荡市
# 2019-2020: 结构性牛市
# 2021-2022: 震荡下跌
# 2023-2024: 震荡回升

# 多周期回测
test_periods = [
    ('2019-01-01', '2019-12-31'),  # 上涨期
    ('2021-01-01', '2021-12-31'),  # 震荡期
    ('2022-01-01', '2022-12-31'),  # 下跌期
]

for start, end in test_periods:
    results = engine.run_backtest(
        strategy_class=MyStrategy,
        data=data,
        start_date=start,
        end_date=end
    )
    print(f"{start} ~ {end}: 收益率 {results['total_return']:.2%}")
```

### 2. 参数优化方法

#### 网格搜索

```python
# 优化策略参数
def optimize_parameters(data):
    """参数网格搜索"""
    best_params = None
    best_return = -float('inf')

    # 定义参数范围
    ma_short_range = range(5, 21, 5)  # 5, 10, 15, 20
    ma_long_range = range(30, 61, 10)  # 30, 40, 50, 60

    results_list = []

    for ma_short in ma_short_range:
        for ma_long in ma_long_range:
            if ma_short >= ma_long:
                continue

            # 创建带参数的策略
            class ParamStrategy(MyStrategy):
                params = (
                    ('ma_short', ma_short),
                    ('ma_long', ma_long),
                )

            # 回测
            engine = BacktestEngine(initial_cash=1_000_000)
            results = engine.run_backtest(
                strategy_class=ParamStrategy,
                data=data
            )

            results_list.append({
                'ma_short': ma_short,
                'ma_long': ma_long,
                'return': results['total_return'],
                'sharpe': results['sharpe_ratio'],
                'max_dd': results['max_drawdown']
            })

            # 更新最优参数
            if results['total_return'] > best_return:
                best_return = results['total_return']
                best_params = (ma_short, ma_long)

    # 输出结果
    import pandas as pd
    df = pd.DataFrame(results_list)
    df = df.sort_values('return', ascending=False)

    print("参数优化结果TOP 10:")
    print(df.head(10))

    print(f"\n最优参数: MA短={best_params[0]}, MA长={best_params[1]}")
    print(f"最优收益率: {best_return:.2%}")

    return best_params, df
```

#### 避免过度优化

**危险信号：**
- 回测收益率异常高（>100%）
- 夏普比率异常高（>3）
- 胜率过高（>80%）
- 最大回撤过低（<5%）

**防止过拟合的方法：**

1. **样本外测试**
```python
# 将数据分为训练集和测试集
train_data = data[:'2022-12-31']
test_data = data['2023-01-01':]

# 在训练集上优化参数
best_params = optimize_parameters(train_data)

# 在测试集上验证
results = engine.run_backtest(
    strategy_class=ParamStrategy,
    data=test_data
)

print(f"样本外收益率: {results['total_return']:.2%}")
```

2. **交叉验证**
```python
from sklearn.model_selection import TimeSeriesSplit

tscv = TimeSeriesSplit(n_splits=5)

returns = []
for train_idx, test_idx in tscv.split(data):
    train_data = data.iloc[train_idx]
    test_data = data.iloc[test_idx]

    # 回测
    results = engine.run_backtest(
        strategy_class=MyStrategy,
        data=test_data
    )
    returns.append(results['total_return'])

print(f"平均收益率: {np.mean(returns):.2%}")
print(f"收益率标准差: {np.std(returns):.2%}")
```

3. **关注稳定性指标**
```python
# 不仅看收益率，更要看风险调整后的收益
def evaluate_strategy(results):
    """综合评估策略质量"""
    score = 0

    # 收益率得分（权重30%）
    if results['total_return'] > 0.3:
        score += 30
    elif results['total_return'] > 0.15:
        score += 20
    elif results['total_return'] > 0:
        score += 10

    # 夏普比率得分（权重40%）
    if results['sharpe_ratio'] > 2:
        score += 40
    elif results['sharpe_ratio'] > 1:
        score += 30
    elif results['sharpe_ratio'] > 0.5:
        score += 20

    # 最大回撤得分（权重30%）
    if results['max_drawdown'] < 0.1:
        score += 30
    elif results['max_drawdown'] < 0.2:
        score += 20
    elif results['max_drawdown'] < 0.3:
        score += 10

    return score

# 使用综合得分选择策略
score = evaluate_strategy(results)
print(f"策略综合得分: {score}/100")
```

### 3. 结果解读和策略改进

#### 关键指标解读

```python
def interpret_backtest_results(results):
    """解读回测结果"""
    print("=" * 60)
    print("回测结果解读")
    print("=" * 60)

    # 1. 收益分析
    total_return = results['total_return']
    print(f"\n【收益分析】")
    print(f"总收益率: {total_return:.2%}")

    if total_return > 0.5:
        print("  评级: 优秀")
    elif total_return > 0.2:
        print("  评级: 良好")
    elif total_return > 0:
        print("  评级: 合格")
    else:
        print("  评级: 不合格")

    # 2. 风险分析
    sharpe = results['sharpe_ratio']
    max_dd = results['max_drawdown']

    print(f"\n【风险分析】")
    print(f"夏普比率: {sharpe:.4f}")
    if sharpe > 2:
        print("  评级: 优秀（风险收益比很好）")
    elif sharpe > 1:
        print("  评级: 良好（风险收益比合理）")
    elif sharpe > 0:
        print("  评级: 一般（风险偏高）")
    else:
        print("  评级: 差（风险过高）")

    print(f"\n最大回撤: {max_dd:.2%}")
    if max_dd < 0.1:
        print("  评级: 优秀（回撤控制很好）")
    elif max_dd < 0.2:
        print("  评级: 良好（回撤可接受）")
    elif max_dd < 0.3:
        print("  评级: 一般（回撤偏大）")
    else:
        print("  评级: 差（回撤过大）")

    # 3. 交易分析
    total_trades = results['total_trades']
    win_rate = results['win_rate']

    print(f"\n【交易分析】")
    print(f"总交易次数: {total_trades}")
    print(f"胜率: {win_rate:.2%}")

    if total_trades < 10:
        print("  提示: 交易次数较少，样本可能不足")

    if win_rate > 0.6:
        print("  评级: 优秀")
    elif win_rate > 0.5:
        print("  评级: 良好")
    else:
        print("  评级: 需改进")

    # 4. 综合建议
    print(f"\n【综合建议】")

    if total_return > 0.2 and sharpe > 1 and max_dd < 0.2:
        print("  ✓ 策略表现优秀，可以考虑实盘")
        print("  ✓ 建议：先小资金试运行，观察实盘表现")
    elif total_return > 0 and sharpe > 0.5:
        print("  ○ 策略表现一般，需要优化")
        print("  建议：")
        print("    - 调整止损止盈参数")
        print("    - 优化入场出场条件")
        print("    - 考虑增加过滤条件")
    else:
        print("  ✗ 策略表现不佳，不建议使用")
        print("  建议：")
        print("    - 重新审视策略逻辑")
        print("    - 尝试不同的技术指标组合")
        print("    - 考虑换用其他策略类型")

# 使用
interpret_backtest_results(results)
```

#### 策略改进方向

**收益率低 → 提高盈利能力**
```python
# 改进方向：
# 1. 优化入场时机（更精准的买点）
# 2. 提高止盈水平（让利润充分奔跑）
# 3. 增加交易频率（在合理范围内）
```

**夏普比率低 → 降低风险**
```python
# 改进方向：
# 1. 收紧止损（及时止损）
# 2. 降低仓位（减少单笔风险）
# 3. 增加过滤条件（提高交易质量）
```

**最大回撤大 → 风险控制**
```python
# 改进方向：
# 1. 设置更严格的止损
# 2. 分散投资（不要满仓单只股票）
# 3. 避免逆势交易
```

**胜率低 → 提高准确率**
```python
# 改进方向：
# 1. 增加趋势判断（只在明确趋势中交易）
# 2. 优化技术指标组合
# 3. 增加基本面过滤
```

---

## 实时监控最佳实践

### 1. 如何设置监控列表

#### 持仓股票监控

```python
from src.monitoring.realtime_watcher import RealTimeWatcher
from src.risk.risk_manager import RiskManager

# 创建监控器
watcher = RealTimeWatcher(stock_list=[], update_interval=60)

# 添加持仓股票
risk_mgr = RiskManager(total_capital=1_000_000)

positions = [
    ('600519', '贵州茅台', '白酒', 100, 1650.0),
    ('000858', '五粮液', '白酒', 200, 180.0),
    ('600036', '招商银行', '银行', 1000, 35.0)
]

for code, name, sector, shares, entry_price in positions:
    # 添加到风险管理器
    risk_mgr.add_position(code, name, sector, shares, entry_price, datetime.now())

    # 添加到监控列表
    watcher.add_stock(code, name)

print(f"监控列表: {len(watcher.get_watchlist())}只股票")
```

#### 关注股票监控

```python
# 筛选出的候选股票
from src.screening.screener import StockScreener

screener = StockScreener()
results = screener.screen(
    preset='strong_momentum',
    top_n=10,
    min_score=70
)

# 添加到监控列表
for _, row in results.iterrows():
    watcher.add_stock(row['code'], row['name'])

print(f"添加{len(results)}只候选股票到监控")
```

### 2. 信号优先级设置

#### 三级信号体系

```python
from src.monitoring.alert_manager import AlertManager

alert_mgr = AlertManager()

# 高优先级：紧急风险
alert_mgr.add_rule(
    name='止损触发',
    condition=lambda position: position['current_price'] <= position['stop_loss_price'],
    action='SELL',
    priority='HIGH',
    notification=['email', 'console']
)

# 中优先级：交易机会
alert_mgr.add_rule(
    name='突破买入信号',
    condition=lambda quote: quote['change_pct'] > 0.05,  # 涨幅>5%
    action='BUY',
    priority='MEDIUM',
    notification=['console']
)

# 低优先级：信息提醒
alert_mgr.add_rule(
    name='价格异动',
    condition=lambda quote: abs(quote['change_pct']) > 0.03,
    action='MONITOR',
    priority='LOW',
    notification=['console']
)
```

#### 信号过滤

```python
def filter_alerts(alerts):
    """过滤和优先处理信号"""
    # 按优先级分组
    high_priority = [a for a in alerts if a['priority'] == 'HIGH']
    medium_priority = [a for a in alerts if a['priority'] == 'MEDIUM']
    low_priority = [a for a in alerts if a['priority'] == 'LOW']

    # 先处理高优先级
    if high_priority:
        print(f"\n⚠️ 高优先级信号 ({len(high_priority)}条)")
        for alert in high_priority:
            print(f"  {alert['stock_name']}: {alert['message']}")
            # 立即处理
            handle_high_priority_alert(alert)

    # 再处理中优先级
    if medium_priority:
        print(f"\n📊 中优先级信号 ({len(medium_priority)}条)")
        for alert in medium_priority[:5]:  # 只显示前5条
            print(f"  {alert['stock_name']}: {alert['message']}")

    # 低优先级仅记录
    if low_priority:
        print(f"\nℹ️ 低优先级信号: {len(low_priority)}条（已记录）")
```

### 3. 如何响应不同信号

#### 止损信号

```python
def handle_stop_loss_alert(alert):
    """处理止损信号"""
    stock_code = alert['stock_code']
    stock_name = alert['stock_name']
    current_price = alert['current_price']
    stop_loss_price = alert['stop_loss_price']

    print(f"\n⚠️ 止损触发: {stock_name}({stock_code})")
    print(f"   当前价: {current_price:.2f}")
    print(f"   止损价: {stop_loss_price:.2f}")
    print(f"   建议: 立即卖出")

    # 自动记录
    with open('trading_log.txt', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now()}: 止损 {stock_name} @ {current_price:.2f}\n")

    # 可以对接实盘API自动下单
    # broker.sell(stock_code, shares, current_price)
```

#### 买入信号

```python
def handle_buy_signal(alert):
    """处理买入信号"""
    stock_code = alert['stock_code']
    stock_name = alert['stock_name']
    current_price = alert['current_price']

    print(f"\n📈 买入信号: {stock_name}({stock_code})")
    print(f"   当前价: {current_price:.2f}")

    # 风险检查
    risk_mgr = RiskManager(total_capital=1_000_000)
    check = risk_mgr.check_position_limit(
        stock_code=stock_code,
        stock_name=stock_name,
        sector='未知',
        position_value=current_price * 100  # 假设买100股
    )

    if check['allowed']:
        print(f"   ✓ 风险检查通过")
        print(f"   建议: 可以买入")
        # 记录或下单
    else:
        print(f"   ✗ 风险检查失败: {check['reason']}")
```

#### 信息提醒

```python
def handle_info_alert(alert):
    """处理信息提醒"""
    # 只记录，不需要立即行动
    print(f"ℹ️ {alert['stock_name']}: {alert['message']}")
```

---

## 风险管理最佳实践

### 1. 仓位控制原则

#### 金字塔式仓位管理

```python
class PositionSizing:
    """仓位管理策略"""

    @staticmethod
    def pyramid_sizing(total_capital, confidence_level):
        """
        金字塔式仓位分配

        confidence_level:
            - HIGH: 确信度高的机会
            - MEDIUM: 一般机会
            - LOW: 试探性机会
        """
        if confidence_level == 'HIGH':
            return total_capital * 0.3  # 30%仓位
        elif confidence_level == 'MEDIUM':
            return total_capital * 0.2  # 20%仓位
        else:
            return total_capital * 0.1  # 10%仓位

    @staticmethod
    def diversification_sizing(total_capital, num_stocks):
        """
        分散化仓位分配

        num_stocks: 持仓股票数量
        """
        # 确保单只股票不超过20%
        max_per_stock = total_capital * 0.2
        avg_per_stock = total_capital / num_stocks

        return min(max_per_stock, avg_per_stock)

# 使用示例
total_capital = 1_000_000

# 高确信度机会
high_conf_size = PositionSizing.pyramid_sizing(total_capital, 'HIGH')
print(f"高确信度仓位: {high_conf_size:,.0f}元")

# 分散投资（5只股票）
div_size = PositionSizing.diversification_sizing(total_capital, 5)
print(f"分散化仓位: {div_size:,.0f}元")
```

#### 仓位控制规则

**基本原则：**
1. 单只股票不超过总资金的20%
2. 单个行业不超过总资金的40%
3. 总仓位根据市场环境调整：
   - 牛市：60-80%
   - 震荡市：40-60%
   - 熊市：20-40%

```python
def adjust_position_by_market(base_position, market_condition):
    """根据市场环境调整仓位"""
    if market_condition == 'BULL':
        return base_position * 1.2  # 增加20%
    elif market_condition == 'BEAR':
        return base_position * 0.6  # 减少40%
    else:
        return base_position  # 保持不变
```

### 2. 止损止盈设置

#### 固定百分比止损

```python
def set_stop_loss(entry_price, stop_loss_pct=0.08):
    """
    设置止损价

    Args:
        entry_price: 入场价格
        stop_loss_pct: 止损百分比（默认8%）
    """
    stop_loss_price = entry_price * (1 - stop_loss_pct)
    return round(stop_loss_price, 2)

def set_take_profit(entry_price, take_profit_pct=0.15):
    """
    设置止盈价

    Args:
        entry_price: 入场价格
        take_profit_pct: 止盈百分比（默认15%）
    """
    take_profit_price = entry_price * (1 + take_profit_pct)
    return round(take_profit_price, 2)

# 示例
entry = 50.0
stop_loss = set_stop_loss(entry, 0.08)
take_profit = set_take_profit(entry, 0.15)

print(f"入场价: {entry:.2f}")
print(f"止损价: {stop_loss:.2f} (-8%)")
print(f"止盈价: {take_profit:.2f} (+15%)")
```

#### 移动止损

```python
class TrailingStopLoss:
    """移动止损"""

    def __init__(self, entry_price, trail_pct=0.05):
        """
        初始化移动止损

        Args:
            entry_price: 入场价格
            trail_pct: 移动止损百分比（默认5%）
        """
        self.entry_price = entry_price
        self.trail_pct = trail_pct
        self.highest_price = entry_price
        self.stop_loss = entry_price * (1 - trail_pct)

    def update(self, current_price):
        """更新止损价"""
        # 更新最高价
        if current_price > self.highest_price:
            self.highest_price = current_price
            # 更新止损价
            new_stop = current_price * (1 - self.trail_pct)
            self.stop_loss = max(self.stop_loss, new_stop)

        return self.stop_loss

    def should_stop(self, current_price):
        """判断是否应该止损"""
        return current_price <= self.stop_loss

# 使用示例
tsl = TrailingStopLoss(entry_price=50.0, trail_pct=0.05)

# 模拟价格变动
prices = [50, 52, 55, 53, 51]
for price in prices:
    stop = tsl.update(price)
    should_stop = tsl.should_stop(price)
    print(f"价格: {price:.2f}, 止损: {stop:.2f}, 触发: {should_stop}")
```

#### ATR动态止损

```python
def atr_stop_loss(entry_price, atr_value, multiplier=2.0):
    """
    基于ATR的动态止损

    Args:
        entry_price: 入场价格
        atr_value: ATR指标值
        multiplier: ATR倍数（默认2倍）
    """
    stop_distance = atr_value * multiplier
    stop_loss = entry_price - stop_distance
    return round(stop_loss, 2)

# 示例：ATR = 2.0
entry = 50.0
atr = 2.0
stop = atr_stop_loss(entry, atr, multiplier=2.0)
print(f"入场价: {entry:.2f}")
print(f"ATR: {atr:.2f}")
print(f"止损价: {stop:.2f} (2倍ATR)")
```

### 3. A股特色风险注意事项

#### T+1规则影响

```python
class T1RiskManager:
    """T+1交易规则下的风险管理"""

    def __init__(self):
        self.today_bought = {}  # 今日买入记录

    def can_sell(self, stock_code, buy_date):
        """检查是否可以卖出（T+1限制）"""
        from datetime import datetime, timedelta

        # 计算持有天数
        days_held = (datetime.now().date() - buy_date.date()).days

        if days_held < 1:
            return False, "T+1限制，今日买入不能卖出"
        else:
            return True, "可以卖出"

    def record_buy(self, stock_code):
        """记录买入"""
        self.today_bought[stock_code] = datetime.now()

    def get_sellable_stocks(self):
        """获取可卖出的股票"""
        sellable = []
        for code, buy_time in self.today_bought.items():
            can_sell, _ = self.can_sell(code, buy_time)
            if can_sell:
                sellable.append(code)
        return sellable

# 使用
t1_mgr = T1RiskManager()
t1_mgr.record_buy('600519')

# 检查能否卖出
can_sell, reason = t1_mgr.can_sell('600519', datetime.now())
print(f"能否卖出: {can_sell}, 原因: {reason}")
```

#### 涨跌停限制

```python
def get_price_limit(stock_code, yesterday_close):
    """
    计算涨跌停价格

    Args:
        stock_code: 股票代码
        yesterday_close: 昨日收盘价
    """
    # 判断板块
    if stock_code.startswith('688') or stock_code.startswith('300'):
        # 科创板/创业板：±20%
        limit_pct = 0.20
    else:
        # 主板：±10%
        limit_pct = 0.10

    upper_limit = round(yesterday_close * (1 + limit_pct), 2)
    lower_limit = round(yesterday_close * (1 - limit_pct), 2)

    return {
        'upper_limit': upper_limit,
        'lower_limit': lower_limit,
        'limit_pct': limit_pct
    }

# 示例
limits = get_price_limit('600519', 1650.0)
print(f"涨停价: {limits['upper_limit']:.2f}")
print(f"跌停价: {limits['lower_limit']:.2f}")
print(f"涨跌幅限制: ±{limits['limit_pct']*100:.0f}%")
```

#### ST股票风险

```python
def check_st_risk(stock_code, stock_name):
    """检查ST股票风险"""
    st_patterns = ['ST', '*ST', 'S*ST', 'SST']

    # 检查股票名称
    for pattern in st_patterns:
        if pattern in stock_name:
            risk_level = 'HIGH' if '*ST' in stock_name else 'MEDIUM'
            return {
                'is_st': True,
                'risk_level': risk_level,
                'warning': f'{stock_name}属于{pattern}股票，存在退市风险'
            }

    return {
        'is_st': False,
        'risk_level': 'LOW',
        'warning': None
    }

# 使用
risk = check_st_risk('600123', 'ST股票')
if risk['is_st']:
    print(f"⚠️ 风险警告: {risk['warning']}")
    print(f"   风险等级: {risk['risk_level']}")
```

#### 单日交易限额

```python
class DailyTradingLimit:
    """单日交易限额管理"""

    def __init__(self, daily_limit=100000):
        self.daily_limit = daily_limit
        self.today_trades = 0
        self.last_reset = datetime.now().date()

    def check_limit(self, trade_amount):
        """检查是否超过限额"""
        # 如果是新的一天，重置计数
        if datetime.now().date() > self.last_reset:
            self.today_trades = 0
            self.last_reset = datetime.now().date()

        # 检查限额
        if self.today_trades + trade_amount > self.daily_limit:
            remaining = self.daily_limit - self.today_trades
            return {
                'allowed': False,
                'reason': f'超过单日交易限额，剩余额度: {remaining:,.0f}元',
                'remaining': remaining
            }
        else:
            return {
                'allowed': True,
                'reason': '在限额范围内',
                'remaining': self.daily_limit - self.today_trades - trade_amount
            }

    def record_trade(self, trade_amount):
        """记录交易"""
        self.today_trades += trade_amount

# 使用
limit_mgr = DailyTradingLimit(daily_limit=100000)

check = limit_mgr.check_limit(50000)
if check['allowed']:
    print(f"✓ 可以交易，剩余额度: {check['remaining']:,.0f}元")
    limit_mgr.record_trade(50000)
```

---

## 完整工作流程

### 从筛选到监控的完整流程

参考 `examples/complete_workflow.py` 了解详细实现。

**基本流程：**
1. 批量筛选候选股票
2. 深度分析TOP股票
3. 回测验证策略
4. 添加到监控列表
5. 实时监控和风险管理

---

## 常见陷阱和注意事项

### 1. 过度交易
- 避免频繁买卖
- 设置最小持仓周期
- 考虑交易成本

### 2. 追涨杀跌
- 遵守既定策略
- 不要被情绪左右
- 设置纪律性止损

### 3. 重仓单只股票
- 严格控制单只股票仓位
- 做好分散投资
- 避免ALL IN

### 4. 忽视风险管理
- 始终设置止损
- 定期评估组合风险
- 及时调整仓位

### 5. 过度优化
- 避免参数过拟合
- 重视样本外测试
- 关注策略稳定性

### 6. 忽视交易成本
- 考虑佣金和印花税
- 减少不必要的交易
- 计算实际收益时扣除成本

### 7. 数据质量问题
- 使用可靠的数据源
- 定期检查数据完整性
- 处理异常值

---

## 总结

遵循这些最佳实践，可以：
- 提高分析效率和准确性
- 降低投资风险
- 提升策略稳定性
- 实现可持续的收益

记住：**纪律和风险管理永远比收益率更重要！**
