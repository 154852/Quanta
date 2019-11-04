import os
from flask import Flask
from . import core

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # SECRET_KEY="dc4f1c32e9c5924910e61dd97faf88fe3a623fbe42c9a496352709b40978cb31"
    )

    app.config["TEMPLATES_AUTO_RELOAD"] = True
    
    if test_config is None: app.config.from_pyfile("config.py", silent=True)
    else: app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError: pass

    app.register_blueprint(core.bp)

    return app

# if __name__ == "__main__":
app = create_app()