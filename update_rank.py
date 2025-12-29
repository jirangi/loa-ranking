import os
import requests
from bs4 import BeautifulSoup
import datetime
import time

# ==========================================
# 1. 설정
# ==========================================
RAW_API_KEY = os.environ.get('LOA_API_KEY', '')
API_KEY = RAW_API_KEY.replace("Bearer ", "").replace("bearer ", "").strip()

# ⭐ 관리할 파일 목록을 여기에 다 적어주면 됩니다!
TARGET_FILES = ["index.html", "jesukdan.html"]

if not API_KEY:
    print("❌ 오류: 'LOA_API_KEY' 환경 변수가 없습니다.")
    exit(1)

headers = {
    'accept': 'application/json',
    'authorization': f'bearer {API_KEY}'
}

# ==========================================
# 2. 파일별 업데이트 루프
# ==========================================
for file_name in TARGET_FILES:
    print(f"\n📂 '{file_name}' 업데이트 시작...")
    
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
    except FileNotFoundError:
        print(f"⚠️ 경고: {file_name} 파일이 없습니다. 넘어갑니다.")
        continue

    rows = soup.select('.rank-row')
    print(f"   📊 총 {len(rows)}명의 캐릭터 발견.")

    for i, row in enumerate(rows, 1):
        # 1) 닉네임 가져오기
        name_div = row.select_one('.char-name')
        if not name_div:
            continue
        
        name = name_div.text.strip()
        print(f"   [{i}/{len(rows)}] '{name}' 조회 중...", end=" ")

        # 2) API 호출
        url = f"https://developer-lostark.game.onstove.com/armories/characters/{name}"
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                profile = data.get('ArmoryProfile', {})
                
                # A. 전투력 업데이트
                combat_power = profile.get('CombatPower', '0')
                val_div = row.select_one('.battle-val')
                if val_div:
                    val_div.string = str(combat_power)

                # B. [추가기능] 캐릭터 이미지 자동 업데이트
                img_url = profile.get('CharacterImage')
                img_tag = row.select_one('.char-img')
                if img_url and img_tag:
                    img_tag['src'] = img_url

                print(f"✅ 완료 ({combat_power})")
                
            elif response.status_code == 429:
                print("⏳ (Too Many Requests) 5초 대기...")
                time.sleep(5)
            else:
                print(f"❌ 실패 ({response.status_code})")

        except Exception as e:
            print(f"💥 에러: {e}")
        
        time.sleep(0.1) # 딜레이

    # 3. 시간 업데이트 및 저장
    time_div = soup.select_one('.update-time')
    if time_div:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_div.string = f"마지막 업데이트: {now}"

    with open(file_name, 'w', encoding='utf-8') as f:
        f.write(str(soup))
    
    print(f"💾 '{file_name}' 저장 완료!")

print("\n🎉 모든 페이지 업데이트가 끝났습니다.")
