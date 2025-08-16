#!/bin/bash

# MailMind Setup Script
# This script sets up the MailMind project with all necessary dependencies

set -e

echo "🚀 Setting up MailMind..."
echo "=========================="

# Check if Python 3.9+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.9 or higher is required. Found: $python_version"
    exit 1
fi

echo "✅ Python version: $python_version"

# Navigate to backend directory
cd backend

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp env.example .env
    echo "📝 Please edit .env file with your API keys and settings"
else
    echo "✅ .env file already exists"
fi

# Initialize Alembic
echo "🗄️  Initializing database migrations..."
alembic init alembic 2>/dev/null || echo "Alembic already initialized"

# Create initial migration
echo "📝 Creating initial database migration..."
alembic revision --autogenerate -m "Initial migration"

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

echo ""
echo "🎉 Setup complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your API keys:"
echo "   - Gmail API credentials"
echo "   - OpenAI API key"
echo "   - MCP server details (if using)"
echo ""
echo "2. Start the application:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python start.py"
echo ""
echo "3. Access the API documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "4. Run tests:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   pytest tests/"
echo ""
echo "Happy email analyzing! 📧✨"
