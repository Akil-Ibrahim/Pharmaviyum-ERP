"""Custom HTML error pages for better user experience."""

from fastapi import Request
from fastapi.responses import HTMLResponse\nfrom typing import Any


def render_error_page(\n    status_code: int, title: str, message: str, request: Request | None = None\n) -> HTMLResponse:
    """Render a branded HTML error page."""
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>{status_code} - Pharmaviyum</title>
<style>
body {{ font-family: sans-serif; background: linear-gradient(135deg, #667eea, #764ba2);
       min-height: 100vh; display: flex; align-items: center; justify-content: center;
       color: white; margin: 0; }}
.container {{ text-align: center; padding: 40px; max-width: 600px; }}
.code {{ font-size: 120px; font-weight: 700; margin: 0; }}
.title {{ font-size: 32px; margin: 10px 0; }}
.msg {{ font-size: 18px; opacity: 0.9; margin-bottom: 30px; }}
.btn {{ display: inline-block; padding: 12px 32px; background: white; color: #667eea;
        text-decoration: none; border-radius: 8px; font-weight: 600; }}
</style></head><body>
<div class="container">
  <div class="code">{status_code}</div>
  <h1 class="title">{title}</h1>
  <p class="msg">{message}</p>
  <a href="/" class="btn">← Back to Home</a>
</div></body></html>"""
    return HTMLResponse(content=html, status_code=status_code)


async def custom_404_handler(request: Request, exc: Exception) -> HTMLResponse:
    return render_error_page(
        404, "Page Not Found", "The page you're looking for doesn't exist.", request
    )


async def custom_500_handler(request: Request, exc: Exception) -> HTMLResponse:
    return render_error_page(
        500, "Server Error", "Something went wrong. Please try again later.", request
    )
