"""
AI-Powered Library Management System
Wolaita Sodo University — Computer Engineering Semester Project
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os, json, time, re
import anthropic

# Local modules
import database as db
import ai_engine as ai

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="WSU AI Library",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
  --bg: #0f0e17;
  --surface: #1a1928;
  --surface2: #252438;
  --accent: #ff6b35;
  --accent2: #f7c59f;
  --text: #fffffe;
  --text-muted: #a7a9be;
  --success: #2cb67d;
  --warning: #ffd166;
  --danger: #ef4565;
  --radius: 14px;
}

/* Base */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif;
}

[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid rgba(255,255,255,0.06);
}

/* Headers */
h1, h2, h3 { font-family: 'Playfair Display', serif !important; color: var(--text) !important; }

/* Buttons */
.stButton > button {
  background: linear-gradient(135deg, var(--accent), #ff8c5a) !important;
  color: white !important;
  border: none !important;
  border-radius: var(--radius) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-weight: 600 !important;
  padding: 0.5rem 1.5rem !important;
  transition: all 0.2s ease !important;
  box-shadow: 0 4px 15px rgba(255,107,53,0.3) !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(255,107,53,0.5) !important;
}

/* Cards */
.book-card {
  background: var(--surface2);
  border-radius: var(--radius);
  padding: 1rem;
  border: 1px solid rgba(255,255,255,0.06);
  transition: all 0.2s ease;
  height: 100%;
}
.book-card:hover {
  border-color: var(--accent);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(255,107,53,0.15);
}
.metric-card {
  background: var(--surface2);
  border-radius: var(--radius);
  padding: 1.5rem;
  border: 1px solid rgba(255,255,255,0.06);
  text-align: center;
}
.metric-card .value {
  font-family: 'Playfair Display', serif;
  font-size: 2.5rem;
  color: var(--accent);
  line-height: 1;
}
.metric-card .label {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin-top: 0.3rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}
.badge-cat {
  background: rgba(255,107,53,0.15);
  color: var(--accent2);
  border: 1px solid rgba(255,107,53,0.3);
}
.badge-avail {
  background: rgba(44,182,125,0.15);
  color: var(--success);
  border: 1px solid rgba(44,182,125,0.3);
}
.badge-unavail {
  background: rgba(239,69,101,0.15);
  color: var(--danger);
  border: 1px solid rgba(239,69,101,0.3);
}
.chat-msg-user {
  background: linear-gradient(135deg, var(--accent), #ff8c5a);
  color: white;
  border-radius: 18px 18px 4px 18px;
  padding: 0.8rem 1rem;
  margin: 0.4rem 0;
  max-width: 75%;
  margin-left: auto;
  font-size: 0.9rem;
}
.chat-msg-bot {
  background: var(--surface2);
  color: var(--text);
  border-radius: 18px 18px 18px 4px;
  padding: 0.8rem 1rem;
  margin: 0.4rem 0;
  max-width: 85%;
  border: 1px solid rgba(255,255,255,0.08);
  font-size: 0.9rem;
}
.score-bar {
  height: 4px;
  background: linear-gradient(90deg, var(--accent), var(--accent2));
  border-radius: 2px;
}
/* Input fields */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
  background: var(--surface2) !important;
  border-color: rgba(255,255,255,0.1) !important;
  color: var(--text) !important;
  border-radius: 10px !important;
}
/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-radius: var(--radius) !important;
  padding: 4px !important;
  gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--text-muted) !important;
  border-radius: 10px !important;
  font-family: 'DM Sans', sans-serif !important;
}
.stTabs [aria-selected="true"] {
  background: var(--accent) !important;
  color: white !important;
}
.stAlert { border-radius: var(--radius) !important; }
.header-brand {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 1rem 0 1.5rem;
}
.header-brand .logo { font-size: 2rem; }
.header-brand .name { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: var(--text); }
.header-brand .sub { font-size: 0.72rem; color: var(--text-muted); letter-spacing: 0.05em; }
</style>
""", unsafe_allow_html=True)

# ── Initialise DB & search index ─────────────────────────────────────────────
@st.cache_resource(show_spinner="⚙️ Initialising AI Library System…")
def initialize():
    db.init_db()
    db.import_books_from_csv("books_dataset.csv", limit=600)
    df = db.get_all_books_df()
    ai.build_search_index(df)
    return df

