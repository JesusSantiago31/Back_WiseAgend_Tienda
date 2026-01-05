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

    # Validación del token
    if not verificar_token(request):
        return jsonify({"error": "Token inválido"}), 401

    body = request.get_json()

    if not body or "productos" not in body:
        return jsonify({"error": "Debe enviar un arreglo 'productos'"}), 400

    productos = body["productos"]

    if not isinstance(productos, list) or len(productos) == 0:
        return jsonify({"error": "La lista de productos no puede estar vacía"}), 400

    productos_ref = db.collection("tienda_productos")

    productos_agregados = []
    errores = []

    for p in productos:

        # Validación de campos obligatorios
        obligatorios = ["id_producto", "nombre", "costo", "tipo"]
        faltan = [campo for campo in obligatorios if campo not in p]

        if faltan:
            errores.append({
                "producto": p,
                "error": f"Faltan campos requeridos: {', '.join(faltan)}"
            })
            continue

        id_producto = p["id_producto"]

        # Verificar si ya existe
        doc = productos_ref.document(id_producto).get()
        if doc.exists:
            errores.append({
                "id_producto": id_producto,
                "error": "El producto ya existe"
            })
            continue

        # Construcción del objeto final
        nuevo_producto = {
            "nombre": p.get("nombre"),
            "descripcion": p.get("descripcion", ""),
            "costo": p.get("costo", 0),
            "tipo": p.get("tipo"),                      # recompensa / premium / etc.
            "category": p.get("category", ""),
            "premium": p.get("premium", False),
            "icono": p.get("icono", ""),
            "canjeado": p.get("canjeado", False),
            "vencimieto": p.get("vencimiento", 0),
                # homogeneización con backend
        }

        # Guardar en Firestore
        productos_ref.document(id_producto).set(nuevo_producto)
        productos_agregados.append(id_producto)

    return jsonify({
        "mensaje": "Proceso completado",
        "productos_agregados": productos_agregados,
        "errores": errores
    }), 200
