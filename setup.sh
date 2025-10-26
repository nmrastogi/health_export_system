#!/bin/bash
# Health Data Export System Setup Script

echo "🏥 Health Data Export System Setup"
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv health_export_env
source health_export_env/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file from template..."
    cp config_template.txt .env
    echo "📝 Please edit .env file with your credentials:"
    echo "   - Amazon RDS database settings"
    echo "   - Health app API endpoints"
    echo "   - API keys"
fi

# Create logs directory
mkdir -p logs

# Test database connection
echo "🧪 Testing database connection..."
python test_connection.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Set up iPhone Shortcuts for health data export"
echo "3. Run: python shortcuts_integration.py for Shortcuts setup guide"
echo "4. Test: python test_connection.py"
echo "5. Start: python main.py"
echo ""
echo "📱 iPhone Setup:"
echo "1. Open Shortcuts app"
echo "2. Create sleep data export shortcut"
echo "3. Create exercise data export shortcut"
echo "4. Set up automations (6h sleep, 15min exercise)"
echo ""
echo "📊 Analytics:"
echo "Run: python health_analytics.py for data analysis"
