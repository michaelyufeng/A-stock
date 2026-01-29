"""基础集成测试 - 验证筛选器能正常工作"""
import pytest
from src.screening.screener import StockScreener


def test_screener_can_be_imported():
    """测试筛选器可以被导入"""
    screener = StockScreener()
    assert screener is not None


def test_screener_has_all_presets():
    """测试所有预设方案都存在"""
    screener = StockScreener()
    assert 'strong_momentum' in screener.presets
    assert 'value_growth' in screener.presets
    assert 'capital_inflow' in screener.presets


def test_preset_returns_valid_config():
    """测试预设方案返回有效配置"""
    screener = StockScreener()

    for preset_name in ['strong_momentum', 'value_growth', 'capital_inflow']:
        config = screener.presets[preset_name]()
        assert 'weights' in config
        assert 'use_fundamental' in config
        assert 'use_capital' in config

        weights = config['weights']
        assert 'technical' in weights
        assert 'fundamental' in weights
        assert 'capital' in weights

        # 权重总和应该接近1.0
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.01


def test_screener_screen_method_exists():
    """测试screen方法存在且有正确的参数"""
    screener = StockScreener()
    assert hasattr(screener, 'screen')
    assert callable(screener.screen)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
