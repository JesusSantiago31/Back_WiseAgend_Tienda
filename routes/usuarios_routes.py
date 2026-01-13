from flask import Blueprint, jsonify, request
from utils import verificar_token, actualizar_productos_usuario

from db import db
usuarios_bp = Blueprint("usuarios_bp", __name__)


@usuarios_bp.get("/usuario/productos")
def productos_usuario():
    user_id = verificar_token(request)

    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    productos = actualizar_productos_usuario(user_id)

    return jsonify({"productos_vigentes": productos}), 200


@usuarios_bp.get("/usuario/me")
def obtener_usuario():
    user_id = verificar_token(request)

    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    user_ref = db.collection("usuarios").document(user_id)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return jsonify({"error": "Usuario no existe"}), 404

    user = user_doc.to_dict()

    return jsonify({
        "ok": True,
        "id": user_id,
        "nombre": user.get("nombre"),
        "tokens": user.get("monedas", 0),
        "email": user.get("correo"),
    }), 200
