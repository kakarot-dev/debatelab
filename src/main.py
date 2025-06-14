"""Main entry point for the debate system - supports both CLI and Streamlit modes."""

import argparse
import sys
import logging
import json
from pathlib import Path
from typing import Optional
import streamlit as st

from .debate_manager import DebateManager
from .display import DebateDisplay, ProgressIndicator
from .config import MODEL_PATH, AGENT_PERSONALITIES, COLORS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debate.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DebateCLI:
    """Command-line interface for the debate system."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.display = DebateDisplay()
        self.debate_manager = None
    
    def run(self):
        """Run the CLI application."""
        try:
            # Parse command line arguments
            args = self._parse_arguments()
            
            # Validate model file exists
            if not self._validate_model():
                return 1
            
            # Show welcome message
            self._show_welcome()
            
            # Get debate topic
            topic = args.topic or self._get_topic_from_user()
            if not topic:
                self.display.show_error("No topic provided")
                return 1
            
            # Initialize and run debate
            return self._run_debate(topic, args)
            
        except KeyboardInterrupt:
            print(f"\n{COLORS['yellow']}Debate interrupted by user{COLORS['reset']}")
            return 0
        except Exception as e:
            self.display.show_error(f"Unexpected error: {e}")
            logger.exception("Unexpected error in CLI")
            return 1
    
    def _parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments.
        
        Returns:
            Parsed arguments
        """
        parser = argparse.ArgumentParser(
            description="AI Debate System - Multiple agents debate a topic using local LLM",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python -m src.main "Should AI replace human teachers?"
  python -m src.main --topic "Climate change solutions" --no-moderator
  python -m src.main --interactive
  python -m src.main --list-personalities
  python -m src.main --streamlit  # Launch Streamlit interface
            """
        )
        
        parser.add_argument(
            "topic",
            nargs="?",
            help="The debate topic (if not provided, will prompt interactively)"
        )
        
        parser.add_argument(
            "--topic", "-t",
            dest="topic_flag",
            help="The debate topic (alternative way to specify)"
        )
        
        parser.add_argument(
            "--no-moderator",
            action="store_true",
            help="Disable the moderator agent"
        )
        
        parser.add_argument(
            "--interactive", "-i",
            action="store_true",
            help="Run in interactive mode with prompts"
        )
        
        parser.add_argument(
            "--list-personalities",
            action="store_true",
            help="List available agent personalities and exit"
        )
        
        parser.add_argument(
            "--save-output",
            metavar="FILE",
            help="Save debate output to a JSON file"
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose logging"
        )
        
        parser.add_argument(
            "--streamlit",
            action="store_true",
            help="Launch Streamlit web interface"
        )
        
        args = parser.parse_args()
        
        # Handle topic from either positional or flag argument
        if not args.topic and args.topic_flag:
            args.topic = args.topic_flag
        
        # Set logging level
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        return args
    
    def _validate_model(self) -> bool:
        """Validate that the model file exists.
        
        Returns:
            True if model exists, False otherwise
        """
        if not MODEL_PATH.exists():
            self.display.show_error(f"Model file not found: {MODEL_PATH}")
            self.display.show_error("Please ensure the GGUF model file is in the models/ directory")
            return False
        
        self.display.show_success(f"Model found: {MODEL_PATH.name}")
        return True
    
    def _show_welcome(self):
        """Show welcome message."""
        print(f"\n{COLORS['bold']}{COLORS['cyan']}🎭 Welcome to the AI Debate Arena! 🎭{COLORS['reset']}")
        print(f"{COLORS['white']}Multiple AI agents with different personalities will debate your topic.{COLORS['reset']}\n")
    
    def _get_topic_from_user(self) -> Optional[str]:
        """Get debate topic from user input.
        
        Returns:
            Topic string or None if cancelled
        """
        print(f"{COLORS['bold']}Enter a debate topic:{COLORS['reset']}")
        print(f"{COLORS['white']}Examples:{COLORS['reset']}")
        print("  • Should artificial intelligence replace human teachers?")
        print("  • Is remote work better than office work?")
        print("  • Should social media be regulated by governments?")
        print("  • Is nuclear energy the solution to climate change?")
        print()
        
        try:
            topic = input(f"{COLORS['cyan']}Topic: {COLORS['reset']}").strip()
            return topic if topic else None
        except (EOFError, KeyboardInterrupt):
            return None
    
    def _run_debate(self, topic: str, args: argparse.Namespace) -> int:
        """Run the debate with the given topic.
        
        Args:
            topic: Debate topic
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            # Show loading indicator
            progress = ProgressIndicator("Initializing debate system")
            progress.start()
            
            # Initialize debate manager
            self.debate_manager = DebateManager(
                topic=topic,
                enable_moderator=not args.no_moderator
            )
            
            progress.stop()
            self.display.show_success("Debate system initialized")
            
            # Start the debate
            conversation_history = self.debate_manager.start_debate()
            
            # Save output if requested
            if args.save_output:
                self._save_debate_output(args.save_output, conversation_history)
            
            # Show final summary
            self._show_debate_summary()
            
            return 0
            
        except Exception as e:
            self.display.show_error(f"Error running debate: {e}")
            logger.exception("Error running debate")
            return 1
    
    def _save_debate_output(self, filename: str, conversation_history: list):
        """Save debate output to a file.
        
        Args:
            filename: Output filename
            conversation_history: List of conversation messages
        """
        try:
            output_data = {
                "debate_summary": self.debate_manager.get_debate_summary(),
                "conversation_history": conversation_history
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            self.display.show_success(f"Debate output saved to {filename}")
            
        except Exception as e:
            self.display.show_error(f"Failed to save output: {e}")
    
    def _show_debate_summary(self):
        """Show final debate summary."""
        if not self.debate_manager:
            return
        
        summary = self.debate_manager.get_debate_summary()
        
        print(f"\n{COLORS['bold']}📊 DEBATE SUMMARY{COLORS['reset']}")
        print(f"Topic: {summary['topic']}")
        print(f"Exchanges: {summary['total_exchanges']}")
        print(f"Messages: {summary['total_messages']}")
        print(f"Participants: {', '.join(summary['participants'])}")
        
        if summary['moderator_used']:
            print("Moderator: Enabled")
        
        print(f"\n{COLORS['green']}Thank you for using the AI Debate Arena!{COLORS['reset']}")
    
    def _list_personalities(self):
        """List available agent personalities."""
        print(f"\n{COLORS['bold']}Available Agent Personalities:{COLORS['reset']}\n")
        
        for key, personality in AGENT_PERSONALITIES.items():
            if key == "moderator":
                continue
                
            color = COLORS.get(personality["color"], COLORS["white"])
            print(f"{color}• {personality['name']}{COLORS['reset']}")
            
            # Extract key traits from system message
            system_msg = personality["personality"]
            if "You are" in system_msg:
                description = system_msg.split("You are")[1].split(".")[0].strip()
                print(f"  {description}")
            print()
        
        # Show moderator separately
        moderator = AGENT_PERSONALITIES["moderator"]
        color = COLORS.get(moderator["color"], COLORS["white"])
        print(f"{color}• {moderator['name']}{COLORS['reset']} (Optional)")
        print("  Facilitates discussion and maintains balance")

class StreamlitApp:
    """Streamlit web interface for the debate system."""
    
    def __init__(self):
        """Initialize the Streamlit app."""
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
    
    def run(self):
        """Run the Streamlit application."""
        # Header
        st.title("🎭 DebateLab Co-pilot")
        st.markdown("*AI-powered debate system with multiple agent personalities*")
        
        # Sidebar
        self.render_sidebar()
        
        # Main content
        self.render_main_content()
    
    def render_sidebar(self):
        """Render the sidebar with controls and information."""
        with st.sidebar:
            st.header("🔧 Controls")
            
            # File upload
            st.subheader("📁 Document Upload")
            uploaded_file = st.file_uploader(
                "Upload a document for context",
                type=["pdf", "txt", "docx", "pptx"],
                help="Upload a document to provide additional context for the debate"
            )
            
            if uploaded_file is not None:
                self.process_uploaded_file(uploaded_file)
            
            st.divider()
            
            # Debate settings
            st.subheader("⚙️ Debate Settings")
            enable_moderator = st.checkbox("Enable Moderator", value=True)
            max_exchanges = st.slider("Max Exchanges", min_value=5, max_value=20, value=8)
            
            st.divider()
            
            # Agent personalities
            st.subheader("👥 Debate Participants")
            for key, personality in AGENT_PERSONALITIES.items():
                if key == "moderator":
                    if enable_moderator:
                        st.write(f"🎯 **{personality['name']}** (Moderator)")
                else:
                    emoji = {"optimist": "😊", "skeptic": "🤔", "ethicist": "⚖️", "judge": "👩‍⚖️"}.get(key, "🤖")
                    st.write(f"{emoji} **{personality['name']}**")
            
            st.divider()
            
            # Model status
            st.subheader("🤖 Model Status")
            if MODEL_PATH.exists():
                st.success(f"✅ Model loaded: {MODEL_PATH.name}")
            else:
                st.error("❌ Model file not found")
                st.info("Please ensure the GGUF model file is in the models/ directory")
    
    def process_uploaded_file(self, uploaded_file):
        """Process uploaded file and extract content."""
        try:
            import tempfile
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
            
        except Exception as e:
            st.error(f"❌ Error processing file: {e}")
    
    def render_main_content(self):
        """Render the main content area."""
        # Topic input
        st.header("💭 Debate Topic")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            topic = st.text_input(
                "Enter your debate topic:",
                placeholder="e.g., Should AI replace human teachers?",
                help="Enter a thought-provoking question or statement for the AI agents to debate"
            )
        
        with col2:
            st.write("")  # Spacing
            start_debate = st.button(
                "🚀 Start Debate",
                type="primary",
                disabled=not topic or st.session_state.debate_running
            )
        
        # Example topics
        st.markdown("**💡 Example topics:**")
        example_topics = [
            "Should artificial intelligence replace human teachers?",
            "Is remote work better than office work?",
            "Should social media be regulated by governments?",
            "Is nuclear energy the solution to climate change?",
            "Should universal basic income be implemented globally?"
        ]
        
        cols = st.columns(len(example_topics))
        for i, example in enumerate(example_topics):
            with cols[i]:
                if st.button(f"📝 {example[:30]}...", key=f"example_{i}"):
                    st.rerun()
        
        # Start debate
        if start_debate and topic:
            self.run_debate(topic)
        
        # Display debate history
        if st.session_state.debate_history:
            self.render_debate_history()
    
    def run_debate(self, topic: str):
        """Run a debate with the given topic."""
        st.session_state.debate_running = True
        
        # Create progress indicator
        progress_placeholder = st.empty()
        with progress_placeholder:
            with st.spinner("🤖 Initializing debate system..."):
                try:
                    # Initialize debate manager
                    debate_manager = DebateManager(
                        topic=topic,
                        enable_moderator=True  # Can be made configurable
                    )
                    
                    st.session_state.current_debate = {
                        "topic": topic,
                        "manager": debate_manager,
                        "messages": []
                    }
                    
                except Exception as e:
                    st.error(f"❌ Error initializing debate: {e}")
                    st.session_state.debate_running = False
                    return
        
        progress_placeholder.empty()
        
        # Run the debate
        st.header(f"🎭 Debate: {topic}")
        
        # Create containers for real-time updates
        debate_container = st.container()
        status_container = st.container()
        
        with status_container:
            st.info("🚀 Debate is starting...")
        
        try:
            # Start the debate and capture messages
            with debate_container:
                conversation_history = self.run_debate_with_display(debate_manager, topic)
            
            # Store in session state
            st.session_state.debate_history.append({
                "topic": topic,
                "timestamp": str(pd.Timestamp.now()),
                "conversation": conversation_history,
                "summary": debate_manager.get_debate_summary()
            })
            
            with status_container:
                st.success("✅ Debate completed successfully!")
                
                # Show summary
                summary = debate_manager.get_debate_summary()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Exchanges", summary.get('total_exchanges', 0))
                with col2:
                    st.metric("Total Messages", summary.get('total_messages', 0))
                with col3:
                    st.metric("Participants", len(summary.get('participants', [])))
        
        except Exception as e:
            with status_container:
                st.error(f"❌ Error during debate: {e}")
            logger.exception("Error running Streamlit debate")
        
        finally:
            st.session_state.debate_running = False
    
    def run_debate_with_display(self, debate_manager: DebateManager, topic: str):
        """Run debate with real-time Streamlit display."""
        conversation_history = []
        
        # Create initial message
        initial_message = f'Welcome to today\'s debate! Our topic is: "{topic}"\n\nLet\'s have a thoughtful discussion where each participant can share their perspective.'
        
        # Display initial message
        with st.chat_message("system"):
            st.write(initial_message)
        
        conversation_history.append({
            "name": "System",
            "content": initial_message
        })
        
        # Get debate agents
        debate_agents = list(debate_manager.agents.values())
        current_speaker = debate_agents[0]  # Start with first agent
        
        # Run conversation
        max_exchanges = 8
        for exchange in range(max_exchanges):
            try:
                # Get response from current speaker
                is_starter = (exchange == 0)
                response = self.get_agent_response_streamlit(debate_manager, current_speaker, is_starter)
                
                if response:
                    # Display message
                    avatar = self.get_agent_avatar(current_speaker.name)
                    with st.chat_message("assistant", avatar=avatar):
                        st.write(f"**{current_speaker.name}:**")
                        st.write(response)
                    
                    conversation_history.append({
                        "name": current_speaker.name,
                        "content": response,
                        "exchange": exchange + 1
                    })
                    
                    # Brief pause for better UX
                    import time
                    time.sleep(0.5)
                    
                    # Select next speaker
                    current_index = debate_agents.index(current_speaker)
                    next_index = (current_index + 1) % len(debate_agents)
                    current_speaker = debate_agents[next_index]
                
            except Exception as e:
                st.error(f"Error getting response from {current_speaker.name}: {e}")
                break
        
        return conversation_history
    
    def get_agent_response_streamlit(self, debate_manager: DebateManager, agent, is_starter: bool = False):
        """Get agent response for Streamlit display."""
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
                # Simple context for follow-up speakers
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
    
    def render_debate_history(self):
        """Render the debate history section."""
        st.header("📚 Debate History")
        
        if not st.session_state.debate_history:
            st.info("No debates yet. Start your first debate above!")
            return
        
        for i, debate in enumerate(reversed(st.session_state.debate_history)):
            with st.expander(f"🎭 {debate['topic']} - {debate['timestamp'][:19]}"):
                
                # Summary metrics
                summary = debate.get('summary', {})
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Exchanges", summary.get('total_exchanges', 0))
                with col2:
                    st.metric("Messages", summary.get('total_messages', 0))
                with col3:
                    st.metric("Participants", len(summary.get('participants', [])))
                
                st.divider()
                
                # Conversation
                st.subheader("💬 Conversation")
                for msg in debate['conversation']:
                    if msg['name'] == 'System':
                        st.info(f"**System:** {msg['content']}")
                    else:
                        avatar = self.get_agent_avatar(msg['name'])
                        st.write(f"{avatar} **{msg['name']}:** {msg['content']}")
                        st.divider()

def launch_streamlit():
    """Launch the Streamlit application."""
    import pandas as pd  # Import here to avoid issues if not needed in CLI mode
    app = StreamlitApp()
    app.run()

def main():
    """Main entry point."""
    # Check if running in Streamlit
    try:
        # This will only work if we're in a Streamlit context
        st.session_state
        launch_streamlit()
        return 0
    except:
        pass
    
    # CLI mode
    cli = DebateCLI()
    
    # Handle special commands
    if len(sys.argv) > 1:
        if "--list-personalities" in sys.argv:
            cli._list_personalities()
            return 0
        elif "--streamlit" in sys.argv:
            # Launch Streamlit
            import subprocess
            subprocess.run([sys.executable, "-m", "streamlit", "run", __file__])
            return 0
    
    # Run the main CLI
    return cli.run()

if __name__ == "__main__":
    sys.exit(main())