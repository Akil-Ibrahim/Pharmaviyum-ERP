"""
Shared Kernel - Core infrastructure used by all modules.

This package contains:
- Database configuration and sessions
- Event bus for inter-module communication
- Shared middleware (auth, logging, rate limiting)
- Common utilities (pagination, responses, exceptions)

IMPORTANT: Modules should ONLY depend on shared/, never on other modules.
Inter-module communication happens via events, not direct imports.
"""
