import requests
import os
from datetime import datetime

# 1. API 키 가져오기 및 안전장치 (Bearer 글자 자동 제거)
RAW_API_KEY = os.environ.get('LOA_API_KEY', '')
API_KEY = RAW_API_KEY.replace("Bearer ", "").replace("bearer ", "").strip()

# 닉네임 리스트
NICKNAMES = [
    "베이비블러쉬", "삼동서머너", "씩씩", "레닌저생화학", "본과호소인", "부추쨩",
    "매일좋은날", "에겐남다다규", "하니쿠", "브레이커쥬니", "서냥이용", "오함마의유혹",
    "븜구리빵", "쏠쏠한포인트", "유산떡락기원", "조선명기", "프리아포스",
    "핑뚝이환수사", "기립", "이핼", "리핼",
    "기상학과추상우", "아가일도",
    "강기석", "미니멀건랜스", "방패쓰는뽈세밍", "뎀딜스커", "태티트",
    "AB시디", "명동성당촛대도둑", "빗나감군단장", "양호시", "독립기념일",
    "간지버거", "탑땡구", "뚜바비뷰", "지금기상해서술사", "한적한흔적",
    "종말의날은영어로떼바...", "주지육림", "최고의스펠뮤트올", "카레이쏭", "헤롱콩",
    "슉슈슉금잼칠", "힐러태연", "공대남", "그형의몽둥이", "낫뜨거워",
    "밤꽃향기나는그녀", "선우현", "절구슬", "노량진게이"
]

# 에러 진단을 위한 로그 저장소
debug_logs = []

def get_info(nickname):
    if not nickname or nickname.endswith("..."):
        return None
    
    encoded_name = requests.utils.quote(nickname)
    url = f'https://developer-lostark.game.onstove.com/armories/characters/{encoded_name}/profiles'
    headers = {'accept': 'application/json', 'authorization': f'bearer {API_KEY}'}
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data:
                attack_power = "-"
                if 'Stats' in data:
                    for stat in data['Stats']:
                        if stat['Type'] == "공격력":
                            attack_power = stat['Value']
                            break
                
                img_url = data.get('CharacterImage')
                if not img_url:
                    img_url = "https://cdn-lostark.game.onstove.com/2018/obt/assets/images/common/thumb/default_profile.png"

                return {
                    'name': nickname,
                    'class': data['CharacterClassName'],
                    'level': float(data['ItemMaxLevel'].replace(',', '')),
                    'atk': attack_power,
                    'img': img_url
                }
            else:
                debug_logs.append(f"❌ {nickname}: 캐릭터 정보 없음 (null 반환)")
        elif res.status_code == 401:
            debug_logs.append(f"🔒 {nickname}: 인증 실패 (401) - API 키가 틀렸습니다.")
        else:
            debug_logs.append(f"⚠️ {nickname}: 서버 오류 ({res.status_code})")
            
    except Exception as e:
        debug_logs.append(f"💥 {nickname}: 프로그램 에러 - {str(e)}")
    return None

