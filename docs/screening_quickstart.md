# 选股筛选器快速开始

## 5分钟上手指南

### 1. 导入模块

```python
from src.screening.screener import StockScreener

# 创建筛选器实例
screener = StockScreener()
```

### 2. 使用预设方案（最简单）

```python
# 筛选强势动量股
results = screener.screen(
    stock_pool=['600519', '000001', '600036'],  # 指定股票
    preset='strong_momentum',                    # 预设方案
    top_n=10                                     # 返回TOP 10
)

# 查看结果
print(results[['code', 'name', 'score', 'reason']])
```

### 3. 三种预设方案

| 方案 | 适用场景 | 权重配置 |
|------|---------|---------|
| `strong_momentum` | 短期交易 | 技术60% + 资金20% + 基本20% |
| `value_growth` | 长期投资 | 基本60% + 技术30% + 资金10% |
| `capital_inflow` | 热点追踪 | 资金40% + 技术40% + 基本20% |

### 4. 自定义筛选

```python
# 自定义筛选条件
results = screener.screen(
    stock_pool=['600519', '000001'],
    filters={
        'use_fundamental': True,
        'use_capital': True,
        'weights': {
            'technical': 0.4,
            'fundamental': 0.4,
            'capital': 0.2
        }
    },
    min_score=70  # 最低评分
)
```

### 5. 全市场筛选（并行）

```python
# 从全市场筛选（需要较长时间）
results = screener.screen(
    stock_pool=None,        # None = 全市场
    preset='value_growth',
    top_n=20,
    parallel=True,          # 开启并行
    max_workers=5           # 5个线程
)
```

### 6. 查看结果

```python
# 筛选结果是一个DataFrame
print(results.head())

# 结果列说明:
# - code: 股票代码
# - name: 股票名称
# - score: 综合评分 (0-100)
# - tech_score: 技术面评分
# - fundamental_score: 基本面评分
# - capital_score: 资金面评分
# - current_price: 当前价格
# - reason: 入选理由

# 按技术面排序
top_tech = results.nlargest(5, 'tech_score')

# 按基本面排序
top_fundamental = results.nlargest(5, 'fundamental_score')
```

### 7. 运行示例

```bash
# 完整示例
python examples/screening_example.py

# 运行测试
pytest tests/screening/ -v
```

---

## 常用场景

### 场景1: 找强势突破股

```python
results = screener.screen(
    preset='strong_momentum',
    min_score=70,
    top_n=10
)
```

### 场景2: 找价值成长股

```python
results = screener.screen(
    preset='value_growth',
    min_score=75,
    top_n=20
)
```

### 场景3: 追踪资金热点

```python
results = screener.screen(
    preset='capital_inflow',
    min_score=65,
    top_n=30
)
```

---

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `stock_pool` | 股票池（None=全市场） | None |
| `preset` | 预设方案名称 | None |
| `filters` | 自定义筛选条件 | None |
| `top_n` | 返回TOP N只股票 | 20 |
| `min_score` | 最低综合评分 | 60.0 |
| `parallel` | 是否并行处理 | True |
| `max_workers` | 最大线程数 | 5 |

---

## 注意事项

1. **首次运行**: 需要网络连接获取数据
2. **API限制**: 全市场筛选调用次数多，注意限流
3. **小股票池**: <10只建议用 `parallel=False`
4. **数据缓存**: 利用缓存加速重复查询

---

## 更多信息

- **详细文档**: `docs/screening_usage.md`
- **示例代码**: `examples/screening_example.py`
- **测试用例**: `tests/screening/test_screener.py`

---

快速开始就是这么简单！祝选股顺利！📈
