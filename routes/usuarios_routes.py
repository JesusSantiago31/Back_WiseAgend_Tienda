from flask import Blueprint, jsonify, request
from utils import verificar_token, actualizar_productos_usuario
from datetime import datetime

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
    # 1️⃣ Verificar token
    user_id = verificar_token(request)
    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    # 2️⃣ Referencia y documento del usuario
    user_ref = db.collection("usuarios").document(user_id)
    user_doc = user_ref.get()
    if not user_doc.exists:
        return jsonify({"error": "Usuario no existe"}), 404

    user = user_doc.to_dict()

    # 3️⃣ Revisar expiración de suscripción premium
    if user.get("tipo_cuenta") == "premium":
        premium_venc = user.get("premium_vencimiento")
        if premium_venc and premium_venc < datetime.utcnow():
            # Expiró la suscripción
            user_ref.update({
                "tipo_cuenta": "free",
                "premium_vencimiento": None
            })
            # Actualizamos localmente para la respuesta
            user["tipo_cuenta"] = "free"
            user["premium_vencimiento"] = None
     # 🔹 OBTENER PRODUCTOS VIGENTES
    productos_vigentes = actualizar_productos_usuario(user_id)

    # 4️⃣ Responder con datos del usuario
    return jsonify({
        "ok": True,
        "id": user_id,
        "nombre": user.get("nombre"),
        "tokens": user.get("monedas", 0),
        "email": user.get("correo"),
        "tipo_cuenta": user.get("tipo_cuenta", "free"),
        "productos_comprados": productos_vigentes  # 🔥 CLAVE
    }), 200