# Business Write-Up: Multilingual Loan Collections & Recovery Agent

## 1. Problem

Banks and NBFCs in India run large outbound calling operations for EMI reminders, early bucket collections, payment follow-ups, and broken promise-to-pay cases. The current model depends heavily on human agents, manual call disposition, inconsistent language coverage, and repeated follow-ups that increase cost and borrower frustration.

This PoC focuses on early-stage overdue customers: 1–30 days past due. These calls are high-volume, repetitive, language-sensitive, and operationally expensive. A human agent is still required for disputes, hardship, fraud claims, legal issues, and complex restructuring. The opportunity is to automate Tier-1 collections while escalating risky cases correctly.

Assumption for ROI model:

- 10 lakh monthly early-bucket outbound calls
- Human call cost: INR 45 per connected call
- AI call cost: INR 6 per completed interaction
- 60% automation of Tier-1 calls
- 15% improvement in promise-to-pay capture due to local language coverage and instant follow-up

## 2. Why AI

Collections is not just reminder automation. Borrowers respond with objections: salary delay, medical emergency, dispute, fraud claim, already paid, callback request, or partial-payment request.

A voice AI agent is better than static IVR because it can:

- understand natural speech in Indian languages and code-mixed Hinglish
- personalize the reminder based on overdue amount, product, and risk band
- handle common objections without human wait time
- capture structured outcomes automatically
- suppress repeat calls when a promise-to-pay is captured
- escalate sensitive cases to human teams

The end user is often mobile-first, voice-first, and may not be comfortable navigating an English app or web portal. Voice in the borrower’s preferred language lowers friction.

## 3. Why Sarvam

Sarvam is a strong fit because the problem is India-specific. Generic voice stacks usually perform poorly on code-mixed speech, Indian accents, and local language collections vocabulary.

Sarvam advantage:

- Saaras v3 for Indian-language and code-mixed speech-to-text
- Sarvam-105B for multilingual reasoning, objection handling, and agentic decisions
- Bulbul v3 for natural Indian-language text-to-speech
- Translate / Mayura for cross-language CRM summaries and supervisor review
- enterprise deployment paths for regulated workloads where data sovereignty matters

This is not a generic chatbot use case. The value comes from Indian language depth, latency, compliance guardrails, and integration into enterprise operations.

## 4. Architecture Summary

The borrower interacts with a voice or web-call interface. Speech is transcribed using Sarvam STT. The conversation orchestrator sends borrower context and policy guardrails to Sarvam-105B. The agent responds in the borrower’s language and uses workflow tools to update CRM, queue reminders, or escalate to human collections specialists. Sarvam TTS converts the response to voice.

Core components:

1. Borrower voice/text interface
2. Sarvam STT: speech-to-text
3. Conversation orchestrator
4. Sarvam-105B: response generation and decisioning
5. Policy guardrails: compliant collections behavior
6. Workflow router: CRM update, reminder queue, escalation queue
7. Sarvam TTS: voice response
8. Post-call analytics: summary, risk score, next-best action

## 5. ROI / Business Case

Monthly call volume assumption: 10 lakh early-stage collections calls.

Current cost:

- 10,00,000 calls × INR 45 = INR 4.5 crore/month

AI-assisted cost:

- 60% automated: 6,00,000 × INR 6 = INR 36 lakh
- 40% human-handled: 4,00,000 × INR 45 = INR 1.8 crore
- Total: INR 2.16 crore/month

Estimated monthly savings: INR 2.34 crore
Estimated annual savings: INR 28.08 crore

Additional upside:

- better right-party contact experience in preferred language
- faster promise-to-pay capture
- reduced repeat calling after commitment
- cleaner CRM disposition
- lower human agent load
- stronger auditability through transcript and summary

## 6. Limitations and Next Steps

PoC limitations:

- uses mock borrower records and mock CRM
- no live telephony integration
- no production consent workflow
- no real payment gateway integration
- no full compliance review
- latency not benchmarked under load

90-day rollout plan:

**Days 1–15: Discovery and compliance design**
Map call types, scripts, escalation rules, consent requirements, and CRM fields.

**Days 16–35: Pilot build**
Integrate telephony, Sarvam STT/TTS/LLM, CRM sandbox, and payment reminder system.

**Days 36–60: Controlled pilot**
Run on one language pair, one product, and one early-bucket segment. Measure containment rate, promise-to-pay rate, escalation quality, and complaint rate.

**Days 61–90: Scale-up**
Expand to more languages, products, and borrower cohorts. Add supervisor dashboard, QA sampling, human-in-loop review, and analytics.
