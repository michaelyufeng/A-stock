# 邮件通知功能使用指南

## 目录
- [功能概述](#功能概述)
- [配置说明](#配置说明)
- [快速开始](#快速开始)
- [高级配置](#高级配置)
- [常见问题](#常见问题)
- [邮箱服务商配置](#邮箱服务商配置)

## 功能概述

邮件通知功能允许 AlertManager 在检测到交易信号时自动发送邮件提醒。主要特性包括：

- ✅ **多收件人支持** - 可同时向多个邮箱发送提醒
- ✅ **HTML美观模板** - 使用精心设计的HTML邮件模板
- ✅ **自动重试机制** - 发送失败时自动重试最多3次
- ✅ **频率限制** - 防止同一股票在短时间内重复发送邮件
- ✅ **安全配置** - 密码从环境变量读取，不存储在代码中
- ✅ **TLS/SSL加密** - 支持安全的SMTP连接
- ✅ **多种信号类型** - 支持BUY、SELL、WARNING、INFO等信号

## 配置说明

### 1. 环境变量配置

首先，创建 `.env` 文件（从 `.env.example` 复制）：

```bash
cp .env.example .env
```

然后编辑 `.env` 文件，添加邮箱配置：

```bash
# Gmail 示例
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_specific_password

# QQ邮箱示例
# EMAIL_SENDER=your_email@qq.com
# EMAIL_PASSWORD=your_authorization_code

# 163邮箱示例
# EMAIL_SENDER=your_email@163.com
# EMAIL_PASSWORD=your_authorization_code
```

**重要提示：**
- Gmail 需要使用"应用专用密码"而不是账号密码
- QQ邮箱和163邮箱需要使用"授权码"而不是邮箱密码
- 详细获取方式请参考 [邮箱服务商配置](#邮箱服务商配置)

### 2. 监控配置文件

编辑 `config/monitoring.yaml`，启用邮件通知：

```yaml
alerts:
  channels:
    - console
    - log
    - email  # 启用邮件通知

  email:
    smtp_server: smtp.gmail.com
    smtp_port: 587
    use_tls: true
    sender: ${EMAIL_SENDER}
    sender_password: ${EMAIL_PASSWORD}
    recipients:
      - recipient1@example.com
      - recipient2@example.com
    subject_template: "[A股监控] {signal_type} - {stock_name}"
    max_retries: 3
    retry_delay: 1
    rate_limit_seconds: 300
```

## 快速开始

### 基本使用示例

```python
from src.monitoring.alert_manager import AlertManager, AlertRule, AlertChannel
from src.monitoring.signal_detector import Signal
from datetime import datetime

# 1. 创建AlertManager实例
alert_manager = AlertManager(config_path='config/monitoring.yaml')

# 2. 创建提醒规则
rule = AlertRule(
    rule_id='email_rule_001',
    name='重要信号邮件提醒',
    stock_codes=['600519', '000858'],  # 监控的股票
    signal_types=['BUY', 'SELL'],      # 关注买卖信号
    categories=['technical'],          # 技术信号
    min_priority='medium',             # 中等及以上优先级
    channels=[AlertChannel.EMAIL],     # 使用邮件通知
    enabled=True,
    cooldown_minutes=60                # 1小时冷却期
)

# 3. 添加规则
alert_manager.add_rule(rule)

# 4. 创建交易信号（通常由SignalDetector自动生成）
signal = Signal(
    stock_code='600519',
    stock_name='贵州茅台',
    signal_type='BUY',
    category='technical',
    description='MA5金叉MA20，形成买入信号',
    priority='high',
    trigger_price=1680.50,
    timestamp=datetime.now(),
    metadata={'ma_short': 5, 'ma_long': 20}
)

# 5. 处理信号（自动发送邮件）
result = alert_manager.process_signal(signal)

if result['triggered']:
    print(f"✅ 邮件提醒已发送")
else:
    print(f"ℹ️  信号未触发提醒规则")
```

### 集成到监控服务

在监控服务中使用邮件通知：

```python
from src.monitoring.monitoring_service import MonitoringService

# 启动监控服务（自动使用config/monitoring.yaml配置）
service = MonitoringService()
service.start()

# 服务会自动：
# 1. 检测交易信号
# 2. 匹配提醒规则
# 3. 发送邮件通知
```

## 高级配置

### 自定义邮件主题

在 `config/monitoring.yaml` 中修改主题模板：

```yaml
email:
  subject_template: "【A股提醒】{signal_type} {stock_name}({stock_code}) - {priority}"
```

可用变量：
- `{signal_type}` - 信号类型（BUY/SELL/WARNING/INFO）
- `{stock_code}` - 股票代码
- `{stock_name}` - 股票名称
- `{priority}` - 优先级（low/medium/high/critical）

### 调整重试策略

```yaml
email:
  max_retries: 5        # 最多重试5次
  retry_delay: 2        # 重试间隔2秒
```

### 调整发送频率限制

```yaml
email:
  rate_limit_seconds: 600  # 同一股票10分钟内只发送一次
```

### 多收件人配置

```yaml
email:
  recipients:
    - trader1@company.com
    - trader2@company.com
    - manager@company.com
```

### 不同邮箱服务商配置

#### Gmail
```yaml
email:
  smtp_server: smtp.gmail.com
  smtp_port: 587
  use_tls: true
```

#### QQ邮箱
```yaml
email:
  smtp_server: smtp.qq.com
  smtp_port: 587
  use_tls: true
```

#### 163邮箱
```yaml
email:
  smtp_server: smtp.163.com
  smtp_port: 465  # 或 25
  use_tls: false  # 使用SSL
```

#### Outlook
```yaml
email:
  smtp_server: smtp.office365.com
  smtp_port: 587
  use_tls: true
```

## 常见问题

### Q1: 邮件发送失败，提示认证错误

**A:** 检查以下几点：
1. 是否使用了正确的密码类型（应用专用密码/授权码）
2. `.env` 文件中的配置是否正确
3. 邮箱是否开启了SMTP服务
4. 防火墙是否阻止了SMTP端口

### Q2: Gmail提示"不够安全的应用"

**A:** Gmail需要使用应用专用密码：
1. 启用两步验证
2. 生成应用专用密码
3. 使用应用专用密码替代账号密码

### Q3: 如何测试邮件功能是否正常

**A:** 运行测试脚本：

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行邮件测试
python -m pytest tests/monitoring/test_alert_manager.py -k "email" -v
```

### Q4: 邮件发送太频繁怎么办

**A:** 调整配置：
1. 增加 `rate_limit_seconds` 值
2. 增加规则的 `cooldown_minutes` 值
3. 提高 `min_priority` 阈值，只发送重要信号

### Q5: 能否自定义邮件模板

**A:** 可以！编辑 `src/monitoring/templates/email_alert.html` 文件。
模板使用Jinja2语法，可以自定义样式和内容。

### Q6: 如何停止接收邮件

**A:** 有三种方式：
1. 在 `config/monitoring.yaml` 中移除 `email` 通道
2. 禁用相关的提醒规则
3. 停止监控服务

## 邮箱服务商配置

### Gmail 配置步骤

1. **启用两步验证**
   - 访问 Google 账号设置 → 安全性
   - 启用"两步验证"

2. **生成应用专用密码**
   - 在两步验证设置中找到"应用专用密码"
   - 选择"邮件"和"其他（自定义名称）"
   - 生成密码并复制

3. **配置 .env**
   ```bash
   EMAIL_SENDER=your_email@gmail.com
   EMAIL_PASSWORD=生成的应用专用密码
   ```

### QQ邮箱配置步骤

1. **开启SMTP服务**
   - 登录QQ邮箱
   - 设置 → 账户 → POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务
   - 开启"POP3/SMTP服务"或"IMAP/SMTP服务"

2. **生成授权码**
   - 点击"生成授权码"
   - 按提示发送短信验证
   - 保存生成的授权码（16位）

3. **配置 .env**
   ```bash
   EMAIL_SENDER=your_email@qq.com
   EMAIL_PASSWORD=生成的授权码
   ```

### 163邮箱配置步骤

1. **开启SMTP服务**
   - 登录163邮箱
   - 设置 → POP3/SMTP/IMAP
   - 开启"SMTP服务"

2. **获取授权密码**
   - 点击"客户端授权密码"
   - 设置授权密码

3. **配置 .env**
   ```bash
   EMAIL_SENDER=your_email@163.com
   EMAIL_PASSWORD=授权密码
   ```

### Outlook 配置步骤

1. **直接使用账号密码**
   - Outlook可以直接使用邮箱密码
   - 如果启用了两步验证，需要使用应用密码

2. **配置 .env**
   ```bash
   EMAIL_SENDER=your_email@outlook.com
   EMAIL_PASSWORD=账号密码或应用密码
   ```

## 安全最佳实践

1. **永远不要将密码提交到版本控制**
   - `.env` 文件已在 `.gitignore` 中
   - 只提交 `.env.example` 作为模板

2. **使用专用密码**
   - 优先使用应用专用密码或授权码
   - 避免使用主账号密码

3. **定期更换密码**
   - 定期更新邮箱密码和授权码
   - 发现异常立即更换

4. **限制收件人**
   - 只添加需要接收提醒的邮箱
   - 避免发送到公开邮箱

5. **启用加密连接**
   - 始终使用 TLS/SSL
   - 不要使用不加密的SMTP

## 性能优化建议

1. **合理设置频率限制**
   ```yaml
   rate_limit_seconds: 300  # 5分钟
   cooldown_minutes: 60     # 1小时
   ```

2. **使用优先级过滤**
   ```yaml
   min_priority: "medium"  # 只发送中等及以上优先级
   ```

3. **避免过多收件人**
   - 建议不超过5个收件人
   - 考虑使用邮件列表

4. **监控发送状态**
   - 检查日志文件中的邮件发送记录
   - 关注失败率和重试次数

## 故障排查

### 检查配置是否正确

```python
from src.monitoring.alert_manager import AlertManager

manager = AlertManager('config/monitoring.yaml')
print("Email config:", manager.email_config)
```

### 查看日志

```bash
# 查看邮件发送日志
tail -f logs/monitoring.log | grep -i email
```

### 测试SMTP连接

```python
import smtplib

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your_email@gmail.com', 'your_password')
print("✅ SMTP连接成功")
server.quit()
```

## 完整示例

查看 `examples/email_notification_demo.py` 了解完整的使用示例。

## 相关文档

- [配置指南](CONFIGURATION_GUIDE.md)
- [监控服务使用说明](MONITORING_SERVICE.md)
- [API参考文档](API_REFERENCE.md)

## 技术支持

如有问题，请：
1. 查看本文档的[常见问题](#常见问题)部分
2. 检查日志文件 `logs/monitoring.log`
3. 运行单元测试验证功能
4. 提交Issue到GitHub仓库
