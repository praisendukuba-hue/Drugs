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

    print("==========================================")
    print("NEW NOTCOIN PAYMENT REQUEST")
    print("==========================================")

    # ==========================================
    # BACKEND AUTH
    # ==========================================

    auth = request.headers.get("X-Backend-Key")

    if not BACKEND_SECRET:
        print("ERROR: BACKEND_SECRET missing")

        return jsonify({
            "ok": False,
            "error": "BACKEND_SECRET is missing on Render"
        }), 200

    if auth != BACKEND_SECRET:
        print("ERROR: Invalid backend secret")

        return jsonify({
            "ok": False,
            "error": "Invalid backend secret"
        }), 200


    # ==========================================
    # PT API KEY
    # ==========================================

    if not PT_API_KEY:
        print("ERROR: PT_EXCHANGE_API_KEY missing")

        return jsonify({
            "ok": False,
            "error": "PT_EXCHANGE_API_KEY is missing on Render"
        }), 200


    # ==========================================
    # READ JSON
    # ==========================================

    data = request.get_json(silent=True)

    print("Received data:", data)

    if not data:
        return jsonify({
            "ok": False,
            "error": "JSON body is missing"
        }), 200


    wallet = str(
        data.get("wallet", "")
    ).strip()

    amount = data.get("amount")


    # ==========================================
    # WALLET
    # ==========================================

    if not wallet:

        return jsonify({
            "ok": False,
            "error": "Wallet is required"
        }), 200


    # ==========================================
    # AMOUNT
    # ==========================================

    if amount is None:

        return jsonify({
            "ok": False,
            "error": "Amount is required"
        }), 200

    try:
        amount = float(amount)

    except:

        return jsonify({
            "ok": False,
            "error": "Invalid amount"
        }), 200


    if amount < 15:

        return jsonify({
            "ok": False,
            "error": "Minimum withdrawal is 15 NOTCOIN"
        }), 200


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


    print("Sending request to PT Exchange...")
    print("Wallet:", wallet)
    print("Amount:", amount)
    print("Symbol: NOT")


    # ==========================================
    # PT EXCHANGE REQUEST
    # ==========================================

    try:

        response = requests.post(
            PT_API_URL,
            json=payload,
            timeout=120
        )

        print(
            "PT Exchange HTTP status:",
            response.status_code
        )

        print(
            "PT Exchange response:",
            response.text
        )

    except requests.Timeout:

        print(
            "ERROR: PT Exchange timed out after 120 seconds"
        )

        return jsonify({
            "ok": False,
            "error": "PT Exchange timed out after 120 seconds"
        }), 200

    except requests.RequestException as e:

        print(
            "PT Exchange connection error:",
            str(e)
        )

        return jsonify({
            "ok": False,
            "error": "PT Exchange connection failed",
            "details": str(e)
        }), 200


    # ==========================================
    # READ RESPONSE
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

        print("PAYMENT SUCCESS")

        return jsonify({

            "ok": True,

            "status_code":
                response.status_code,

            "amount":
                amount,

            "wallet":
                wallet,

            "gateway":
                gateway

        }), 200


    # ==========================================
    # PT EXCHANGE ERROR
    # ==========================================

    print("PAYMENT FAILED")

    return jsonify({

        "ok": False,

        "status_code":
            response.status_code,

        "error":
            "PT Exchange rejected the payment",

        "gateway":
            gateway

    }), 200


# ==========================================
# START
# ==========================================

if __name__ == "__main__":

    port = int(
        os.getenv("PORT", "10000")
    )

    app.run(
        host="0.0.0.0",
        port=port
    )
