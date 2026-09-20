"""Custom HTML error pages for better user experience."""

from typing import Optional

from fastapi import Request
from fastapi.responses import HTMLResponse


def render_error_page(
    status_code: int, title: str, message: str, request: Optional[Request] = None
) -> HTMLResponse:
    """Render a branded HTML error page."""
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{status_code} - Pharmaviyum CRM</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; color: white; margin: 0; }}
            .container {{ text-align: center; padding: 40px; max-width: 600px; }}
            .status-code {{ font-size: 120px; font-weight: 700; margin-bottom: 10px; }}
            .title {{ font-size: 32px; margin-bottom: 20px; }}
            .message {{ font-size: 18px; margin-bottom: 30px; opacity: 0.9; }}
            .btn {{ display: inline-block; padding: 12px 32px; background: white; color: #667eea; text-decoration: none; border-radius: 8px; font-weight: 600; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status-code">{status_code}</div>
            <h1 class="title">{title}</h1>
            <p class="message">{message}</p>
            <a href="/" class="btn">Back to Home</a>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=status_code)


async def custom_404_handler(request: Request, exc):
    """Handle 404 Not Found errors."""
    return render_error_page(
        404,
        "Page Not Found",
        "The page you're looking for doesn't exist or has been moved.",
        request,
    )


async def custom_500_handler(request: Request, exc):
    """Handle 500 Internal Server Error."""
    return render_error_page(
        500,
        "Server Error",
        "Something went wrong on our end. Please try again later.",
        request,
    )
