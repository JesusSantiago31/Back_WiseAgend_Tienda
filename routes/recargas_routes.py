from flask import Blueprint, request, jsonify
from utils import verificar_token
from db import db
from google.cloud.firestore_v1 import Increment

recargas_bp = Blueprint("recargas_bp", __name__)

@recargas_bp.post("/recargar")
def recargar():
    user_id = verificar_token(request)

    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    data = request.json or {}

    try:
        cantidad = int(data.get("cantidad", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Cantidad inválida"}), 400

    if cantidad <= 0:
        return jsonify({"error": "Cantidad inválida"}), 400

    user_ref = db.collection("usuarios").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return jsonify({"error": "Usuario no existe"}), 404

    user_ref.update({
        "tokens": Increment(cantidad)
    })

    nuevo_total = user_doc.to_dict().get("tokens", 0) + cantidad

    return jsonify({
        "ok": True,
        "mensaje": "Recarga exitosa",
        "nuevo_total": nuevo_total
    }), 200
