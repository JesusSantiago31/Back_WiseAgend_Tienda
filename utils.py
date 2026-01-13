from flask import jsonify
from datetime import datetime
from config import API_TOKEN
from db import db

import firebase_admin
from firebase_admin import auth as firebase_auth

def verificar_token(request):
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    id_token = auth_header.split(" ")[1]

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        return decoded_token["uid"]
    except Exception as e:
        print("ERROR VERIFICANDO TOKEN:", e)
        return None


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


from datetime import datetime
from db import db

def obtener_ids_productos_vigentes(id_usuario):
    ahora = datetime.utcnow()
    coleccion = db.collection("usuarios_productos")

    compras = coleccion.where("id_usuario", "==", id_usuario).stream()

    ids_productos = []

    for doc in compras:
        data = doc.to_dict()

        # Ignorar productos vencidos
        if data.get("fecha_vencimiento") and data["fecha_vencimiento"] < ahora:
            continue

        # SOLO EL ID
        if "id_producto" in data:
            ids_productos.append(data["id_producto"])

    return ids_productos

