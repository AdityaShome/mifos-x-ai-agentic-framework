from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.agent.prompts import EXPLANATION_PROMPT

try:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_ollama import ChatOllama
except Exception:  # pragma: no cover - fallback when optional deps are unavailable
    ChatOllama = None
    ChatPromptTemplate = None
    StrOutputParser = None


def _fallback_explanation(evidence: dict[str, Any], risk_tier: str, policy_decision: str) -> str:
    factors = []
    for key in ("days_past_due", "overdue_amount", "missed_installments", "repayment_history_score", "recent_activity_score"):
        if key in evidence:
            factors.append(f"{key.replace('_', ' ')}={evidence[key]}")

    factor_text = ", ".join(factors) if factors else "no structured factors available"
    return (
        f"Risk tier {risk_tier}. Main evidence: {factor_text}. "
        f"Recommended safe next step: {policy_decision}."
    )


@dataclass(slots=True)
class ExplanationAgent:
    model_name: str
    base_url: str

    def generate(self, evidence: dict[str, Any], risk_tier: str, policy_decision: str, autonomy_level: int) -> str:
        if ChatOllama is None or ChatPromptTemplate is None or StrOutputParser is None:
            return _fallback_explanation(evidence, risk_tier, policy_decision)

        try:
            prompt = ChatPromptTemplate.from_template(EXPLANATION_PROMPT)
            llm = ChatOllama(model=self.model_name, base_url=self.base_url, temperature=0)
            chain = prompt | llm | StrOutputParser()
            return chain.invoke(
                {
                    "evidence": evidence,
                    "risk_tier": risk_tier,
                    "policy_decision": policy_decision,
                    "autonomy_level": autonomy_level,
                }
            ).strip()
        except Exception:
            return _fallback_explanation(evidence, risk_tier, policy_decision)


def generate_explanation(
    evidence: dict[str, Any],
    risk_tier: str,
    policy_decision: str,
    autonomy_level: int,
    model_name: str,
    base_url: str,
) -> str:
    agent = ExplanationAgent(model_name=model_name, base_url=base_url)
    return agent.generate(evidence=evidence, risk_tier=risk_tier, policy_decision=policy_decision, autonomy_level=autonomy_level)
