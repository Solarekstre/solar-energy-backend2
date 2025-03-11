from flask import Flask, request, jsonify
import pytesseract
from PIL import Image
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "Dosya yüklenmedi"}), 400

    file = request.files["file"]
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    try:
        extracted_text = pytesseract.image_to_string(Image.open(file_path), lang="eng")
        daily_consumption = extract_consumption(extracted_text)
        
        if not daily_consumption:
            return jsonify({
                "error": "Günlük tüketim değeri okunamadı.",
                "manual_input_required": True
            }), 400

        calculations = calculate_solar_needs(daily_consumption)
        return jsonify(calculations)

    except Exception as e:
        return jsonify({"error": "OCR işlemi sırasında hata oluştu.", "details": str(e)}), 500

def extract_consumption(text):
    """ OCR çıktısından günlük tüketim değerini çıkarır """
    lines = text.split("\n")
    for line in lines:
        if "kWh/gün" in line or "kWh/gun" in line:
            numbers = [float(s.replace(",", ".")) for s in line.split() if s.replace(",", ".").replace(".", "").isdigit()]
            return numbers[0] if numbers else None
    return None

def calculate_solar_needs(daily_kwh):
    """ Güneş paneli ve batarya ihtiyacını hesaplar """
    panel_power = 0.55  # 550W = 0.55 kW
    sunlight_hours = 5.5  # Adana ortalama güneşlenme süresi
    battery_capacity = 7  # kWh

    required_power = daily_kwh / sunlight_hours
    panel_count = int(required_power / panel_power) + 1  # Yuvarlama
    
    panel_area_per_panel = 2.2  # 2.2 m² bir panelin kapladığı alan
    total_panel_area = panel_count * panel_area_per_panel
    
    return {
        "daily_consumption_kwh": daily_kwh,
        "required_power_kw": round(required_power, 2),
        "panel_count": panel_count,
        "total_panel_area_m2": round(total_panel_area, 2),
        "battery_capacity_kwh": battery_capacity,
        "payback_period_years": round((panel_count * 6000 + battery_capacity * 10000) / (daily_kwh * 365 * 2.75), 2)
    }

if _name_ == "_main_":
    app.run(debug=True)
