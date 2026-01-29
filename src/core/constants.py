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
