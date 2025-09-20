#!/usr/bin/env python3
"""
Example usage of the Solana Memecoin Trading Bot.
"""

import asyncio
import os
import logging
from memecoin_bot import MemecoinBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def basic_example():
    """Basic bot usage example."""
    logger.info("🚀 Starting Solana Memecoin Trading Bot...")
    
    try:
        async with MemecoinBot() as bot:
            logger.info("✅ Bot initialized successfully")
            logger.info(f"📊 Configuration: Max Position Size: {bot.config.max_position_size} SOL")
            logger.info(f"🎯 Min Confidence Score: {bot.config.min_confidence_score}%")
            logger.info(f"📈 Copy Trading: {'Enabled' if bot.config.copy_trading_enabled else 'Disabled'}")
            
            # Run the bot
            await bot.run_bot()
            
    except KeyboardInterrupt:
        logger.info("⏹️  Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")


async def monitoring_example():
    """Example of monitoring bot status."""
    logger.info("🔍 Bot Monitoring Example...")
    
    try:
        async with MemecoinBot() as bot:
            await bot.initialize()
            
            # Start monitoring tasks
            tasks = []
            
            if bot.dexscreener_client:
                tasks.append(asyncio.create_task(bot.dexscreener_client.start()))
                
            if bot.wallet_monitor:
                tasks.append(asyncio.create_task(bot.wallet_monitor.start_monitoring()))
            
            # Monitor for 5 minutes
            logger.info("📡 Monitoring for 5 minutes...")
            await asyncio.sleep(300)
            
            # Get status
            status = bot.get_status()
            logger.info(f"📊 Bot Status: {status}")
            
            # Stop monitoring
            for task in tasks:
                task.cancel()
                
    except Exception as e:
        logger.error(f"❌ Monitoring error: {e}")


async def analysis_only_example():
    """Example of running analysis only (no trading)."""
    logger.info("🔬 Analysis-Only Mode...")
    
    try:
        # Create bot with analysis-only config
        bot = MemecoinBot()
        await bot.initialize()
        
        # Disable trading by setting max position size to 0
        bot.config.max_position_size = 0.0
        
        logger.info("📊 Running token analysis without trading...")
        
        # Start discovery
        if bot.dexscreener_client:
            await bot.dexscreener_client.start()
            
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")


def check_requirements():
    """Check if all requirements are met."""
    logger.info("🔍 Checking requirements...")
    
    # Check environment file
    if not os.path.exists('.env'):
        logger.error("❌ .env file not found. Please copy env.example to .env and configure it.")
        return False
        
    # Check required environment variables
    required_vars = ['PRIVATE_KEY', 'SOLANA_RPC_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
            
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
        
    logger.info("✅ All requirements met")
    return True


async def main():
    """Main example function."""
    logger.info("🤖 Solana Memecoin Trading Bot Examples")
    logger.info("=" * 50)
    
    # Check requirements
    if not check_requirements():
        logger.error("❌ Please fix the requirements before running the bot.")
        return
        
    logger.info("Choose an example to run:")
    logger.info("1. Basic Bot (Full Trading)")
    logger.info("2. Monitoring Only")
    logger.info("3. Analysis Only (No Trading)")
    logger.info("4. Exit")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            await basic_example()
        elif choice == "2":
            await monitoring_example()
        elif choice == "3":
            await analysis_only_example()
        elif choice == "4":
            logger.info("👋 Goodbye!")
        else:
            logger.error("❌ Invalid choice. Please run the script again.")
            
    except KeyboardInterrupt:
        logger.info("👋 Goodbye!")
    except Exception as e:
        logger.error(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
