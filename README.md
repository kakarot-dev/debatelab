# AI Debate Arena 🎭

A sophisticated debate system that uses AutoGen's groupchat module to orchestrate debates between multiple AI agents with distinct personalities, powered by a local GGUF model.

## Features

- **Multiple AI Personalities**: 4 distinct debate agents with unique perspectives:
  - **Alex the Optimist**: Focuses on positive aspects and solutions
  - **Sam the Skeptic**: Questions assumptions and examines problems
  - **Pat the Pragmatist**: Emphasizes practical implementation and costs
  - **Iris the Idealist**: Champions principles and moral standards
  
- **Optional Moderator**: Morgan the Moderator facilitates discussion and maintains balance

- **Local LLM Integration**: Uses your local GGUF model (phi-3.gguf) for complete privacy

- **Rich CLI Interface**: Colorized output with real-time debate visualization

- **Flexible Topic Input**: Command-line arguments or interactive prompts

- **Debate Export**: Save debates to JSON for later analysis

## Project Structure

```
debatelab/
├── models/
│   └── phi-3.gguf              # Your GGUF model file
├── src/
│   ├── __init__.py             # Package initialization
│   ├── main.py                 # CLI interface and main entry point
│   ├── config.py               # Configuration settings and personalities
│   ├── llm_wrapper.py          # Local LLM interface wrapper
│   ├── agents.py               # Custom AutoGen agents
│   ├── debate_manager.py       # Debate orchestration logic
│   └── display.py              # CLI display utilities
├── run_debate.py               # Simple runner script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify Model**: Ensure your GGUF model file is in the `models/` directory:
   ```bash
   ls models/
   # Should show: phi-3.gguf
   ```

## Usage

### Quick Start

```bash
# Simple usage with topic as argument
python run_debate.py "Should AI replace human teachers?"

# Or using module syntax
python -m src.main "Is remote work better than office work?"
```

### Interactive Mode

```bash
# Interactive mode - prompts for topic
python run_debate.py --interactive
```

### Advanced Options

```bash
# Disable moderator
python run_debate.py "Climate change solutions" --no-moderator

# Save debate output to file
python run_debate.py "Nuclear energy debate" --save-output debate_output.json

# Verbose logging
python run_debate.py "Social media regulation" --verbose

# List available personalities
python run_debate.py --list-personalities
```

### Command Line Options

```
positional arguments:
  topic                 The debate topic

optional arguments:
  -h, --help            Show help message
  --topic TOPIC, -t TOPIC
                        Alternative way to specify topic
  --no-moderator        Disable the moderator agent
  --interactive, -i     Run in interactive mode with prompts
  --list-personalities  List available agent personalities
  --save-output FILE    Save debate output to JSON file
  --verbose, -v         Enable verbose logging
```

## Example Debate Topics

- "Should artificial intelligence replace human teachers?"
- "Is remote work better than office work?"
- "Should social media be regulated by governments?"
- "Is nuclear energy the solution to climate change?"
- "Should universal basic income be implemented?"
- "Is space exploration worth the investment?"

## How It Works

1. **Initialization**: The system loads the local GGUF model and creates AI agents with distinct personalities
2. **Topic Introduction**: The debate topic is presented to all participants
3. **Structured Rounds**: Agents take turns presenting their perspectives in organized rounds
4. **Moderator Intervention**: The moderator periodically summarizes and asks follow-up questions
5. **Natural Conclusion**: The debate concludes after meaningful discussion

## Agent Personalities

### Alex the Optimist 🌟
- **Color**: Green
- **Focus**: Positive aspects, solutions, human potential
- **Style**: Enthusiastic and hopeful

### Sam the Skeptic 🔍
- **Color**: Yellow  
- **Focus**: Critical thinking, potential problems, evidence
- **Style**: Analytical and probing

### Pat the Pragmatist 🔧
- **Color**: Blue
- **Focus**: Real-world implications, feasibility, costs
- **Style**: Grounded and solution-oriented

### Iris the Idealist ✨
- **Color**: Magenta
- **Focus**: Principles, values, moral standards
- **Style**: Principled and inspiring

### Morgan the Moderator ⚖️
- **Color**: Cyan
- **Focus**: Facilitation, balance, summarization
- **Style**: Neutral and guiding

## Configuration

Key settings can be modified in [`src/config.py`](src/config.py):

- **Model Settings**: Path, context window, temperature, etc.
- **Debate Parameters**: Max rounds, speakers per round, moderator frequency
- **Agent Personalities**: System messages and colors
- **Display Options**: Colors and formatting

## Output Format

When using `--save-output`, debates are saved as JSON with this structure:

```json
{
  "debate_summary": {
    "topic": "Your debate topic",
    "total_rounds": 6,
    "total_messages": 15,
    "participants": ["Alex the Optimist", "Sam the Skeptic", ...],
    "moderator_used": true
  },
  "conversation_history": [
    {
      "name": "Alex the Optimist",
      "content": "I believe this topic offers great opportunities...",
      "round": 1
    }
  ]
}
```

## Troubleshooting

### Model Not Found
```
ERROR: Model file not found: /path/to/models/phi-3.gguf
```
**Solution**: Ensure your GGUF model file is in the `models/` directory and named `phi-3.gguf`

### Import Errors
```
ModuleNotFoundError: No module named 'autogen'
```
**Solution**: Install dependencies with `pip install -r requirements.txt`

### Memory Issues
If you encounter memory issues:
1. Reduce `n_ctx` in [`src/config.py`](src/config.py)
2. Lower `max_tokens` per response
3. Use a smaller GGUF model

### Performance Issues
For better performance:
1. Increase `n_threads` in model config
2. Use GPU acceleration if available with llama-cpp-python
3. Reduce conversation history length

## Logs

The system creates a `debate.log` file with detailed logging information for debugging purposes.

## Dependencies

- **pyautogen**: AutoGen framework for multi-agent conversations
- **llama-cpp-python**: Python bindings for llama.cpp (GGUF model support)
- **colorama**: Cross-platform colored terminal text
- **argparse**: Command-line argument parsing (built-in)

## License

This project is open source. Feel free to modify and extend it for your needs.

## Contributing

Contributions are welcome! Areas for improvement:
- Additional agent personalities
- Better conversation flow algorithms
- Web interface
- Integration with other LLM backends
- Enhanced debate analysis features

---

**Enjoy debating with AI! 🎭**
