"""Display utilities for formatting debate output in the CLI."""

import time
from typing import List
from .config import COLORS, AGENT_PERSONALITIES

class DebateDisplay:
    """Handles the visual presentation of the debate in the CLI."""
    
    def __init__(self):
        """Initialize the display manager."""
        self.terminal_width = 80  # Default terminal width
        try:
            import shutil
            self.terminal_width = shutil.get_terminal_size().columns
        except:
            pass  # Use default if unable to get terminal size
    
    def show_debate_header(self, topic: str, participants: List[str]):
        """Display the debate header with topic and participants.
        
        Args:
            topic: The debate topic
            participants: List of participant names
        """
        self._print_separator("=")
        self._print_centered("🎭 DEBATE ARENA 🎭", "bold")
        self._print_separator("=")
        
        print(f"{COLORS['bold']}Topic:{COLORS['reset']} {COLORS['white']}{topic}{COLORS['reset']}")
        print()
        
        print(f"{COLORS['bold']}Participants:{COLORS['reset']}")
        for participant in participants:
            personality = self._get_personality_by_participant(participant)
            if personality:
                color = COLORS.get(personality["color"], COLORS["white"])
                print(f"  {color}• {personality['name']}{COLORS['reset']} - {self._get_personality_description(participant)}")
        
        if len(participants) < len(AGENT_PERSONALITIES) - 1:  # -1 for moderator
            print(f"  {COLORS['cyan']}• Morgan the Moderator{COLORS['reset']} - Facilitates discussion")
        
        print()
        self._print_separator("-")
        print()

    
    def show_exchange_header(self, exchange_num: int):
        """Display the exchange header.
        
        Args:
            exchange_num: Exchange number
        """
        print(f"\n{COLORS['bold']}{COLORS['cyan']}=== EXCHANGE {exchange_num} ==={COLORS['reset']}\n")
    
    def show_message(self, speaker: str, message: str, color_key: str, streaming: bool = True):
        """Display a message from a speaker.
        
        Args:
            speaker: Name of the speaker
            message: The message content
            color_key: Color key for the speaker
            streaming: Whether to display with streaming effect
        """
        color = COLORS.get(color_key, COLORS["white"])
        timestamp = time.strftime("%H:%M:%S")
        
        # Format the speaker name with color and timestamp
        speaker_line = f"{COLORS['bold']}{color}[{timestamp}] {speaker}:{COLORS['reset']}"
        print(speaker_line)
        
        if streaming:
            self._stream_text(message, color, indent=2)
        else:
            # Format and display the message with proper wrapping
            formatted_message = self._wrap_text(message, indent=2)
            print(f"{color}{formatted_message}{COLORS['reset']}")
        
        print()  # Add spacing between messages
    
    def _stream_text(self, text: str, color: str, indent: int = 0, delay: float = 0.03):
        """Display text with a streaming effect.
        
        Args:
            text: Text to display
            color: Color code for the text
            indent: Number of spaces to indent
            delay: Delay between characters (seconds)
        """
        import sys
        
        # Add indentation
        indent_str = " " * indent
        print(indent_str, end="")
        
        # Stream the text character by character
        print(color, end="")
        for char in text:
            print(char, end="", flush=True)
            if char in '.!?':
                time.sleep(delay * 3)  # Longer pause after sentences
            elif char in ',;:':
                time.sleep(delay * 2)  # Medium pause after punctuation
            elif char == ' ':
                time.sleep(delay * 0.5)  # Short pause after spaces
            else:
                time.sleep(delay)  # Normal character delay
        
        print(COLORS['reset'], end="")
    
    def show_debate_footer(self, total_rounds: int):
        """Display the debate conclusion.
        
        Args:
            total_rounds: Total number of rounds completed
        """
        print()
        self._print_separator("=")
        self._print_centered("🏁 DEBATE CONCLUDED 🏁", "bold")
        self._print_separator("=")
        print(f"{COLORS['bold']}Total Rounds Completed:{COLORS['reset']} {total_rounds}")
        print(f"{COLORS['bold']}Thank you for participating in this debate!{COLORS['reset']}")
        self._print_separator("=")
        print()
    
    def show_error(self, error_message: str):
        """Display an error message.
        
        Args:
            error_message: The error message to display
        """
        print(f"{COLORS['bold']}{COLORS['yellow']}⚠️  ERROR: {error_message}{COLORS['reset']}")
    
    def show_loading(self, message: str):
        """Display a loading message.
        
        Args:
            message: Loading message
        """
        print(f"{COLORS['cyan']}⏳ {message}...{COLORS['reset']}")
    
    def show_success(self, message: str):
        """Display a success message.
        
        Args:
            message: Success message
        """
        print(f"{COLORS['green']}✅ {message}{COLORS['reset']}")
    
    def _print_separator(self, char: str = "-"):
        """Print a separator line.
        
        Args:
            char: Character to use for the separator
        """
        print(char * min(self.terminal_width, 80))
    
    def _print_centered(self, text: str, color_key: str = "white"):
        """Print centered text.
        
        Args:
            text: Text to center
            color_key: Color key for the text
        """
        color = COLORS.get(color_key, COLORS["white"])
        padding = (min(self.terminal_width, 80) - len(text)) // 2
        centered_text = " " * padding + text
        print(f"{color}{centered_text}{COLORS['reset']}")
    
    def _wrap_text(self, text: str, indent: int = 0) -> str:
        """Wrap text to fit terminal width with optional indentation.
        
        Args:
            text: Text to wrap
            indent: Number of spaces to indent
            
        Returns:
            Wrapped text
        """
        import textwrap
        
        # Calculate available width
        available_width = min(self.terminal_width, 80) - indent
        
        # Wrap the text
        wrapped_lines = textwrap.wrap(text, width=available_width)
        
        # Add indentation
        indent_str = " " * indent
        return "\n".join(indent_str + line for line in wrapped_lines)
    
    def _get_personality_by_participant(self, participant_key: str) -> dict:
        """Get personality config by participant key.
        
        Args:
            participant_key: Participant key
            
        Returns:
            Personality configuration or None
        """
        return AGENT_PERSONALITIES.get(participant_key)
    
    def _get_personality_description(self, participant_key: str) -> str:
        """Get a brief description of the personality.
        
        Args:
            participant_key: Participant key
            
        Returns:
            Brief personality description
        """
        descriptions = {
            "optimist": "Focuses on positive aspects and solutions",
            "skeptic": "Questions assumptions and examines problems",
            "ethicist": "Examines moral implications and fairness",
            "moderator": "Facilitates discussion and maintains balance"
        }
        return descriptions.get(participant_key, "Contributes unique perspective")

class ProgressIndicator:
    """Simple progress indicator for long operations."""
    
    def __init__(self, message: str):
        """Initialize progress indicator.
        
        Args:
            message: Message to display
        """
        self.message = message
        self.is_running = False
    
    def start(self):
        """Start the progress indicator."""
        import threading
        import sys
        
        self.is_running = True
        
        def animate():
            chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
            i = 0
            while self.is_running:
                sys.stdout.write(f"\r{COLORS['cyan']}{chars[i]} {self.message}...{COLORS['reset']}")
                sys.stdout.flush()
                time.sleep(0.1)
                i = (i + 1) % len(chars)
            sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
            sys.stdout.flush()
        
        self.thread = threading.Thread(target=animate)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the progress indicator."""
        self.is_running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=0.2)