# HTML报告功能文档

## 概述

HTML报告功能为A股量化交易系统提供了专业、美观的HTML格式股票分析报告。相比传统的文本或Markdown报告，HTML报告提供：

- 响应式设计，支持移动端和桌面端
- 可视化评分雷达图（使用Chart.js）
- 现代化的UI设计和交互体验
- 安全的数据渲染（自动XSS防护）
- 打印友好的样式

## 功能特性

### 1. 核心功能

- **多维度评分可视化**：技术面、基本面、资金面、情绪面的雷达图展示
- **响应式布局**：自动适配不同屏幕尺寸（手机、平板、电脑）
- **专业配色方案**：买入/卖出/持有评级使用不同的渐变色方案
- **交互式图表**：Chart.js驱动的动态雷达图
- **安全性保障**：Jinja2自动转义防止XSS攻击

### 2. 报告内容

HTML报告包含以下核心板块：

#### 标题区域
- 股票代码和名称
- 报告生成时间
- 分析模式标识（快速/完整）

#### 投资决策摘要
- 投资评级（买入/持有/卖出）
- 综合评分（0-100分）
- 信心度（1-10分）

#### 操作建议
- 目标价格
- 止损价格
- 信心度说明

#### 多维度评分
- 可视化雷达图
- 各维度评分徽章
- 分数等级标识（优秀/良好/一般/较差）

#### 核心理由
- 支持评级的主要原因列表
- 清晰的条目展示

#### AI综合分析
- AI生成的综合洞察（完整模式）
- 规则引擎分析（快速模式）

#### 风险提示
- 通用风险警示
- A股特色风险提醒

#### 免责声明
- 法律免责声明
- 投资风险提示

## 使用方法

### 1. 命令行使用

#### 基础使用
```bash
# 分析股票并生成HTML报告
python scripts/analyze_stock.py --code 600519 --html-output report.html
```

#### 快速分析模式
```bash
# 快速分析（仅技术面+资金面）
python scripts/analyze_stock.py --code 600519 --depth quick --html-output quick_report.html
```

#### 同时生成多种格式
```bash
# 同时生成Markdown和HTML报告
python scripts/analyze_stock.py --code 600519 \
    --output report.md \
    --html-output report.html
```

#### 完整分析
```bash
# 完整分析（技术+基本+资金+AI）
python scripts/analyze_stock.py --code 600519 \
    --depth full \
    --html-output 600519_full_analysis.html
```

### 2. Python代码使用

#### 基础示例
```python
from src.reporting.html_reporter import HTMLReporter

# 准备分析结果
analysis_result = {
    'rating': 'buy',
    'confidence': 8.5,
    'target_price': 120.50,
    'stop_loss': 95.00,
    'reasons': ['技术面强势', '资金流入'],
    'risks': ['市场波动风险'],
    'a_share_risks': ['T+1交易制度'],
    'ai_insights': 'AI综合分析...',
    'scores': {
        'technical': 85.50,
        'fundamental': 78.30,
        'capital': 82.00,
        'overall': 81.95
    }
}

# 创建报告生成器
reporter = HTMLReporter()

# 生成HTML报告
html_content = reporter.generate_report(
    stock_code='600519',
    stock_name='贵州茅台',
    analysis_result=analysis_result
)

# 保存到文件
html_content = reporter.generate_report(
    stock_code='600519',
    stock_name='贵州茅台',
    analysis_result=analysis_result,
    save_to_file=True,
    output_path='report.html'
)
```

#### 集成到工作流
```python
from scripts.analyze_stock import analyze_stock, save_html_report, get_stock_name

# 执行分析
stock_code = '600519'
result = analyze_stock(stock_code, depth='full')

# 获取股票名称
stock_name = get_stock_name(stock_code)

# 生成HTML报告
save_html_report(stock_code, stock_name, result, 'analysis_report.html')
```

## 技术实现

### 1. 架构设计

```
src/reporting/
├── html_reporter.py          # HTMLReporter核心类
└── templates/
    └── stock_analysis.html   # Jinja2 HTML模板
```

### 2. 主要组件

#### HTMLReporter类

```python
class HTMLReporter:
    """HTML格式股票分析报告生成器"""

    def __init__(self):
        """初始化，设置Jinja2环境"""

    def generate_report(
        self,
        stock_code: str,
        stock_name: str,
        analysis_result: Dict[str, Any],
        save_to_file: bool = False,
        output_path: Optional[str] = None
    ) -> str:
        """生成HTML报告"""

    def _prepare_template_data(self, ...) -> Dict[str, Any]:
        """准备模板数据"""

    def _validate_output_path(self, path: str) -> str:
        """验证输出路径安全性"""
```

### 3. 安全特性

#### XSS防护
- Jinja2自动HTML转义
- 所有用户输入数据自动转义
- 防止脚本注入攻击

```python
# Jinja2自动转义配置
env = Environment(
    loader=FileSystemLoader(template_dir),
    autoescape=select_autoescape(['html', 'xml'])  # 启用自动转义
)
```

#### 路径遍历防护
- 输出路径验证
- 仅允许在安全目录下保存
- 防止写入系统敏感位置

```python
# 安全目录限制
safe_dirs = [
    Path.cwd(),           # 当前工作目录
    Path.home(),          # 用户主目录
    Path('/tmp'),         # 临时目录
    Path('/var/folders')  # macOS临时目录
]
```

### 4. 响应式设计

#### 移动端优化
```css
@media (max-width: 768px) {
    .header h1 { font-size: 1.8em; }
    .summary-grid { grid-template-columns: 1fr; }
    .chart-container { padding: 10px; }
}
```