def main():
    if not API_KEY:
        error_msg = "🚫 치명적 오류: API 키가 없습니다. Settings > Secrets를 확인하세요."
        print(error_msg)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"<h1>{error_msg}</h1>")
        return

    results = []
    print(f"--- 조회 시작 ({len(NICKNAMES)}명) ---")
    
    for name in NICKNAMES:
        info = get_info(name)
        if info: 
            results.append(info)
    
    # 🚨 만약 결과가 하나도 없다면 -> 진단 모드 화면 출력
    if len(results) == 0:
        print("결과가 0개여서 진단 리포트를 생성합니다.")
        log_html = "<br>".join(debug_logs[:10]) # 최대 10개까지만 표시
        
        html = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <body style="background-color: #222; color: white; padding: 20px; font-family: sans-serif;">
            <h1 style="color: #ff6b6b;">⚠️ 데이터 조회 실패</h1>
            <p>서버 배경색은 바뀌었지만, 캐릭터 데이터를 가져오지 못했습니다.</p>
            <div style="background: #333; padding: 15px; border-radius: 10px;">
                <h3>🔍 실패 원인 분석 로그:</h3>
                <p>{log_html}</p>
                <p>...</p>
            </div>
            <h3 style="margin-top:20px;">💡 해결 방법:</h3>
            <ul>
                <li>로그에 <b>'401'</b>이 뜬다면: API 키가 잘못된 것입니다. Secrets에서 키를 다시 등록하세요.</li>
                <li>로그에 <b>'null'</b>이 뜬다면: 닉네임이 실제 게임에 없는 이름입니다.</li>
            </ul>
        </body>
        </html>
        """
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html)
        return

    # 정상일 경우 기존 로직 수행
    results.sort(key=lambda x: x['level'], reverse=True)

    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>로스트아크 놀자에요 랭킹</title>
        <style>
            body {{
                font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
                background-color: #121214;
                color: #e0e0e0;
                display: flex;
                justify-content: center;
                padding: 20px;
                margin: 0;
            }}
            .container {{
                max-width: 900px;
                width: 100%;
                background-color: #1e1e20;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 8px 16px rgba(0,0,0,0.5);
            }}
            h2 {{ text-align: center; color: #ffca5c; margin-bottom: 20px; }}
            .rank-row {{
                display: flex;
                align-items: center;
                background-color: #2a2a2e;
                margin-bottom: 10px;
                padding: 10px 20px;
                border-radius: 8px;
                border: 1px solid #3a3a40;
                transition: 0.2s;
            }}
            .rank-row:hover {{ background-color: #35353a; transform: translateY(-2px); }}
            .rank-num {{ width: 40px; font-size: 1.2em; font-weight: bold; color: #888; text-align: center; }}
            .rank-1 {{ color: #ffd700; }} .rank-2 {{ color: #c0c0c0; }} .rank-3 {{ color: #cd7f32; }}
            .char-img {{ width: 50px; height: 50px; border-radius: 50%; border: 2px solid #555; object-fit: cover; margin: 0 20px; background: #000; }}
            .char-info {{ flex-grow: 1; }}
            .char-name {{ font-size: 1.1em; font-weight: bold; color: #fff; }}
            .char-class {{ font-size: 0.85em; color: #aaa; margin-top: 2px; }}
            .stat-box {{ width: 100px; text-align: right; margin-left: 10px; }}
            .stat-label {{ font-size: 0.75em; color: #777; display: block; }}
            .stat-value {{ font-size: 1.1em; font-weight: bold; }}
            .level-val {{ color: #00d1ce; }}
            .atk-val {{ color: #ff6b6b; }}
            .update-time {{ text-align: center; font-size: 0.8em; color: #555; margin-top: 20px; }}
            @media (max-width: 600px) {{
                .rank-row {{ flex-wrap: wrap; padding: 15px; }}
                .char-img {{ width: 40px; height: 40px; margin: 0 10px; }}
                .stat-box {{ width: 45%; margin: 10px 0 0 0; text-align: left; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🏆 놀자에요 전투력 측정기</h2>
            <div class="list-area">
    """
    
    for i, char in enumerate(results, 1):
        rank_class = f"rank-{i}" if i <= 3 else ""
        html += f"""
            <div class="rank-row">
                <div class="rank-num {rank_class}">{i}</div>
                <img src="{char['img']}" class="char-img" alt="img">
                <div class="char-info">
                    <div class="char-name">{char['name']}</div>
                    <div class="char-class">{char['class']}</div>
                </div>
                <div class="stat-box">
                    <span class="stat-label">아이템 레벨</span>
                    <div class="stat-value level-val">{char['level']:,.2f}</div>
                </div>
                <div class="stat-box">
                    <span class="stat-label">공격력</span>
                    <div class="stat-value atk-val">{char['atk']}</div>
                </div>
            </div>
        """
    
    html += f"""
            </div>
            <div class="update-time">마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
