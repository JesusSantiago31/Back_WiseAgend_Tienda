from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from utils import verificar_token
from db import db

compras_bp = Blueprint("compras_bp", __name__)

@compras_bp.post("/comprar")
def comprar_producto():
    data = request.json

    id_usuario = data.get("id_usuario")
    id_producto = data.get("id_producto")

    if not id_usuario or not id_producto:
        return jsonify({
            "ok": False,
            "mensaje": "Datos incompletos"
        }), 400

    # Referencias
    user_ref = db.collection("usuarios").document(id_usuario)
    prod_ref = db.collection("tienda_productos").document(id_producto)

    user_doc = user_ref.get()
    prod_doc = prod_ref.get()

    if not user_doc.exists:
        return jsonify({"ok": False, "mensaje": "Usuario no existe"}), 404

    if not prod_doc.exists:
        return jsonify({"ok": False, "mensaje": "Producto no existe"}), 404

    user = user_doc.to_dict()
    product = prod_doc.to_dict()

    # 1. Ya canjeado
    if product.get("canjeado", False):
        return jsonify({
            "ok": False,
            "mensaje": "Este producto ya fue canjeado"
        }), 400

    tokens_usuario = user.get("tokens", 0)
    costo = product.get("costo", 0)

    # 2. Tokens insuficientes
    if tokens_usuario < costo:
        return jsonify({
            "ok": False,
            "mensaje": "Tokens insuficientes",
            "tokens_disponibles": tokens_usuario
        }), 400

    # 3. Transacción segura
    @db.transactional
    def realizar_compra(transaction):
        transaction.update(user_ref, {
            "tokens": tokens_usuario - costo
        })

        transaction.update(prod_ref, {
            "canjeado": True,
            "id_usuario": id_usuario
        })

    transaction = db.transaction()
    realizar_compra(transaction)

    return jsonify({
        "ok": True,
        "mensaje": "Producto canjeado correctamente",
        "tokens_restantes": tokens_usuario - costo
    })

# Renovar producto
@compras_bp.post("/renovar")
def renovar():
    if not verificar_token(request):
        return jsonify({"error": "Token inválido"}), 401

    data = request.json
    id_usuario = data.get("id_usuario")
    id_producto = data.get("id_producto")

    if not id_usuario or not id_producto:
        return jsonify({"error": "Datos incompletos"}), 400

    user_ref = db.collection("usuarios").document(id_usuario)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return jsonify({"error": "Usuario no existe"}), 404

    usuario = user_doc.to_dict()

    prod_ref = db.collection("tienda_productos").document(id_producto)
    prod_doc = prod_ref.get()

    if not prod_doc.exists:
        return jsonify({"error": "Producto no existe"}), 404

    producto = prod_doc.to_dict()

    costo = producto.get("costo")
    dias = producto.get("dias_vigencia")

    if usuario["monedas"] < costo:
        return jsonify({"error": "No tienes suficientes monedas"}), 403

    # Pagar renovación
    user_ref.update({"monedas": usuario["monedas"] - costo})

    fecha_compra = datetime.utcnow()
    fecha_venc = fecha_compra + timedelta(days=dias)

    compras_ref = db.collection("usuarios_productos")
    compras = compras_ref.where("id_usuario", "==", id_usuario)\
                         .where("id_producto", "==", id_producto).stream()

    found = False
    for doc in compras:
        found = True
        compras_ref.document(doc.id).update({
            "fecha_compra": fecha_compra,
            "fecha_vencimiento": fecha_venc
        })

    if not found:
        compras_ref.add({
            "id_usuario": id_usuario,
            "id_producto": id_producto,
            "fecha_compra": fecha_compra,
            "fecha_vencimiento": fecha_venc
        })

    return jsonify({"mensaje": "Renovación exitosa"}), 200
