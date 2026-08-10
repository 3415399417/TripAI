"""TripAI AI service — split into focused submodules for maintainability.

All public symbols are re-exported so existing imports continue to work:
    from app.services import ai_service
    from app.services.ai_service import generate_itinerary, LLMError, ...
"""

from app.services.ai_service.prompt import (
    SYSTEM_PROMPT,
    LLMError,
    build_user_prompt,
    last_prompt,
)
from app.services.ai_service.client import (
    _call_llm,
    _parse_json,
    _supports_thinking_param,
    _COST_RANGES,
    _calibrate_cost,
)
from app.services.ai_service.budget import (
    compute_budget_plan,
    _LEVEL_RATIOS,
    _LEVEL_TAGS,
    _city_cost_factor,
)
from app.services.ai_service.mock import (
    _CITY_COORDS,
    _MOCK_PLACES,
    _mock_itinerary,
    _mock_reoptimize,
)
from app.services.ai_service.saver import (
    save_itinerary,
    save_reoptimized,
    _dist_sq,
    _order_by_nearest,
)
from app.services.ai_service.optimizer import (
    reoptimize_itinerary,
    _group_schedules,
)
from app.services.ai_service.generator import generate_itinerary

__all__ = [
    # Generator (main entry)
    "generate_itinerary",
    # Prompt
    "SYSTEM_PROMPT",
    "LLMError",
    "build_user_prompt",
    "last_prompt",
    # Client
    "_call_llm",
    "_parse_json",
    "_supports_thinking_param",
    "_COST_RANGES",
    "_calibrate_cost",
    # Budget
    "compute_budget_plan",
    "_LEVEL_RATIOS",
    "_LEVEL_TAGS",
    "_city_cost_factor",
    # Mock
    "_CITY_COORDS",
    "_MOCK_PLACES",
    "_mock_itinerary",
    "_mock_reoptimize",
    # Saver
    "save_itinerary",
    "save_reoptimized",
    "_dist_sq",
    "_order_by_nearest",
    # Optimizer
    "save_reoptimized",
    "reoptimize_itinerary",
    "_group_schedules",
]
