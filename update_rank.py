import os
import requests
from bs4 import BeautifulSoup
import datetime
import time

# ==========================================
# 1. 설정 (환경 변수에서 안전하게 키 가져오기)
# ==========================================
# 말씀하신 코드 그대로 적용했습니다.
RAW_API_KEY = os.environ.get('LOA_API_KEY', '')
API_KEY = RAW_API_KEY.replace("Bearer ", "").replace("bearer ", "").strip()

HTML_FILE = "index.html"

# 키가 제대로 들어왔는지 체크 (보안상 앞 5자리만 출력)
if not API_KEY:
    print("❌ 오류: 'LOA_API_KEY' 환경 변수가 설정되지 않았습니다!")
    exit(1)
else:
    print(f"🔑 API 키 로드 성공 (앞부분: {API_KEY[:5]}...)")

# ==========================================
# 2. HTML 파일 읽기
# ==========================================
print("📂 index.html 파일을 읽는 중...")
try:
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
except FileNotFoundError:
    print(f"❌ 오류: {HTML_FILE} 파일을 찾을 수 없습니다.")
    exit(1)

# HTML에서 캐릭터 목록(행)을 모두 찾습니다.
rows = soup.select('.rank-row')
print(f"📊 총 {len(rows)}명의 캐릭터를 발견했습니다. 전투력 업데이트를 시작합니다.")

# ==========================================
# 3. 각 캐릭터별 데이터 업데이트
# ==========================================
headers = {
    'accept': 'application/json',
    'authorization': f'bearer {API_KEY}'
}

for i, row in enumerate(rows, 1):
    # 1) HTML에서 캐릭터 닉네임 가져오기
    name_div = row.select_one('.char-name')
    if not name_div:
        continue
    
    name = name_div.text.strip()
    print(f"[{i}/{len(rows)}] '{name}' 조회 중...", end=" ")

    # 2) API 호출 (전투력 정보 가져오기)
    # 한글 닉네임 인코딩 등은 requests가 알아서 처리해줍니다.
    url = f"https://developer-lostark.game.onstove.com/armories/characters/{name}"
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            
            # ★ 핵심 수정: 'CombatPower' (전투력) 가져오기
            # 값이 없으면 0으로 처리
            combat_power = "0"
            if data and 'ArmoryProfile' in data:
                combat_power = data['ArmoryProfile'].get('CombatPower', '0')
            
            # 3) HTML 값 업데이트 (.battle-val 클래스 찾기)
            val_div = row.select_one('.battle-val') 
            
            if val_div:
                val_div.string = str(combat_power) # 값 덮어쓰기
                print(f"✅ 성공 -> {combat_power}")
            else:
                print("⚠️ 실패 (HTML에 .battle-val 클래스가 없음)")
                
        elif response.status_code == 429:
             print(f"⏳ 너무 빠릅니다! (429 Too Many Requests)")
             time.sleep(5) # 5초 대기
        else:
            print(f"❌ API 오류 ({response.status_code})")
            
    except Exception as e:
        print(f"💥 에러 발생: {e}")
    
    # 서버 부하 방지 및 API 제한 준수를 위해 딜레이
    time.sleep(0.1) # 0.1초 대기

# ==========================================
# 4. 업데이트 시간 기록 및 저장
# ==========================================
# 하단 시간 업데이트
time_div = soup.select_one('.update-time')
if time_div:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    time_div.string = f"마지막 업데이트: {now}"

# 파일 저장
with open(HTML_FILE, 'w', encoding='utf-8') as f:
    f.write(str(soup))

print("\n🎉 모든 작업이 완료되었습니다! index.html의 전투력이 갱신되었습니다.")
