"""
Aura Jewels - Production WebAR Flask Backend
--------------------------------------------
Features:
1. Dynamic 3D Model & Fallback Detection API.
2. WebAR Marker Configuration & Asset Delivery.
3. Enhanced Security Headers & CORS for WebAR Camera Access.
4. Production Logging, Performance Caching & Error Handlers.
"""

import os
import sys
import logging
from datetime import datetime
from flask import (
    Flask, 
    render_template, 
    jsonify, 
    send_from_directory, 
    request, 
    make_response
)

# -----------------------------------------------------------------------------
# 1. Flask App Initialization & Configuration
# -----------------------------------------------------------------------------
app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)

# Application Settings
app.config['SECRET_KEY'] = 'aura_jewels_webar_secret_key_2026'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max 16MB file limit
app.config['MODEL_FOLDER'] = os.path.join(app.static_folder, 'models')
app.config['MODEL_FILENAME'] = 'bangle.glb'

# Configure Production Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('AuraWebAR')

# Ensure Directories Exist
os.makedirs(app.config['MODEL_FOLDER'], exist_ok=True)


# -----------------------------------------------------------------------------
# 2. Security & Performance Middleware Headers
# -----------------------------------------------------------------------------
@app.after_request
def add_security_and_ar_headers(response):
    """
    Appends HTTP headers required for WebAR camera access, cross-origin resource 
    sharing (CORS), and performance caching.
    """
    # Allow camera permissions across contexts
    response.headers['Permissions-Policy'] = "camera=(self), microphone=()"
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    
    # Disable strict caching for dynamic HTML templates to ensure fresh WebAR assets
    if request.path in ['/', '/tryon']:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    else:
        # Cache static assets (images, 3D glb models) for 1 hour
        response.headers['Cache-Control'] = 'public, max-age=3600'

    return response


# -----------------------------------------------------------------------------
# 3. Product & WebAR Configuration Data
# -----------------------------------------------------------------------------
PRODUCT_DATA = {
    "id": "bangle-kundan-01",
    "name": "Royal Velvet & Kundan Bangle Chura Set",
    "price": "₹4,999",
    "original_price": "₹8,999",
    "discount": "44% OFF",
    "currency": "INR",
    "colors": {
        "primary": "#BE185D",  # Deep Pink
        "secondary": "#D4AF37" # Gold
    },
    "description": "Handcrafted traditional Indian bridal chura set lined with magenta velvet rings and studded with antique gold Kundan polki filigree.",
    "ar_marker": "hiro",
    "rating": "4.9",
    "reviews_count": 128
}


# -----------------------------------------------------------------------------
# 4. Web Routes & Views
# -----------------------------------------------------------------------------
@app.route('/')
def home():
    """
    Landing Page / Storefront Route.
    Renders store catalog and WebAR launch action.
    """
    logger.info(f"Landing page accessed by {request.remote_addr}")
    return render_template('index.html', product=PRODUCT_DATA)


@app.route('/tryon')
def tryon():
    """
    WebAR Interactive Camera View Route.
    Passes WebAR configuration dynamically to the A-Frame frontend.
    """
    logger.info(f"WebAR Try-On session initiated by {request.remote_addr}")
    
    # Check if custom GLB 3D model exists on server
    model_path = os.path.join(app.config['MODEL_FOLDER'], app.config['MODEL_FILENAME'])
    has_custom_model = os.path.isfile(model_path)
    
    return render_template(
        'tryon.html',
        product=PRODUCT_DATA,
        has_custom_model=has_custom_model,
        model_url=f"/static/models/{app.config['MODEL_FILENAME']}"
    )


# -----------------------------------------------------------------------------
# 5. REST APIs & Helper Routes
# -----------------------------------------------------------------------------
@app.route('/api/status', methods=['GET'])
def api_status():
    """
    Health check API endpoint for frontend/mobile monitoring.
    """
    model_path = os.path.join(app.config['MODEL_FOLDER'], app.config['MODEL_FILENAME'])
    model_exists = os.path.isfile(model_path)
    
    return jsonify({
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "product": PRODUCT_DATA["name"],
        "3d_model_available": model_exists,
        "ar_engine": "A-Frame / AR.js"
    }), 200


@app.route('/api/product-details', methods=['GET'])
def api_product_details():
    """
    API endpoint returning product specifications for dynamic UI popups.
    """
    return jsonify({
        "success": True,
        "data": PRODUCT_DATA
    }), 200


@app.route('/static/models/<path:filename>')
def serve_model(filename):
    """
    Dedicated route to serve 3D models with correct MIME types for GLTF/GLB files.
    """
    response = make_response(send_from_directory(app.config['MODEL_FOLDER'], filename))
    if filename.endswith('.glb'):
        response.headers['Content-Type'] = 'model/gltf-binary'
    elif filename.endswith('.gltf'):
        response.headers['Content-Type'] = 'model/gltf+json'
    return response


# -----------------------------------------------------------------------------
# 6. Global Error Handlers
# -----------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    logger.warning(f"404 Error: {request.url}")
    return jsonify({
        "error": "Page or Resource Not Found",
        "status_code": 404
    }), 404


@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 Internal Server Error: {str(e)}")
    return jsonify({
        "error": "Internal Server Error",
        "status_code": 500
    }), 500


# -----------------------------------------------------------------------------
# 7. Application Entrypoint
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    logger.info("Starting Aura Jewels WebAR Server...")
    logger.info("Local WebAR Access: http://127.0.0.1:5000")
    
    # Run server locally (Set debug=False for production)
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )