# A股量化交易分析系统

一个功能完整的A股量化交易分析系统，支持技术分析、基本面分析、资金面分析、AI评级、策略回测、选股筛选和实时监控。

## 功能特性

- **多维度分析**：技术面 + 基本面 + 资金面 + AI综合评级
- **策略回测**：基于backtrader的回测引擎，支持A股T+1规则
- **选股筛选**：批量筛选优质股票，多条件组合过滤
- **实时监控**：持仓监控，关键信号推送
- **风险管理**：仓位控制、止损止盈、A股特色风控

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，填入DeepSeek API密钥
```

### 使用示例

```bash
# 分析单只股票
python scripts/analyze_stock.py --code 600519

# 批量筛选股票
python scripts/run_screening.py --preset strong_momentum --top 20

# 策略回测
python scripts/run_backtest.py --strategy momentum --code 600519 --start 2023-01-01

# 实时监控
python scripts/daily_monitor.py --watch-list my_stocks.txt
```

## 项目结构

```
A-stock/
├── config/           # 配置文件
├── src/              # 源代码
│   ├── core/         # 核心模块
│   ├── data/         # 数据获取层
│   ├── analysis/     # 分析模块
│   ├── strategy/     # 策略模块
│   ├── backtest/     # 回测模块
│   ├── screening/    # 选股模块
│   ├── monitoring/   # 监控模块
│   ├── risk/         # 风控模块
│   └── reporting/    # 报告模块
├── data/             # 数据存储
├── scripts/          # 脚本
└── tests/            # 测试
```

## 技术栈

- **数据源**：AKShare
- **AI分析**：DeepSeek API
- **回测框架**：backtrader
- **技术指标**：pandas_ta
- **数据存储**：SQLite

## 许可证

MIT License
