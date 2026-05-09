"""HR Shortlisting Agent — Space Theme"""
import os, streamlit as st, base64
from datetime import datetime
from dotenv import load_dotenv
from utils.llm_client import DEFAULT_MODEL
from utils.file_handler import read_uploaded_file
from agents.jd_parser import parse_jd
from agents.profile_parser import parse_profile
from agents.scorer import score_candidate
from agents.report_generator import generate_html_report, generate_json_report

load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY","")
MODEL   = os.getenv("GROQ_MODEL", DEFAULT_MODEL)

# Load space hero background as base64
_bg_path = os.path.join(os.path.dirname(__file__), "static", "space_hero_bg.png")
_BG_B64 = ""
if os.path.exists(_bg_path):
    with open(_bg_path, "rb") as _f:
        _BG_B64 = base64.b64encode(_f.read()).decode()

st.set_page_config(page_title="HR Shortlisting Agent", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

:root {
  --iris:#7c3aed; --violet:#8b5cf6; --sky:#38bdf8; --mint:#34d399;
  --bg:#0d0221; --s1:#130a2e; --s2:#1a0f3d; --s3:#1e1545;
  --border:rgba(124,58,237,0.2); --text:#e2e8f0; --muted:#64748b;
  --shadow:0 4px 24px rgba(0,0,0,0.4);
}

[data-testid="stSidebar"],[data-testid="collapsedControl"]{display:none!important}
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;color:var(--text)!important;}
.stApp{background:var(--bg)!important}
.main .block-container{padding:0 2.5rem 3rem!important;max-width:1280px!important}

/* ── HERO ── */
.hero{
  background:linear-gradient(135deg,#0d0221 0%,#2d1b69 45%,#0f2760 100%);
  padding:4rem 3.5rem 7rem; margin:0 -2.5rem; position:relative; overflow:hidden;
}
.hero::before{content:'';position:absolute;top:-100px;right:5%;width:380px;height:380px;
  border-radius:50%;background:radial-gradient(circle,rgba(180,80,255,0.35) 0%,transparent 65%);}
.hero::after{content:'';position:absolute;top:30px;right:28%;width:160px;height:160px;
  border-radius:50%;background:radial-gradient(circle,rgba(100,180,255,0.4) 0%,transparent 60%);}
.hero-wave{position:absolute;bottom:-2px;left:0;right:0;}
.hero-tag{display:inline-flex;align-items:center;gap:6px;
  background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);
  color:rgba(255,255,255,0.8);padding:5px 16px;border-radius:999px;
  font-size:0.7rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1.2rem;}
.hero-title{font-size:3.2rem;font-weight:900;color:white;letter-spacing:-0.04em;line-height:1.1;max-width:560px;}
.hero-sub{color:rgba(255,255,255,0.5);font-size:0.95rem;margin-top:0.7rem;max-width:440px;line-height:1.7;}
.hero-pills{display:flex;flex-wrap:wrap;gap:0.4rem;margin-top:1.4rem;}
.hpill{background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);
  color:rgba(255,255,255,0.75);border-radius:999px;padding:4px 12px;font-size:0.7rem;font-weight:500;}

/* ── STEPS ── */
.steps{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;
  margin:-3rem 0 2rem;position:relative;z-index:10;}
.step{background:var(--s1);border:1px solid var(--border);border-radius:20px;
  padding:1.5rem 1rem;text-align:center;box-shadow:var(--shadow);
  transition:transform 0.2s,box-shadow 0.2s,border-color 0.2s;}
.step:hover{transform:translateY(-4px);border-color:rgba(124,58,237,0.5);
  box-shadow:0 12px 40px rgba(124,58,237,0.25);}
.step-icon{width:60px;height:60px;border-radius:50%;
  background:linear-gradient(135deg,rgba(124,58,237,0.2),rgba(99,102,241,0.15));
  border:2px solid rgba(124,58,237,0.35);
  display:flex;align-items:center;justify-content:center;
  font-size:1.4rem;margin:0 auto 0.8rem;}
