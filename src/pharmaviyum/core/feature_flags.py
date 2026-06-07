from functools import lru_cache
from src.pharmaviyum.config import settings


@lru_cache()
def is_feature_enabled(name: str) -> bool:
	# Simple feature flags via env variables: FEATURE_<NAME>=1
	key = f"FEATURE_{name.upper()}"
	val = getattr(settings, key, None)
	if val is None:
		return False
	return str(val).lower() in ("1", "true", "yes")
