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
        "sheet_url": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQqw-xJfEXM-EvpHbNaN3W-6X0AwlcKdiIGMLhHuD70POHaBZgWERs551beDYoSyieMupea1tLuM8mQ/pub?output=csv"
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
    safe_name = requests.utils.quote(name)
    url = f"https://developer-lostark.game.onstove.com/armories/characters/{safe_name}"
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200: return res.json()
        elif res.status_code == 429: 
            time.sleep(5)
            return get_character_data(name)
    except: pass
    return None

def get_siblings(name):
    safe_name = requests.utils.quote(name)
    url = f"https://developer-lostark.game.onstove.com/characters/{safe_name}/siblings"
    high_level_siblings = []
    try:
        res = requests.get(url, headers=HEADERS)
        if res.status_code == 200:
            for char in res.json():
                try:
                    if float(char.get('ItemMaxLevel', '0').replace(',', '')) >= 1700.0:
                        high_level_siblings.append(char.get('CharacterName'))
                except: continue
        elif res.status_code == 429: time.sleep(5)
    except: pass
    return high_level_siblings

# ==========================================
# 3. 메인 로직
# ==========================================
if not API_KEY: exit(1)

for group in GROUPS:
    print(f"\n📂 [{group['name']}] 처리 중...")
    
    prev_dates = {}
    if os.path.exists(group['json_file']):
        try:
            with open(group['json_file'], 'r', encoding='utf-8') as f:
                for char in json.load(f).get('characters', []):
                    if char.get('congrats_date'): prev_dates[char['name']] = char['congrats_date']
        except: pass

    local_names = []
    if os.path.exists(group['txt_file']):
        with open(group['txt_file'], 'r', encoding='utf-8') as f:
            local_names = [line.strip() for line in f if line.strip()]
    
    base_names = list(set(local_names + get_google_sheet_names(group['sheet_url'])))
    final_search_list = set(base_names)
    
    print(f"   🔍 원정대 확인 중...")
    for name in base_names:
        for s in get_siblings(name): final_search_list.add(s)
        time.sleep(0.5)

    results = []
    for i, name in enumerate(final_search_list):
        print(f"[{i+1}/{len(final_search_list)}] {name}...", end=" ")
        data = get_character_data(name)
        
        if data:
            profile = data.get('ArmoryProfile', {})
            item_level = profile.get('ItemMaxLevel') or profile.get('ItemAvgLevel', '0.00')
            
            # 1. 공격력 (Attack Power) 찾기 - 큰 숫자
            attack_power = '0'
            for stat in profile.get('Stats', []):
                if stat.get('Type') == '공격력':
                    attack_power = stat.get('Value', '0')
                    break
            
            # 2. 전투력 (Combat Power) 찾기 - 작은 숫자
            combat_power = profile.get('CombatPower', '0')
            
            # 축하 날짜 확인
            congrats_date = ""
            try:
                if float(item_level.replace(',', '')) >= 1700.0:
                    congrats_date = prev_dates.get(name, datetime.now().strftime("%Y-%m-%d"))
            except: pass

            results.append({
                "name": name,
                "job": profile.get('CharacterClassName', '정보없음'),
                "img": profile.get('CharacterImage', ''),
                "itemLevel": item_level,
                "attackPower": attack_power,   # 공격력 저장
                "combatPower": combat_power,   # 전투력 저장
                "congrats_date": congrats_date
            })
            print(f"✅")
        else:
            print("❌")
        time.sleep(0.1)

    with open(group['json_file'], 'w', encoding='utf-8') as f:
        json.dump({"updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "characters": results}, f, ensure_ascii=False, indent=2)
    print("저장 완료.")
