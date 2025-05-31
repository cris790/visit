from flask import Flask, jsonify
import aiohttp
import asyncio
import requests
from byte import *
from protobuf_parser import Parser, Utils

app = Flask(__name__)

def fetch_tokens():
    url = "https://tokenff.discloud.app/token"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            tokens_data = response.json()
            print("🔹 Dados recebidos da API:", tokens_data)

            tokens = []

            # Formato novo [{"token": "..."}]
            if isinstance(tokens_data, list):
                for item in tokens_data:
                    if isinstance(item, dict) and "token" in item:
                        tokens.append(item["token"])

            # Formato antigo {"tokens": ["..."]}
            elif isinstance(tokens_data, dict) and "tokens" in tokens_data:
                if isinstance(tokens_data["tokens"], list):
                    tokens.extend(tokens_data["tokens"])

            # Formato aninhado [{"tokens": ["..."]}]
            elif isinstance(tokens_data, list):
                for item in tokens_data:
                    if isinstance(item, dict) and "tokens" in item:
                        if isinstance(item["tokens"], list):
                            tokens.extend(item["tokens"])

            # Filtra tokens válidos
            valid_tokens = [t for t in tokens if t and isinstance(t, str) and t != "N/A"][:4]
            print(f"✅ {len(valid_tokens)} tokens válidos encontrados")
            return valid_tokens

        print(f"⚠️ Falha ao buscar tokens. Código de status: {response.status_code}")
        return []
    except Exception as e:
        print(f"⚠️ Erro ao buscar tokens: {e}")
        return []

async def visit(session, token, uid, data):
    url = "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"
    headers = {
        "ReleaseVersion": "OB49",
        "X-GA": "v1 1",
        "Authorization": f"Bearer {token}",
        "Host": "clientbp.ggblueshark.com"
    }
    try:
        async with session.post(url, headers=headers, data=data, ssl=False):
            pass
    except Exception as e:
        print(f"⚠️ Erro na requisição com token: {e}")

async def send_requests_concurrently(tokens, uid, num_requests=300):
    connector = aiohttp.TCPConnector(limit=0)
    async with aiohttp.ClientSession(connector=connector) as session:
        data = bytes.fromhex(encrypt_api("08" + Encrypt_ID(uid) + "1801"))
        tasks = [asyncio.create_task(visit(session, tokens[i % len(tokens)], uid, data)) 
                for i in range(num_requests)]
        await asyncio.gather(*tasks)

@app.route('/<int:uid>', methods=['GET'])
def send_visits(uid):
    tokens = fetch_tokens()

    if not tokens:
        return jsonify({
            "status": "erro",
            "message": "⚠️ Nenhum token válido encontrado",
            "solucao": "Verifique se a API de tokens está funcionando"
        }), 500

    print(f"✅ Tokens disponíveis: {len(tokens)}")

    num_requests = 300
    asyncio.run(send_requests_concurrently(tokens, uid, num_requests))

    return jsonify({
        "status": "sucesso",
        "message": f"✅ {num_requests} visitas enviadas para UID: {uid}",
        "tokens_utilizados": len(tokens),
        "requisicoes_por_token": num_requests // len(tokens)
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=50099)
