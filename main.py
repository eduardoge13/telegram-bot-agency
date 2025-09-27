#!/usr/bin/env python3
"""
Simple main.py for Cloud Run that runs the bot in the main thread
"""

import os
import logging
import signal
import sys
import threading
import time
from flask import Flask, jsonify

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    force=True
)

logger = logging.getLogger(__name__)
logger.info("🚀 Starting main.py...")

# Flask app for health checks
app = Flask(__name__)

# Global state
bot_instance = None
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info(f"📨 Received signal {signum}, initiating shutdown...")
    shutdown_requested = True
    
    if bot_instance and hasattr(bot_instance, 'application'):
        try:
            bot_instance.application.stop()
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    sys.exit(0)

def run_flask_server():
    """Run Flask server in background thread"""
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

@app.route('/')
def health_check():
    """Simple health check"""
    return "✅ Bot is running!" if bot_instance else "🔄 Bot is starting...", 200

@app.route('/health')
def detailed_health():
    """Detailed health status"""
    global bot_instance
    
    status = {
        "status": "running" if bot_instance else "starting",
        "bot_ready": bot_instance is not None,
        "timestamp": int(time.time())
    }
    
    if bot_instance:
        try:
            status["sheets_connected"] = bool(
                hasattr(bot_instance, 'sheets_manager') and 
                bot_instance.sheets_manager and 
                bot_instance.sheets_manager.service
            )
            
            if hasattr(bot_instance, 'sheet_info'):
                status["total_clients"] = bot_instance.sheet_info.get('total_clients', 0)
        except Exception as e:
            status["health_error"] = str(e)
    
    return jsonify(status), 200

def run_bot_with_restart():
    """Run bot with auto-restart in main thread"""
    global bot_instance, shutdown_requested
    
    try:
        from bot_telegram_polling import TelegramBot, setup_logging
        setup_logging()
        
        while not shutdown_requested:
            try:
                logger.info("🤖 Initializing bot...")
                bot_instance = TelegramBot()
                logger.info("✅ Bot instance ready")
                
                logger.info("🚀 Starting bot polling...")
                # This MUST run in main thread for asyncio
                bot_instance.run()
                
                if not shutdown_requested:
                    logger.warning("⚠️ Bot stopped unexpectedly, restarting in 10s...")
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"❌ Bot error: {e}")
                bot_instance = None
                if not shutdown_requested:
                    logger.info("🔄 Restarting bot in 30s...")
                    time.sleep(30)
                    
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        raise

def main():
    """Main entry point"""
    logger.info("🎬 Main function started")
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)  
    signal.signal(signal.SIGINT, signal_handler)
    
    # Start Flask server in background
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    # Give Flask time to start
    time.sleep(2)
    logger.info("✅ Flask health server started")
    
    # Run bot in main thread (CRITICAL for asyncio)
    try:
        run_bot_with_restart()
    except KeyboardInterrupt:
        logger.info("🛑 Application interrupted")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        raise

if __name__ == "__main__":
    main()