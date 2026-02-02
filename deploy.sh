#!/usr/bin/env bash
set -euo pipefail

ENV="${1:-dev}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ROOT}/devops/.env"
GENERATED_ENV_FILE="${ROOT}/devops/cognito.env"

[ -f "${ENV_FILE}" ] && set -o allexport && . "${ENV_FILE}" && set +o allexport

AWS_REGION="${AWS_REGION:-ap-south-1}"
AWS_PROFILE="${AWS_PROFILE:-}"
EMAIL_IDENTITY_ARN="${EMAIL_IDENTITY_ARN:-}"
CALLBACK_URLS="${CALLBACK_URLS:-http://localhost:8000/api/v1/auth/callback}"
LOGOUT_URLS="${LOGOUT_URLS:-http://localhost:3000/logout}"

# 🔥 Make domain unique if not provided
if [ -z "${DOMAIN_PREFIX:-}" ]; then
  DOMAIN_PREFIX="fastapi-auth-${ENV}-$(whoami | tr '[:upper:]' '[:lower:]')"
fi

if [ -z "${EMAIL_IDENTITY_ARN}" ]; then
  echo "❌ EMAIL_IDENTITY_ARN must be set"
  exit 2
fi

STACK_NAME="fastapi-auth-cognito-${ENV}"
TEMPLATE_FILE="devops/cognito/cognito.yaml"
AWS_CLI_IMAGE="amazon/aws-cli:latest"

echo "🚀 Deploying stack: ${STACK_NAME}"

DOCKER_OPTS=(
  --rm
  -v "${ROOT}":/workspace
  -w /workspace
  -e AWS_REGION="${AWS_REGION}"
)

[ -d "${HOME}/.aws" ] && DOCKER_OPTS+=(-v "${HOME}/.aws":/root/.aws:ro)

# ---------------------------------------------------------
# 🚫 DO NOT AUTO DELETE COGNITO STACKS
# ---------------------------------------------------------
STACK_STATUS="$(docker run "${DOCKER_OPTS[@]}" "${AWS_CLI_IMAGE}" \
  cloudformation describe-stacks \
  --stack-name "${STACK_NAME}" \
  --region "${AWS_REGION}" \
  --query "Stacks[0].StackStatus" \
  --output text 2>/dev/null || echo "NOT_FOUND")"

if [[ "${STACK_STATUS}" == "ROLLBACK_COMPLETE" ]]; then
  echo "❌ Stack in ROLLBACK_COMPLETE."
  echo "Delete manually ONLY if you are sure:"
  echo "aws cloudformation delete-stack --stack-name ${STACK_NAME}"
  exit 3
fi

PARAMS=(
  Environment="${ENV}"
  DomainPrefix="${DOMAIN_PREFIX}"
  CallbackURL="${CALLBACK_URLS}"
  LogoutURL="${LOGOUT_URLS}"
)

echo "📦 Deploying CloudFormation..."
docker run "${DOCKER_OPTS[@]}" "${AWS_CLI_IMAGE}" \
  cloudformation deploy \
    --template-file "${TEMPLATE_FILE}" \
    --stack-name "${STACK_NAME}" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "${AWS_REGION}" \
    --parameter-overrides "${PARAMS[@]}"

echo "✅ Deployment complete"

# ---------------------------------------------------------
# Fetch outputs
# ---------------------------------------------------------
fetch_output() {
  docker run "${DOCKER_OPTS[@]}" "${AWS_CLI_IMAGE}" \
    cloudformation describe-stacks \
    --stack-name "${STACK_NAME}" \
    --region "${AWS_REGION}" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" \
    --output text
}

USER_POOL_ID="$(fetch_output UserPoolId)"
APP_CLIENT_ID="$(fetch_output AppClientId)"
DOMAIN_URL="$(fetch_output DomainURL)"

cat > "${GENERATED_ENV_FILE}" <<EOF
COGNITO_USER_POOL_ID=${USER_POOL_ID}
COGNITO_CLIENT_ID=${APP_CLIENT_ID}
COGNITO_DOMAIN=${DOMAIN_URL}
COGNITO_REGION=${AWS_REGION}
EOF

echo "📝 Generated: devops/cognito.env"