.step-title{font-size:0.82rem;font-weight:700;color:#e2e8f0;margin-bottom:0.25rem;}
.step-desc{font-size:0.7rem;color:#475569;line-height:1.5;}

/* ── KPI ── */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:0.75rem;margin-bottom:1.5rem;}
.kpi{background:var(--s1);border:1px solid var(--border);border-radius:16px;
  padding:1.1rem 0.8rem;text-align:center;position:relative;overflow:hidden;
  box-shadow:var(--shadow);transition:transform 0.2s,box-shadow 0.2s;cursor:default;}
.kpi:hover{transform:translateY(-4px);border-color:rgba(124,58,237,0.4);box-shadow:0 8px 30px rgba(124,58,237,0.2);}
.kpi::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 16px 0 0;}
.kpi-a::before{background:linear-gradient(90deg,#7c3aed,#8b5cf6);}
.kpi-b::before{background:linear-gradient(90deg,#38bdf8,#34d399);}
.kpi-c::before{background:linear-gradient(90deg,#fb7185,#f97316);}
.kpi-d::before{background:linear-gradient(90deg,#fbbf24,#f59e0b);}
.kpi-e::before{background:linear-gradient(90deg,#34d399,#059669);}
.kpi-f::before{background:linear-gradient(90deg,#c084fc,#7c3aed);}
.knum{font-size:1.8rem;font-weight:800;line-height:1;color:#a78bfa;}
.klbl{font-size:0.6rem;color:#475569;text-transform:uppercase;letter-spacing:0.08em;margin-top:0.3rem;}

/* ── SECTION LABEL ── */
.slbl{display:flex;align-items:center;gap:8px;font-size:0.68rem;font-weight:700;
  text-transform:uppercase;letter-spacing:0.1em;color:#a78bfa;margin:1.5rem 0 0.75rem;}
.snum{width:22px;height:22px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#6366f1);
  color:white;font-size:0.68rem;font-weight:800;display:inline-flex;align-items:center;justify-content:center;}

/* ── BARS ── */
.bt{background:rgba(255,255,255,0.06);border-radius:999px;height:6px;overflow:hidden;flex:1;}
.bf{height:100%;border-radius:999px;}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"]{background:var(--s1)!important;border-radius:12px!important;
  padding:0.3rem!important;border:1px solid var(--border)!important;gap:0.2rem!important;}
.stTabs [data-baseweb="tab"]{border-radius:8px!important;color:#64748b!important;font-weight:600!important;font-size:0.88rem!important;}
.stTabs [aria-selected="true"]{background:linear-gradient(135deg,#7c3aed,#6366f1)!important;color:white!important;}

/* ── BUTTONS ── */
.stButton>button{background:linear-gradient(135deg,#7c3aed,#6366f1)!important;color:white!important;
  border:none!important;border-radius:12px!important;font-weight:700!important;
  padding:0.65rem 2rem!important;transition:all 0.2s!important;font-size:0.95rem!important;}
.stButton>button:hover{opacity:0.9!important;transform:translateY(-2px)!important;
  box-shadow:0 8px 28px rgba(124,58,237,0.45)!important;}

/* ── INPUTS ── */
.stTextInput input,.stTextArea textarea{
  background:var(--s2)!important;border:1.5px solid var(--border)!important;
  border-radius:10px!important;color:#e2e8f0!important;font-size:0.9rem!important;}
.stTextInput input:focus,.stTextArea textarea:focus{
  border-color:#7c3aed!important;box-shadow:0 0 0 3px rgba(124,58,237,0.15)!important;}
label,.stRadio label,.stToggle label{color:#94a3b8!important;font-weight:500!important;}

/* ── EXPANDER ── */
div[data-testid="stExpander"]{background:var(--s1)!important;border:1px solid var(--border)!important;
  border-radius:14px!important;box-shadow:var(--shadow)!important;}
div[data-testid="stExpander"]:hover{border-color:rgba(124,58,237,0.4)!important;}
div[data-testid="stExpander"] p,div[data-testid="stExpander"] li,
div[data-testid="stExpander"] span{color:#94a3b8!important;}

/* ── FILE UPLOADER ── */
div[data-testid="stFileUploader"]{background:var(--s1)!important;
  border:2px dashed rgba(124,58,237,0.35)!important;border-radius:14px!important;}

/* ── STATUS / PROGRESS ── */
div[data-testid="stAlert"]{border-radius:12px!important;}
div[data-testid="stStatusWidget"]{background:var(--s1)!important;}
.stProgress>div>div{background:linear-gradient(90deg,#7c3aed,#38bdf8)!important;border-radius:999px!important;}
div[data-testid="stProgress"]>div{background:rgba(255,255,255,0.06)!important;border-radius:999px!important;}

/* ── STATUS CHIPS ── */
.status-chip{display:inline-flex;align-items:center;gap:5px;padding:5px 12px;
  border-radius:999px;font-size:0.7rem;font-weight:600;border:1px solid;}
.sc-active{background:rgba(16,185,129,0.1);color:#34d399;border-color:rgba(52,211,153,0.3);}
.sc-review{background:rgba(124,58,237,0.1);color:#a78bfa;border-color:rgba(167,139,250,0.3);}
.sc-warn{background:rgba(245,158,11,0.1);color:#fbbf24;border-color:rgba(251,191,36,0.3);}
</style>
""", unsafe_allow_html=True)

if _BG_B64:
    st.markdown(f"""
    <style>
    .hero {{
      background: url(data:image/png;base64,{_BG_B64}) center center / cover no-repeat !important;
    }}
    </style>
    """, unsafe_allow_html=True)



# helpers
def sc(s): return "green" if s>=8 else "blue" if s>=6.5 else "amber" if s>=5 else "red"
COLS={"green":"#10b981","blue":"#3b82f6","amber":"#f59e0b","red":"#ef4444"}
RECS={"Strong Hire":("&#x1F7E2;","rgba(16,185,129,0.12)","#10b981"),"Hire":("&#x1F535;","rgba(59,130,246,0.12)","#3b82f6"),
      "Maybe":("&#x1F7E1;","rgba(245,158,11,0.12)","#f59e0b"),"No Hire":("&#x1F534;","rgba(239,68,68,0.12)","#ef4444")}


def bar(s,w):
    c=sc(s);col=COLS[c]
    return(f'<div style="display:grid;grid-template-columns:140px 1fr 36px;gap:.5rem;align-items:center;margin:.25rem 0;">'
           f'<span style="font-size:.72rem;color:#94a3b8;">Weight {w}%</span>'
           f'<div class="bt"><div class="bf" style="width:{s*10}%;background:{col};"></div></div>'
           f'<span style="font-size:.78rem;font-weight:700;color:{col};text-align:right;">{s:.1f}</span></div>')

# session state
for k,v in [("results",[]),("jd_parsed",None),("override_log",[])]:
    if k not in st.session_state: st.session_state[k]=v

# HERO + WAVE + STEPS
st.markdown("""
<div class="hero">
  <div style="position:relative;z-index:2;">
    <div class="hero-tag">&#9889; AI-Powered Recruitment Intelligence</div>
    <div class="hero-title">Hire Smarter,<br>Not Harder.</div>
    <div class="hero-sub">Upload a Job Description and resumes &mdash; get a transparent AI-scored shortlist in seconds.</div>
    <div class="hero-pills">
      <span class="hpill">&#128202; 5-Dimension Rubric</span>
      <span class="hpill">&#129302; Llama 3.3 70B &middot; Groq</span>
      <span class="hpill">&#128274; Secure &amp; Private</span>
      <span class="hpill">&#128100; Human-in-the-Loop</span>
    </div>
  </div>
  <div class="hero-wave">
    <svg viewBox="0 0 1440 80" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" style="display:block;width:100%;height:80px;">
      <path d="M0,40 C240,80 480,0 720,40 C960,80 1200,0 1440,40 L1440,80 L0,80 Z" fill="#0d0221"/>
    </svg>
  </div>
</div>
<div class="steps">
  <div class="step"><div class="step-icon">&#128203;</div><div class="step-title">Paste Job Description</div><div class="step-desc">Add the JD text or upload a file</div></div>
  <div class="step"><div class="step-icon">&#128194;</div><div class="step-title">Upload Resumes</div><div class="step-desc">PDF, DOCX or TXT supported</div></div>
  <div class="step"><div class="step-icon">&#129302;</div><div class="step-title">AI Analyses</div><div class="step-desc">Scores each candidate on 5 dimensions</div></div>
  <div class="step"><div class="step-icon">&#127942;</div><div class="step-title">Get Shortlist</div><div class="step-desc">Ranked results + downloadable report</div></div>
</div>
""", unsafe_allow_html=True)


tab1,tab2,tab3 = st.tabs(["📋  Setup & Analyse","🏆  Results & Override","📄  Export Report"])



# ── TAB 1 ──────────────────────────────────────────────────────────────────
with tab1:
    c1,c2 = st.columns([1,1],gap="large")
    with c1:
        st.markdown('<div class="slbl"><span class="snum">1</span>Job Description</div>',unsafe_allow_html=True)
        src = st.radio("",["✏️ Paste text","📁 Upload file"],horizontal=True,label_visibility="collapsed")
        if src=="✏️ Paste text":
            sp=os.path.join(os.path.dirname(__file__),"sample_data","sample_jd.txt")
            jd_text=st.text_area("",value=open(sp,encoding="utf-8").read() if os.path.exists(sp) else "",
                                 height=320,label_visibility="collapsed",placeholder="Paste job description here…")
        else:
            jf=st.file_uploader("",type=["txt","pdf","docx"],label_visibility="collapsed")
            jd_text=""
            if jf:
                try: jd_text,_=read_uploaded_file(jf); st.success(f"✅ {jf.name}")
                except Exception as e: st.error(str(e))

    with c2:
        st.markdown('<div class="slbl"><span class="snum">2</span>Candidate Resumes</div>',unsafe_allow_html=True)
        demo=st.toggle("Use built-in sample resumes (demo mode)",value=True)
        if demo:
            sd=os.path.join(os.path.dirname(__file__),"sample_data")
            n=len([f for f in os.listdir(sd) if f.startswith("resume_")])
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,#eef2ff,#f0f9ff);border:1.5px solid #c7d2fe;
              border-radius:16px;padding:2rem;text-align:center;margin-top:0.5rem;">
              <div style="font-size:3rem;font-weight:900;color:#6366f1;">{n}</div>
              <div style="font-size:0.9rem;font-weight:600;color:#3730a3;margin-top:0.2rem;">Sample resumes ready</div>
              <div style="font-size:0.75rem;color:#64748b;margin-top:0.4rem;">Mix of excellent, good, partial & poor matches</div>
            </div>""",unsafe_allow_html=True)
            uploaded=None
        else:
            uploaded=st.file_uploader("Drop PDF / DOCX / TXT files",type=["pdf","docx","txt"],
                                      accept_multiple_files=True,label_visibility="collapsed")
            if uploaded:
                st.success(f"✅ {len(uploaded)} file(s) ready")

    st.markdown("<br>",unsafe_allow_html=True)
    _,bc,_ = st.columns([2,2,2])
    with bc: run=st.button("🚀 Analyse Candidates",use_container_width=True)

    if run:
        if not API_KEY: st.error("❌ GROQ_API_KEY not set in .env — add it and restart."); st.stop()
        if not jd_text or len(jd_text.strip())<30: st.error("❌ Provide a Job Description."); st.stop()
        resumes=[]
        if demo:
            sd=os.path.join(os.path.dirname(__file__),"sample_data")
            for fn in sorted(os.listdir(sd)):
                if fn.startswith("resume_") and fn.endswith(".txt"):
                    resumes.append((open(os.path.join(sd,fn),encoding="utf-8").read(),fn))
        elif uploaded:
            for uf in uploaded:
                try: c,n=read_uploaded_file(uf); resumes.append((c,n))
                except Exception as e: st.warning(f"Skipped {uf.name}: {e}")
        else: st.error("❌ Upload resumes or enable sample mode."); st.stop()

        with st.status("🔍 Parsing Job Description…",expanded=True) as status:
            try:
                jd=parse_jd(jd_text,model=MODEL,api_key=API_KEY)
                st.session_state.jd_parsed=jd
                st.write(f"✅ **{jd.job_title}** · {len(jd.required_skills)} skills found")
                status.update(label="✅ JD Parsed",state="complete")
            except Exception as e: st.error(f"Failed to parse JD: {e}"); st.stop()

        results=[]
        prog=st.progress(0,text="Analysing candidates…")
        for i,(txt,fn) in enumerate(resumes):
            prog.progress(int(i/len(resumes)*100),text=f"Processing {fn}…")
            with st.status(f"📄 {fn}",expanded=False):
                try:
                    p=parse_profile(txt,fn,model=MODEL,api_key=API_KEY)
                    s=score_candidate(jd,p,fn,model=MODEL,api_key=API_KEY)
                    results.append(s)
                    st.write(f"→ **{s.total_score:.1f}/10** · {s.recommendation}")
                    st.success("✅ Done")
                except Exception as e: st.error(f"Error: {e}")

        prog.progress(100,text="✅ Complete!")
        results.sort(key=lambda x:x.total_score,reverse=True)
        st.session_state.results=results
        st.session_state.override_log=[]
        st.success(f"🎉 Analysed **{len(results)}** candidates! See the **Results** tab →")

# ── TAB 2 ──────────────────────────────────────────────────────────────────
with tab2:
    results=st.session_state.results
    if not results:
        st.markdown("""<div style="text-align:center;padding:5rem;background:white;border-radius:20px;
          border:1.5px dashed #c7d2fe;margin-top:1rem;">
          <div style="font-size:3rem;">📊</div>
          <div style="font-size:1.1rem;color:#3730a3;font-weight:700;margin-top:0.8rem;">No results yet</div>
          <div style="color:#64748b;margin-top:0.4rem;font-size:0.9rem;">Complete the analysis in the Setup tab first</div>
        </div>""",unsafe_allow_html=True)
    else:
        jd=st.session_state.jd_parsed
        sh=sum(1 for r in results if r.recommendation=="Strong Hire")
        hi=sum(1 for r in results if r.recommendation=="Hire")
        ma=sum(1 for r in results if r.recommendation=="Maybe")
        no=sum(1 for r in results if r.recommendation=="No Hire")
        avg=sum(r.total_score for r in results)/len(results)

        st.markdown(f"""<div class="kpi-row">
          <div class="kpi"><div class="knum" style="color:#6366f1;">{len(results)}</div><div class="klbl">Analysed</div></div>
          <div class="kpi"><div class="knum" style="color:#10b981;">{sh}</div><div class="klbl">Strong Hire</div></div>
          <div class="kpi"><div class="knum" style="color:#3b82f6;">{hi}</div><div class="klbl">Hire</div></div>
          <div class="kpi"><div class="knum" style="color:#f59e0b;">{ma}</div><div class="klbl">Maybe</div></div>
          <div class="kpi"><div class="knum" style="color:#ef4444;">{no}</div><div class="klbl">No Hire</div></div>
          <div class="kpi"><div class="knum" style="color:#8b5cf6;">{avg:.1f}</div><div class="klbl">Avg Score</div></div>
        </div>""",unsafe_allow_html=True)

        st.markdown(f'<div class="slbl">🏆 Ranked Shortlist — {jd.job_title}</div>',unsafe_allow_html=True)

        for rank,c in enumerate(results,1):
            icon,bg,col=RECS.get(c.recommendation,("⚪","#f8fafc","#64748b"))
            ovr=" · ⚠ *overridden*" if c.is_overridden else ""
            with st.expander(f"#{rank}  **{c.candidate_name}**  ·  {icon} {c.recommendation}  ·  **{c.total_score:.1f}**/10{ovr}",expanded=(rank<=2)):
                L,R=st.columns([3,2])
                with L:
                    st.markdown(f"""<div style="padding-bottom:0.8rem;margin-bottom:0.8rem;
                      border-bottom:1px solid #f1f5f9;">
                      <span style="color:#94a3b8;font-size:0.78rem;">📄 {c.file_name}</span><br>
                      <span style="color:#475569;font-size:0.85rem;">💼 {c.profile.current_role or 'N/A'} &nbsp;·&nbsp; {int(c.profile.experience_years)} yrs</span>
                    </div>""",unsafe_allow_html=True)
                    st.markdown("**📊 Dimension Scores**")
                    for s in c.scores:
                        st.markdown(bar(s.raw_score,int(s.weight*100)),unsafe_allow_html=True)
                        st.markdown(f"<div style='font-size:.7rem;color:#94a3b8;margin:-.05rem 0 .4rem .3rem;'>↳ {s.dimension}: {s.justification}</div>",unsafe_allow_html=True)
                with R:
                    st.markdown(f"""<div style="background:{bg};border:1.5px solid {col}33;
                      border-radius:14px;padding:1rem;text-align:center;margin-bottom:1rem;">
                      <div style="font-size:1.3rem;">{icon}</div>
                      <div style="font-weight:700;color:{col};font-size:0.95rem;">{c.recommendation}</div>
                      <div style="font-size:2.2rem;font-weight:900;color:{col};">{c.total_score:.1f}<span style="font-size:1rem;opacity:.5;">/10</span></div>
                    </div>""",unsafe_allow_html=True)
                    if c.strengths:
                        st.markdown("**✅ Strengths**")
                        for s in c.strengths: st.markdown(f"<span style='font-size:.8rem;color:#475569;'>• {s}</span><br>",unsafe_allow_html=True)
                    if c.gaps:
                        st.markdown("**⚠ Gaps**")
                        for g in c.gaps: st.markdown(f"<span style='font-size:.8rem;color:#475569;'>• {g}</span><br>",unsafe_allow_html=True)
                    if c.overall_justification:
                        st.markdown(f"<div style='margin-top:.8rem;font-size:.75rem;color:#64748b;font-style:italic;border-top:1px solid #f1f5f9;padding-top:.6rem;'>{c.overall_justification}</div>",unsafe_allow_html=True)
                    if c.is_overridden and c.override_reason:
                        st.warning(f"⚠ Override: {c.override_reason}")

                with st.form(key=f"ov_{rank}"):
                    st.markdown("**🖊 HR Override**")
                    fc1,fc2=st.columns([1,2])
                    with fc1: ns=st.number_input("New score",0.0,10.0,float(c.total_score),0.5)
                    with fc2: reason=st.text_input("Reason",placeholder="e.g. Strong culture fit")
                    if st.form_submit_button("Apply Override"):
                        if not reason.strip(): st.error("Add a reason.")
                        else:
                            idx=next((i for i,r in enumerate(st.session_state.results) if r.file_name==c.file_name),None)
                            if idx is not None:
                                r=st.session_state.results[idx]
                                if not r.is_overridden: r.original_total_score=r.total_score
                                r.total_score=ns; r.is_overridden=True; r.override_reason=reason
                                from agents.scorer import _get_recommendation
                                r.recommendation=_get_recommendation(ns)
                                st.session_state.override_log.append({"ts":datetime.now().isoformat(),"candidate":r.candidate_name,"score":ns,"reason":reason})
                                st.session_state.results.sort(key=lambda x:x.total_score,reverse=True)
                                st.rerun()

        if st.session_state.override_log:
            with st.expander("📋 Override Audit Log"): st.json(st.session_state.override_log)

# ── TAB 3 ──────────────────────────────────────────────────────────────────
with tab3:
    results=st.session_state.results
    if not results:
        st.markdown("""<div style="text-align:center;padding:5rem;background:white;border-radius:20px;
          border:1.5px dashed #c7d2fe;margin-top:1rem;">
          <div style="font-size:3rem;">📄</div>
          <div style="font-size:1.1rem;color:#3730a3;font-weight:700;margin-top:0.8rem;">No data to export</div>
          <div style="color:#64748b;font-size:0.9rem;margin-top:0.4rem;">Run the analysis first</div>
        </div>""",unsafe_allow_html=True)
    else:
        jd=st.session_state.jd_parsed
        st.markdown('<div class="slbl">📄 Generate Report</div>',unsafe_allow_html=True)
        ca,cb=st.columns(2)
        with ca:
            if st.button("🖨 HTML Report",use_container_width=True):
                with st.spinner("Generating…"):
                    st.session_state["html_report"]=generate_html_report(jd,results)
                st.success("✅ Ready!")
        with cb:
            if st.button("📦 JSON Export",use_container_width=True):
                with st.spinner("Exporting…"):
                    st.session_state["json_report"]=generate_json_report(jd,results)
                st.success("✅ Ready!")
        if "html_report" in st.session_state:
            st.download_button("⬇️ Download HTML",st.session_state["html_report"],
                f"shortlist_{jd.job_title.replace(' ','_')}.html","text/html",use_container_width=True)
            with st.expander("👁 Preview"):
                st.components.v1.html(st.session_state["html_report"],height=700,scrolling=True)
        if "json_report" in st.session_state:
            st.download_button("⬇️ Download JSON",st.session_state["json_report"],
                f"shortlist_{jd.job_title.replace(' ','_')}.json","application/json",use_container_width=True)
