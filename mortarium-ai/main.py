from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Mortarium AI",
    description="Pharmacy RAG System",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "mortarium-ai"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Mortarium AI is running", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
