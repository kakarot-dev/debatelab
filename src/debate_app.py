"""Simple Streamlit interface for the DebateLab system."""

import sys
import os
sys.path.append(os.path.abspath("."))

import streamlit as st
import tempfile
import time
from datetime import datetime
from src.debate_manager import DebateManager
from src.config import MODEL_PATH, AGENT_PERSONALITIES

def apply_custom_css():
    """Apply custom CSS styling - called after page config."""
    st.markdown("""<style>
    /* Global background with modern dark theme */
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        min-height: 100vh;
    }
    
    .main .block-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2.5rem;
        backdrop-filter: blur(20px);
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.3),
            0 0 0 1px rgba(255, 255, 255, 0.05),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
        margin: 1rem;
    }
    
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 3rem;
        letter-spacing: -0.02em;
        text-shadow: none;
    }
    
    .agent-message {
        padding: 1.5rem;
        margin: 1.2rem 0;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .agent-message::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: var(--agent-color);
        opacity: 0.8;
    }
    
    .agent-message:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.3);
    }
    
    .optimist-message {
        --agent-color: #10b981;
        background: linear-gradient(135deg, 
            rgba(16, 185, 129, 0.1) 0%, 
            rgba(5, 150, 105, 0.05) 100%);
        border-color: rgba(16, 185, 129, 0.2);
    }
    
    .skeptic-message {
        --agent-color: #f59e0b;
        background: linear-gradient(135deg, 
            rgba(245, 158, 11, 0.1) 0%, 
            rgba(217, 119, 6, 0.05) 100%);
        border-color: rgba(245, 158, 11, 0.2);
    }
    
    .ethicist-message {
        --agent-color: #8b5cf6;
        background: linear-gradient(135deg, 
            rgba(139, 92, 246, 0.1) 0%, 
            rgba(124, 58, 237, 0.05) 100%);
        border-color: rgba(139, 92, 246, 0.2);
    }
    
    .judge-message {
        --agent-color: #ef4444;
        background: linear-gradient(135deg, 
            rgba(239, 68, 68, 0.1) 0%, 
            rgba(220, 38, 38, 0.05) 100%);
        border-color: rgba(239, 68, 68, 0.2);
    }
    
    .moderator-message {
        --agent-color: #06b6d4;
        background: linear-gradient(135deg, 
            rgba(6, 182, 212, 0.1) 0%, 
            rgba(8, 145, 178, 0.05) 100%);
        border-color: rgba(6, 182, 212, 0.2);
    }
    
    .agent-name {
        font-weight: 700;
        font-size: 1.3rem;
        margin-bottom: 0.8rem;
        color: var(--agent-color);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .agent-name::before {
        content: '';
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--agent-color);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .debate-controls {
        background: transparent;
        border: none;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    
    .status-info {
        background: linear-gradient(135deg, 
            rgba(99, 102, 241, 0.1) 0%, 
            rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid rgba(99, 102, 241, 0.2);
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        text-align: center;
        font-weight: 600;
        color: #a5b4fc;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.1);
    }
    
    .stop-button {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.8rem 2.5rem !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        box-shadow: 0 4px 16px rgba(239, 68, 68, 0.4) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    
    .stop-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px rgba(239, 68, 68, 0.6) !important;
    }
    
    .progress-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 16px;
        margin: 1.5rem 0;
        backdrop-filter: blur(15px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
    }
    
    .system-message {
        background: linear-gradient(135deg, 
            rgba(156, 163, 175, 0.1) 0%, 
            rgba(107, 114, 128, 0.05) 100%);
        border: 1px solid rgba(156, 163, 175, 0.2);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        font-style: italic;
        color: #9ca3af;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(156, 163, 175, 0.1);
    }
    
    .loading-indicator {
        background: linear-gradient(135deg, 
            rgba(59, 130, 246, 0.1) 0%, 
            rgba(37, 99, 235, 0.05) 100%);
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.1);
        color: #93c5fd;
        animation: shimmer 2s infinite;
    }
    
    @keyframes shimmer {
        0% { opacity: 0.8; }
        50% { opacity: 1; }
        100% { opacity: 0.8; }
    }
    
    /* Additional loading animation styles */
    .generating-indicator {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 12px;
        background: linear-gradient(135deg,
            rgba(59, 130, 246, 0.1) 0%,
            rgba(147, 51, 234, 0.1) 100%);
        border: 1px solid rgba(59, 130, 246, 0.2);
        backdrop-filter: blur(10px);
    }
    
    .loading-text {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #64748b;
        font-style: italic;
    }
    
    .loading-animation {
        display: inline-flex;
        gap: 0.2rem;
    }
    
    .loading-animation .dot {
        animation: loading-dots 1.4s infinite ease-in-out;
        font-weight: bold;
        color: #3b82f6;
    }
    
    .loading-animation .dot:nth-child(1) { animation-delay: -0.32s; }
    .loading-animation .dot:nth-child(2) { animation-delay: -0.16s; }
    .loading-animation .dot:nth-child(3) { animation-delay: 0s; }
    
    @keyframes loading-dots {
        0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% {
            transform: scale(1.2);
            opacity: 1;
        }
    }
    
        /* Sidebar styling */
    .stSidebar {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(20px);
        box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.05);
    }
    
    /* Sidebar text styling */
    .stSidebar h1, .stSidebar h2, .stSidebar h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 1rem !important;
    }
    
    .stSidebar h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        font-size: 1.8rem !important;
    }
    
    .stSidebar p, .stSidebar div, .stSidebar span, .stSidebar label {
        color: #d1d5db !important;
        font-weight: 400 !important;
    }
    
    /* Sidebar button styling */
    .stSidebar .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%) !important;
        color: white !important;
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2) !important;
        backdrop-filter: blur(10px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.025em !important;
    }
    
    .stSidebar .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px rgba(59, 130, 246, 0.4) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
    }
    
    .stSidebar .stButton > button:active {
        transform: translateY(0) !important;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.3) !important;
    }
    
    /* Sidebar input styling */
    .stSidebar .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: #e5e7eb !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stSidebar .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: #e5e7eb !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .stSidebar .stTextInput > div > div > input:focus {
        border-color: rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    }
    
    /* Sidebar slider styling */
    .stSidebar .stSlider > div > div > div {
        background: rgba(59, 130, 246, 0.3) !important;
    }
    
    .stSidebar .stSlider > div > div > div > div {
        background: #3b82f6 !important;
        border: 2px solid #ffffff !important;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* Sidebar checkbox styling */
    .stSidebar .stCheckbox > label > div {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 4px !important;
    }
    
    .stSidebar .stCheckbox > label > div[data-checked="true"] {
        background: #3b82f6 !important;
        border-color: #3b82f6 !important;
    }
    
    /* Sidebar radio button styling */
    .stSidebar .stRadio > div > label > div {
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    
    .stSidebar .stRadio > div > label > div[data-checked="true"] {
        border-color: #3b82f6 !important;
        background: rgba(59, 130, 246, 0.2) !important;
    }
    
    .stSidebar .stRadio > div > label > div[data-checked="true"]::before {
        background: #3b82f6 !important;
    }
                    /* Target the actual message content container */
    .stChatMessage > div {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(15px) !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1) !important;
        color: #e5e7eb !important;
        padding: 1rem !important; /* Reduce padding */
    }

    /* Remove default Streamlit padding/margin */
    .stChatMessage {
        margin-bottom: 0.5rem !important;
        padding: 0 !important;
    }

    /* Target the message content specifically */
    .stChatMessage [data-testid="stChatMessageContent"] {
        padding: 0.8rem !important; /* Smaller padding */
        margin: 0 !important;
    }

    /* Fix element container spacing */
    .stElementContainer {
        margin-bottom: 0.5rem !important;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        border-radius: 8px !important;
    }
    
    .stProgress > div > div {
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-top-color: #3b82f6 !important;
        border-right-color: transparent !important;
        border-bottom-color: transparent !important;
        border-left-color: transparent !important;
    }
    
    /* Alert styling */
    .stAlert {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1) !important;
        color: #e5e7eb !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        color: #e5e7eb !important;
        backdrop-filter: blur(10px) !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-top: none !important;
        backdrop-filter: blur(15px) !important;
        border-radius: 0 0 12px 12px !important;
        color: #d1d5db !important;
    }
    
    /* Text color improvements */
    .stApp, .stApp p, .stApp span, .stApp div {
        color: #e5e7eb;
    }
    
    /* Modern scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }
    
    /* Glowing effects for interactivity */
    .agent-message:hover .agent-name {
        text-shadow: 0 0 10px var(--agent-color);
    }
    
    /* Smooth transitions for all interactive elements */
    * {
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
</style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state."""
    if "debate_history" not in st.session_state:
        st.session_state.debate_history = []
    if "debate_running" not in st.session_state:
        st.session_state.debate_running = False
    if "uploaded_content" not in st.session_state:
        st.session_state.uploaded_content = None
    if "stop_debate" not in st.session_state:
        st.session_state.stop_debate = False

def process_uploaded_file(uploaded_file):
    """Process uploaded file and extract content."""
    try:
        # Try to use textract if available
        try:
            import textract
            
            with tempfile.NamedTemporaryFile(
                suffix="." + uploaded_file.name.split('.')[-1],
                delete=False
            ) as tmp:
                tmp.write(uploaded_file.getbuffer())
                tmp.flush()
                tmp_path = tmp.name
            
            text_bytes = textract.process(tmp_path)
            content = text_bytes.decode("utf-8", errors="ignore")
            content = " ".join(content.split())
            
            st.session_state.uploaded_content = {
                "filename": uploaded_file.name,
                "content": content[:2000]  # Limit content length
            }
            
            st.success(f"✅ File processed: {uploaded_file.name}")
            
        except ImportError:
            # Fallback for text files
            if uploaded_file.type == "text/plain":
                content = str(uploaded_file.read(), "utf-8")
                st.session_state.uploaded_content = {
                    "filename": uploaded_file.name,
                    "content": content[:2000]
                }
                st.success(f"✅ Text file processed: {uploaded_file.name}")
            else:
                st.warning("⚠️ textract not available. Only plain text files supported.")
                
    except Exception as e:
        st.error(f"❌ Error processing file: {e}")

def get_agent_avatar(agent_name: str) -> str:
    """Get emoji avatar for agent."""
    avatars = {
        "Alex the Optimist": "😊",
        "Sam the Skeptic": "🤔", 
        "Dr. Elena Ethics": "⚖️",
        "Judge Sophia": "👩‍⚖️",
        "Morgan the Moderator": "🎯"
    }
    return avatars.get(agent_name, "🤖")

# Removed get_agent_response_streamlit - now using existing backend system

def run_debate_display(debate_manager, topic):
    """Run debate using the existing backend with Streamlit display."""
    
    # Create a custom display adapter for Streamlit
    class StreamlitDisplayAdapter:
        def __init__(self):
            self.messages = []
            self.stop_requested = False
            self.current_loading_placeholder = None
        
        def show_debate_header(self, topic: str, participants: list):
            """Display the debate header with topic and participants."""
            st.markdown(f'<div class="system-message">🎭 <strong>Debate Topic:</strong> {topic}</div>', unsafe_allow_html=True)
            participant_names = ", ".join(participants)
            st.markdown(f'<div class="system-message">👥 <strong>Participants:</strong> {participant_names}</div>', unsafe_allow_html=True)
        
        def show_exchange_header(self, exchange_num: int):
            """Display the exchange header."""
            st.markdown(f'<div class="system-message">🔄 <strong>Exchange {exchange_num}</strong></div>', unsafe_allow_html=True)
        
        def show_generating_indicator(self, speaker: str):
            """Show generating response indicator for the next speaker."""
            if st.session_state.get("stop_debate", False):
                return
            
            avatar = get_agent_avatar(speaker)
            
            # Clear any existing loading placeholder
            if self.current_loading_placeholder:
                self.current_loading_placeholder.empty()
            
            # Create new loading placeholder
            self.current_loading_placeholder = st.empty()
            
            with self.current_loading_placeholder.container():
                with st.chat_message("assistant", avatar=avatar):
                    st.markdown(f'<div class="agent-name">{speaker}:</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="agent-message {speaker}-message">
                        <div class="loading-text">
                            <span class="loading-dots">💭 Generating response</span>
                            <div class="loading-animation">
                                <span class="dot">.</span>
                                <span class="dot">.</span>
                                <span class="dot">.</span>
                            </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        def show_message(self, speaker: str, message: str, color_key: str = None, streaming: bool = True):
            """Display a message from a speaker."""
            if st.session_state.get("stop_debate", False):
                self.stop_requested = True
                return
            
            # Clear loading indicator if it exists
            if self.current_loading_placeholder:
                self.current_loading_placeholder.empty()
                self.current_loading_placeholder = None
                
            # Store message
            message_entry = {
                "name": speaker,
                "content": message,
                "timestamp": datetime.now().isoformat()
            }
            self.messages.append(message_entry)
            
            # Display in Streamlit
            if speaker == "System":
                st.markdown(f'<div class="system-message">🎭 <h6>System:</h6> \n{message}</div>', unsafe_allow_html=True)
            else:
                avatar = get_agent_avatar(speaker)
                agent_class = speaker.lower().replace(" ", "-").replace("the", "").replace("dr.", "").replace(".", "").strip()
                
                with st.chat_message("assistant", avatar=avatar):
                    st.markdown(f'<div class="agent-name">{speaker}:</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="agent-message {agent_class}-message">{message}</div>', unsafe_allow_html=True)
        
        def show_debate_footer(self, total_rounds: int):
            """Display the debate conclusion."""
            st.markdown(f'<div class="system-message">🏁 <strong>Debate Concluded</strong> - Total Rounds: {total_rounds}</div>', unsafe_allow_html=True)
        
        def show_error(self, error_message: str):
            """Display an error message."""
            st.error(f"⚠️ ERROR: {error_message}")
        
        def show_loading(self, message: str):
            """Display a loading message."""
            st.info(f"⏳ {message}...")
        
        def show_success(self, message: str):
            """Display a success message."""
            st.success(f"✅ {message}")
    
    # Replace the debate manager's display with our Streamlit adapter
    original_display = debate_manager.display
    streamlit_display = StreamlitDisplayAdapter()
    debate_manager.display = streamlit_display
    
    # Create control panel with stop button
    stop_container = st.container()
    with stop_container:
        st.markdown('<div class="debate-controls">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            if st.button("⏹️ Stop Debate", key="main_stop_btn", type="secondary", help="Click to stop the debate at any time"):
                st.session_state.stop_debate = True
                streamlit_display.stop_requested = True
                st.warning("🛑 Debate stop requested...")
        
        with col2:
            if st.session_state.get("stop_debate", False):
                st.markdown("**Status:** Stopping...")
            else:
                st.markdown("**Status:** Running")
        
        with col3:
            st.markdown("**Mode:** AI Debate")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Reset stop flag at start
    if "stop_debate" not in st.session_state:
        st.session_state.stop_debate = False
    
    try:
        # Use the existing backend system!
        conversation_history = debate_manager.start_debate()
        
        # Return the messages from our adapter
        return streamlit_display.messages
        
    except Exception as e:
        st.error(f"❌ Error during debate: {e}")
        return []
    
    finally:
        # Restore original display
        debate_manager.display = original_display
        # Reset stop flag after debate ends
        st.session_state.stop_debate = False

def main():
    """Main Streamlit app."""
    # Page config MUST be first
    st.set_page_config(
        page_title="DebateLab Co-pilot",
        page_icon="🎭",
        layout="wide"
    )
    
    # Apply custom CSS after page config
    apply_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Header with better styling
    st.markdown('<h1 class="main-header">🎭 DebateLab Co-pilot</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #6c757d; margin-bottom: 2rem;"><em>AI-powered debate system with multiple agent personalities</em></p>', unsafe_allow_html=True)
    
    # Check model availability
    if not MODEL_PATH.exists():
        st.error("❌ **Model file not found!**")
        st.info(f"Please ensure the GGUF model file is located at: `{MODEL_PATH}`")
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Controls")
        
        # File upload
        st.subheader("📁 Document Upload")
        uploaded_file = st.file_uploader(
            "Upload a file", 
            type=["pdf", "txt", "docx", "pptx"],
            disabled=st.session_state.debate_running,
        )
        
        if uploaded_file is not None:
            process_uploaded_file(uploaded_file)
        
        if st.session_state.uploaded_content:
            st.success(f"✅ File loaded: {st.session_state.uploaded_content['filename']}")
        
        st.divider()
        
        # Agent info
        st.subheader("👥 Debate Participants")
        for key, personality in AGENT_PERSONALITIES.items():
            if key != "moderator":
                emoji = {
                    "optimist": "😊", 
                    "skeptic": "🤔", 
                    "ethicist": "⚖️", 
                    "judge": "👩‍⚖️"
                }.get(key, "🤖")
                st.write(f"{emoji} **{personality['name']}**")
        
        st.divider()
        
        # Model status
        st.subheader("🤖 Model Status")
        st.success(f"✅ Model loaded: {MODEL_PATH.name}")
    
    # Main content with better styling
    st.markdown('<h2 style="color: #2c3e50; margin-top: 2rem;">💭 Enter Debate Topic</h2>', unsafe_allow_html=True)
    
    # Topic input with improved layout
    col1, col2 = st.columns([4, 1])
    
    with col1:
        topic = st.text_input(
            "What should the AI agents debate?",
            placeholder="e.g., Should AI replace human teachers?",
            disabled=st.session_state.debate_running,
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown('<div style="margin-top: 1.8rem;"></div>', unsafe_allow_html=True)  # Better spacing
        start_button = st.button(
            "🚀 Start Debate",
            type="primary",
            disabled=not topic or st.session_state.debate_running,
            use_container_width=True
        )
    
    # Removed quick start examples section
    
    # Run debate
    if start_button and topic:
        st.session_state.debate_running = True
        st.session_state.stop_debate = False
        
        st.header(f"🎭 Debate: {topic}")
        
        # Initialize debate
        with st.spinner("🤖 Initializing debate system..."):
            try:
                debate_manager = DebateManager(topic=topic, enable_moderator=True)
                st.success("✅ Debate system ready!")
            except Exception as e:
                st.error(f"❌ Error initializing debate: {e}")
                st.session_state.debate_running = False
                st.stop()
        
        # Run the debate
        st.info("🚀 Starting debate... Use the stop button below to interrupt at any time.")
        conversation_history = run_debate_display(debate_manager, topic)
        
        # Save to history (even if stopped early)
        if conversation_history and len(conversation_history) > 1:  # More than just system message
            st.session_state.debate_history.append({
                "topic": topic,
                "timestamp": datetime.now().isoformat(),
                "conversation": conversation_history,
                "summary": debate_manager.get_debate_summary() if hasattr(debate_manager, 'get_debate_summary') else {},
                "stopped_early": st.session_state.stop_debate
            })
        
        # Show completion message
        if st.session_state.stop_debate:
            st.warning("⏹️ Debate was stopped early by user")
        else:
            st.success("🎉 Debate completed!")
        
        # Show comprehensive summary in dropdown format
        if hasattr(debate_manager, 'get_debate_summary') and len(conversation_history) > 1:
            summary = debate_manager.get_debate_summary()
            
            # Main summary dropdown
            with st.expander("📊 **Debate Summary & Statistics**", expanded=False):
                st.markdown("### 📈 Quick Overview")
                
                # Basic metrics in a compact layout
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("💬 Messages", summary.get('total_messages', len(conversation_history)))
                with col2:
                    st.metric("🔄 Exchanges", summary.get('total_exchanges', len([m for m in conversation_history if m['name'] != 'System'])))
                with col3:
                    st.metric("👥 Participants", len(summary.get('participants', [])))
                with col4:
                    st.metric("🎯 Status", "✅ Complete" if len(conversation_history) > 2 else "⚠️ Partial")
                
                st.divider()
                
                # Detailed summaries section
                detailed_summary = summary.get('detailed_summary', {})
                if detailed_summary and detailed_summary != "No detailed summaries available yet.":
                    st.markdown("### 📝 Exchange Summaries")
                    
                    # Parse detailed summary if it's a string
                    if isinstance(detailed_summary, str):
                        # Split by exchange if formatted as combined string
                        exchange_parts = detailed_summary.split("Exchange ")
                        for i, part in enumerate(exchange_parts[1:], 1):  # Skip first empty part
                            if part.strip():
                                lines = part.strip().split('\n', 1)
                                if len(lines) > 1:
                                    exchange_title = f"Exchange {lines[0].split(':')[0]}"
                                    exchange_content = lines[1].strip()
                                    st.markdown(f"**🔍 {exchange_title}:**")
                                    st.write(exchange_content)
                                    st.markdown("---")
                    else:
                        # Handle dictionary format
                        for exchange_num in sorted(detailed_summary.keys()):
                            exchange_summary = detailed_summary[exchange_num]
                            if isinstance(exchange_summary, dict) and 'summary' in exchange_summary:
                                content = exchange_summary['summary']
                            elif isinstance(exchange_summary, str):
                                content = exchange_summary
                            else:
                                content = str(exchange_summary)
                            
                            if content and content.strip():
                                st.markdown(f"**🔍 Exchange {exchange_num}:**")
                                st.write(content)
                                st.markdown("---")
                
                st.divider()
                
                # Summary statistics section
                summary_stats = summary.get('summary_stats', {})
                if summary_stats:
                    st.markdown("### 📊 Detailed Statistics")
                    
                    stats_col1, stats_col2, stats_col3 = st.columns(3)
                    
                    with stats_col1:
                        if 'brief_summaries' in summary_stats:
                            st.metric("📋 Brief Summaries", summary_stats['brief_summaries'])
                        if 'total_words' in summary_stats:
                            st.metric("📝 Total Words", summary_stats['total_words'])
                    
                    with stats_col2:
                        if 'detailed_summaries' in summary_stats:
                            st.metric("📄 Detailed Summaries", summary_stats['detailed_summaries'])
                        if 'avg_summary_length' in summary_stats:
                            st.metric("📏 Avg Summary Length", f"{summary_stats['avg_summary_length']} words")
                    
                    with stats_col3:
                        if 'exchanges_covered' in summary_stats:
                            st.metric("🔄 Exchanges Covered", summary_stats['exchanges_covered'])
                        # Add participants list
                        participants = summary.get('participants', [])
                        if participants:
                            st.metric("👥 Participant Count", len(participants))
                    
                    # Show participant list
                    participants = summary.get('participants', [])
                    if participants:
                        st.markdown("**🎭 Participants:**")
                        participant_text = " • ".join(participants)
                        st.write(participant_text)
        
        # Reset states
        st.session_state.debate_running = False
        st.session_state.stop_debate = False
        
        # Add restart button
        if st.button("🔄 Start New Debate", type="primary"):
            st.rerun()
    
    # Show debate history
    if st.session_state.debate_history:
        st.header("📚 Recent Debates")
        
        for i, debate in enumerate(reversed(st.session_state.debate_history[-3:])):  # Show last 3
            with st.expander(f"🎭 {debate['topic']} - {debate['timestamp'][:19]}"):
                st.write(f"**Messages:** {len(debate['conversation'])}")
                
                # Show conversation
                for msg in debate['conversation']:
                    if msg['name'] == 'System':
                        st.info(f"**System:** {msg['content']}")
                    else:
                        avatar = get_agent_avatar(msg['name'])
                        st.write(f"{avatar} **{msg['name']}:** {msg['content']}")

if __name__ == "__main__":
    main()
