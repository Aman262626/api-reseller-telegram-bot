from flask import Flask, request, jsonify, send_from_directory
import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
import logging
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot_application = None

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
        'settings': {
            'master_api': '',
            'bot_token': '',
            'webhook_url': '',
            'api_price': 499,
            'default_commission': 20,
            'channel_id': '',
            'channel_username': '',
            'force_subscribe': True,
            'updates_channel': '',
            'notifications_enabled': True
        }
    }

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def generate_api_key():
    return f"pplx-{secrets.token_urlsafe(32)}"

def log_activity(user, action, status='success'):
    try:
        data = load_data()
        activity = {'time': datetime.now().isoformat(), 'user': user, 'action': action, 'status': status}
        data['activities'].insert(0, activity)
        data['activities'] = data['activities'][:100]
        save_data(data)
    except Exception as e:
        logger.error(f"Error logging: {e}")

async def send_channel_notification(message, channel_id=None):
    """Send notification to channel"""
    try:
        if bot_application is None:
            return False
        
        data = load_data()
        if not channel_id:
            channel_id = data['settings'].get('channel_id', '')
        
        if not channel_id:
            logger.warning("Channel ID not configured")
            return False
        
        await bot_application.bot.send_message(chat_id=channel_id, text=message, parse_mode='HTML')
        return True
    except Exception as e:
        logger.error(f"Channel notification error: {e}")
        return False

async def check_channel_subscription(user_id):
    """Check if user is subscribed to channel"""
    try:
        data = load_data()
        if not data['settings'].get('force_subscribe', False):
            return True
        
        channel_id = data['settings'].get('channel_id', '')
        if not channel_id:
            return True
        
        member = await bot_application.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Check subscription error: {e}")
        return True

