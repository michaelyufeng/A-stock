# 报告生成模块

## 概述

报告生成模块负责将股票分析结果转换为易读的Markdown格式报告。支持买入、持有、卖出三种评级，包含技术面、基本面、资金面的详细分析。

## 核心类

### StockReportGenerator

生成综合股票分析报告的主类。

#### 主要功能

1. **生成Markdown报告** - 将分析结果格式化为结构化的Markdown文档
2. **支持三种评级** - 买入(buy)、持有(hold)、卖出(sell)
3. **A股特色** - 包含T+1风险、涨跌停板等A股特有风险提示
4. **技术指标表格** - 自动从K线数据生成技术指标分析表
5. **文件保存** - 支持保存报告到本地文件

## 使用方法

### 基础用法

```python
from src.reporting.stock_report import StockReportGenerator

# 准备分析结果（来自StockRater）
analysis_result = {
    'rating': 'buy',
    'confidence': 8.5,
    'target_price': 15.80,
    'stop_loss': 13.50,
    'reasons': ['技术面强势', '基本面良好'],
    'risks': ['市场波动风险'],
    'a_share_risks': ['T+1限制'],
    'ai_insights': 'AI分析内容...',
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
```

### 包含K线数据

```python
import pandas as pd

# K线数据（包含技术指标）
kline_df = pd.DataFrame({
    'date': [...],
    'close': [...],
    'MA5': [...],
    'MA20': [...],
    'MACD': [...],
    'RSI': [...],
    # 更多技术指标...
})

# 生成包含技术指标详情的报告
report = generator.generate_report(
    stock_code='000001',
    stock_name='平安银行',
    analysis_result=analysis_result,
    kline_df=kline_df  # 提供K线数据
)
```

### 保存到文件

```python
# 保存到指定路径
report = generator.generate_report(
    stock_code='000001',
    stock_name='平安银行',
    analysis_result=analysis_result,
    save_to_file=True,
    output_path='./reports/stock_report_000001.md'
)

# 使用默认路径（当前目录/stock_report_{code}.md）
report = generator.generate_report(
    stock_code='000001',
    stock_name='平安银行',
    analysis_result=analysis_result,
    save_to_file=True
)
```

## 报告结构

生成的报告包含以下部分：

1. **标题和时间戳** - 股票代码、名称、生成时间
2. **投资决策** - 评级、目标价、止损价、信心度
3. **核心理由** - 买入/持有/卖出的主要原因
4. **风险提示** - 通用风险 + A股特色风险
5. **详细分析**
   - 技术面分析（含技术指标表格）
   - 基本面分析
   - 资金面分析
6. **AI综合分析** - DeepSeek生成的深度分析
7. **综合评分** - 各维度评分汇总表
8. **免责声明** - 投资风险提示

## 技术指标表格

如果提供K线数据，报告会自动生成技术指标表格，包括：

- **MA5/MA20** - 均线系统（金叉/死叉）
- **MACD** - 趋势指标（多头/空头）
- **RSI** - 相对强弱指标（超买/超卖/中性）
- **KDJ** - 随机指标（金叉/死叉）
- **布林带** - 价格区间（超买/超卖区）
- **成交量** - 量能分析（放量/缩量）
- **ATR** - 波动率（高/中/低波动）

## 评分等级

分数解释：

- **80-100分** - 优秀
- **65-79分** - 良好
- **45-64分** - 一般
- **0-44分** - 较差

## 评级翻译

- `buy` → 买入
- `hold` → 持有
- `sell` → 卖出

## A股特色风险

报告自动包含以下A股特有风险提示：

1. **T+1交易制度** - 当日买入次日才能卖出
2. **涨跌停板** - 10%/20%涨跌幅限制
3. **ST股票** - 退市风险警示
4. **分批建仓** - 降低风险策略

## 文件格式

生成的报告为标准Markdown格式，支持：

- ✅ GitHub Markdown
- ✅ Obsidian
- ✅ Typora
- ✅ VS Code Preview
- ✅ 任何Markdown查看器

## 示例

完整示例请参考：`examples/report_generation_example.py`

## 测试

```bash
# 运行所有测试
pytest tests/reporting/ -v

# 运行特定测试
pytest tests/reporting/test_stock_report.py -v

# 运行集成测试
pytest tests/reporting/test_integration.py -v
```

## 依赖

- `pandas` - 数据处理
- `datetime` - 时间戳格式化
- `pathlib` - 文件路径操作

## 注意事项

1. **analysis_result格式** - 必须包含所有必需字段（rating, confidence, scores等）
2. **K线数据可选** - 不提供K线数据时，技术指标表格将被省略
3. **文件编码** - 保存文件使用UTF-8编码
4. **路径处理** - 自动创建不存在的父目录

## 未来改进

- [ ] 支持PDF格式导出
- [ ] 添加图表嵌入（matplotlib）
- [ ] 支持自定义模板
- [ ] 多语言支持（英文）
- [ ] HTML格式导出
