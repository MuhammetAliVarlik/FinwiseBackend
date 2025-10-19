#!/bin/bash
# ============================================================
# Automated Branch Setup Script
# ------------------------------------------------------------
# Creates all standard branches for scalable backend projects
# ============================================================

set -e  # Stop on error

# Check remote
echo "🔍 Checking Git remote..."
if ! git remote | grep -q origin; then
    echo "Remote 'origin' not found."
    echo "Please add your GitHub repository first"
    exit 1
fi

# Sync with remote
echo "Fetching from origin..."
git fetch origin

# Create main branch
echo "Checking out main branch..."
git checkout main 2>/dev/null || git checkout -b main
git pull origin main || echo "No remote main branch found yet."

# Create develop branch
echo "Creating develop branch..."
git checkout -b develop 2>/dev/null || echo "Develop branch already exists."
git push -u origin develop

# Create feature branches
FEATURES=(
  "feature/init-backend"
  "feature/finance-api"
  "feature/response-api"
  "feature/docker-ci"
  "feature/docs"
)

for BRANCH in "${FEATURES[@]}"; do
  echo "Creating $BRANCH..."
  git checkout develop
  git checkout -b $BRANCH 2>/dev/null || echo "$BRANCH already exists."
  git push -u origin $BRANCH
done

# Create release and hotfix branches
echo "Creating release and hotfix branches..."
git checkout develop
git checkout -b release/v1.0.0 2>/dev/null || true
git push -u origin release/v1.0.0

git checkout main
git checkout -b hotfix/template 2>/dev/null || true
git push -u origin hotfix/template

# Summary
echo ""
echo "Branch setup completed successfully!"
echo ""
echo "Created branches:"
git branch -a
echo ""
echo "Workflow Summary:"
echo "  - main: production code"
echo "  - develop: integration branch"
echo "  - feature/*: feature development"
echo "  - release/*: pre-production staging"
echo "  - hotfix/*: emergency production fixes"
echo ""
echo "Backend Git workflow is ready!"
