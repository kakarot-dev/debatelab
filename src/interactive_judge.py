"""Interactive judge system for real-time debate evaluation and intervention."""

import logging
from typing import Dict, List, Optional, Tuple
from .llm_wrapper import get_llm
from .summary_manager import SummaryManager

logger = logging.getLogger(__name__)

class InteractiveJudge:
    """Interactive judge that can analyze arguments and ask clarifying questions."""
    
    def __init__(self, judge_agent, summary_manager: SummaryManager):
        """Initialize the interactive judge.
        
        Args:
            judge_agent: The judge agent instance
            summary_manager: Summary manager for context
        """
        self.judge_agent = judge_agent
        self.summary_manager = summary_manager
        self.llm = None
        self.intervention_history = []
        
        # Weak argument patterns for quick detection
        self.weak_patterns = {
            "missing_evidence": [
                "obviously", "clearly", "everyone knows", "it's common sense",
                "without a doubt", "undeniably", "certainly"
            ],
            "logical_gaps": [
                "therefore", "thus", "so", "hence", "consequently"
            ],
            "vague_language": [
                "some people", "many believe", "it seems", "probably",
                "might", "could be", "perhaps", "maybe"
            ],
            "weak_connections": [
                "anyway", "moving on", "in any case", "regardless"
            ]
        }
    
    def _get_llm(self):
        """Get LLM instance lazily."""
        if not self.llm:
            self.llm = get_llm()
        return self.llm
    
    def analyze_argument_quality(self, speaker: str, argument: str, exchange_num: int) -> Tuple[bool, str, float]:
        """Quickly analyze argument quality to determine if intervention is needed.
        
        Args:
            speaker: Name of the speaker
            argument: The argument content
            exchange_num: Current exchange number
        
        Returns:
            Tuple of (needs_clarification, weakness_type, confidence_score)
        """
        # Quick heuristic checks
        weakness_type, confidence = self._quick_weakness_detection(argument, exchange_num)
        
        if confidence > 0.7:  # High confidence in weakness detection
            return True, weakness_type, confidence
        
        # If heuristics are inconclusive, use LLM for deeper analysis
        if confidence > 0.3:  # Medium confidence, worth checking
            return self._llm_quality_analysis(speaker, argument, exchange_num)
        
        return False, "none", confidence
    
    def _quick_weakness_detection(self, argument: str, exchange_num: int) -> Tuple[str, float]:
        """Use heuristics to quickly detect argument weaknesses.
        
        Args:
            argument: The argument to analyze
            
        Returns:
            Tuple of (weakness_type, confidence_score)
        """
        argument_lower = argument.lower()
        word_count = len(argument.split())
        
        # Check for very short arguments
        if word_count < 20:
            return "insufficient_detail", 0.8
        
        # Check for weak evidence patterns
        evidence_score = 0
        for pattern in self.weak_patterns["missing_evidence"]:
            if pattern in argument_lower:
                evidence_score += 0.3
        
        if evidence_score > 0.6:
            return "missing_evidence", min(evidence_score, 0.9)
        
        # Check for logical gaps
        logical_score = 0
        conclusion_words = sum(1 for pattern in self.weak_patterns["logical_gaps"] 
                              if pattern in argument_lower)
        if conclusion_words > 2 and "because" not in argument_lower and "since" not in argument_lower:
            logical_score = 0.7
        
        if logical_score > 0.6:
            return "logical_gaps", logical_score
        
        # Check for vague language
        vague_score = 0
        for pattern in self.weak_patterns["vague_language"]:
            if pattern in argument_lower:
                vague_score += 0.2
        
        if vague_score > 0.6:
            return "vague_language", min(vague_score, 0.8)
        
        # Check for poor engagement
        if word_count > 50:  # Only check engagement for longer responses
            engagement_score = 0
            other_speaker_mentions = argument_lower.count("alex") + argument_lower.count("sam") + argument_lower.count("elena")
            if other_speaker_mentions == 0 and exchange_num > 1:
                engagement_score = 0.6
            
            if engagement_score > 0.5:
                return "weak_connections", engagement_score
        
        return "none", 0.1
    
    def _llm_quality_analysis(self, speaker: str, argument: str, exchange_num: int) -> Tuple[bool, str, float]:
        """Use LLM for deeper argument quality analysis.
        
        Args:
            speaker: Name of the speaker
            argument: The argument content
            exchange_num: Current exchange number
        
        Returns:
            Tuple of (needs_clarification, weakness_type, confidence_score)
        """
        # Get brief context for analysis
        context = self.summary_manager.get_context_for_judge("quick", exchange_num, [])
        
        prompt = f"""Analyze this debate argument for potential weaknesses that might need clarification:

Context: {context}

Current Speaker: {speaker}
Argument: {argument}

Check for these issues:
1. Missing evidence or examples
2. Logical gaps or unsupported conclusions
3. Vague or unclear language
4. Poor engagement with other participants' points

Respond in this format:
NEEDS_CLARIFICATION: Yes/No
WEAKNESS_TYPE: missing_evidence/logical_gaps/vague_language/weak_connections/none
CONFIDENCE: 0.0-1.0
BRIEF_REASON: One sentence explanation"""

        try:
            llm = self._get_llm()
            response = llm.generate_response(prompt, max_tokens=150)
            
            # Parse response
            lines = response.strip().split('\n')
            needs_clarification = False
            weakness_type = "none"
            confidence = 0.0
            
            for line in lines:
                if line.startswith("NEEDS_CLARIFICATION:"):
                    needs_clarification = "yes" in line.lower()
                elif line.startswith("WEAKNESS_TYPE:"):
                    weakness_type = line.split(":", 1)[1].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence = float(line.split(":", 1)[1].strip())
                    except ValueError:
                        confidence = 0.5
            
            return needs_clarification, weakness_type, confidence
            
        except Exception as e:
            logger.error(f"Error in LLM quality analysis: {e}")
            return False, "none", 0.0
    
    def generate_clarifying_question(self, speaker: str, argument: str, weakness_type: str, exchange_num: int) -> str:
        """Generate a targeted clarifying question based on detected weakness.
        
        Args:
            speaker: Name of the speaker
            argument: The original argument
            weakness_type: Type of weakness detected
            exchange_num: Current exchange number
            
        Returns:
            Clarifying question for the speaker
        """
        # Get brief context
        context = self.summary_manager.get_context_for_judge("quick", exchange_num, [])
        
        # Create question templates based on weakness type
        question_templates = {
            "missing_evidence": f"{speaker}, could you provide specific examples or evidence to support your claim?",
            "logical_gaps": f"{speaker}, could you explain the reasoning that connects your premises to your conclusion?",
            "vague_language": f"{speaker}, could you be more specific about what you mean by that?",
            "weak_connections": f"{speaker}, how does your point relate to what the other participants have said?",
            "insufficient_detail": f"{speaker}, could you elaborate on your argument with more detail?"
        }
        
        base_question = question_templates.get(weakness_type, 
                                             f"{speaker}, could you clarify your argument?")
        
        # Use LLM to create a more contextual question
        prompt = f"""Create a specific clarifying question for this debate situation:

Context: {context}

Speaker: {speaker}
Argument: {argument}
Weakness Type: {weakness_type}
Base Question: {base_question}

Generate a professional, specific clarifying question that addresses the weakness while maintaining the debate flow. Keep it concise (1-2 sentences).

Question:"""

        try:
            llm = self._get_llm()
            question = llm.generate_response(prompt, max_tokens=100)
            question = question.strip()
            
            # Ensure question ends with question mark
            if not question.endswith('?'):
                question += '?'
            
            # Log the intervention
            self.intervention_history.append({
                "exchange": exchange_num,
                "speaker": speaker,
                "weakness_type": weakness_type,
                "question": question
            })
            
            return question
            
        except Exception as e:
            logger.error(f"Error generating clarifying question: {e}")
            return base_question
    
    def evaluate_clarification(self, original_argument: str, clarification: str, weakness_type: str) -> Tuple[bool, str]:
        """Evaluate if the clarification adequately addresses the weakness.
        
        Args:
            original_argument: The original argument
            clarification: The speaker's clarification
            weakness_type: Type of weakness that was addressed
            
        Returns:
            Tuple of (is_adequate, brief_assessment)
        """
        prompt = f"""Evaluate if this clarification adequately addresses the identified weakness:

Original Argument: {original_argument}

Weakness Type: {weakness_type}

Clarification: {clarification}

Does the clarification adequately address the weakness?

Respond in this format:
ADEQUATE: Yes/No
ASSESSMENT: Brief explanation (1 sentence)"""

        try:
            llm = self._get_llm()
            response = llm.generate_response(prompt, max_tokens=100)
            
            # Parse response
            lines = response.strip().split('\n')
            is_adequate = False
            assessment = "Clarification provided."
            
            for line in lines:
                if line.startswith("ADEQUATE:"):
                    is_adequate = "yes" in line.lower()
                elif line.startswith("ASSESSMENT:"):
                    assessment = line.split(":", 1)[1].strip()
            
            return is_adequate, assessment
            
        except Exception as e:
            logger.error(f"Error evaluating clarification: {e}")
            return True, "Clarification accepted."
    
    def get_intervention_stats(self) -> Dict:
        """Get statistics about judge interventions.
        
        Returns:
            Dictionary with intervention statistics
        """
        if not self.intervention_history:
            return {"total_interventions": 0}
        
        weakness_counts = {}
        for intervention in self.intervention_history:
            weakness_type = intervention["weakness_type"]
            weakness_counts[weakness_type] = weakness_counts.get(weakness_type, 0) + 1
        
        return {
            "total_interventions": len(self.intervention_history),
            "weakness_breakdown": weakness_counts,
            "exchanges_with_interventions": len(set(i["exchange"] for i in self.intervention_history))
        }