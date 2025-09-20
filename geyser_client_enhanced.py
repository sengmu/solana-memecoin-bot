#!/usr/bin/env python3
"""
增强版 Geyser 客户端
参考 OpenSolBot 实现，优化实时数据获取
"""

import asyncio
import json
import logging
import aiohttp
import websockets
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import base64

logger = logging.getLogger(__name__)

class GeyserClientEnhanced:
    """增强版 Geyser 客户端用于实时数据订阅"""
    
    def __init__(self, endpoint: str, token: str, programs: List[str] = None):
        self.endpoint = endpoint
        self.token = token
        self.programs = programs or []
        self.session = None
        self.websocket = None
        self.subscriptions = {}
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
        if self.session:
            await self.session.close()
    
    async def connect_websocket(self) -> bool:
        """连接 WebSocket"""
        try:
            ws_url = self.endpoint.replace('https://', 'wss://').replace('http://', 'ws://')
            if not ws_url.endswith('/'):
                ws_url += '/'
            ws_url += 'rpc'
            
            self.websocket = await websockets.connect(
                ws_url,
                extra_headers={"Authorization": f"Bearer {self.token}"}
            )
            logger.info("WebSocket 连接成功")
            return True
        except Exception as e:
            logger.error(f"WebSocket 连接失败: {e}")
            return False
    
    async def subscribe_to_programs(self, callback: Callable) -> bool:
        """订阅程序事件"""
        try:
            if not self.websocket:
                if not await self.connect_websocket():
                    return False
            
            for program_id in self.programs:
                subscription_data = {
                    "jsonrpc": "2.0",
                    "id": len(self.subscriptions) + 1,
                    "method": "programSubscribe",
                    "params": [
                        program_id,
                        {
                            "encoding": "jsonParsed",
                            "commitment": "confirmed",
                            "filters": [
                                {
                                    "memcmp": {
                                        "offset": 0,
                                        "bytes": base64.b64encode(bytes.fromhex(program_id)).decode()
                                    }
                                }
                            ]
                        }
                    ]
                }
                
                await self.websocket.send(json.dumps(subscription_data))
                response = await self.websocket.recv()
                result = json.loads(response)
                
                if 'result' in result:
                    subscription_id = result['result']
                    self.subscriptions[subscription_id] = {
                        'program_id': program_id,
                        'callback': callback
                    }
                    logger.info(f"成功订阅程序: {program_id} (ID: {subscription_id})")
                else:
                    logger.error(f"订阅程序失败: {result}")
            
            return True
        except Exception as e:
            logger.error(f"订阅程序失败: {e}")
            return False
    
    async def start_listening(self, callback: Callable = None):
        """开始监听事件"""
        self.running = True
        logger.info("开始监听 Geyser 事件...")
        
        # 订阅程序
        if self.programs and callback:
            await self.subscribe_to_programs(callback)
        
        while self.running:
            try:
                if not self.websocket or self.websocket.closed:
                    if not await self.connect_websocket():
                        await asyncio.sleep(5)
                        continue
                
                # 接收消息
                message = await self.websocket.recv()
                data = json.loads(message)
                
                # 处理订阅数据
                if 'method' in data and data['method'] == 'programNotification':
                    await self._handle_program_notification(data)
                elif 'result' in data:
                    # 处理订阅确认
                    logger.debug(f"收到订阅确认: {data}")
                
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket 连接断开，尝试重连...")
                await self._reconnect()
            except Exception as e:
                logger.error(f"监听事件失败: {e}")
                await asyncio.sleep(5)
    
    async def _handle_program_notification(self, data: Dict[str, Any]):
        """处理程序通知"""
        try:
            params = data.get('params', {})
            result = params.get('result', {})
            
            # 提取交易信息
            transaction = result.get('transaction', {})
            meta = transaction.get('meta', {})
            account_keys = transaction.get('transaction', {}).get('message', {}).get('accountKeys', [])
            
            # 解析交易数据
            trade_data = {
                'signature': result.get('signature'),
                'slot': result.get('slot'),
                'timestamp': datetime.now().isoformat(),
                'program_id': result.get('subscription'),
                'accounts': account_keys,
                'logs': meta.get('logMessages', []),
                'fee': meta.get('fee', 0),
                'status': 'success' if meta.get('err') is None else 'failed'
            }
            
            # 调用回调函数
            subscription_id = data.get('subscription')
            if subscription_id in self.subscriptions:
                callback = self.subscriptions[subscription_id]['callback']
                await callback(trade_data)
            
        except Exception as e:
            logger.error(f"处理程序通知失败: {e}")
    
    async def _reconnect(self):
        """重连 WebSocket"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("达到最大重连次数，停止重连")
            self.running = False
            return
        
        self.reconnect_attempts += 1
        logger.info(f"尝试重连 ({self.reconnect_attempts}/{self.max_reconnect_attempts})...")
        
        await asyncio.sleep(min(2 ** self.reconnect_attempts, 30))  # 指数退避
        
        if await self.connect_websocket():
            self.reconnect_attempts = 0
            # 重新订阅
            for subscription_id, sub_data in self.subscriptions.items():
                await self.subscribe_to_programs(sub_data['callback'])
    
    async def get_account_info(self, account: str) -> Optional[Dict]:
        """获取账户信息"""
        try:
            data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    account,
                    {"encoding": "jsonParsed"}
                ]
            }
            
            async with self.session.post(
                f"{self.endpoint}/rpc",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('result')
                else:
                    logger.error(f"获取账户信息失败: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            return None
    
    async def get_program_accounts(self, program_id: str, filters: List[Dict] = None) -> List[Dict]:
        """获取程序账户"""
        try:
            data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getProgramAccounts",
                "params": [
                    program_id,
                    {
                        "encoding": "jsonParsed",
                        "filters": filters or []
                    }
                ]
            }
            
            async with self.session.post(
                f"{self.endpoint}/rpc",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('result', [])
                else:
                    logger.error(f"获取程序账户失败: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"获取程序账户失败: {e}")
            return []
    
    async def stop(self):
        """停止监听"""
        self.running = False
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        logger.info("Geyser 客户端已停止")
