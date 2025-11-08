#!/bin/bash
# Helper script to set up Git authentication for GitHub

echo "🔐 GitHub Authentication Setup"
echo "=============================="
echo ""

# Check if SSH key exists
if [ -f ~/.ssh/id_ed25519.pub ] || [ -f ~/.ssh/id_rsa.pub ]; then
    echo "✅ SSH key found!"
    echo ""
    echo "📋 Your public key:"
    if [ -f ~/.ssh/id_ed25519.pub ]; then
        cat ~/.ssh/id_ed25519.pub
    else
        cat ~/.ssh/id_rsa.pub
    fi
    echo ""
    echo "📝 Next steps:"
    echo "1. Copy the key above"
    echo "2. Go to: https://github.com/settings/keys"
    echo "3. Click 'New SSH key'"
    echo "4. Paste the key and save"
    echo "5. Run: git remote set-url origin git@github.com:KAXUN01/Heal-X-Bot.git"
    echo "6. Run: git push origin main"
else
    echo "❌ No SSH key found"
    echo ""
    echo "🔑 Option 1: Create SSH Key (Recommended)"
    echo "Run: ssh-keygen -t ed25519 -C 'kasunmadhushanw@gmail.com'"
    echo "Then run this script again"
    echo ""
    echo "🔑 Option 2: Use Personal Access Token (Easier)"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select scope: repo"
    echo "4. Copy the token"
    echo "5. Run: git push origin main"
    echo "6. Username: KAXUN01"
    echo "7. Password: (paste your token)"
fi

echo ""
echo "📚 For detailed instructions, see: GITHUB_PUSH_GUIDE.md"

