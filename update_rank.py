import requests
import os
from datetime import datetime

# 깃허브 Secret에서 키를 가져옴
API_KEY = os.environ.get('LOA_API_KEY')

# 추출한 닉네임 리스트 (서버명 제거됨)
NICKNAMES = [
    # 이미지 1
    "베이비블러쉬", "삼동서머너", "씩씩", "레닌저생화학", "본과호소인", "부추쨩",
    # 이미지 2
    "매일좋은날", "에겐남다다규", "하니쿠", "브레이커쥬니", "서냥이용", "오함마의유혹",
    # 이미지 3
    "븜구리빵", "쏠쏠한포인트", "유산떡락기원", "조선명기", "프리아포스",
    # 이미지 4
    "핑뚝이환수사", "기립", "이핼", "리핼",
    # 이미지 5
    "기상학과추상우", "아가일도",
    # 이미지 6
    "강기석", "미니멀건랜스", "방패쓰는뽈세밍", "뎀딜스커", "태티트",
    # 이미지 7
    "AB시디", "명동성당촛대도둑", "빗나감군단장", "양호시", "독립기념일",
    # 이미지 8
    "간지버거", "탑땡구", "뚜바비뷰", "지금기상해서술사", "한적한흔적",
    # 이미지 9 (주의: 첫 번째 닉네임 확인 필요)
    "종말의날은영어로떼바시", "주지육림", "최고의스펠뮤트올", "카레이쏭", "헤롱콩",
    # 이미지 10
    "슉슈슉금잼칠", "힐러태연", "공대남", "그형의몽둥이", "낫뜨거워",
    # 이미지 11
    "밤꽃향기나는그녀", "선우현", "절구슬", "노량진게이"
]

def get_info(nickname):
    # 이름이 ...으로 끝나거나 비어있으면 건너뜀
    if not nickname or nickname.endswith("..."):
        return None
        
    url = f'https://developer-lostark.game.onstove.com/armories/characters/{nickname}/profiles'
    headers = {'accept': 'application/json', 'authorization': f'bearer {API_KEY}'}
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            data = res.json()
            if data:
                return {
                    'name': nickname,
                    'class': data['CharacterClassName'],
                    'level': float(data['ItemMaxLevel'].replace(',', ''))
                }
    except:
        pass
    return None

def main():
    results = []
    print(f"총 {len(NICKNAMES)}명의 정보를 조회합니다...")
    
    for name in NICKNAMES:
        info = get_info(name)
        if info: 
            results.append(info)
        else:
            print(f"실패/제외: {name}")
    
    # 레벨 내림차순 정렬
    results.sort(key=lambda x: x['level'], reverse=True)

    # HTML 파일 생성
    html = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>로스트아크 산책회 랭킹</title>
        <style>
            body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background-color: #f0f2f5; display: flex; justify-content: center; padding: 20px; }}
            .container {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 600px; width: 100%; }}
            h2 {{ text-align: center; color: #333; margin-bottom: 20px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background-color: #4c5c68; color: white; padding: 12px; font-weight: bold; }}
            td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: center; color: #333; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr:hover {{ background-color: #f1f1f1; }}
            .rank {{ font-weight: bold; color: #1e3a8a; }}
            .level {{ font-weight: bold; color: #d97706; }}
            .update-time {{ text-align: center; font-size: 0.8em; color: #888; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🏆 로스트아크 레벨 랭킹</h2>
            <table>
                <thead>
                    <tr>
                        <th width="15%">순위</th>
                        <th>닉네임</th>
                        <th width="20%">직업</th>
                        <th width="25%">아이템 레벨</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for i, char in enumerate(results, 1):
        # 상위 3등까지는 왕관 아이콘 표시 (재미 요소)
        rank_display = str(i)
        if i == 1: rank_display = "🥇"
        elif i == 2: rank_display = "🥈"
        elif i == 3: rank_display = "🥉"

        html += f"""
                    <tr>
                        <td class="rank">{rank_display}</td>
                        <td>{char['name']}</td>
                        <td>{char['class']}</td>
                        <td class="level">{char['level']:,.2f}</td>
                    </tr>"""
    
    html += f"""
                </tbody>
            </table>
            <div class="update-time">
                마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
    </body>
    </html>
    """

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML 생성 완료!")

if __name__ == "__main__":
    main()
