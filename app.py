from flask import Flask, request, jsonify
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

PT_API_URL = "https://ptexchange-api.vercel.app/pay/jetton"

PT_API_KEY = os.getenv("PT_EXCHANGE_API_KEY")
BACKEND_SECRET = os.getenv("BACKEND_SECRET")


@app.route("/")
def home():
    return jsonify({
        "ok": True,
        "service": "NOTCOIN Payment Backend"
    })


@app.route("/pay/notcoin", methods=["POST"])
def pay_notcoin():

    # ==========================================
    # BACKEND AUTHENTICATION
    # ==========================================

    auth = request.headers.get("X-Backend-Key")

    if not BACKEND_SECRET:
        return jsonify({
            "ok": False,
            "error": "BACKEND_SECRET is missing on Render"
        }), 500

    if auth != BACKEND_SECRET:
        return jsonify({
            "ok": False,
            "error": "Invalid backend secret"
        }), 401


    # ==========================================
    # PT EXCHANGE KEY
    # ==========================================

    if not PT_API_KEY:
        return jsonify({
            "ok": False,
            "error": "PT_EXCHANGE_API_KEY is missing on Render"
        }), 500


    # ==========================================
    # READ JSON
    # ==========================================

    data = request.get_json(silent=True)

    if not data:
        return jsonify({
            "ok": False,
            "error": "JSON body is missing"
        }), 400


    wallet = str(
        data.get("wallet", "")
    ).strip()

    amount = data.get("amount")


    # ==========================================
    # WALLET CHECK
    # ==========================================

    if not wallet:
        return jsonify({
            "ok": False,
            "error": "Wallet is required"
        }), 400


    # ==========================================
    # AMOUNT CHECK
    # ==========================================

    if amount is None:
        return jsonify({
            "ok": False,
            "error": "Amount is required"
        }), 400

    try:
        amount = float(amount)
    except:
        return jsonify({
            "ok": False,
            "error": "Invalid amount"
        }), 400


    if amount < 15:
        return jsonify({
            "ok": False,
            "error": "Minimum withdrawal is 15 NOTCOIN"
        }), 400


    # ==========================================
    # PT EXCHANGE PAYLOAD
    # ==========================================

    payload = {
        "api_key": PT_API_KEY,
        "to_address": wallet,
        "jetton_symbol": "NOT",
        "amount": amount,
        "comment": "NOTCOIN Withdrawal"
    }


    # ==========================================
    # SEND TO PT EXCHANGE
    # ==========================================

    try:

        response = requests.post(
            PT_API_URL,
            json=payload,
            timeout=30
        )

    except requests.RequestException as e:

        return jsonify({
            "ok": False,
            "error": "PT Exchange connection failed",
            "details": str(e)
        }), 502


    # ==========================================
    # READ PT RESPONSE
    # ==========================================

    try:

        gateway = response.json()

    except:

        gateway = {
            "raw": response.text
        }


    # ==========================================
    # SUCCESS
    # ==========================================

    if 200 <= response.status_code < 300:

        return jsonify({
            "ok": True,
            "status_code": response.status_code,
            "amount": amount,
            "wallet": wallet,
            "gateway": gateway
        }), 200


    # ==========================================
    # PT EXCHANGE ERROR
    # ==========================================

    return jsonify({
        "ok": False,
        "status_code": response.status_code,
        "error": "PT Exchange rejected the payment",
        "gateway": gateway
    }), response.status_code


if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "10000")
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