df_books = initialize()
def _get_anthropic_client():
    # Try Streamlit secrets first (for cloud deployment), then env var
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY","")
        return anthropic.Anthropic(api_key=api_key)
    except Exception:
        return anthropic.Anthropic()

anthr_client = _get_anthropic_client()

# ── Session defaults ──────────────────────────────────────────────────────────
for key, val in {
    "user": None,
    "chat_history": [],
    "page": "home",
    "selected_book": None,
    "ml_chat_history": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Helpers ───────────────────────────────────────────────────────────────────
def rating_stars(rating: float) -> str:
    full = int(rating)
    half = 1 if (rating - full) >= 0.5 else 0
    empty = 5 - full - half
    return "★" * full + "½" * half + "☆" * empty

def truncate(text: str, n: int = 120) -> str:
    return text[:n] + "…" if len(text) > n else text

def book_thumbnail(url: str, width: int = 80) -> str:
    if url and url.startswith("http"):
        return f'<img src="{url}" width="{width}" style="border-radius:8px;object-fit:cover;">'
    return f'<div style="width:{width}px;height:{int(width*1.4)}px;background:linear-gradient(135deg,#ff6b35,#252438);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:2rem;">📖</div>'

def render_book_card(book: dict, show_borrow: bool = True):
    bid = book.get("book_id","")
    title = book.get("title","Unknown")
    authors = book.get("authors","Unknown")
    cats = book.get("categories","")
    rating = float(book.get("average_rating") or 0)
    thumb = book.get("thumbnail","")
    avail = int(book.get("copies_available") or 1)
    desc = truncate(str(book.get("description","No description.")), 110)

    html = f"""<div class="book-card">
  <div style="display:flex;gap:0.8rem;align-items:flex-start">
    {book_thumbnail(thumb, 70)}
    <div style="flex:1;min-width:0">
      <div style="font-family:'Playfair Display',serif;font-size:0.95rem;font-weight:700;margin-bottom:2px;color:#fffffe;line-height:1.3">{truncate(title,55)}</div>
      <div style="font-size:0.78rem;color:#a7a9be;margin-bottom:4px">{truncate(authors,40)}</div>
      <div style="color:#ffd166;font-size:0.8rem">{rating_stars(rating)} <span style="color:#a7a9be">({rating:.1f})</span></div>
    </div>
  </div>
  <div style="margin-top:0.5rem;font-size:0.78rem;color:#a7a9be">{desc}</div>
  <div style="margin-top:0.6rem;display:flex;gap:0.4rem;flex-wrap:wrap;align-items:center">
    {"".join(f'<span class="badge badge-cat">{c.strip()}</span>' for c in str(cats).split(",")[:2] if c.strip() and c.strip()!="nan")}
    <span class="badge {'badge-avail' if avail>0 else 'badge-unavail'}">{avail} available</span>
  </div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)
    if show_borrow and st.session_state.user:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📖 Borrow", key=f"borrow_{bid}"):
                ok, msg = db.borrow_book(st.session_state.user["id"], bid)
                st.toast(msg, icon="✅" if ok else "❌")
                db.add_reading_history(st.session_state.user["id"], bid, cats)
        with col2:
            if st.button("🔍 Details", key=f"detail_{bid}"):
                st.session_state.selected_book = bid
                st.rerun()

# ── AI Chatbot (Anthropic) ────────────────────────────────────────────────────
def get_library_system_prompt():
    return """You are LibraBot, an intelligent AI assistant for the Wolaita Sodo University (WSU) AI-Powered Library Management System.

You help library users with:
- Book recommendations based on their interests
- Explaining topics and summarizing books
- Helping with search queries
- Library policies (14-day borrow period, 3 copies per book)
- Academic guidance for students

You have access to a library of 600+ books across various categories including Fiction, Science, Technology, Business, History, and more.

Be helpful, concise, friendly, and academic. When recommending books, be specific. Support queries in English and other languages — detect the language and respond in the same language.
"""

def chat_with_ai(user_msg: str, history: list) -> str:
    messages = []
    for h in history[-10:]:  # last 10 turns
        messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": user_msg})
    try:
        resp = anthr_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=get_library_system_prompt(),
            messages=messages,
        )
        return resp.content[0].text
    except Exception as e:
        return f"⚠️ AI service error: {str(e)}"

# ── ML Multi-play Chat (special AI feature) ──────────────────────────────────
def multiplay_ai_query(query: str, books_context: list) -> str:
    """Multi-step AI: search + summarize + recommend in one pass."""
    books_text = "\n".join([
        f"- {b['title']} by {b['authors']} [{b['categories']}] (rating: {b.get('average_rating',0):.1f})"
        for b in books_context[:8]
    ])
    system = """You are an advanced library AI. Given a user query and search results, you:
1. Acknowledge what the user is looking for
2. Explain why the top results are relevant
3. Add useful context or learning tips
4. Suggest related topics to explore
Be concise, warm, and genuinely helpful. Format with markdown."""
    prompt = f"""User query: "{query}"

Search results found:
{books_text}

Provide a rich, helpful response."""
    try:
        resp = anthr_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"⚠️ {str(e)}"

def ai_summarize_book(book: dict) -> str:
    desc = book.get("description","No description available.")[:500]
    prompt = f"""Summarize this book for a university student in 3-4 sentences. Focus on what they'll learn.

Title: {book['title']}
Authors: {book.get('authors','')}
Category: {book.get('categories','')}
Description: {desc}"""
    try:
        resp = anthr_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"⚠️ {str(e)}"

def ai_explain_topic(topic: str) -> str:
    prompt = f"Explain '{topic}' in 4-5 sentences as if to a university student, and suggest 2-3 types of books they should read to learn more."
    try:
        resp = anthr_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except Exception as e:
        return f"⚠️ {str(e)}"

def ai_translate_and_search(query: str) -> tuple[str, list]:
    """Translate non-English query then search."""
    detect_prompt = f"""Detect the language of this text and translate it to English if not already in English.
Return JSON only: {{"language": "...", "english_query": "..."}}
Text: "{query}" """
    try:
        resp = anthr_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": detect_prompt}],
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r'```json|```', '', raw).strip()
        data = json.loads(raw)
        en_query = data.get("english_query", query)
        lang = data.get("language", "English")
    except:
        en_query = query
        lang = "English"
    results = ai.semantic_search(en_query, top_k=8)
    return lang, en_query, results

# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""<div class="header-brand">
  <span class="logo">📚</span>
  <div><div class="name">WSU AI Library</div>
  <div class="sub">WOLAITA SODO UNIVERSITY</div></div>
</div>""", unsafe_allow_html=True)

        if st.session_state.user:
            u = st.session_state.user
            role_icons = {"admin":"👑","librarian":"🔑","teacher":"👨‍🏫","student":"🎓"}
            st.markdown(f"""<div style="background:var(--surface2);border-radius:12px;padding:0.8rem;margin-bottom:1rem;border:1px solid rgba(255,107,53,0.2)">
  <div style="font-weight:600">{role_icons.get(u['role'],'👤')} {u.get('full_name') or u['username']}</div>
  <div style="font-size:0.78rem;color:#a7a9be;margin-top:2px">{u['role'].title()} · {u['username']}</div>
</div>""", unsafe_allow_html=True)

            pages = [
                ("🏠", "Home", "home"),
                ("🔍", "Search Books", "search"),
                ("🤖", "AI Multiplay", "ai_multiplay"),
                ("💬", "AI Chatbot", "chatbot"),
                ("⭐", "Recommendations", "recommendations"),
                ("📖", "My Books", "my_books"),
            ]
            if u["role"] in ("admin","librarian"):
                pages += [
                    ("📊", "Analytics", "analytics"),
                    ("👥", "Manage Users", "users"),
                    ("📋", "All Borrows", "all_borrows"),
                ]
            for icon, label, page_id in pages:
                active = st.session_state.page == page_id
                if st.button(
                    f"{icon} {label}",
                    key=f"nav_{page_id}",
                    use_container_width=True,
                    type="primary" if active else "secondary"
                ):
                    st.session_state.page = page_id
                    st.session_state.selected_book = None
                    st.rerun()
            st.markdown("---")
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.page = "home"
                st.session_state.chat_history = []
                st.rerun()
        else:
            st.info("Please login to access all features.")

