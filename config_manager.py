#!/usr/bin/env python3
"""
配置管理器
参考 OpenSolBot 的配置管理方式
"""

import os
import toml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: str = "config.toml"):
        self.config_path = Path(config_path)
        self.config = {}
        self.load_config()
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = toml.load(f)
                logger.info(f"配置文件加载成功: {self.config_path}")
            else:
                logger.warning(f"配置文件不存在: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """创建默认配置"""
        self.config = {
            'bot': {
                'name': 'Solana Memecoin Bot',
                'version': '2.0.0',
                'debug': False,
                'log_level': 'INFO'
            },
            'wallet': {
                'private_key': 'your_wallet_private_key_here',
                'wallet_address': ''
            },
            'rpc': {
                'endpoints': ['https://api.mainnet-beta.solana.com'],
                'websocket_endpoints': ['wss://api.mainnet-beta.solana.com'],
                'timeout': 30,
                'retry_count': 3
            },
            'api': {
                'helius_api_base_url': 'https://api.helius.xyz/v0',
                'helius_api_key': 'your_helius_api_key_here',
                'shyft_api_base_url': 'https://api.shyft.to',
                'shyft_api_key': 'your_shyft_api_key_here'
            },
            'trading': {
                'max_position_size': 0.1,
                'min_volume_24h': 1000000,
                'min_fdv': 100000,
                'max_slippage': 0.05,
                'default_slippage': 0.01
            },
            'copy_trading': {
                'enabled': True,
                'leader_wallets': [],
                'copy_ratio': 1.0,
                'min_confidence_score': 70
            },
            'telegram': {
                'enabled': False,
                'bot_token': 'your_telegram_bot_token_here',
                'chat_id': 'your_telegram_chat_id_here'
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                toml.dump(self.config, f)
            logger.info(f"配置已保存: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"配置保存失败: {e}")
            return False
    
    def get_wallet_config(self) -> Dict[str, Any]:
        """获取钱包配置"""
        return {
            'private_key': self.get('wallet.private_key'),
            'wallet_address': self.get('wallet.wallet_address')
        }
    
    def get_rpc_config(self) -> Dict[str, Any]:
        """获取 RPC 配置"""
        return {
            'endpoints': self.get('rpc.endpoints', []),
            'websocket_endpoints': self.get('rpc.websocket_endpoints', []),
            'timeout': self.get('rpc.timeout', 30),
            'retry_count': self.get('rpc.retry_count', 3)
        }
    
    def get_trading_config(self) -> Dict[str, Any]:
        """获取交易配置"""
        return {
            'max_position_size': self.get('trading.max_position_size', 0.1),
            'min_volume_24h': self.get('trading.min_volume_24h', 1000000),
            'min_fdv': self.get('trading.min_fdv', 100000),
            'max_slippage': self.get('trading.max_slippage', 0.05),
            'default_slippage': self.get('trading.default_slippage', 0.01),
            'max_daily_loss': self.get('trading.max_daily_loss', 0.1),
            'stop_loss_percentage': self.get('trading.stop_loss_percentage', 0.2),
            'take_profit_percentage': self.get('trading.take_profit_percentage', 0.5)
        }
    
    def get_copy_trading_config(self) -> Dict[str, Any]:
        """获取跟单交易配置"""
        return {
            'enabled': self.get('copy_trading.enabled', False),
            'leader_wallets': self.get('copy_trading.leader_wallets', []),
            'copy_ratio': self.get('copy_trading.copy_ratio', 1.0),
            'min_confidence_score': self.get('copy_trading.min_confidence_score', 70),
            'max_copy_amount': self.get('copy_trading.max_copy_amount', 1.0)
        }
    
    def get_telegram_config(self) -> Dict[str, Any]:
        """获取 Telegram 配置"""
        return {
            'enabled': self.get('telegram.enabled', False),
            'bot_token': self.get('telegram.bot_token'),
            'chat_id': self.get('telegram.chat_id'),
            'admin_chat_id': self.get('telegram.admin_chat_id')
        }
    
    def get_geyser_config(self) -> Dict[str, Any]:
        """获取 Geyser 配置"""
        return {
            'enabled': self.get('geyser.enabled', False),
            'endpoint': self.get('geyser.endpoint'),
            'token': self.get('geyser.token'),
            'programs': self.get('geyser.programs', [])
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取 API 配置"""
        return {
            'helius_api_base_url': self.get('api.helius_api_base_url'),
            'helius_api_key': self.get('api.helius_api_key'),
            'shyft_api_base_url': self.get('api.shyft_api_base_url'),
            'shyft_api_key': self.get('api.shyft_api_key'),
            'jupiter_api_key': self.get('api.jupiter_api_key'),
            'raydium_api_key': self.get('api.raydium_api_key')
        }
    
    def validate_config(self) -> tuple[List[str], List[str]]:
        """验证配置"""
        errors = []
        warnings = []
        
        # 检查必需配置
        required_configs = [
            ('wallet.private_key', '钱包私钥'),
            ('rpc.endpoints', 'RPC 节点'),
        ]
        
        for key, name in required_configs:
            if not self.get(key) or self.get(key) == f'your_{key.split(".")[-1]}_here':
                errors.append(f"{name}未配置")
        
        # 检查跟单配置
        if self.get('copy_trading.enabled'):
            if not self.get('copy_trading.leader_wallets'):
                warnings.append("跟单功能已启用但未配置跟单钱包")
        
        # 检查 Telegram 配置
        if self.get('telegram.enabled'):
            if not self.get('telegram.bot_token') or not self.get('telegram.chat_id'):
                warnings.append("Telegram 功能已启用但配置不完整")
        
        return errors, warnings
    
    def update_from_env(self) -> None:
        """从环境变量更新配置"""
        env_mapping = {
            'PRIVATE_KEY': 'wallet.private_key',
            'SOLANA_RPC_URL': 'rpc.endpoints',
            'SOLANA_WS_URL': 'rpc.websocket_endpoints',
            'HELIUS_API_KEY': 'api.helius_api_key',
            'SHYFT_API_KEY': 'api.shyft_api_key',
            'JUPITER_API_KEY': 'api.jupiter_api_key',
            'RAYDIUM_API_KEY': 'api.raydium_api_key',
            'TELEGRAM_BOT_TOKEN': 'telegram.bot_token',
            'TELEGRAM_CHAT_ID': 'telegram.chat_id',
            'COPY_TRADING_ENABLED': 'copy_trading.enabled',
            'LEADER_WALLET_ADDRESS': 'copy_trading.leader_wallets',
            'COPY_RATIO': 'copy_trading.copy_ratio',
            'MIN_CONFIDENCE_SCORE': 'copy_trading.min_confidence_score',
            'MAX_POSITION_SIZE': 'trading.max_position_size',
            'MIN_VOLUME_24H': 'trading.min_volume_24h',
            'MIN_FDV': 'trading.min_fdv',
            'MAX_SLIPPAGE': 'trading.max_slippage',
            'DEFAULT_SLIPPAGE': 'trading.default_slippage'
        }
        
        for env_key, config_key in env_mapping.items():
            env_value = os.getenv(env_key)
            if env_value:
                # 处理特殊类型
                if env_key in ['COPY_TRADING_ENABLED']:
                    self.set(config_key, env_value.lower() == 'true')
                elif env_key in ['COPY_RATIO', 'MAX_POSITION_SIZE', 'MAX_SLIPPAGE', 'DEFAULT_SLIPPAGE']:
                    try:
                        self.set(config_key, float(env_value))
                    except ValueError:
                        pass
                elif env_key in ['MIN_VOLUME_24H', 'MIN_FDV', 'MIN_CONFIDENCE_SCORE']:
                    try:
                        self.set(config_key, int(float(env_value)))
                    except ValueError:
                        pass
                elif env_key == 'LEADER_WALLET_ADDRESS':
                    # 处理多个钱包地址
                    wallets = [w.strip() for w in env_value.split(',') if w.strip()]
                    self.set(config_key, wallets)
                else:
                    self.set(config_key, env_value)

# 全局配置管理器实例
config_manager = ConfigManager()
