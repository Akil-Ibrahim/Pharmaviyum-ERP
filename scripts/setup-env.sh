#!/bin/bash
# ============================================
# Setup Environment Configuration
# ============================================

set -e

ENV=${1:-development}

echo "🚀 Setting up $ENV environment..."

case $ENV in
    dev|development)
        if [ -f .env.development ]; then
            cp .env.development .env
            echo "✅ Development environment configured"
            echo "📝 Using .env.development"
        else
            echo "❌ .env.development not found"
            exit 1
        fi
        ;;
    
    prod|production)
        if [ -f .env.production ]; then
            # Check if secrets are generated
            if grep -q "CHANGE_ME" .env.production; then
                echo "⚠️  Production secrets not generated yet"
                echo "🔐 Run: bash scripts/generate-secrets.sh"
                exit 1
            fi
            
            cp .env.production .env
            echo "✅ Production environment configured"
            echo "📝 Using .env.production"
        else
            echo "❌ .env.production not found"
            exit 1
        fi
        ;;
    
    *)
        echo "❌ Unknown environment: $ENV"
        echo "Usage: $0 [dev|prod]"
        exit 1
        ;;
esac

# Verify .env is in .gitignore
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
    echo "✅ Added .env to .gitignore"
fi

echo ""
echo "🎉 Environment setup complete!"
echo "📋 Next steps:"
echo "   1. Review .env file: cat .env"
echo "   2. Start services: docker-compose up -d"
echo "   3. Check logs: docker-compose logs -f"