# ── Pages ─────────────────────────────────────────────────────────────────────
def page_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem">
  <div style="font-size:4rem">📚</div>
  <h1 style="margin:0.3rem 0">WSU AI Library</h1>
  <p style="color:#a7a9be;font-size:0.9rem">Wolaita Sodo University — AI-Powered Library System</p>
</div>""", unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐 Login", "✍️ Register"])
        with tab1:
            username = st.text_input("Username", placeholder="admin / student1 / teacher1")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            st.caption("Demo: admin/admin123 · student1/student123 · teacher1/teacher123 · librarian1/lib123")
            if st.button("Login →", use_container_width=True):
                user = db.authenticate_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.page = "home"
                    st.success(f"Welcome back, {user.get('full_name') or user['username']}!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
        with tab2:
            r_name = st.text_input("Full Name")
            r_user = st.text_input("Username", key="reg_u")
            r_email = st.text_input("Email")
            r_pass = st.text_input("Password", type="password", key="reg_p")
            r_role = st.selectbox("Role", ["student", "teacher"])
            if st.button("Register →", use_container_width=True):
                if r_name and r_user and r_pass:
                    ok, msg = db.register_user(r_user, r_pass, r_name, r_email, r_role)
                    if ok:
                        st.success(msg + " Please login.")
                    else:
                        st.error(msg)
                else:
                    st.warning("Please fill all required fields.")

def page_home():
    st.markdown("# 🏠 Dashboard")
    stats = db.get_analytics()
    c1, c2, c3, c4 = st.columns(4)
    for col, val, label, icon in zip(
        [c1,c2,c3,c4],
        [stats["total_books"], stats["total_users"], stats["active_borrows"], stats["available_books"]],
        ["Total Books","Registered Users","Active Borrows","Books Available"],
        ["📚","👥","📤","✅"]
    ):
        with col:
            st.markdown(f"""<div class="metric-card">
  <div class="value">{val:,}</div>
  <div style="font-size:1.5rem">{icon}</div>
  <div class="label">{label}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🔥 Featured Books")
    featured = db.get_books(limit=6)
    cols = st.columns(3)
    for i, book in enumerate(featured):
        with cols[i % 3]:
            render_book_card(book)

    st.markdown("---")
    st.markdown("### 🤖 AI Features at a Glance")
    feat_cols = st.columns(3)
    features = [
        ("🔍 Semantic Search", "Search by meaning, not just keywords. Ask 'machine learning for beginners' and find perfect matches."),
        ("⭐ Smart Recommendations", "AI learns your reading patterns and suggests books tailored to your interests."),
        ("💬 AI Chatbot", "Chat with LibraBot, your intelligent library assistant. Ask anything about books or topics."),
        ("🌍 Multilingual Search", "Search in Amharic, French, Spanish or any language — AI translates for you."),
        ("📊 Analytics Dashboard", "Real-time insights on borrowing trends, popular categories, and user activity."),
        ("🎮 AI Multiplay", "Multi-step AI: search + explain + recommend in one powerful query."),
    ]
    for i, (title, desc) in enumerate(features):
        with feat_cols[i % 3]:
            st.markdown(f"""<div class="book-card" style="margin-bottom:0.8rem">
  <div style="font-size:1.5rem;margin-bottom:0.4rem">{title.split(' ')[0]}</div>
  <div style="font-weight:600;margin-bottom:0.3rem">{' '.join(title.split(' ')[1:])}</div>
  <div style="font-size:0.82rem;color:#a7a9be">{desc}</div>
</div>""", unsafe_allow_html=True)

