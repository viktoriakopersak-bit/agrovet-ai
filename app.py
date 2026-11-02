from flask import Flask, render_template, jsonify, request
from models import AlertManager, Cow, HealthRecord
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
manager = AlertManager()
manager.create_test_data()

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cow/<cow_id>')
def cow_detail(cow_id):
    cow = manager.get_cow(cow_id)
    if not cow:
        return "Корова не найдена", 404
    return render_template('cow.html', cow=cow.to_dict(), today=datetime.now().strftime("%Y-%m-%d"))

# ====================== API ======================
@app.route('/api/cows', methods=['GET'])
def api_cows():
    return jsonify([cow.to_dict() for cow in manager.get_all_cows()])

@app.route('/api/records', methods=['POST'])
def api_add_record():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Нет данных"}), 400

        cow_id = data.get('cow_id')
        date = data.get('date')
        weight = data.get('weight')
        bcs = data.get('bcs')

        if not all([cow_id, date, weight is not None, bcs is not None]):
            return jsonify({"error": "Не все поля заполнены"}), 400

        record = HealthRecord(date, float(weight), float(bcs))
        manager.add_record(cow_id, record)

        return jsonify({"status": "ok", "message": "Запись успешно добавлена"})
    
    except Exception as e:
        print("Ошибка при добавлении записи:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    alerts = []
    for cow in manager.get_all_cows():
        last = cow.last()
        if not last:
            continue
        delta = manager.weight_change_percent(cow)

        if last.bcs < 4:
            alerts.append({
                "cow_id": cow.id,
                "nickname": cow.nickname,
                "type": "Худая",
                "severity": 3,
                "description": f"Аномально низкий BCS ({last.bcs})",
                "recommendation": "Срочно вызвать ветеринара, усилить кормление, проверить на болезни"
            })
        elif last.bcs > 7:
            alerts.append({
                "cow_id": cow.id,
                "nickname": cow.nickname,
                "type": "Ожирение",
                "severity": 2,
                "description": f"Аномально высокий BCS ({last.bcs})",
                "recommendation": "Снизить калорийность рациона, увеличить выгул"
            })

        if delta and abs(delta) > 3:
            alerts.append({
                "cow_id": cow.id,
                "nickname": cow.nickname,
                "type": "Изменение веса",
                "severity": 2 if abs(delta) > 5 else 1,
                "description": f"Аномальное изменение веса ({delta}%)",
                "recommendation": "Провести обследование, проверить корм и состояние здоровья"
            })

    alerts.sort(key=lambda x: x['severity'], reverse=True)
    return jsonify(alerts)

@app.route('/api/simulate', methods=['POST'])
def api_simulate():
    try:
        days = int(request.json.get('days', 3))
        manager.simulate_days(days)
        return jsonify({"status": "ok", "message": f"Симуляция {days} дней выполнена"})
    except Exception as e:
        print("Ошибка симуляции:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/clear', methods=['POST'])
def api_clear():
    manager.herd.clear()
    manager.create_test_data()
    return jsonify({"status": "cleared"})

@app.route('/api/upload_excel', methods=['POST'])
def api_upload_excel():
    if 'file' not in request.files:
        return jsonify({"error": "Нет файла"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        manager.load_from_excel(filepath)
        return jsonify({
            "status": "success", 
            "message": f"Успешно загружено {len(manager.herd)} коров"
        })
    except Exception as e:
        print("Ошибка загрузки Excel:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)