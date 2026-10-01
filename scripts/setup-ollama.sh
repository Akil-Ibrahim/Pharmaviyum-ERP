#!/bin/bash
# ============================================================================
# Pull required Ollama models
# ============================================================================

echo "🤖 Pulling Ollama models..."
echo ""

MODELS=(
    "qwen3.5:9b"
    "mxbai-embed-large"
)

for model in "${MODELS[@]}"; do
    echo " Pulling $model..."
    docker-compose exec ollama ollama pull "$model"
    echo ""
done

echo "✅ All models pulled successfully!"
echo ""
echo "📊 Available models:"
docker-compose exec ollama ollama list
