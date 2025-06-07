import json
import requests
import random
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class Weather(Enum):
    SUNNY = "sunny"
    CLOUDY = "cloudy" 
    RAINY = "rainy"
    SNOWY = "snowy"
    WINDY = "windy"

class TimeOfDay(Enum):
    DAWN = "dawn"      # 04:00-06:59
    MORNING = "morning"  # 07:00-11:59
    AFTERNOON = "afternoon"  # 12:00-17:59
    EVENING = "evening"  # 18:00-21:59
    NIGHT = "night"    # 22:00-03:59

class EmotionTag(Enum):
    HAPPY = "happy"
    SAD = "sad"
    CALM = "calm"
    ENERGETIC = "energetic"
    ROMANTIC = "romantic"
    STRESSED = "stressed"
    MELANCHOLIC = "melancholic"
    PEACEFUL = "peaceful"
    UPLIFTING = "uplifting"
    DRAMATIC = "dramatic"

class ActivityTag(Enum):
    WORK = "work"
    STUDY = "study"
    EXERCISE = "exercise"
    RELAXATION = "relaxation"
    PARTY = "party"
    MEDITATION = "meditation"
    COMMUTE = "commute"
    SLEEP = "sleep"
    FOCUS = "focus"
    SOCIAL = "social"

@dataclass
class MusicScenario:
    """음악 시나리오 (감정+활동 조합)"""
    name: str
    emoji: str
    description: str
    emotion: EmotionTag
    activity: ActivityTag
    keywords: List[str]  # 검색용 키워드

@dataclass
class RatioBreakdown:
    """반영 비율 상세 분석"""
    parameter: str
    emotion_contribution: float  # 감정 기여도
    weather_contribution: float  # 날씨 기여도
    time_contribution: float     # 시간 기여도
    final_value: str
    calculation_detail: str

@dataclass
class RecommendationScore:
    """추천 점수와 이유를 담는 클래스"""
    parameter: str
    value: str
    emotion_score: float      # 감정 점수 (0-1)
    weather_score: float      # 날씨 점수 (0-1) 
    time_score: float         # 시간 점수 (0-1)
    final_score: float        # 최종 점수
    reasoning: str

@dataclass
class MusicRecommendation:
    """최종 추천 결과"""
    api_params: Dict[str, str]
    explanation: List[RecommendationScore]
    ratio_breakdown: List[RatioBreakdown]
    total_confidence: float

