import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

TONAPI_TOKEN = os.getenv("TONAPI_TOKEN")
BASE_URL = "https://tonapi.io/v2"

class TONAPIService:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {TONAPI_TOKEN}"
        }

    async def get_wallet_nfts(self, wallet_address: str):
        """Получить NFT кошелька (без сохранения в БД)"""
        url = f"{BASE_URL}/accounts/{wallet_address}/nfts?limit=1000&offset=0&indirect_ownership=false"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    return data.get("nft_items", [])
            except aiohttp.ClientError as e:
                print(f"Error fetching NFTs for wallet {wallet_address}: {e}")
                return []

    async def get_nft_details(self, nft_address: str):
        """Получить детали конкретной NFT"""
        url = f"{BASE_URL}/nfts/{nft_address}"
        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    return await response.json()
            except aiohttp.ClientError as e:
                print(f"Error fetching details for NFT {nft_address}: {e}")
                return None
