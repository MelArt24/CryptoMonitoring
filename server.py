import firebase_admin
from firebase_admin import credentials, messaging
from flask import Flask, request, jsonify
import traceback
import requests
import pandas as pd
import ta

# Ініціалізація Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

app = Flask(__name__)


@app.route("/send", methods=["POST"])
def send_notification():
    try:
        data = request.get_json()
        token = data["token"]
        title = data["title"]
        body = data["body"]

        message = messaging.Message(
            data={
                "title": title,
                "body": body
            },
            token=token
        )

        response = messaging.send(message)
        return jsonify({"success": True, "response": response})

    except Exception as e:
        # Вивід повної інформації про помилку
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/crypto/indicators", methods=["GET"])
def get_indicators():
    try:
        symbol = request.args.get("symbol", default="SHIBUSDT")
        interval = request.args.get("interval", default="1h")
        limit = int(request.args.get("limit", default=100))

        # 1. Отримуємо історію цін (klines) з Binance
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }

        response = requests.get(url, params=params)
        klines = response.json()

        # 2. Побудова DataFrame
        df = pd.DataFrame(klines, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])
        df["close"] = pd.to_numeric(df["close"])

        # 3. Розрахунок RSI (6 періодів)
        df["rsi6"] = ta.momentum.RSIIndicator(df["close"], window=6).rsi()

        # 4. Розрахунок MACD
        macd = ta.trend.MACD(df["close"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_hist"] = macd.macd_diff()

        # 5. Отримуємо останній рядок
        last = df.iloc[-1]

        result = {
            "symbol": symbol,
            "price": str(last["close"]),
            "rsi6": round(last["rsi6"], 2),
            "macd": round(last["macd"], 8),
            "signal_line": round(last["macd_signal"], 8),
            "histogram": round(last["macd_hist"], 8)
        }

        return jsonify(result)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
