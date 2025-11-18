# =================================
# ============ IMPORTS ============
# =================================
import streamlit as st
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from models import AgentState
from nodes import sql_node, semantic_search_node, omdb_node, web_node, synthesizer_node, planner_node
from utils import route_from_planner

# =================================
# ========== BUILD AGENT ==========
# =================================
@st.cache_resource
def build_agent():
    """Build workflow"""
    workflow = StateGraph(AgentState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("sql", sql_node)
    workflow.add_node("semantic", semantic_search_node)
    workflow.add_node("omdb", omdb_node)
    workflow.add_node("web", web_node)
    workflow.add_node("synthesize", synthesizer_node)
    
    # START → planner
    workflow.add_edge(START, "planner")
    
    # From planner: route to ALL needed tools OR direct to synthesize
    workflow.add_conditional_edges(
        "planner",
        route_from_planner,
        ["sql", "semantic", "omdb", "web", "synthesize"]
    )
    
    # All tools converge to synthesize
    workflow.add_edge("sql", "synthesize") #?? workflow.add_conditional_edges("sql", route_from_sql, ["semantic", "omdb", "web", "synthesize"])
    workflow.add_edge("semantic", "synthesize") #?? workflow.add_conditional_edges("semantic", route_from_semantic, ["omdb", "web", "synthesize"]) 
    workflow.add_edge("omdb", "synthesize") #?? workflow.add_conditional_edges("omdb", route_from_omdb, ["web", "synthesize"]) 
    workflow.add_edge("web", "synthesize")
    workflow.add_edge("synthesize", END)
    
    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

app = build_agent()
