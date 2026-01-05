from flask import Flask
from routes.productos_routes import productos_bp
from routes.usuarios_routes import usuarios_bp
from routes.recargas_routes import recargas_bp
from routes.compras_routes import compras_bp
from flask_cors import CORS



app = Flask(__name__)
CORS(app)
# Registrar blueprints
app.register_blueprint(productos_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(recargas_bp)
app.register_blueprint(compras_bp)


if __name__ == "__main__":
    app.run(debug=True)
