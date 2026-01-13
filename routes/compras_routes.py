from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from utils import verificar_token
from db import db

compras_bp = Blueprint("compras_bp", __name__)

@compras_bp.post("/comprar")
def comprar_producto():

    user_id = verificar_token(request)
    if not user_id:
        return jsonify({"ok": False, "mensaje": "Token inválido"}), 401

    data = request.json or {}
    id_producto = data.get("id_producto")

    if not id_producto:
        return jsonify({
            "ok": False,
            "mensaje": "id_producto requerido"
        }), 400

    # Referencias
    user_ref = db.collection("usuarios").document(user_id)
    prod_ref = db.collection("tienda_productos").document(id_producto)

    user_doc = user_ref.get()
    prod_doc = prod_ref.get()

    if not user_doc.exists:
        return jsonify({"ok": False, "mensaje": "Usuario no existe"}), 404

    if not prod_doc.exists:
        return jsonify({"ok": False, "mensaje": "Producto no existe"}), 404

    user = user_doc.to_dict()
    product = prod_doc.to_dict()

    # Ya canjeado
    if product.get("canjeado", False):
        return jsonify({
            "ok": False,
            "mensaje": "Este producto ya fue canjeado"
        }), 400

    tokens_usuario = user.get("tokens", 0)
    costo = product.get("costo", 0)

    if tokens_usuario < costo:
        return jsonify({
            "ok": False,
            "mensaje": "Tokens insuficientes",
            "tokens_disponibles": tokens_usuario
        }), 400

    @db.transactional
    def realizar_compra(transaction):
        transaction.update(user_ref, {
            "tokens": tokens_usuario - costo
        })

        transaction.update(prod_ref, {
            "canjeado": True,
            "id_usuario": user_id,
            "fecha_compra": datetime.utcnow()
        })

    transaction = db.transaction()
    realizar_compra(transaction)

    return jsonify({
        "ok": True,
        "mensaje": "Producto canjeado correctamente",
        "tokens_restantes": tokens_usuario - costo
    }), 200

@compras_bp.post("/renovar")
def renovar():

    user_id = verificar_token(request)
    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    data = request.json or {}
    id_producto = data.get("id_producto")

    if not id_producto:
        return jsonify({"error": "id_producto requerido"}), 400

    user_ref = db.collection("usuarios").document(user_id)
    prod_ref = db.collection("tienda_productos").document(id_producto)

    user_doc = user_ref.get()
    prod_doc = prod_ref.get()

    if not user_doc.exists:
        return jsonify({"error": "Usuario no existe"}), 404

    if not prod_doc.exists:
        return jsonify({"error": "Producto no existe"}), 404

    usuario = user_doc.to_dict()
    producto = prod_doc.to_dict()

    # Validar que el producto pertenece al usuario
    if producto.get("id_usuario") != user_id:
        return jsonify({"error": "Este producto no pertenece al usuario"}), 403

    costo = producto.get("costo", 0)
    dias = producto.get("dias_vigencia", 30)  # default seguro

    tokens_usuario = usuario.get("tokens", 0)

    if tokens_usuario < costo:
        return jsonify({"error": "Tokens insuficientes"}), 403

    nueva_fecha_venc = datetime.utcnow() + timedelta(days=dias)

    @db.transactional
    def renovar_producto(transaction):
        transaction.update(user_ref, {
            "tokens": tokens_usuario - costo
        })

        transaction.update(prod_ref, {
            "fecha_vencimiento": nueva_fecha_venc
        })

    transaction = db.transaction()
    renovar_producto(transaction)

    return jsonify({
        "ok": True,
        "mensaje": "Renovación exitosa",
        "fecha_vencimiento": nueva_fecha_venc
    }), 200
