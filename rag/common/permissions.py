"""
Permissions module for RAG service.
Access is restricted to authorized pharmacists only.
"""

class RAGPermissionError(PermissionError):
    pass

def check_rag_access(user_role: str):
    """
    Validates if the user has access to the RAG system.
    The developer role has been removed to comply with the least privilege principle.
    """
    allowed_roles = ["pharmacist", "admin"]
    
    if user_role not in allowed_roles:
        raise RAGPermissionError(f"Access denied for role: {user_role}. Only pharmacists can access RAG.")
    
    return True
