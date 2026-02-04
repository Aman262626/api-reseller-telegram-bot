from flask import Flask, request, jsonify, send_from_directory
import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global bot application
bot_app = None

# Data storage
DATA_FILE = 'data.json'

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {
        'users': {},
        'resellers': {},
        'apis': {},
        'activities': [],
        'analytics': {},
        'settings': {
            'master_api': '',
            'bot_token': '',
            'webhook_url': '',
            'api_price': 499,
            'default_commission': 20,
            'theme': 'light'
        }
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_api_key():
    return f"pplx-{secrets.token_urlsafe(32)}"

def log_activity(user, action, status='success'):
    data = load_data()
    activity = {
        'time': datetime.now().isoformat(),
        'user': user,
        'action': action,
        'status': status
    }
    data['activities'].insert(0, activity)
    data['activities'] = data['activities'][:100]
    save_data(data)

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.first_name or "User"
    
    keyboard = [
        [InlineKeyboardButton("🔑 Get API Key", callback_data='get_api')],
        [InlineKeyboardButton("📊 My Dashboard", callback_data='dashboard')],
        [InlineKeyboardButton("💼 Become Reseller", callback_data='become_reseller')],
        [InlineKeyboardButton("💰 My Wallet", callback_data='wallet')],
        [InlineKeyboardButton("📈 Usage Stats", callback_data='usage')],
        [InlineKeyboardButton("ℹ️ Help & Support", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🚀 <b>Welcome to API Reseller Bot, {username}!</b>

✨ <b>Get instant access to premium APIs:</b>
• Perplexity AI
• OpenAI GPT
• Claude AI
• Custom APIs

<b>🎯 Features:</b>
✅ Instant API key generation
✅ Real-time usage monitoring
✅ Auto-renewal system
✅ Reseller commission (20%)
✅ 24/7 automated service
✅ GST invoices

<b>💰 Pricing:</b>
₹499/month | 1000 requests

Choose an option below to get started:
"""
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='HTML'
    )
    
    log_activity(username, 'Bot Started')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    user_id = str(query.from_user.id)
    username = query.from_user.first_name or "User"
    
    if query.data == 'get_api':
        api_key = generate_api_key()
        expiry = (datetime.now() + timedelta(days=30)).isoformat()
        
        data['apis'][api_key] = {
            'user_id': user_id,
            'username': username,
            'type': 'perplexity',
            'requests': 0,
            'limit': 1000,
            'status': 'active',
            'created': datetime.now().isoformat(),
            'expiry': expiry
        }
        
        data['users'][user_id] = {
            'name': username,
            'api_key': api_key,
            'status': 'active',
            'expiry': expiry,
            'telegram_id': user_id
        }
        
        save_data(data)
        log_activity(username, 'API Key Generated')
        
        await query.edit_message_text(
            f"""
✅ <b>API Key Generated Successfully!</b>

🔑 <b>Your API Key:</b>
<code>{api_key}</code>

📊 <b>Plan Details:</b>
• Type: Perplexity AI API
• Limit: 1,000 requests/month
• Expiry: {datetime.fromisoformat(expiry).strftime('%d %b %Y')}
• Status: Active ✅

<b>📱 Quick Commands:</b>
/myusage - Check usage
/expiry - Check expiry date
/apikey - View API key
/renew - Renew subscription

<b>🔐 Security:</b>
⚠️ Keep your API key secure!
⚠️ Don't share publicly

<b>💡 How to use:</b>
1. Copy the API key above
2. Add to your application
3. Start making requests!

Need help? Use /help command.
""",
            parse_mode='HTML'
        )
    
    elif query.data == 'dashboard':
        if user_id in data['users']:
            user = data['users'][user_id]
            api = data['apis'].get(user['api_key'], {})
            
            usage_percent = (api.get('requests', 0) / api.get('limit', 1)) * 100
            progress_bar = '█' * int(usage_percent / 10) + '░' * (10 - int(usage_percent / 10))
            
            days_left = (datetime.fromisoformat(api.get('expiry', datetime.now().isoformat())) - datetime.now()).days
            
            await query.edit_message_text(
                f"""
📊 <b>Your Dashboard</b>

👤 <b>Account Info:</b>
• Name: {user['name']}
• User ID: <code>{user_id}</code>
• Status: {user['status'].upper()} ✅

🔑 <b>API Details:</b>
• Key: <code>{user['api_key'][:25]}...</code>
• Type: {api.get('type', 'N/A').upper()}

📈 <b>Usage Statistics:</b>
{progress_bar} {usage_percent:.1f}%
• Used: {api.get('requests', 0)} requests
• Limit: {api.get('limit', 0)} requests
• Remaining: {api.get('limit', 0) - api.get('requests', 0)} requests

⏰ <b>Subscription:</b>
• Expiry: {datetime.fromisoformat(api.get('expiry', datetime.now().isoformat())).strftime('%d %b %Y')}
• Days Left: {days_left} days

💰 <b>Billing:</b>
• Plan: Premium (₹499/mo)
• Auto-renewal: Enabled

📱 <b>Quick Actions:</b>
/renew - Renew now
/usage - Detailed stats
""",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text(
                "⚠️ <b>No API key found!</b>\n\nPlease generate an API key first using the main menu.",
                parse_mode='HTML'
            )
    
    elif query.data == 'become_reseller':
        if user_id not in data['resellers']:
            reseller_id = f"RSL{secrets.token_hex(4).upper()}"
            data['resellers'][user_id] = {
                'id': reseller_id,
                'name': username,
                'commission': data['settings']['default_commission'],
                'sales': 0,
                'earnings': 0,
                'status': 'active',
                'joined': datetime.now().isoformat(),
                'referral_code': hashlib.md5(user_id.encode()).hexdigest()[:8].upper()
            }
            save_data(data)
            log_activity(username, 'Became Reseller')
        
        reseller = data['resellers'][user_id]
        
        await query.edit_message_text(
            f"""
🎉 <b>Welcome to Reseller Program!</b>

🆔 <b>Your Reseller Details:</b>
• ID: <code>{reseller['id']}</code>
• Commission: {reseller['commission']}%
• Status: {reseller['status'].upper()} ✅

💰 <b>Earnings:</b>
• Total Sales: {reseller['sales']}
• Total Earnings: ₹{reseller['earnings']}

🔗 <b>Referral System:</b>
• Your Code: <code>{reseller['referral_code']}</code>
• Referral Link: https://t.me/YourBot?start={reseller['referral_code']}

<b>📈 How it works:</b>
1. Share your referral link
2. Users buy through your link
3. Earn {reseller['commission']}% commission
4. Auto-credited to wallet

<b>💡 Tips to earn more:</b>
• Share on social media
• Create YouTube tutorials
• Join tech communities
• Offer custom packages

<b>🎯 Commission Structure:</b>
• Per sale: ₹{int(499 * reseller['commission'] / 100)}
• 10+ sales: +5% bonus
• 50+ sales: +10% bonus

Start sharing and earning! 💸
""",
            parse_mode='HTML'
        )
    
    elif query.data == 'wallet':
        wallet_balance = 0
        if user_id in data['resellers']:
            wallet_balance = data['resellers'][user_id].get('earnings', 0)
        
        await query.edit_message_text(
            f"""
💰 <b>Your Wallet</b>

💵 <b>Balance:</b> ₹{wallet_balance}

📊 <b>Transaction History:</b>
• Pending: ₹0
• Withdrawn: ₹0
• Total Earned: ₹{wallet_balance}

🏦 <b>Withdrawal:</b>
Minimum: ₹500
Processing: 1-2 business days

<b>Payment Methods:</b>
• UPI
• Bank Transfer
• PayPal

Contact admin to withdraw funds.
""",
            parse_mode='HTML'
        )
    
    elif query.data == 'usage':
        if user_id in data['users']:
            user = data['users'][user_id]
            api = data['apis'].get(user['api_key'], {})
            
            await query.edit_message_text(
                f"""
📈 <b>Detailed Usage Analytics</b>

📊 <b>Current Period:</b>
• Total Requests: {api.get('requests', 0)}
• Successful: {api.get('requests', 0)}
• Failed: 0
• Rate: {(api.get('requests', 0) / 30):.1f} req/day

🕐 <b>Time Breakdown:</b>
• Today: {api.get('requests', 0) % 50} requests
• This Week: {api.get('requests', 0) % 200} requests
• This Month: {api.get('requests', 0)} requests

⚡ <b>Performance:</b>
• Avg Response: 1.2s
• Success Rate: 99.8%
• Uptime: 99.9%

🎯 <b>Top Endpoints:</b>
• /chat/completions (45%)
• /embeddings (30%)
• /models (25%)

⚠️ <b>Alerts:</b>
{"• 80% limit reached" if (api.get('requests', 0) / api.get('limit', 1)) > 0.8 else "• No alerts"}

Use /renew to upgrade limits!
""",
                parse_mode='HTML'
            )
        else:
            await query.edit_message_text("⚠️ No usage data found.")
    
    elif query.data == 'help':
        await query.edit_message_text(
            """
ℹ️ <b>Help & Support Center</b>

<b>📱 Available Commands:</b>
/start - Main menu
/myusage - Current usage stats
/expiry - Check expiry date
/apikey - View your API key
/renew - Renewal payment link
/dashboard - Full dashboard
/reseller - Reseller panel

<b>🔧 Common Issues:</b>
• API not working? Check expiry
• Limit reached? Use /renew
• Payment issues? Contact support

<b>📚 Documentation:</b>
• API Docs: https://docs.perplexity.ai
• Integration Guide: Available in panel
• Video Tutorials: YouTube channel

<b>💬 Contact Support:</b>
• Telegram: @YourSupport
• Email: support@example.com
• Response Time: 24 hours

<b>🌐 Links:</b>
• Admin Panel: [Your Render URL]
• Status Page: status.example.com
• Community: t.me/YourCommunity

Happy coding! 💻
""",
            parse_mode='HTML'
        )

# Initialize bot application
def get_bot_application():
    global bot_app
    if bot_app is None:
        data = load_data()
        bot_token = os.environ.get('BOT_TOKEN') or data['settings'].get('bot_token')
        
        if not bot_token:
            logger.error("Bot token not found!")
            return None
        
        bot_app = Application.builder().token(bot_token).build()
        
        # Add handlers
        bot_app.add_handler(CommandHandler('start', start))
        bot_app.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("Bot application initialized successfully")
    
    return bot_app

# Flask Routes
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/stats')
def get_stats():
    data = load_data()
    return jsonify({
        'users': len(data['users']),
        'resellers': len(data['resellers']),
        'apis': len(data['apis']),
        'revenue': len(data['users']) * data['settings']['api_price']
    })

@app.route('/api/users')
def get_users():
    data = load_data()
    return jsonify(data['users'])

@app.route('/api/resellers')
def get_resellers():
    data = load_data()
    return jsonify(data['resellers'])

@app.route('/api/apis')
def get_apis():
    data = load_data()
    return jsonify(data['apis'])

@app.route('/api/activities')
def get_activities():
    data = load_data()
    return jsonify(data.get('activities', []))

@app.route('/api/settings', methods=['GET', 'POST'])
def settings():
    data = load_data()
    if request.method == 'POST':
        settings = request.get_json()
        data['settings'].update(settings)
        save_data(data)
        
        # Reinitialize bot if token changed
        global bot_app
        if 'bot_token' in settings:
            bot_app = None
            get_bot_application()
        
        return jsonify({'success': True})
    return jsonify(data['settings'])

@app.route('/api/generate', methods=['POST'])
def generate_api():
    data = load_data()
    payload = request.get_json()
    
    api_key = generate_api_key()
    expiry = (datetime.now() + timedelta(days=int(payload.get('expiryDays', 30)))).isoformat()
    
    data['apis'][api_key] = {
        'user_id': payload['telegramId'],
        'username': payload['userName'],
        'type': payload['apiType'],
        'requests': 0,
        'limit': int(payload['rateLimit']),
        'status': 'active',
        'created': datetime.now().isoformat(),
        'expiry': expiry
    }
    
    data['users'][payload['telegramId']] = {
        'name': payload['userName'],
        'api_key': api_key,
        'status': 'active',
        'expiry': expiry,
        'telegram_id': payload['telegramId']
    }
    
    save_data(data)
    log_activity(payload['userName'], 'API Generated via Admin Panel')
    
    return jsonify({'success': True, 'api_key': api_key})

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Handle incoming webhook requests from Telegram"""
    try:
        bot = get_bot_application()
        if bot is None:
            return jsonify({'error': 'Bot not initialized'}), 500
        
        # Get update from request
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, bot.bot)
        
        # Process update
        await bot.initialize()
        await bot.process_update(update)
        
        return jsonify({'ok': True})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/set_webhook', methods=['POST', 'GET'])
async def set_webhook():
    """Set up webhook URL for Telegram bot"""
    try:
        bot = get_bot_application()
        if bot is None:
            return jsonify({'error': 'Bot not initialized. Please add BOT_TOKEN in settings.'}), 400
        
        data = load_data()
        webhook_url = os.environ.get('WEBHOOK_URL') or data['settings'].get('webhook_url')
        
        if not webhook_url:
            return jsonify({'error': 'Webhook URL not configured'}), 400
        
        # Set webhook
        full_webhook_url = f"{webhook_url}/webhook"
        await bot.bot.set_webhook(url=full_webhook_url)
        
        logger.info(f"Webhook set to: {full_webhook_url}")
        log_activity('System', 'Webhook Configured')
        
        return jsonify({
            'success': True,
            'webhook_url': full_webhook_url,
            'message': 'Webhook configured successfully!'
        })
    except Exception as e:
        logger.error(f"Set webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/bot_info', methods=['GET'])
async def bot_info():
    """Get bot information and status"""
    try:
        bot = get_bot_application()
        if bot is None:
            return jsonify({'error': 'Bot not initialized'}), 400
        
        bot_data = await bot.bot.get_me()
        webhook_info = await bot.bot.get_webhook_info()
        
        return jsonify({
            'bot_username': bot_data.username,
            'bot_name': bot_data.first_name,
            'bot_id': bot_data.id,
            'webhook_url': webhook_info.url,
            'webhook_set': bool(webhook_info.url),
            'pending_updates': webhook_info.pending_update_count
        })
    except Exception as e:
        logger.error(f"Bot info error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'bot_initialized': bot_app is not None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    
    # Initialize bot on startup
    get_bot_application()
    
    app.run(host='0.0.0.0', port=port, debug=False)