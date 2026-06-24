# app.py
#
# Streamlit entry point — Pure UI Orchestration Layer.
# Now implements the Brutalist Editorial Design System.
#
# Run with:  streamlit run app.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from datetime import datetime

import config
from utils.logger import logger
from utils.startup_check import verify_system_health

from core.pdf_processor import build_vector_store, get_retriever
from core.chat_engine import build_chat_engine, create_conversation_chain, ask, rebuild_memory_from_messages
from core.summarizer import summarize_documents
from core.citations import format_citations
from core.pdf_exporter import generate_pdf_report
from core.document_comparator import compare_documents
from core.session_manager import session_db
from core.auth_manager import auth_manager
from core.ui_design_system import CSS_STYLES
from core.ui_renderer import render_message, render_typing_indicator, render_citations
from core.collection_manager import (
    create_collection,
    list_collections,
    rename_collection,
    archive_collection,
    get_metadata,
)
from core.document_storage import list_collection_files
from core.search_manager import global_search
from core.analytics_manager import get_analytics
import core.source_viewer

# ── Deployment Readiness Check ────────────────────────────────────────────────────
# We run this before the UI initializes to ensure the environment is stable.
if not verify_system_health():
    st.error("🚀 System Health Check Failed. Please check logs for details.")
    st.stop()

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject the Brutalist Design System
st.markdown(CSS_STYLES, unsafe_allow_html=True)