def page_search():
    st.markdown("# 🔍 Semantic Book Search")
    st.markdown("*Search by meaning — describe what you're looking for in natural language*")

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        query = st.text_input("", placeholder="e.g. 'machine learning for beginners' or 'mystery thriller set in Africa'", label_visibility="collapsed")
    with col2:
        cats = ["All Categories"] + db.get_categories()
        cat_filter = st.selectbox("Category", cats, label_visibility="collapsed")
    with col3:
        top_k = st.selectbox("Results", [5, 10, 15, 20], index=1, label_visibility="collapsed")

    if query:
        cf = None if cat_filter == "All Categories" else cat_filter
        with st.spinner("🔍 Searching with AI…"):
            results = ai.semantic_search(query, top_k=top_k, category_filter=cf)

        if results:
            st.markdown(f"**{len(results)} results found** for *\"{query}\"*")
            cols = st.columns(2)
            for i, book in enumerate(results):
                with cols[i % 2]:
                    score = book.get("score", 0)
                    st.markdown(f"""<div class="book-card">
  <div style="display:flex;gap:0.8rem;align-items:flex-start">
    {book_thumbnail(book.get('thumbnail',''), 65)}
    <div style="flex:1">
      <div style="font-family:'Playfair Display',serif;font-size:0.95rem;font-weight:700;color:#fffffe">{truncate(book['title'],52)}</div>
      <div style="font-size:0.78rem;color:#a7a9be">{truncate(book.get('authors',''),38)}</div>
      <div style="color:#ffd166;font-size:0.8rem">{rating_stars(float(book.get('average_rating') or 0))}</div>
      <div style="margin-top:4px">{"".join(f'<span class="badge badge-cat">{c.strip()}</span> ' for c in str(book.get('categories','')).split(',')[:2] if c.strip() and c.strip()!='nan')}</div>
    </div>
  </div>
  <div style="margin-top:0.4rem;font-size:0.78rem;color:#a7a9be">{truncate(book.get('description',''),120)}</div>
  <div style="margin-top:0.5rem"><div class="score-bar" style="width:{int(score*100)}%"></div>
  <div style="font-size:0.72rem;color:#a7a9be;margin-top:2px">Relevance: {int(score*100)}%</div></div>
</div>""", unsafe_allow_html=True)
                    if st.session_state.user:
                        b1, b2 = st.columns(2)
                        with b1:
                            if st.button("📖 Borrow", key=f"s_borrow_{i}"):
                                ok, msg = db.borrow_book(st.session_state.user["id"], book["book_id"])
                                st.toast(msg, icon="✅" if ok else "❌")
                                db.add_reading_history(st.session_state.user["id"], book["book_id"], book.get("categories",""))
                        with b2:
                            if st.button("✨ AI Summary", key=f"s_sum_{i}"):
                                with st.spinner("Generating summary…"):
                                    summary = ai_summarize_book(book)
                                st.info(summary)
        else:
            st.warning("No matching books found. Try a different query.")

