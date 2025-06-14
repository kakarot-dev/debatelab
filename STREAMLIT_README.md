# DebateLab Streamlit Interface

This document explains how to use the Streamlit web interface for the DebateLab debate system.

## 🚀 Quick Start

### Option 1: Using the Launch Script (Recommended)
```bash
python run_streamlit.py
```

### Option 2: Direct Streamlit Command
```bash
# Simple interface
streamlit run src/debate_app.py

# Advanced interface (more features)
streamlit run streamlit_app.py
```

### Option 3: Through Main CLI
```bash
python -m src.main --streamlit
```

## 📋 Prerequisites

1. **Model File**: Ensure you have a GGUF model file in the `models/` directory (e.g., `models/phi-3.gguf`)
2. **Dependencies**: Install required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. **Optional**: For document upload support, install textract:
   ```bash
   pip install textract
   ```

## 🎭 Features

### Simple Interface (`src/debate_app.py`)
- Clean, focused interface for running debates
- Real-time chat display with agent avatars
- Document upload support
- Debate history with recent debates
- Progress tracking during debates

### Advanced Interface (`streamlit_app.py`)
- Full-featured interface with extensive controls
- Configurable debate settings (moderator, max exchanges)
- Comprehensive debate history with download options
- Detailed agent personality information
- File upload with multiple format support
- Debate session management

## 🎯 How to Use

1. **Start the App**: Use one of the launch methods above
2. **Enter Topic**: Type your debate topic in the text input field
3. **Quick Start**: Click on example topics for instant debates
4. **Upload Documents** (Optional): Upload PDF, DOCX, TXT, or PPTX files for context
5. **Start Debate**: Click "🚀 Start Debate" to begin
6. **Watch the Debate**: AI agents will discuss the topic in real-time
7. **Review History**: Check previous debates in the history section

## 🤖 AI Agents

The system includes several AI agents with distinct personalities:

- **😊 Alex the Optimist**: Focuses on positive aspects and opportunities
- **🤔 Sam the Skeptic**: Questions assumptions and examines problems
- **⚖️ Dr. Elena Ethics**: Analyzes moral implications and fairness
- **👩‍⚖️ Judge Sophia**: Provides impartial evaluation and insights
- **🎯 Morgan the Moderator**: Facilitates discussion (optional)

## 📁 File Structure

```
debatelab/
├── src/
│   ├── main.py              # Enhanced main entry point with Streamlit support
│   ├── debate_app.py        # Simple Streamlit interface
│   ├── debate_manager.py    # Core debate logic
│   └── ...                  # Other source files
├── streamlit_app.py         # Advanced Streamlit interface
├── run_streamlit.py         # Launch script
└── requirements.txt         # Dependencies
```

## 🔧 Configuration

### Debate Settings (Advanced Interface)
- **Enable Moderator**: Toggle moderator participation
- **Max Exchanges**: Set maximum number of debate rounds (5-20)

### Model Configuration
Edit `src/config.py` to adjust:
- Model path and parameters
- Agent personalities
- Debate flow settings

## 🐛 Troubleshooting

### Common Issues

1. **Model Not Found**
   - Ensure GGUF model file is in `models/` directory
   - Check `MODEL_PATH` in `src/config.py`

2. **Import Errors**
   - Install missing dependencies: `pip install -r requirements.txt`
   - For document upload: `pip install textract`

3. **Slow Performance**
   - Adjust model parameters in `src/config.py`
   - Reduce `max_exchanges` in debate settings

4. **Port Already in Use**
   - Streamlit default port is 8501
   - Use: `streamlit run src/debate_app.py --server.port 8502`

### Debug Mode
Enable verbose logging by setting environment variable:
```bash
export STREAMLIT_LOGGER_LEVEL=debug
streamlit run src/debate_app.py
```

## 🚀 Advanced Usage

### Custom Topics
Create engaging debate topics by:
- Making them specific and focused
- Ensuring they have multiple valid perspectives
- Using current, relevant issues
- Framing as questions or statements

### Document Context
Upload relevant documents to provide context:
- Research papers for academic topics
- News articles for current events
- Policy documents for governance topics
- Technical specs for technology debates

### Saving Debates
- Simple interface: Debates auto-save to session history
- Advanced interface: Download debates as JSON files
- History persists during browser session

## 📊 Example Topics

- "Should AI replace human teachers in primary education?"
- "Is remote work more productive than office work?"
- "Should governments regulate social media platforms?"
- "Is nuclear energy the best solution to climate change?"
- "Should universal basic income be implemented globally?"
- "Is cryptocurrency a viable alternative to traditional currency?"
- "Should genetic engineering be used to enhance human capabilities?"

## 🤝 Contributing

To extend the Streamlit interface:
1. Modify `src/debate_app.py` for simple changes
2. Edit `streamlit_app.py` for advanced features
3. Update `src/main.py` for CLI integration
4. Test with `python run_streamlit.py`

## 📝 Notes

- Debates run locally using your GGUF model
- No data is sent to external services
- Session state persists during browser session
- For production deployment, consider Streamlit Cloud or Docker