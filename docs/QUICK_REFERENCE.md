# A股量化交易系统快速参考

## 核心模块速查

### 1. 股票分析

**快速分析**（不消耗API额度）:
```python
from src.reporting.stock_report import analyze_stock
result = analyze_stock('600519', depth='quick')
```

**完整分析**（含AI评级）:
```python
result = analyze_stock('600519', depth='full')  # 需要API key
```

**关键输出**:
- `technical_score`: 技术面评分 (0-100)
- `fundamental_score`: 基本面评分 (0-100)
- `capital_score`: 资金面评分 (0-100)
- `ai_rating`: AI综合评级
- `recommendation`: 投资建议

---

### 2. 批量筛选

**使用预设策略**:
```python
from src.screening.screener import StockScreener

screener = StockScreener()

# 强势动量股（短线）
results = screener.screen(preset='strong_momentum', top_n=20)

# 价值成长股（长线）
results = screener.screen(preset='value_growth', top_n=20)

# 资金流入股（热点）
results = screener.screen(preset='capital_inflow', top_n=20)
```

**自定义筛选**:
```python
custom_filters = {
    'use_fundamental': True,
    'use_capital': True,
    'weights': {
        'technical': 0.4,    # 技术面40%
        'fundamental': 0.4,  # 基本面40%
        'capital': 0.2       # 资金面20%
    }
}

results = screener.screen(filters=custom_filters, top_n=30)
```

---

### 3. 策略回测

**基础回测**:
```python
from src.backtest.engine import BacktestEngine
from src.strategy.short_term.momentum import MomentumStrategy

engine = BacktestEngine(
    initial_cash=1_000_000,
    commission=0.0003,
    stamp_tax=0.001
)

results = engine.run_backtest(
    strategy_class=MomentumStrategy,
    data=your_data,
    stock_code='600519'
)
```

**关键指标**:
- `total_return`: 总收益率
- `sharpe_ratio`: 夏普比率
- `max_drawdown`: 最大回撤
- `win_rate`: 胜率

---

### 4. 实时监控

**创建监控器**:
```python
from src.monitoring.realtime_watcher import RealTimeWatcher

watcher = RealTimeWatcher(
    stock_list=[
        {'code': '600519', 'name': '贵州茅台'},
        {'code': '000858', 'name': '五粮液'}
    ],
    update_interval=60  # 60秒更新一次
)

# 添加股票
watcher.add_stock('600036', '招商银行')

# 获取行情
quote = watcher.get_latest_quote('600519')
all_quotes = watcher.get_all_quotes()
```

**配置告警**:
```python
from src.monitoring.alert_manager import AlertManager

alert_mgr = AlertManager()

# 添加告警规则
alert_mgr.add_rule(
    name='大幅下跌',
    condition=lambda quote: quote.get('change_pct', 0) < -0.03,
    action='WARNING',
    priority='HIGH',
    notification=['console', 'email']
)
```

---

### 5. 风险管理

**创建风险管理器**:
```python
from src.risk.risk_manager import RiskManager

risk_mgr = RiskManager(total_capital=1_000_000)

# 检查仓位限制
check = risk_mgr.check_position_limit(
    stock_code='600519',
    stock_name='贵州茅台',
    sector='白酒',
    position_value=200_000
)

if check['allowed']:
    # 添加持仓
    risk_mgr.add_position(
        stock_code='600519',
        stock_name='贵州茅台',
        sector='白酒',
        shares=100,
        entry_price=1650.0,
        entry_time=datetime.now()
    )
```

**设置止损止盈**:
```python
# 自动计算止损止盈
position = risk_mgr.get_position('600519')
stop_loss = position['stop_loss_price']    # 默认-8%
take_profit = position['take_profit_price']  # 默认+15%
```

---

## 评分体系速查

### 技术面评分
- **80-100分**: 强势，适合短期交易
- **60-79分**: 中性偏强，技术面健康
- **40-59分**: 中性，观察为主
- **0-39分**: 弱势，技术面较差

### 基本面评分
- **80-100分**: 优秀企业，财务健康
- **60-79分**: 良好，基本面稳健
- **40-59分**: 一般，关注风险
- **0-39分**: 较差，财务堪忧

