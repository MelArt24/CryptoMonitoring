import firebase_admin
from firebase_admin import credentials, messaging
from flask import Flask, request, jsonify
import traceback

import os
import json
from firebase_admin import credentials, initialize_app

# Ініціалізація Firebase Admin SDK
cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
cred_dict = json.loads(cred_json)
cred = credentials.Certificate(cred_dict)
initialize_app(cred)

#firebase_admin.initialize_app(cred)

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
