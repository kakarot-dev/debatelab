"""Debate manager for orchestrating group chat debates."""

import random
import time
from typing import List, Dict, Optional
import logging
from .agents import DebateAgentFactory, LocalLLMAgent
from .config import DEBATE_CONFIG, COLORS
from .display import DebateDisplay
from .summary_manager import SummaryManager
from .interactive_judge import InteractiveJudge

logger = logging.getLogger(__name__)

class DebateManager:
    """Manages the debate flow and group chat."""
    
    def __init__(self, topic: str, enable_moderator: bool = True):
        """Initialize the debate manager.
        
        Args:
            topic: The debate topic
            enable_moderator: Whether to include a moderator
        """
        self.topic = topic
        self.enable_moderator = enable_moderator
        self.agents = {}
        self.moderator = None
        self.judge = None
        self.display = DebateDisplay()
        self.conversation_history = []
        
        # Initialize new components
        self.summary_manager = SummaryManager()
        self.interactive_judge = None  # Will be initialized after judge is created
        
        self._setup_agents()
    
    def _setup_agents(self):
        """Set up all debate agents."""
        logger.info("Setting up debate agents...")
        
        # Create debate agents
        self.agents = DebateAgentFactory.create_all_agents()
        
        # Create judge
        self.judge = DebateAgentFactory.create_judge()
        
        # Initialize interactive judge system
        self.interactive_judge = InteractiveJudge(self.judge, self.summary_manager)
        
        # Create moderator if enabled
        if self.enable_moderator:
            self.moderator = DebateAgentFactory.create_moderator()
        
        logger.info(f"Created {len(self.agents)} debate agents, 1 interactive judge" +
                   (f" and 1 moderator" if self.moderator else ""))
    
    def start_debate(self) -> List[Dict]:
        """Start the debate and return the conversation history.
        
        Returns:
            List of conversation messages
        """
        self.display.show_debate_header(self.topic, list(self.agents.keys()))
        
        # Initial topic introduction
        initial_message = self._create_initial_message()
        
        try:
            # Start the group chat
            self.display.show_message("System", "Starting the debate...", "white")
            
            # Run natural conversation flow
            self._run_natural_conversation(initial_message)
            
        except Exception as e:
            logger.error(f"Error during debate: {e}")
            self.display.show_message("System", f"Debate ended due to error: {e}", "white")
        
        self.display.show_message("System", "Conversation completed.", "white")
        return self.conversation_history
    
    def _create_initial_message(self) -> str:
        """Create the initial debate message.
        
        Returns:
            Initial message string
        """
        return f"""Welcome to today's debate! Our topic is: "{self.topic}"

Let's have a thoughtful discussion where each participant can share their perspective. 
Remember to be respectful and build upon each other's ideas.

Who would like to start with their opening thoughts?"""
    
    def _run_natural_conversation(self, initial_message: str):
        """Run a natural conversation flow without rigid rounds.
        
        Args:
            initial_message: The initial message to start the debate
        """
        # Show initial message
        self.display.show_message("System", initial_message, "white")
        self.conversation_history.append({
            "name": "System",
            "content": initial_message
        })
        
        # Get list of debate agents
        debate_agents = list(self.agents.values())
        
        # Select the best starting agent
        current_speaker = self._select_best_starter(debate_agents)
        self.display.show_message("System", f"{current_speaker.name} will start the discussion.", "white")
        
        # Track conversation metrics
        total_exchanges = 0
        max_exchanges = DEBATE_CONFIG.get("max_exchanges", 20)  # Default to 20 exchanges
        min_exchanges = DEBATE_CONFIG.get("min_exchanges", 8)   # Default to 8 exchanges
        
        # Natural conversation flow
        while total_exchanges < max_exchanges:
            try:
                # Determine if this is the opening statement
                is_starter = (total_exchanges == 0)
                
                # Get response from current speaker
                response = self._get_agent_response(current_speaker, is_starter)
                if response:
                    self.display.show_message(current_speaker.name, response, current_speaker.personality["color"])
                    self.conversation_history.append({
                        "name": current_speaker.name,
                        "content": response
                    })
                    
                    total_exchanges += 1
                    
                    # Generate brief summary for this response
                    self.summary_manager.update_brief_summary(current_speaker.name, response, total_exchanges)
                    
                    # Check if judge intervention is needed
                    self._check_judge_intervention(current_speaker, response, total_exchanges)
                    
                    # Brief pause between speakers
                    time.sleep(1)
                    
                    # Select next speaker naturally based on conversation flow
                    current_speaker = self._select_next_speaker(debate_agents, current_speaker)
                    
                    # Periodic moderator intervention
                    if (self.moderator and
                        total_exchanges % DEBATE_CONFIG.get("moderator_frequency", 6) == 0 and
                        total_exchanges < max_exchanges - 2):
                        self._moderator_intervention(total_exchanges)
                    
                    # Check if conversation should end naturally
                    if total_exchanges >= min_exchanges and self._should_end_debate():
                        break
                        
                else:
                    # If speaker fails, try next speaker
                    current_speaker = self._select_next_speaker(debate_agents, current_speaker)
                    
            except Exception as e:
                logger.error(f"Error getting response from {current_speaker.name}: {e}")
                current_speaker = self._select_next_speaker(debate_agents, current_speaker)
                continue
        
        # Final evaluation and summary
        self._provide_final_evaluation()
    
    def _select_next_speaker(self, agents: List[LocalLLMAgent], current_speaker: LocalLLMAgent) -> LocalLLMAgent:
        """Select the next speaker based on natural conversation flow.
        
        Args:
            agents: Available agents
            current_speaker: The agent who just spoke
            
        Returns:
            Next speaker agent
        """
        # Simple rotation for now - can be enhanced with more intelligent selection
        current_index = agents.index(current_speaker)
        next_index = (current_index + 1) % len(agents)
        return agents[next_index]
    
    def _provide_final_evaluation(self):
        """Provide final evaluation and summary of the conversation."""
        if not self.conversation_history:
            return
            
        self.display.show_message("System", "\n" + "="*50, "white")
        self.display.show_message("System", "🏁 CONVERSATION COMPLETE 🏁", "white")
        self.display.show_message("System", "="*50, "white")
        
        # Get final detailed summary
        if self.summary_manager:
            final_summary = self.summary_manager.get_detailed_summary()
            if final_summary and final_summary != "No detailed summaries available yet.":
                self.display.show_message("System", "\n📋 CONVERSATION SUMMARY:", "white")
                self.display.show_message("System", final_summary, "white")
        
        # Judge's final evaluation if available
        if self.judge:
            try:
                # Count non-system messages for evaluation
                participant_messages = [
                    msg for msg in self.conversation_history
                    if msg.get("name") != "System"
                ]
                
                if participant_messages:
                    evaluation_prompt = f"""As Judge Sophia, provide a final evaluation of this debate on: "{self.topic}"

Please analyze:
1. Overall quality of arguments presented
2. How well participants engaged with each other's points
3. Most compelling arguments made
4. Areas where the discussion could have been stronger
5. Key insights that emerged from the conversation

Conversation included {len(participant_messages)} exchanges between the participants.

Provide a thoughtful final assessment:"""

                    success, final_evaluation = self.judge._custom_generate_reply(
                        messages=[{"content": evaluation_prompt, "name": "System"}],
                        sender=None
                    )
                    
                    if success and final_evaluation:
                        self.display.show_message("Judge Sophia", f"⚖️ Final Evaluation: {final_evaluation}", "blue")
                        
            except Exception as e:
                logger.error(f"Error in final evaluation: {e}")

    def _select_best_starter(self, agents: List[LocalLLMAgent]) -> LocalLLMAgent:
        """Select the best agent to start the debate based on the topic.
        
        Args:
            agents: Available agents
            
        Returns:
            The selected starter agent
        """
        # Ask the model which agent should start
        starter_prompt = f"""Given the debate topic: "{self.topic}"

Which of these debate personalities would be most appropriate to start the discussion?

1. Alex the Optimist - Focuses on positive aspects, opportunities, and solutions
2. Sam the Skeptic - Questions assumptions and examines potential problems  
3. Dr. Elena Ethics - Examines moral implications, fairness, and justice

Respond with just the number (1, 2, or 3) of the best starter."""

        try:
            from .llm_wrapper import get_llm
            llm = get_llm()
            response = llm.generate_response(starter_prompt, max_tokens=10)
            
            # Parse the response to get the agent
            if "1" in response:
                selected = next(agent for agent in agents if "Optimist" in agent.name)
            elif "2" in response:
                selected = next(agent for agent in agents if "Skeptic" in agent.name)
            elif "3" in response:
                selected = next(agent for agent in agents if "Ethics" in agent.name)
            else:
                # Default to optimist if unclear
                selected = next(agent for agent in agents if "Optimist" in agent.name)
                
            logger.info(f"Selected {selected.name} to start the debate")
            return selected
            
        except Exception as e:
            logger.error(f"Error selecting starter: {e}")
            # Default to first agent
            return agents[0]
    
    
    def _get_agent_response(self, agent: LocalLLMAgent, is_starter: bool = False) -> Optional[str]:
        """Get a response from an agent.
        
        Args:
            agent: The agent to get response from
            is_starter: Whether this agent should start the debate
            
        Returns:
            Agent's response or None if error
        """
        try:
            # Prepare context message
            if is_starter:
                context_message = self._prepare_starter_context(agent)
            else:
                context_message = self._prepare_context_for_agent(agent)
            
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
    
    def _prepare_starter_context(self, agent: LocalLLMAgent) -> str:
        """Prepare a special starter context for the first speaker.
        
        Args:
            agent: The starting agent
            
        Returns:
            Starter context message
        """
        return f"""Topic: {self.topic}
 YOU ARE THE OPENING SPEAKER

You have been selected as the best personality to start this debate. As the opening speaker, you have the important role of setting the foundation for the entire discussion.

Your responsibilities as the opening speaker:
- Present your opening perspective on this topic with detail
- Set the tone for yourself to be always on the right path
- Provide compelling arguments that will give other participants substantial material to respond to

Remember to stay true to your personality while making compelling arguments that will spark meaningful discussion. This is your moment to shape the direction of the entire debate."""
    
    def _prepare_context_for_agent(self, agent: LocalLLMAgent) -> str:
        """Prepare context message for an agent.
        
        Args:
            agent: The agent
            
        Returns:
            Context message
        """
        context_parts = [f"Topic: {self.topic}"]
        context_parts.append(f"\n{agent.name} - IT'S YOUR TURN TO SPEAK")
        
        # Give agents access to recent conversation history for better context
        # Include last 6 messages or all if fewer to prevent context overflow
        recent_history = self.conversation_history[-6:] if len(self.conversation_history) > 6 else self.conversation_history
        
        if recent_history:
            context_parts.append("\nConversation so far:")
            for msg in recent_history:
                if msg["name"] != agent.name and msg["name"] != "System":  # Don't include agent's own messages or system messages
                    content = msg['content']
                    context_parts.append(f"{msg['name']}: {content}")
        
        context_parts.append(f"\nAs the current speaker, your role is to:")
        context_parts.append("- Respond directly to the most compelling points made by other participants")
        context_parts.append("- Present your unique perspective with detailed reasoning and examples")
        context_parts.append("- Challenge weak arguments or build upon strong ones")
        context_parts.append("- Advance the conversation with new insights or evidence")
        context_parts.append("- Stay true to your personality while engaging meaningfully with the discussion")
        context_parts.append(f"\nNow share your thoughts:")
        
        return "\n".join(context_parts)
    
    def _moderator_intervention(self, exchange_num: int):
        """Have the moderator intervene in the discussion.
        
        Args:
            exchange_num: Current exchange number
        """
        if not self.moderator:
            return
        
        try:
            # Prepare moderator context
            context = self._prepare_moderator_context(exchange_num)
            
            # Get moderator response
            success, response = self.moderator._custom_generate_reply(
                messages=[{"content": context, "name": "System"}],
                sender=None
            )
            
            if success and response:
                self.display.show_message(self.moderator.name, response, self.moderator.personality["color"])
                self.conversation_history.append({
                    "name": self.moderator.name,
                    "content": response
                })
        
        except Exception as e:
            logger.error(f"Error with moderator intervention: {e}")
    
    def _prepare_moderator_context(self, exchange_num: int) -> str:
        """Prepare context for moderator intervention.
        
        Args:
            exchange_num: Current exchange number
            
        Returns:
            Moderator context message
        """
        context_parts = [
            f"Topic: {self.topic}",
            f"After {exchange_num} exchanges - Time for moderator intervention.",
            "\nRecent discussion summary:"
        ]
        
        # Summarize recent points
        recent_messages = self.conversation_history[-5:] if len(self.conversation_history) > 5 else self.conversation_history
        for msg in recent_messages:
            if msg["name"] != "System" and msg["name"] != self.moderator.name:
                context_parts.append(f"- {msg['name']}: {msg['content']}")
        
        context_parts.append("\nPlease summarize key points and ask a follow-up question to drive the discussion forward.")
        
        return "\n".join(context_parts)
    
    def _should_end_debate(self) -> bool:
        """Determine if the debate should end early.
        
        Returns:
            True if debate should end, False otherwise
        """
        # Simple heuristic: end if recent messages are very short or repetitive
        if len(self.conversation_history) < 3:
            return False
        
        recent_messages = self.conversation_history[-3:]
        avg_length = sum(len(msg["content"]) for msg in recent_messages) / len(recent_messages)
        
        # End if average message length is very short (indicates low engagement)
        return avg_length < 50
    
    def _check_judge_intervention(self, speaker: LocalLLMAgent, response: str, exchange_num: int):
        """Check if judge intervention is needed and handle it.
        
        Args:
            speaker: The speaker who just responded
            response: The speaker's response
            exchange_num: Current exchange number
        """
        if not self.interactive_judge:
            return
            
        try:
            # Analyze argument quality
            needs_clarification, weakness_type, confidence = self.interactive_judge.analyze_argument_quality(
                speaker.name, response, exchange_num
            )
            
            if needs_clarification and confidence > 0.6:
                # Generate clarifying question
                question = self.interactive_judge.generate_clarifying_question(
                    speaker.name, response, weakness_type, exchange_num
                )
                
                # Display judge's question
                self.display.show_message("Judge Sophia", f"🤔 {question}", "blue")
                
                # Get clarification from speaker
                clarification_prompt = f"""The judge has asked you a clarifying question about your recent argument:

Your argument: {response}

Judge's question: {question}

Please provide a brief clarification that addresses the judge's concern while staying true to your personality."""

                try:
                    success, clarification = speaker._custom_generate_reply(
                        messages=[{"content": clarification_prompt, "name": "Judge"}],
                        sender=None
                    )
                    
                    if success and clarification:
                        # Display clarification
                        self.display.show_message(speaker.name, f"📝 {clarification}", speaker.personality["color"])
                        
                        # Add clarification to conversation history
                        self.conversation_history.append({
                            "name": speaker.name,
                            "content": f"[Clarification] {clarification}",
                            "exchange": exchange_num
                        })
                        
                        # Evaluate the clarification
                        is_adequate, assessment = self.interactive_judge.evaluate_clarification(
                            response, clarification, weakness_type
                        )
                        
                        if is_adequate:
                            self.display.show_message("Judge Sophia", f"✅ {assessment}", "blue")
                        else:
                            self.display.show_message("Judge Sophia", f"⚠️ {assessment}", "blue")
                            
                except Exception as e:
                    logger.error(f"Error getting clarification from {speaker.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in judge intervention: {e}")

    def get_debate_summary(self) -> Dict:
        """Get a summary of the debate.
        
        Returns:
            Debate summary dictionary
        """
        return {
            "topic": self.topic,
            "total_exchanges": len(self.conversation_history),
            "total_messages": len(self.conversation_history),
            "participants": [agent.name for agent in self.agents.values()],
            "moderator_used": self.moderator is not None,
            "conversation_history": self.conversation_history
        }