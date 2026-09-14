"""
MCP Prompts — Reusable prompt templates for the AI agent.

Best practice 2026:
- Parameterized prompt templates
- Versioned prompts for A/B testing
- Domain-specific structured prompts
"""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field
from src.pharmaviyum.core.logging import logger


class PromptArgument(BaseModel):
    name: str
    description: str
    required: bool = True


class PromptTemplate(BaseModel):
    name: str
    description: str
    arguments: list[PromptArgument]
    template: str


class PromptRegistry:
    """Registry for MCP prompt templates."""
    
    def __init__(self):
        self._prompts: dict[str, PromptTemplate] = {}
    
    def prompt(
        self,
        name: str,
        description: str,
        arguments: list[PromptArgument],
    ):
        """Decorator to register a prompt template."""
        def decorator(func):
            # The function itself becomes the template generator
            self._prompts[name] = PromptTemplate(
                name=name,
                description=description,
                arguments=arguments,
                template="",  # Will be filled by func
            )
            # Store the generator function
            self._prompts[name]._generator = func
            logger.info(f"Registered MCP prompt: {name}")
            return func
        return decorator
    
    def list_prompts(self) -> list[PromptTemplate]:
        # Return copies without the internal _generator
        return [
            PromptTemplate(
                name=p.name,
                description=p.description,
                arguments=p.arguments,
                template="Template available via get_prompt",
            )
            for p in self._prompts.values()
        ]
    
    async def get_prompt(self, name: str, arguments: dict[str, Any]) -> str:
        """Generate prompt from template with provided arguments."""
        if name not in self._prompts:
            raise ValueError(f"Prompt not found: {name}")
        
        prompt_obj = self._prompts[name]
        generator = getattr(prompt_obj, "_generator", None)
        if not generator:
            raise ValueError(f"Prompt {name} has no generator function")
        
        return await generator(**arguments)


prompt_registry = PromptRegistry()


# ============================================================================
# PROMPT DEFINITIONS
# ============================================================================

@prompt_registry.prompt(
    name="halal_consultation",
    description="Generate a structured halal compliance consultation response",
    arguments=[
        PromptArgument(name="drug_name", description="Name of the medication", required=True),
        PromptArgument(name="country", description="Patient's country (e.g., ID, SA, IQ)", required=True),
        PromptArgument(name="fiqh_school", description="Specific fiqh school if known (e.g., Ja'fari_Sistani)", required=False),
    ],
)
async def generate_halal_consultation(drug_name: str, country: str, fiqh_school: str = "General") -> str:
    return f"""You are a pharmaceutical AI assistant specializing in Halal compliance.

Patient Inquiry: Is "{drug_name}" halal?
Country Context: {country}
Fiqh School Preference: {fiqh_school}

Please provide a structured response including:
1. Halal Status (Halal, Haram, Mushbooh, or Darurah Exempt)
2. Specific ingredient concerns (e.g., gelatin source, ethanol content, E-numbers)
3. Relevant certification bodies (e.g., MUI, JAKIM, SFDA, IFDA)
4. Halal-certified alternatives if applicable
5. A brief, compassionate note acknowledging the patient's religious preferences.

Respond in the patient's local language based on the country context."""


@prompt_registry.prompt(
    name="drug_interaction_check",
    description="Generate a structured drug interaction warning for a pharmacist",
    arguments=[
        PromptArgument(name="drug_list", description="Comma-separated list of drugs", required=True),
        PromptArgument(name="patient_age", description="Patient age", required=False),
        PromptArgument(name="patient_conditions", description="Comma-separated list of conditions", required=False),
    ],
)
async def generate_interaction_check(drug_list: str, patient_age: str = "Unknown", patient_conditions: str = "None") -> str:
    return f"""URGENT PHARMACIST ALERT: Drug Interaction Check

Medications: {drug_list}
Patient Age: {patient_age}
Existing Conditions: {patient_conditions}

Analyze the provided medications for:
1. Critical or High-severity pharmacokinetic/pharmacodynamic interactions.
2. Contraindications based on the patient's existing conditions.
3. Required monitoring parameters (e.g., INR, renal function).
4. Actionable management recommendations (e.g., dose adjustment, alternative therapy).

Format the output clearly with severity badges (🔴 CRITICAL, 🟡 HIGH, 🟢 MODERATE)."""
