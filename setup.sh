#!/bin/bash

# SAFT Doctor - Development Setup Script
# Este script automatiza o setup do ambiente de desenvolvimento

set -e

echo "🏥 SAFT Doctor - Development Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Windows (Git Bash/WSL)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    print_warning "Windows detected. Some commands may need adjustment."
fi

# Check dependencies
print_status "Checking dependencies..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
print_success "Python $PYTHON_VERSION found"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker Desktop."
    exit 1
fi

print_success "Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_warning "docker-compose not found. Trying docker compose..."
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

print_success "Docker Compose found"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    print_status "Creating .env file from template..."
    cat > .env << EOL
# Application
APP_ENV=dev
APP_PORT=8080
DEFAULT_COUNTRY=pt
SECRET_KEY=$(openssl rand -hex 32)
MASTER_KEY=$(openssl rand -base64 32)
LOG_LEVEL=INFO

# Database
MONGO_URI=mongodb://localhost:27017
MONGO_DB=saft_doctor
MONGO_SCOPING=collection_prefix
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=$(openssl rand -hex 16)

# Storage (Backblaze B2) - Configure these with your values
B2_ENDPOINT=https://s3.eu-central-003.backblazeb2.com
B2_REGION=eu-central-003
B2_BUCKET=your-bucket-name
B2_KEY_ID=your-key-id
B2_APP_KEY=your-app-key

# FACTEMI CLI
FACTEMICLI_JAR_PATH=/opt/factemi/FACTEMICLI.jar
SUBMIT_TIMEOUT_MS=600000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Redis (for future caching)
REDIS_URL=redis://localhost:6379/0
EOL
    print_success ".env file created with random secrets"
else
    print_warning ".env file already exists, skipping creation"
fi

# Create directories
print_status "Creating required directories..."
mkdir -p var logs saft-pt-doctor/factemi
print_success "Directories created"

# Setup Python virtual environment
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
print_status "Installing Python dependencies..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip
pip install -r services/requirements.txt

print_success "Python dependencies installed"

# Start services with Docker Compose
print_status "Starting services with Docker Compose..."
$COMPOSE_CMD -f docker-compose.dev.yml up -d mongo redis

print_success "Database services started"

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 10

# Test MongoDB connection
print_status "Testing MongoDB connection..."
if docker exec -it saft-doctor-mongo-1 mongosh --eval "db.adminCommand({ping: 1})" &> /dev/null; then
    print_success "MongoDB is ready"
else
    print_warning "MongoDB may not be fully ready yet"
fi

# Display instructions
echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "==========="
echo "1. Configure your Backblaze B2 credentials in .env"
echo "2. Place FACTEMICLI.jar in saft-pt-doctor/factemi/ directory"
echo "3. Start the development server:"
echo ""
echo "   # Activate virtual environment"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "   source venv/Scripts/activate"
else
    echo "   source venv/bin/activate"
fi
echo ""
echo "   # Start the API server"
echo "   cd services"
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8080"
echo ""
echo "4. Access the application:"
echo "   - API: http://localhost:8080"
echo "   - Docs: http://localhost:8080/docs"
echo "   - MongoDB Admin: http://localhost:8081 (if enabled)"
echo ""
echo "5. Run tests:"
echo "   pytest tests/ -v"
echo ""
echo "Happy coding! 🚀"