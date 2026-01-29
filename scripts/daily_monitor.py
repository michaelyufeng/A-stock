#!/usr/bin/env python
"""
每日监控脚本

使用MonitoringService监控股票池，自动检测交易信号并发送提醒。

用法:
    python scripts/daily_monitor.py                  # 使用默认配置
    python scripts/daily_monitor.py --config custom.yaml  # 使用自定义配置
    python scripts/daily_monitor.py --once           # 运行一次后退出
"""

import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.monitoring import MonitoringService
import logging


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/monitoring.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='A股每日监控服务')
    parser.add_argument(
        '--config',
        default='config/monitoring.yaml',
        help='配置文件路径（默认: config/monitoring.yaml）'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='运行一次后退出（默认: 持续运行）'
    )

    args = parser.parse_args()

    # 设置日志
    setup_logging()

    print("=" * 60)
    print("  A股监控服务")
    print("=" * 60)
    print(f"配置文件: {args.config}")
    print(f"运行模式: {'单次执行' if args.once else '持续监控'}")
    print()

    try:
        # 创建监控服务
        service = MonitoringService(args.config)

        # 显示监控列表
        watchlist = service.get_watchlist()
        print(f"监控股票数: {len(watchlist)}")
        for code, name in list(watchlist.items())[:5]:
            print(f"  - {code} {name}")
        if len(watchlist) > 5:
            print(f"  ... 及其他 {len(watchlist) - 5} 只")
        print()

        if args.once:
            # 运行一次
            print("开始执行监控...\n")
            signals = service.run_once()

            if signals:
                print(f"\n检测到 {len(signals)} 个信号:")
                for signal in signals:
                    print(f"  [{signal.priority}] {signal.stock_name}: {signal.description}")
            else:
                print("\n未检测到信号")

            # 生成报告
            print("\n" + service.generate_daily_summary())

        else:
            # 持续运行
            print("开始监控...")
            print(f"更新频率: {service.update_interval}秒")
            print("按 Ctrl+C 停止\n")

            service.run()

    except FileNotFoundError:
        print(f"\n❌ 配置文件未找到: {args.config}")
        print("请确保配置文件存在，或使用 --config 指定正确的路径")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n正在停止监控...")

        # 生成每日总结
        try:
            summary = service.generate_daily_summary()
            print("\n" + summary)

            # 保存报告
            from datetime import datetime
            report_file = f"logs/summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(summary)
            print(f"\n报告已保存: {report_file}")

        except Exception as e:
            print(f"\n生成报告时出错: {e}")

        print("\n监控已停止")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
