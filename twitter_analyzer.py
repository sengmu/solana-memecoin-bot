"""
Twitter analysis module for evaluating token quality based on social media presence.
"""

import asyncio
import aiohttp
import logging
import re
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import quote

from models import TokenInfo, TwitterProfile, TwitterTweet, BotConfig

class TwitterAnalyzer:
    """Analyzes Twitter profiles and tweets for token quality assessment."""

    def __init__(self, config: BotConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            'Authorization': f'Bearer {config.twitter_bearer_token}',
            'Content-Type': 'application/json'
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def analyze_token(self, token: TokenInfo) -> float:
        """Analyze a token's Twitter presence and return quality score."""
        try:
            if not self.config.twitter_bearer_token:
                self.logger.warning("Twitter Bearer token not configured")
                return 0.0

            # Search for token-related Twitter accounts
            twitter_accounts = await self._search_token_accounts(token)

            if not twitter_accounts:
                self.logger.info(f"No Twitter accounts found for {token.symbol}")
                return 0.0

            # Analyze each account and get the best score
            best_score = 0.0
            for account in twitter_accounts:
                try:
                    profile = await self._get_user_profile(account['username'])
                    if profile:
                        tweets = await self._get_user_tweets(profile.username, limit=50)
                        score = self._calculate_quality_score(profile, tweets, token)
                        best_score = max(best_score, score)

                except Exception as e:
                    self.logger.error(f"Error analyzing account {account['username']}: {e}")
                    continue

            return min(best_score, 100.0)  # Cap at 100

        except Exception as e:
            self.logger.error(f"Error analyzing token {token.symbol}: {e}")
            return 0.0

    async def _search_token_accounts(self, token: TokenInfo) -> List[Dict[str, str]]:
        """Search for Twitter accounts related to the token."""
        try:
            # Search queries to find relevant accounts
            search_queries = [
                f'${token.symbol}',
                f'#{token.symbol}',
                token.name,
                f'{token.symbol} token',
                f'{token.symbol} coin'
            ]

            accounts = []
            for query in search_queries:
                try:
                    url = "https://api.twitter.com/2/tweets/search/recent"
                    params = {
                        'query': f'{query} -is:retweet lang:en',
                        'max_results': 10,
                        'tweet.fields': 'author_id,created_at,public_metrics',
                        'user.fields': 'username,name,public_metrics,verified'
                    }

                    async with self.session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()

                            # Extract unique users
                            users = {}
                            for tweet in data.get('data', []):
                                author_id = tweet.get('author_id')
                                if author_id:
                                    # Get user info from includes
                                    for user in data.get('includes', {}).get('users', []):
                                        if user['id'] == author_id:
                                            username = user.get('username')
                                            if username and username not in users:
                                                users[username] = {
                                                    'username': username,
                                                    'name': user.get('name', ''),
                                                    'followers': user.get('public_metrics', {}).get('followers_count', 0),
                                                    'verified': user.get('verified', False)
                                                }
                            accounts.extend(users.values())

                except Exception as e:
                    self.logger.error(f"Error searching for query '{query}': {e}")
                    continue

            # Remove duplicates and sort by followers
            unique_accounts = {}
            for account in accounts:
                username = account['username']
                if username not in unique_accounts or account['followers'] > unique_accounts[username]['followers']:
                    unique_accounts[username] = account

            return list(unique_accounts.values())

        except Exception as e:
            self.logger.error(f"Error searching token accounts: {e}")
            return []

    async def _get_user_profile(self, username: str) -> Optional[TwitterProfile]:
        """Get detailed user profile information."""
        try:
            url = f"https://api.twitter.com/2/users/by/username/{username}"
            params = {
                'user.fields': 'id,username,name,description,public_metrics,verified,created_at'
            }

            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    user_data = data.get('data', {})

                    if user_data:
                        metrics = user_data.get('public_metrics', {})
                        created_at = datetime.now()

                        # Parse creation date
                        if 'created_at' in user_data:
                            try:
                                created_at = datetime.fromisoformat(
                                    user_data['created_at'].replace('Z', '+00:00')
                                )
                            except ValueError:
                                pass

                        return TwitterProfile(
                            username=user_data.get('username', ''),
                            display_name=user_data.get('name', ''),
                            followers_count=metrics.get('followers_count', 0),
                            following_count=metrics.get('following_count', 0),
                            tweet_count=metrics.get('tweet_count', 0),
                            verified=user_data.get('verified', False),
                            created_at=created_at,
                            bio=user_data.get('description', '')
                        )

        except Exception as e:
            self.logger.error(f"Error getting user profile for {username}: {e}")

        return None

    async def _get_user_tweets(self, username: str, limit: int = 50) -> List[TwitterTweet]:
        """Get recent tweets from a user."""
        try:
            # First get user ID
            user_url = f"https://api.twitter.com/2/users/by/username/{username}"
            async with self.session.get(user_url) as response:
                if response.status != 200:
                    return []

                user_data = await response.json()
                user_id = user_data.get('data', {}).get('id')
                if not user_id:
                    return []

            # Get tweets
            tweets_url = f"https://api.twitter.com/2/users/{user_id}/tweets"
            params = {
                'max_results': min(limit, 100),
                'tweet.fields': 'created_at,public_metrics',
                'exclude': 'retweets,replies'
            }

            async with self.session.get(tweets_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    tweets = []

                    for tweet_data in data.get('data', []):
                        metrics = tweet_data.get('public_metrics', {})
                        created_at = datetime.now()

                        # Parse tweet date
                        if 'created_at' in tweet_data:
                            try:
                                created_at = datetime.fromisoformat(
                                    tweet_data['created_at'].replace('Z', '+00:00')
                                )
                            except ValueError:
                                pass

                        tweet = TwitterTweet(
                            id=tweet_data.get('id', ''),
                            text=tweet_data.get('text', ''),
                            created_at=created_at,
                            retweet_count=metrics.get('retweet_count', 0),
                            like_count=metrics.get('like_count', 0),
                            reply_count=metrics.get('reply_count', 0)
                        )

                        # Calculate engagement score
                        tweet.engagement_score = self._calculate_tweet_engagement(tweet)
                        tweets.append(tweet)

                    return tweets

        except Exception as e:
            self.logger.error(f"Error getting tweets for {username}: {e}")

        return []

    def _calculate_quality_score(self, profile: TwitterProfile, tweets: List[TwitterTweet], token: TokenInfo) -> float:
        """Calculate overall quality score based on profile and tweets."""
        try:
            score = 0.0

            # Profile quality (40% of total score)
            profile_score = self._calculate_profile_score(profile)
            score += profile_score * 0.4

            # Tweet quality (40% of total score)
            tweet_score = self._calculate_tweet_score(tweets, token)
            score += tweet_score * 0.4

            # Token relevance (20% of total score)
            relevance_score = self._calculate_relevance_score(profile, tweets, token)
            score += relevance_score * 0.2

            return min(score, 100.0)

        except Exception as e:
            self.logger.error(f"Error calculating quality score: {e}")
            return 0.0

    def _calculate_profile_score(self, profile: TwitterProfile) -> float:
        """Calculate profile quality score."""
        score = 0.0

        # Follower count (0-30 points)
        if profile.followers_count >= 100000:
            score += 30
        elif profile.followers_count >= 50000:
            score += 25
        elif profile.followers_count >= 10000:
            score += 20
        elif profile.followers_count >= 5000:
            score += 15
        elif profile.followers_count >= 1000:
            score += 10
        elif profile.followers_count >= 100:
            score += 5

        # Verification status (0-20 points)
        if profile.verified:
            score += 20

        # Account age (0-15 points)
        account_age_days = (datetime.now() - profile.created_at).days
        if account_age_days >= 365:
            score += 15
        elif account_age_days >= 180:
            score += 10
        elif account_age_days >= 90:
            score += 5

        # Follower to following ratio (0-15 points)
        if profile.following_count > 0:
            ratio = profile.followers_count / profile.following_count
            if ratio >= 10:
                score += 15
            elif ratio >= 5:
                score += 10
            elif ratio >= 2:
                score += 5

        # Bio quality (0-20 points)
        bio_score = self._analyze_bio_quality(profile.bio)
        score += bio_score

        return min(score, 100.0)

    def _calculate_tweet_score(self, tweets: List[TwitterTweet], token: TokenInfo) -> float:
        """Calculate tweet quality score."""
        if not tweets:
            return 0.0

        score = 0.0

        # Average engagement (0-40 points)
        total_engagement = sum(tweet.engagement_score for tweet in tweets)
        avg_engagement = total_engagement / len(tweets)
        score += min(avg_engagement * 0.4, 40)

        # Recent activity (0-30 points)
        recent_tweets = [t for t in tweets if (datetime.now() - t.created_at).days <= 7]
        if recent_tweets:
            score += min(len(recent_tweets) * 2, 30)

        # Token mentions (0-30 points)
        token_mentions = 0
        for tweet in tweets:
            if self._tweet_mentions_token(tweet, token):
                token_mentions += 1

        mention_score = min(token_mentions * 5, 30)
        score += mention_score

        return min(score, 100.0)

    def _calculate_relevance_score(self, profile: TwitterProfile, tweets: List[TwitterTweet], token: TokenInfo) -> float:
        """Calculate how relevant the account is to the token."""
        score = 0.0

        # Check if username/symbol match
        username_lower = profile.username.lower()
        symbol_lower = token.symbol.lower()

        if symbol_lower in username_lower or username_lower in symbol_lower:
            score += 30

        # Check bio for token mentions
        bio_lower = profile.bio.lower()
        if symbol_lower in bio_lower or token.name.lower() in bio_lower:
            score += 20

        # Check tweets for token relevance
        relevant_tweets = 0
        for tweet in tweets:
            if self._tweet_mentions_token(tweet, token):
                relevant_tweets += 1

        if relevant_tweets > 0:
            score += min(relevant_tweets * 10, 50)

        return min(score, 100.0)

    def _calculate_tweet_engagement(self, tweet: TwitterTweet) -> float:
        """Calculate engagement score for a single tweet."""
        # Weighted engagement score
        engagement = (
            tweet.like_count * 1.0 +
            tweet.retweet_count * 2.0 +
            tweet.reply_count * 3.0
        )

        # Normalize based on follower count (if available)
        # This is a simplified calculation
        return min(engagement / 100, 100.0)

    def _analyze_bio_quality(self, bio: str) -> float:
        """Analyze bio quality and return score."""
        if not bio:
            return 0.0

        score = 0.0

        # Length (0-5 points)
        if len(bio) >= 100:
            score += 5
        elif len(bio) >= 50:
            score += 3
        elif len(bio) >= 20:
            score += 1

        # Professional indicators (0-10 points)
        professional_keywords = ['founder', 'ceo', 'developer', 'team', 'project', 'official']
        bio_lower = bio.lower()
        for keyword in professional_keywords:
            if keyword in bio_lower:
                score += 2

        # Contact information (0-5 points)
        if any(char in bio for char in ['@', 'http', 'www', '.com']):
            score += 5

        return min(score, 20.0)

    def _tweet_mentions_token(self, tweet: TwitterTweet, token: TokenInfo) -> bool:
        """Check if a tweet mentions the token."""
        text_lower = tweet.text.lower()
        symbol_lower = token.symbol.lower()
        name_lower = token.name.lower()

        return (
            f'${symbol_lower}' in text_lower or
            f'#{symbol_lower}' in text_lower or
            symbol_lower in text_lower or
            name_lower in text_lower
        )