def page_ai_multiplay():
    st.markdown("# 🎮 AI Multiplay")
    st.markdown("*Multi-step AI: search + deep analysis + recommendations in one powerful flow*")

    tab1, tab2, tab3 = st.tabs(["🔍 Smart Search + Explain", "🌍 Multilingual Search", "🧠 Topic Deep Dive"])

    with tab1:
        st.markdown("### Ask anything — AI searches, explains, and recommends")
        q = st.text_input("Your query:", placeholder="e.g. 'I want to learn data science from scratch'")
        if st.button("🚀 AI Multiplay Search", type="primary"):
            if q:
                with st.spinner("🤖 AI is thinking…"):
                    results = ai.semantic_search(q, top_k=8)
                    ai_response = multiplay_ai_query(q, results)

                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown("#### 🤖 AI Analysis")
                    st.markdown(f"""<div class="chat-msg-bot" style="max-width:100%;padding:1rem">{ai_response}</div>""", unsafe_allow_html=True)
                with col2:
                    st.markdown("#### 📚 Top Matches")
                    for b in results[:4]:
                        st.markdown(f"""<div class="book-card" style="margin-bottom:0.5rem;padding:0.7rem">
  <div style="font-family:'Playfair Display',serif;font-size:0.85rem;font-weight:700;color:#fffffe">{truncate(b['title'],40)}</div>
  <div style="font-size:0.75rem;color:#a7a9be">{truncate(b.get('authors',''),30)}</div>
  <div style="font-size:0.75rem;color:#ff6b35">Relevance: {int(b['score']*100)}%</div>
</div>""", unsafe_allow_html=True)
                        if st.session_state.user and st.button("Borrow", key=f"mp_b_{b['book_id']}"):
                            ok, msg = db.borrow_book(st.session_state.user["id"], b["book_id"])
                            st.toast(msg, icon="✅" if ok else "❌")

    with tab2:
        st.markdown("### 🌍 Search in Any Language")
        st.markdown("Type your query in Amharic, French, Arabic, Spanish, or any language!")
        ml_query = st.text_input("Multilingual query:", placeholder="ስለ ሜሽን ለርኒንግ መጽሐፍ ፈልጌ ነበር / Je cherche des livres sur l'IA / أبحث عن كتب علم الحاسوب")
        if st.button("🌍 Search Across Languages"):
            if ml_query:
                with st.spinner("🤖 Detecting language and translating…"):
                    lang, en_query, results = ai_translate_and_search(ml_query)
                st.success(f"🌐 Detected: **{lang}** → Searched as: *\"{en_query}\"*")
                if results:
                    cols = st.columns(2)
                    for i, b in enumerate(results[:6]):
                        with cols[i % 2]:
                            st.markdown(f"""<div class="book-card">
  <div style="font-family:'Playfair Display',serif;font-size:0.9rem;font-weight:700;color:#fffffe">{truncate(b['title'],50)}</div>
  <div style="font-size:0.78rem;color:#a7a9be">{b.get('authors','')}</div>
  <div style="font-size:0.75rem;color:#ff6b35;margin-top:4px">Relevance: {int(b['score']*100)}%</div>
</div>""", unsafe_allow_html=True)
                else:
                    st.warning("No results found.")

    with tab3:
        st.markdown("### 🧠 Topic Deep Dive")
        st.markdown("Enter any topic and AI will explain it + find relevant books")
        topic = st.text_input("Topic:", placeholder="e.g. Neural Networks, Ethiopian History, Quantum Computing")
        if st.button("🧠 Deep Dive", type="primary"):
            if topic:
                col1, col2 = st.columns([1.2, 1])
                with col1:
                    with st.spinner("AI is explaining…"):
                        explanation = ai_explain_topic(topic)
                    st.markdown("#### 📖 AI Explanation")
                    st.markdown(f"""<div class="chat-msg-bot" style="max-width:100%;padding:1rem">{explanation}</div>""", unsafe_allow_html=True)
                with col2:
                    with st.spinner("Searching related books…"):
                        books = ai.semantic_search(topic, top_k=5)
                    st.markdown("#### 📚 Related Books")
                    for b in books:
                        st.markdown(f"""<div class="book-card" style="margin-bottom:0.5rem;padding:0.7rem">
  <div style="font-weight:700;font-size:0.85rem">{truncate(b['title'],42)}</div>
  <div style="font-size:0.75rem;color:#a7a9be">{truncate(b.get('authors',''),35)}</div>
</div>""", unsafe_allow_html=True)
                        if st.session_state.user and st.button("📖", key=f"dd_b_{b['book_id']}"):
                            ok, msg = db.borrow_book(st.session_state.user["id"], b["book_id"])
                            st.toast(msg, icon="✅" if ok else "❌")

