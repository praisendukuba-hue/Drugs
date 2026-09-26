from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

PT_API_URL = "https://ptexchange-api.vercel.app/pay/jetton"
PT_API_KEY = os.environ.get("PT_EXCHANGE_API_KEY")

BACKEND_SECRET = os.environ.get("BACKEND_SECRET")


@app.route("/")
def home():
    return jsonify({
        "ok": True,
        "service": "NOTCOIN Payment Backend"
    })


@app.route("/pay/notcoin", methods=["POST"])
def pay_notcoin():

    # ==========================================
    # CHECK BACKEND SECRET
    # ==========================================

    auth = request.headers.get("X-Backend-Key")

    if not BACKEND_SECRET or auth != BACKEND_SECRET:
        return jsonify({
            "ok": False,
            "error": "Unauthorized"
        }), 401

    # ==========================================
    # CHECK PT EXCHANGE KEY
    # ==========================================

    if not PT_API_KEY:
        return jsonify({
            "ok": False,
            "error": "PT Exchange API key is not configured"
        }), 500

    # ==========================================
    # GET REQUEST DATA
    # ==========================================

    data = request.get_json(silent=True) or {}

    wallet = str(data.get("wallet", "")).strip()
    amount = data.get("amount")

    if not wallet:
        return jsonify({
            "ok": False,
            "error": "Wallet is required"
        }), 400

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
            "error": "Payment gateway connection failed"
        }), 502

    # ==========================================
    # GET RESPONSE
    # ==========================================

    try:
        result = response.json()
    except:
        result = {
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
            "gateway": result
        }), 200

    # ==========================================
    # PT EXCHANGE REJECTED PAYMENT
    # ==========================================

    return jsonify({
        "ok": False,
        "status_code": response.status_code,
        "error": "PT Exchange rejected payment",
        "gateway": result
    }), 400


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
