"""Summary manager for efficient conversation context management."""

import logging
from typing import Dict, List, Optional
from .llm_wrapper import get_llm

logger = logging.getLogger(__name__)

class SummaryManager:
    """Manages multi-level conversation summaries for efficient context handling."""
    
    def __init__(self):
        """Initialize the summary manager."""
        self.brief_summaries = {}  # {round: {speaker: brief_summary}}
        self.detailed_summaries = {}  # {round: detailed_summary}
        self.llm = None
        
    def _get_llm(self):
        """Get LLM instance lazily."""
        if not self.llm:
            self.llm = get_llm()
        return self.llm
    
    def update_brief_summary(self, speaker: str, content: str, exchange_num: int) -> str:
        """Generate and store a brief summary of speaker's contribution.
        
        Args:
            speaker: Name of the speaker
            content: Full content of the speaker's response
            exchange_num: Current round number
            
        Returns:
            Brief summary (1-2 sentences)
        """
        if exchange_num not in self.brief_summaries:
            self.brief_summaries[exchange_num] = {}
            
        # Create brief summary prompt
        prompt = f"""Summarize this debate contribution in 1-2 concise sentences, focusing on the main argument and key evidence:

Speaker: {speaker}
Content: {content}

Summary:"""

        try:
            llm = self._get_llm()
            summary = llm.generate_response(prompt, max_tokens=100)
            
            # Clean and store the summary
            summary = summary.strip()
            if not summary.endswith('.'):
                summary += '.'
                
            self.brief_summaries[exchange_num][speaker] = summary
            logger.debug(f"Generated brief summary for {speaker} in exchange {exchange_num}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating brief summary: {e}")
            # Fallback to truncated content
            fallback = content[:150] + "..." if len(content) > 150 else content
            self.brief_summaries[exchange_num][speaker] = fallback
            return fallback
    
    def generate_detailed_summary(self, exchange_num: int, conversation_history: List[Dict]) -> str:
        """Generate a detailed summary of the entire round.
        
        Args:
            exchange_num: Round number to summarize
            conversation_history: Full conversation history
            
        Returns:
            Detailed summary of the round
        """
        # Get all messages from this round
        exchange_messages = [
            msg for msg in conversation_history 
            if msg.get("exchange") == exchange_num and msg.get("name") != "System"
        ]
        
        if not exchange_messages:
            return f"Round {exchange_num}: No contributions recorded."
            
        # Create detailed summary prompt
        exchange_content = "\n".join([
            f"{msg['name']}: {msg['content']}"
            for msg in exchange_messages
        ])
        
        prompt = f"""Create a comprehensive summary of this debate exchange, including:
1. Main arguments presented by each participant
2. Key evidence and examples used
3. How participants engaged with each other's points
4. Overall quality and direction of the discussion

Exchange {exchange_num} Content:
{exchange_content}

Detailed Summary:"""

        try:
            llm = self._get_llm()
            summary = llm.generate_response(prompt, max_tokens=400)
            
            # Clean and store the summary
            summary = summary.strip()
            self.detailed_summaries[exchange_num] = summary
            logger.debug(f"Generated detailed summary for exchange {exchange_num}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating detailed summary: {e}")
            # Fallback to basic summary
            fallback = f"Round {exchange_num}: {len(exchange_messages)} contributions from participants."
            self.detailed_summaries[exchange_num] = fallback
            return fallback
    
    def get_context_for_judge(self, decision_type: str, exchange_num: int, 
                             conversation_history: List[Dict]) -> str:
        """Get appropriate context for judge based on decision type.
        
        Args:
            decision_type: 'quick' for intervention decisions, 'detailed' for final evaluation
            exchange_num: Current round number
            conversation_history: Full conversation history
            
        Returns:
            Formatted context string
        """
        if decision_type == "quick":
            return self._get_quick_context(exchange_num)
        elif decision_type == "detailed":
            return self._get_detailed_context(exchange_num, conversation_history)
        else:
            raise ValueError(f"Unknown decision type: {decision_type}")
    
    def _get_quick_context(self, exchange_num: int) -> str:
        """Get brief context for quick judge decisions.
        
        Args:
            exchange_num: Current round number
            
        Returns:
            Brief context summary
        """
        context_parts = []
        
        # Include brief summaries from current round
        if exchange_num in self.brief_summaries:
            context_parts.append(f"Round {exchange_num} contributions:")
            for speaker, summary in self.brief_summaries[exchange_num].items():
                context_parts.append(f"- {speaker}: {summary}")
        
        # Include previous round's detailed summary if available
        prev_exchange = exchange_num - 1
        if prev_exchange in self.detailed_summaries:
            context_parts.append(f"\nPrevious exchange summary: {self.detailed_summaries[prev_exchange]}")
        
        return "\n".join(context_parts) if context_parts else "No context available."
    
    def _get_detailed_context(self, exchange_num: int, conversation_history: List[Dict]) -> str:
        """Get comprehensive context for final judge evaluation.
        
        Args:
            exchange_num: Current round number
            conversation_history: Full conversation history
            
        Returns:
            Detailed context summary
        """
        context_parts = []
        
        # Generate detailed summary for current round if not exists
        if exchange_num not in self.detailed_summaries:
            self.generate_detailed_summary(exchange_num, conversation_history)
        
        # Include detailed summaries from all rounds
        for r in range(1, exchange_num + 1):
            if r in self.detailed_summaries:
                context_parts.append(f"Round {r}: {self.detailed_summaries[r]}")
        
        return "\n\n".join(context_parts) if context_parts else "No detailed context available."
    
    def get_summary_stats(self) -> Dict:
        """Get statistics about current summaries.
        
        Returns:
            Dictionary with summary statistics
        """
        total_brief = sum(len(round_summaries) for round_summaries in self.brief_summaries.values())
        total_detailed = len(self.detailed_summaries)
        
        return {
            "brief_summaries": total_brief,
            "detailed_summaries": total_detailed,
            "exchanges_covered": len(self.brief_summaries)
        }
    
    def get_detailed_summary(self) -> str:
        """Get a comprehensive detailed summary of all rounds.
        
        Returns:
            Combined detailed summary of all rounds
        """
        if not self.detailed_summaries:
            return "No detailed summaries available yet."
        
        summary_parts = []
        for exchange_num in sorted(self.detailed_summaries.keys()):
            summary_parts.append(f"Exchange {exchange_num}: {self.detailed_summaries[exchange_num]}")
        
        return "\n\n".join(summary_parts)
    
    def update_summaries(self, conversation_history: List[Dict]):
        """Update summaries based on current conversation history.
        
        Args:
            conversation_history: Full conversation history
        """
        # Find the latest exchange number
        latest_exchange = 0
        for msg in conversation_history:
            if msg.get("exchange", 0) > latest_exchange:
                latest_exchange = msg.get("exchange", 0)
        
        # Generate detailed summary for the latest exchange if not exists
        if latest_exchange > 0 and latest_exchange not in self.detailed_summaries:
            self.generate_detailed_summary(latest_exchange, conversation_history)