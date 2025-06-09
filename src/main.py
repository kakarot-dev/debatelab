"""Main CLI interface for the debate system."""

import argparse
import sys
import logging
import json
from pathlib import Path
from typing import Optional

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
            system_msg = personality["system_message"]
            if "You are" in system_msg:
                description = system_msg.split("You are")[1].split(".")[0].strip()
                print(f"  {description}")
            print()
        
        # Show moderator separately
        moderator = AGENT_PERSONALITIES["moderator"]
        color = COLORS.get(moderator["color"], COLORS["white"])
        print(f"{color}• {moderator['name']}{COLORS['reset']} (Optional)")
        print("  Facilitates discussion and maintains balance")

def main():
    """Main entry point."""
    cli = DebateCLI()
    
    # Handle special commands
    if len(sys.argv) > 1 and "--list-personalities" in sys.argv:
        cli._list_personalities()
        return 0
    
    # Run the main CLI
    return cli.run()

if __name__ == "__main__":
    sys.exit(main())