class BalancedRatioRecommender:
    def __init__(self):
        # 🎯 핵심 반영 비율 설정 (고정)
        self.EMOTION_RATIO = 0.5   # 50%
        self.WEATHER_RATIO = 0.3   # 30%  
        self.TIME_RATIO = 0.2      # 20%
        
        # ✅ 감정별 기본 특성 (실제 지원되는 태그들로 수정)
        self.emotion_characteristics = {
            EmotionTag.HAPPY: {
                "energy": 0.7, "valence": 0.8, "arousal": 0.6,
                "speed": 0.7, "tags": ["happy", "uplifting", "energetic", "pop"]
            },
            EmotionTag.SAD: {
                "energy": 0.3, "valence": 0.2, "arousal": 0.3,
                "speed": 0.3, "tags": ["melancholic", "emotional", "peaceful", "classical"]
            },
            EmotionTag.CALM: {
                "energy": 0.2, "valence": 0.6, "arousal": 0.2,
                "speed": 0.3, "tags": ["peaceful", "relaxing", "ambient", "meditation"]
            },
            EmotionTag.ENERGETIC: {
                "energy": 0.9, "valence": 0.7, "arousal": 0.9,
                "speed": 0.8, "tags": ["energetic", "electronic", "rock", "motivational"]
            },
            EmotionTag.ROMANTIC: {
                "energy": 0.4, "valence": 0.7, "arousal": 0.5,
                "speed": 0.4, "tags": ["romantic", "jazz", "acoustic", "soft"]
            },
            EmotionTag.STRESSED: {
                "energy": 0.1, "valence": 0.3, "arousal": 0.7,
                "speed": 0.2, "tags": ["peaceful", "ambient", "relaxing", "healing"]
            },
            EmotionTag.MELANCHOLIC: {
                "energy": 0.3, "valence": 0.2, "arousal": 0.4,
                "speed": 0.3, "tags": ["melancholic", "classical", "emotional", "ambient"]
            },
            EmotionTag.PEACEFUL: {
                "energy": 0.2, "valence": 0.6, "arousal": 0.1,
                "speed": 0.3, "tags": ["peaceful", "ambient", "meditation", "nature"]
            },
            EmotionTag.UPLIFTING: {
                "energy": 0.6, "valence": 0.8, "arousal": 0.6,
                "speed": 0.6, "tags": ["uplifting", "motivational", "pop", "electronic"]
            },
            EmotionTag.DRAMATIC: {
                "energy": 0.8, "valence": 0.5, "arousal": 0.8,
                "speed": 0.7, "tags": ["cinematic", "orchestral", "classical", "soundtrack"]
            }
        }
        
        # 활동별 보정값 (감정에 추가로 적용)
        self.activity_adjustments = {
            ActivityTag.WORK: {"energy": -0.1, "speed": 0.0, "vocal": "instrumental"},
            ActivityTag.STUDY: {"energy": -0.2, "speed": -0.1, "vocal": "instrumental"},
            ActivityTag.EXERCISE: {"energy": 0.2, "speed": 0.2, "vocal": "vocal"},
            ActivityTag.RELAXATION: {"energy": -0.3, "speed": -0.2, "vocal": "instrumental"},
            ActivityTag.PARTY: {"energy": 0.3, "speed": 0.3, "vocal": "vocal"},
            ActivityTag.MEDITATION: {"energy": -0.4, "speed": -0.3, "vocal": "instrumental"},
            ActivityTag.COMMUTE: {"energy": 0.0, "speed": 0.1, "vocal": "vocal"},
            ActivityTag.SLEEP: {"energy": -0.4, "speed": -0.4, "vocal": "instrumental"},
            ActivityTag.FOCUS: {"energy": -0.1, "speed": 0.0, "vocal": "instrumental"},
            ActivityTag.SOCIAL: {"energy": 0.1, "speed": 0.1, "vocal": "vocal"}
        }
        
        # 날씨별 영향 (0-1 범위)
        self.weather_influences = {
            Weather.SUNNY: {"energy": 0.8, "valence": 0.9, "speed": 0.7},
            Weather.RAINY: {"energy": 0.3, "valence": 0.4, "speed": 0.3},
            Weather.CLOUDY: {"energy": 0.5, "valence": 0.5, "speed": 0.5},
            Weather.SNOWY: {"energy": 0.4, "valence": 0.6, "speed": 0.4},
            Weather.WINDY: {"energy": 0.7, "valence": 0.6, "speed": 0.6}
        }
        
        # 시간대별 영향 (0-1 범위)
        self.time_influences = {
            TimeOfDay.DAWN: {"energy": 0.2, "valence": 0.5, "speed": 0.2},
            TimeOfDay.MORNING: {"energy": 0.7, "valence": 0.8, "speed": 0.6},
            TimeOfDay.AFTERNOON: {"energy": 0.6, "valence": 0.6, "speed": 0.6},
            TimeOfDay.EVENING: {"energy": 0.4, "valence": 0.6, "speed": 0.4},
            TimeOfDay.NIGHT: {"energy": 0.3, "valence": 0.5, "speed": 0.3}
        }
        
        # ✅ 속도 매핑 (실제 지원되는 값들만)
        self.speed_mapping = {
            "medium": 0, "high": 1, "veryhigh": 2
        }
        self.speed_reverse = {v: k for k, v in self.speed_mapping.items()}
        
        # 🎲 랜덤 추천을 위한 정렬 옵션들 (실제 지원되는 값들만)
        self.random_orders = [
            "releasedate",          # 발매일순
            "popularity_week",      # 주간 인기
            "popularity_month",     # 월간 인기
            "popularity_total",     # 전체 인기
            "downloads_week",       # 주간 다운로드
            "downloads_month",      # 월간 다운로드
            "downloads_total",      # 전체 다운로드
            "listens_week",         # 주간 청취
            "listens_month",        # 월간 청취
            "listens_total",        # 전체 청취
            "name",                 # 제목순
            "artist_name",          # 아티스트명순
            "album_name",           # 앨범명순
            "duration",             # 길이순
            "buzzrate",             # 버즈레이트
            "relevance"             # 관련도순
        ]

    def get_time_of_day(self, hour: int) -> TimeOfDay:
        """시간을 기반으로 시간대 결정"""
        if 4 <= hour < 7:
            return TimeOfDay.DAWN
        elif 7 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 18:
            return TimeOfDay.AFTERNOON
        elif 18 <= hour < 22:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT

    def calculate_balanced_score(self, emotion: EmotionTag, weather: Weather, 
                               time_of_day: TimeOfDay, attribute: str) -> Tuple[float, str]:
        """50%-30%-20% 비율로 균형잡힌 점수 계산"""
        
        # 1. 감정 점수 (0-1)
        emotion_score = self.emotion_characteristics[emotion][attribute]
        
        # 2. 날씨 점수 (0-1)
        weather_score = self.weather_influences[weather][attribute]
        
        # 3. 시간 점수 (0-1)
        time_score = self.time_influences[time_of_day][attribute]
        
        # 4. 🎯 정확한 비율 적용
        final_score = (
            emotion_score * self.EMOTION_RATIO +      # 50%
            weather_score * self.WEATHER_RATIO +      # 30%
            time_score * self.TIME_RATIO              # 20%
        )
        
        # 5. 계산 과정 상세 설명
        calculation_detail = (
            f"{emotion_score:.2f}×{self.EMOTION_RATIO} + "
            f"{weather_score:.2f}×{self.WEATHER_RATIO} + "
            f"{time_score:.2f}×{self.TIME_RATIO} = {final_score:.2f}"
        )
        
        return final_score, calculation_detail

    def calculate_comprehensive_characteristics(self, emotion: EmotionTag, activity: ActivityTag,
                                             weather: Weather, time_of_day: TimeOfDay) -> Dict:
        """모든 특성을 균형잡힌 비율로 계산"""
        
        results = {}
        
        # 핵심 속성들 계산
        for attribute in ["energy", "speed"]:
            score, detail = self.calculate_balanced_score(emotion, weather, time_of_day, attribute)
            
            # 활동별 미세 조정 (±10% 범위)
            activity_adj = self.activity_adjustments[activity].get(attribute, 0) * 0.1
            adjusted_score = max(0.0, min(1.0, score + activity_adj))
            
            results[attribute] = {
                "base_score": score,
                "activity_adjustment": activity_adj,
                "final_score": adjusted_score,
                "calculation": detail
            }
        
        # 태그 조합
        emotion_tags = self.emotion_characteristics[emotion]["tags"]
        results["tags"] = emotion_tags
        
        # 보컬 선택 (활동 우선)
        results["vocal"] = self.activity_adjustments[activity]["vocal"]
        
        return results

    def select_optimal_tags_with_ratio(self, emotion: EmotionTag, weather: Weather, 
                                     time_of_day: TimeOfDay, base_tags: List[str]) -> List[Tuple[str, float]]:
        """태그별 50%-30%-20% 적합도 계산"""
        
        tag_scores = []
        
        for tag in base_tags:
            # 감정 적합도 (기본 1.0, 해당 감정의 태그이므로)
            emotion_fit = 1.0
            
            # 날씨 적합도 계산
            weather_fit = self.calculate_weather_tag_fit(tag, weather)
            
            # 시간대 적합도 계산  
            time_fit = self.calculate_time_tag_fit(tag, time_of_day)
            
            # 🎯 정확한 비율 적용
            final_fit = (
                emotion_fit * self.EMOTION_RATIO +    # 50%
                weather_fit * self.WEATHER_RATIO +    # 30%
                time_fit * self.TIME_RATIO            # 20%
            )
            
            tag_scores.append((tag, final_fit))
        
        # 점수 순으로 정렬
        tag_scores.sort(key=lambda x: x[1], reverse=True)
        return tag_scores[:2]  # 상위 2개만 (더 관대하게)

    def calculate_weather_tag_fit(self, tag: str, weather: Weather) -> float:
        """날씨와 태그의 적합도 (0-1) - 실제 지원되는 태그들로 업데이트"""
        weather_tag_map = {
            Weather.SUNNY: {
                "uplifting": 0.9, "happy": 0.9, "energetic": 0.8, "pop": 0.8,
                "electronic": 0.7, "motivational": 0.8, "melancholic": 0.2
            },
            Weather.RAINY: {
                "peaceful": 0.9, "ambient": 0.8, "melancholic": 0.8, "romantic": 0.7,
                "classical": 0.7, "jazz": 0.8, "energetic": 0.3, "rock": 0.2
            },
            Weather.CLOUDY: {
                "ambient": 0.7, "peaceful": 0.7, "jazz": 0.6, "classical": 0.6,
                "electronic": 0.4, "rock": 0.4
            },
            Weather.SNOWY: {
                "peaceful": 0.9, "ambient": 0.8, "classical": 0.8, "meditation": 0.8,
                "jazz": 0.7, "energetic": 0.3, "rock": 0.3
            },
            Weather.WINDY: {
                "electronic": 0.8, "energetic": 0.7, "rock": 0.8, "cinematic": 0.7,
                "peaceful": 0.4, "ambient": 0.3
            }
        }
        
        return weather_tag_map.get(weather, {}).get(tag, 0.5)  # 기본값 0.5

    def calculate_time_tag_fit(self, tag: str, time_of_day: TimeOfDay) -> float:
        """시간대와 태그의 적합도 (0-1) - 실제 지원되는 태그들로 업데이트"""
        time_tag_map = {
            TimeOfDay.DAWN: {
                "peaceful": 1.0, "ambient": 0.9, "meditation": 0.9, "nature": 0.8,
                "classical": 0.8, "energetic": 0.1, "rock": 0.1, "electronic": 0.2
            },
            TimeOfDay.MORNING: {
                "energetic": 0.9, "uplifting": 0.9, "motivational": 0.8, "pop": 0.8,
                "electronic": 0.7, "jazz": 0.6, "melancholic": 0.3
            },
            TimeOfDay.AFTERNOON: {
                "pop": 0.8, "rock": 0.7, "energetic": 0.6, "electronic": 0.6,
                "jazz": 0.6, "ambient": 0.5, "cinematic": 0.4
            },
            TimeOfDay.EVENING: {
                "romantic": 0.9, "jazz": 0.8, "classical": 0.7, "ambient": 0.7,
                "acoustic": 0.8, "soft": 0.7, "energetic": 0.4, "rock": 0.3
            },
            TimeOfDay.NIGHT: {
                "peaceful": 0.9, "ambient": 0.9, "meditation": 0.8, "classical": 0.8,
                "jazz": 0.7, "healing": 0.9, "energetic": 0.2, "rock": 0.2
            }
        }
        
        return time_tag_map.get(time_of_day, {}).get(tag, 0.5)  # 기본값 0.5

    def recommend_music(self, emotion: EmotionTag, activity: ActivityTag,
                       weather: Weather, time_of_day: Optional[TimeOfDay] = None,
                       randomize: bool = True) -> MusicRecommendation:
        """50%-30%-20% 비율 기반 랜덤 추천"""
        
        if time_of_day is None:
            current_hour = datetime.now().hour
            time_of_day = self.get_time_of_day(current_hour)
        
        # 1. 전체 특성 계산
        characteristics = self.calculate_comprehensive_characteristics(
            emotion, activity, weather, time_of_day
        )
        
        # 2. 태그 선택 (50%-30%-20% 비율 적용) - 더 관대하게
        base_tags = characteristics["tags"]
        selected_tags_with_scores = self.select_optimal_tags_with_ratio(
            emotion, weather, time_of_day, base_tags
        )
        # 태그 수를 1-2개로 제한 (더 관대한 검색)
        selected_tags = [tag for tag, score in selected_tags_with_scores[:2]]
        
        # 3. ✅ 속도 결정 (실제 지원되는 값들만 사용)
        speed_score = characteristics["speed"]["final_score"]
        # 0-1 점수를 0-2 범위로 변환 (medium=0, high=1, veryhigh=2)
        speed_numeric = min(2, round(speed_score * 2))
        primary_speed = self.speed_reverse[speed_numeric]
        
        # 4. 🎲 랜덤 파라미터 추가
        random_params = {}
        if randomize:
            # 랜덤 정렬 방식 선택
            random_order = random.choice(self.random_orders)
            random_params["order"] = random_order
            
            # 랜덤 오프셋 (0-500 범위에서)
            random_offset = random.randint(0, 500)
            random_params["offset"] = str(random_offset)
            
            # 결과 수를 조금 더 많이 가져와서 나중에 섞기
            random_params["limit"] = "50"
        
        # 5. ✅ API 파라미터 구성 (더 관대한 설정)
        api_params = {
            "fuzzytags": "+".join(selected_tags),  # ✅ 1-2개 태그만
            "speed": primary_speed,  # ✅ 단일 속도만 사용
            "vocalinstrumental": characteristics["vocal"],  # ✅ 올바른 값들
            "limit": "20",
            "include": "musicinfo",
            # featured는 제거 - 더 많은 결과를 위해
            "format": "json"  # ✅ 명시적으로 추가
        }
        
        # 랜덤 파라미터 추가
        if randomize:
            api_params.update(random_params)
            api_params["limit"] = "20"  # 최종적으로는 20개만
        
        # 6. 상세 설명 생성 (기존과 동일)
        explanations = []
        ratio_breakdowns = []
        
        # 태그 설명
        for i, (tag, score) in enumerate(selected_tags_with_scores):
            emotion_contrib = 1.0 * self.EMOTION_RATIO
            weather_contrib = self.calculate_weather_tag_fit(tag, weather) * self.WEATHER_RATIO
            time_contrib = self.calculate_time_tag_fit(tag, time_of_day) * self.TIME_RATIO
            
            explanations.append(RecommendationScore(
                parameter="tags",
                value=tag,
                emotion_score=1.0,
                weather_score=self.calculate_weather_tag_fit(tag, weather),
                time_score=self.calculate_time_tag_fit(tag, time_of_day),
                final_score=score,
                reasoning=f"'{tag}' 태그: 감정 {emotion_contrib:.1f} + 날씨 {weather_contrib:.1f} + 시간 {time_contrib:.1f} = {score:.2f}"
            ))
            
            ratio_breakdowns.append(RatioBreakdown(
                parameter=f"tag_{tag}",
                emotion_contribution=emotion_contrib,
                weather_contribution=weather_contrib,
                time_contribution=time_contrib,
                final_value=tag,
                calculation_detail=f"50%×1.0 + 30%×{self.calculate_weather_tag_fit(tag, weather):.1f} + 20%×{self.calculate_time_tag_fit(tag, time_of_day):.1f}"
            ))
        
        # 속도 설명
        speed_char = characteristics["speed"]
        
        explanations.append(RecommendationScore(
            parameter="speed",
            value=primary_speed,
            emotion_score=self.emotion_characteristics[emotion]["speed"],
            weather_score=self.weather_influences[weather]["speed"],
            time_score=self.time_influences[time_of_day]["speed"],
            final_score=speed_score,
            reasoning=f"속도: {speed_char['calculation']} + 활동조정({speed_char['activity_adjustment']:+.1f}) = {speed_score:.2f}"
        ))
        
        ratio_breakdowns.append(RatioBreakdown(
            parameter="speed",
            emotion_contribution=self.emotion_characteristics[emotion]["speed"] * self.EMOTION_RATIO,
            weather_contribution=self.weather_influences[weather]["speed"] * self.WEATHER_RATIO,
            time_contribution=self.time_influences[time_of_day]["speed"] * self.TIME_RATIO,
            final_value=primary_speed,
            calculation_detail=speed_char['calculation']
        ))
        
        # 7. 랜덤 설명 추가
        if randomize:
            explanations.append(RecommendationScore(
                parameter="randomization",
                value=f"정렬: {random_params.get('order', 'default')}, 오프셋: {random_params.get('offset', '0')}",
                emotion_score=0.0,
                weather_score=0.0,
                time_score=0.0,
                final_score=1.0,
                reasoning=f"🎲 랜덤 요소: {random_params.get('order')} 정렬 + {random_params.get('offset')} 위치부터 시작"
            ))
        
        # 8. 신뢰도 계산
        emotion_weight_achieved = sum(rb.emotion_contribution for rb in ratio_breakdowns) / len(ratio_breakdowns)
        weather_weight_achieved = sum(rb.weather_contribution for rb in ratio_breakdowns) / len(ratio_breakdowns)
        time_weight_achieved = sum(rb.time_contribution for rb in ratio_breakdowns) / len(ratio_breakdowns)
        
        emotion_accuracy = 1.0 - abs(emotion_weight_achieved - self.EMOTION_RATIO)
        weather_accuracy = 1.0 - abs(weather_weight_achieved - self.WEATHER_RATIO)
        time_accuracy = 1.0 - abs(time_weight_achieved - self.TIME_RATIO)
        
        confidence = (emotion_accuracy + weather_accuracy + time_accuracy) / 3 * 100
        
        return MusicRecommendation(
            api_params=api_params,
            explanation=explanations,
            ratio_breakdown=ratio_breakdowns,
            total_confidence=confidence
        )

    def get_detailed_analysis(self, recommendation: MusicRecommendation) -> str:
        """상세 분석 리포트 생성"""
        
        analysis = "🎲 랜덤 음악 추천 시스템 (감정 50% - 날씨 30% - 시간 20%)\n"
        analysis += "=" * 70 + "\n\n"
        
        # 실제 반영 비율 계산
        total_emotion = sum(rb.emotion_contribution for rb in recommendation.ratio_breakdown)
        total_weather = sum(rb.weather_contribution for rb in recommendation.ratio_breakdown)
        total_time = sum(rb.time_contribution for rb in recommendation.ratio_breakdown)
        total_sum = total_emotion + total_weather + total_time
        
        actual_emotion_ratio = (total_emotion / total_sum) * 100
        actual_weather_ratio = (total_weather / total_sum) * 100
        actual_time_ratio = (total_time / total_sum) * 100
        
        analysis += "📊 목표 vs 실제 반영 비율:\n"
        analysis += f"  🎭 감정: 50% 목표 → {actual_emotion_ratio:.1f}% 실제 ({actual_emotion_ratio-50:+.1f}%)\n"
        analysis += f"  🌤️ 날씨: 30% 목표 → {actual_weather_ratio:.1f}% 실제 ({actual_weather_ratio-30:+.1f}%)\n"
        analysis += f"  🕐 시간: 20% 목표 → {actual_time_ratio:.1f}% 실제 ({actual_time_ratio-20:+.1f}%)\n"
        analysis += f"  📈 정확도: {recommendation.total_confidence:.1f}%\n"
        analysis += f"  🎲 랜덤 모드: 항상 활성화\n"
        analysis += "\n"
        
        analysis += "🎵 선택된 파라미터:\n"
        for param, value in recommendation.api_params.items():
            if param not in ["limit", "include", "featured", "format"]:
                analysis += f"  • {param}: {value}\n"
        
        analysis += "\n🔍 파라미터별 상세 계산:\n"
        for breakdown in recommendation.ratio_breakdown:
            analysis += f"\n【{breakdown.parameter}】 = {breakdown.final_value}\n"
            analysis += f"  📊 기여도: 감정 {breakdown.emotion_contribution:.2f} + 날씨 {breakdown.weather_contribution:.2f} + 시간 {breakdown.time_contribution:.2f}\n"
            analysis += f"  🧮 계산식: {breakdown.calculation_detail}\n"
        
        return analysis

