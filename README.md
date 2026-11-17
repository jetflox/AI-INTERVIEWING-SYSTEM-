# AI Recruitment & Interview System (Multi-Agent)

Six cooperating LLM agents that **analyse a resume, match it to a job, generate
tailored interview questions, run a mock interview with follow-ups, score every
answer with a rubric, and produce a hiring-support report.**

```
Resume + JD ─► ResumeAnalyzer ─► JobMatcher ─► QuestionGenerator
                                                     │
        Report ◄─ ReportAgent ◄─ AnswerEvaluator ◄─ MockInterviewer ◄┘  (loop per question)
```

## Quick start
```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # add ANTHROPIC_API_KEY (or OPENAI_API_KEY)

python main.py --demo                                 # CLI, simulated candidate
python main.py --resume my_resume.pdf --job jd.txt    # CLI, you answer live
streamlit run app.py                                  # web UI
python main.py --demo --provider mock                 # no API key needed (offline heuristics)
```

## Project structure
| File | Purpose |
|---|---|
| `src/prompts.py` | **All prompts** – roles, rubric, JSON schemas, fairness rules (the prompt-engineering core) |
| `src/agents.py` | The 6 agents, each with JSON validation, retry and a deterministic fallback |
| `src/orchestrator.py` | Shared state (blackboard) + step-wise pipeline |
| `src/llm.py` | Provider wrapper (Anthropic / OpenAI / mock) + robust JSON extraction |
| `src/simulator.py` | Simulated candidate for hands-free demos |
| `main.py` / `app.py` | CLI and Streamlit front-ends |

## Prompt-engineering techniques demonstrated
1. **Role prompting** – narrow persona per agent
2. **Structured output** – JSON schema inside the prompt, parsed and validated
3. **Few-shot example** – inside the evaluator prompt
4. **Rubric with anchors** – technical / depth / relevance / communication (1-10)
5. **Guardrails** – fairness rules (ignore name, gender, college), "no invented facts"
6. **Validation + retry + fallback** – invalid JSON triggers one retry, then heuristics

## Scoring
* Answer score = 0.35·technical + 0.25·depth + 0.25·relevance + 0.15·communication
* Final score = 0.4·job-match + 0.6·(interview average × 10)
* ≥ 75 → **Hire**, 55–74 → **Hold**, < 55 → **No Hire** (decision *support* only; a human decides)

## Ideas to extend
Voice interviews (speech-to-text), RAG over company hiring rubrics, ATS integration,
bias-audit dashboard, multilingual interviews.
