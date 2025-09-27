import os
import time
import threading
import logging
import signal
import sys
from flask import Flask, jsonify

# Setup logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    force=True
)

logger = logging.getLogger(__name__)
logger.info("🚀 Starting bot_runner.py...")

# Initialize Flask app
app = Flask(__name__)

# Global variables
bot_thread = None
bot_instance = None
shutdown_requested = False
startup_error = None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_requested, bot_instance
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True
    
    if bot_instance and hasattr(bot_instance, 'application'):
        try:
            bot_instance.application.stop()
            logger.info("Bot application stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
    
    sys.exit(0)

def run_bot():
    """Run bot in separate thread"""
    global bot_instance, shutdown_requested, startup_error
    
    logger.info("🤖 Bot thread started, initializing...")
    
    try:
        # Try importing bot modules
        logger.info("📦 Importing bot modules...")
        from bot_telegram_polling import TelegramBot, setup_logging
        
        logger.info("📋 Setting up logging...")
        setup_logging()
        
        bot_logger = logging.getLogger("bot_telegram_polling")
        
        while not shutdown_requested:
            try:
                logger.info("🔄 Initializing Telegram Bot...")
                bot_instance = TelegramBot()
                logger.info("✅ Bot instance created successfully")
                
                logger.info("🚀 Starting bot.run()...")
                bot_instance.run()
                
                # If we reach here and not shutting down, restart
                if not shutdown_requested:
                    logger.warning("⚠️ Bot stopped unexpectedly. Restarting in 10s...")
                    time.sleep(10)
                    
            except Exception as e:
                logger.error(f"❌ Bot error: {e}", exc_info=True)
                startup_error = str(e)
                if not shutdown_requested:
                    logger.info("🔄 Restarting in 30s...")
                    time.sleep(30)
                    
    except ImportError as e:
        logger.error(f"❌ Import error: {e}", exc_info=True)
        startup_error = f"Import error: {e}"
    except Exception as e:
        logger.error(f"❌ Critical bot thread error: {e}", exc_info=True)
        startup_error = f"Critical error: {e}"

@app.route('/')
def health_check():
    """Health check for Cloud Run"""
    global bot_thread, startup_error
    
    logger.info("🏥 Health check called")
    
    # Start bot thread if needed
    if bot_thread is None or not bot_thread.is_alive():
        logger.info("🎯 Starting bot thread...")
        startup_error = None  # Reset error
        bot_thread = threading.Thread(target=run_bot, daemon=True, name="BotThread")
        bot_thread.start()
        logger.info("✅ Bot thread started")
    
    # Return status
    if startup_error:
        return f"Bot startup error: {startup_error}", 500
    elif bot_instance:
        return "✅ Bot is running!", 200
    else:
        return "🔄 Bot is starting...", 200

@app.route('/health')
def detailed_health():
    """Detailed health status"""
    global bot_thread, bot_instance, startup_error
    
    logger.info("📊 Detailed health check called")
    
    status = {
        "status": "running" if not startup_error else "error",
        "bot_thread_alive": bot_thread.is_alive() if bot_thread else False,
        "bot_instance_ready": bot_instance is not None,
        "startup_error": startup_error,
        "timestamp": int(time.time())
    }
    
    if bot_instance:
        try:
            status["sheets_connected"] = bool(
                hasattr(bot_instance, 'data_manager') and 
                bot_instance.data_manager and 
                bot_instance.data_manager.service
            )
            if hasattr(bot_instance, 'bot_username'):
                status["bot_username"] = bot_instance.bot_username
        except Exception as e:
            status["health_check_error"] = str(e)
    
    logger.info(f"📊 Status: {status}")
    return jsonify(status), 200 if status["status"] == "running" else 500

@app.route('/logs')
def show_logs():
    """Show recent logs for debugging"""
    # This is a simple endpoint to help debug
    return {
        "message": "Check Cloud Run logs for detailed information",
        "bot_thread_alive": bot_thread.is_alive() if bot_thread else False,
        "bot_ready": bot_instance is not None,
        "error": startup_error
    }

def main():
    """Main entry point"""
    logger.info("🎬 Main function started")
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Get port from environment
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Starting Flask app on port {port}")
    
    # Log environment info
    logger.info(f"🐍 Python version: {sys.version}")
    logger.info(f"📁 Working directory: {os.getcwd()}")
    logger.info(f"📋 Environment variables: GCP_PROJECT_ID={'✅' if os.getenv('GCP_PROJECT_ID') else '❌'}")
    
    try:
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("⚠️ Application interrupted by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()