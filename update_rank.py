import os
import requests
import json
import time
import csv
from io import StringIO
from datetime import datetime

# ==========================================
# 1. 설정 (API 키)
# ==========================================
RAW_API_KEY = os.environ.get('LOA_API_KEY', '')
API_KEY = RAW_API_KEY.replace("Bearer ", "").replace("bearer ", "").strip()
HEADERS = {'accept': 'application/json', 'authorization': f'bearer {API_KEY}'}

# ==========================================
# 2. 그룹별 설정 (구글 시트 링크 유지하세요!)
# ==========================================
GROUPS = [
    {
        "name": "제숙단",
        "txt_file": "jesukdan.txt",
        "json_file": "jesukdan_data.json",
        "sheet_url": "여기에_제숙단_CSV_링크를_넣으세요"  # 👈 [기존 링크 유지]
    },
    {
        "name": "놀자에요",
        "txt_file": "nolja.txt",
        "json_file": "nolja_data.json",
        "sheet_url": "여기에_놀자에요_CSV_링크를_넣으세요" # 👈 [기존 링크 유지]
    }
]

# ==========================================
# 3. 기능 함수들
# ==========================================
def get_google_sheet_names(url):
    """구글 시트에서 신청된 닉네임들을 가져옵니다."""
    new_names = []
    if not url or "http" not in url:
        return []
        
    try:
        print(f"   📡 시트 데이터 조회 중...")
        res = requests.get(url)
        if res.status_code == 200:
            f = StringIO(res.text)
            reader = csv.reader(f)
            next(reader) # 헤더 건너뛰기
            for row in reader:
                if len(row) > 1:
                    nickname = row[1].strip()
                    if nickname:
                        new_names.append(nickname)
            print(f"   ✅ 시트에서 {len(new_names)}명 확인")
        else:
            print(f"   ❌ 시트 조회 실패 ({res.status_code})")
    except Exception as e:
        print(f"   💥 시트 에러: {e}")
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
# 4. 메인 로직
# ==========================================
if not API_KEY:
    print("❌ 오류: API 키가 없습니다.")
    exit(1)

for group in GROUPS:
    print(f"\n📂 [{group['name']}] 업데이트 시작...")
    
    # A. 로컬 파일 명단 읽기
    local_names = []
    if os.path.exists(group['txt_file']):
        with open(group['txt_file'], 'r', encoding='utf-8') as f:
            local_names = [line.strip() for line in f if line.strip()]
    
    # B. 구글 시트 명단 읽기
    sheet_names = get_google_sheet_names(group['sheet_url'])

    # C. 명단 합치기
    all_names = list(set(local_names + sheet_names))
    print(f"   📊 총 {len(all_names)}명의 데이터 갱신 시작")

    results = []
    
    # D. 로아 API 조회
    for i, name in enumerate(all_names):
        print(f"   [{i+1}/{len(all_names)}] '{name}'...", end=" ")
        data = get_character_data(name)
        
        if data:
            profile = data.get('ArmoryProfile', {})
            
            # 1. 아이템 레벨 안전하게 가져오기
            item_level = profile.get('ItemMaxLevel')
            if not item_level:
                item_level = profile.get('ItemAvgLevel', '0.00')

            # 2. 전투력(공격력) 찾기 [수정된 부분]
            # Stats 리스트 안에서 "Type"이 "공격력"인 것을 찾습니다.
            combat_power = '0'
            stats_list = profile.get('Stats', [])
            if stats_list:
                for stat in stats_list:
                    if stat.get('Type') == '공격력':
                        combat_power = stat.get('Value', '0')
                        break

            char_info = {
                "name": name,
                "job": profile.get('CharacterClassName', '정보없음'),
                "img": profile.get('CharacterImage', 'https://cdn-lostark.game.onstove.com/2018/obt/assets/images/common/thumb/default_profile.png'),
                "itemLevel": item_level,
                "combatPower": combat_power
            }
            results.append(char_info)
            print(f"✅ (Lv.{item_level} / {combat_power})")
        else:
            print("❌")
        
        time.sleep(0.1)

    # E. JSON 저장
    save_data = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "characters": results
    }
    
    with open(group['json_file'], 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 '{group['json_file']}' 저장 완료!")

print("\n🎉 모든 그룹 업데이트 완료.")
