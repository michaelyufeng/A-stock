# 选股筛选策略速查表

## 快速选择指南

### 按投资风格选择

| 投资风格 | 推荐策略 | 命令 |
|---------|---------|------|
| 保守价值投资 | low_pe_value, high_dividend | `--preset low_pe_value` |
| 稳健成长投资 | value_growth, institutional_favorite | `--preset value_growth` |
| 激进趋势交易 | breakout, strong_momentum | `--preset breakout` |
| 短线交易 | oversold_rebound, strong_momentum | `--preset oversold_rebound` |
| 收益型投资 | high_dividend | `--preset high_dividend` |
| 跟随机构 | institutional_favorite | `--preset institutional_favorite` |

---

## 8种策略一览表

| # | 策略代码 | 中文名称 | 风险 | 周期 | 核心指标 | 一句话描述 |
|---|---------|---------|------|------|---------|-----------|
| 1 | strong_momentum | 强势动量股 | 中高 | 短期 | 技术60%+资金20% | 技术面强势，适合短线 |
| 2 | value_growth | 价值成长股 | 中 | 中长期 | 基本面60%+技术30% | 基本面优秀，适合价投 |
| 3 | capital_inflow | 资金流入股 | 中高 | 短中期 | 资金40%+技术40% | 主力资金流入，追热点 |
| 4 | **low_pe_value** | **低PE价值股** | **低** | **中长期** | **PE<15, ROE>10%** | **低估值优质股** |
| 5 | **high_dividend** | **高股息率股** | **低** | **长期** | **股息率>3%** | **稳定现金流** |
| 6 | **breakout** | **突破新高股** | **中高** | **短中期** | **突破20日新高+放量** | **趋势跟踪** |
| 7 | **oversold_rebound** | **超卖反弹股** | **高** | **短期** | **RSI<30后反弹** | **均值回归** |
| 8 | **institutional_favorite** | **机构重仓股** | **中** | **中长期** | **机构持仓>30%** | **跟随聪明钱** |

---

## 使用命令速查

### 基础命令格式
```bash
python scripts/run_screening.py --preset [策略代码] [选项]
```

### 常用选项
| 选项 | 说明 | 示例 |
|------|------|------|
| `--top N` | 返回TOP N只股票 | `--top 30` |
| `--min-score N` | 最低评分 | `--min-score 70` |
| `--output FILE` | 导出文件 | `--output result.csv` |
| `--max-workers N` | 并行线程数 | `--max-workers 10` |
| `--no-parallel` | 禁用并行 | `--no-parallel` |

### 快速命令示例

```bash
# 低PE价值股（TOP 30）
python scripts/run_screening.py --preset low_pe_value --top 30

# 高股息股（导出Excel）
python scripts/run_screening.py --preset high_dividend --output dividends.xlsx

# 突破新高股（高分）
python scripts/run_screening.py --preset breakout --min-score 70

# 超卖反弹（短线15只）
python scripts/run_screening.py --preset oversold_rebound --top 15

# 机构重仓（TOP 40）
python scripts/run_screening.py --preset institutional_favorite --top 40
```

---

## 策略特征对比

### 权重分配

| 策略 | 技术面 | 基本面 | 资金面 |
|------|--------|--------|--------|
| strong_momentum | 60% | 20% | 20% |
| value_growth | 30% | 60% | 10% |
| capital_inflow | 40% | 20% | 40% |
| **low_pe_value** | **30%** | **60%** | **10%** |
| **high_dividend** | **20%** | **70%** | **10%** |
| **breakout** | **60%** | **10%** | **30%** |
| **oversold_rebound** | **70%** | **15%** | **15%** |
| **institutional_favorite** | **20%** | **50%** | **30%** |

### 风险-收益特征

```
高收益
  ↑
  │  oversold_rebound (高风险高收益)
  │       ↗
  │  breakout, strong_momentum (中高风险)
  │       ↗
  │  capital_inflow, institutional_favorite (中等)
  │       ↗
  │  value_growth (中低风险)
  │       ↗
  │  low_pe_value, high_dividend (低风险稳健)
  └────────────────────────────→ 高风险
```

---

## 适用市场环境

