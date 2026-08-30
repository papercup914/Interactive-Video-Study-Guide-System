import time
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_web(url: str):
    """
    Scrape text from a webpage using r.jina.ai for high quality markdown.
    Returns (transcript, title).
    """
    if not url or not isinstance(url, str):
        raise ValueError("유효하지 않은 URL입니다.")
        
    target_url = url.strip()
    # 유튜브 단축 URL 또는 파라미터가 포함된 경우 표준 URL로 정규화
    if "youtu.be" in target_url or "youtube.com" in target_url:
        try:
            from backend.services.video import extract_video_id
            vid = extract_video_id(target_url)
            if vid:
                target_url = f"https://www.youtube.com/watch?v={vid}"
        except Exception:
            pass

    try:
        jina_url = f"https://r.jina.ai/{target_url}"
        headers = {
            "Accept": "application/json",
            "X-Return-Format": "markdown", # Ensures we get markdown with images
        }
        
        # We can also pass an API key if needed, but r.jina.ai is often free without it
        jina_api_key = os.getenv("JINA_API_KEY")
        if jina_api_key:
            headers["Authorization"] = f"Bearer {jina_api_key}"
            
        response = requests.get(jina_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        if data.get("code") == 200 and data.get("data"):
            content = data["data"].get("content", "")
            title = data["data"].get("title", target_url)
            if title:
                title = title.replace(" - YouTube", "").replace("- YouTube", "").replace("YouTube", "").strip()
            if not title:
                title = "학습 가이드"
            if content and len(content.strip()) >= 200:
                return content.strip(), title
            else:
                raise Exception(f"Jina Reader로 추출된 텍스트가 너무 짧습니다 ({len(content) if content else 0}자).")
        else:
            raise Exception(f"Jina API returned error: {data}")
            
    except Exception as e:
        print(f"r.jina.ai failed, falling back to BeautifulSoup: {e}")
        # Fallback to BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = (soup.title.string if soup.title else target_url) or target_url
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        if len(text) < 100:
            raise Exception("웹 페이지에서 충분한 본문 텍스트를 가져올 수 없습니다 (내용이 너무 짧거나 크롤링이 차단된 페이지입니다).")
        return text, title


def extract_text_from_pdf(file_path: str) -> str:
    """
    Fast and lightweight PDF text extraction using pure-python pypdf.
    """
    if not file_path or not os.path.exists(file_path):
        raise ValueError(f"유효하지 않은 PDF 파일 경로입니다: {file_path}")
        
    try:
        from pypdf import PdfReader
        print(f"Reading {file_path} with pypdf (Lightweight Mode)...")
        reader = PdfReader(file_path)
        
        full_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text and page_text.strip():
                full_text.append(page_text.strip())
                
        if not full_text:
            raise ValueError("PDF 파일에서 텍스트를 추출할 수 없습니다 (스캔 이미지 PDF일 수 있습니다).")
            
        return "\n\n---\n\n".join(full_text)
        
    except Exception as e:
        print(f"PDF 추출 실패: {str(e)}")
        raise Exception(f"PDF 로컬 파싱 실패: {str(e)}")

def extract_text_with_pymupdf4llm(file_path: str) -> str:
    """
    Fallback markdown extraction using pypdf.
    """
    return extract_text_from_pdf(file_path)

def upload_pdf_to_gemini(file_path: str):
    """
    Upload PDF to Gemini Files API and poll until ACTIVE (Option C).
    Returns a special string with the file name.
    """
    from backend.services.llm import get_gemini_client
    import time
    
    try:
        print(f"Uploading {file_path} to Gemini (Option C)...")
        client = get_gemini_client()
        uploaded_file = client.files.upload(file=file_path)
        
        # ACTIVE 상태가 될 때까지 폴링 대기
        while uploaded_file.state.name == "PROCESSING":
            print(f"Gemini PDF 처리 중 대기... (상태: {uploaded_file.state.name})")
            time.sleep(3)
            uploaded_file = client.files.get(name=uploaded_file.name)
            
        if uploaded_file.state.name == "FAILED":
            raise Exception("Gemini 파일 업로드 처리 실패")
            
        print(f"Gemini Upload Complete: {uploaded_file.name}")
        return f"GEMINI_FILE_URI::{uploaded_file.name}"
    except Exception as e:
        print(f"Gemini 파일 업로드 실패: {str(e)}")
        raise Exception(f"Gemini 파일 업로드 실패: {str(e)}")
