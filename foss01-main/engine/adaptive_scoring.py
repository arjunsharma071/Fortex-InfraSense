# engine/adaptive_scoring.py
"""
InfraSense AI - Adaptive Country-Specific Scoring Engine
Dynamically adjusts ISI weights based on country/region characteristics
"""

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np


class DevelopmentLevel(Enum):
    """Country development classification"""
    DEVELOPED = "developed"
    DEVELOPING = "developing"
    EMERGING = "emerging"
    LEAST_DEVELOPED = "least_developed"


@dataclass
class CountryProfile:
    """Profile for country-specific characteristics"""
    code: str
    name: str
    development_level: DevelopmentLevel
    currency: str
    currency_symbol: str
    exchange_rate_usd: float  # Local currency per 1 USD
    traffic_side: str  # 'left' or 'right'
    mixed_traffic: bool
    monsoon_affected: bool
    seismic_zone: int  # 0-5
    population_density: float  # per sq km


class AdaptiveScoringEngine:
    """
    Dynamically adjusts ISI weights based on country/region
    Implements the formula:
    ISI = w1*Congestion + w2*Safety + w3*Growth + w4*Quality
    Where weights vary by country characteristics
    """
    
    # Country-specific weight configurations
    COUNTRY_WEIGHTS = {
        'IN': {  # India (dense urban, mixed traffic)
            'congestion': 0.40,  # Very important - severe urban congestion
            'safety': 0.35,      # High accident rates
            'growth': 0.15,      # Rapid urbanization
            'quality': 0.10,     # Often poor maintenance
            'description': 'Dense urban, mixed traffic (auto-rickshaws, bikes, pedestrians)'
        },
        'US': {  # USA (suburban sprawl, car-centric)
            'congestion': 0.30,
            'safety': 0.25,
            'growth': 0.20,
            'quality': 0.25,     # Higher maintenance standards expected
            'description': 'Car-centric, highway focus, suburban sprawl'
        },
        'DE': {  # Germany (precision engineering)
            'congestion': 0.25,
            'safety': 0.30,      # Strict safety standards
            'growth': 0.15,
            'quality': 0.30,     # Excellent maintenance expected
            'description': 'High engineering standards, autobahn culture'
        },
        'NG': {  # Nigeria (developing, informal settlements)
            'congestion': 0.35,
            'safety': 0.20,      # Limited accident data
            'growth': 0.40,      # Explosive urban growth
            'quality': 0.05,     # Minimal maintenance infrastructure
            'description': 'Rapid urbanization, informal settlements, limited data'
        },
        'BR': {  # Brazil
            'congestion': 0.35,
            'safety': 0.30,
            'growth': 0.25,
            'quality': 0.10,
            'description': 'Mixed development, BRT systems, favela considerations'
        },
        'JP': {  # Japan
            'congestion': 0.30,
            'safety': 0.25,
            'growth': 0.10,      # Stable population
            'quality': 0.35,     # High quality expectations
            'description': 'High-tech infrastructure, seismic considerations'
        },
        'AU': {  # Australia
            'congestion': 0.25,
            'safety': 0.30,
            'growth': 0.20,
            'quality': 0.25,
            'description': 'Sparse population, long-distance freight'
        },
        'AE': {  # UAE
            'congestion': 0.35,
            'safety': 0.25,
            'growth': 0.30,      # Rapid development
            'quality': 0.10,
            'description': 'Rapid development, extreme heat considerations'
        },
        'CN': {  # China
            'congestion': 0.40,
            'safety': 0.25,
            'growth': 0.25,
            'quality': 0.10,
            'description': 'Massive scale, rapid infrastructure development'
        },
        'UK': {  # United Kingdom
            'congestion': 0.30,
            'safety': 0.30,
            'growth': 0.15,
            'quality': 0.25,
            'description': 'Historical infrastructure, strict safety standards'
        },
        'FR': {  # France
            'congestion': 0.30,
            'safety': 0.30,
            'growth': 0.15,
            'quality': 0.25,
            'description': 'Well-maintained network, toll roads'
        },
        'MX': {  # Mexico
            'congestion': 0.35,
            'safety': 0.30,
            'growth': 0.25,
            'quality': 0.10,
            'description': 'Urban sprawl, developing infrastructure'
        },
        'ZA': {  # South Africa
            'congestion': 0.30,
            'safety': 0.35,      # High accident rates
            'growth': 0.25,
            'quality': 0.10,
            'description': 'Dual economy, safety concerns'
        },
        'ID': {  # Indonesia
            'congestion': 0.40,
            'safety': 0.30,
            'growth': 0.20,
            'quality': 0.10,
            'description': 'Island nation, Jakarta super-congestion'
        },
        'SA': {  # Saudi Arabia
            'congestion': 0.30,
            'safety': 0.30,
            'growth': 0.30,
            'quality': 0.10,
            'description': 'Rapid modernization, Vision 2030'
        }
    }
    
    # Country profiles with detailed information
    COUNTRY_PROFILES = {
        'IN': CountryProfile('IN', 'India', DevelopmentLevel.DEVELOPING, 'INR', '₹', 83.0, 'left', True, True, 3, 464),
        'US': CountryProfile('US', 'United States', DevelopmentLevel.DEVELOPED, 'USD', '$', 1.0, 'right', False, False, 2, 36),
        'DE': CountryProfile('DE', 'Germany', DevelopmentLevel.DEVELOPED, 'EUR', '€', 0.92, 'right', False, False, 1, 240),
        'NG': CountryProfile('NG', 'Nigeria', DevelopmentLevel.DEVELOPING, 'NGN', '₦', 1550.0, 'right', True, True, 1, 226),
        'BR': CountryProfile('BR', 'Brazil', DevelopmentLevel.EMERGING, 'BRL', 'R$', 5.0, 'right', True, True, 2, 25),
        'JP': CountryProfile('JP', 'Japan', DevelopmentLevel.DEVELOPED, 'JPY', '¥', 150.0, 'left', False, False, 5, 347),
        'AU': CountryProfile('AU', 'Australia', DevelopmentLevel.DEVELOPED, 'AUD', 'A$', 1.55, 'left', False, False, 1, 3),
        'AE': CountryProfile('AE', 'UAE', DevelopmentLevel.DEVELOPED, 'AED', 'د.إ', 3.67, 'right', False, False, 0, 118),
        'CN': CountryProfile('CN', 'China', DevelopmentLevel.EMERGING, 'CNY', '¥', 7.2, 'right', True, False, 4, 153),
        'UK': CountryProfile('UK', 'United Kingdom', DevelopmentLevel.DEVELOPED, 'GBP', '£', 0.79, 'left', False, False, 1, 281),
        'FR': CountryProfile('FR', 'France', DevelopmentLevel.DEVELOPED, 'EUR', '€', 0.92, 'right', False, False, 2, 119),
        'MX': CountryProfile('MX', 'Mexico', DevelopmentLevel.EMERGING, 'MXN', '$', 17.0, 'right', True, False, 4, 66),
        'ZA': CountryProfile('ZA', 'South Africa', DevelopmentLevel.EMERGING, 'ZAR', 'R', 18.5, 'left', True, False, 1, 49),
        'ID': CountryProfile('ID', 'Indonesia', DevelopmentLevel.DEVELOPING, 'IDR', 'Rp', 15800.0, 'left', True, True, 4, 151),
        'SA': CountryProfile('SA', 'Saudi Arabia', DevelopmentLevel.DEVELOPED, 'SAR', 'ر.س', 3.75, 'right', False, False, 1, 16),
    }
    
    def __init__(self):
        self.cache = {}
    
    def get_weights(self, country_code: str) -> Dict[str, float]:
        """Get ISI weights for a country"""
        weights = self.COUNTRY_WEIGHTS.get(country_code, self.COUNTRY_WEIGHTS['IN'])
        return {k: v for k, v in weights.items() if k != 'description'}
    
    def get_country_profile(self, country_code: str) -> Optional[CountryProfile]:
        """Get detailed country profile"""
        return self.COUNTRY_PROFILES.get(country_code)
    
    def calculate_dynamic_isi(self, country_code: str, scores: Dict[str, float]) -> Tuple[float, Dict]:
        """
        Calculate ISI using country-specific weighting
        
        Args:
            country_code: ISO 2-letter country code
            scores: Dictionary with keys 'congestion', 'safety', 'growth', 'quality'
        
        Returns:
            Tuple of (ISI score, weights used)
        """
        weights = self.get_weights(country_code)
        
        # Ensure all required scores are present
        required_keys = ['congestion', 'safety', 'growth', 'quality']
        for key in required_keys:
            if key not in scores:
                scores[key] = 0.5  # Default value
        
        # Calculate weighted ISI
        isi = (
            weights['congestion'] * scores['congestion'] +
            weights['safety'] * scores['safety'] +
            weights['growth'] * scores['growth'] +
            weights['quality'] * scores['quality']
        )
        
        # Ensure ISI is in valid range [0, 1]
        isi = max(0.0, min(1.0, isi))
        
        return isi, weights
    
    def get_score_breakdown(self, country_code: str, scores: Dict[str, float]) -> Dict[str, Any]:
        """
        Get detailed breakdown of ISI calculation
        """
        isi, weights = self.calculate_dynamic_isi(country_code, scores)
        profile = self.get_country_profile(country_code)
        country_info = self.COUNTRY_WEIGHTS.get(country_code, self.COUNTRY_WEIGHTS['IN'])
        
        # Calculate contribution of each component
        contributions = {
            key: weights[key] * scores.get(key, 0.5)
            for key in ['congestion', 'safety', 'growth', 'quality']
        }
        
        # Identify dominant factor
        dominant_factor = max(contributions, key=contributions.get)
        
        return {
            'isi_score': round(isi, 4),
            'country_code': country_code,
            'country_description': country_info.get('description', 'Unknown'),
            'weights_used': weights,
            'input_scores': scores,
            'contributions': {k: round(v, 4) for k, v in contributions.items()},
            'dominant_factor': dominant_factor,
            'dominant_contribution': round(contributions[dominant_factor], 4),
            'profile': {
                'name': profile.name if profile else 'Unknown',
                'development_level': profile.development_level.value if profile else 'unknown',
                'currency': profile.currency if profile else 'USD',
                'currency_symbol': profile.currency_symbol if profile else '$'
            } if profile else None
        }
    
    def compare_countries(self, scores: Dict[str, float], 
                          country_codes: List[str]) -> Dict[str, Any]:
        """
        Compare ISI scores across multiple countries for same conditions
        """
        comparisons = []
        
        for code in country_codes:
            isi, weights = self.calculate_dynamic_isi(code, scores)
            profile = self.get_country_profile(code)
            
            comparisons.append({
                'country_code': code,
                'country_name': profile.name if profile else code,
                'isi_score': round(isi, 4),
                'weights': weights,
                'priority_level': self._get_priority_level(isi)
            })
        
        # Sort by ISI score
        comparisons.sort(key=lambda x: x['isi_score'], reverse=True)
        
        return {
            'input_scores': scores,
            'comparisons': comparisons,
            'highest_isi': comparisons[0] if comparisons else None,
            'lowest_isi': comparisons[-1] if comparisons else None,
            'isi_range': round(comparisons[0]['isi_score'] - comparisons[-1]['isi_score'], 4) if len(comparisons) > 1 else 0
        }
    
    def _get_priority_level(self, isi: float) -> str:
        """Convert ISI score to priority level"""
        if isi >= 0.7:
            return 'CRITICAL'
        elif isi >= 0.5:
            return 'HIGH'
        elif isi >= 0.3:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_regional_adjustment(self, country_code: str, 
                                 region_type: str) -> Dict[str, float]:
        """
        Get additional weight adjustments for specific region types
        """
        base_weights = self.get_weights(country_code)
        
        # Regional adjustment factors
        adjustments = {
            'urban_dense': {
                'congestion': 1.2,
                'safety': 1.1,
                'growth': 1.0,
                'quality': 0.9
            },
            'suburban': {
                'congestion': 0.9,
                'safety': 1.0,
                'growth': 1.2,
                'quality': 1.0
            },
            'rural': {
                'congestion': 0.7,
                'safety': 0.9,
                'growth': 0.8,
                'quality': 1.3
            },
            'highway_corridor': {
                'congestion': 1.1,
                'safety': 1.2,
                'growth': 0.9,
                'quality': 1.1
            },
            'port_area': {
                'congestion': 1.3,
                'safety': 1.0,
                'growth': 1.1,
                'quality': 1.0
            },
            'industrial_zone': {
                'congestion': 1.1,
                'safety': 1.1,
                'growth': 1.0,
                'quality': 1.0
            },
            'tourist_area': {
                'congestion': 1.0,
                'safety': 1.2,
                'growth': 1.1,
                'quality': 1.2
            }
        }
        
        region_adj = adjustments.get(region_type, {k: 1.0 for k in base_weights})
        
        # Apply adjustments
        adjusted_weights = {
            k: base_weights[k] * region_adj.get(k, 1.0)
            for k in base_weights
        }
        
        # Normalize to sum to 1.0
        total = sum(adjusted_weights.values())
        adjusted_weights = {k: v/total for k, v in adjusted_weights.items()}
        
        return adjusted_weights
    
    def get_supported_countries(self) -> List[Dict[str, str]]:
        """Return list of supported countries"""
        return [
            {
                'code': code,
                'name': self.COUNTRY_PROFILES[code].name if code in self.COUNTRY_PROFILES else code,
                'description': info.get('description', '')
            }
            for code, info in self.COUNTRY_WEIGHTS.items()
        ]
    
    def convert_to_local_currency(self, amount_usd: float, 
                                   country_code: str) -> Dict[str, Any]:
        """Convert USD amount to local currency"""
        profile = self.get_country_profile(country_code)
        
        if not profile:
            return {
                'amount_usd': amount_usd,
                'local_amount': amount_usd,
                'currency': 'USD',
                'symbol': '$'
            }
        
        local_amount = amount_usd * profile.exchange_rate_usd
        
        # Format based on currency
        if profile.exchange_rate_usd > 100:
            # Large exchange rate, use millions/lakhs/crores
            if profile.code == 'IN':
                if local_amount >= 10000000:
                    formatted = f"{profile.currency_symbol}{local_amount/10000000:.2f} Cr"
                elif local_amount >= 100000:
                    formatted = f"{profile.currency_symbol}{local_amount/100000:.2f} L"
                else:
                    formatted = f"{profile.currency_symbol}{local_amount:,.0f}"
            else:
                formatted = f"{profile.currency_symbol}{local_amount:,.0f}"
        else:
            formatted = f"{profile.currency_symbol}{local_amount:,.2f}"
        
        return {
            'amount_usd': amount_usd,
            'local_amount': local_amount,
            'formatted': formatted,
            'currency': profile.currency,
            'symbol': profile.currency_symbol,
            'exchange_rate': profile.exchange_rate_usd
        }


# Singleton instance
adaptive_scorer = AdaptiveScoringEngine()
