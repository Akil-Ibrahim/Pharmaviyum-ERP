"""Event handlers package.

Handlers are registered by their owning service modules. Keep this package
free of imports for optional/removed handlers so importing the package does
not fail during application startup or static analysis.
"""

__all__: list[str] = []