def page_chatbot():
    st.markdown("# 💬 LibraBot — AI Library Assistant")
    st.markdown("*Ask anything about books, topics, recommendations, or library policies*")

    # Chat display
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_history:
            st.markdown("""<div class="chat-msg-bot">
👋 Hello! I'm <strong>LibraBot</strong>, your AI library assistant at Wolaita Sodo University.<br><br>
I can help you:
<ul style="margin:0.5rem 0;padding-left:1.2rem">
  <li>Find books on any topic</li>
  <li>Get book recommendations</li>
  <li>Explain academic concepts</li>
  <li>Answer library policy questions</li>
  <li>Chat in multiple languages 🌍</li>
</ul>
What can I help you with today?
</div>""", unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            css_class = "chat-msg-user" if msg["role"] == "user" else "chat-msg-bot"
            prefix = "" if msg["role"] == "user" else "🤖 "
            st.markdown(f'<div class="{css_class}">{prefix}{msg["content"]}</div>', unsafe_allow_html=True)

    # Quick prompts
    st.markdown("**Quick prompts:**")
    qp_cols = st.columns(4)
    quick_prompts = [
        "Recommend Machine Learning books",
        "Best fiction novels in the library",
        "Explain FAISS vector search",
        "Library borrowing rules",
    ]
    for i, qp in enumerate(quick_prompts):
        with qp_cols[i]:
            if st.button(qp, key=f"qp_{i}"):
                st.session_state.chat_history.append({"role":"user","content":qp})
                with st.spinner("LibraBot is thinking…"):
                    reply = chat_with_ai(qp, st.session_state.chat_history[:-1])
                st.session_state.chat_history.append({"role":"assistant","content":reply})
                st.rerun()

    # Input
    col1, col2 = st.columns([5, 1])
    with col1:
        user_input = st.text_input("", placeholder="Type your message…", key="chat_input", label_visibility="collapsed")
    with col2:
        send = st.button("Send →", use_container_width=True)

    if (send or user_input) and user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.spinner("🤖 LibraBot is thinking…"):
            reply = chat_with_ai(user_input, st.session_state.chat_history[:-1])
        st.session_state.chat_history.append({"role": "assistant", "content": reply})
        st.rerun()

    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

def page_recommendations():
    st.markdown("# ⭐ AI Book Recommendations")
    user_id = st.session_state.user["id"]
    user_cats = db.get_user_history_categories(user_id)
    borrows = db.get_user_borrows(user_id)
    borrowed_ids = [b["book_id"] for b in borrows]

    if user_cats:
        st.markdown(f"*Based on your reading history across: {', '.join(set(user_cats[:5]))}*")
    else:
        st.markdown("*Showing popular books — borrow more books to get personalised recommendations!*")

    with st.spinner("🤖 Generating recommendations…"):
        recs = ai.get_recommendations(user_cats, exclude_ids=borrowed_ids, top_k=8)

    if recs:
        cols = st.columns(2)
        for i, book in enumerate(recs):
            full_book = db.get_book_by_id(book["book_id"])
            if full_book:
                with cols[i % 2]:
                    render_book_card(full_book)
    else:
        st.info("No recommendations yet. Start borrowing books!")

    # Similar books section
    if borrows:
        st.markdown("---")
        st.markdown("### 📖 More Like What You've Read")
        last_borrow = borrows[0]
        similar = ai.get_similar_books(last_borrow["book_id"], top_k=4)
        if similar:
            cols = st.columns(4)
            for i, b in enumerate(similar):
                full_book = db.get_book_by_id(b["book_id"])
                if full_book:
                    with cols[i % 4]:
                        render_book_card(full_book)

def page_my_books():
    st.markdown("# 📖 My Books")
    user_id = st.session_state.user["id"]
    borrows = db.get_user_borrows(user_id)

    active = [b for b in borrows if b["status"] == "borrowed"]
    returned = [b for b in borrows if b["status"] == "returned"]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="value">{len(active)}</div><div class="label">Currently Borrowed</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="value">{len(returned)}</div><div class="label">Books Returned</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="value">{len(borrows)}</div><div class="label">Total Borrowed</div></div>""", unsafe_allow_html=True)

    tab1, tab2 = st.tabs([f"📤 Active ({len(active)})", f"✅ History ({len(returned)})"])
    with tab1:
        if active:
            for b in active:
                due = b.get("due_date","")[:10]
                overdue = due < datetime.now().strftime("%Y-%m-%d") if due else False
                st.markdown(f"""<div class="book-card" style="margin-bottom:0.7rem;display:flex;gap:1rem;align-items:center">
  {book_thumbnail(b.get('thumbnail',''),55)}
  <div style="flex:1">
    <div style="font-weight:700">{b['title']}</div>
    <div style="font-size:0.8rem;color:#a7a9be">{b.get('authors','')}</div>
    <div style="font-size:0.8rem;color:{'#ef4565' if overdue else '#2cb67d'}">
      {'⚠️ OVERDUE' if overdue else '📅 Due'}: {due}
    </div>
  </div>
</div>""", unsafe_allow_html=True)
                if st.button(f"↩️ Return", key=f"ret_{b['id']}"):
                    db.return_book(b["id"], b["book_id"])
                    st.toast("Book returned successfully!", icon="✅")
                    st.rerun()
        else:
            st.info("No active borrows. Visit the Search page to find books!")
    with tab2:
        if returned:
            for b in returned:
                st.markdown(f"""<div class="book-card" style="margin-bottom:0.5rem;padding:0.8rem;display:flex;gap:0.8rem;align-items:center">
  {book_thumbnail(b.get('thumbnail',''),50)}
  <div>
    <div style="font-weight:600">{b['title']}</div>
    <div style="font-size:0.78rem;color:#a7a9be">Returned: {str(b.get('return_date',''))[:10]}</div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("No returned books yet.")

def page_analytics():
    st.markdown("# 📊 Library Analytics Dashboard")
    stats = db.get_analytics()

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    for col, val, label in zip(
        [c1,c2,c3,c4],
        [stats["total_books"], stats["total_users"], stats["active_borrows"], stats["available_books"]],
        ["Total Books","Users","Active Borrows","Available Copies"]
    ):
        with col:
            st.markdown(f"""<div class="metric-card"><div class="value">{val:,}</div><div class="label">{label}</div></div>""", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📚 Most Borrowed Books")
        if stats["top_books"]:
            df_top = pd.DataFrame(stats["top_books"])
            fig = px.bar(df_top, x="cnt", y="title", orientation="h",
                        labels={"cnt":"Borrows","title":""},
                        color="cnt", color_continuous_scale=["#252438","#ff6b35"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                             font_color="#fffffe", showlegend=False, height=300,
                             margin=dict(l=0,r=0,t=10,b=0))
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("#### 🏷️ Category Distribution")
        if stats["cat_dist"]:
            df_cat = pd.DataFrame(stats["cat_dist"])
            df_cat = df_cat[df_cat["categories"].str.len() < 40]
            fig2 = px.pie(df_cat.head(10), names="categories", values="cnt",
                         color_discrete_sequence=px.colors.sequential.Oranges_r)
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#fffffe", height=300,
                              margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### 📅 Borrowing Activity (Last 30 Days)")
    if stats["monthly"]:
        df_monthly = pd.DataFrame(stats["monthly"])
        fig3 = px.area(df_monthly, x="day", y="cnt",
                      labels={"day":"Date","cnt":"Borrows"},
                      color_discrete_sequence=["#ff6b35"])
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#fffffe", height=200, margin=dict(l=0,r=0,t=10,b=0))
        fig3.update_xaxes(gridcolor="rgba(255,255,255,0.05)")
        fig3.update_yaxes(gridcolor="rgba(255,255,255,0.05)")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No borrowing activity yet. Activity chart will appear once books are borrowed.")

def page_users():
    st.markdown("# 👥 User Management")
    users = db.get_all_users()
    df_users = pd.DataFrame(users)
    if not df_users.empty:
        df_users = df_users.drop(columns=["password"], errors="ignore")
        st.dataframe(df_users, use_container_width=True, hide_index=True)
    st.markdown(f"**Total users: {len(users)}**")

def page_all_borrows():
    st.markdown("# 📋 All Borrow Records")
    borrows = db.get_all_borrows()
    if borrows:
        df_b = pd.DataFrame(borrows)
        df_b["borrow_date"] = df_b["borrow_date"].str[:10]
        df_b["due_date"] = df_b["due_date"].str[:10]
        active_mask = df_b["status"] == "borrowed"
        st.markdown(f"**Active: {active_mask.sum()} · Returned: {(~active_mask).sum()} · Total: {len(df_b)}**")
        st.dataframe(df_b[["id","username","full_name","title","borrow_date","due_date","status"]],
                     use_container_width=True, hide_index=True)
    else:
        st.info("No borrow records yet.")

# ── Main router ───────────────────────────────────────────────────────────────
def main():
    render_sidebar()

    if not st.session_state.user:
        page_login()
        return

    page = st.session_state.page
    if page == "home":       page_home()
    elif page == "search":   page_search()
    elif page == "ai_multiplay": page_ai_multiplay()
    elif page == "chatbot":  page_chatbot()
    elif page == "recommendations": page_recommendations()
    elif page == "my_books": page_my_books()
    elif page == "analytics": page_analytics()
    elif page == "users":    page_users()
    elif page == "all_borrows": page_all_borrows()
    else: page_home()

if __name__ == "__main__":
    main()
