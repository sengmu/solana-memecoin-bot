"""
RugCheck integration using Selenium for token safety analysis.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from models import TokenInfo, RugCheckResult, BotConfig


class RugCheckAnalyzer:
    """Analyzes token safety using RugCheck website."""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.driver: Optional[webdriver.Chrome] = None
        
    async def analyze_token(self, token: TokenInfo) -> Optional[RugCheckResult]:
        """Analyze token safety using RugCheck."""
        try:
            await self._setup_driver()
            
            # Navigate to RugCheck
            rugcheck_url = f"https://rugcheck.xyz/tokens/{token.address}"
            self.logger.info(f"Analyzing {token.symbol} on RugCheck: {rugcheck_url}")
            
            self.driver.get(rugcheck_url)
            
            # Wait for page to load
            await asyncio.sleep(3)
            
            # Extract safety information
            result = await self._extract_safety_data(token.address)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing token {token.symbol} on RugCheck: {e}")
            return None
        finally:
            await self._cleanup_driver()
            
    async def _setup_driver(self):
        """Setup Chrome driver with appropriate options."""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Disable images and CSS for faster loading
            prefs = {
                "profile.managed_default_content_settings.images": 2,
                "profile.default_content_setting_values.stylesheets": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
        except Exception as e:
            self.logger.error(f"Error setting up Chrome driver: {e}")
            raise
            
    async def _cleanup_driver(self):
        """Clean up the Chrome driver."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.error(f"Error cleaning up driver: {e}")
            finally:
                self.driver = None
                
    async def _extract_safety_data(self, token_address: str) -> RugCheckResult:
        """Extract safety data from RugCheck page."""
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Initialize result with defaults
            result = RugCheckResult(
                token_address=token_address,
                rating="Unknown",
                liquidity_locked=False,
                ownership_renounced=False,
                whale_percentage=0.0,
                holder_distribution={},
                contract_verified=False,
                honeypot=False,
                mint_authority=True,
                freeze_authority=True,
                overall_score=0.0
            )
            
            # Wait for main content to load
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "token-info")))
            except TimeoutException:
                self.logger.warning("Timeout waiting for token info to load")
                return result
                
            # Extract overall rating
            try:
                rating_element = self.driver.find_element(By.CSS_SELECTOR, ".rating-badge, .score-badge, [class*='rating']")
                result.rating = rating_element.text.strip()
            except NoSuchElementException:
                self.logger.warning("Could not find rating element")
                
            # Extract liquidity information
            try:
                liquidity_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Liquidity') or contains(text(), 'liquidity')]")
                for element in liquidity_elements:
                    parent = element.find_element(By.XPATH, "./..")
                    if "locked" in parent.text.lower() or "yes" in parent.text.lower():
                        result.liquidity_locked = True
                        break
            except NoSuchElementException:
                pass
                
            # Extract ownership information
            try:
                ownership_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Ownership') or contains(text(), 'Renounced')]")
                for element in ownership_elements:
                    if "renounced" in element.text.lower() or "yes" in element.text.lower():
                        result.ownership_renounced = True
                        break
            except NoSuchElementException:
                pass
                
            # Extract whale percentage
            try:
                whale_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Whale') or contains(text(), 'whale') or contains(text(), '%')]")
                for element in whale_elements:
                    text = element.text
                    if "%" in text:
                        # Try to extract percentage
                        import re
                        percentages = re.findall(r'(\d+\.?\d*)%', text)
                        if percentages:
                            max_percentage = max(float(p) for p in percentages)
                            if max_percentage > result.whale_percentage:
                                result.whale_percentage = max_percentage
            except (NoSuchElementException, ValueError):
                pass
                
            # Extract contract verification status
            try:
                verified_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Verified') or contains(text(), 'Contract')]")
                for element in verified_elements:
                    if "verified" in element.text.lower() or "yes" in element.text.lower():
                        result.contract_verified = True
                        break
            except NoSuchElementException:
                pass
                
            # Extract honeypot status
            try:
                honeypot_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Honeypot') or contains(text(), 'honeypot')]")
                for element in honeypot_elements:
                    if "yes" in element.text.lower() or "true" in element.text.lower():
                        result.honeypot = True
                        break
            except NoSuchElementException:
                pass
                
            # Extract mint authority status
            try:
                mint_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Mint') or contains(text(), 'mint')]")
                for element in mint_elements:
                    if "no" in element.text.lower() or "false" in element.text.lower():
                        result.mint_authority = False
                        break
            except NoSuchElementException:
                pass
                
            # Extract freeze authority status
            try:
                freeze_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Freeze') or contains(text(), 'freeze')]")
                for element in freeze_elements:
                    if "no" in element.text.lower() or "false" in element.text.lower():
                        result.freeze_authority = False
                        break
            except NoSuchElementException:
                pass
                
            # Calculate overall score
            result.overall_score = self._calculate_safety_score(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error extracting safety data: {e}")
            return RugCheckResult(
                token_address=token_address,
                rating="Error",
                liquidity_locked=False,
                ownership_renounced=False,
                whale_percentage=0.0,
                holder_distribution={},
                contract_verified=False,
                honeypot=False,
                mint_authority=True,
                freeze_authority=True,
                overall_score=0.0
            )
            
    def _calculate_safety_score(self, result: RugCheckResult) -> float:
        """Calculate overall safety score based on various factors."""
        score = 0.0
        
        # Rating score (0-30 points)
        rating_scores = {
            "Good": 30,
            "Excellent": 30,
            "Safe": 25,
            "Fair": 15,
            "Poor": 5,
            "Bad": 0,
            "Dangerous": 0,
            "Rug": 0
        }
        
        rating_lower = result.rating.lower()
        for rating, points in rating_scores.items():
            if rating.lower() in rating_lower:
                score += points
                break
        else:
            # Default score for unknown ratings
            score += 10
            
        # Liquidity locked (0-20 points)
        if result.liquidity_locked:
            score += 20
            
        # Ownership renounced (0-20 points)
        if result.ownership_renounced:
            score += 20
            
        # Whale percentage (0-15 points)
        if result.whale_percentage <= 5:
            score += 15
        elif result.whale_percentage <= 10:
            score += 10
        elif result.whale_percentage <= 20:
            score += 5
            
        # Contract verified (0-10 points)
        if result.contract_verified:
            score += 10
            
        # Honeypot check (0-10 points)
        if not result.honeypot:
            score += 10
            
        # Mint authority (0-10 points)
        if not result.mint_authority:
            score += 10
            
        # Freeze authority (0-10 points)
        if not result.freeze_authority:
            score += 10
            
        return min(score, 100.0)
        
    def is_safe_token(self, result: RugCheckResult) -> bool:
        """Determine if a token is safe based on RugCheck analysis."""
        try:
            # Must have "Good" or better rating
            if result.rating.lower() not in ["good", "excellent", "safe"]:
                return False
                
            # Must not be a honeypot
            if result.honeypot:
                return False
                
            # Whale percentage should be reasonable
            if result.whale_percentage > 10:
                return False
                
            # Overall score should be above 70
            if result.overall_score < 70:
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error determining token safety: {e}")
            return False
            
    async def batch_analyze(self, tokens: list[TokenInfo]) -> Dict[str, RugCheckResult]:
        """Analyze multiple tokens in batch."""
        results = {}
        
        for token in tokens:
            try:
                result = await self.analyze_token(token)
                if result:
                    results[token.address] = result
                    
                # Add delay between requests to avoid rate limiting
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error in batch analysis for {token.symbol}: {e}")
                continue
                
        return results
