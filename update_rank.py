import os
import requests
import json
import time
import csv
from io import StringIO
from datetime import datetime

# ==========================================
# 1. 설정
# ==========================================
RAW_API_KEY = os.environ.get('LOA_API_KEY', '')
API_KEY = RAW_API_KEY.replace("Bearer ", "").replace("bearer ", "").strip()
HEADERS = {'accept': 'application/json', 'authorization': f'bearer {API_KEY}'}

# 👇 [중요] 아까 복사한 구글 시트 CSV 링크를 따옴표 안에 넣으세요!
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYJZDPz2DK2bYNbwDWg-Lrd2GWOGunX8BZGYsW_nE7Xomcv93zCtN00vj_tFZESjQGCYKsL1BlxJ03/pub?output=csv"

# 파일 매핑
TARGETS = {
    "jesukdan.txt": "jesukdan_data.json", 
    # "nolja.txt": "nolja_data.json" 
}

# ==========================================
# 2. 기능 함수들
# ==========================================
def get_google_sheet_names(url):
    """구글 시트에서 신청된 닉네임들을 가져옵니다."""
    new_names = []
    try:
        print(f"📡 구글 시트 데이터 조회 중...")
        res = requests.get(url)
        if res.status_code == 200:
            # CSV 데이터 파싱
            f = StringIO(res.text)
            reader = csv.reader(f)
            next(reader) # 첫 번째 줄(헤더: 타임스탬프, 닉네임) 건너뛰기
            
            for row in reader:
                if len(row) > 1: # 닉네임 컬럼이 있는지 확인
                    nickname = row[1].strip() # B열(두번째)에 닉네임이 있다고 가정
                    if nickname:
                        new_names.append(nickname)
            print(f"   ✅ 구글 시트에서 {len(new_names)}명의 신청자를 찾았습니다.")
        else:
            print(f"   ❌ 구글 시트 조회 실패 ({res.status_code})")
    except Exception as e:
        print(f"   💥 구글 시트 에러: {e}")
    return new_names

def get_character_data(name):
    url = f"https://developer-lostark.game.onstove.com/armories/characters/{name}"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 429:
            print("⏳ 429 Too Many Requests - 잠시 대기")
            time.sleep(5)
            return None
    except Exception as e:
        print(f"Error: {e}")
    return None

# ==========================================
# 3. 메인 로직
# ==========================================
for txt_file, json_filename in TARGETS.items():
    print(f"\n📂 '{json_filename}' 업데이트 준비...")
    
    # A. 로컬 파일(.txt) 명단 읽기
    local_names = []
    if os.path.exists(txt_file):
        with open(txt_file, 'r', encoding='utf-8') as f:
            local_names = [line.strip() for line in f if line.strip()]

    # B. 구글 시트 명단 읽기 (제숙단인 경우에만)
    sheet_names = []
    if "jesukdan" in json_filename and GOOGLE_SHEET_URL.startswith("http"):
        sheet_names = get_google_sheet_names(GOOGLE_SHEET_URL)

    # C. 명단 합치기 (중복 제거)
    # set()을 사용해 중복을 없애고 다시 리스트로 만듭니다.
    all_names = list(set(local_names + sheet_names))
    print(f"   📊 총 {len(all_names)}명의 데이터를 갱신합니다.")

    results = []
    
    # D. 로스트아크 API 조회
    for i, name in enumerate(all_names):
        print(f"   [{i+1}/{len(all_names)}] '{name}' 정보 수집...", end=" ")
        data = get_character_data(name)
        
        if data:
            profile = data.get('ArmoryProfile', {})
            
            # 아이템 레벨 안전하게 가져오기
            item_level = profile.get('ItemMaxLevel')
            if not item_level:
                item_level = profile.get('ItemAvgLevel', '0.00')

            char_info = {
                "name": name,
                "job": profile.get('CharacterClassName', '정보없음'),
                "img": profile.get('CharacterImage', 'https://cdn-lostark.game.onstove.com/2018/obt/assets/images/common/thumb/default_profile.png'),
                "itemLevel": item_level,
                "combatPower": profile.get('CombatPower', '0')
            }
            results.append(char_info)
            print("✅")
        else:
            print("❌ (검색 실패)")
        
        time.sleep(0.1)

    # E. JSON 파일 저장
    save_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "characters": results
    }
    
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 저장 완료: {json_filename}")

print("\n🎉 모든 작업 완료.")
