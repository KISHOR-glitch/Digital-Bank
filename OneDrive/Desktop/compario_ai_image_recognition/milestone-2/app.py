from flask import Flask, request, jsonify, render_template
from concurrent.futures import ThreadPoolExecutor, as_completed
import os, re, pandas as pd

# AI + OCR imports
import recognition_mobilenet as recognition
import recognition_easyocr as ocr

# Scraper imports
from multi_scraper import init_driver, scrape_amazon, scrape_flipkart, scrape_snapdeal

app = Flask(__name__)
UPLOAD_FOLDER = "uploads/"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------------
# Helper Functions
# ------------------------
def clean_text(text):
    """Clean OCR text"""
    return re.sub(r'[^a-zA-Z0-9\s]', '', str(text)).lower().strip()

def parse_price(price_str):
    """Convert ₹ or Rs. price string to float for comparison."""
    try:
        return float(re.sub(r"[^\d.]", "", price_str))
    except:
        return float("inf")

def run_scrapers(query):
    """Run 3 scrapers in parallel for speed."""
    results = {}
    with ThreadPoolExecutor(max_workers=3) as executor:
        tasks = {
            executor.submit(scrape_amazon, init_driver(), query): "Amazon",
            executor.submit(scrape_flipkart, init_driver(), query): "Flipkart",
            executor.submit(scrape_snapdeal, init_driver(), query): "Snapdeal",
        }
        for task in as_completed(tasks):
            site = tasks[task]
            try:
                results[site] = task.result()
            except Exception as e:
                results[site] = {"Name": "Error", "Price": "N/A", "Link": "#"}
                print(f"⚠️ {site} scraper failed: {e}")
    return results

def build_search_query(cleaned_text, ai_label):
    """Smartly combine OCR + AI label → skip generic terms."""
    GENERIC_WORDS = [
        "cellular_telephone", "ipod", "handset", "telephone", "gadget",
        "mobile_phone", "smartphone", "communication_device", "modem",
        "remote_control", "handheld_computer", "personal_computer"
    ]

    clean_ai = ai_label.lower()
    for bad in GENERIC_WORDS:
        clean_ai = clean_ai.replace(bad, "")

    query = (cleaned_text + " " + clean_ai).strip() if cleaned_text else clean_ai

    # Brand smartening
    BRANDS = ["apple", "iphone", "samsung", "vivo", "oppo", "oneplus", "redmi", "realme", "motorola", "iqoo", "nothing"]
    if any(b in query for b in BRANDS):
        # If iPhone detected → enforce correct format
        if "iphone" in query or "apple" in query:
            return "Apple iPhone"
        return query
    # fallback generic
    return "smartphone"

# ------------------------
# Routes
# ------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """Accept uploaded product image → AI + OCR → Scrape → Compare prices"""
    if 'image' not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"})

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # Step 1️⃣ - AI Prediction
    predictions = recognition.predict_product(file_path)
    if not predictions:
        return jsonify({"error": "AI model failed to predict the image."})
    top_prediction = predictions[0]['name']

    # Step 2️⃣ - OCR Detection
    detected_text = ocr.extract_text(file_path)
    cleaned_text = clean_text(detected_text)

    # Step 3️⃣ - Smart Query Builder
    search_query = build_search_query(cleaned_text, top_prediction)
    print(f"🧠 AI: {top_prediction}")
    print(f"📝 OCR: {cleaned_text}")
    print(f"🔍 Final Query: {search_query}")

    # Step 4️⃣ - Run Scrapers
    results = run_scrapers(search_query)

    # Step 5️⃣ - Clean Results
    matches = [
        {
            "Platform": site,
            "Title": data["Name"],
            "Price": data["Price"],
            "Product Link": data["Link"]
        }
        for site, data in results.items() if data["Name"] != "No products found"
    ]

    # Step 6️⃣ - Find Lowest Price
    lowest = min(matches, key=lambda x: parse_price(x["Price"])) if matches else None

    # Step 7️⃣ - Save JSON
    os.makedirs("datasets", exist_ok=True)
    pd.DataFrame(matches).to_json(f"datasets/{search_query}_results.json", orient="records", indent=4)

    return jsonify({
        "message": "Search completed successfully!",
        "top_product": top_prediction,
        "detected_text": cleaned_text,
        "search_query": search_query,
        "matches": matches,
        "lowest_price": lowest
    })

if __name__ == "__main__":
    app.run(debug=True)
