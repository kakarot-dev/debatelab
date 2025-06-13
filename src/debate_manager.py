"""Debate manager for orchestrating group chat debates."""
import time
from typing import List, Dict, Optional
import logging
from .agents import DebateAgentFactory, LocalLLMAgent
from .config import (
    DEBATE_CONFIG, COLORS,
    get_initial_debate_message, get_starter_context_prompt, get_starter_selection_prompt,
    get_final_evaluation_prompt, get_clarification_prompt, get_agent_context_instructions,
    get_moderator_intervention_instructions
)
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
        return get_initial_debate_message(self.topic)
    
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
        current_exchange = 1  # Track current exchange/round number
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
                        "content": response,
                        "exchange": current_exchange
                    })
                    
                    total_exchanges += 1
                    
                    # Generate brief summary for this response
                    self.summary_manager.update_brief_summary(current_speaker.name, response, current_exchange)
                    
                    # Update exchange number every few exchanges to group related discussions
                    if total_exchanges % 3 == 0:  # Group every 3 exchanges into one round
                        current_exchange += 1
                    
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
        
        # Update summaries before final evaluation
        self.summary_manager.update_summaries(self.conversation_history)
        
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
            
            # Show summary statistics
            stats = self.summary_manager.get_summary_stats()
            self.display.show_message("System", f"\n📊 Summary Statistics: {stats['exchanges_covered']} rounds covered, {stats['brief_summaries']} brief summaries, {stats['detailed_summaries']} detailed summaries", "white")
        
        # Judge's final evaluation if available
        if self.judge:
            try:
                # Count non-system messages for evaluation
                participant_messages = [
                    msg for msg in self.conversation_history
                    if msg.get("name") != "System"
                ]
                
                if participant_messages:
                    # Get detailed context from summary manager
                    detailed_context = self.get_summary_for_judge("detailed")
                    print(detailed_context)
                    evaluation_prompt = get_final_evaluation_prompt(
                        self.topic, len(participant_messages), detailed_context
                    )

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
        starter_prompt = get_starter_selection_prompt(self.topic)

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
                context_message = self._prepare_starter_context()
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
    
    def _prepare_starter_context(self) -> str:
        """Prepare a special starter context for the first speaker.
        
        Args:
            agent: The starting agent
            
        Returns:
            Starter context message
        """
        return get_starter_context_prompt(self.topic)
    
    def _prepare_context_for_agent(self, agent: LocalLLMAgent) -> str:
        """Prepare context message for an agent using concise summaries.
        
        Args:
            agent: The agent
            
        Returns:
            Context message with concise summary instead of full conversation
        """
        context_parts = [f"Topic: {self.topic}"]
        
        # Always use summary context instead of full conversation history
        if len(self.conversation_history) > 1:  # If there's any conversation to summarize
            try:
                current_exchange_round = max(
                    (msg.get("exchange", 1) for msg in self.conversation_history
                     if msg.get("name") != "System"),
                    default=1
                )
                
                # Get concise summary context
                summary_context = self.summary_manager.get_context_for_judge("quick", current_exchange_round, self.conversation_history)
                if summary_context and summary_context != "No context available.":
                    context_parts.append(f"\nConversation summary:\n{summary_context}")
                else:
                    # Generate a brief summary of key points if no summary available
                    context_parts.append(self._generate_brief_context_summary(agent))
                    
            except Exception as e:
                logger.error(f"Error preparing summary context for {agent.name}: {e}")
                # Fallback to brief summary
                context_parts.append(self._generate_brief_context_summary(agent))
        
        context_parts.append(get_agent_context_instructions())
        return "\n".join(context_parts)
    
    def _generate_brief_context_summary(self, agent: LocalLLMAgent) -> str:
        """Generate a brief summary of the conversation context.
        
        Args:
            agent: The current agent (to exclude their own messages)
            
        Returns:
            Brief context summary
        """
        # Get recent non-system messages from other participants
        other_messages = [
            msg for msg in self.conversation_history[-6:]
            if msg.get("name") != agent.name and msg.get("name") != "System"
        ]
        
        if not other_messages:
            return "\nNo previous discussion to summarize."
        
        # Create brief summary of key points
        summary_parts = ["\nKey points from discussion:"]
        for msg in other_messages[-3:]:  # Only last 3 messages from others
            # Truncate long messages to key points
            content = msg['content']
            if len(content) > 150:
                # Try to get the first sentence or key point
                sentences = content.split('. ')
                content = sentences[0] + '.' if sentences else content[:150] + "..."
            summary_parts.append(f"- {msg['name']}: {content}")
        
        return "\n".join(summary_parts)
    
    
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
        ]
        
        # Use summary manager to get appropriate context
        try:
            current_exchange_round = max(
                (msg.get("exchange", 1) for msg in self.conversation_history
                 if msg.get("name") != "System"),
                default=1
            )
            
            summary_context = self.summary_manager.get_context_for_judge("quick", current_exchange_round, self.conversation_history)
            if summary_context and summary_context != "No context available.":
                context_parts.append(f"\nDiscussion summary:\n{summary_context}")
            else:
                # Fallback to recent messages if no summary available
                recent_messages = self.conversation_history[-5:] if len(self.conversation_history) > 5 else self.conversation_history
                context_parts.append("\nRecent discussion:")
                for msg in recent_messages:
                    if msg["name"] != "System" and msg["name"] != self.moderator.name:
                        context_parts.append(f"- {msg['name']}: {msg['content'][:100]}...")
        except Exception as e:
            logger.error(f"Error getting summary context for moderator: {e}")
            # Fallback to recent messages
            recent_messages = self.conversation_history[-5:] if len(self.conversation_history) > 5 else self.conversation_history
            context_parts.append("\nRecent discussion:")
            for msg in recent_messages:
                if msg["name"] != "System" and msg["name"] != self.moderator.name:
                    context_parts.append(f"- {msg['name']}: {msg['content'][:100]}...")
        
        context_parts.append(f"\n{get_moderator_intervention_instructions()}")
        
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
                clarification_prompt = get_clarification_prompt(response, question)

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
        """Get a comprehensive summary of the debate.
        
        Returns:
            Debate summary dictionary with detailed summaries
        """
        # Update summaries to ensure they're current
        self.summary_manager.update_summaries(self.conversation_history)
        
        return {
            "topic": self.topic,
            "total_exchanges": len(self.conversation_history),
            "total_messages": len(self.conversation_history),
            "participants": [agent.name for agent in self.agents.values()],
            "moderator_used": self.moderator is not None,
            "conversation_history": self.conversation_history,
            "detailed_summary": self.summary_manager.get_detailed_summary(),
            "summary_stats": self.summary_manager.get_summary_stats()
        }
    
    def get_brief_summaries(self) -> Dict:
        """Get brief summaries for all exchanges.
        
        Returns:
            Dictionary of brief summaries by exchange and speaker
        """
        return self.summary_manager.brief_summaries
    
    def get_detailed_summaries(self) -> Dict:
        """Get detailed summaries for all exchanges.
        
        Returns:
            Dictionary of detailed summaries by exchange number
        """
        return self.summary_manager.detailed_summaries
    
    def get_summary_for_judge(self, decision_type: str = "detailed") -> str:
        """Get appropriate summary context for judge decisions.
        
        Args:
            decision_type: 'quick' for brief context, 'detailed' for comprehensive context
            
        Returns:
            Formatted summary context
        """
        if not self.conversation_history:
            return "No conversation history available."
        
        # Find the latest exchange number
        latest_exchange = max(
            (msg.get("exchange", 1) for msg in self.conversation_history
             if msg.get("name") != "System"),
            default=1
        )
        
        return self.summary_manager.get_context_for_judge(
            decision_type, latest_exchange, self.conversation_history
        )
    
    def generate_exchange_summary(self, exchange_num: int) -> str:
        """Generate a detailed summary for a specific exchange.
        
        Args:
            exchange_num: The exchange number to summarize
            
        Returns:
            Detailed summary of the specified exchange
        """
        return self.summary_manager.generate_detailed_summary(exchange_num, self.conversation_history)