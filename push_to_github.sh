#!/bin/bash
# Push Bitcoin EMA Analyzer to GitHub
# Replace YOUR_USERNAME with your actual GitHub username

echo "Enter your GitHub username:"
read USERNAME

echo "Pushing to GitHub..."

# Add remote
git remote add origin https://github.com/$USERNAME/bitcoin-ema-analyzer.git

# Push to GitHub
git branch -M main
git push -u origin main

echo ""
echo "✅ Code pushed to GitHub!"
echo "Repository: https://github.com/$USERNAME/bitcoin-ema-analyzer"
echo ""
echo "Next step: Deploy to Streamlit Cloud"
echo "Go to: https://share.streamlit.io/"
