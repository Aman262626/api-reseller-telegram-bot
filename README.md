# 🚀 API Reseller Telegram Bot

Complete Production-Ready API Reseller System with Super Admin Panel, Analytics Dashboard & Automated Distribution

## 🎯 Features

### 📊 Advanced Analytics & Monitoring
- Real-time usage graphs (Hourly/Daily/Monthly)
- Per-API endpoint statistics
- Error tracking (401/429/500)
- Live request counter with WebSocket

### 💰 Billing & Revenue Management
- Multiple subscription plans (Basic/Pro/Unlimited)
- Pay-as-you-go pricing
- Auto-renewal & expiry reminders
- GST-ready invoice generation
- Reseller wallet with auto-commission

### 🤖 Smart Telegram Bot
- `/start` - Main menu with inline buttons
- `/myusage` - Current usage statistics
- `/expiry` - Check expiry date
- `/apikey` - View masked API key
- `/renew` - Get payment link
- Auto alerts for 80% usage & expiry

### 🧑‍💼 Reseller Power Features
- Custom pricing per reseller
- White-label branding
- Referral codes system
- Sales & profit dashboard
- Commission tracking

### ⚙️ System Enhancements
- Multi-API fallback (Perplexity + OpenAI + Claude)
- Webhook events
- Complete audit logs
- Daily encrypted backups
- Test/Production mode

### 🎨 Premium UI/UX
- Dark/Light theme toggle
- Search & filter in tables
- Bulk actions (revoke, extend, delete)
- Toast notifications
- CSV export functionality

## 🚀 Deployment Guide

### 1. Clone Repository
```bash
git clone https://github.com/Aman262626/api-reseller-telegram-bot.git
cd api-reseller-telegram-bot
```

### 2. Telegram Bot Setup
1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow instructions to create bot
4. Save the bot token

### 3. Deploy on Render
1. Go to [Render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect this GitHub repository
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment Variables:**
     - `BOT_TOKEN` = Your Telegram bot token
     - `MASTER_API` = Your Perplexity API key
     - `PORT` = 10000

### 4. Configure Webhook
1. After deployment, copy your Render URL
2. Open the URL in browser (Admin Panel will open)
3. Go to Settings tab
4. Add Webhook URL and Bot Token
5. Save Settings

### 5. Test Bot
1. Search your bot on Telegram
2. Send `/start`
3. Click "Get API Key"
4. API key will be generated! 🎉

## 📁 File Structure
```
api-reseller-telegram-bot/
├── app.py              # Flask backend + Telegram bot
├── index.html          # Admin panel frontend
├── requirements.txt    # Python dependencies
├── Procfile           # Render configuration
├── data.json          # Data storage
└── README.md          # Documentation
```

## 🔧 Configuration

Edit `data.json` settings:
- `api_price`: Monthly API price (₹499)
- `default_commission`: Reseller commission (20%)
- `master_api`: Your main Perplexity API key
- `bot_token`: Telegram bot token

## 📊 Admin Panel Features
- Dashboard with real-time stats
- User management
- Reseller management
- API key generation & monitoring
- Analytics & reports
- System settings

## 🆘 Support
For issues or questions, create an issue on GitHub.

## 📄 License
MIT License - Free to use and modify

---
Built with ❤️ by Aman