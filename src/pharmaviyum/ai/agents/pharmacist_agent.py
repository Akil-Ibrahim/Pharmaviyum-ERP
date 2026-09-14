"""
Pharmacist Agent — LangGraph Orchestration.

Best practice 2026:
- Modular node design (Router → Planner → Executor → Reviewer)
- Fast model for routing, main model for reasoning
- Strict iteration limits to prevent infinite loops
"""
from __future__ import annotations
from typing import Any
from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from .state import AgentState
from src.pharmaviyum.core.logging import logger


class PharmacistAgent:
    """
    Multi-node LangGraph agent for pharmaceutical consultation.
    
    Graph flow:
    1. Router: Classifies query intent
    2. Planner: Decides which MCP tools to call
    3. Executor: Executes tools via MCP Client
    4. Reviewer: Validates safety, applies guardrails, formats output
    """
    
    def __init__(self, router_llm, main_llm, mcp_client, rag_pipeline):
        self.router_llm = router_llm  # Fast, cheap model (e.g., Qwen 1.5B)
        self.main_llm = main_llm      # Main reasoning model (e.g., Qwen 7B/72B)
        self.mcp_client = mcp_client
        self.rag_pipeline = rag_pipeline
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build and compile the LangGraph state machine."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("router", self.router_node)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("executor", self.executor_node)
        workflow.add_node("reviewer", self.reviewer_node)
        
        # Entry point
        workflow.set_entry_point("router")
        
        # Conditional routing after router
        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "drug_interaction": "planner",
                "prescription_check": "planner",
                "patient_consultation": "planner",
                "simple_query": "reviewer",  # Skip tool planning for simple facts
            }
        )
        
        # Linear flow with loop back for multi-step tool use
        workflow.add_edge("planner", "executor")
        
        workflow.add_conditional_edges(
            "executor",
            self._should_continue,
            {
                "continue": "planner",  # Need more tools
                "done": "reviewer",     # Have all info, validate
                "error": END,           # Fatal tool error
            }
        )
        
        workflow.add_edge("reviewer", END)
        
        return workflow.compile()
    
    async def router_node(self, state: AgentState) -> dict:
        """
        Node 1: Classify user query into specific categories.
        Uses a fast, lightweight model for low-latency routing.
        """
        last_msg = state["messages"][-1].content
        
        router_prompt = f"""
        Classify this pharmacy query into EXACTLY ONE category:
        - drug_interaction: Checking interactions between medications
        - prescription_check: Verifying prescription validity or limits
        - patient_consultation: General medical advice, dosage, allergies
        - simple_query: Factual question requiring no tools (e.g., "What is Paracetamol?")
        
        Query: {last_msg}
        Category:
        """
        
        response = await self.router_llm.ainvoke(router_prompt)
        category = response.content.strip().lower()
        
        # Fallback to patient_consultation if classification fails
        valid_categories = ["drug_interaction", "prescription_check", "patient_consultation", "simple_query"]
        intent = category if any(cat in category for cat in valid_categories) else "patient_consultation"
        
        logger.info(f"Router classified query as: {intent}")
        return {"query_intent": intent}
    
    def _route_decision(self, state: AgentState) -> str:
        """Conditional edge: where to go after router."""
        return state.get("query_intent", "patient_consultation")
    
    def _should_continue(self, state: AgentState) -> str:
        """Conditional edge: continue planning or finish."""
        if state.get("iteration", 0) > 5:
            logger.warning("Max iterations reached, forcing review")
            return "done"
        
        last_msg = state["messages"][-1]
        # Check if LLM requested tool calls
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "continue"
        
        return "done"

    async def planner_node(self, state: AgentState) -> dict:
        """
        Node 2: Decide which MCP tools to call based on query and context.
        Uses the main LLM with tool binding for structured tool selection.
        """
        # Increment iteration counter to prevent infinite loops
        current_iteration = state.get("iteration", 0) + 1
        
        # Get available tools from MCP client
        tools = self.mcp_client.to_openai_tools()
        
        # Bind tools to the main LLM
        llm_with_tools = self.main_llm.bind_tools(tools)
        
        # Construct system prompt with context
        context = state.get("context", {})
        country = context.get("country", "VN")
        language = context.get("language", "vi")
        halal_filter = context.get("halal_filter", False)
        
        system_prompt = f"""You are an expert pharmaceutical AI assistant for Southeast Asian and Middle Eastern pharmacies.

Rules:
1. Answer based ONLY on provided tools and retrieved knowledge.
2. If patient safety is at risk, prioritize safety warnings.
3. Country: {country} | Language: {language}
4. Halal Filter: {'ENABLED - Always check halal compliance and suggest alternatives' if halal_filter else 'Disabled'}
5. If you need information, use the available tools. Do not guess.
6. Return tool calls in the exact format requested.

Available Tools:
- check_drug_interactions: Check interactions between medications
- get_patient_history: Retrieve patient medical history (allergies, conditions)
- check_halal_compliance: Verify if a medication is halal-certified
- verify_prescription: Validate prescription against regulatory limits
"""
        
        # Combine system prompt with conversation history
        messages = [SystemMessage(content=system_prompt)] + state["messages"]
        
        try:
            # Invoke LLM with tool binding
            response = await llm_with_tools.ainvoke(messages)
            
            logger.info(
                f"Planner selected tools",
                extra={
                    "tools_called": [tc["name"] for tc in getattr(response, "tool_calls", [])],
                    "iteration": current_iteration,
                }
            )
            
            return {
                "messages": [response],
                "iteration": current_iteration,
            }
            
        except Exception as e:
            logger.error(f"Planner node failed: {e}", exc_info=True)
            # Return error as AI message to halt gracefully
            return {
                "messages": [AIMessage(content=f"Error in planning: {str(e)}")],
                "iteration": current_iteration,
            }

    async def executor_node(self, state: AgentState) -> dict:
        """
        Node 3: Execute the tool calls requested by the planner.
        Uses MCP Client with retry, timeout, and circuit breaker protection.
        """
        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", [])
        
        if not tool_calls:
            logger.warning("Executor called but no tool calls found in last message")
            return {"messages": [], "tool_results": []}
        
        tool_results = []
        new_messages = []
        
        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            logger.info(
                f"Executing tool: {tool_name}",
                extra={"tool": tool_name, "args": tool_args}
            )
            
            try:
                # Call MCP Client (handles retry, circuit breaker, validation)
                result = await self.mcp_client.call_tool(
                    tool_name=tool_name,
                    input_data=tool_args,
                    trace_id=state.get("context", {}).get("trace_id"),
                )
                
                if result.success:
                    content = str(result.data)
                    tool_results.append({
                        "tool": tool_name,
                        "success": True,
                        "data": result.data,
                    })
                else:
                    content = f"Error: {result.error}"
                    tool_results.append({
                        "tool": tool_name,
                        "success": False,
                        "error": result.error,
                    })
                    logger.warning(f"Tool {tool_name} failed: {result.error}")
                
            except Exception as e:
                content = f"Critical Error executing {tool_name}: {str(e)}"
                tool_results.append({
                    "tool": tool_name,
                    "success": False,
                    "error": str(e),
                })
                logger.error(f"Critical tool execution error: {e}", exc_info=True)
            
            # Append ToolMessage to conversation history
            new_messages.append(
                ToolMessage(content=content, tool_call_id=tool_id, name=tool_name)
            )
        
        return {
            "messages": new_messages,
            "tool_results": tool_results,
        }

    async def reviewer_node(self, state: AgentState) -> dict:
        """
        Node 4: Final validation and safety check before returning to user.
        
        Checks:
        1. Safety: No dangerous medical advice or hallucinated dosages
        2. Completeness: Did it actually answer the user's question?
        3. Formatting: Is the response clear and structured?
        """
        messages = state["messages"]
        context = state.get("context", {})
        warnings = state.get("warnings", []).copy()
        
        # Find the last AI message (the drafted response)
        ai_messages = [m for m in messages if isinstance(m, AIMessage) and not hasattr(m, "tool_calls")]
        if not ai_messages:
            # Fallback if no AI response was generated
            final_answer = "I apologize, but I couldn't generate a response. Please consult a licensed pharmacist."
            warnings.append("no_ai_response_generated")
            return {"final_answer": final_answer, "warnings": warnings}
        
        draft_response = ai_messages[-1].content
        
        # Safety validation prompt
        safety_prompt = f"""
        You are a medical safety reviewer for a pharmacy AI assistant.
        Review the following draft response for safety and accuracy.
        
        User Query: {messages[0].content if messages else "Unknown"}
        Draft Response: {draft_response}
        
        Check for:
        1. Hallucinated dosages or medications not mentioned in tools/sources.
        2. Dangerous advice (e.g., "stop taking immediately", "double the dose").
        3. Missing mandatory disclaimers for medical advice.
        
        Return a JSON object:
        {{
            "is_safe": boolean,
            "needs_revision": boolean,
            "revised_response": "string or null",
            "new_warnings": ["string"]
        }}
        """
        
        try:
            # Use a fast, reliable model for safety checking
            review_response = await self.main_llm.ainvoke([
                SystemMessage(content="You are a strict medical safety reviewer. Respond ONLY in valid JSON."),
                HumanMessage(content=safety_prompt)
            ])
            
            # Parse JSON response (basic parsing, in production use structured output)
            import json
            import re
            json_match = re.search(r'\{.*\}', review_response.content, re.DOTALL)
            if json_match:
                review_data = json.loads(json_match.group())
            else:
                review_data = {"is_safe": True, "needs_revision": False, "new_warnings": []}
            
            # Apply revisions and warnings
            final_answer = review_data.get("revised_response") or draft_response
            new_warnings = review_data.get("new_warnings", [])
            warnings.extend(new_warnings)
            
            if not review_data.get("is_safe", True):
                final_answer = "⚠️ SAFETY WARNING: I cannot provide this information as it may be unsafe. Please consult a licensed pharmacist or physician immediately."
                warnings.append("safety_block_triggered")
            
            # Append mandatory medical disclaimer if not present
            if "consult a licensed pharmacist" not in final_answer.lower() and "consult a physician" not in final_answer.lower():
                final_answer += "\n\n*Disclaimer: This is AI assistance. Always consult a licensed pharmacist or physician for personalized medical advice.*"
            
            logger.info(
                "Reviewer validation complete",
                extra={
                    "is_safe": review_data.get("is_safe", True),
                    "warnings_added": len(new_warnings),
                }
            )
            
        except Exception as e:
            logger.error(f"Reviewer node failed, using draft response: {e}", exc_info=True)
            final_answer = draft_response + "\n\n*Disclaimer: This is AI assistance. Always consult a licensed pharmacist.*"
            warnings.append("reviewer_error_fallback")
        
        return {
            "final_answer": final_answer,
            "warnings": warnings,
        }

    async def run(
        self,
        query: str,
        context: dict[str, Any] | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute the full agent graph for a single query.
        
        Args:
            query: User's question or request
            context: Additional context (patient_id, country, language, halal_filter)
            thread_id: Optional thread ID for memory/tracing
        
        Returns:
            Dictionary containing final_answer, warnings, and execution metadata
        """
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "context": context or {},
            "tool_calls": [],
            "tool_results": [],
            "final_answer": None,
            "warnings": [],
            "iteration": 0,
        }
        
        config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
        
        logger.info(
            "Starting Pharmacist Agent execution",
            extra={"query_preview": query[:50], "context": context}
        )
        
        try:
            # Execute the compiled graph
            final_state = await self.graph.ainvoke(initial_state, config=config)
            
            return {
                "success": True,
                "answer": final_state.get("final_answer", "No answer generated."),
                "warnings": final_state.get("warnings", []),
                "tool_calls_made": len(final_state.get("tool_results", [])),
                "iterations": final_state.get("iteration", 0),
            }
            
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            return {
                "success": False,
                "answer": "I encountered an error while processing your request. Please try again or consult a pharmacist.",
                "warnings": ["agent_execution_error"],
                "error": str(e),
            }

    async def astream(
        self,
        query: str,
        context: dict[str, Any] | None = None,
    ):
        """
        Stream the agent execution step-by-step.
        Useful for real-time UI updates (showing "Thinking...", "Checking interactions...", etc.)
        """
        initial_state: AgentState = {
            "messages": [HumanMessage(content=query)],
            "context": context or {},
            "tool_calls": [],
            "tool_results": [],
            "final_answer": None,
            "warnings": [],
            "iteration": 0,
        }
        
        async for event in self.graph.astream(initial_state, stream_mode="updates"):
            # Yield node name and its output for UI streaming
            for node_name, node_output in event.items():
                yield {
                    "node": node_name,
                    "data": node_output,
                }
