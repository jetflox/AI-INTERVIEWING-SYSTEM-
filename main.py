"""CLI entry point.

  python main.py --demo                          # simulated candidate, sample files
  python main.py --resume my.pdf --job jd.txt    # you answer the questions live
  python main.py --demo --provider mock          # fully offline
"""
import argparse
import json
import os

from src.llm import LLMClient
from src.orchestrator import Orchestrator
from src.simulator import SimulatedCandidate
from src.utils import read_resume

BAR = "─" * 64


def main():
    ap = argparse.ArgumentParser(description="Multi-agent AI recruitment & interview system")
    ap.add_argument("--resume", default="data/sample_resume.txt")
    ap.add_argument("--job", default="data/sample_job.txt")
    ap.add_argument("--questions", type=int, default=6)
    ap.add_argument("--provider", choices=["anthropic", "openai", "mock"])
    ap.add_argument("--demo", action="store_true", help="simulated candidate answers")
    ap.add_argument("--out", default="outputs/report.json")
    a = ap.parse_args()

    llm = LLMClient(a.provider)
    print(f"\n{BAR}\n AI RECRUITMENT & INTERVIEW SYSTEM   [{llm.provider} · {llm.model}]\n{BAR}")
    orch = Orchestrator(llm)
    resume, job = read_resume(a.resume), read_resume(a.job)

    print("\n[1/2] ResumeAnalyzer + JobMatcher …")
    profile, match = orch.screen(resume, job)
    print(f"  Candidate : {profile.get('name')}  ({profile.get('experience_years')} yrs)")
    print(f"  Match     : {match['score']}/100  → {match['recommendation']}")
    print(f"  Matched   : {', '.join(match['matched_skills']) or '-'}")
    print(f"  Missing   : {', '.join(match['missing_skills']) or '-'}")

    print("\n[3] QuestionGenerator …")
    questions = orch.plan_interview(a.questions)
    for q in questions:
        print(f"  Q{q.id} [{q.type}/{q.difficulty}] {q.question}")

    print(f"\n[4-5] Mock interview + evaluation\n{BAR}")
    sim = SimulatedCandidate(llm, resume) if a.demo else None
    for i, q in enumerate(questions):
        print(f"\nInterviewer Q{q.id}: {q.question}")
        ans = sim.answer(q, i) if sim else input("Your answer > ")
        if sim:
            print(f"Candidate  : {ans}")
        fu = orch.get_follow_up(q, ans)
        fu_ans = None
        if fu:
            print(f"Follow-up  : {fu}")
            fu_ans = sim.answer(q, i + 1) if sim else input("Your answer > ")
            if sim:
                print(f"Candidate  : {fu_ans}")
        ev = orch.process_answer(q, ans, fu_ans)
        print(f"  ⇒ score {ev.overall}/10  (T{ev.technical:.0f} D{ev.depth:.0f} "
              f"R{ev.relevance:.0f} C{ev.communication:.0f})  {ev.feedback}")

    print(f"\n[6] ReportAgent …\n{BAR}")
    rep = orch.finish()
    print(f"  DECISION   : {rep['decision']}   (final {rep['final_score']}/100)")
    print(f"  Match {rep['match_score']} · Interview avg {rep['interview_avg']}/10")
    print(f"  Summary    : {rep.get('summary')}")
    print(f"  Strengths  : {', '.join(rep.get('strengths', []))}")
    print(f"  Concerns   : {', '.join(rep.get('concerns', []))}")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(orch.state.to_dict(), f, indent=2, default=str)
    print(f"\nFull report + agent trace saved to {a.out}\n")


if __name__ == "__main__":
    main()
