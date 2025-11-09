import aiohttp
from src.config import TON_API_KEY
import logging

logger = logging.getLogger(__name__)

class TONAPIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://tonapi.io/v2"

    async def get_nfts(self, wallet_address: str, limit: int = 10, offset: int = 0) -> dict:
        """Fetches NFTs for a given wallet address."""
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        params = {
            "limit": limit,
            "offset": offset,
        }
        url = f"{self.base_url}/accounts/{wallet_address}/nfts"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"Error fetching NFTs from TON API: {e}")
                return {"nft_items": []}
