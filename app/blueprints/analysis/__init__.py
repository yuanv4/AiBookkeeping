from flask import Blueprint

analysis_bp = Blueprint('analysis_bp', __name__, url_prefix='/analysis')

from . import routes 