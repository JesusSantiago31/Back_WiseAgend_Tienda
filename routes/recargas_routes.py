from flask import Blueprint, request, jsonify
from utils import verificar_token
from db import db

recargas_bp = Blueprint("recargas_bp", __name__)

@recargas_bp.post("/recargar")
def recargar():
    if not verificar_token(request):
        return jsonify({"error": "Token inválido"}), 401

    data = request.json
    id_usuario = data.get("id_usuario")
    cantidad = data.get("cantidad", 0)

    if cantidad <= 0:
        return jsonify({"error": "Cantidad inválida"}), 400

    user_ref = db.collection("usuarios").document(id_usuario)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return jsonify({"error": "Usuario no existe"}), 404

    usuario = user_doc.to_dict()
    nuevo_total = usuario.get("monedas", 0) + cantidad

    user_ref.update({"monedas": nuevo_total})

    return jsonify({"mensaje": "Recarga exitosa", "nuevo_total": nuevo_total})
