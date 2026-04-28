#!/bin/bash
# Quick Deployment Script for NagrikMitra

echo "🚀 NagrikMitra Deployment Helper"
echo "================================="
echo ""

# Step 1: Git configuration
echo "📦 Step 1: Initialize Git Repository"
git config user.name "Your Name"
git config user.email "your.email@example.com"
git add .
git commit -m "Initial commit: NagrikMitra - AI Citizen Service Assistant" || true
echo "✅ Git initialized"
echo ""

# Step 2: Remote configuration
echo "🔗 Step 2: Add GitHub Remote"
echo "Enter your GitHub repository URL (e.g., https://github.com/yourusername/citizen-assistant.git):"
read REPO_URL
git remote add origin $REPO_URL || git remote set-url origin $REPO_URL
git branch -M main
git push -u origin main
echo "✅ Code pushed to GitHub"
echo ""

# Step 3: Deployment info
echo "📋 Deployment Checklist:"
echo "1. ✅ Code pushed to GitHub"
echo "2. ⏳ Frontend on Streamlit Cloud (see DEPLOYMENT.md)"
echo "3. ⏳ Backend on Railway (see DEPLOYMENT.md)"
echo ""
echo "🔑 Remember to set environment variables on Streamlit Cloud and Railway!"
echo ""
echo "📚 Full guide: cat DEPLOYMENT.md"
