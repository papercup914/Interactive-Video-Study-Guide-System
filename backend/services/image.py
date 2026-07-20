import os
import aiohttp
import urllib.parse
from dotenv import load_dotenv

load_dotenv()

async def fetch_unsplash_image(keyword: str) -> str:
    """
    Unsplash API를 사용하여 주어진 키워드와 관련된 가로 방향(landscape) 사진의 URL을 반환합니다.
    실패 시 기본 이미지를 반환합니다.
    """
    access_key = os.getenv("UNSPLASH_ACCESS_KEY")
    fallback_url = "https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=800&auto=format&fit=crop" # Default study note image
    
    if not access_key:
        print("Unsplash API Key not found. Using fallback image.")
        return fallback_url
        
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://api.unsplash.com/search/photos?query={encoded_keyword}&per_page=1&orientation=landscape&client_id={access_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("results") and len(data["results"]) > 0:
                        # Return the regular size image url
                        return data["results"][0]["urls"]["regular"]
                else:
                    print(f"Unsplash API error: {response.status}")
    except Exception as e:
        print(f"Failed to fetch image from Unsplash: {str(e)}")
        
    return fallback_url