class UserInterface:
    """사용자 입력 인터페이스"""
    
    def __init__(self):
        self.recommender = BalancedRatioRecommender()
        self.scenarios = self.create_music_scenarios()
    
    def create_music_scenarios(self) -> List[MusicScenario]:
        """감정+활동 조합 시나리오 생성"""
        scenarios = [
            # 작업/공부 관련
            MusicScenario("집중해서 일할 때", "💼", "스트레스 받지만 집중이 필요한 업무", 
                         EmotionTag.STRESSED, ActivityTag.FOCUS, ["일", "업무", "집중", "작업"]),
            MusicScenario("편안하게 공부할 때", "📚", "차분한 마음으로 학습하기", 
                         EmotionTag.CALM, ActivityTag.STUDY, ["공부", "학습", "독서"]),
            MusicScenario("야근할 때", "🌙", "지쳤지만 계속 일해야 할 때", 
                         EmotionTag.STRESSED, ActivityTag.WORK, ["야근", "늦은", "지친"]),
            
            # 운동/활동 관련  
            MusicScenario("신나게 운동할 때", "🏃", "에너지 넘치는 상태로 운동하기", 
                         EmotionTag.ENERGETIC, ActivityTag.EXERCISE, ["운동", "헬스", "피트니스", "신나는"]),
            MusicScenario("행복한 아침 조깅", "🌅", "기분 좋은 아침에 가벼운 운동", 
                         EmotionTag.HAPPY, ActivityTag.EXERCISE, ["조깅", "아침", "달리기"]),
            MusicScenario("스트레스 풀러 운동", "💪", "화나거나 답답해서 운동으로 푸는", 
                         EmotionTag.STRESSED, ActivityTag.EXERCISE, ["스트레스", "화", "답답"]),
            
            # 휴식/치유 관련
            MusicScenario("힐링이 필요할 때", "🛋️", "마음의 평화가 필요한 휴식", 
                         EmotionTag.PEACEFUL, ActivityTag.RELAXATION, ["힐링", "치유", "평화", "휴식"]),
            MusicScenario("명상하며 마음 정리", "🧘", "깊은 사색과 명상을 위한", 
                         EmotionTag.CALM, ActivityTag.MEDITATION, ["명상", "요가", "사색"]),
            MusicScenario("우울할 때 혼자만의 시간", "😔", "슬픈 감정을 온전히 느끼며", 
                         EmotionTag.MELANCHOLIC, ActivityTag.RELAXATION, ["우울", "혼자", "슬픔"]),
            
            # 사교/파티 관련
            MusicScenario("친구들과 즐거운 파티", "🎉", "신나고 들뜬 파티 분위기", 
                         EmotionTag.HAPPY, ActivityTag.PARTY, ["파티", "친구", "모임", "축제"]),
            MusicScenario("로맨틱한 데이트", "💕", "연인과의 달콤한 시간", 
                         EmotionTag.ROMANTIC, ActivityTag.SOCIAL, ["데이트", "연인", "로맨틱"]),
            MusicScenario("분위기 있는 저녁 모임", "🍷", "어른스럽고 세련된 사교", 
                         EmotionTag.DRAMATIC, ActivityTag.SOCIAL, ["저녁", "모임", "분위기"]),
            
            # 이동/통근 관련
            MusicScenario("출근길 기분전환", "🚗", "새로운 하루를 위한 동기부여", 
                         EmotionTag.UPLIFTING, ActivityTag.COMMUTE, ["출근", "통근", "아침"]),
            MusicScenario("퇴근길 힐링타임", "🚌", "하루의 피로를 달래는", 
                         EmotionTag.PEACEFUL, ActivityTag.COMMUTE, ["퇴근", "피로", "집"]),
            
            # 수면/잠자리 관련
            MusicScenario("잠들기 전 마음 진정", "😴", "편안한 잠자리를 위한", 
                         EmotionTag.PEACEFUL, ActivityTag.SLEEP, ["잠", "수면", "밤"]),
            MusicScenario("불면증으로 잠 못 이룰 때", "🌙", "스트레스로 잠이 안 올 때", 
                         EmotionTag.STRESSED, ActivityTag.SLEEP, ["불면", "잠못이룸", "고민"]),
            
            # 특별한 감정 상태
            MusicScenario("감동적인 순간을 느끼고 싶을 때", "✨", "깊은 감동과 여운이 필요한", 
                         EmotionTag.DRAMATIC, ActivityTag.RELAXATION, ["감동", "여운", "특별한"]),
            MusicScenario("에너지 충전이 필요할 때", "⚡", "의욕을 되찾고 동기부여", 
                         EmotionTag.ENERGETIC, ActivityTag.FOCUS, ["동기부여", "의욕", "충전"]),
            MusicScenario("기분이 좋아서 뭔가 하고 싶을 때", "🌟", "행복해서 무언가 활동하고 싶은", 
                         EmotionTag.HAPPY, ActivityTag.WORK, ["기분좋은", "활동적", "생산적"])
        ]
        return scenarios
    
    def display_welcome(self):
        """환영 메시지 출력"""
        print("🎵" + "=" * 60 + "🎵")
        print("        AI 음악 추천 시스템")
        print("    감정 50% | 날씨 30% | 시간 20%")
        print("     ✅ Jamendo API 최적화 버전")
        print("     🎲 항상 랜덤 추천 모드")
        print("🎵" + "=" * 60 + "🎵")
        print()
        
        # 현재 시간 자동 감지 표시
        current_hour = datetime.now().hour
        auto_time = self.recommender.get_time_of_day(current_hour)
        time_emoji = self.get_time_emoji(auto_time)
        print(f"🕐 현재 시간: {time_emoji} {auto_time.value} ({current_hour}시) - 자동 반영됩니다")
        print()
    
    def get_scenario_input(self) -> List[MusicScenario]:
        """시나리오 선택 (다중 선택 가능)"""
        print("🎭 현재 상황에 맞는 것을 선택해주세요 (여러 개 선택 가능):")
        print("💡 번호를 쉼표로 구분해서 입력하세요 (예: 1,3,5)")
        print()
        
        for i, scenario in enumerate(self.scenarios, 1):
            print(f"  {i:2d}. {scenario.emoji} {scenario.name}")
            print(f"      {scenario.description}")
            if i % 5 == 0:  # 5개마다 줄바꿈
                print()
        
        while True:
            try:
                user_input = input(f"\n선택 (1-{len(self.scenarios)}): ").strip()
                
                # 쉼표로 분리하고 숫자 파싱
                choices = []
                for choice_str in user_input.split(','):
                    choice_str = choice_str.strip()
                    if choice_str:
                        choice = int(choice_str)
                        if 1 <= choice <= len(self.scenarios):
                            choices.append(choice - 1)  # 0-based index
                        else:
                            raise ValueError(f"번호 {choice}는 범위를 벗어남")
                
                if not choices:
                    print("❌ 최소 하나는 선택해주세요.")
                    continue
                
                # 중복 제거
                choices = list(set(choices))
                selected_scenarios = [self.scenarios[i] for i in choices]
                
                print("\n✅ 선택된 상황:")
                for scenario in selected_scenarios:
                    print(f"   {scenario.emoji} {scenario.name}")
                
                return selected_scenarios
                
            except ValueError as e:
                print(f"❌ 올바른 번호를 입력해주세요. {e}")
            except Exception as e:
                print(f"❌ 입력 오류: {e}")
    
    def get_weather_input(self) -> Weather:
        """날씨 입력 받기"""
        print("\n🌤️ 현재 날씨는 어떤가요?")
        weathers = list(Weather)
        
        for i, weather in enumerate(weathers, 1):
            emoji = self.get_weather_emoji(weather)
            description = self.get_weather_description(weather)
            print(f"  {i}. {emoji} {weather.value} - {description}")
        
        while True:
            try:
                choice = int(input(f"\n선택 (1-{len(weathers)}): "))
                if 1 <= choice <= len(weathers):
                    selected = weathers[choice - 1]
                    print(f"✅ 선택됨: {self.get_weather_emoji(selected)} {selected.value}")
                    return selected
                else:
                    print("❌ 올바른 번호를 입력해주세요.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
    

    
    def combine_scenarios(self, scenarios: List[MusicScenario]) -> Tuple[EmotionTag, ActivityTag]:
        """여러 시나리오를 조합하여 대표 감정과 활동 결정"""
        if len(scenarios) == 1:
            return scenarios[0].emotion, scenarios[0].activity
        
        # 감정별 빈도 계산
        emotion_counts = {}
        activity_counts = {}
        
        for scenario in scenarios:
            emotion_counts[scenario.emotion] = emotion_counts.get(scenario.emotion, 0) + 1
            activity_counts[scenario.activity] = activity_counts.get(scenario.activity, 0) + 1
        
        # 최빈값 선택
        primary_emotion = max(emotion_counts.items(), key=lambda x: x[1])[0]
        primary_activity = max(activity_counts.items(), key=lambda x: x[1])[0]
        
        print(f"\n🎯 조합 결과: {primary_emotion.value} 감정 + {primary_activity.value} 활동")
        print("   (선택된 여러 상황을 종합한 결과)")
        
        return primary_emotion, primary_activity
    
    def fetch_and_display_music(self, api_url: str, is_random: bool = False):
        """API를 호출해서 음악 리스트를 가져와 표시 (백업 전략 포함)"""
        try:
            print("\n🎵 음악을 검색하고 있습니다...")
            response = requests.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['headers']['status'] == 'success':
                    tracks = data['results']
                    count = data['headers']['results_count']
                    
                    if count == 0:
                        print("🔄 조건에 맞는 음악이 없어서 더 넓은 범위에서 검색합니다...")
                        # 백업 전략: 조건을 완화해서 다시 시도
                        backup_url = self.create_backup_search_url(api_url)
                        backup_response = requests.get(backup_url)
                        
                        if backup_response.status_code == 200:
                            backup_data = backup_response.json()
                            if backup_data['headers']['status'] == 'success' and backup_data['results']:
                                tracks = backup_data['results']
                                count = backup_data['headers']['results_count']
                                print(f"✅ 넓은 범위에서 {count}개의 음악을 찾았습니다!")
                    
                    if tracks:
                        # 🎲 랜덤 모드에서는 결과를 섞기
                        if is_random and tracks:
                            random.shuffle(tracks)
                        
                        print(f"\n🎲 랜덤 발견: {count}개의 음악을 찾았습니다!")
                        print("=" * 60)
                        
                        for i, track in enumerate(tracks[:10], 1):  # 상위 10개만 표시
                            print(f"\n{i:2d}. 🎵 {track['name']}")
                            print(f"    👤 아티스트: {track['artist_name']}")
                            print(f"    ⏱️  길이: {track['duration']}초")
                            print(f"    🎧 듣기: {track['audio']}")
                            
                            if i == 5:  # 5개마다 구분선
                                print("    " + "-" * 40)
                        
                        print(f"\n🎲 랜덤 팁: 같은 설정으로 다시 추천받으면 다른 음악들을 발견할 수 있어요!")
                    else:
                        print("😅 죄송합니다. 해당 조건에 맞는 음악을 찾을 수 없었습니다.")
                        print("💡 다른 시나리오나 날씨 조건으로 다시 시도해보세요!")
                            
                else:
                    print(f"❌ API 오류: {data['headers']['error_message']}")
                    if 'warnings' in data['headers'] and data['headers']['warnings']:
                        print(f"⚠️ 경고: {data['headers']['warnings']}")
                    
            else:
                print(f"❌ HTTP 오류: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 네트워크 오류: {e}")
    
    def create_backup_search_url(self, original_url: str) -> str:
        """조건을 완화한 백업 검색 URL 생성"""
        # URL에서 파라미터 추출
        if "fuzzytags=" in original_url:
            # 태그를 하나만 사용하도록 단순화
            parts = original_url.split("fuzzytags=")[1].split("&")[0]
            first_tag = parts.split("+")[0]  # 첫 번째 태그만 사용
            
            # 조건 완화: 속도와 보컬 제한 제거
            backup_url = original_url.split("?")[0] + "?"
            backup_url += f"client_id=709fa152&fuzzytags={first_tag}&limit=20&format=json"
            
            return backup_url
        
        return original_url
    
    def run_interactive_session(self):
        """대화형 세션 실행"""
        self.display_welcome()
        
        # 사용자 입력 수집
        selected_scenarios = self.get_scenario_input()
        weather = self.get_weather_input()
        
        # 시간은 자동 감지
        current_hour = datetime.now().hour
        time_period = self.recommender.get_time_of_day(current_hour)
        
        # 시나리오 조합
        emotion, activity = self.combine_scenarios(selected_scenarios)
        
        # 추천 생성
        print(f"\n🎲 랜덤 음악 추천을 생성하고 있습니다...")
        print("-" * 50)
        
        recommendation = self.recommender.recommend_music(
            emotion=emotion,
            activity=activity,
            weather=weather,
            time_of_day=time_period,
            randomize=True
        )
        
        # 선택된 시나리오 요약 출력
        print(f"\n📋 선택된 상황 요약:")
        for scenario in selected_scenarios:
            print(f"   {scenario.emoji} {scenario.name}")
        
        # 결과 출력
        print(self.recommender.get_detailed_analysis(recommendation))
        
        # API URL 생성
        params = "&".join([f"{k}={v}" for k, v in recommendation.api_params.items()])
        api_url = f"https://api.jamendo.com/v3.0/tracks/?client_id=602b9767&{params}"
        
        print("\n🔗 Jamendo API 호출 URL:")
        print(api_url)
        
        # ✅ 실제 음악 데이터 가져오기
        # 여기서 YOUR_CLIENT_ID를 실제 클라이언트 ID로 바꿔주세요!
        actual_api_url = api_url.replace("YOUR_CLIENT_ID", "709fa152")  # 테스트용 ID
        self.fetch_and_display_music(actual_api_url, True)
        
        # 다시 실행 여부
        print("\n" + "=" * 60)
        restart = input("🔄 다시 추천받으시겠습니까? (y/n): ").lower()
        if restart in ['y', 'yes', '네', 'ㅇ']:
            print("\n")
            self.run_interactive_session()
        else:
            print("🎵 이용해주셔서 감사합니다!")
    
    # 이모지 및 설명 헬퍼 메서드들
    def get_weather_emoji(self, weather: Weather) -> str:
        emoji_map = {
            Weather.SUNNY: "☀️", Weather.CLOUDY: "☁️", Weather.RAINY: "🌧️",
            Weather.SNOWY: "❄️", Weather.WINDY: "💨"
        }
        return emoji_map.get(weather, "🌤️")
    
    def get_weather_description(self, weather: Weather) -> str:
        desc_map = {
            Weather.SUNNY: "맑고 화창한 날씨",
            Weather.CLOUDY: "흐리고 구름 많은 날씨",
            Weather.RAINY: "비가 내리는 날씨",
            Weather.SNOWY: "눈이 내리는 날씨",
            Weather.WINDY: "바람이 강한 날씨"
        }
        return desc_map.get(weather, "")
    
    def get_time_emoji(self, time_period: TimeOfDay) -> str:
        emoji_map = {
            TimeOfDay.DAWN: "🌅", TimeOfDay.MORNING: "🌄", TimeOfDay.AFTERNOON: "☀️",
            TimeOfDay.EVENING: "🌆", TimeOfDay.NIGHT: "🌙"
        }
        return emoji_map.get(time_period, "🕐")

# 사용 예시
def main():
    # 1. 대화형 모드
    print("🎵 음악 추천 시스템 - 실행 모드 선택")
    print("1. 🖥️ 대화형 모드 (사용자 입력)")
    print("2. 📋 데모 모드 (미리 설정된 예시)")
    
    while True:
        try:
            mode = int(input("\n선택 (1-2): "))
            if mode == 1:
                ui = UserInterface()
                ui.run_interactive_session()
                break
            elif mode == 2:
                run_demo_mode()
                break
            else:
                print("❌ 1 또는 2를 입력해주세요.")
        except ValueError:
            print("❌ 숫자를 입력해주세요.")

def run_demo_mode():
    """데모 모드 실행"""
    recommender = BalancedRatioRecommender()
    
    print("\n🎵 데모 모드: 미리 설정된 시나리오들")
    print("=" * 60)
    
    demos = [
        {
            "name": "😰💼 스트레스 받는 직장인의 집중 작업",
            "emotion": EmotionTag.STRESSED,
            "activity": ActivityTag.FOCUS,
            "weather": Weather.RAINY,
            "description": "비오는 오후, 스트레스 받지만 집중해서 일해야 할 때"
        },
        {
            "name": "😊🏃 행복한 아침 운동",
            "emotion": EmotionTag.HAPPY,
            "activity": ActivityTag.EXERCISE,
            "weather": Weather.SUNNY,
            "description": "맑은 아침, 기분 좋게 운동하러 나갈 때"
        },
        {
            "name": "💕🍷 로맨틱한 저녁 데이트",
            "emotion": EmotionTag.ROMANTIC,
            "activity": ActivityTag.SOCIAL,
            "weather": Weather.CLOUDY,
            "description": "흐린 저녁, 연인과의 달콤한 시간"
        },
        {
            "name": "🧘🌙 명상하며 마음 정리",
            "emotion": EmotionTag.PEACEFUL,
            "activity": ActivityTag.MEDITATION,
            "weather": Weather.SNOWY,
            "description": "눈 내리는 밤, 조용히 명상하며 하루 마무리"
        }
    ]
    
    for i, demo in enumerate(demos, 1):
        print(f"\n{i}. {demo['name']}")
        print(f"   {demo['description']}")
        print("-" * 40)
        
        # 현재 시간 자동 감지
        current_hour = datetime.now().hour
        time_period = recommender.get_time_of_day(current_hour)
        
        # 랜덤 추천
        recommendation = recommender.recommend_music(
            emotion=demo['emotion'],
            activity=demo['activity'],
            weather=demo['weather'],
            time_of_day=time_period,
            randomize=True
        )
        print(recommender.get_detailed_analysis(recommendation))

if __name__ == "__main__":
    main()