from flask import Flask, request, jsonify
from flask_cors import CORS
from music_select import BalancedRatioRecommender, EmotionTag, ActivityTag, Weather
import requests

app = Flask(__name__)
CORS(app)
recommender = BalancedRatioRecommender()

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    print("[FLASK] 🔍 요청 데이터:", data, flush=True)

    # 1. Enum으로 변환
    emotion = EmotionTag[data['emotion'].upper()]
    activity = ActivityTag[data['activity'].upper()]
    weather = Weather[data['weather'].upper()]

    # 2. 추천 수행
    result = recommender.recommend_music(emotion, activity, weather)
    analysis = recommender.get_detailed_analysis(result)

    # 3. Jamendo API 호출
    base_url = "https://api.jamendo.com/v3.0/tracks/"
    client_id = "602b9767"  # 실제 Client ID
    query_string = "&".join([f"{key}={value}" for key, value in result.api_params.items()])
    full_url = f"{base_url}?client_id={client_id}&{query_string}"

    print(f"[FLASK] 🔗 Jamendo API 요청 URL:\n{full_url}\n", flush=True)

    try:
        response = requests.get(full_url)
        response.raise_for_status()
        jamendo_data = response.json()

        if jamendo_data['headers']['status'] == 'success':
            tracks = jamendo_data['results']
        else:
            tracks = []

    except Exception as e:
        print(f"[FLASK] ❌ Jamendo API 호출 실패: {e}", flush=True)
        tracks = []

    # 4. 클라이언트로 전송
    return jsonify({
        "analysis": analysis,
        "tracks": tracks  # 최대 20곡
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
