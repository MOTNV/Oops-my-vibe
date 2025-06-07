from flask import Flask, request, jsonify
from flask_cors import CORS
from music_select import BalancedRatioRecommender, EmotionTag, ActivityTag, Weather

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

    # 2. 추천 수행
    result = recommender.recommend_music(emotion, activity, weather)

    # 3. 리포트 출력
    print(f"[FLASK] ✅ 추천 결과 파라미터: {result.api_params}", flush=True)

    print("\n[FLASK] 🎲 추천 분석 리포트 ↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓", flush=True)
    analysis = recommender.get_detailed_analysis(result)
    print(analysis, flush=True)
    print("[FLASK] 🔚 리포트 끝 ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑", flush=True)

    # 4. ✅ Jamendo API URL 생성 및 출력
    base_url = "https://api.jamendo.com/v3.0/tracks/"
    client_id = "602b9767"  # 클라이언트 ID (테스트용 또는 실제 사용용)
    query_string = "&".join([f"{key}={value}" for key, value in result.api_params.items()])
    full_url = f"{base_url}?client_id={client_id}&{query_string}"

    print(f"[FLASK] 🔗 생성된 Jamendo API URL:\n{full_url}\n", flush=True)

    return jsonify(result.api_params)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
