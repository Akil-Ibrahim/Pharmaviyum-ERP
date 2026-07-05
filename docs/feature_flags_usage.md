# Feature Flags Usage Guide

## Overview

Feature flags allow you to:
- Gradually roll out new features
- Run A/B tests
- Target specific user segments
- Quickly disable features without deployment

## Feature Flag Types

### 1. Boolean (Simple On/Off)
```python
# Create flag
POST /api/v1/feature-flags/
{
    "key": "new_dashboard",
    "name": "New Dashboard",
    "flag_type": "boolean",
    "enabled": true
}

# Check in code
if await is_feature_enabled("new_dashboard"):
    # Show new dashboard
```

### 2. Percentage Rollout
```python
# Create flag
POST /api/v1/feature-flags/
{
    "key": "ai_recommendations",
    "name": "AI Recommendations",
    "flag_type": "percentage",
    "enabled": true,
    "percentage": 25  # 25% of users
}

# Check in code
if await is_feature_enabled("ai_recommendations", user_id="123"):
    # Show AI recommendations to 25% of users
```

### 3. Segment Targeting
```python
# Create flag
POST /api/v1/feature-flags/
{
    "key": "premium_features",
    "name": "Premium Features",
    "flag_type": "segment",
    "enabled": true,
    "segments": ["gold", "platinum"]
}

# Check in code
if await is_feature_enabled("premium_features", user_segment="gold"):
    # Show premium features to gold/platinum users
```

### 4. Multivariate (A/B Testing)
```python
# Create flag
POST /api/v1/feature-flags/
{
    "key": "checkout_flow",
    "name": "Checkout Flow A/B Test",
    "flag_type": "multivariate",
    "enabled": true,
    "variants": {
        "control": {"button_color": "blue", "layout": "standard"},
        "variant_a": {"button_color": "green", "layout": "compact"},
        "variant_b": {"button_color": "orange", "layout": "expanded"}
    }
}

# Check in code
variant = await get_feature_variant("checkout_flow", user_id="123")
if variant["layout"] == "compact":
    # Show compact layout
```

## Admin API

### List all flags
```bash
GET /api/v1/feature-flags/
```

### Create flag
```bash
POST /api/v1/feature-flags/
{
    "key": "new_feature",
    "name": "New Feature",
    "flag_type": "boolean",
    "enabled": false
}
```

### Update flag
```bash
PUT /api/v1/feature-flags/new_feature
{
    "enabled": true,
    "percentage": 50
}
```

### Enable/Disable
```bash
POST /api/v1/feature-flags/new_feature/enable
POST /api/v1/feature-flags/new_feature/disable
```

### Set percentage
```bash
POST /api/v1/feature-flags/new_feature/set-percentage?percentage=75
```

### Get statistics
```bash
GET /api/v1/feature-flags/new_feature/stats
```

### Check flag
```bash
POST /api/v1/feature-flags/check
{
    "key": "new_feature",
    "user_id": "123",
    "user_segment": "gold"
}
```

## Best Practices

1. **Use descriptive keys**: `ai_recommendations` not `flag1`
2. **Start small**: Begin with 5-10% rollout
3. **Monitor metrics**: Watch error rates and performance
4. **Document flags**: Add clear descriptions
5. **Clean up**: Remove flags after full rollout
6. **Use segments**: Target specific user groups
7. **A/B test properly**: Use multivariate for experiments

## Examples in Pharmaviyum CRM

### AI Recommendations Rollout
```python
# Gradually enable AI for pharmacies
if await is_feature_enabled("ai_recommendations", user_id=pharmacy_id):
    recommendations = await mortarium_ai.get_recommendations(patient_id)
```

### New UI A/B Test
```python
# Test new dashboard layout
variant = await get_feature_variant("dashboard_ui", user_id=user_id)
if variant == "new":
    return render_new_dashboard()
else:
    return render_old_dashboard()
```

### Premium Features
```python
# Only for premium pharmacies
if await is_feature_enabled("premium_analytics", user_segment="enterprise"):
    return advanced_analytics()
```

### Halal Filter (Regional)
```python
# Enable for Muslim-majority regions
if await is_feature_enabled("halal_filter", user_segment="malaysia"):
    products = filter_halal(products)
```
