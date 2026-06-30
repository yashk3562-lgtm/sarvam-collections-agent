# Architecture Diagram

```mermaid
sequenceDiagram
    participant B as Borrower
    participant UI as Web/Telephony Interface
    participant STT as Sarvam Saaras v3 STT
    participant ORCH as Conversation Orchestrator
    participant LLM as Sarvam-105B
    participant TTS as Sarvam Bulbul v3 TTS
    participant CRM as Loan CRM
    participant R as Reminder Queue
    participant H as Human Escalation Queue

    B->>UI: Speaks in Hindi / English / Hinglish
    UI->>STT: Audio stream
    STT->>ORCH: Transcript
    ORCH->>LLM: Borrower context + policy + transcript
    LLM->>ORCH: Agent response + decision
    ORCH->>CRM: Update disposition
    alt Promise-to-pay
        ORCH->>R: Queue reminder
    else Dispute / distress / refusal
        ORCH->>H: Escalate case
    end
    ORCH->>TTS: Response text
    TTS->>UI: Agent audio
    UI->>B: Speaks response
```

## Data Flow

1. Borrower speech enters web app or telephony layer.
2. Saaras v3 transcribes speech and handles code-mixing.
3. Orchestrator injects account details and collections policy.
4. Sarvam-105B generates compliant response and workflow decision.
5. Workflow layer updates CRM, reminder queue, and escalation queue.
6. Bulbul v3 generates voice output.
7. Post-call analytics summarizes outcome and risk.
