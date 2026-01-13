from flask import Blueprint, request, jsonify
from db import db
from utils import verificar_token

productos_bp = Blueprint("productos_bp", __name__)


# =====================================================
# GET /productos — Obtener todos los productos
# =====================================================
@productos_bp.get("/productos")
def obtener_productos():
    productos_ref = db.collection('tienda_productos')
    docs = productos_ref.stream()

    productos = []
    for doc in docs:
        data = doc.to_dict()
        data["id_producto"] = doc.id
        productos.append(data)

    return jsonify({"productos": productos}), 200


# =====================================================
# POST /productos/agregar — Agregar productos
# =====================================================
@productos_bp.post("/productos/agregar")
def agregar_productos():
    user_id = verificar_token(request)

    if not user_id:
        return jsonify({"error": "Token inválido"}), 401

    user_doc = db.collection("usuarios").document(user_id).get()
    if not user_doc.exists or user_doc.to_dict().get("rol") != "admin":
        return jsonify({"error": "No autorizado"}), 403

    body = request.get_json()

    if not body or "productos" not in body:
        return jsonify({"error": "Debe enviar un arreglo 'productos'"}), 400

    productos = body["productos"]

    if not isinstance(productos, list) or not productos:
        return jsonify({"error": "La lista de productos no puede estar vacía"}), 400

    productos_ref = db.collection("tienda_productos")

    productos_agregados = []
    errores = []

    for p in productos:
        obligatorios = ["id_producto", "nombre", "costo", "tipo"]
        faltan = [campo for campo in obligatorios if campo not in p]

        if faltan:
            errores.append({
                "producto": p,
                "error": f"Faltan campos requeridos: {', '.join(faltan)}"
            })
            continue

        id_producto = p["id_producto"]

        if productos_ref.document(id_producto).get().exists:
            errores.append({
                "id_producto": id_producto,
                "error": "El producto ya existe"
            })
            continue

        try:
            costo = int(p.get("costo", 0))
        except (TypeError, ValueError):
            errores.append({
                "id_producto": id_producto,
                "error": "Costo inválido"
            })
            continue

        nuevo_producto = {
            "nombre": p.get("nombre"),
            "descripcion": p.get("descripcion", ""),
            "costo": costo,
            "tipo": p.get("tipo"),
            "category": p.get("category", ""),
            "premium": bool(p.get("premium", False)),
            "icono": p.get("icono", ""),
            "canjeado": bool(p.get("canjeado", False)),
            "vencimiento": p.get("vencimiento", 0),
        }

        productos_ref.document(id_producto).set(nuevo_producto)
        productos_agregados.append(id_producto)

    return jsonify({
        "mensaje": "Proceso completado",
        "productos_agregados": productos_agregados,
        "errores": errores
    }), 200
