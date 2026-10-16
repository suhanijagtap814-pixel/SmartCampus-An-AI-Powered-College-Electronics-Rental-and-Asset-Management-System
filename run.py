import sys
import io

# Ensure UTF-8 output encoding on Windows console
if sys.platform.startswith('win'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print(">> SMART CAMPUS ELECTRONICS RENTAL & MANAGEMENT SYSTEM")
    print("="*60)
    print(">> Running on: http://127.0.0.1:5000")
    print(">> Database: PostgreSQL (Port 5432)")
    print(">> Roles available: Student, Staff, Admin")
    print(">> AI Engines: Recommender, Demand Predictor, Damage Detector, Risk Detector, Chatbot")
    print(">> QR Generator & Scanner enabled")
    print("="*60 + "\n")
    app.run(debug=True, port=5000, host='127.0.0.1')
