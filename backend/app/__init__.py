from flask import Flask
from .config import Config
from .extensions import db, migrate, jwt, cors

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # register blueprints
    from .routes.auth import auth_bp
    from .routes.users import users_bp
    from .routes.admin_users import admin_users_bp

    from .routes.brands import brands_bp
    from .routes.laptops import laptops_bp
    from .routes.imports import imports_bp
    from .routes.criteria import criteria_bp
    from .routes.evaluations import evaluations_bp
    from .routes.orders import orders_bp
    from .routes.reviews import reviews_bp
    from .routes.chat import chat_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(admin_users_bp, url_prefix="/api/admin")

    app.register_blueprint(brands_bp, url_prefix="/api/brands")
    app.register_blueprint(laptops_bp, url_prefix="/api/laptops")
    app.register_blueprint(imports_bp, url_prefix="/api/imports")
    app.register_blueprint(criteria_bp, url_prefix="/api/ahp")
    app.register_blueprint(evaluations_bp, url_prefix="/api/evaluations")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(reviews_bp, url_prefix="/api/reviews")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")

    return app