| 市场环境 | 推荐策略 | 说明 |
|---------|---------|------|
| 牛市上涨 | breakout, strong_momentum | 追涨强势股 |
| 震荡市 | low_pe_value, high_dividend | 防御性配置 |
| 熊市下跌 | high_dividend, institutional_favorite | 稳健价值股 |
| 反弹初期 | oversold_rebound, capital_inflow | 捕捉反弹 |
| 结构性行情 | value_growth, institutional_favorite | 精选个股 |

---

## 持仓周期建议

| 策略 | 建议持仓周期 | 止损建议 | 止盈建议 |
|------|-------------|---------|---------|
| strong_momentum | 3-10天 | 3-5% | 10-15% |
| value_growth | 3-12个月 | 15-20% | 30-50% |
| capital_inflow | 5-20天 | 5-8% | 15-25% |
| **low_pe_value** | **6-24个月** | **20-25%** | **50-100%** |
| **high_dividend** | **12个月以上** | **15-20%** | **持有收息** |
| **breakout** | **5-15天** | **3-5%** | **10-20%** |
| **oversold_rebound** | **1-3天** | **2-3%** | **5-8%** |
| **institutional_favorite** | **6-18个月** | **15-20%** | **40-60%** |

---

## 注意事项速查

### ⚠️ 高风险策略（需要经验）
- **oversold_rebound**: 快进快出，严格止损
- **breakout**: 注意追高风险，设置止损

### ✓ 低风险策略（适合新手）
- **high_dividend**: 稳定分红，长期持有
- **low_pe_value**: 价值投资，耐心持有

### 💡 中等风险策略（需要判断）
- **institutional_favorite**: 关注机构动向
- **value_growth**: 需要基本面分析能力

---

## 组合建议

### 保守组合（低风险）
```bash
# 40% 高股息
python scripts/run_screening.py --preset high_dividend --top 10

# 40% 低PE价值
python scripts/run_screening.py --preset low_pe_value --top 10

# 20% 机构重仓
python scripts/run_screening.py --preset institutional_favorite --top 5
```

### 稳健组合（中等风险）
```bash
# 30% 价值成长
python scripts/run_screening.py --preset value_growth --top 8

# 30% 低PE价值
python scripts/run_screening.py --preset low_pe_value --top 8

# 40% 机构重仓
python scripts/run_screening.py --preset institutional_favorite --top 10
```

### 激进组合（高风险）
```bash
# 40% 突破新高
python scripts/run_screening.py --preset breakout --top 10

# 30% 强势动量
python scripts/run_screening.py --preset strong_momentum --top 8

# 30% 超卖反弹
python scripts/run_screening.py --preset oversold_rebound --top 8
```

---

## 常见问题

### Q: 哪个策略最适合新手？
A: **high_dividend**（高股息）或 **low_pe_value**（低PE价值），风险低，容易理解。

### Q: 如何快速筛选强势股？
A: 使用 **breakout**（突破新高）或 **strong_momentum**（强势动量），但注意止损。

### Q: 想跟随机构投资，用哪个？
A: **institutional_favorite**（机构重仓），但要注意数据延迟。

### Q: 短线交易用什么策略？
A: **oversold_rebound**（超卖反弹），但需要丰富经验和严格止损。

### Q: 如何获得稳定收益？
A: **high_dividend**（高股息），追求稳定分红，长期持有。

### Q: 筛选耗时多久？
A: 全市场10-30分钟，指定股票池1-5分钟（取决于数量和网络）。

---

## 性能提示

### 加速筛选
```bash
# 增加并行线程（推荐5-10）
python scripts/run_screening.py --preset low_pe_value --max-workers 10
```

### 节省时间
```bash
# 先筛小范围，确认后再全市场
python scripts/run_screening.py --preset breakout --top 20
```

### 避免限流
```bash
# 如遇API限流，使用串行处理
python scripts/run_screening.py --preset value_growth --no-parallel
```

---

## 更新日志

- **2026-01-29**: 新增5种策略（v2.0.0）
  - low_pe_value（低PE价值股）
  - high_dividend（高股息率股）
  - breakout（突破新高股）
  - oversold_rebound（超卖反弹股）
  - institutional_favorite（机构重仓股）

---

**快速开始**:
```bash
# 试试低PE价值股（最简单）
python scripts/run_screening.py --preset low_pe_value --top 20

# 查看所有策略
python scripts/run_screening.py --help
```

**详细文档**:
- `/docs/screening_usage.md` - 详细使用指南
- `/docs/screening_presets_changelog.md` - 更新日志
- `/docs/USER_GUIDE.md` - 用户指南
