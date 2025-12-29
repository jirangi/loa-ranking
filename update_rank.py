import os
import requests
import json
import time
import csv
from io import StringIO
from datetime import datetime, timedelta

# ==========================================
# 1. 설정
# ==========================================
RAW_API_KEY = os.environ.get('LOA_API_KEY', '')
API_KEY = RAW_API_KEY.replace("Bearer ", "").replace("bearer ", "").strip()
HEADERS = {'accept': 'application/json', 'authorization': f'bearer {API_KEY}'}

# 그룹 설정 (링크 유지!)
GROUPS = [
    {
        "name": "제숙단",
        "txt_file": "jesukdan.txt",
        "json_file": "jesukdan_data.json",
        "sheet_url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vRYJZDPz2DK2bYNbwDWg-Lrd2GWOGunX8BZGYsW_nE7Xomcv93zCtN00vj_tFZESjQGCYKsL1BlxJ03/pub?output=csv"
    },
    {
        "name": "놀자에요",
        "txt_file": "nolja.txt",
        "json_file": "nolja_data.json",
        "sheet_url": "https://docs.google.com/spreadsheets/d/1BGzvgQ_PN70_DUCv5b0lbdIp5Fq3arIkPRpmZ2AVfWY/export?format=csv&gid=1405051"
    }
]

# ==========================================
# 2. 기능 함수들
# ==========================================
def get_google_sheet_names(url):
    new_names = []
    if not url or "http" not in url: return []
    try:
        res = requests.get(url)
        if res.status_code == 200:
            res.encoding = 'utf-8'
            f = StringIO(res.text)
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) > 1 and row[1].strip():
                    new_names.append(row[1].strip())
    except: pass
    return new_names

def get_character_data(name):
    # 특수문자 처리
    safe_name = requests.utils.quote(name)
    url = f"https://developer-lostark.game.onstove.com/armories/characters/{safe_name}"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200: return res.json()
        elif res.status_code == 429: 
            print("⏳ API 제한 대기 (5초)...")
            time.sleep(5)
            # 재시도
            return get_character_data(name)
    except: pass
    return None

def get_siblings(name):
    """원정대 캐릭터 목록 조회 (1700 이상만 추출)"""
    safe_name = requests.utils.quote(name)
    url = f"https://developer-lostark.game.onstove.com/characters/{safe_name}/siblings"
    high_level_siblings = []
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            siblings = res.json()
            for char in siblings:
                # 레벨 확인
                lvl_str = char.get('ItemMaxLevel', '0').replace(',', '')
                try:
                    if float(lvl_str) >= 1700.0:
                        high_level_siblings.append(char.get('CharacterName'))
                except: continue
        elif res.status_code == 429:
            time.sleep(5)
    except: pass
    return high_level_siblings

# ==========================================
# 3. 메인 로직
# ==========================================
if not API_KEY: exit(1)

for group in GROUPS:
    print(f"\n📂 [{group['name']}] 처리 중...")
    
    # 1. 기존 데이터 로드 (날짜 기억용)
    prev_dates = {} # { "닉네임": "2025-01-01" }
    if os.path.exists(group['json_file']):
        try:
            with open(group['json_file'], 'r', encoding='utf-8') as f:
                old_json = json.load(f)
                for char in old_json.get('characters', []):
                    if char.get('congrats_date'):
                        prev_dates[char['name']] = char['congrats_date']
        except: pass

    # 2. 명단 수집 (로컬 + 시트)
    local_names = []
    if os.path.exists(group['txt_file']):
        with open(group['txt_file'], 'r', encoding='utf-8') as f:
            local_names = [line.strip() for line in f if line.strip()]
    sheet_names = get_google_sheet_names(group['sheet_url'])
    
    # 기본 검색 대상
    base_names = list(set(local_names + sheet_names))
    
    # 3. 원정대(형제) 검색 및 추가
    final_search_list = set(base_names) # 중복 제거용 집합
    
    print(f"   🔍 원정대 캐릭터 검색 중 (오래 걸릴 수 있음)...")
    for name in base_names:
        # 본캐 검색하면서 형제도 같이 찾음
        siblings = get_siblings(name)
        if siblings:
            for s in siblings:
                final_search_list.add(s)
        time.sleep(0.6) # API 보호를 위해 딜레이

    print(f"   📊 최종 검색 대상: {len(final_search_list)}명")

    # 4. 상세 정보 조회
    results = []
    for i, name in enumerate(final_search_list):
        print(f"[{i+1}/{len(final_search_list)}] {name}...", end=" ")
        data = get_character_data(name)
        
        if data:
            profile = data.get('ArmoryProfile', {})
            item_level_str = profile.get('ItemMaxLevel') or profile.get('ItemAvgLevel', '0.00')
            
            # 공격력 찾기
            combat_power = '0'
            stats = profile.get('Stats', [])
            for stat in stats:
                if stat.get('Type') == '공격력':
                    combat_power = stat.get('Value', '0')
                    break
            if combat_power == '0':
                combat_power = profile.get('CombatPower', '0')

            # 축하 날짜 로직
            congrats_date = ""
            try:
                lvl_float = float(item_level_str.replace(',', ''))
                if lvl_float >= 1700.0:
                    # 1700 넘음! 기존 기록 있는지 확인
                    if name in prev_dates:
                        congrats_date = prev_dates[name] # 옛날 날짜 유지
                    else:
                        congrats_date = datetime.now().strftime("%Y-%m-%d") # 오늘 달성!
            except: pass

            results.append({
                "name": name,
                "job": profile.get('CharacterClassName', '정보없음'),
                "img": profile.get('CharacterImage', 'https://cdn-lostark.game.onstove.com/2018/obt/assets/images/common/thumb/default_profile.png'),
                "itemLevel": item_level_str,
                "combatPower": combat_power,
                "congrats_date": congrats_date # 날짜 저장
            })
            print(f"✅")
        else:
            print("❌")
        time.sleep(0.1)

    # 5. 저장
    with open(group['json_file'], 'w', encoding='utf-8') as f:
        json.dump({"updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "characters": results}, f, ensure_ascii=False, indent=2)
    print("저장 완료.")
