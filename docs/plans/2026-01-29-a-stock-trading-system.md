# A股量化交易分析系统 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a modular A-share quantitative trading analysis system with technical/fundamental/capital analysis, AI rating, backtesting, screening, and real-time monitoring capabilities.

**Architecture:** Layered architecture with data provider layer (AKShare), analysis layer (technical/fundamental/capital/AI), strategy layer (short-term/long-term), backtest engine (backtrader), and monitoring/reporting layers. Configuration-driven with YAML configs, SQLite caching, and modular design for extensibility.

**Tech Stack:** Python 3.8+, AKShare (data), DeepSeek API (AI), backtrader (backtest), pandas_ta (indicators), SQLite (storage), YAML (config)

---

## Phase 1: Foundation - Core Infrastructure

### Task 1.1: Project Structure Setup

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `README.md`
- Create: `config/config.yaml`
- Create: `config/strategies.yaml`
- Create: `config/risk_rules.yaml`

**Step 1: Create requirements.txt**

Run:
```bash
cat > requirements.txt << 'EOF'
# Core dependencies
akshare>=1.12.0
pandas>=2.0.0
numpy>=1.24.0

# AI analysis
openai>=1.0.0
tiktoken>=0.5.0

# Technical indicators
pandas_ta>=0.3.14

# Backtest framework
backtrader>=1.9.78
matplotlib>=3.7.0
mplfinance>=0.12.0

# Data storage
sqlalchemy>=2.0.0

# Configuration and logging
pyyaml>=6.0
python-dotenv>=1.0.0
loguru>=0.7.0

# Utilities
tqdm>=4.65.0
click>=8.1.0
colorama>=0.4.6
tabulate>=0.9.0

# Templates and reporting
jinja2>=3.1.0
markdown>=3.4.0

# Performance optimization
joblib>=1.3.0
diskcache>=5.6.0
EOF
```

**Step 2: Create .env.example**

Run:
```bash
cat > .env.example << 'EOF'
# DeepSeek API Key
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# Debug mode
DEBUG=false

# Data cache settings
CACHE_ENABLED=true
CACHE_DIR=./data/cache

# Database
DB_PATH=./data/storage/a_stock.db
EOF
```

**Step 3: Create .gitignore**

Run:
```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment variables
.env

# Data files
data/cache/
data/storage/*.db
data/exports/
*.csv
*.xlsx

# Logs
logs/
*.log

# System
.DS_Store
Thumbs.db

# Jupyter
.ipynb_checkpoints/
*.ipynb

# Testing
.pytest_cache/
.coverage
htmlcov/

# Backtest results
backtest_results/
EOF
```

**Step 4: Create README.md**

Run:
```bash
cat > README.md << 'EOF'
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
EOF
```

**Step 5: Create config/config.yaml**

Run:
```bash
mkdir -p config
cat > config/config.yaml << 'EOF'
# A股量化交易系统配置文件

data:
  provider: akshare
  cache:
    enabled: true
    directory: ./data/cache
    ttl:
      realtime: 60        # 实时行情缓存60秒
      daily: 3600         # 日线数据缓存1小时
      financial: 86400    # 财务数据缓存1天

  # 数据源配置
  sources:
    stock_list: "stock_zh_a_spot"
    realtime_quote: "stock_zh_a_spot_em"
    daily_kline: "stock_zh_a_hist"
    financial: "stock_financial_analysis_indicator"
    money_flow: "stock_individual_fund_flow"

ai:
  provider: deepseek
  model: deepseek-chat
  reasoning_model: deepseek-reasoner
  temperature: 0.7
  max_tokens: 4000
  timeout: 30

  # AI评级权重
  rating_weights:
    technical: 0.30
    fundamental: 0.30
    capital: 0.25
    sentiment: 0.15

logging:
  level: INFO
  format: "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
  files:
    app: ./logs/app.log
    error: ./logs/error.log
    trade: ./logs/trade.log
  rotation: "100 MB"
  retention: "30 days"

market:
  # A股涨跌停限制
  limit_ratio:
    main_board: 0.10      # 主板10%
    star_market: 0.20     # 科创板20%
    gem: 0.20             # 创业板20%

  # 交易时间
  trading_hours:
    morning_start: "09:30"
    morning_end: "11:30"
    afternoon_start: "13:00"
    afternoon_end: "15:00"

  # 最小交易单位
  min_lot: 100            # 1手=100股

database:
  path: ./data/storage/a_stock.db
  echo: false
  pool_size: 5
  max_overflow: 10
EOF
```

**Step 6: Create config/strategies.yaml**

Run:
```bash
cat > config/strategies.yaml << 'EOF'
# 策略配置文件

# 短线动量策略
momentum:
  type: short_term
  description: "基于价格动量和成交量的短线策略"

  parameters:
    # 技术指标参数
    rsi_period: 14
    rsi_oversold: 30
    rsi_overbought: 70

    macd_fast: 12
    macd_slow: 26
    macd_signal: 9

    volume_ma_period: 5
    volume_surge_ratio: 2.0    # 成交量放大倍数

    # 交易参数
    stop_loss: 0.08            # 止损8%
    take_profit: 0.15          # 止盈15%
    max_holding_days: 10       # 最大持仓天数

  entry_conditions:
    - "RSI从超卖区回升"
    - "MACD金叉"
    - "成交量放大"
    - "价格突破短期阻力"

  exit_conditions:
    - "RSI进入超买区"
    - "MACD死叉"
    - "触及止盈止损"
    - "持仓超过最大天数"

# 价值投资策略
value_investing:
  type: long_term
  description: "基于基本面的价值投资策略"

  parameters:
    # 基本面筛选条件
    min_roe: 0.15              # 最低ROE 15%
    max_pe: 30                 # 最高PE 30
    max_pb: 3                  # 最高PB 3
    min_gross_margin: 0.30     # 最低毛利率30%

    # 财务健康度
    max_debt_ratio: 0.60       # 最高负债率60%
    min_current_ratio: 1.5     # 最低流动比率1.5

    # 成长性
    min_revenue_growth: 0.10   # 最低营收增长10%
    min_profit_growth: 0.10    # 最低利润增长10%

    # 持仓参数
    stop_loss: 0.15            # 止损15%
    take_profit: 0.50          # 止盈50%
    max_holding_days: 365      # 最大持仓天数

  entry_conditions:
    - "ROE稳定在15%以上"
    - "PE低于行业平均"
    - "连续盈利且增长"
    - "资产负债率健康"

  exit_conditions:
    - "基本面恶化"
    - "估值过高"
    - "触及止盈止损"

# 突破策略
breakout:
  type: short_term
  description: "价格突破策略"

  parameters:
    # 突破参数
    breakout_period: 20        # 突破周期
    breakout_threshold: 0.03   # 突破幅度3%
    volume_confirm: true       # 成交量确认

    # 交易参数
    stop_loss: 0.05            # 止损5%
    take_profit: 0.20          # 止盈20%
    trailing_stop: 0.03        # 移动止损3%

  entry_conditions:
    - "突破N日高点"
    - "成交量放大确认"
    - "无明显阻力位"

  exit_conditions:
    - "跌破关键支撑"
    - "触及止盈止损"
    - "成交量萎缩"
EOF
```

