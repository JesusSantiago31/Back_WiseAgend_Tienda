from flask import Blueprint, jsonify, request
from utils import verificar_token, actualizar_productos_usuario, obtener_ids_productos_vigentes
from datetime import datetime
from db import db

usuarios_bp = Blueprint("usuarios_bp", __name__)


@usuarios_bp.get("/usuario/productos")
def productos_usuario():
    user_id = verificar_token(request)
    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    # 👉 AQUÍ SÍ SE USA actualizar_productos_usuario
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

    # Expiración de suscripción premium
    if user.get("tipo_cuenta") == "premium":
        premium_venc = user.get("premium_vencimiento")
        if premium_venc and premium_venc < datetime.utcnow():
            user_ref.update({
                "tipo_cuenta": "free",
                "premium_vencimiento": None
            })
            user["tipo_cuenta"] = "free"
            user["premium_vencimiento"] = None

    # 👉 SOLO IDS, SIN EFECTOS SECUNDARIOS
    productos_vigentes = obtener_ids_productos_vigentes(user_id)

    return jsonify({
        "ok": True,
        "id": user_id,
        "nombre": user.get("nombre"),
        "tokens": user.get("monedas", 0),
        "email": user.get("correo"),
        "tipo_cuenta": user.get("tipo_cuenta", "free"),
        "productos_comprados": productos_vigentes
    }), 200
