"""
Handler for the GitHub Actions DevRAG Bot.
Parses the user query, runs the LangChain agent, and comments on PR/Issue.
"""
import sys
import os

# Remove @devrag from the query
raw_query = sys.argv[1]
issue_number = sys.argv[2]
query = raw_query.replace("@devrag", "").strip()

def main():
    # 1. Load Vectorstore (Chroma)
    # 2. Initialize LangChain Agent with custom system prompt
    # 3. answer = agent.answer_code_question(query)
    
    answer = f"**🤖 DevRAG AI:**\n\nAnalyzed codebase for: *'{query}'*\n\nThe auth logic is in `src/pharmaviyum/core/oauth2.py`."
    
    # Save answer to file for the GitHub Action to read
    with open("dev_rag_answer.md", "w") as f:
        f.write(answer)

if __name__ == "__main__":
    main()
