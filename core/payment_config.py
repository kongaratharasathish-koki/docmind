# core/payment_config.py
#
# Payment configuration for DocMind pricing tiers and provider integrations.
# All prices in USD for international customers.
#
# Provider Priority:
#   1. PayPal (primary)
#   2. Stripe (secondary/fallback)
#   3. Google Play Billing (future - mobile)
#   4. Apple In-App Purchase (future - mobile)
#   5. Wise (future - international transfers)
#   6. UPI (future - India)
#

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Dict, List


class PricingTier(str, Enum):
    STUDENT = "student"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# Primary and fallback providers
PROVIDERS_PRIMARY = ["paypal"]
PROVIDERS_FALLBACK = ["stripe"]
PROVIDERS_FUTURE = ["google_play", "apple_iap", "wise", "upi"]


PRICING_USD: Dict[str, Dict[str, Any]] = {
    PricingTier.STUDENT: {
        "id": "price_student_monthly",
        "name": "Student",
        "price_usd": 4.99,
        "description": "Up to 5 libraries, 50 documents total",
        "features": ["5 libraries", "50 documents", "Basic support"],
        "provider_ids": {
            "paypal": "P-PLACEHOLDER-STUDENT",
            "stripe": "price_placeholder_student",
        },
    },
    PricingTier.BASIC: {
        "id": "price_basic_monthly",
        "name": "Research Assistant",
        "price_usd": 9.99,
        "description": "Up to 20 libraries, 500 documents total",
        "features": ["20 libraries", "500 documents", "Priority support"],
        "provider_ids": {
            "paypal": "P-PLACEHOLDER-RESEARCH",
            "stripe": "price_placeholder_research",
        },
    },
    PricingTier.PRO: {
        "id": "price_pro_monthly",
        "name": "Professional",
        "price_usd": 19.99,
        "description": "Unlimited libraries and documents",
        "features": ["Unlimited libraries", "Unlimited documents", "Priority support"],
        "provider_ids": {
            "paypal": "P-PLACEHOLDER-PRO",
            "stripe": "price_placeholder_pro",
        },
    },
    PricingTier.ENTERPRISE: {
        "id": "price_enterprise_monthly",
        "name": "Business",
        "price_usd": 49.99,
        "description": "Multi-user, API access, dedicated support",
        "features": ["Multi-user", "API access", "Dedicated support"],
        "provider_ids": {
            "paypal": "P-PLACEHOLDER-BUSINESS",
            "stripe": "price_placeholder_business",
        },
    },
}


def get_tier_config(tier: PricingTier) -> Optional[Dict[str, Any]]:
    return PRICING_USD.get(tier)


def get_all_tiers() -> List[Dict[str, Any]]:
    return [
        {"tier": tier.value, **config}
        for tier, config in PRICING_USD.items()
    ]