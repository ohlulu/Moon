from dataclasses import dataclass
from typing import Optional
import math

@dataclass
class LeverageInfo:
    """槓桿交易資訊"""
    suggested_leverage: float   # 建議槓桿倍數
    max_leverage: float        # 最大可用槓桿
    risk_level: str           # 風險等級：'low', 'medium', 'high'
    description: str          # 說明
    score_details: dict       # 詳細評分數據

class LeverageCalculator:
    """槓桿計算器"""
    
    def __init__(self, max_leverage: float = 8.0, min_leverage: float = 4.0):
        """初始化槓桿計算器
        
        Args:
            max_leverage: 用戶期望的最大槓桿倍數
            min_leverage: 用戶期望的最小槓桿倍數
        """
        self.max_leverage = max_leverage
        self.min_leverage = min_leverage
        self.leverage_range = max_leverage - min_leverage
        
        # 市值排名分界點
        self.rank_thresholds = {
            'top': 20,      # 大市值
            'mid': 150,     # 中市值
            'bottom': 500   # 小市值
        }
        
        # 波動率基準值
        self.volatility_params = {
            'base_normal': 0.015,  # 基礎正常波動率（排名第1的幣種）
            'base_max': 0.035,     # 基礎最大波動率
            'rank_factor': 0.0001  # 排名影響因子
        }
    
    def _get_rank_based_params(self, market_cap_rank: int) -> tuple[float, float, float]:
        """根據市值排名計算參數
        
        Args:
            market_cap_rank: 市值排名（1-500）
            
        Returns:
            (正常波動率, 最大波動率, sigmoid曲線陡峭度)
        """
        # 確保排名在有效範圍內
        rank = max(1, min(self.rank_thresholds['bottom'], market_cap_rank))
        
        # 1. 計算正常波動率
        # 使用對數函數使波動率隨排名增加而增加，但增速逐漸降低
        normal_volatility = self.volatility_params['base_normal'] * (1 + math.log10(rank) * 0.5)
        
        # 2. 計算最大波動率
        max_volatility = self.volatility_params['base_max'] * (1 + math.log10(rank) * 0.6)
        
        # 3. 計算 sigmoid 曲線陡峭度
        # 排名越高，曲線越陡（對波動率變化越敏感）
        if rank <= self.rank_thresholds['top']:
            k = -300
        elif rank <= self.rank_thresholds['mid']:
            k = -250 + (rank - self.rank_thresholds['top']) * 1.0  # 逐漸變得平緩
        else:
            k = -200 + (rank - self.rank_thresholds['mid']) * 0.2  # 更加平緩
            
        return normal_volatility, max_volatility, k
    
    def _calculate_volatility_score(self, volatility: float, market_cap_rank: int) -> float:
        """計算波動率分數
        
        使用 sigmoid 函數將波動率映射到 0-1 範圍，提供更平滑的過渡
        低波動率得高分，高波動率得低分
        
        Args:
            volatility: ATR/價格
            market_cap_rank: 市值排名（1-500）
            
        Returns:
            0-1 之間的分數
        """
        # 獲取基於排名的參數
        normal_volatility, max_volatility, k = self._get_rank_based_params(market_cap_rank)
        
        # 使用 sigmoid 函數計算分數
        score = 1 / (1 + math.exp(k * (volatility - normal_volatility)))
        
        # 如果波動率超過最大值，額外懲罰
        if volatility > max_volatility:
            penalty = math.exp(-5 * (volatility - max_volatility))  # 指數衰減
            score *= penalty
        
        return score
    
    def _calculate_trend_score(self, trend_strength: float) -> float:
        """計算趨勢強度分數
        
        使用指數函數增強強趨勢的影響
        
        Args:
            trend_strength: 0-1 的趨勢強度
            
        Returns:
            0-1 之間的分數
        """
        # 使用指數函數，強化高趨勢強度的影響
        return math.pow(trend_strength, 0.7)  # 0.7 次方可以適度提升中等強度的權重
    
    def _calculate_volume_score(self, volume_stability: float) -> float:
        """計算成交量穩定性分數
        
        使用對數函數增強對低穩定性的懲罰
        
        Args:
            volume_stability: 0-1 的成交量穩定性
            
        Returns:
            0-1 之間的分數
        """
        # 使用對數函數，加強對低穩定性的懲罰
        if volume_stability <= 0:
            return 0
        return math.log(1 + 9 * volume_stability) / math.log(10)
    
    def _calculate_composite_score(self, volatility_score: float, trend_score: float, volume_score: float) -> float:
        """計算綜合分數
        
        使用加權幾何平均數，確保所有因素都很重要
        
        Args:
            volatility_score: 波動率分數
            trend_score: 趨勢分數
            volume_score: 成交量分數
            
        Returns:
            0-1 之間的綜合分數
        """
        # 使用加權幾何平均數
        weights = [0.5, 0.3, 0.2]  # 波動率、趨勢、成交量的權重
        scores = [volatility_score, trend_score, volume_score]
        
        weighted_product = math.prod([math.pow(s, w) for s, w in zip(scores, weights)])
        return weighted_product
    
    def calculate(self, volatility: float,trend_strength: float,volume_stability: float,market_cap_rank: int) -> LeverageInfo:
        """計算建議槓桿倍數
        
        Args:
            volatility: 波動率（ATR/價格）
            trend_strength: 趨勢強度（0-1）
            volume_stability: 成交量穩定性（0-1）
            market_cap_rank: 市值排名（1-500）
            
        Returns:
            LeverageInfo 物件
        """
        # 1. 計算各項分數
        volatility_score = self._calculate_volatility_score(volatility, market_cap_rank)
        trend_score = self._calculate_trend_score(trend_strength)
        volume_score = self._calculate_volume_score(volume_stability)
        
        # 2. 計算綜合分數
        composite_score = self._calculate_composite_score(
            volatility_score, trend_score, volume_score)
        
        # 3. 計算建議槓桿
        base_leverage = self.min_leverage + self.leverage_range * composite_score
        
        # 4. 動態調整係數（基於市場條件）
        market_condition_multiplier = 1.0
        
        # 極端情況調整
        normal_volatility, max_volatility, _ = self._get_rank_based_params(market_cap_rank)
        if volatility > max_volatility:
            market_condition_multiplier *= 0.7  # 高波動率大幅降低槓桿
        elif trend_strength > 0.8 and volume_stability > 0.7:
            market_condition_multiplier *= 1.1  # 強趨勢且穩定時小幅提升槓桿
        
        # 5. 計算最終槓桿
        final_leverage = base_leverage * market_condition_multiplier
        
        # 確保在允許範圍內
        final_leverage = max(self.min_leverage, min(self.max_leverage, final_leverage))
        
        # 6. 計算相對槓桿水平
        relative_level = (final_leverage - self.min_leverage) / self.leverage_range
        
        # 7. 決定風險等級
        if relative_level <= 0.33:
            risk_level = 'low'
            risk_description = '低風險，適合保守策略'
        elif relative_level <= 0.66:
            risk_level = 'medium'
            risk_description = '中等風險，適合均衡策略'
        else:
            risk_level = 'high'
            risk_description = '高風險，需要嚴格風險控制'
        
        # 8. 記錄詳細評分
        score_details = {
            'volatility_score': round(volatility_score, 3),
            'trend_score': round(trend_score, 3),
            'volume_score': round(volume_score, 3),
            'composite_score': round(composite_score, 3),
            'market_condition_multiplier': round(market_condition_multiplier, 3),
            'normal_volatility': round(normal_volatility, 4),
            'max_volatility': round(max_volatility, 4)
        }
        
        # 9. 生成說明
        description = (
            f"建議槓桿：{final_leverage:.1f}x（範圍：{self.min_leverage:.1f}x-{self.max_leverage:.1f}x）\n"
            f"風險等級：{risk_level}（相對水平：{relative_level:.1%}）\n"
            f"市值排名：{market_cap_rank}\n"
            f"預期波動率範圍：{normal_volatility:.2%} - {max_volatility:.2%}\n"
            f"當前波動率：{volatility:.2%}\n"
            f"波動率評分：{volatility_score:.3f}\n"
            f"趨勢強度評分：{trend_score:.3f}\n"
            f"成交量穩定性評分：{volume_score:.3f}\n"
            f"綜合評分：{composite_score:.3f}\n"
            f"市場條件調整：{market_condition_multiplier:.2f}\n"
            f"風險提示：{risk_description}"
        )
        
        return LeverageInfo(
            suggested_leverage=round(final_leverage, 1),
            max_leverage=self.max_leverage,
            risk_level=risk_level,
            description=description,
            score_details=score_details
        )

# 使用示例
if __name__ == "__main__":
    # 保守型用戶
    conservative = LeverageCalculator(max_leverage=4.0, min_leverage=1.0)
    
    # 激進型用戶
    aggressive = LeverageCalculator(max_leverage=10.0, min_leverage=5.0)
    
    # 測試數據
    test_data = {
        "volatility": 0.01,      # 1% 波動率
        "trend_strength": 0.8,   # 80% 趨勢強度
        "volume_stability": 0.7,  # 70% 成交量穩定性
        "market_cap_rank": 1     # 市值第一名
    }
    
    # 計算結果
    conservative_result = conservative.calculate(**test_data)
    aggressive_result = aggressive.calculate(**test_data)
    
    print("保守型用戶建議：")
    print(conservative_result.description)
    print("\n激進型用戶建議：")
    print(aggressive_result.description) 