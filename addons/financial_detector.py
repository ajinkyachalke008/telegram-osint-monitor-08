"""Dedicated Financial-Ad Detector Module (Workstream D / R3).

Detects and categorizes financial trade signals:
- Intent: buy, sell, rent, recruit
- Instruments: savings, current, corporate, ATM/debit card, credit card, net-banking kit, SIM, UPI, crypto
- Signals: commission, price, KYC-less/pre-KYC, fastag, high-limit transaction capacity
- Mule Recruitment Pattern Flag: identifies recruitment of individuals for account renting/laundering
- Exact Text Span Offsets: captures byte/character offsets of evidentiary phrases for court admissibility
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple

from core.normalizer import normalize_text


@dataclass
class EvidenceSpan:
    text: str
    start: int
    end: int
    signal_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "signal_type": self.signal_type
        }


@dataclass
class FinancialDetectionResult:
    is_financial_ad: bool
    intent: str  # "recruit" | "rent" | "sell" | "buy" | "none"
    instruments: List[str]
    signals: Dict[str, Any]
    mule_recruitment_pattern: bool
    risk_assessment: str  # "High" | "Medium" | "Low" | "Clean"
    evidence_spans: List[EvidenceSpan]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_financial_ad": self.is_financial_ad,
            "intent": self.intent,
            "instruments": self.instruments,
            "signals": self.signals,
            "mule_recruitment_pattern": self.mule_recruitment_pattern,
            "risk_assessment": self.risk_assessment,
            "evidence_spans": [s.to_dict() for s in self.evidence_spans],
            "summary": self.summary
        }


class FinancialAdDetector:
    """Specialized detector for banking mule recruitment, illicit account leasing, and card trade."""

    INTENT_PATTERNS = [
        ("recruit", re.compile(r"(?i)\b(?:recruit(?:ing|ment)?|earn daily|earn commission|commission base[d]?|commission per (?:day|transaction|load)|rent your (?:account|khata)|give your (?:account|khata)|idle (?:account|khata)|daily income)\b")),
        ("rent", re.compile(r"(?i)\b(?:for rent|on rent|rent basis|rented account|bhade pe|rent chahiye|chahiye rent|account on lease)\b")),
        ("sell", re.compile(r"(?i)\b(?:selling|for sale|fresh stock|ready for sale|vikne|in stock|ready to swipe|direct delivery|available for sale)\b")),
        ("buy", re.compile(r"(?i)\b(?:buying|need|looking for|require|chahiye|urgent requirement|want to buy|want account)\b"))
    ]

    INSTRUMENT_PATTERNS = [
        ("corporate_account", re.compile(r"(?i)\b(?:corporate (?:current|account|khata|netbanking)|maker[- ]checker)\b")),
        ("current_account", re.compile(r"(?i)\b(?:current account|current khata|vyapari khate|current)\b")),
        ("savings_account", re.compile(r"(?i)\b(?:savings? account|savings? khata|bachat khata)\b")),
        ("bank_account", re.compile(r"(?i)\b(?:bank accounts?|bank khata|idle accounts?|khata|khate)\b")),
        ("net_banking_kit", re.compile(r"(?i)\b(?:net[- ]?banking kit|digital banking kit|user id password|login credentials|full kit|4 in 1 kit|5 in 1 kit|token device)\b")),
        ("atm_card", re.compile(r"(?i)\b(?:atm (?:debit )?cards?|debit cards?|atm kits?|pos cards?|card swipe|plastic cards?|carding kit)\b")),
        ("credit_card", re.compile(r"(?i)\b(?:credit cards?|cloned (?:credit|debit) cards?)\b")),
        ("sim_card", re.compile(r"(?i)\b(?:sim cards?|pre-?activated sims?|otps? sims?|chalu sim|fake kyc sims?)\b")),
        ("crypto_wallet", re.compile(r"(?i)\b(?:usdt|trc20|erc20|crypto deposit|p2p merchant|crypto transactions?)\b")),
        ("upi", re.compile(r"(?i)\b(?:upi|gpay|phonepe|paytm)\b"))
    ]

    SIGNAL_PATTERNS = {
        "commission": re.compile(r"(?i)\b(?:(?:high|heavy|daily|good|\d+%\s*)\s*)?commission(?: (?:milenga|milega|dunga|basis|per txn|paid))?\b"),
        "kyc_less": re.compile(r"(?i)\b(?:no kyc|pre[- ]?kyc|clean kyc|bina (?:aadhar|kyc|pan)|without (?:kyc|id|documents|papers)|fake kyc|zero chargeback)\b"),
        "high_limit": re.compile(r"(?i)\b(?:high limit|heavy limit|daily limit|withdrawal limit|\d+[lL]\s*limit|\d+\s*(?:lakh|cr)|no hold)\b"),
        "fastag": re.compile(r"(?i)\b(?:fastag|fastag account)\b"),
        "price": re.compile(r"(?i)(?:₹\s*[\d,]+|rs\.?\s*[\d,]+|inr\s*[\d,]+|[\d,]+\s*(?:rs|inr|rupees))")
    }

    BENIGN_EXCLUSIONS = [
        re.compile(r"(?i)\bnever share\b"),
        re.compile(r"(?i)\bbeware of (?:fraud|fraudsters)\b"),
        re.compile(r"(?i)\bofficial notice\b"),
        re.compile(r"(?i)\bpublic awareness\b"),
        re.compile(r"(?i)\bcybercrime helpline 1930\b"),
    ]

    def detect(self, text: str) -> FinancialDetectionResult:
        if not text or not text.strip():
            return FinancialDetectionResult(
                is_financial_ad=False,
                intent="none",
                instruments=[],
                signals={},
                mule_recruitment_pattern=False,
                risk_assessment="Clean",
                evidence_spans=[],
                summary="Empty text."
            )

        # Check for official security advisories first
        for pat in self.BENIGN_EXCLUSIONS:
            if pat.search(text):
                return FinancialDetectionResult(
                    is_financial_ad=False,
                    intent="none",
                    instruments=[],
                    signals={"security_advisory": True},
                    mule_recruitment_pattern=False,
                    risk_assessment="Clean",
                    evidence_spans=[],
                    summary="Legitimate security warning or public advisory."
                )

        evidence_spans: List[EvidenceSpan] = []

        # 1. Detect Intent
        detected_intent = "none"
        for intent_name, pat in self.INTENT_PATTERNS:
            for m in pat.finditer(text):
                if detected_intent == "none":
                    detected_intent = intent_name
                evidence_spans.append(EvidenceSpan(
                    text=m.group(0),
                    start=m.start(),
                    end=m.end(),
                    signal_type=f"intent:{intent_name}"
                ))

        # 2. Detect Instruments
        detected_instruments: List[str] = []
        for inst_name, pat in self.INSTRUMENT_PATTERNS:
            for m in pat.finditer(text):
                if inst_name not in detected_instruments:
                    detected_instruments.append(inst_name)
                evidence_spans.append(EvidenceSpan(
                    text=m.group(0),
                    start=m.start(),
                    end=m.end(),
                    signal_type=f"instrument:{inst_name}"
                ))

        # 3. Detect Signals
        signals: Dict[str, Any] = {}
        for sig_name, pat in self.SIGNAL_PATTERNS.items():
            matches = list(pat.finditer(text))
            if matches:
                signals[sig_name] = [m.group(0) for m in matches]
                for m in matches:
                    evidence_spans.append(EvidenceSpan(
                        text=m.group(0),
                        start=m.start(),
                        end=m.end(),
                        signal_type=f"signal:{sig_name}"
                    ))

        # 4. Mule Recruitment Pattern
        # True if recruiting/renting + financial instrument + (commission or daily income or KYC-less)
        has_recruit_intent = detected_intent in ("recruit", "rent")
        has_financial_instrument = any(inst in detected_instruments for inst in [
            "corporate_account", "current_account", "savings_account", "bank_account",
            "net_banking_kit", "atm_card", "credit_card", "sim_card"
        ])
        has_incentive = "commission" in signals or "kyc_less" in signals or "high_limit" in signals or detected_intent == "recruit"

        mule_recruitment = has_recruit_intent and has_financial_instrument and has_incentive

        # 5. Risk Assessment & Summary
        is_financial_ad = bool(has_financial_instrument and (detected_intent != "none" or signals))

        if mule_recruitment:
            risk_assessment = "High"
            summary = (
                f"Mule Recruitment Detected: Soliciting {', '.join(detected_instruments)} "
                f"with intent '{detected_intent}' and incentive signals {list(signals.keys())}."
            )
        elif is_financial_ad and detected_intent in ("sell", "rent"):
            risk_assessment = "High"
            summary = (
                f"Illicit Financial Instrument Trade: Offering {', '.join(detected_instruments)} "
                f"for {detected_intent}."
            )
        elif is_financial_ad:
            risk_assessment = "Medium"
            summary = (
                f"Suspicious Financial Ad: Inquiring about {', '.join(detected_instruments)} "
                f"(intent: {detected_intent})."
            )
        elif detected_instruments:
            risk_assessment = "Low"
            summary = f"Mention of financial terms {', '.join(detected_instruments)} without clear illicit trade intent."
        else:
            risk_assessment = "Clean"
            summary = "No financial instruments or mule trade patterns detected."

        return FinancialDetectionResult(
            is_financial_ad=is_financial_ad,
            intent=detected_intent,
            instruments=detected_instruments,
            signals=signals,
            mule_recruitment_pattern=mule_recruitment,
            risk_assessment=risk_assessment,
            evidence_spans=evidence_spans,
            summary=summary
        )
