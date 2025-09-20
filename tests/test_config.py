#!/usr/bin/env python3
"""
配置管理器测试
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from config_manager import ConfigManager

class TestConfigManager:
    """配置管理器测试类"""

    def test_config_manager_initialization(self):
        """测试配置管理器初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            config_manager = ConfigManager(str(config_path))

            assert config_manager is not None
            assert config_manager.config_path == config_path

    def test_get_config_value(self):
        """测试获取配置值"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            config_manager = ConfigManager(str(config_path))

            # 测试获取默认值
            value = config_manager.get('bot.name', 'default_name')
            assert value == 'default_name'

    def test_set_config_value(self):
        """测试设置配置值"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            config_manager = ConfigManager(str(config_path))

            # 设置配置值
            config_manager.set('bot.name', 'Test Bot')

            # 验证设置成功
            value = config_manager.get('bot.name')
            assert value == 'Test Bot'

    def test_get_trading_config(self):
        """测试获取交易配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            config_manager = ConfigManager(str(config_path))

            trading_config = config_manager.get_trading_config()

            assert 'max_position_size' in trading_config
            assert 'min_volume_24h' in trading_config
            assert 'min_fdv' in trading_config

    def test_get_copy_trading_config(self):
        """测试获取跟单配置"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            config_manager = ConfigManager(str(config_path))

            copy_config = config_manager.get_copy_trading_config()

            assert 'enabled' in copy_config
            assert 'leader_wallets' in copy_config
            assert 'copy_ratio' in copy_config

    def test_validate_config(self):
        """测试配置验证"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            config_manager = ConfigManager(str(config_path))

            errors, warnings = config_manager.validate_config()

            # 应该有错误，因为私钥未配置
            assert len(errors) > 0
            assert '钱包私钥' in errors[0] or 'PRIVATE_KEY' in errors[0]

if __name__ == "__main__":
    pytest.main([__file__])
