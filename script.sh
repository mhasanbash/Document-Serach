#!/bin/bash

# ============================================
# Script: script.sh
# Description: Create .env file interactively and run server
# ============================================
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' 

ENV_FILE=".env"

# Default values 
declare -A DEFAULTS=(
    ["DJANGO_LOGLEVEL"]="info"
    ["DJANGO_ALLOWED_HOSTS"]="localhost"
    ["DEBUG"]="True"
    ["DJANGO_SETTINGS_MODULE"]="config.settings.development"
    ["DATABASE_NAME"]="docs"
    ["DATABASE_USERNAME"]="dbuser"
    ["DATABASE_PASSWORD"]="dbpassword"
    ["DATABASE_HOST"]="db"
    ["DATABASE_PORT"]="5432"
    ["DATABASE_ENGINE"]="postgresql"
    ["POSTGRES_DB"]="docs"
    ["POSTGRES_USER"]="dbuser"
    ["POSTGRES_PASSWORD"]="dbpassword"
    ["OPENAI_API_KEY"]="your-actual-api-key-here"
    ["SECRET_KEY"]="your-secret-key"
)

KEYS_ORDER_INPUT=(
    "DJANGO_ALLOWED_HOSTS"
    "DJANGO_SETTINGS_MODULE"
    "DEBUG"
    "SECRET_KEY"
    "OPENAI_API_KEY"
)

KEYS_ORDER=(
    "DJANGO_LOGLEVEL"
    "DATABASE_NAME"
    "DATABASE_USERNAME"
    "DATABASE_PASSWORD"
    "DATABASE_HOST"
    "DATABASE_PORT"
    "DATABASE_ENGINE"
    "POSTGRES_DB"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
)

# Welcome message
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   RAG Project   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo "for first step set your keys and env varibale."
echo "You can accept default values or enter your own."
echo -e "${YELLOW}Press Enter to use default value.${NC}"
echo ""

# Check if .env already exists
if [ -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Warning: $ENV_FILE already exists.${NC}"
    read -p "Overwrite? (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# Create or empty the .env file
> "$ENV_FILE"

# Loop through each key and ask for input
for key in "${KEYS_ORDER_INPUT[@]}"; do
    default="${DEFAULTS[$key]}"
    read -p "$key [$default]: " input
    value="${input:-$default}"
    # Write to .env
    echo "$key=$value" >> "$ENV_FILE"
done

echo "" >> "$ENV_FILE"  
for key in "${KEYS_ORDER[@]}"; do
    value="${DEFAULTS[$key]}"
    echo "$key=$value" >> "$ENV_FILE"
done

echo -e "your env variable set successfully!${NC}"

echo "starting Docker Compose..."
docker compose up --build 

if [ $? -eq 0 ]; then
    echo "srvice started succesfully"
else
    echo "error"
fi