# ── Session-state initialisation ─────────────────────────────────────────────
def _init_session():
    defaults = {
        "user": None,
        "chat_history": [],
        "chain": None,
        "processed_files": [],
        "summary": None,
        "comparison": None,
        "current_session_id": None,
        "session_rename_target": None,
        "session_rename_value": "",
        "collection_rename_target": None,
        "collection_rename_value": "",
        "active_collection_id": None,
        "new_collection_name": "",
        "show_new_library": False,
        "source_panel_open": False,
        "active_source_index": None,
        "search_query": "",
        "search_results": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session()

def _switch_session(session_id: int):
    """Loads history from DB and updates the RAG chain's memory."""
    try:
        user_id = st.session_state.user.id
        st.session_state.current_session_id = session_id
        st.session_state.session_rename_target = None
        st.session_state.source_panel_open = False
        st.session_state.active_source_index = None
        history = session_db.load_messages(session_id, user_id)
        st.session_state.chat_history = history

        collection_id = None
        with session_db._get_connection() as conn:
            row = conn.execute(
                "SELECT collection_id FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        if row and row["collection_id"] is not None:
            collection_id = row["collection_id"]
            st.session_state.active_collection_id = collection_id
        else:
            st.session_state.active_collection_id = None

        if collection_id:
            from core.vectorstore_manager import load_or_build_collection_vectorstore
            from core.document_storage import list_collection_files
            try:
                vector_store = load_or_build_collection_vectorstore(user_id, collection_id)
                st.session_state.chain = create_conversation_chain(vector_store)
                st.session_state.processed_files = list_collection_files(user_id, collection_id)
                if st.session_state.chain and history:
                    st.session_state.chain = rebuild_memory_from_messages(st.session_state.chain, history)
            except Exception as e:
                logger.warning(f"Collection vectorstore load/build failed: {e}")
                st.session_state.chain = None
                st.session_state.processed_files = []
        else:
            if st.session_state.chain:
                st.session_state.chain = rebuild_memory_from_messages(st.session_state.chain, history)
            st.session_state.processed_files = []

        logger.info(f"Session switched to {session_id} for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to switch session: {e}")
        st.error("Error loading chat session.")

# ── Authentication Flow ──────────────────────────────────────────────────────
def auth_screen():
    """Renders the login/signup interface."""
    st.markdown('<div class="auth-center">', unsafe_allow_html=True)
    st.markdown(f'<div class="auth-title">{config.APP_TITLE}</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-subtitle">Analysis Engine</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Sign In", use_container_width=True):
            try:
                user, error = auth_manager.sign_in(email, password)
                if error:
                    st.error(error)
                elif user:
                    st.session_state.user = user
                    session_db.ensure_user_exists(user.id, user.email)
                    logger.info(f"User {user.email} authenticated successfully.")
                    st.rerun()
            except Exception as e:
                logger.exception(f"Auth error during sign-in: {e}")
                st.error("A critical authentication error occurred.")

    with tab2:
        s_email = st.text_input("Email", key="signup_email")
        s_password = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Create Account", use_container_width=True):
            try:
                user, error = auth_manager.sign_up(s_email, s_password)
                if error:
                    st.error(error)
                elif user:
                    st.session_state.user = user
                    session_db.ensure_user_exists(user.id, user.email)
                    st.success("Account created! Please log in.")
                    logger.info(f"New user account created: {user.email}")
                    st.rerun()
            except Exception as e:
                logger.exception(f"Auth error during sign-up: {e}")
                st.error("A critical error occurred while creating the account.")

    st.markdown('</div>', unsafe_allow_html=True)

# ── Main Application ──────────────────────────────────────────────────────────
def main_app():
    with st.sidebar:
        user_email = st.session_state.user.email
        user_id = st.session_state.user.id
        
        # Search
        st.markdown('<div class="dockmind-section">Search</div>', unsafe_allow_html=True)
        
        def on_search_change():
            q = st.session_state.search_sidebar
            if q.strip():
                with st.spinner("Searching…"):
                    st.session_state.search_query = q
                    st.session_state.search_results = global_search(user_id, q, st.session_state.active_collection_id)
            else:
                st.session_state.search_query = ""
                st.session_state.search_results = None
        
        search_query = st.text_input("Search", key="search_sidebar", placeholder="Search documents, conversations…", label_visibility="collapsed", on_change=on_search_change)
        
        if st.session_state.get("search_results") and st.session_state.get("search_query"):
            results = st.session_state.search_results
            q = st.session_state.search_query
            st.markdown(f'<div class="dockmind-meta dockmind-spacer-bottom">Results for: <strong>{q}</strong></div>', unsafe_allow_html=True)
            if st.button("Clear Search", use_container_width=True):
                st.session_state.search_query = ""
                st.session_state.search_results = None
                st.session_state.search_sidebar = ""
                st.rerun()
            if not any(results.values()):
                st.markdown('<div class="dockmind-meta">No results.</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="dockmind-divider"></div>', unsafe_allow_html=True)
        
        # Context
        st.markdown('<div class="dockmind-section">Context</div>', unsafe_allow_html=True)
        collections = list_collections(user_id, include_archived=False)
        active_collections = [c for c in collections if c["id"] == st.session_state.active_collection_id]
        if active_collections:
            ctx_parts = [c["name"] for c in active_collections]
            st.markdown(f'<div class="dockmind-workspace">{" · ".join(ctx_parts)}</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="dockmind-divider"></div>', unsafe_allow_html=True)
        
        # Libraries
        st.markdown('<div class="dockmind-section">Knowledge</div>', unsafe_allow_html=True)
        if not collections:
            st.markdown('<div class="dockmind-meta dockmind-faded">Create your first library.</div>', unsafe_allow_html=True)
        for col in collections:
            meta = get_metadata(col["id"])
            doc_count = meta.get("document_count", 0) if meta else 0
            is_active = st.session_state.active_collection_id == col["id"]
            
            cols = st.columns([3, 1])
            with cols[0]:
                if st.button(col["name"], key=f"col_{col['id']}", use_container_width=True):
                    with st.spinner("Loading…"):
                        st.session_state.active_collection_id = col["id"]
                        st.session_state.collection_rename_target = None
                        st.session_state.source_panel_open = False
                        st.session_state.active_source_index = None
                        st.rerun()
            with cols[1]:
                if is_active:
                    if st.button("⋯", key=f"menu_col_{col['id']}", help="Actions"):
                        st.session_state.collection_rename_target = col["id"]
                        st.session_state.collection_rename_value = col["name"]
                        st.rerun()
            
            if is_active and st.session_state.get("collection_rename_target") == col["id"]:
                new_name = st.text_input("Rename", value=st.session_state.collection_rename_value, key="rename_col_input", label_visibility="collapsed")
                if st.button("Save", use_container_width=True):
                    rename_collection(col["id"], user_id, new_name)
                    st.session_state.collection_rename_target = None
                    st.rerun()
            st.markdown(f'<div class="dockmind-meta">{doc_count} documents</div>', unsafe_allow_html=True)
        
        if st.button("New Library", use_container_width=True, key="new_library"):
            st.session_state.show_new_library = True
        
        if st.session_state.get("show_new_library"):
            new_col_name = st.text_input("Library name", key="new_collection_name", label_visibility="collapsed")
            if st.button("Create", use_container_width=True):
                if new_col_name.strip():
                    cid = create_collection(user_id, new_col_name.strip())
                    from core.collection_manager import ensure_metadata_exists
                    ensure_metadata_exists(cid)
                    st.session_state.active_collection_id = cid
                    st.session_state.show_new_library = False
                    st.rerun()
        
        st.markdown('<div class="dockmind-divider"></div>', unsafe_allow_html=True)
        
        # Conversations
        st.markdown('<div class="dockmind-section">Conversations</div>', unsafe_allow_html=True)
        sessions = session_db.list_sessions(user_id)
        if sessions:
            collection_sessions = {}
            legacy_sessions = []
            for s in sessions:
                cid = s.get("collection_id")
                if cid is not None:
                    collection_sessions.setdefault(cid, []).append(s)
                else:
                    legacy_sessions.append(s)
            
            for cid, c_sessions in collection_sessions.items():
                for s in c_sessions:
                    is_active = st.session_state.current_session_id == s["id"]
                    cols = st.columns([3, 1])
                    with cols[0]:
                        if st.button(s["name"], key=f"sess_{s['id']}", use_container_width=True):
                            with st.spinner("Loading…"):
                                _switch_session(s["id"])
                                st.rerun()
                    with cols[1]:
                        if is_active or st.session_state.session_rename_target == s["id"]:
                            if st.button("⋯", key=f"menu_sess_{s['id']}", help="Actions"):
                                st.session_state.session_rename_target = s["id"] if st.session_state.session_rename_target != s["id"] else None
                                st.rerun()
                    
                    if st.session_state.session_rename_target == s["id"]:
                        new_name = st.text_input("Rename", value=s["name"], key="rename_input", label_visibility="collapsed")
                        if st.button("Save", use_container_width=True):
                            session_db.rename_session(s["id"], user_id, new_name)
                            st.session_state.session_rename_target = None
                            st.rerun()
            
            if legacy_sessions:
                for s in legacy_sessions:
                    is_active = st.session_state.current_session_id == s["id"]
                    cols = st.columns([3, 1])
                    with cols[0]:
                        if st.button(s["name"], key=f"sess_{s['id']}", use_container_width=True):
                            with st.spinner("Loading…"):
                                _switch_session(s["id"])
                                st.rerun()
                    with cols[1]:
                        if is_active or st.session_state.session_rename_target == s["id"]:
                            if st.button("⋯", key=f"menu_sess_{s['id']}", help="Actions"):
                                st.session_state.session_rename_target = s["id"] if st.session_state.session_rename_target != s["id"] else None
                                st.rerun()
                    
                    if st.session_state.session_rename_target == s["id"]:
                        new_name = st.text_input("Rename", value=s["name"], key="rename_input", label_visibility="collapsed")
                        if st.button("Save", use_container_width=True):
                            session_db.rename_session(s["id"], user_id, new_name)
                            st.session_state.session_rename_target = None
                            st.rerun()
        else:
            st.markdown('<div class="dockmind-meta dockmind-faded">Start a conversation.</div>', unsafe_allow_html=True)
        
        if st.button("New Conversation", use_container_width=True, key="new_conversation"):
            session_name = f"Conversation {len(sessions) + 1}"
            cid = st.session_state.active_collection_id
            new_id = session_db.create_session(user_id, session_name, collection_id=cid)
            st.session_state.session_rename_target = None
            st.session_state.collection_rename_target = None
            _switch_session(new_id)
            st.rerun()
        
        st.markdown('<div class="dockmind-divider"></div>', unsafe_allow_html=True)
        
        # Insights
        st.markdown('<div class="dockmind-section">Overview</div>', unsafe_allow_html=True)
        analytics = get_analytics(user_id)
        st.markdown(f'<div class="dockmind-meta">{analytics["total_documents"]} documents</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="dockmind-meta">{analytics["total_collections"]} libraries</div>', unsafe_allow_html=True)
        if analytics.get("top_collection"):
            st.markdown(f'<div class="dockmind-meta dockmind-spacer-top">{analytics["top_collection"]["name"]}</div>', unsafe_allow_html=True)
        if analytics.get("last_active"):
            try:
                ts = datetime.fromisoformat(analytics["last_active"]).strftime("%b %d, %I:%M %p")
            except Exception:
                ts = analytics["last_active"]
            st.markdown(f'<div class="dockmind-meta dockmind-spacer-top">Updated {ts}</div>', unsafe_allow_html=True)
        
        if st.button("Logout", use_container_width=True, key="logout"):
            try:
                auth_manager.sign_out()
                st.session_state.user = None
                logger.info(f"User {user_email} signed out.")
                st.rerun()
            except Exception as e:
                logger.error(f"Logout error: {e}")
                st.error("Logout failed.")

    # ── Main Area: The Editorial Canvas ──────────────────────────────────────────
    st.markdown('<div class="dockmind-canvas">', unsafe_allow_html=True)
    st.markdown(f'<div class="editorial-title">{config.APP_TITLE}</div>', unsafe_allow_html=True)

    if st.session_state.summary:
        with st.expander("Summary Analysis"):
            s = st.session_state.summary
            st.markdown(f"**Overview:** {s.get('short_summary', 'N/A')}")
            st.markdown(f"**Detailed:** {s.get('detailed_summary', 'N/A')}")

    if st.session_state.comparison:
        with st.expander("Document Comparison"):
            c = st.session_state.comparison
            st.markdown(f"**Executive Summary:** {c.get('executive_summary', 'N/A')}")

    st.markdown(f'<div class="dockmind-section">Conversation</div>', unsafe_allow_html=True)
    st.divider()

    # Render Chat History
    for message in st.session_state.chat_history:
        st.markdown(render_message(message["role"], message["content"]), unsafe_allow_html=True)
    
    # Render citation sources
    if hasattr(st.session_state, 'current_citations') and st.session_state.current_citations:
        citations = st.session_state.current_citations
        st.markdown('<div class="dockmind-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="dockmind-section">Sources</div>', unsafe_allow_html=True)
        
        for idx, cite in enumerate(citations):
            display_name = core.source_viewer.humanize_filename(cite.get("filename", ""))
            page = cite.get("page", "?")
            snippet = (cite.get("snippet", "") or "")[:80]
            
            is_active = st.session_state.get("source_panel_open") and st.session_state.get("active_source_index") == idx
            
            if st.button(
                f"{display_name}    p.{page}",
                key=f"cite_{idx}",
                use_container_width=True,
                help=snippet if snippet else None
            ):
                if st.session_state.get("source_panel_open") and st.session_state.get("active_source_index") == idx:
                    st.session_state.source_panel_open = False
                    st.session_state.active_source_index = None
                else:
                    st.session_state.source_panel_open = True
                    st.session_state.active_source_index = idx
                st.rerun()
        
        # Render inspector panel
        if st.session_state.get("source_panel_open") and st.session_state.get("active_source_index") is not None:
            from core.source_viewer import get_active_source, render_source_panel
            active = get_active_source(citations, st.session_state.active_source_index)
            if active:
                st.markdown('<div class="dockmind-divider"></div>', unsafe_allow_html=True)
                st.markdown(render_source_panel(active), unsafe_allow_html=True)

    user_question = st.chat_input(config.CHAT_PLACEHOLDER, disabled=st.session_state.chain is None)

    if user_question:
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        if st.session_state.current_session_id:
            try:
                session_db.save_message(st.session_state.current_session_id, "user", user_question)
            except Exception as e:
                logger.exception(f"DB Save Error (user): {e}")

        # Auto-name session from first user message
        if st.session_state.current_session_id:
            try:
                with session_db._get_connection() as conn:
                    row = conn.execute(
                        "SELECT name FROM sessions WHERE id = ?", (st.session_state.current_session_id,)
                    ).fetchone()
                if row and row["name"].startswith("Chat "):
                    new_title = user_question[:60]
                    if len(user_question) > 60:
                        last_space = new_title.rfind(' ')
                        if last_space > 35:
                            new_title = new_title[:last_space]
                        new_title = new_title.rstrip() + "…"
                    session_db.rename_session(st.session_state.current_session_id, user_id, new_title)
            except Exception as e:
                logger.exception(f"Auto-naming error: {e}")

        with st.empty():
            st.markdown(render_typing_indicator(), unsafe_allow_html=True)
            try:
                response = ask(st.session_state.chain, user_question)
                answer = response["answer"]
                source_docs = response.get("source_documents", [])
                citations = format_citations(source_docs)
                st.session_state.current_citations = citations
                
                # Store only the answer in history; citations render separately
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                if st.session_state.current_session_id:
                    session_db.save_message(st.session_state.current_session_id, "assistant", answer)
                logger.info(f"AI Response successfully generated for user {user_id}")
            except Exception as e:
                logger.exception(f"AI Inference Error: {e}")
                st.session_state.chat_history.append({"role": "assistant", "content": f"Error: The AI engine encountered a problem. Please try rephrasing."})
            st.empty()

    if st.session_state.chain is None:
        st.markdown('<div class="empty-state"><p>Upload documents to initialize the analysis engine.</p></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ── Entry Point ─────────────────────────────────────────────────────────────────
if st.session_state.user is None:
    st.markdown('<div id="brutalist-root">', unsafe_allow_html=True)
    auth_screen()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div id="brutalist-root">', unsafe_allow_html=True)
    main_app()
    st.markdown('</div>', unsafe_allow_html=True)
