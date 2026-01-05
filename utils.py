from flask import jsonify
from datetime import datetime
from config import API_TOKEN
from db import db

def verificar_token(req):
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {API_TOKEN}"

def actualizar_productos_usuario(id_usuario):
    ahora = datetime.utcnow()
    coleccion = db.collection("usuarios_productos")
    compras = coleccion.where("id_usuario", "==", id_usuario).stream()

    productos_vigentes = []
    premium_activo = False

    for doc in compras:
        data = doc.to_dict()

        # Expirado → eliminar
        if data.get("fecha_vencimiento") and data["fecha_vencimiento"] < ahora:
            coleccion.document(doc.id).delete()
            continue

        productos_vigentes.append(data)

        # Detectar si es premium
        prod_doc = db.collection("tienda_productos").document(
            data["id_producto"]
        ).get()

        if prod_doc.exists and prod_doc.to_dict().get("tipo") == "premium":
            premium_activo = True

    # Actualizar tipo de cuenta
    user_ref = db.collection("usuarios").document(id_usuario)
    user_ref.update({"tipo_cuenta": "premium" if premium_activo else "free"})

    return productos_vigentes