**Step 7: Create config/risk_rules.yaml**

Run:
```bash
cat > config/risk_rules.yaml << 'EOF'
# 风险管理配置

# 仓位管理
position:
  max_single_position: 0.20      # 单一持仓最大20%
  max_sector_exposure: 0.30      # 单一行业最大30%
  max_total_position: 0.95       # 总仓位最大95%
  min_position_value: 10000      # 最小建仓金额1万元

# 交易限制
trade_restrictions:
  禁止ST股: true
  禁止退市风险股: true
  min_listing_days: 30           # 最少上市30天
  min_market_cap: 2000000000     # 最小市值20亿
  min_daily_volume: 10000000     # 最小日成交额1000万

  # A股特色限制
  avoid_continuous_limit_up: true      # 避免连续涨停
  avoid_continuous_limit_down: true    # 避免连续跌停
  max_continuous_limit: 3              # 最多连续涨跌停天数

# 止损止盈
stop_loss:
  enabled: true
  method: "fixed"                # fixed/trailing/atr
  fixed_ratio: 0.08              # 固定止损8%
  trailing_ratio: 0.05           # 移动止损5%
  atr_multiplier: 2.0            # ATR止损倍数

take_profit:
  enabled: true
  method: "fixed"                # fixed/dynamic
  fixed_ratio: 0.15              # 固定止盈15%
  partial_take_profit:
    enabled: true
    first_target: 0.10           # 第一目标10%
    first_size: 0.50             # 减仓50%

# A股特色风控
a_share_specific:
  t1_settlement: true            # T+1交易制度
  check_limit_price: true        # 检查涨跌停

  # 涨跌停处理
  limit_up_action: "hold"        # 涨停处理：hold/sell
  limit_down_action: "hold"      # 跌停处理：hold/emergency_sell

  # 特殊时段
  avoid_before_holiday: false    # 避免节前买入
  avoid_year_end: false          # 避免年末买入

# 风险预警
alerts:
  position_concentration:
    warning: 0.15                # 单一持仓15%预警
    critical: 0.20               # 单一持仓20%严重

  drawdown:
    warning: 0.05                # 5%回撤预警
    critical: 0.10               # 10%回撤严重

  volatility:
    warning: 0.30                # 30%波动率预警
    critical: 0.50               # 50%波动率严重

# 交易限制
trading_limits:
  max_trades_per_day: 5          # 每日最多交易5次
  max_trades_per_week: 15        # 每周最多交易15次
  min_holding_period: 1          # 最短持仓1天（T+1）
  cooling_period: 5              # 同一股票冷却期5天
EOF
```

**Step 8: Verify files created**

Run:
```bash
ls -la
ls -la config/
```

Expected: All configuration files created successfully

**Step 9: Commit**

Run:
```bash
git init
git add .
git commit -m "chore: initial project setup with configs and requirements"
```

---

### Task 1.2: Core Module - Configuration Manager

**Files:**
- Create: `src/__init__.py`
- Create: `src/core/__init__.py`
- Create: `src/core/config_manager.py`
- Create: `tests/__init__.py`
- Create: `tests/core/__init__.py`
- Create: `tests/core/test_config_manager.py`

**Step 1: Write the failing test**

