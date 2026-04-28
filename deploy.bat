@echo off
REM Quick Deployment Script for NagrikMitra (Windows)

echo.
echo 🚀 NagrikMitra Deployment Helper
echo =================================
echo.

REM Step 1: Git initialization
echo 📦 Step 1: Initialize Git Repository
git config user.name "Your Name"
git config user.email "your.email@example.com"
git add .
git commit -m "Initial commit: NagrikMitra - AI Citizen Service Assistant" 2>nul || echo (Already committed)
echo ✅ Git initialized
echo.

REM Step 2: Push to GitHub
echo 🔗 Step 2: Add GitHub Remote
set /p REPO_URL="Enter your GitHub repository URL (e.g., https://github.com/yourusername/citizen-assistant.git): "
git remote add origin %REPO_URL% 2>nul || git remote set-url origin %REPO_URL%
git branch -M main
git push -u origin main
echo ✅ Code pushed to GitHub
echo.

REM Step 3: Show checklist
echo 📋 Deployment Checklist:
echo 1. ✅ Code pushed to GitHub
echo 2. ⏳ Frontend on Streamlit Cloud (see DEPLOYMENT.md)
echo 3. ⏳ Backend on Railway (see DEPLOYMENT.md)
echo.
echo 🔑 Remember to set environment variables on Streamlit Cloud and Railway!
echo.
echo 📚 Full guide: type DEPLOYMENT.md
echo.
pause
