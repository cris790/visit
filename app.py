from flask import Flask, jsonify
import aiohttp
import asyncio
import requests
from byte import *
from protobuf_parser import Parser, Utils

app = Flask(__name__)

# جلب أول 4 توكنات صالحة فقط
def fetch_tokens():
    url = "http://164.92.134.31:5001/token"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            tokens_data = response.json()
            print("🔹 البيانات المسترجعة من API:", tokens_data)  # ✅ سجل البيانات للتحقق من صحتها

            # استخراج قائمة التوكنات
            if isinstance(tokens_data, dict) and "tokens" in tokens_data:
                tokens = tokens_data["tokens"]
            elif isinstance(tokens_data, list):
                tokens = []
                for item in tokens_data:
                    if isinstance(item, dict) and "tokens" in item:
                        tokens.extend(item["tokens"])  # إذا كان الحقل قائمة، نضيف جميع العناصر
            else:
                tokens = []

            # تصفية القيم غير الصالحة مثل "N/A" وأخذ أول 4 توكنات فقط
            valid_tokens = [t for t in tokens if t and t != "N/A"][:4]

            print(f"✅ تم استخراج {len(valid_tokens)} توكنات صالحة: {valid_tokens}")
            return valid_tokens
        else:
            print(f"⚠️ فشل في جلب التوكنات. كود الاستجابة: {response.status_code}")
            return []
    except Exception as e:
        print(f"⚠️ خطأ أثناء جلب التوكنات: {e}")
        return []

# إرسال الطلبات
async def visit(session, token, uid, data):
    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    headers = {
        "ReleaseVersion": "OB48",
        "X-GA": "v1 1",
        "Authorization": f"Bearer {token}",
        "Host": "clientbp.ggblueshark.com"
    }
    try:
        async with session.post(url, headers=headers, data=data, ssl=False):
            pass  # تجاهل الاستجابة
    except:
        pass  # تجاهل الأخطاء

# إرسال الطلبات بأقصى سرعة
async def send_requests_concurrently(tokens, uid, num_requests=300):
    connector = aiohttp.TCPConnector(limit=0)
    async with aiohttp.ClientSession(connector=connector) as session:
        data = bytes.fromhex(encrypt_api("08" + Encrypt_ID(uid) + "1801"))
        tasks = [asyncio.create_task(visit(session, tokens[i % len(tokens)], uid, data)) for i in range(num_requests)]
        await asyncio.gather(*tasks)

@app.route('/<int:uid>', methods=['GET'])
def send_visits(uid):
    tokens = fetch_tokens()
    
    if not tokens:
        return jsonify({"message": "⚠️ لم يتم العثور على أي توكن صالح"}), 500
    
    print(f"✅ عدد التوكنات المتاحة: {len(tokens)}")  # ✅ تأكيد عدد التوكنات

    num_requests = 300
    asyncio.run(send_requests_concurrently(tokens, uid, num_requests))

    return jsonify({"message": f"✅ تم إرسال {num_requests} زائر إلى UID: {uid} باستخدام {len(tokens)} توكنات بسرعة عالية"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=50099)