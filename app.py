"""Streamlit UI:  streamlit run app.py"""
import json
import streamlit as st

from src.llm import LLMClient
from src.orchestrator import Orchestrator
from src.utils import read_resume

st.set_page_config(page_title="AI Recruitment & Interview System", page_icon="🤝", layout="wide")
st.title("🤝 AI Recruitment & Interview System")
st.caption("Multi-agent pipeline: Resume Analyzer → Job Matcher → Question Generator → "
           "Mock Interviewer → Answer Evaluator → Report Agent")

ss = st.session_state
if "orch" not in ss:
    ss.orch, ss.step, ss.qi, ss.pending_fu = Orchestrator(LLMClient()), "input", 0, None
orch = ss.orch
st.sidebar.markdown(f"**LLM:** `{orch.llm.provider}` · `{orch.llm.model}`")
n_q = st.sidebar.slider("Number of questions", 3, 10, 5)
if st.sidebar.button("🔄 Start over"):
    ss.clear()
    st.rerun()

# ── Step 1: input ────────────────────────────────────────────────────────
if ss.step == "input":
    c1, c2 = st.columns(2)
    up = c1.file_uploader("Resume (PDF or TXT)", type=["pdf", "txt"])
    jd = c2.text_area("Job description", height=220, value=open("data/sample_job.txt").read())
    if st.button("Analyse & match", type="primary"):
        resume = read_resume(up) if up else open("data/sample_resume.txt").read()
        with st.spinner("ResumeAnalyzer and JobMatcher are working…"):
            orch.screen(resume, jd)
            orch.plan_interview(n_q)
        ss.step = "screen"
        st.rerun()

# ── Step 2: screening result ─────────────────────────────────────────────
elif ss.step == "screen":
    p, m = orch.state.profile, orch.state.match
    c1, c2, c3 = st.columns(3)
    c1.metric("Candidate", p.get("name", "?"))
    c2.metric("Experience (yrs)", p.get("experience_years", 0))
    c3.metric("Job match", f"{m['score']}/100", m["recommendation"])
    st.success("Matched: " + (", ".join(m["matched_skills"]) or "–"))
    st.warning("Missing: " + (", ".join(m["missing_skills"]) or "–"))
    st.write(m.get("reasoning", ""))
    with st.expander(f"Interview plan ({len(orch.state.questions)} questions)"):
        for q in orch.state.questions:
            st.write(f"**Q{q.id}** [{q.type}/{q.difficulty}] {q.question}")
    if st.button("Start mock interview ▶", type="primary"):
        ss.step = "interview"
        st.rerun()

# ── Step 3: interview ────────────────────────────────────────────────────
elif ss.step == "interview":
    qs = orch.state.questions
    if ss.qi >= len(qs):
        orch.finish()
        ss.step = "report"
        st.rerun()
    q = qs[ss.qi]
    st.progress(ss.qi / len(qs), text=f"Question {ss.qi + 1} of {len(qs)}")
    st.chat_message("assistant").write(q.question)
    if ss.get("first_answer"):
        st.chat_message("user").write(ss.first_answer)
        st.chat_message("assistant").write(ss.pending_fu)
    ans = st.chat_input("Type your answer…")
    if ans:
        if ss.pending_fu is None:                      # first answer → maybe follow-up
            fu = orch.get_follow_up(q, ans)
            if fu:
                ss.first_answer, ss.pending_fu = ans, fu
            else:
                orch.process_answer(q, ans)
                ss.qi += 1
        else:                                          # follow-up answer
            orch.process_answer(q, ss.first_answer, ans)
            ss.first_answer, ss.pending_fu = None, None
            ss.qi += 1
        st.rerun()

# ── Step 4: report ───────────────────────────────────────────────────────
else:
    r = orch.state.report
    st.header(f"Decision support: {r['decision']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Final score", f"{r['final_score']}/100")
    c2.metric("Resume match", r["match_score"])
    c3.metric("Interview average", f"{r['interview_avg']}/10")
    st.write(r.get("summary", ""))
    st.subheader("Per-question scores")
    for e in orch.state.evaluations:
        q = orch.state.questions[e.question_id - 1]
        with st.expander(f"Q{e.question_id}: {q.question[:70]}…  →  {e.overall}/10"):
            st.write(e.feedback)
            st.info("Tip: " + e.improvement)
    with st.expander("Agent trace (explainability)"):
        st.dataframe(orch.state.trace)
    st.download_button("Download JSON report",
                       json.dumps(orch.state.to_dict(), indent=2, default=str),
                       "report.json", "application/json")
    st.caption("This tool supports, not replaces, human hiring decisions.")