#### 打印优化
```css
@media print {
    body { background: white; }
    .container { box-shadow: none; }
}
```

## 配置说明

### 1. 依赖项

HTML报告功能需要以下Python包：

```txt
jinja2>=3.1.0      # 模板引擎
```

已包含在 `requirements.txt` 中。

### 2. 外部资源

HTML报告使用CDN加载Chart.js：

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
```

如需离线使用，可下载Chart.js并修改模板引用本地文件。

## 测试

### 1. 单元测试

```bash
# 运行HTML Reporter测试
python -m pytest tests/reporting/test_html_reporter.py -v

# 运行集成测试
python -m pytest tests/reporting/test_analyze_stock_html_integration.py -v
```

### 2. 测试覆盖

测试套件包含37个测试用例，覆盖：

- HTML结构验证
- 数据准确性测试
- 响应式设计测试
- XSS防护测试
- 路径安全性测试
- 编码测试
- 边界情况测试

### 3. 手动测试

```bash
# 生成演示报告
python -c "
from src.reporting.html_reporter import HTMLReporter

sample_result = {
    'rating': 'buy',
    'confidence': 8.5,
    'target_price': 120.50,
    'stop_loss': 95.00,
    'reasons': ['测试原因1', '测试原因2'],
    'risks': ['测试风险1'],
    'a_share_risks': ['T+1制度'],
    'ai_insights': '测试分析',
    'scores': {
        'technical': 85.0,
        'fundamental': 78.0,
        'capital': 82.0,
        'overall': 82.0
    }
}

reporter = HTMLReporter()
reporter.generate_report(
    stock_code='600519',
    stock_name='贵州茅台',
    analysis_result=sample_result,
    save_to_file=True,
    output_path='demo_report.html'
)
"
```

## 最佳实践

### 1. 报告命名

```python
# 推荐：包含股票代码和日期
output_path = f"{stock_code}_{datetime.now().strftime('%Y%m%d')}_analysis.html"

# 示例：600519_20260129_analysis.html
```

### 2. 批量生成

```python
stock_codes = ['600519', '000001', '600036']

for code in stock_codes:
    result = analyze_stock(code)
    stock_name = get_stock_name(code)
    output_path = f"reports/{code}_report.html"
    save_html_report(code, stock_name, result, output_path)
```

### 3. 定时任务

```python
import schedule

def daily_report():
    """每日生成报告"""
    watch_list = ['600519', '000001']
    for code in watch_list:
        try:
            result = analyze_stock(code)
            stock_name = get_stock_name(code)
            date_str = datetime.now().strftime('%Y%m%d')
            output_path = f"daily_reports/{code}_{date_str}.html"
            save_html_report(code, stock_name, result, output_path)
        except Exception as e:
            print(f"Error analyzing {code}: {e}")

# 每天9:00生成报告
schedule.every().day.at("09:00").do(daily_report)
```

## 故障排除

### 1. 常见问题

#### 问题：ModuleNotFoundError: No module named 'jinja2'
**解决**：安装Jinja2
```bash
pip install jinja2
```

#### 问题：ValueError: 不安全的输出路径
**解决**：确保输出路径在允许的安全目录下
```python
# 使用相对路径或当前目录
output_path = './reports/report.html'

# 或使用用户主目录
output_path = os.path.expanduser('~/reports/report.html')
```

#### 问题：Chart.js无法加载（离线环境）
**解决**：下载Chart.js并修改模板
```bash
# 1. 下载Chart.js
curl -o static/chart.min.js https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js

# 2. 修改模板中的script标签
<script src="static/chart.min.js"></script>
```

### 2. 调试技巧

#### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)

reporter = HTMLReporter()
# 将输出详细日志
```

#### 验证HTML有效性
```bash
# 使用HTML validator
pip install html5validator
html5validator report.html
```

## 扩展开发

### 1. 自定义模板

复制并修改默认模板：

```bash
cp src/reporting/templates/stock_analysis.html \
   src/reporting/templates/custom_template.html
```

修改HTMLReporter使用自定义模板：

```python
template = self.env.get_template('custom_template.html')
```

### 2. 添加新图表

在模板中添加新的Canvas元素：

```html
<canvas id="newChart"></canvas>

<script>
// 添加新图表配置
const newChart = new Chart(ctx, {
    type: 'line',  // 或 'bar', 'pie' 等
    data: { ... },
    options: { ... }
});
</script>
```

### 3. 自定义样式

修改模板中的CSS：

```css
/* 自定义配色方案 */
.rating-buy {
    background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
}
```

## 性能优化

### 1. 批量生成优化

```python
# 复用HTMLReporter实例
reporter = HTMLReporter()

for code in stock_list:
    html = reporter.generate_report(...)  # 避免重复初始化
```

### 2. 模板缓存

Jinja2自动启用模板缓存，无需额外配置。

### 3. 异步生成

```python
import asyncio

async def generate_report_async(code, result):
    """异步生成报告"""
    reporter = HTMLReporter()
    return reporter.generate_report(...)

# 批量异步生成
tasks = [generate_report_async(code, result) for code, result in items]
reports = await asyncio.gather(*tasks)
```

## 更新日志

### v1.0.0 (2026-01-29)
- 初始版本发布
- 支持完整分析和快速分析模式
- 响应式设计支持移动端
- Chart.js雷达图可视化
- XSS防护和路径安全验证
- 37个单元测试和集成测试

## 许可证

本功能遵循项目主许可证。

## 支持

如有问题或建议，请提交Issue或联系开发团队。
