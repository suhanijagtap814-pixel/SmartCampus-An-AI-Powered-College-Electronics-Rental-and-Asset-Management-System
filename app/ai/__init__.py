"""
AI engines for the Smart Campus Rental platform.

  - recommender      : TF-IDF + spec heuristic hardware recommender
  - demand_predictor : category demand forecasting from rental history
  - damage_detector  : computer-vision style return-damage scoring
  - risk_detector    : student trust / risk profiler
  - chatbot          : contextual rental assistant with live DB queries
"""
from app.ai.recommender import recommend_devices
from app.ai.demand_predictor import predict_demand
from app.ai.damage_detector import analyze_return
from app.ai.risk_detector import assess_student_risk, assess_all_students
from app.ai.chatbot import chatbot_reply

__all__ = [
    'recommend_devices',
    'predict_demand',
    'analyze_return',
    'assess_student_risk',
    'assess_all_students',
    'chatbot_reply',
]
