# strategies/__init__.py - 策略注册
from strategies.vp_sync import evaluate as vp_sync_evaluate
from strategies.vp_pulse import evaluate as vp_pulse_evaluate
from strategies.vr_slope import evaluate as vr_slope_evaluate

# 策略注册表：策略ID → (evaluate函数, 参数列表)
STRATEGIES = {
    'vp_sync': vp_sync_evaluate,
    'vp_pulse': vp_pulse_evaluate,
    'vr_slope': vr_slope_evaluate,
}


def get_strategy(strategy_id):
    """根据策略ID获取evaluate函数"""
    if strategy_id not in STRATEGIES:
        raise ValueError(f"未知策略: {strategy_id}，可用策略: {list(STRATEGIES.keys())}")
    return STRATEGIES[strategy_id]


def list_strategies():
    """列出所有可用策略"""
    return list(STRATEGIES.keys())
