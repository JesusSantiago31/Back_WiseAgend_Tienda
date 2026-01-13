from flask import Blueprint, jsonify, request
from utils import verificar_token, actualizar_productos_usuario, obtener_ids_productos_vigentes
from datetime import datetime, timezone
from db import db

usuarios_bp = Blueprint("usuarios_bp", __name__)


# EN TU BACKEND (Python)

@usuarios_bp.get("/usuario/productos")
def productos_usuario():
    user_id = verificar_token(request)
    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    productos = actualizar_productos_usuario(user_id)

    # 🔥 CORRECCIÓN: Convertir objetos datetime a string
    for p in productos:
        if "fecha_compra" in p and p["fecha_compra"]:
            p["fecha_compra"] = p["fecha_compra"].isoformat()
        
        if "fecha_vencimiento" in p and p["fecha_vencimiento"]:
            p["fecha_vencimiento"] = p["fecha_vencimiento"].isoformat()

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
        if premium_venc and premium_venc < datetime.now(timezone.utc):
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

@usuarios_bp.get("/usuario/historial")
def historial_usuario():
    user_id = verificar_token(request)
    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    # Obtenemos TODOS los documentos de 'usuarios_productos' para este usuario
    # (incluso los vencidos)
    coleccion = db.collection("usuarios_productos")
    docs = coleccion.where("id_usuario", "==", user_id).stream()

    historial = []
    now = datetime.now(timezone.utc)

    def _to_dt(v):
        if not v:
            return None
        if isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(v)
        except Exception:
            return None

    product_ids = set()

    for doc in docs:
        data = doc.to_dict() or {}

        id_producto = data.get("id_producto")
        id_usuario = data.get("id_usuario")
        fecha_compra_raw = data.get("fecha_compra")
        fecha_venc_raw = data.get("fecha_vencimiento")

        fecha_compra_dt = _to_dt(fecha_compra_raw)
        fecha_venc_dt = _to_dt(fecha_venc_raw)

        # Preparar salida usando solo campos de la BD
        fecha_compra_out = fecha_compra_dt.isoformat() if fecha_compra_dt else (str(fecha_compra_raw) if fecha_compra_raw else None)
        fecha_venc_out = fecha_venc_dt.isoformat() if fecha_venc_dt else (str(fecha_venc_raw) if fecha_venc_raw else None)

        es_vigente = False
        if fecha_venc_dt:
            try:
                es_vigente = fecha_venc_dt > now
            except Exception:
                es_vigente = False

        item = {
            "id_compra": doc.id,
            "id_usuario": id_usuario,
            "id_producto": id_producto,
            "fecha_compra": fecha_compra_out,
            "fecha_vencimiento": fecha_venc_out,
            "es_vigente": es_vigente
        }

        # Guardamos id_producto para fetch masivo
        if id_producto:
            product_ids.add(id_producto)

        historial.append(item)

    # Obtener datos de productos en una sola pasada (evitar N+1)
    products_map = {}
    for pid in product_ids:
        try:
            pdoc = db.collection("tienda_productos").document(pid).get()
            if pdoc.exists:
                pd = pdoc.to_dict() or {}
                products_map[pid] = {
                    "id": pdoc.id,
                    "nombre": pd.get("nombre"),
                    "descripcion": pd.get("descripcion"),
                    "costo": pd.get("costo"),
                    "tipo": pd.get("tipo"),
                    "category": pd.get("category"),
                    "icono": pd.get("icono"),
                    "premium": bool(pd.get("premium", False))
                }
            else:
                products_map[pid] = None
        except Exception as e:
            print("ERROR fetching product", pid, e)
            products_map[pid] = None

    # Adjuntar datos del producto a cada item (si disponible)
    for item in historial:
        pid = item.get("id_producto")
        item["producto"] = products_map.get(pid)

    # Ordenar por fecha de compra descendente (el más reciente primero)
    historial.sort(key=lambda x: x.get("fecha_compra") or "", reverse=True)

    return jsonify({"historial": historial}), 200