### 资金面评分
- **70-100分**: 主力流入，关注度高
- **50-69分**: 资金平衡
- **0-49分**: 资金流出，谨慎

---

## 预设筛选策略对比

| 策略 | 适用场景 | 权重配置 | 风险 |
|-----|---------|---------|------|
| strong_momentum | 短线交易 | 技术60% + 资金20% + 基本面20% | 高 |
| value_growth | 长线投资 | 基本面60% + 技术30% + 资金10% | 低 |
| capital_inflow | 热点追踪 | 资金40% + 技术40% + 基本面20% | 中 |

---

## 回测参数建议

### 最小回测周期
- **短线策略**: 3-6个月
- **波段策略**: 6-12个月
- **趋势跟踪**: 1-2年
- **价值投资**: 2-3年

### 参数优化范围
```python
# MA策略参数
ma_short: 5-20
ma_long: 30-60

# RSI策略参数
rsi_period: 10-20
rsi_oversold: 20-35
rsi_overbought: 65-80
```

### 评估标准
- **收益率**: >15% (年化)
- **夏普比率**: >1.0
- **最大回撤**: <20%
- **胜率**: >50%

---

## 风险控制参数

### 仓位限制
- **单只股票**: ≤20% 总资金
- **单个行业**: ≤40% 总资金
- **总仓位**:
  - 牛市 60-80%
  - 震荡市 40-60%
  - 熊市 20-40%

### 止损止盈
- **止损**: 默认 -8%
- **止盈**: 默认 +15%
- **移动止损**: 5% trailing

### A股特色规则
- **T+1**: 当日买入次日才能卖出
- **涨跌停**:
  - 主板 ±10%
  - 科创板/创业板 ±20%
- **交易费用**:
  - 佣金 0.03%
  - 印花税 0.1% (卖出)

---

## 常用命令

### 分析单只股票
```bash
python scripts/analyze_stock.py --code 600519 --depth full
```

### 批量筛选
```bash
python scripts/run_screening.py --preset strong_momentum --top 20
```

### 策略回测
```bash
python scripts/run_backtest.py \
  --strategy momentum \
  --code 600519 \
  --start 2023-01-01 \
  --end 2024-01-01
```

### 实时监控
```bash
python scripts/daily_monitor.py --watch-list stocks.txt
```

---

## 示例代码

### 完整工作流
```bash
python examples/complete_workflow.py
```

### 自定义筛选
```bash
python examples/custom_screening.py
```

---

## 配置文件位置

- **环境变量**: `.env`
- **风控规则**: `config/risk_rules.yaml`
- **监控配置**: `config/monitoring.yaml`
- **告警配置**: `config/alerts.yaml`

---

## 日志和数据

- **日志目录**: `logs/`
- **数据缓存**: `data/cache/`
- **数据库**: `data/storage/a_stock.db`
- **报告输出**: `reports/`

---

## 文档链接

- [完整用户指南](USER_GUIDE.md)
- [配置指南](CONFIGURATION_GUIDE.md)
- [最佳实践](BEST_PRACTICES.md)
- [筛选使用](screening_usage.md)
- [回测指标](backtest_metrics_guide.md)
- [监控指南](realtime_watcher_guide.md)
- [风控指南](risk_manager_guide.md)

---

## 快速故障排查

### 问题1: API调用失败
```
检查: .env文件中的DEEPSEEK_API_KEY是否正确
解决: 重新设置API密钥或使用depth='quick'
```

### 问题2: 数据获取失败
```
检查: 网络连接是否正常
解决: 检查akshare是否可以访问，清除缓存重试
```

### 问题3: 回测失败
```
检查: 数据是否足够（至少60天）
解决: 增加回测周期或更换股票
```

### 问题4: 内存不足
```
检查: 是否加载过多数据
解决: 减少股票池大小，启用并行处理限制worker数量
```

---

## 获取帮助

- 查看详细文档: `docs/`目录
- 运行示例代码: `examples/`目录
- 查看测试用例: `tests/`目录
- GitHub Issues: 提交问题和建议

---

**最后更新**: 2026-01-29
**版本**: 1.0.0
