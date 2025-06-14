"""Streamlit web interface for the DebateLab system."""

import streamlit as st
import pandas as pd
import tempfile
import time
import logging
from datetime import datetime
from typing import Optional, List, Dict

# Import the debate system components
from src.debate_manager import DebateManager
from src.config import MODEL_PATH, AGENT_PERSONALITIES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DebateLabApp:
    """Main Streamlit application for DebateLab."""
    
    def __init__(self):
        """Initialize the application."""
        self.setup_page_config()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="DebateLab Co-pilot",
            page_icon="🎭",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if "debate_history" not in st.session_state:
            st.session_state.debate_history = []
        if "current_debate" not in st.session_state:
            st.session_state.current_debate = None
        if "debate_running" not in st.session_state:
            st.session_state.debate_running = False
        if "uploaded_content" not in st.session_state:
            st.session_state.uploaded_content = None
        if "selected_topic" not in st.session_state:
            st.session_state.selected_topic = ""
    
    def run(self):
        """Run the main application."""
        # Header
        st.title("🎭 DebateLab Co-pilot")
        st.markdown("*AI-powered debate system with multiple agent personalities*")
        
        # Check model availability
        if not self.check_model_availability():
            return
        
        # Sidebar
        self.render_sidebar()
        
        # Main content
        self.render_main_content()
    
    def check_model_availability(self) -> bool:
        """Check if the model is available."""
        if not MODEL_PATH.exists():
            st.error("❌ **Model file not found!**")
            st.info(f"Please ensure the GGUF model file is located at: `{MODEL_PATH}`")
            st.info("The debate system requires a local LLM model to function.")
            return False
        return True
    
    def render_sidebar(self):
        """Render the sidebar with controls and information."""
        with st.sidebar:
            st.header("🔧 Controls")
            
            # File upload section
            self.render_file_upload()
            
            st.divider()
            
            # Debate settings
            self.render_debate_settings()
            
            st.divider()
            
            # Agent information
            self.render_agent_info()
            
            st.divider()
            
            # Model status
            self.render_model_status()
    
    def render_file_upload(self):
        """Render file upload section."""
        st.subheader("📁 Document Upload")
        uploaded_file = st.file_uploader(
            "Upload a document for context",
            type=["pdf", "txt", "docx", "pptx"],
            help="Upload a document to provide additional context for the debate"
        )
        
        if uploaded_file is not None:
            self.process_uploaded_file(uploaded_file)
        
        if st.session_state.uploaded_content:
            st.success(f"✅ File loaded: {st.session_state.uploaded_content['filename']}")
            if st.button("🗑️ Clear uploaded file"):
                st.session_state.uploaded_content = None
                st.rerun()
    
    def render_debate_settings(self):
        """Render debate settings section."""
        st.subheader("⚙️ Debate Settings")
        
        enable_moderator = st.checkbox("Enable Moderator", value=True, key="enable_moderator")
        max_exchanges = st.slider(
            "Max Exchanges", 
            min_value=5, 
            max_value=20, 
            value=8,
            key="max_exchanges",
            help="Maximum number of back-and-forth exchanges between agents"
        )
        
        # Store settings in session state
        st.session_state.debate_settings = {
            "enable_moderator": enable_moderator,
            "max_exchanges": max_exchanges
        }
    
    def render_agent_info(self):
        """Render agent information section."""
        st.subheader("👥 Debate Participants")
        
        for key, personality in AGENT_PERSONALITIES.items():
            if key == "moderator":
                if st.session_state.get("debate_settings", {}).get("enable_moderator", True):
                    st.write(f"🎯 **{personality['name']}** (Moderator)")
            else:
                emoji = {
                    "optimist": "😊", 
                    "skeptic": "🤔", 
                    "ethicist": "⚖️", 
                    "judge": "👩‍⚖️"
                }.get(key, "🤖")
                st.write(f"{emoji} **{personality['name']}**")
        
        # Show personality details in expander
        with st.expander("📋 View Agent Personalities"):
            for key, personality in AGENT_PERSONALITIES.items():
                if key != "moderator":
                    st.write(f"**{personality['name']}:**")
                    # Extract key traits from personality description
                    traits = personality['personality'].split('\n')[2:5]  # Get first few bullet points
                    for trait in traits:
                        if trait.strip().startswith('•'):
                            st.write(f"  {trait.strip()}")
                    st.write("")
    
    def render_model_status(self):
        """Render model status section."""
        st.subheader("🤖 Model Status")
        if MODEL_PATH.exists():
            st.success(f"✅ Model loaded")
            st.caption(f"File: {MODEL_PATH.name}")
        else:
            st.error("❌ Model file not found")
    
    def process_uploaded_file(self, uploaded_file):
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
                
            except ImportError:
                # Fallback for text files
                if uploaded_file.type == "text/plain":
                    content = str(uploaded_file.read(), "utf-8")
                else:
                    st.warning("⚠️ textract not available. Only plain text files supported.")
                    return
            
            st.session_state.uploaded_content = {
                "filename": uploaded_file.name,
                "content": content[:2000]  # Limit content length
            }
            
            st.success(f"✅ File processed: {uploaded_file.name}")
            
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
    
    def render_main_content(self):
        """Render the main content area."""
        # Topic input section
        self.render_topic_input()
        
        # Current debate display
        if st.session_state.debate_running:
            self.render_active_debate()
        
        # Debate history
        if st.session_state.debate_history:
            self.render_debate_history()
    
    def render_topic_input(self):
        """Render topic input section."""
        st.header("💭 Debate Topic")
        
        # Topic input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            topic = st.text_input(
                "Enter your debate topic:",
                value=st.session_state.selected_topic,
                placeholder="e.g., Should AI replace human teachers?",
                help="Enter a thought-provoking question or statement for the AI agents to debate",
                key="topic_input"
            )
        
        with col2:
            st.write("")  # Spacing
            start_debate = st.button(
                "🚀 Start Debate",
                type="primary",
                disabled=not topic or st.session_state.debate_running,
                help="Click to start the debate with the entered topic"
            )
        
        # Example topics
        # st.markdown("**💡 Example topics:**")
        # example_topics = [
        #     "Should artificial intelligence replace human teachers?",
        #     "Is remote work better than office work?",
        #     "Should social media be regulated by governments?",
        #     "Is nuclear energy the solution to climate change?",
        #     "Should universal basic income be implemented globally?"
        # ]
        
        # # Create columns for example buttons
        # cols = st.columns(min(len(example_topics), 3))
        # for i, example in enumerate(example_topics):
        #     col_idx = i % len(cols)
        #     with cols[col_idx]:
        #         if st.button(f"📝 {example[:40]}...", key=f"example_{i}"):
        #             st.session_state.selected_topic = example
        #             st.rerun()
        
        # Start debate
        if start_debate and topic:
            self.start_debate(topic)
    
    def start_debate(self, topic: str):
        """Start a new debate."""
        st.session_state.debate_running = True
        st.session_state.current_debate = {
            "topic": topic,
            "messages": [],
            "start_time": datetime.now()
        }
        st.rerun()
    
    def render_active_debate(self):
        """Render the active debate interface."""
        if not st.session_state.current_debate:
            return
        
        topic = st.session_state.current_debate["topic"]
        st.header(f"🎭 Active Debate: {topic}")
        
        # Control buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button("⏹️ Stop Debate", type="secondary"):
                self.stop_debate()
                return
        with col2:
            if st.button("💾 Save & Stop", type="primary"):
                self.save_and_stop_debate()
                return
        
        # Run the debate
        self.run_debate(topic)
    
    def run_debate(self, topic: str):
        """Run the actual debate."""
        # Create containers for the debate
        status_container = st.container()
        debate_container = st.container()
        
        with status_container:
            st.info("🤖 Initializing debate system...")
        
        try:
            # Initialize debate manager
            settings = st.session_state.get("debate_settings", {})
            debate_manager = DebateManager(
                topic=topic,
                enable_moderator=settings.get("enable_moderator", True)
            )
            
            with status_container:
                st.success("✅ Debate system initialized. Starting conversation...")
            
            # Run the debate with real-time display
            with debate_container:
                conversation_history = self.run_debate_with_display(debate_manager, topic)
            
            # Store results
            st.session_state.current_debate["messages"] = conversation_history
            st.session_state.current_debate["summary"] = debate_manager.get_debate_summary()
            
            with status_container:
                st.success("🎉 Debate completed successfully!")
                
                # Show summary metrics
                summary = debate_manager.get_debate_summary()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Exchanges", summary.get('total_exchanges', 0))
                with col2:
                    st.metric("Total Messages", summary.get('total_messages', 0))
                with col3:
                    st.metric("Participants", len(summary.get('participants', [])))
            
            # Auto-save to history
            self.save_current_debate()
            
        except Exception as e:
            with status_container:
                st.error(f"❌ Error during debate: {e}")
            logger.exception("Error running debate")
        
        finally:
            st.session_state.debate_running = False
    
    def run_debate_with_display(self, debate_manager: DebateManager, topic: str) -> List[Dict]:
        """Run debate with real-time Streamlit display."""
        conversation_history = []
        
        # Initial message
        initial_message = f'Welcome to today\'s debate! Our topic is: "{topic}"\n\nLet\'s have a thoughtful discussion where each participant can share their perspective.'
        
        with st.chat_message("system"):
            st.write(initial_message)
        
        conversation_history.append({
            "name": "System",
            "content": initial_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Get debate agents
        debate_agents = list(debate_manager.agents.values())
        if not debate_agents:
            st.error("No debate agents available!")
            return conversation_history
        
        current_speaker = debate_agents[0]
        max_exchanges = st.session_state.get("debate_settings", {}).get("max_exchanges", 8)
        
        # Progress bar
        progress_bar = st.progress(0)
        
        # Run conversation
        for exchange in range(max_exchanges):
            # Update progress
            progress_bar.progress((exchange + 1) / max_exchanges)
            
            try:
                # Get response from current speaker
                is_starter = (exchange == 0)
                response = self.get_agent_response(debate_manager, current_speaker, is_starter)
                
                if response:
                    # Display message
                    avatar = self.get_agent_avatar(current_speaker.name)
                    with st.chat_message("assistant", avatar=avatar):
                        st.write(f"**{current_speaker.name}:**")
                        st.write(response)
                    
                    conversation_history.append({
                        "name": current_speaker.name,
                        "content": response,
                        "exchange": exchange + 1,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Brief pause for better UX
                    time.sleep(0.5)
                    
                    # Select next speaker
                    current_index = debate_agents.index(current_speaker)
                    next_index = (current_index + 1) % len(debate_agents)
                    current_speaker = debate_agents[next_index]
                
                else:
                    st.warning(f"⚠️ {current_speaker.name} couldn't respond. Skipping...")
                    
            except Exception as e:
                st.error(f"❌ Error getting response from {current_speaker.name}: {e}")
                break
        
        progress_bar.empty()
        return conversation_history
    
    def get_agent_response(self, debate_manager: DebateManager, agent, is_starter: bool = False) -> Optional[str]:
        """Get agent response."""
        try:
            if is_starter:
                context_message = f"""Topic: {debate_manager.topic}

YOU ARE THE OPENING SPEAKER

You have been chosen to open this debate because your perspective sets a strong foundation for thoughtful discussion.

Your responsibilities as the opening speaker:
- Introduce your position on the topic with clarity and depth.
- Establish a clear and principled tone for the debate.
- Offer compelling ethical or logical arguments that others can build on or challenge.
- Do not refer to other speakers — you are going first.
- Keep your response focused and concise (~200–220 words).
- Remain fully in-character at all times.

Now begin your opening statement:"""
            else:
                context_message = f"""Topic: {debate_manager.topic}

As the current speaker, your role is to:
- Respond directly to the strongest arguments made in the previous round.
- Present your position clearly, using specific reasoning or examples.
- Identify any flawed logic or missing perspectives, and explain why they matter.
- Add new insights that move the discussion forward.
- Stay fully in character and consistent with your assigned personality.

Now deliver your response:"""
            
            # Get response using the agent's custom reply method
            success, response = agent._custom_generate_reply(
                messages=[{"content": context_message, "name": "System"}],
                sender=None
            )
            
            if success and response:
                return response
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting response from {agent.name}: {e}")
            return None
    
    def get_agent_avatar(self, agent_name: str) -> str:
        """Get emoji avatar for agent."""
        avatars = {
            "Alex the Optimist": "😊",
            "Sam the Skeptic": "🤔",
            "Dr. Elena Ethics": "⚖️",
            "Judge Sophia": "👩‍⚖️",
            "Morgan the Moderator": "🎯"
        }
        return avatars.get(agent_name, "🤖")
    
    def stop_debate(self):
        """Stop the current debate without saving."""
        st.session_state.debate_running = False
        st.session_state.current_debate = None
        st.rerun()
    
    def save_and_stop_debate(self):
        """Save current debate and stop."""
        self.save_current_debate()
        st.session_state.debate_running = False
        st.rerun()
    
    def save_current_debate(self):
        """Save the current debate to history."""
        if st.session_state.current_debate:
            debate_data = st.session_state.current_debate.copy()
            debate_data["end_time"] = datetime.now()
            debate_data["duration"] = (debate_data["end_time"] - debate_data["start_time"]).total_seconds()
            
            st.session_state.debate_history.append(debate_data)
            st.session_state.current_debate = None
    
    def render_debate_history(self):
        """Render the debate history section."""
        st.header("📚 Debate History")
        
        if not st.session_state.debate_history:
            st.info("No debates yet. Start your first debate above!")
            return
        
        # Add clear history button
        if st.button("🗑️ Clear History", type="secondary"):
            st.session_state.debate_history = []
            st.rerun()
        
        # Display debates in reverse chronological order
        for i, debate in enumerate(reversed(st.session_state.debate_history)):
            start_time = debate.get("start_time", datetime.now())
            timestamp_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
            
            with st.expander(f"🎭 {debate['topic']} - {timestamp_str}"):
                
                # Summary metrics
                summary = debate.get('summary', {})
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Exchanges", summary.get('total_exchanges', len(debate.get('messages', []))))
                with col2:
                    st.metric("Messages", summary.get('total_messages', len(debate.get('messages', []))))
                with col3:
                    st.metric("Participants", len(summary.get('participants', [])))
                with col4:
                    duration = debate.get('duration', 0)
                    st.metric("Duration", f"{int(duration//60)}m {int(duration%60)}s")
                
                st.divider()
                
                # Download button for debate
                if st.button(f"💾 Download Debate {i+1}", key=f"download_{i}"):
                    self.download_debate(debate)
                
                st.divider()
                
                # Conversation display
                st.subheader("💬 Conversation")
                messages = debate.get('messages', [])
                
                for msg in messages:
                    if msg['name'] == 'System':
                        with st.chat_message("system"):
                            st.write(msg['content'])
                    else:
                        avatar = self.get_agent_avatar(msg['name'])
                        with st.chat_message("assistant", avatar=avatar):
                            st.write(f"**{msg['name']}:**")
                            st.write(msg['content'])
    
    def download_debate(self, debate_data: Dict):
        """Prepare debate data for download."""
        import json
        
        # Prepare data for download
        download_data = {
            "topic": debate_data["topic"],
            "start_time": debate_data["start_time"].isoformat() if isinstance(debate_data["start_time"], datetime) else str(debate_data["start_time"]),
            "end_time": debate_data.get("end_time", datetime.now()).isoformat() if isinstance(debate_data.get("end_time"), datetime) else str(debate_data.get("end_time", "")),
            "duration_seconds": debate_data.get("duration", 0),
            "summary": debate_data.get("summary", {}),
            "messages": debate_data.get("messages", [])
        }
        
        # Convert to JSON
        json_str = json.dumps(download_data, indent=2, ensure_ascii=False)
        
        # Create download button
        st.download_button(
            label="📄 Download as JSON",
            data=json_str,
            file_name=f"debate_{debate_data['topic'][:30].replace(' ', '_')}_{debate_data['start_time'].strftime('%Y%m%d_%H%M%S') if isinstance(debate_data['start_time'], datetime) else 'unknown'}.json",
            mime="application/json"
        )

def main():
    """Main entry point for the Streamlit app."""
    app = DebateLabApp()
    app.run()

if __name__ == "__main__":
    main()