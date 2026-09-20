"""
Medical Guardrails for Agent Harness.

Best practice 2026:
- Input sanitization (PII removal, prompt injection detection)
- Output validation (hallucinated dosages, dangerous advice blocking)
- Regulatory compliance checks (country-specific)
- Async validation for non-blocking execution
- Structured Pydantic models for guardrail results
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from src.pharmaviyum.core.logging import logger


class GuardrailResult(BaseModel):
    """Result of guardrail validation."""

    is_safe: bool = True
    sanitized_input: str | None = None
    validated_output: str | None = None
    warnings: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None


class MedicalGuardrails:
    """
    Production-ready medical safety guardrails.

    Ensures AI responses are:
    1. Safe (no dangerous medical advice)
    2. Accurate (no hallucinated dosages)
    3. Compliant (adheres to regional regulations)
    4. Professional (includes mandatory disclaimers)
    """

    def __init__(self, country_code: str = "VN"):
        self.country_code = country_code.upper()

        # Dangerous phrases that should trigger immediate blocking
        self.dangerous_phrases = [
            r"stop taking immediately",
            r"double the dose",
            r"mix with alcohol",
            r"ignore side effects",
            r"fatal",
            r"overdose is safe",
            r"no need to consult",
        ]

        # Regex for unverified dosage patterns (e.g., "take 500mg 4 times a day")
        # We flag these if they don't match retrieved sources
        self.dosage_pattern = re.compile(
            r"\b\d+\s*(mg|ml|g|tablets|capsules|drops)\s*(daily|per day|times a day|twice|thrice)\b",
            re.IGNORECASE,
        )

        # PII patterns to redact from user input before sending to LLM
        self.pii_patterns = {
            "phone": re.compile(r"\+?\d[\d -]{8,12}\d"),
            "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
            "id_number": re.compile(r"\b\d{9,12}\b"),  # National ID patterns
        }

    async def pre_process(self, user_input: str) -> GuardrailResult:
        """
        Sanitize input before sending to LLM.

        Actions:
        1. Remove PII (phone, email, ID numbers)
        2. Detect prompt injection attempts
        3. Truncate excessively long inputs
        """
        warnings = []
        sanitized = user_input

        # 1. Redact PII
        for pii_type, pattern in self.pii_patterns.items():
            if pattern.search(sanitized):
                sanitized = pattern.sub(f"[REDACTED_{pii_type.upper()}]", sanitized)
                warnings.append(f"pii_{pii_type}_redacted")

        # 2. Prompt injection detection (basic heuristics)
        injection_keywords = [
            "ignore previous instructions",
            "system prompt",
            "dan mode",
            "jailbreak",
        ]
        if any(kw in sanitized.lower() for kw in injection_keywords):
            # Never log user-controlled prompt content; it may contain PII.
            logger.warning("Potential prompt injection detected")
            return GuardrailResult(
                is_safe=False,
                blocked_reason="Potential prompt injection detected",
                warnings=["prompt_injection_attempt"],
            )

        # 3. Length limit (prevent context window exhaustion)
        if len(sanitized) > 4000:
            sanitized = sanitized[:4000] + "... [Input truncated due to length]"
            warnings.append("input_truncated")

        return GuardrailResult(
            is_safe=True,
            sanitized_input=sanitized,
            warnings=warnings,
        )

    async def post_process(
        self,
        answer: str,
        question: str,
        sources: list[Any] | None = None,
    ) -> GuardrailResult:
        """
        Validate and sanitize LLM output before returning to user.

        Actions:
        1. Check for dangerous recommendations
        2. Flag unverified dosages
        3. Ensure regulatory compliance
        4. Append mandatory medical disclaimer
        """
        warnings = []
        validated_answer = answer
        is_safe = True
        blocked_reason = None

        # 1. Dangerous recommendation check
        for phrase in self.dangerous_phrases:
            if re.search(phrase, validated_answer, re.IGNORECASE):
                is_safe = False
                blocked_reason = f"Dangerous phrase detected: '{phrase}'"
                warnings.append("dangerous_phrase_detected")
                break

        if not is_safe:
            return GuardrailResult(
                is_safe=False,
                blocked_reason=blocked_reason,
                warnings=warnings,
            )

        # 2. Unverified dosage check
        if self._contains_unverified_dosage(validated_answer, sources):
            validated_answer = self._add_dosage_disclaimer(validated_answer)
            warnings.append("dosage_unverified_disclaimer_added")

        # 3. Regulatory compliance check (country-specific)
        compliance_warning = self._check_regulatory_compliance(validated_answer)
        if compliance_warning:
            warnings.append(compliance_warning)

        # 4. Mandatory medical disclaimer
        if not self._has_disclaimer(validated_answer):
            disclaimer = "\n\n⚠️ **Medical Disclaimer**: This information is for educational purposes only and does not replace professional medical advice. Always consult a licensed pharmacist or physician before starting, stopping, or changing any medication."
            validated_answer += disclaimer
            warnings.append("disclaimer_appended")

        return GuardrailResult(
            is_safe=True,
            validated_output=validated_answer,
            warnings=warnings,
        )

    def _contains_unverified_dosage(self, text: str, sources: list[Any] | None) -> bool:
        """
        Detect specific dosage recommendations that are not backed by retrieved sources.
        """
        if not sources:
            # If no sources provided, be conservative and flag any dosage
            return bool(self.dosage_pattern.search(text))

        # In a full implementation, we would cross-reference the dosage
        # mentioned in the text with the dosages in the retrieved sources.
        # For now, we flag if dosage is mentioned but sources are generic.
        has_dosage = bool(self.dosage_pattern.search(text))
        has_source_dosage = any(
            "dosage" in str(source).lower() or "mg" in str(source).lower()
            for source in sources
        )

        return has_dosage and not has_source_dosage

    def _add_dosage_disclaimer(self, text: str) -> str:
        """Append a specific warning about dosage verification."""
        disclaimer = "\n\n⚠️ **Dosage Warning**: The dosages mentioned are for informational purposes only. Actual dosages must be verified by a licensed pharmacist based on patient-specific factors (age, weight, renal function, drug interactions)."
        return text + disclaimer

    def _check_regulatory_compliance(self, text: str) -> str | None:
        """
        Check for country-specific regulatory violations.
        """
        text_lower = text.lower()

        if self.country_code in ["VN", "ID", "MY"]:
            # Southeast Asia: Strict rules on antibiotics and psychotropics
            if "antibiotic" in text_lower and "prescription" not in text_lower:
                return "antibiotic_prescription_warning"
            if (
                any(drug in text_lower for drug in ["diazepam", "tramadol", "codeine"])
                and "controlled" not in text_lower
            ):
                return "controlled_substance_warning"

        return None

    def _has_disclaimer(self, text: str) -> bool:
        """Check if the text already contains a medical disclaimer."""
        disclaimer_keywords = [
            "consult a licensed pharmacist",
            "consult a physician",
            "medical disclaimer",
            "educational purposes only",
        ]
        return any(kw in text.lower() for kw in disclaimer_keywords)
