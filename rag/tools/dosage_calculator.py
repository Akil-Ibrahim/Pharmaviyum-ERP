"""
Tool: Dosage Calculator.
Called by MortariumAgent via Mistral Nemo function calling.
"""
def calculate_dosage(weight_kg: float, mg_per_kg: float) -> float:
    """
    Calculates the recommended drug dosage based on patient weight.
    Mistral Nemo will extract weight_kg and mg_per_kg from the user query.
    """
    if weight_kg <= 0 or mg_per_kg <= 0:
        raise ValueError("Weight and dosage must be positive.")
    return weight_kg * mg_per_kg
