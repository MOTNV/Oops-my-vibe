from flask import Flask, request, jsonify
from flask_cors import CORS
from music_select import BalancedRatioRecommender, EmotionTag, ActivityTag, Weather
import requests
import random

app = Flask(__name__)
CORS(app)
recommender = BalancedRatioRecommender()

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    print("[FLASK] 🔍 요청 데이터:", data, flush=True)

    # 1. 사용자 선택값 Enum으로 변환
    emotion = EmotionTag[data['emotion'].upper()]
    activity = ActivityTag[data['activity'].upper()]
    weather = Weather[data['weather'].upper()]

    print(f"[FLASK] 🎭 감정: {emotion}, ⚙️ 활동: {activity}, 🌤️ 날씨: {weather}", flush=True)

    # 2. 추천 수행 (파라미터만 생성)
    result = recommender.recommend_music(emotion, activity, weather)

    if not result:
        print("[FLASK] ❌ 추천 실패", flush=True)
        return jsonify({'error': '추천 실패'}), 500

    # 3. 리포트 출력
    print(f"[FLASK] ✅ 추천 결과 파라미터: {result.api_params}", flush=True)
    print("\n[FLASK] 🎲 추천 분석 리포트 ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓", flush=True)
    analysis = recommender.get_detailed_analysis(result)
    print(analysis, flush=True)
    print("[FLASK] 🔚 리포트 끝 ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑", flush=True)

    # 4. Jamendo API URL 생성
    base_url = "https://api.jamendo.com/v3.0/tracks/"
    client_id = "602b9767"
    query_string = "&".join(f"{k}={v}" for k, v in result.api_params.items())
    full_url = f"{base_url}?client_id={client_id}&{query_string}"
    print(f"[FLASK] 🔗 Jamendo 요청 URL:\n{full_url}\n", flush=True)

    # 5. 서버에서 직접 API 호출 → 트랙 리스트 받아오기
    try:
        resp = requests.get(full_url)
        if resp.status_code != 200:
            print("[FLASK] ❌ Jamendo API 요청 실패:", resp.text, flush=True)
            return jsonify({'error': 'API 요청 실패'}), 502

        data = resp.json()
        tracks = data.get('results', [])
        print(f"[FLASK] 🎵 받아온 트랙 수: {len(tracks)}", flush=True)

        # 6. 랜덤 섞어서 20개만 추출
        random.shuffle(tracks)
        selected = tracks[:20]
        print(f"[FLASK] ✅ 최종 추천할 음악 수: {len(selected)}", flush=True)

        # 🔊 추천 곡 리스트를 보기 좋게 터미널에 출력
        print("\n🎲 추천 곡 리스트 ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓\n", flush=True)
        for idx, track in enumerate(selected[:10], 1):
            print(f"{idx:2d}. 🎵 {track['name']}", flush=True)
            print(f"    👤 아티스트: {track['artist_name']}", flush=True)
            print(f"    ⏱️  길이: {track['duration']}초", flush=True)
            print(f"    🎧 듣기: {track['audio']}\n", flush=True)
            if idx == 5:
                print("    " + "-" * 40, flush=True)
        print("🎲 추천 곡 리스트 ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑\n", flush=True)

        # 7. 최종 JSON 반환
        return jsonify({
            'api_params': result.api_params,
            'analysis': analysis,
            'tracks': selected
        })

    except Exception as e:
        print("[FLASK] ❗예외 발생:", e, flush=True)
        return jsonify({'error': '서버 내부 오류'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
