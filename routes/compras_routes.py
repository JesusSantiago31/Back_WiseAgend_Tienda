from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from utils import verificar_token
from db import db

compras_bp = Blueprint("compras_bp", __name__)

@compras_bp.post("/comprar")
def comprar_producto():
    # 1️⃣ Verificar token
    user_id = verificar_token(request)
    if not user_id:
        return jsonify({"ok": False, "mensaje": "Token inválido"}), 401

    # 2️⃣ Obtener id_producto del request
    data = request.json or {}
    id_producto = data.get("id_producto")
    if not id_producto:
        return jsonify({"ok": False, "mensaje": "id_producto requerido"}), 400

    # 3️⃣ Referencias a la BD
    user_ref = db.collection("usuarios").document(user_id)
    prod_ref = db.collection("tienda_productos").document(id_producto)
    user_prod_ref = db.collection("usuarios_productos")

    # 4️⃣ Obtener documentos
    user_doc = user_ref.get()
    prod_doc = prod_ref.get()
    if not user_doc.exists:
        return jsonify({"ok": False, "mensaje": "Usuario no existe"}), 404
    if not prod_doc.exists:
        return jsonify({"ok": False, "mensaje": "Producto no existe"}), 404

    user = user_doc.to_dict()
    product = prod_doc.to_dict()

    # 5️⃣ Validaciones de negocio
    tokens_usuario = user.get("monedas", 0)
    tipo_cuenta = user.get("tipo_cuenta", "free")
    costo = product.get("costo", 0)
    es_premium = product.get("premium", False)
    dias_vencimiento = product.get("vencimiento", 30)
    tipo_producto = product.get("tipo", "normal")

    if es_premium and tipo_cuenta != "premium":
        return jsonify({"ok": False, "mensaje": "Producto solo para usuarios premium"}), 403

    if tokens_usuario < costo:
        return jsonify({
            "ok": False,
            "mensaje": "Tokens insuficientes",
            "tokens_disponibles": tokens_usuario
        }), 400

    # 6️⃣ Verificar si el usuario ya compró el producto y sigue vigente
    query = user_prod_ref.where("id_usuario", "==", user_id)\
                         .where("id_producto", "==", id_producto)\
                         .where("fecha_vencimiento", ">", datetime.utcnow())\
                         .get()
    if query:
        return jsonify({"ok": False, "mensaje": "Ya tienes este producto activo"}), 400

    # 7️⃣ Preparar fechas
    fecha_compra = datetime.utcnow()
    fecha_vencimiento = fecha_compra + timedelta(days=dias_vencimiento)

    # 8️⃣ Función transaccional
    @db.transaction
    def realizar_compra(transaction):
        # Restar tokens al usuario
        transaction.update(user_ref, {"monedas": tokens_usuario - costo})

        # Registrar compra en usuarios_productos
        compra_ref = user_prod_ref.document()
        transaction.set(compra_ref, {
            "id_usuario": user_id,
            "id_producto": id_producto,
            "fecha_compra": fecha_compra,
            "fecha_vencimiento": fecha_vencimiento
        })

        # Si es suscripción premium, actualizar tipo_cuenta y vencimiento
        if tipo_producto == "premium":
            transaction.update(user_ref, {
                "tipo_cuenta": "premium",
                "premium_vencimiento": fecha_vencimiento
            })

    # Ejecutar la transacción
    transaction = db.transaction()
    realizar_compra(transaction)

    mensaje = "Producto comprado correctamente"
    if tipo_producto == "premium":
        mensaje = f"Suscripción Premium activada por {dias_vencimiento} días"

    # 9️⃣ Respuesta
    return jsonify({
        "ok": True,
        "mensaje": mensaje,
        "tokens_restantes": tokens_usuario - costo,
        "fecha_vencimiento": fecha_vencimiento.isoformat(),
        "producto": {
            "id": product.get("id"),
            "nombre": product.get("nombre"),
            "descripcion": product.get("descripcion"),
            "costo": costo,
            "premium": es_premium,
            "tipo": tipo_producto,
            "categoria": product.get("category"),
        }
    }), 200
