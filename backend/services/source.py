import time
import os
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def extract_text_from_web(url: str):
    """
    Scrape text from a general webpage.
    Returns (transcript, title).
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get title
        title = soup.title.string if soup.title else url
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.extract()
            
        # Get text
        text = soup.get_text(separator='\n')
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        if len(text) < 50:
            raise Exception("가져올 수 없습니다 (내용이 너무 짧거나 크롤링이 차단된 페이지입니다).")
            
        return text, title
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"가져올 수 없습니다 (네트워크 오류 또는 차단된 페이지입니다). 상세: {str(e)}")
    except Exception as e:
        raise Exception(f"웹 페이지 추출 실패: {str(e)}")

def extract_text_from_pdf(file_path: str):
    """
    Upload PDF to Gemini Files API, poll until ACTIVE, and extract text/tables.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("GEMINI_API_KEY is not set.")
    
    genai.configure(api_key=api_key)
    
    try:
        print(f"Uploading {file_path} to Gemini...")
        uploaded_file = genai.upload_file(path=file_path, display_name=os.path.basename(file_path))
        
        # Poll until ACTIVE
        print(f"File uploaded. Polling state (current: {uploaded_file.state.name})...")
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)
            print(f"Polling state: {uploaded_file.state.name}")
            
        if uploaded_file.state.name == "FAILED":
            raise Exception("Gemini PDF 업로드 실패 (FAILED 상태).")
            
        print("File is ACTIVE. Extracting text...")
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = (
            "이 문서는 PDF 파일입니다. 문서 안의 모든 텍스트, 표(Table), 차트/이미지의 설명(Caption) 등 의미 있는 "
            "모든 정보를 마크다운 형식으로 상세히 추출해주세요. 이미지가 있다면 이미지에서 유추할 수 있는 내용도 글로 묘사해주세요."
        )
        
        response = model.generate_content([uploaded_file, prompt])
        
        # Optional: delete file after extraction to save quota
        try:
            genai.delete_file(uploaded_file.name)
        except Exception:
            pass
            
        return response.text
        
    except Exception as e:
        raise Exception(f"PDF 추출 실패: {str(e)}")
