#!/bin/bash

# FastAPI + Cognito + PostgreSQL Deployment Script
# Usage: ./deploy.sh [environment]
# Default environment: dev

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Default environment
ENVIRONMENT=${1:-dev}
STACK_NAME="fastapi-cognito-${ENVIRONMENT}"
PROJECT_NAME="fastapi-auth"

# Get AWS region from .env file
if [ -f .env ]; then
    AWS_REGION=$(grep "^AWS_REGION=" .env | cut -d '=' -f2 | tr -d '"')
fi
AWS_REGION=${AWS_REGION:-us-east-1}

log_info "🚀 Deploying FastAPI application to environment: $ENVIRONMENT"

# Check prerequisites
check_prerequisites() {
    log_info "🔍 Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not installed. Install with: curl 'https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip' -o 'awscliv2.zip' && unzip awscliv2.zip && sudo ./aws/install"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Run: aws configure"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not installed. Install with: curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose not installed. Install with: sudo curl -L 'https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)' -o /usr/local/bin/docker-compose && sudo chmod +x /usr/local/bin/docker-compose"
        exit 1
    fi
    
    log_success "All prerequisites met"
}

# Handle stuck Cognito stack with update strategy
handle_stack_update() {
    log_info "🔄 Checking CloudFormation stack status..."
    
    # Check if stack exists and its status
    STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || echo "NOT_EXISTS")
    
    if [[ "$STACK_STATUS" == "ROLLBACK_COMPLETE" || "$STACK_STATUS" == "ROLLBACK_FAILED" || "$STACK_STATUS" == "CREATE_FAILED" || "$STACK_STATUS" == "UPDATE_ROLLBACK_COMPLETE" ]]; then
        log_warning "Found stack with status: $STACK_STATUS - will update with new template"
        
        # Get UserPool ID if it exists and disable deletion protection
        USER_POOL_ID=$(aws cloudformation describe-stack-resources --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'StackResources[?LogicalResourceId==`UserPool`].PhysicalResourceId' --output text 2>/dev/null || echo "")
        
        if [ ! -z "$USER_POOL_ID" ] && [ "$USER_POOL_ID" != "None" ]; then
            log_info "🔓 Disabling UserPool deletion protection: $USER_POOL_ID"
            aws cognito-idp update-user-pool --user-pool-id "$USER_POOL_ID" --deletion-protection INACTIVE --region "$AWS_REGION" 2>/dev/null || true
        fi
        
        log_info "📋 Stack will be updated during Cognito deployment"
        
    elif [ "$STACK_STATUS" == "DELETE_FAILED" ]; then
        log_warning "Stack in DELETE_FAILED state - attempting cleanup"
        
        # Disable deletion protection if UserPool exists
        USER_POOL_ID=$(aws cloudformation describe-stack-resources --stack-name "$STACK_NAME" --region "$AWS_REGION" --query 'StackResources[?LogicalResourceId==`UserPool`].PhysicalResourceId' --output text 2>/dev/null || echo "")
        
        if [ ! -z "$USER_POOL_ID" ] && [ "$USER_POOL_ID" != "None" ]; then
            aws cognito-idp update-user-pool --user-pool-id "$USER_POOL_ID" --deletion-protection INACTIVE --region "$AWS_REGION" 2>/dev/null || true
        fi
        
        # Try to delete the stack
        aws cloudformation delete-stack --stack-name "$STACK_NAME" --region "$AWS_REGION"
        sleep 30
        
    elif [ "$STACK_STATUS" != "NOT_EXISTS" ]; then
        log_info "Stack exists with status: $STACK_STATUS"
    fi
}

# Deploy Cognito stack
deploy_cognito() {
    log_info "☁️ Deploying Cognito infrastructure..."
    
    python3 deploy-cognito.py \
        --stack-name "$STACK_NAME" \
        --environment "$ENVIRONMENT" \
        --project-name "$PROJECT_NAME" \
        --region "$AWS_REGION"
    
    if [ $? -ne 0 ]; then
        log_error "Cognito deployment failed"
        exit 1
    fi
    
    log_success "Cognito infrastructure deployed"
}

# Setup environment
setup_environment() {
    log_info "📝 Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        log_info "Created .env from template"
    fi
    
    # Generate secure secret key if not set
    if ! grep -q "SECRET_KEY=.*[a-zA-Z0-9]" .env; then
        SECRET_KEY=$(openssl rand -hex 32)
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
        log_info "Generated secure SECRET_KEY"
    fi
    
    # Set environment
    sed -i "s/ENVIRONMENT=.*/ENVIRONMENT=$ENVIRONMENT/" .env
    
    log_success "Environment configured"
}

# Start services with Docker commands
start_services() {
    log_info "🐳 Starting Docker services..."
    
    # Stop existing containers
    log_info "Stopping existing containers..."
    docker stop $(docker ps -q) 2>/dev/null || true
    docker container prune -f 2>/dev/null || true
    
    # Remove existing containers and networks
    docker-compose down --remove-orphans --volumes 2>/dev/null || true
    
    # Build and start services
    log_info "Building and starting services..."
    docker-compose build --no-cache
    docker-compose up -d
    
    log_info "⏳ Waiting for services to be ready..."
    sleep 20
    
    # Health check with better error handling
    log_info "Performing health check..."
    for i in {1..30}; do
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API is healthy!"
            
            # Show container status
            log_info "Container status:"
            docker-compose ps
            return 0
        fi
        
        if [ $i -eq 15 ]; then
            log_warning "Health check taking longer than expected, checking logs..."
            docker-compose logs --tail=10 api
        fi
        
        if [ $i -eq 30 ]; then
            log_error "Health check failed after 60 seconds"
            log_info "Container logs:"
            docker-compose logs api
            log_info "Container status:"
            docker-compose ps
            exit 1
        fi
        
        sleep 2
    done
}

# Main deployment
main() {
    check_prerequisites
    handle_stack_update
    deploy_cognito
    setup_environment
    start_services
    
    log_success "🎉 Deployment completed!"
    echo
    echo "📊 Service URLs:"
    echo "  • API Health: http://localhost:8000/health"
    echo "  • API Docs: http://localhost:8000/docs"
    echo "  • Interactive API: http://localhost:8000/redoc"
    echo
    echo "📋 Useful commands:"
    echo "  • View logs: docker-compose logs -f"
    echo "  • Stop services: docker-compose down"
    echo "  • View stack: aws cloudformation describe-stacks --stack-name $STACK_NAME"
}

main "$@"