from dataclasses import dataclass
from typing import Optional
import math

@dataclass
class LeverageInfo:
    """槓桿交易資訊"""
    suggested_leverage: int    # 建議槓桿倍數
    max_leverage: int         # 最大可用槓桿
    risk_level: str           # 風險等級：'low', 'medium', 'high'
    description: str          # 說明
    score_details: dict       # 詳細評分數據

class LeverageCalculator:
    """槓桿計算器"""
    
    def __init__(self, min_leverage: int = 4, max_leverage: int = 8):
        """初始化槓桿計算器
        
        Args:
            min_leverage: 用戶期望的最小槓桿倍數
            max_leverage: 用戶期望的最大槓桿倍數
        """
        self.max_leverage = max_leverage
        self.min_leverage = min_leverage
        self.leverage_range = max_leverage - min_leverage
    
    def _calculate_risk_score(self, volatility: float) -> float:
        """計算風險分數
        
        基於實際市場波動率範圍計算風險分數：
        - 0.1%-0.5%: 穩定幣範圍
        - 1%-3%: 主流幣穩定期
        - 3%-8%: 主流幣波動期
        - 5%-15%: 小市值幣
        - >15%: 極端行情
        
        Args:
            volatility: ATR/價格
            
        Returns:
            0-1 之間的分數
        """
        if volatility <= 0.005:  # 穩定幣
            return 1.0
        elif volatility <= 0.02:  # 低波動（主流幣穩定期）
            return 0.9 - (volatility - 0.005) * 20
        elif volatility <= 0.05:  # 中等波動（主流幣波動期）
            return 0.7 - (volatility - 0.02) * 10
        elif volatility <= 0.10:  # 高波動（小市值幣）
            return 0.4 - (volatility - 0.05) * 4
        else:  # 極端波動
            return max(0.1, 0.2 - (volatility - 0.10) * 2)
    
    def _calculate_trend_score(self, trend_strength: float) -> float:
        """計算趨勢分數
        
        Args:
            trend_strength: 0-1 的趨勢強度
            
        Returns:
            0-1 之間的分數
        """
        return trend_strength  # 直接使用趨勢強度，不需要額外轉換
    
    def _map_score_to_leverage(self, composite_score: float) -> float:
        """將綜合分數映射到槓桿範圍
        
        使用分段線性映射，確保不同分數能得到明顯不同的槓桿
        
        Args:
            composite_score: 0-1 之間的綜合分數
            
        Returns:
            建議槓桿倍數
        """
        # 基礎槓桿計算
        if composite_score <= 0.2:
            # 0-0.2 分數使用最低槓桿
            return self.min_leverage
        elif composite_score <= 0.4:
            # 0.2-0.4 分數使用 min 到 min + 20% 範圍
            ratio = (composite_score - 0.2) / 0.2
            return self.min_leverage + self.leverage_range * 0.2 * ratio
        elif composite_score <= 0.6:
            # 0.4-0.6 分數使用 min + 20% 到 min + 50% 範圍
            ratio = (composite_score - 0.4) / 0.2
            return self.min_leverage + self.leverage_range * (0.2 + 0.3 * ratio)
        elif composite_score <= 0.8:
            # 0.6-0.8 分數使用 min + 50% 到 min + 80% 範圍
            ratio = (composite_score - 0.6) / 0.2
            return self.min_leverage + self.leverage_range * (0.5 + 0.3 * ratio)
        else:
            # 0.8-1.0 分數使用 min + 80% 到 max 範圍
            ratio = (composite_score - 0.8) / 0.2
            return self.min_leverage + self.leverage_range * (0.8 + 0.2 * ratio)
    
    def calculate(self, volatility: float, trend_strength: float) -> LeverageInfo:
        """計算建議槓桿倍數
        
        Args:
            volatility: 波動率（ATR/價格）
            trend_strength: 趨勢強度（0-1）
            
        Returns:
            LeverageInfo 物件
        """
        # 1. 計算風險和趨勢分數
        risk_score = self._calculate_risk_score(volatility)
        trend_score = self._calculate_trend_score(trend_strength)
        
        # 2. 計算綜合分數
        # 根據波動率調整權重：波動率越高，風險權重越高
        risk_weight = min(0.8, 0.6 + volatility)  # 最高到 0.8
        trend_weight = 1 - risk_weight
        composite_score = risk_score * risk_weight + trend_score * trend_weight
        
        # 3. 將分數映射到槓桿範圍
        leverage = self._map_score_to_leverage(composite_score)
        
        # 4. 確保在允許範圍內，並轉換為整數
        final_leverage = round(max(self.min_leverage, min(self.max_leverage, leverage)))
        
        # 5. 計算相對槓桿水平
        relative_level = (final_leverage - self.min_leverage) / self.leverage_range
        
        # 6. 決定風險等級
        if relative_level <= 0.33:
            risk_level = 'low'
            risk_description = '低風險，適合保守策略'
        elif relative_level <= 0.66:
            risk_level = 'medium'
            risk_description = '中等風險，適合均衡策略'
        else:
            risk_level = 'high'
            risk_description = '高風險，需要嚴格風險控制'
        
        # 7. 記錄詳細評分
        score_details = {
            'risk_score': round(risk_score, 3),
            'trend_score': round(trend_score, 3),
            'composite_score': round(composite_score, 3)
        }
        
        # 8. 生成說明
        description = (
            f"建議槓桿：{final_leverage}x（範圍：{self.min_leverage}x-{self.max_leverage}x）\n"
            f"風險等級：{risk_level}（相對水平：{relative_level:.1%}）\n"
            f"波動率：{volatility:.1%}\n"
            f"趨勢強度：{trend_strength:.1%}\n"
            # f"風險評分：{risk_score:.3f}\n"
            # f"趨勢評分：{trend_score:.3f}\n"
            # f"綜合評分：{composite_score:.3f}\n"
            # f"風險提示：{risk_description}"
        )
        
        return LeverageInfo(
            suggested_leverage=final_leverage,
            max_leverage=self.max_leverage,
            risk_level=risk_level,
            description=description,
            score_details=score_details
        )