def setup_bot():
    global bot_application
    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
        
        data = load_data()
        bot_token = os.environ.get('BOT_TOKEN', data['settings'].get('bot_token', ''))
        
        if not bot_token:
            logger.warning("Bot token not configured")
            return None
        
        bot_application = Application.builder().token(bot_token).build()
        
        async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user_id = update.effective_user.id
            username = update.effective_user.first_name or "User"
            
            data = load_data()
            
            # Check channel subscription
            if data['settings'].get('force_subscribe', False):
                is_subscribed = await check_channel_subscription(user_id)
                if not is_subscribed:
                    channel_username = data['settings'].get('channel_username', 'YourChannel')
                    keyboard = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel_username}")],
                               [InlineKeyboardButton("✅ Check Subscription", callback_data='check_subscription')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await update.message.reply_text(
                        f"""
⚠️ <b>Please Join Our Channel First!</b>

📢 To use this bot, you must join our official channel:
@{channel_username}

<b>After joining, click 'Check Subscription' below.</b>
""",
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                    return
            
            keyboard = [
                [InlineKeyboardButton("🔑 Get API Key", callback_data='get_api')],
                [InlineKeyboardButton("📊 Dashboard", callback_data='dashboard')],
                [InlineKeyboardButton("💼 Become Reseller", callback_data='become_reseller')],
                [InlineKeyboardButton("💰 Wallet", callback_data='wallet')],
                [InlineKeyboardButton("📢 Channel", url=f"https://t.me/{data['settings'].get('channel_username', 'YourChannel')}")],
                [InlineKeyboardButton("ℹ️ Help", callback_data='help')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            welcome_text = f"""
🚀 <b>Welcome {username}!</b>

✨ <b>Premium API Access:</b>
• Perplexity AI
• OpenAI GPT
• Claude AI

<b>🎯 Features:</b>
✅ Instant API generation
✅ Real-time monitoring
✅ Reseller program (20%)
✅ 24/7 service

<b>💰 Pricing:</b>
₹499/month | 1000 requests

<b>📢 Stay Updated:</b>
Join our channel for updates!

Choose an option:
"""
            
            await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='HTML')
            log_activity(username, 'Bot Started')
        
        async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            query = update.callback_query
            await query.answer()
            
            data = load_data()
            user_id = query.from_user.id
            username = query.from_user.first_name or "User"
            
            # Check subscription for protected actions
            if query.data in ['get_api', 'dashboard', 'become_reseller'] and data['settings'].get('force_subscribe', False):
                is_subscribed = await check_channel_subscription(user_id)
                if not is_subscribed:
                    channel_username = data['settings'].get('channel_username', 'YourChannel')
                    keyboard = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{channel_username}")],
                               [InlineKeyboardButton("✅ Check Subscription", callback_data='check_subscription')]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        f"⚠️ <b>Please join @{channel_username} first!</b>",
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                    return
            
            if query.data == 'check_subscription':
                is_subscribed = await check_channel_subscription(user_id)
                if is_subscribed:
                    await query.answer("✅ Verified! Use /start to continue.", show_alert=True)
                else:
                    await query.answer("❌ Not subscribed yet! Please join the channel.", show_alert=True)
                return
            
            if query.data == 'get_api':
                api_key = generate_api_key()
                expiry = (datetime.now() + timedelta(days=30)).isoformat()
                
                data['apis'][api_key] = {
                    'user_id': str(user_id),
                    'username': username,
                    'type': 'perplexity',
                    'requests': 0,
                    'limit': 1000,
                    'status': 'active',
                    'created': datetime.now().isoformat(),
                    'expiry': expiry
                }
                
                data['users'][str(user_id)] = {
                    'name': username,
                    'api_key': api_key,
                    'status': 'active',
                    'expiry': expiry,
                    'telegram_id': str(user_id)
                }
                
                save_data(data)
                log_activity(username, 'API Key Generated')
                
                # Send channel notification
                if data['settings'].get('notifications_enabled', True):
                    notification = f"""
🎉 <b>New API Key Generated!</b>

👤 User: {username}
🆔 ID: {user_id}
🔑 Type: Perplexity AI
📅 Date: {datetime.now().strftime('%d %b %Y')}

📊 Total Users: {len(data['users'])}
"""
                    asyncio.create_task(send_channel_notification(notification))
                
                await query.edit_message_text(
                    f"""
✅ <b>API Key Generated!</b>

🔑 <b>Your Key:</b>
<code>{api_key}</code>

📊 <b>Details:</b>
• Type: Perplexity AI
• Limit: 1,000 requests/mo
• Expiry: {datetime.fromisoformat(expiry).strftime('%d %b %Y')}
• Status: Active ✅

<b>🔐 Keep it secure!</b>

Use /start to return.
""",
                    parse_mode='HTML'
                )
            
            elif query.data == 'dashboard':
                if str(user_id) in data['users']:
                    user = data['users'][str(user_id)]
                    api = data['apis'].get(user['api_key'], {})
                    usage_percent = (api.get('requests', 0) / api.get('limit', 1)) * 100
                    progress = '█' * int(usage_percent / 10) + '░' * (10 - int(usage_percent / 10))
                    days_left = (datetime.fromisoformat(api.get('expiry', datetime.now().isoformat())) - datetime.now()).days
                    
                    await query.edit_message_text(
                        f"""
📊 <b>Your Dashboard</b>

👤 {user['name']}
🆔 <code>{user_id}</code>

🔑 <b>API:</b> <code>{user['api_key'][:20]}...</code>

📈 <b>Usage:</b>
{progress} {usage_percent:.1f}%
• Used: {api.get('requests', 0)}
• Limit: {api.get('limit', 0)}
• Remaining: {api.get('limit', 0) - api.get('requests', 0)}

⏰ <b>Expires:</b> {days_left} days
💰 <b>Plan:</b> Premium (₹499/mo)

Use /start to return.
""",
                        parse_mode='HTML'
                    )
                else:
                    await query.edit_message_text(
                        "⚠️ <b>No API key found!</b>\n\nGenerate one first.",
                        parse_mode='HTML'
                    )
            
            elif query.data == 'become_reseller':
                if str(user_id) not in data['resellers']:
                    reseller_id = f"RSL{secrets.token_hex(4).upper()}"
                    data['resellers'][str(user_id)] = {
                        'id': reseller_id,
                        'name': username,
                        'commission': data['settings']['default_commission'],
                        'sales': 0,
                        'earnings': 0,
                        'status': 'active',
                        'joined': datetime.now().isoformat(),
                        'referral_code': hashlib.md5(str(user_id).encode()).hexdigest()[:8].upper()
                    }
                    save_data(data)
                    log_activity(username, 'Became Reseller')
                    
                    # Send channel notification
                    if data['settings'].get('notifications_enabled', True):
                        notification = f"""
👥 <b>New Reseller Joined!</b>

👤 Name: {username}
🆔 ID: {reseller_id}
💰 Commission: {data['settings']['default_commission']}%
📅 Date: {datetime.now().strftime('%d %b %Y')}

📈 Total Resellers: {len(data['resellers'])}
"""
                        asyncio.create_task(send_channel_notification(notification))
                
                reseller = data['resellers'][str(user_id)]
                
                await query.edit_message_text(
                    f"""
🎉 <b>Welcome Reseller!</b>

🆔 <b>ID:</b> <code>{reseller['id']}</code>
💰 <b>Commission:</b> {reseller['commission']}%
💵 <b>Earnings:</b> ₹{reseller['earnings']}

🔗 <b>Referral Code:</b>
<code>{reseller['referral_code']}</code>

<b>Share your link!</b>
https://t.me/YourBot?start={reseller['referral_code']}

• Per sale: ₹{int(499 * reseller['commission'] / 100)}

Start earning! 💸
""",
                    parse_mode='HTML'
                )
            
            elif query.data == 'wallet':
                wallet_balance = 0
                if str(user_id) in data['resellers']:
                    wallet_balance = data['resellers'][str(user_id)].get('earnings', 0)
                
                await query.edit_message_text(
                    f"""
💰 <b>Your Wallet</b>

💵 <b>Balance:</b> ₹{wallet_balance}

📊 <b>Transactions:</b>
• Pending: ₹0
• Withdrawn: ₹0
• Total: ₹{wallet_balance}

🏦 <b>Withdrawal:</b>
Minimum: ₹500

Contact admin to withdraw.
""",
                    parse_mode='HTML'
                )
            
            elif query.data == 'help':
                channel_username = data['settings'].get('channel_username', 'YourChannel')
                await query.edit_message_text(
                    f"""
ℹ️ <b>Help & Support</b>

<b>📱 Commands:</b>
/start - Main menu
/dashboard - View stats

<b>🔧 Issues?</b>
• API not working? Check expiry
• Limit reached? Contact admin

<b>📢 Channel:</b>
@{channel_username}

<b>💬 Support:</b>
• Telegram: @YourSupport
• Email: support@example.com

Use /start to return.
""",
                    parse_mode='HTML'
                )
        
        bot_application.add_handler(CommandHandler('start', start))
        bot_application.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("Bot initialized successfully")
        return bot_application
        
    except Exception as e:
        logger.error(f"Bot setup error: {e}")
        return None

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
        
        if 'bot_token' in settings:
            global bot_application
            bot_application = setup_bot()
        
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

@app.route('/api/broadcast', methods=['POST'])
def broadcast_message():
    """Send broadcast message to all users"""
    try:
        payload = request.get_json()
        message = payload.get('message')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        data = load_data()
        users = data['users']
        
        sent_count = 0
        failed_count = 0
        
        for user_id in users.keys():
            try:
                asyncio.run(bot_application.bot.send_message(chat_id=int(user_id), text=message, parse_mode='HTML'))
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to {user_id}: {e}")
                failed_count += 1
        
        log_activity('Admin', f'Broadcast sent to {sent_count} users')
        
        return jsonify({
            'success': True,
            'sent': sent_count,
            'failed': failed_count,
            'total': len(users)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/channel_post', methods=['POST'])
def post_to_channel():
    """Post message to channel"""
    try:
        payload = request.get_json()
        message = payload.get('message')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        success = asyncio.run(send_channel_notification(message))
        
        if success:
            log_activity('Admin', 'Channel post sent')
            return jsonify({'success': True, 'message': 'Posted to channel'})
        else:
            return jsonify({'error': 'Failed to post'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<api_key>', methods=['DELETE'])
def delete_api(api_key):
    try:
        data = load_data()
        
        if api_key in data['apis']:
            api_info = data['apis'][api_key]
            user_id = api_info.get('user_id')
            
            del data['apis'][api_key]
            if user_id and user_id in data['users']:
                del data['users'][user_id]
            
            save_data(data)
            log_activity('Admin', f'API Deleted: {api_key[:20]}...')
            
            return jsonify({'success': True, 'message': 'API deleted'})
        else:
            return jsonify({'success': False, 'message': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/revoke/<api_key>', methods=['POST'])
def revoke_api(api_key):
    try:
        data = load_data()
        
        if api_key in data['apis']:
            data['apis'][api_key]['status'] = 'revoked'
            save_data(data)
            log_activity('Admin', f'API Revoked: {api_key[:20]}...')
            
            return jsonify({'success': True, 'message': 'API revoked'})
        else:
            return jsonify({'success': False, 'message': 'Not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        global bot_application
        if bot_application is None:
            bot_application = setup_bot()
        
        if bot_application is None:
            return jsonify({'error': 'Bot not initialized'}), 500
        
        from telegram import Update
        
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, bot_application.bot)
        
        asyncio.run(bot_application.process_update(update))
        
        return jsonify({'ok': True})
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/setup_webhook', methods=['GET', 'POST'])
def setup_webhook():
    try:
        global bot_application
        if bot_application is None:
            bot_application = setup_bot()
        
        if bot_application is None:
            return jsonify({'error': 'Bot not configured'}), 400
        
        data = load_data()
        webhook_url = os.environ.get('WEBHOOK_URL') or data['settings'].get('webhook_url')
        
        if not webhook_url:
            return jsonify({'error': 'Webhook URL not set'}), 400
        
        full_url = f"{webhook_url.rstrip('/')}/webhook"
        asyncio.run(bot_application.bot.set_webhook(url=full_url))
        
        logger.info(f"Webhook set: {full_url}")
        log_activity('System', 'Webhook Configured')
        
        return jsonify({
            'success': True,
            'webhook_url': full_url,
            'message': 'Webhook configured! Bot is active.'
        })
    except Exception as e:
        logger.error(f"Setup error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/bot_status', methods=['GET'])
def bot_status():
    try:
        global bot_application
        if bot_application is None:
            return jsonify({'initialized': False, 'message': 'Bot not initialized'})
        
        bot_info = asyncio.run(bot_application.bot.get_me())
        webhook_info = asyncio.run(bot_application.bot.get_webhook_info())
        
        return jsonify({
            'initialized': True,
            'bot_username': bot_info.username,
            'bot_name': bot_info.first_name,
            'webhook_url': webhook_info.url,
            'webhook_active': bool(webhook_info.url),
            'pending_updates': webhook_info.pending_update_count
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'bot_initialized': bot_application is not None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    bot_application = setup_bot()
    app.run(host='0.0.0.0', port=port, debug=False)