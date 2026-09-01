import os
import sys
import time
import random
import requests
from dotenv import load_dotenv
from google import genai

# .env 로드
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")

def generate_thread_post(topic: str) -> str:
    """Google Gemini를 사용하여 스레드 최적화 포스팅 텍스트 생성"""
    if not GEMINI_API_KEY:
        print("[경고] GEMINI_API_KEY가 설정되지 않아 기본 테스트 문구를 반환합니다.")
        return f"💡 오늘 공유하고 싶은 인사이트: {topic}\n\n여러분은 이 주제에 대해 어떻게 생각하시나요? 댓글로 의견을 나눠주세요! 👇"

    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
    당신은 센스 있고 트렌디한 스레드(Threads) 전문 크리에이터입니다.
    주제: "{topic}"

    [작성 규칙]
    1. 분량은 3~5줄 내외로 간결하고 흡입력 있게 작성하세요.
    2. 어투: 친근하고 솔직한 구어체 (~해요, ~하더라고요).
    3. 본문에 링크(URL)는 절대 넣지 마세요 (도달률 저하 방지).
    4. 글의 맨 마지막 줄은 반드시 독자의 댓글 참여와 리포스트를 유도하는 질문으로 끝마치세요.
    5. 적절한 이모지를 2~3개 자연스럽게 섞어주세요.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()

def publish_to_threads(text_content: str, enable_jitter: bool = True) -> bool:
    """공식 Meta Threads API로 2단계(컨테이너 생성 -> 발행) 자동 포스팅"""
    if not THREADS_USER_ID or not THREADS_ACCESS_TOKEN:
        print("[에러] THREADS_USER_ID 또는 THREADS_ACCESS_TOKEN이 필요합니다. .env 파일을 확인하세요.")
        return False

    if enable_jitter:
        # 기계적인 정각 실행 회피 (1분~5분 랜덤 지연)
        jitter = random.randint(30, 180)
        print(f"⏳ 봇 탐지 방지를 위해 {jitter}초 동안 안전 대기 후 발행합니다...")
        time.sleep(jitter)

    # 1단계: 미디어 컨테이너 생성
    creation_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads"
    creation_payload = {
        "media_type": "TEXT",
        "text": text_content,
        "access_token": THREADS_ACCESS_TOKEN
    }
    
    print("📤 Step 1: 스레드 미디어 컨테이너 생성 중...")
    create_res = requests.post(creation_url, data=creation_payload).json()
    container_id = create_res.get("id")

    if not container_id:
        print(f"❌ 컨테이너 생성 실패: {create_res}")
        return False

    print(f"✅ 컨테이너 생성 완료 (ID: {container_id})")
    time.sleep(5)  # 메타 서버 처리 대기

    # 2단계: 스레드 발행
    publish_url = f"https://graph.threads.net/v1.0/{THREADS_USER_ID}/threads_publish"
    publish_payload = {
        "creation_id": container_id,
        "access_token": THREADS_ACCESS_TOKEN
    }

    print("🚀 Step 2: 스레드 정식 게시(Publish) 중...")
    publish_res = requests.post(publish_url, data=publish_payload).json()
    post_id = publish_res.get("id")

    if post_id:
        print(f"🎉 성공적으로 게시되었습니다! Post ID: {post_id}")
        return True
    else:
        print(f"❌ 스레드 게시 실패: {publish_res}")
        return False

if __name__ == "__main__":
    sample_topic = sys.argv[1] if len(sys.argv) > 1 else "바쁜 일상에서 집중력을 2배 올려주는 뽀모도로 시간 관리 팁"
    print(f"📝 포스팅 생성 시작: 주제 = {sample_topic}")
    content = generate_thread_post(sample_topic)
    print("\n--- [생성된 스레드 본문] ---")
    print(content)
    print("---------------------------\n")

    # 실제 발행을 원할 경우 환경변수 설정 후 아래 주석을 해제하세요:
    # publish_to_threads(content, enable_jitter=False)
