"""
Feature flag admin endpoints
Best practice 2026: Full CRUD + statistics + testing
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from src.pharmaviyum.core.feature_flags import (
    feature_flag_service,
    FeatureFlag,
    FlagType,
)
from src.pharmaviyum.schemas.feature_flag import (
    FeatureFlagCreate,
    FeatureFlagUpdate,
    FeatureFlagResponse,
    FeatureFlagListResponse,
    FeatureFlagStatsResponse,
    FeatureFlagCheckRequest,
    FeatureFlagCheckResponse,
)

router = APIRouter(prefix="/feature-flags", tags=["feature-flags"])


@router.post("/", response_model=FeatureFlagResponse, status_code=status.HTTP_201_CREATED)
async def create_feature_flag(flag_data: FeatureFlagCreate):
    """
    Create a new feature flag
    
    Args:
        flag_data: Feature flag creation data
        
    Returns:
        Created feature flag
        
    Raises:
        HTTPException 400: If flag already exists
    """
    try:
        flag = FeatureFlag(
            key=flag_data.key,
            name=flag_data.name,
            description=flag_data.description or "",
            flag_type=flag_data.flag_type,
            enabled=flag_data.enabled,
            percentage=flag_data.percentage,
            segments=flag_data.segments,
            variants=flag_data.variants,
            default_value=flag_data.default_value,
        )
        
        created = await feature_flag_service.create_flag(flag)
        return FeatureFlagResponse(**created.to_dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/", response_model=FeatureFlagListResponse)
async def list_feature_flags():
    """
    List all feature flags
    
    Returns:
        List of feature flags
    """
    flags = await feature_flag_service.list_flags()
    
    return FeatureFlagListResponse(
        flags=[FeatureFlagResponse(**flag.to_dict()) for flag in flags],
        total=len(flags),
    )


@router.get("/{key}", response_model=FeatureFlagResponse)
async def get_feature_flag(key: str):
    """
    Get feature flag by key
    
    Args:
        key: Feature flag key
        
    Returns:
        Feature flag
        
    Raises:
        HTTPException 404: If flag not found
    """
    flag = await feature_flag_service.get_flag(key)
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' not found",
        )
    
    return FeatureFlagResponse(**flag.to_dict())


@router.put("/{key}", response_model=FeatureFlagResponse)
async def update_feature_flag(key: str, flag_data: FeatureFlagUpdate):
    """
    Update feature flag
    
    Args:
        key: Feature flag key
        flag_data: Update data
        
    Returns:
        Updated feature flag
        
    Raises:
        HTTPException 404: If flag not found
    """
    try:
        updates = flag_data.model_dump(exclude_unset=True)
        
        # Convert enum values
        if "flag_type" in updates and updates["flag_type"]:
            updates["flag_type"] = FlagType(updates["flag_type"])
        
        updated = await feature_flag_service.update_flag(key, updates)
        return FeatureFlagResponse(**updated.to_dict())
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_flag(key: str):
    """
    Delete feature flag
    
    Args:
        key: Feature flag key
        
    Raises:
        HTTPException 404: If flag not found
    """
    deleted = await feature_flag_service.delete_flag(key)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' not found",
        )


@router.get("/{key}/stats", response_model=FeatureFlagStatsResponse)
async def get_feature_flag_stats(key: str):
    """
    Get feature flag statistics
    
    Args:
        key: Feature flag key
        
    Returns:
        Feature flag statistics
    """
    stats = await feature_flag_service.get_flag_stats(key)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag '{key}' not found",
        )
    
    return FeatureFlagStatsResponse(**stats)


@router.post("/check", response_model=FeatureFlagCheckResponse)
async def check_feature_flag(request: FeatureFlagCheckRequest):
    """
    Check if feature flag is enabled
    
    Args:
        request: Check request with user context
        
    Returns:
        Check result with enabled status and variant
    """
    enabled = await feature_flag_service.is_enabled(
        key=request.key,
        user_id=request.user_id,
        user_segment=request.user_segment,
    )
    
    # Record check for statistics
    await feature_flag_service.record_check(request.key, enabled)
    
    # Get variant if multivariate
    variant = None
    if enabled and request.user_id:
        flag = await feature_flag_service.get_flag(request.key)
        if flag and flag.flag_type == FlagType.MULTIVARIATE:
            variant = await feature_flag_service.get_variant(request.key, request.user_id)
    
    return FeatureFlagCheckResponse(
        key=request.key,
        enabled=enabled,
        variant=variant,
    )


@router.post("/{key}/enable")
async def enable_feature_flag(key: str):
    """
    Enable feature flag
    
    Args:
        key: Feature flag key
    """
    try:
        await feature_flag_service.update_flag(key, {"enabled": True})
        return {"status": "enabled", "key": key}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{key}/disable")
async def disable_feature_flag(key: str):
    """
    Disable feature flag
    
    Args:
        key: Feature flag key
    """
    try:
        await feature_flag_service.update_flag(key, {"enabled": False})
        return {"status": "disabled", "key": key}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/{key}/set-percentage")
async def set_percentage_rollout(
    key: str,
    percentage: int = Query(..., ge=0, le=100),
):
    """
    Set percentage rollout for feature flag
    
    Args:
        key: Feature flag key
        percentage: Percentage (0-100)
    """
    try:
        await feature_flag_service.update_flag(key, {"percentage": percentage})
        return {"status": "updated", "key": key, "percentage": percentage}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post("/cache/invalidate")
async def invalidate_cache(key: Optional[str] = None):
    """
    Invalidate feature flag cache
    
    Args:
        key: Specific flag key (optional, clears all if not provided)
    """
    feature_flag_service.invalidate_cache(key)
    return {"status": "cache_invalidated", "key": key}
