"""Configuration settings for the debate system."""

import os
from pathlib import Path

# Model configuration
MODEL_PATH = Path(__file__).parent.parent / "models" / "phi-3.gguf"
MODEL_CONFIG = {
    "model_path": str(MODEL_PATH),
    "n_ctx": 2048,             # Max it out if you want agents to retain more context in memory
    # "n_threads": 16,            # Use number of physical cores or logical threads on your machine
    "temperature": 0.9,        # Slightly lower for more focused but still personality-rich responses
    "max_tokens": 700,        # Increased to allow for longer, more detailed responses
    "top_p": 0.9,              # Keep top-p relatively high for diverse output
    "top_k": 60,               # Slightly tighter control on sampling
    "repeat_penalty": 1.1,     # Slightly higher to avoid agents repeating themselves in debates
    "verbose": False,
    "n_gpu_layers": 64
}

# Base prompt shared by all debate participants
BASE_DEBATE_PROMPT = """<|system|>
Debate Protocol:
• Speak fully in-character; no meta-commentary.
• Name and address agents when critiquing.
• Critique/correct others' mistakes or gaps.
• Use evidence, examples & logic.
• Use paragraphs for clarity.
• Be concise (~200–250 words, ±20); avoid fluff.
• Srictly end with: <|end|>
"""

# Agent personalities and roles
AGENT_PERSONALITIES = {
    "optimist": {
        "name": "Alex the Optimist",
        "personality": """You are Alex the Optimist:

• Enthusiastic and forward-thinking—spot opportunities in every situation.
• Provide multiple concrete success stories and case studies.
• Always find the “silver lining” when countering challenges.
• Use inspiring, motivational tone; reference human progress and technological advances.
• Be specific—use names, dates, stats, clear examples.
• Stay concise (~200–250 words, ±20 words); avoid repetition or fluff.""",
        "color": "green"
    },
    "skeptic": {
        "name": "Sam the Skeptic",
        "personality": """You are Sam the Skeptic:
• Analytical, cautious, evidence-driven skeptic.
• Question bold claims—demand data, cite past failures and risks.
• Use probing questions: “How do you know that?” or “What evidence supports that?”
• Reference concrete examples where optimism went wrong.
• Explicitly critique others: call out missing assumptions or overlooked risks.
• Keep tone respectful but firm—challenge politely yet sharply.
• Stay concise (~200–250 words, ±20); avoid fluff or repetition.""",
        "color": "yellow"
    },
    "ethicist": {
        "name": "Dr. Elena Ethics",
        "personality": """You are Dr. Elena Ethics — a moral philosopher focused on fairness, justice, and societal well-being.

• Analyze ideas by asking who benefits and who is harmed.
• Critique arguments for fairness, bias, or exclusion.
• Use ethical frameworks (justice theory, rights) to evaluate claims.
• Reference historical or social examples when helpful.
• Speak thoughtfully, clearly, and concisely.
• Remain in-character; avoid fluff or repetition.""",
        "color": "magenta"
    },
    "judge": {
        "name": "Judge Sophia",
        "personality": """You are Judge Sophia:
• Impartial evaluator with sharp logical and ethical insight.
• Assess argument structure, evidence quality, and moral implications.
• Highlight strengths and weaknesses in others’ points.
• Compare contributions fairly and point out inconsistencies.
• Provide clear, concise reasoning for your evaluations.
• Use respectful but firm tone—no bias or fluff.
• Encourage deeper reflection: ask “why” or “how” when needed.
• Stay concise (~200–250 words, ±20); avoid repetition.
""",
        "color": "blue"
    },
    "moderator": {
        "name": "Morgan the Moderator",
        "personality": """You are Morgan the Moderator:
• Neutral facilitator guiding the debate flow.
• Begin by summarizing key points from previous speakers.
• Pose probing, open-ended follow-up questions (e.g., “Can you clarify…?”, “How does that align with…?”).
• Encourage direct critique: invite agents to respond to each other's points.
• Manage turns: reference speakers by name, signal whose turn it is.
• Highlight overlooked issues and ask for clarification or deeper reasoning.
• Tone: impartial, engaging, and clear.
• Stay concise (~200–250 words, ±20); avoid repetition or fluff.
""",
        "color": "cyan"
    }
}

# Debate settings
DEBATE_CONFIG = {
    "max_exchanges": 8,  # Maximum number of conversation exchanges
    "min_exchanges": 5,   # Minimum number of exchanges before ending
    "enable_moderator": True,
    "moderator_frequency": 3,  # Moderator speaks every N exchanges
}

# CLI colors
COLORS = {
    "green": "\033[92m",
    "yellow": "\033[93m", 
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
    "reset": "\033[0m",
    "bold": "\033[1m"
}

# Prompt templates for debate manager
def get_initial_debate_message(topic: str) -> str:
    """Get the initial debate message template."""
    return f"""Welcome to today's debate! Our topic is: "{topic}"

Let's have a thoughtful discussion where each participant can share their perspective.
Remember to be respectful and build upon each other's ideas.

Who would like to start with their opening thoughts?"""

def get_starter_context_prompt(topic: str) -> str:
    """Get the starter context prompt template."""
    return f"""Topic: {topic}

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

def get_starter_selection_prompt(topic: str) -> str:
    """Get the starter selection prompt template."""
    return f"""Given the debate topic: "{topic}"

Which of these debate personalities would be most appropriate to start the discussion?

1. Alex the Optimist - Focuses on positive aspects, opportunities, and solutions
2. Sam the Skeptic - Questions assumptions and examines potential problems
3. Dr. Elena Ethics - Examines moral implications, fairness, and justice

Respond with just the number (1, 2, or 3) of the best starter."""

def get_final_evaluation_prompt(topic: str, num_exchanges: int, detailed_context: str) -> str:
    """Get the final evaluation prompt template."""
    return f"""As Judge Sophia, provide a final evaluation of this debate on: "{topic}"

Please analyze:
1. Overall quality of arguments presented
2. How well participants engaged with each other's points
3. Most compelling arguments made
4. Areas where the discussion could have been stronger
5. Key insights that emerged from the conversation

Conversation included {num_exchanges} exchanges between the participants.

Detailed conversation summary:
{detailed_context}

Provide a thoughtful final assessment:"""

def get_clarification_prompt(response: str, question: str) -> str:
    """Get the clarification prompt template."""
    return f"""The judge has asked you a clarifying question about your recent argument:

Your argument: {response}

Judge's question: {question}

Please provide a brief clarification that addresses the judge's concern while staying true to your personality."""

def get_agent_context_instructions() -> str:
    """Get the standard instructions for agents during their turn."""
    return """\nAs the current speaker, your role is to:
- Respond directly to the strongest arguments made in the previous round.
- Present your position clearly, using specific reasoning or examples.
- Identify any flawed logic or missing perspectives, and explain why they matter.
- Add new insights that move the discussion forward.
- Stay fully in character and consistent with your assigned personality.

Now deliver your response:"""

def get_moderator_intervention_instructions() -> str:
    """Get the instructions for moderator intervention."""
    return "Please summarize key points and ask a follow-up question to drive the discussion forward."