Run:
```bash
mkdir -p src/core tests/core
touch src/__init__.py src/core/__init__.py tests/__init__.py tests/core/__init__.py

cat > tests/core/test_config_manager.py << 'EOF'
import pytest
from pathlib import Path
from src.core.config_manager import ConfigManager


class TestConfigManager:
    def test_singleton_pattern(self):
        """测试单例模式"""
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2

    def test_load_config(self):
        """测试加载配置文件"""
        config = ConfigManager()
        assert config.config is not None
        assert 'data' in config.config
        assert 'ai' in config.config

    def test_get_value(self):
        """测试获取配置值"""
        config = ConfigManager()
        provider = config.get('data.provider')
        assert provider == 'akshare'

    def test_get_nested_value(self):
        """测试获取嵌套配置值"""
        config = ConfigManager()
        cache_ttl = config.get('data.cache.ttl.realtime')
        assert cache_ttl == 60

    def test_get_default_value(self):
        """测试获取默认值"""
        config = ConfigManager()
        value = config.get('non.existent.key', default='default_value')
        assert value == 'default_value'

    def test_get_section(self):
        """测试获取整个配置节"""
        config = ConfigManager()
        ai_config = config.get('ai')
        assert isinstance(ai_config, dict)
        assert ai_config['provider'] == 'deepseek'
EOF
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/core/test_config_manager.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.config_manager'"

**Step 3: Write minimal implementation**

Run:
```bash
cat > src/core/config_manager.py << 'EOF'
"""配置管理器模块"""
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器（单例模式）"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """加载所有配置文件"""
        config_dir = Path(__file__).parent.parent.parent / 'config'

        # 加载主配置
        config_file = config_dir / 'config.yaml'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}

        # 加载策略配置
        strategies_file = config_dir / 'strategies.yaml'
        if strategies_file.exists():
            with open(strategies_file, 'r', encoding='utf-8') as f:
                self._config['strategies'] = yaml.safe_load(f) or {}

        # 加载风控规则
        risk_rules_file = config_dir / 'risk_rules.yaml'
        if risk_rules_file.exists():
            with open(risk_rules_file, 'r', encoding='utf-8') as f:
                self._config['risk_rules'] = yaml.safe_load(f) or {}

    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的嵌套键）

        Args:
            key: 配置键，支持 'data.provider' 格式
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()
EOF
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/core/test_config_manager.py -v
```

Expected: PASS all tests

**Step 5: Commit**

Run:
```bash
git add src/core/config_manager.py tests/core/test_config_manager.py
git commit -m "feat: add config manager with singleton pattern"
```

---

### Task 1.3: Core Module - Logger

**Files:**
- Create: `src/core/logger.py`
- Create: `tests/core/test_logger.py`

**Step 1: Write the failing test**

Run:
```bash
cat > tests/core/test_logger.py << 'EOF'
import pytest
from pathlib import Path
from src.core.logger import get_logger, setup_logger


class TestLogger:
    def test_get_logger(self):
        """测试获取logger实例"""
        logger = get_logger(__name__)
        assert logger is not None

    def test_logger_name(self):
        """测试logger名称"""
        logger = get_logger("test_module")
        # loguru logger不直接暴露name属性，但可以验证它能工作
        logger.info("Test message")

    def test_multiple_loggers_same_name(self):
        """测试同名logger是否相同"""
        logger1 = get_logger("same_name")
        logger2 = get_logger("same_name")
        # loguru返回同一个logger实例
        assert logger1 is logger2

    def test_log_levels(self):
        """测试不同日志级别"""
        logger = get_logger("test_levels")
        # 验证不会抛出异常
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_setup_logger_creates_log_dir(self, tmp_path):
        """测试setup_logger创建日志目录"""
        log_dir = tmp_path / "logs"
        setup_logger(log_dir=str(log_dir))
        assert log_dir.exists()
EOF
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/core/test_logger.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.logger'"

**Step 3: Write minimal implementation**

Run:
```bash
cat > src/core/logger.py << 'EOF'
"""日志模块"""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from src.core.config_manager import ConfigManager


_logger_initialized = False


def setup_logger(log_dir: Optional[str] = None) -> None:
    """
    设置全局logger

    Args:
        log_dir: 日志目录路径
    """
    global _logger_initialized

    if _logger_initialized:
        return

    # 移除默认handler
    logger.remove()

    # 加载配置
    config = ConfigManager()
    log_config = config.get('logging', {})
    level = log_config.get('level', 'INFO')
    log_format = log_config.get('format',
                                 "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                                 "<level>{level: <8}</level> | "
                                 "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                                 "<level>{message}</level>")

    # 控制台输出
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        colorize=True
    )

    # 文件输出
    if log_dir is None:
        log_files = log_config.get('files', {})
        app_log = log_files.get('app', './logs/app.log')
        error_log = log_files.get('error', './logs/error.log')
    else:
        log_dir_path = Path(log_dir)
        app_log = log_dir_path / 'app.log'
        error_log = log_dir_path / 'error.log'

    # 确保日志目录存在
    Path(app_log).parent.mkdir(parents=True, exist_ok=True)
    Path(error_log).parent.mkdir(parents=True, exist_ok=True)

    # 应用日志
    logger.add(
        app_log,
        format=log_format,
        level='DEBUG',
        rotation=log_config.get('rotation', '100 MB'),
        retention=log_config.get('retention', '30 days'),
        compression='zip',
        encoding='utf-8'
    )

    # 错误日志
    logger.add(
        error_log,
        format=log_format,
        level='ERROR',
        rotation=log_config.get('rotation', '100 MB'),
        retention=log_config.get('retention', '30 days'),
        compression='zip',
        encoding='utf-8'
    )

    _logger_initialized = True


def get_logger(name: str):
    """
    获取logger实例

    Args:
        name: logger名称

    Returns:
        logger实例
    """
    if not _logger_initialized:
        setup_logger()

    return logger.bind(name=name)


# 模块级别logger
log = get_logger(__name__)
EOF
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/core/test_logger.py -v
```

Expected: PASS all tests

**Step 5: Commit**

Run:
```bash
git add src/core/logger.py tests/core/test_logger.py
git commit -m "feat: add logger with loguru integration"
```

---

### Task 1.4: Core Module - Constants

**Files:**
- Create: `src/core/constants.py`
- Create: `tests/core/test_constants.py`

**Step 1: Write the failing test**

Run:
```bash
cat > tests/core/test_constants.py << 'EOF'
import pytest
from src.core.constants import (
    Market, StockStatus, OrderSide, OrderType,
    MAIN_BOARD_LIMIT, STAR_MARKET_LIMIT, GEM_LIMIT,
    TRADING_HOURS, MIN_LOT
)


class TestConstants:
    def test_market_enum(self):
        """测试市场枚举"""
        assert Market.MAIN_BOARD.value == 'main_board'
        assert Market.STAR_MARKET.value == 'star_market'
        assert Market.GEM.value == 'gem'

    def test_stock_status_enum(self):
        """测试股票状态枚举"""
        assert StockStatus.NORMAL.value == 'normal'
        assert StockStatus.ST.value == 'st'
        assert StockStatus.DELISTING.value == 'delisting'

    def test_limit_ratios(self):
        """测试涨跌停限制"""
        assert MAIN_BOARD_LIMIT == 0.10
        assert STAR_MARKET_LIMIT == 0.20
        assert GEM_LIMIT == 0.20

    def test_trading_hours(self):
        """测试交易时间"""
        assert 'morning_start' in TRADING_HOURS
        assert TRADING_HOURS['morning_start'] == '09:30'
        assert TRADING_HOURS['afternoon_end'] == '15:00'

    def test_min_lot(self):
        """测试最小交易单位"""
        assert MIN_LOT == 100
EOF
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/core/test_constants.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.core.constants'"

**Step 3: Write minimal implementation**

Run:
```bash
cat > src/core/constants.py << 'EOF'
"""系统常量定义"""
from enum import Enum


# ==================== 枚举类型 ====================

class Market(Enum):
    """市场类型"""
    MAIN_BOARD = 'main_board'      # 主板
    STAR_MARKET = 'star_market'    # 科创板
    GEM = 'gem'                    # 创业板


class StockStatus(Enum):
    """股票状态"""
    NORMAL = 'normal'              # 正常
    ST = 'st'                      # ST股
    STAR_ST = 'star_st'            # *ST股
    DELISTING = 'delisting'        # 退市整理
    SUSPENDED = 'suspended'        # 停牌


class OrderSide(Enum):
    """交易方向"""
    BUY = 'buy'                    # 买入
    SELL = 'sell'                  # 卖出


class OrderType(Enum):
    """订单类型"""
    MARKET = 'market'              # 市价单
    LIMIT = 'limit'                # 限价单


class SignalType(Enum):
    """信号类型"""
    BUY = 'buy'                    # 买入信号
    SELL = 'sell'                  # 卖出信号
    HOLD = 'hold'                  # 持有信号


# ==================== A股市场常量 ====================

# 涨跌停限制
MAIN_BOARD_LIMIT = 0.10            # 主板涨跌停限制 10%
STAR_MARKET_LIMIT = 0.20           # 科创板涨跌停限制 20%
GEM_LIMIT = 0.20                   # 创业板涨跌停限制 20%

# 交易时间
TRADING_HOURS = {
    'morning_start': '09:30',
    'morning_end': '11:30',
    'afternoon_start': '13:00',
    'afternoon_end': '15:00',
    'call_auction_start': '09:15',  # 集合竞价开始
    'call_auction_end': '09:25',    # 集合竞价结束
}

# 交易单位
MIN_LOT = 100                      # 最小交易单位（1手 = 100股）

# 交易费用
COMMISSION_RATE = 0.0003           # 佣金费率 0.03%
MIN_COMMISSION = 5.0               # 最低佣金 5元
STAMP_TAX_RATE = 0.001             # 印花税 0.1% (仅卖出)
TRANSFER_FEE_RATE = 0.00002        # 过户费 0.002%

# 市场板块代码前缀
MARKET_PREFIX = {
    'SH_MAIN': ['600', '601', '603', '605'],      # 上海主板
    'SZ_MAIN': ['000', '001'],                     # 深圳主板
    'GEM': ['300'],                                # 创业板
    'STAR': ['688'],                               # 科创板
    'BJ': ['82', '83', '87'],                      # 北交所
}

# 特殊股票标识
ST_PATTERNS = ['ST', '*ST', 'S*ST', 'SST']

# ==================== 技术指标常量 ====================

# 默认指标参数
DEFAULT_INDICATORS = {
    'MA': [5, 10, 20, 60],                # 移动平均线周期
    'EMA': [12, 26],                       # 指数移动平均线周期
    'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
    'KDJ': {'n': 9, 'k': 3, 'd': 3},
    'RSI': [6, 14, 24],                    # RSI周期
    'BOLL': {'n': 20, 'std': 2},          # 布林带参数
    'ATR': 14,                             # ATR周期
    'VOL_MA': [5, 10],                     # 成交量均线周期
}

# ==================== 回测常量 ====================

# 初始资金
DEFAULT_CAPITAL = 1_000_000            # 默认初始资金100万

# 回测参数
BACKTEST_DEFAULTS = {
    'commission': COMMISSION_RATE,
    'stamp_tax': STAMP_TAX_RATE,
    'slippage': 0.001,                 # 滑点 0.1%
}

# ==================== 风控常量 ====================

# 仓位限制
MAX_SINGLE_POSITION = 0.20             # 单一持仓最大20%
MAX_SECTOR_EXPOSURE = 0.30             # 单一行业最大30%
MAX_TOTAL_POSITION = 0.95              # 总仓位最大95%

# 止损止盈
DEFAULT_STOP_LOSS = 0.08               # 默认止损8%
DEFAULT_TAKE_PROFIT = 0.15             # 默认止盈15%

# 筛选条件
MIN_MARKET_CAP = 20_0000_0000          # 最小市值20亿
MIN_DAILY_VOLUME = 1000_0000           # 最小日成交额1000万
MIN_LISTING_DAYS = 30                  # 最少上市30天

# ==================== 数据库常量 ====================

# 表名
TABLE_NAMES = {
    'STOCK_BASIC': 'stock_basic',
    'DAILY_KLINE': 'daily_kline',
    'FINANCIAL': 'financial_data',
    'MONEY_FLOW': 'money_flow',
    'SIGNALS': 'signals',
    'POSITIONS': 'positions',
    'ORDERS': 'orders',
}
EOF
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/core/test_constants.py -v
```

Expected: PASS all tests

**Step 5: Commit**

Run:
```bash
git add src/core/constants.py tests/core/test_constants.py
git commit -m "feat: add A-share market constants and enums"
```

---

## Phase 2: Data Layer - AKShare Integration

### Task 2.1: Market Calendar

**Files:**
- Create: `src/data/__init__.py`
- Create: `src/data/market_calendar.py`
- Create: `tests/data/__init__.py`
- Create: `tests/data/test_market_calendar.py`

**Step 1: Write the failing test**

Run:
```bash
mkdir -p src/data tests/data
touch src/data/__init__.py tests/data/__init__.py

cat > tests/data/test_market_calendar.py << 'EOF'
import pytest
from datetime import datetime, time
from src.data.market_calendar import MarketCalendar


class TestMarketCalendar:
    def test_is_trading_day_workday(self):
        """测试工作日判断"""
        calendar = MarketCalendar()
        # 2024年1月2日是交易日（周二）
        result = calendar.is_trading_day(datetime(2024, 1, 2))
        assert result is True

    def test_is_trading_day_weekend(self):
        """测试周末判断"""
        calendar = MarketCalendar()
        # 2024年1月6日是周六
        result = calendar.is_trading_day(datetime(2024, 1, 6))
        assert result is False

    def test_is_trading_time_during_market(self):
        """测试交易时段判断"""
        calendar = MarketCalendar()
        # 上午10点是交易时间
        result = calendar.is_trading_time(time(10, 0))
        assert result is True

    def test_is_trading_time_lunch(self):
        """测试午休时段判断"""
        calendar = MarketCalendar()
        # 中午12点是午休时间
        result = calendar.is_trading_time(time(12, 0))
        assert result is False

    def test_is_trading_time_after_close(self):
        """测试闭市后判断"""
        calendar = MarketCalendar()
        # 下午4点已闭市
        result = calendar.is_trading_time(time(16, 0))
        assert result is False

    def test_get_latest_trading_day(self):
        """测试获取最近交易日"""
        calendar = MarketCalendar()
        result = calendar.get_latest_trading_day()
        assert isinstance(result, datetime)

    def test_is_call_auction_time(self):
        """测试集合竞价时间判断"""
        calendar = MarketCalendar()
        # 9:20是集合竞价时间
        result = calendar.is_call_auction_time(time(9, 20))
        assert result is True
EOF
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/data/test_market_calendar.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.data.market_calendar'"

**Step 3: Write minimal implementation**

Run:
```bash
cat > src/data/market_calendar.py << 'EOF'
"""A股交易日历模块"""
import akshare as ak
from datetime import datetime, time, timedelta
from typing import List, Optional
from functools import lru_cache
from src.core.logger import get_logger
from src.core.constants import TRADING_HOURS

logger = get_logger(__name__)


class MarketCalendar:
    """A股交易日历"""

    def __init__(self):
        self._trading_days_cache: Optional[List[datetime]] = None
        self._cache_year: Optional[int] = None

    def _load_trading_days(self, year: int) -> List[datetime]:
        """
        加载指定年份的交易日

        Args:
            year: 年份

        Returns:
            交易日列表
        """
        try:
            # 使用akshare获取交易日历
            df = ak.tool_trade_date_hist_sina()
            # 筛选指定年份
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df_year = df[df['trade_date'].dt.year == year]
            return df_year['trade_date'].tolist()
        except Exception as e:
            logger.warning(f"Failed to load trading days from akshare: {e}")
            # 降级：使用简单规则（仅排除周末，不考虑节假日）
            return self._generate_simple_trading_days(year)

    def _generate_simple_trading_days(self, year: int) -> List[datetime]:
        """
        生成简单的交易日列表（仅排除周末）

        Args:
            year: 年份

        Returns:
            交易日列表
        """
        trading_days = []
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)

        current = start_date
        while current <= end_date:
            # 排除周末
            if current.weekday() < 5:  # 0-4是周一到周五
                trading_days.append(current)
            current += timedelta(days=1)

        return trading_days

    def _ensure_cache(self, date: datetime) -> None:
        """确保缓存已加载"""
        year = date.year
        if self._cache_year != year:
            self._trading_days_cache = self._load_trading_days(year)
            self._cache_year = year

    def is_trading_day(self, date: datetime) -> bool:
        """
        判断是否为交易日

        Args:
            date: 日期

        Returns:
            是否为交易日
        """
        # 周末肯定不是交易日
        if date.weekday() >= 5:
            return False

        # 检查缓存
        self._ensure_cache(date)

        # 检查是否在交易日列表中
        date_only = date.replace(hour=0, minute=0, second=0, microsecond=0)
        return any(td.date() == date_only.date() for td in self._trading_days_cache)

    def is_trading_time(self, check_time: time) -> bool:
        """
        判断是否为交易时间

        Args:
            check_time: 时间

        Returns:
            是否为交易时间
        """
        morning_start = time.fromisoformat(TRADING_HOURS['morning_start'])
        morning_end = time.fromisoformat(TRADING_HOURS['morning_end'])
        afternoon_start = time.fromisoformat(TRADING_HOURS['afternoon_start'])
        afternoon_end = time.fromisoformat(TRADING_HOURS['afternoon_end'])

        # 上午时段
        if morning_start <= check_time <= morning_end:
            return True

        # 下午时段
        if afternoon_start <= check_time <= afternoon_end:
            return True

        return False

    def is_call_auction_time(self, check_time: time) -> bool:
        """
        判断是否为集合竞价时间

        Args:
            check_time: 时间

        Returns:
            是否为集合竞价时间
        """
        auction_start = time.fromisoformat(TRADING_HOURS['call_auction_start'])
        auction_end = time.fromisoformat(TRADING_HOURS['call_auction_end'])

        return auction_start <= check_time <= auction_end

    def get_latest_trading_day(self, before_date: Optional[datetime] = None) -> datetime:
        """
        获取最近的交易日

        Args:
            before_date: 参考日期，默认为当前日期

        Returns:
            最近的交易日
        """
        if before_date is None:
            before_date = datetime.now()

        # 向前查找最近的交易日
        current = before_date
        for _ in range(10):  # 最多向前查找10天
            if self.is_trading_day(current):
                return current
            current -= timedelta(days=1)

        # 如果10天内都没有交易日，返回参考日期
        logger.warning(f"No trading day found within 10 days before {before_date}")
        return before_date

    def get_next_trading_day(self, after_date: Optional[datetime] = None) -> datetime:
        """
        获取下一个交易日

        Args:
            after_date: 参考日期，默认为当前日期

        Returns:
            下一个交易日
        """
        if after_date is None:
            after_date = datetime.now()

        # 向后查找下一个交易日
        current = after_date + timedelta(days=1)
        for _ in range(10):  # 最多向后查找10天
            if self.is_trading_day(current):
                return current
            current += timedelta(days=1)

        # 如果10天内都没有交易日，返回参考日期
        logger.warning(f"No trading day found within 10 days after {after_date}")
        return after_date


# 需要导入pandas
import pandas as pd
EOF
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/data/test_market_calendar.py -v
```

Expected: PASS all tests

**Step 5: Commit**

Run:
```bash
git add src/data/market_calendar.py tests/data/test_market_calendar.py
git commit -m "feat: add market calendar with trading day detection"
```

---

### Task 2.2: Cache Manager

**Files:**
- Create: `src/data/cache_manager.py`
- Create: `tests/data/test_cache_manager.py`

**Step 1: Write the failing test**

Run:
```bash
cat > tests/data/test_cache_manager.py << 'EOF'
import pytest
from src.data.cache_manager import CacheManager


class TestCacheManager:
    def test_set_and_get(self):
        """测试设置和获取缓存"""
        cache = CacheManager()
        cache.set('test_key', 'test_value')
        result = cache.get('test_key')
        assert result == 'test_value'

    def test_get_nonexistent_key(self):
        """测试获取不存在的键"""
        cache = CacheManager()
        result = cache.get('nonexistent_key')
        assert result is None

    def test_get_with_default(self):
        """测试获取不存在的键返回默认值"""
        cache = CacheManager()
        result = cache.get('nonexistent_key', default='default_value')
        assert result == 'default_value'

    def test_delete(self):
        """测试删除缓存"""
        cache = CacheManager()
        cache.set('test_key', 'test_value')
        cache.delete('test_key')
        result = cache.get('test_key')
        assert result is None

    def test_clear(self):
        """测试清空缓存"""
        cache = CacheManager()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.clear()
        assert cache.get('key1') is None
        assert cache.get('key2') is None

    def test_ttl_expiration(self):
        """测试TTL过期"""
        import time
        cache = CacheManager()
        cache.set('test_key', 'test_value', ttl=1)  # 1秒过期
        time.sleep(1.5)
        result = cache.get('test_key')
        assert result is None
EOF
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/data/test_cache_manager.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.data.cache_manager'"

**Step 3: Write minimal implementation**

Run:
```bash
cat > src/data/cache_manager.py << 'EOF'
"""缓存管理器模块"""
import pickle
from pathlib import Path
from typing import Any, Optional
from diskcache import Cache as DiskCache
from src.core.config_manager import ConfigManager
from src.core.logger import get_logger

logger = get_logger(__name__)


class CacheManager:
    """缓存管理器"""

    def __init__(self):
        config = ConfigManager()
        cache_config = config.get('data.cache', {})

        # 缓存目录
        cache_dir = cache_config.get('directory', './data/cache')
        Path(cache_dir).mkdir(parents=True, exist_ok=True)

        # 初始化磁盘缓存
        self._cache = DiskCache(cache_dir)

        # 是否启用缓存
        self._enabled = cache_config.get('enabled', True)

        # 默认TTL
        self._default_ttl = cache_config.get('ttl', {})

        logger.info(f"Cache manager initialized: dir={cache_dir}, enabled={self._enabled}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            default: 默认值

        Returns:
            缓存值或默认值
        """
        if not self._enabled:
            return default

        try:
            value = self._cache.get(key, default=default)
            if value != default:
                logger.debug(f"Cache hit: {key}")
            else:
                logger.debug(f"Cache miss: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），None表示不过期

        Returns:
            是否设置成功
        """
        if not self._enabled:
            return False

        try:
            self._cache.set(key, value, expire=ttl)
            logger.debug(f"Cache set: {key} (ttl={ttl})")
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存键

        Returns:
            是否删除成功
        """
        if not self._enabled:
            return False

        try:
            result = self._cache.delete(key)
            logger.debug(f"Cache delete: {key}")
            return result
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def clear(self) -> bool:
        """
        清空所有缓存

        Returns:
            是否清空成功
        """
        if not self._enabled:
            return False

        try:
            self._cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False

    def get_ttl(self, data_type: str) -> Optional[int]:
        """
        获取指定数据类型的默认TTL

        Args:
            data_type: 数据类型 ('realtime', 'daily', 'financial')

        Returns:
            TTL秒数
        """
        return self._default_ttl.get(data_type)

    def __del__(self):
        """清理资源"""
        if hasattr(self, '_cache'):
            self._cache.close()
EOF
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/data/test_cache_manager.py -v
```

Expected: PASS all tests

**Step 5: Commit**

Run:
```bash
git add src/data/cache_manager.py tests/data/test_cache_manager.py
git commit -m "feat: add cache manager with diskcache"
```

---

### Task 2.3: AKShare Provider

**Files:**
- Create: `src/data/akshare_provider.py`
- Create: `src/utils/__init__.py`
- Create: `src/utils/stock_code_helper.py`
- Create: `tests/data/test_akshare_provider.py`

**Step 1: Create stock code helper first**

Run:
```bash
mkdir -p src/utils tests/utils
touch src/utils/__init__.py tests/utils/__init__.py

cat > src/utils/stock_code_helper.py << 'EOF'
"""股票代码辅助工具"""
from src.core.constants import MARKET_PREFIX, Market


def normalize_stock_code(code: str) -> str:
    """
    标准化股票代码（添加市场前缀）

    Args:
        code: 股票代码

    Returns:
        标准化后的代码（如 600519 -> 600519.SH）
    """
    code = code.strip()

    # 如果已经有后缀，直接返回
    if '.' in code:
        return code.upper()

    # 根据前缀判断市场
    prefix = code[:3]

    # 上海主板
    if any(code.startswith(p) for p in MARKET_PREFIX['SH_MAIN']):
        return f"{code}.SH"

    # 科创板
    if any(code.startswith(p) for p in MARKET_PREFIX['STAR']):
        return f"{code}.SH"

    # 深圳主板
    if any(code.startswith(p) for p in MARKET_PREFIX['SZ_MAIN']):
        return f"{code}.SZ"

    # 创业板
    if any(code.startswith(p) for p in MARKET_PREFIX['GEM']):
        return f"{code}.SZ"

    # 北交所
    if any(code.startswith(p) for p in MARKET_PREFIX['BJ']):
        return f"{code}.BJ"

    # 默认返回原代码
    return code


def get_market_from_code(code: str) -> Market:
    """
    根据股票代码获取市场类型

    Args:
        code: 股票代码

    Returns:
        市场类型
    """
    code = code.strip()
    prefix = code[:3]

    # 科创板
    if any(code.startswith(p) for p in MARKET_PREFIX['STAR']):
        return Market.STAR_MARKET

    # 创业板
    if any(code.startswith(p) for p in MARKET_PREFIX['GEM']):
        return Market.GEM

    # 默认主板
    return Market.MAIN_BOARD


def strip_market_suffix(code: str) -> str:
    """
    移除市场后缀

    Args:
        code: 股票代码（如 600519.SH）

    Returns:
        纯数字代码（如 600519）
    """
    return code.split('.')[0]
EOF
```

**Step 2: Write the failing test**

Run:
```bash
cat > tests/data/test_akshare_provider.py << 'EOF'
import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.data.akshare_provider import AKShareProvider


class TestAKShareProvider:
    def test_get_stock_list(self):
        """测试获取股票列表"""
        provider = AKShareProvider()
        df = provider.get_stock_list()
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert '代码' in df.columns or 'symbol' in df.columns

    def test_get_realtime_quote(self):
        """测试获取实时行情"""
        provider = AKShareProvider()
        quote = provider.get_realtime_quote('600519')
        assert quote is not None
        assert isinstance(quote, dict)
        assert 'price' in quote or '最新价' in quote

    def test_get_daily_kline(self):
        """测试获取日线数据"""
        provider = AKShareProvider()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        df = provider.get_daily_kline(
            '600519',
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d')
        )
        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_cache_usage(self):
        """测试缓存功能"""
        provider = AKShareProvider()

        # 第一次调用
        quote1 = provider.get_realtime_quote('600519')

        # 第二次调用应该使用缓存
        quote2 = provider.get_realtime_quote('600519')

        assert quote1 == quote2
EOF
```

**Step 3: Run test to verify it fails**

Run:
```bash
pytest tests/data/test_akshare_provider.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.data.akshare_provider'"

**Step 4: Write minimal implementation**

Run:
```bash
cat > src/data/akshare_provider.py << 'EOF'
"""AKShare数据提供者"""
import akshare as ak
import pandas as pd
from typing import Optional, Dict, Any
from datetime import datetime
from src.core.logger import get_logger
from src.core.config_manager import ConfigManager
from src.data.cache_manager import CacheManager
from src.utils.stock_code_helper import strip_market_suffix

logger = get_logger(__name__)


class AKShareProvider:
    """AKShare数据提供者"""

    def __init__(self):
        self.config = ConfigManager()
        self.cache = CacheManager()
        self.sources = self.config.get('data.sources', {})

    def get_stock_list(self) -> pd.DataFrame:
        """
        获取A股股票列表

        Returns:
            股票列表DataFrame
        """
        cache_key = 'stock_list'

        # 尝试从缓存获取
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info("Fetching stock list from akshare...")
            df = ak.stock_zh_a_spot_em()

            # 缓存1小时
            self.cache.set(cache_key, df, ttl=3600)

            logger.info(f"Fetched {len(df)} stocks")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch stock list: {e}")
            raise

    def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        """
        获取实时行情

        Args:
            code: 股票代码

        Returns:
            行情字典
        """
        code = strip_market_suffix(code)
        cache_key = f'realtime_quote:{code}'

        # 尝试从缓存获取
        ttl = self.cache.get_ttl('realtime')
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info(f"Fetching realtime quote for {code}...")
            df = ak.stock_zh_a_spot_em()

            # 查找指定股票
            stock_data = df[df['代码'] == code]
            if stock_data.empty:
                logger.warning(f"Stock {code} not found")
                return {}

            # 转换为字典
            quote = stock_data.iloc[0].to_dict()

            # 缓存
            self.cache.set(cache_key, quote, ttl=ttl)

            return quote
        except Exception as e:
            logger.error(f"Failed to fetch realtime quote for {code}: {e}")
            raise

    def get_daily_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = 'qfq'
    ) -> pd.DataFrame:
        """
        获取日线数据

        Args:
            code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adjust: 复权类型 ('qfq'-前复权, 'hfq'-后复权, ''-不复权)

        Returns:
            日线数据DataFrame
        """
        code = strip_market_suffix(code)

        # 默认日期
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - pd.Timedelta(days=365)).strftime('%Y%m%d')

        cache_key = f'daily_kline:{code}:{start_date}:{end_date}:{adjust}'

        # 尝试从缓存获取
        ttl = self.cache.get_ttl('daily')
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info(f"Fetching daily kline for {code} ({start_date} to {end_date})...")
            df = ak.stock_zh_a_hist(
                symbol=code,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )

            # 缓存
            self.cache.set(cache_key, df, ttl=ttl)

            logger.info(f"Fetched {len(df)} daily records for {code}")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch daily kline for {code}: {e}")
            raise

    def get_financial_data(self, code: str) -> pd.DataFrame:
        """
        获取财务指标数据

        Args:
            code: 股票代码

        Returns:
            财务指标DataFrame
        """
        code = strip_market_suffix(code)
        cache_key = f'financial:{code}'

        # 尝试从缓存获取
        ttl = self.cache.get_ttl('financial')
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info(f"Fetching financial data for {code}...")
            df = ak.stock_financial_analysis_indicator(symbol=code)

            # 缓存
            self.cache.set(cache_key, df, ttl=ttl)

            logger.info(f"Fetched financial data for {code}")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch financial data for {code}: {e}")
            raise

    def get_money_flow(self, code: str) -> pd.DataFrame:
        """
        获取资金流向数据

        Args:
            code: 股票代码

        Returns:
            资金流向DataFrame
        """
        code = strip_market_suffix(code)
        cache_key = f'money_flow:{code}'

        # 尝试从缓存获取
        ttl = self.cache.get_ttl('realtime')
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            logger.info(f"Fetching money flow for {code}...")
            df = ak.stock_individual_fund_flow(stock=code, market="sh" if code.startswith('6') else "sz")

            # 缓存
            self.cache.set(cache_key, df, ttl=ttl)

            logger.info(f"Fetched money flow data for {code}")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch money flow for {code}: {e}")
            raise
EOF
```

**Step 5: Run test to verify it passes**

Run:
```bash
# 注意：这些测试需要网络连接，可能较慢
pytest tests/data/test_akshare_provider.py -v -s
```

Expected: PASS all tests (may take time due to network requests)

**Step 6: Commit**

Run:
```bash
git add src/data/akshare_provider.py src/utils/stock_code_helper.py tests/data/test_akshare_provider.py
git commit -m "feat: add akshare provider with caching support"
```

---

## Phase 3: Analysis Layer

### Task 3.1: Technical Analysis - Indicators

**Files:**
- Create: `src/analysis/__init__.py`
- Create: `src/analysis/technical/__init__.py`
- Create: `src/analysis/technical/indicators.py`
- Create: `tests/analysis/__init__.py`
- Create: `tests/analysis/technical/__init__.py`
- Create: `tests/analysis/technical/test_indicators.py`

**Step 1: Write the failing test**

Run:
```bash
mkdir -p src/analysis/technical tests/analysis/technical
touch src/analysis/__init__.py src/analysis/technical/__init__.py
touch tests/analysis/__init__.py tests/analysis/technical/__init__.py

cat > tests/analysis/technical/test_indicators.py << 'EOF'
import pytest
import pandas as pd
import numpy as np
from src.analysis.technical.indicators import TechnicalIndicators


class TestTechnicalIndicators:
    @pytest.fixture
    def sample_df(self):
        """创建示例DataFrame"""
        dates = pd.date_range('2023-01-01', periods=100)
        np.random.seed(42)
        df = pd.DataFrame({
            '日期': dates,
            '收盘': np.cumsum(np.random.randn(100)) + 100,
            '最高': np.cumsum(np.random.randn(100)) + 105,
            '最低': np.cumsum(np.random.randn(100)) + 95,
            '成交量': np.random.randint(1000000, 10000000, 100)
        })
        return df

    def test_calculate_ma(self, sample_df):
        """测试计算移动平均线"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_ma(sample_df, periods=[5, 10, 20])

        assert 'MA5' in result.columns
        assert 'MA10' in result.columns
        assert 'MA20' in result.columns
        assert not result['MA5'].isna().all()

    def test_calculate_macd(self, sample_df):
        """测试计算MACD"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_macd(sample_df)

        assert 'MACD' in result.columns
        assert 'MACD_signal' in result.columns
        assert 'MACD_hist' in result.columns

    def test_calculate_rsi(self, sample_df):
        """测试计算RSI"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_rsi(sample_df, period=14)

        assert 'RSI' in result.columns
        assert result['RSI'].max() <= 100
        assert result['RSI'].min() >= 0

    def test_calculate_kdj(self, sample_df):
        """测试计算KDJ"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_kdj(sample_df)

        assert 'K' in result.columns
        assert 'D' in result.columns
        assert 'J' in result.columns

    def test_calculate_boll(self, sample_df):
        """测试计算布林带"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_boll(sample_df)

        assert 'BOLL_UPPER' in result.columns
        assert 'BOLL_MIDDLE' in result.columns
        assert 'BOLL_LOWER' in result.columns

    def test_calculate_all(self, sample_df):
        """测试计算所有指标"""
        indicators = TechnicalIndicators()
        result = indicators.calculate_all(sample_df)

        # 验证主要指标都已添加
        assert 'MA5' in result.columns
        assert 'MACD' in result.columns
        assert 'RSI' in result.columns
        assert 'K' in result.columns
        assert 'BOLL_UPPER' in result.columns
EOF
```

**Step 2: Run test to verify it fails**

Run:
```bash
pytest tests/analysis/technical/test_indicators.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.analysis.technical.indicators'"

**Step 3: Write minimal implementation**

Run:
```bash
cat > src/analysis/technical/indicators.py << 'EOF'
"""技术指标计算模块"""
import pandas as pd
import pandas_ta as ta
from typing import List, Dict, Any
from src.core.logger import get_logger
from src.core.constants import DEFAULT_INDICATORS

logger = get_logger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""

    def __init__(self):
        self.config = DEFAULT_INDICATORS

    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        标准化DataFrame列名

        Args:
            df: 原始DataFrame

        Returns:
            标准化后的DataFrame
        """
        df = df.copy()

        # 列名映射
        column_map = {
            '收盘': 'close',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '日期': 'date',
        }

        df.rename(columns=column_map, inplace=True)
        return df

    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算移动平均线

        Args:
            df: 股票数据
            periods: MA周期列表

        Returns:
            添加MA指标的DataFrame
        """
        if periods is None:
            periods = self.config['MA']

        df = self._standardize_columns(df)

        for period in periods:
            df[f'MA{period}'] = ta.sma(df['close'], length=period)

        return df

    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = None,
        slow: int = None,
        signal: int = None
    ) -> pd.DataFrame:
        """
        计算MACD指标

        Args:
            df: 股票数据
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期

        Returns:
            添加MACD指标的DataFrame
        """
        macd_config = self.config['MACD']
        if fast is None:
            fast = macd_config['fast']
        if slow is None:
            slow = macd_config['slow']
        if signal is None:
            signal = macd_config['signal']

        df = self._standardize_columns(df)

        macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        df['MACD'] = macd[f'MACD_{fast}_{slow}_{signal}']
        df['MACD_hist'] = macd[f'MACDh_{fast}_{slow}_{signal}']
        df['MACD_signal'] = macd[f'MACDs_{fast}_{slow}_{signal}']

        return df

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """
        计算RSI指标

        Args:
            df: 股票数据
            period: RSI周期

        Returns:
            添加RSI指标的DataFrame
        """
        df = self._standardize_columns(df)
        df['RSI'] = ta.rsi(df['close'], length=period)
        return df

    def calculate_kdj(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算KDJ指标

        Args:
            df: 股票数据

        Returns:
            添加KDJ指标的DataFrame
        """
        df = self._standardize_columns(df)

        kdj_config = self.config['KDJ']
        n = kdj_config['n']

        stoch = ta.stoch(df['high'], df['low'], df['close'], k=n, d=3, smooth_k=3)
        df['K'] = stoch[f'STOCHk_{n}_3_3']
        df['D'] = stoch[f'STOCHd_{n}_3_3']
        df['J'] = 3 * df['K'] - 2 * df['D']

        return df

    def calculate_boll(self, df: pd.DataFrame, n: int = 20, std: int = 2) -> pd.DataFrame:
        """
        计算布林带指标

        Args:
            df: 股票数据
            n: 周期
            std: 标准差倍数

        Returns:
            添加布林带指标的DataFrame
        """
        df = self._standardize_columns(df)

        bbands = ta.bbands(df['close'], length=n, std=std)
        df['BOLL_UPPER'] = bbands[f'BBU_{n}_{std}.0']
        df['BOLL_MIDDLE'] = bbands[f'BBM_{n}_{std}.0']
        df['BOLL_LOWER'] = bbands[f'BBL_{n}_{std}.0']

        return df

    def calculate_volume_ma(self, df: pd.DataFrame, periods: List[int] = None) -> pd.DataFrame:
        """
        计算成交量均线

        Args:
            df: 股票数据
            periods: 均线周期列表

        Returns:
            添加成交量均线的DataFrame
        """
        if periods is None:
            periods = self.config['VOL_MA']

        df = self._standardize_columns(df)

        for period in periods:
            df[f'VOL_MA{period}'] = ta.sma(df['volume'], length=period)

        return df

    def calculate_atr(self, df: pd.DataFrame, period: int = None) -> pd.DataFrame:
        """
        计算ATR指标

        Args:
            df: 股票数据
            period: ATR周期

        Returns:
            添加ATR指标的DataFrame
        """
        if period is None:
            period = self.config['ATR']

        df = self._standardize_columns(df)
        df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=period)

        return df

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术指标

        Args:
            df: 股票数据

        Returns:
            添加所有指标的DataFrame
        """
        logger.info("Calculating all technical indicators...")

        df = self.calculate_ma(df)
        df = self.calculate_macd(df)
        df = self.calculate_rsi(df)
        df = self.calculate_kdj(df)
        df = self.calculate_boll(df)
        df = self.calculate_volume_ma(df)
        df = self.calculate_atr(df)

        logger.info("All technical indicators calculated")
        return df
EOF
```

**Step 4: Run test to verify it passes**

Run:
```bash
pytest tests/analysis/technical/test_indicators.py -v
```

Expected: PASS all tests

**Step 5: Commit**

Run:
```bash
git add src/analysis/technical/indicators.py tests/analysis/technical/test_indicators.py
git commit -m "feat: add technical indicators calculation with pandas_ta"
```

---

**Note:** The plan continues with more tasks for:
- Phase 3: Fundamental analysis, capital analysis, AI analysis
- Phase 4: Strategy and backtest modules
- Phase 5: Screening and risk management
- Phase 6: Monitoring and reporting
- Phase 7: CLI scripts

Due to length constraints, I'll save the plan here and continue if needed.

---

## Execution Options

After reviewing the first 7 tasks above (foundation and data layer), would you like to:

1. **Continue reading the complete plan** (I'll add remaining phases)
2. **Start implementing** using one of these approaches:
   - **Subagent-Driven**: I dispatch fresh subagents per task, review between tasks
   - **Parallel Session**: You open new session with executing-plans skill

Which approach would you prefer?
