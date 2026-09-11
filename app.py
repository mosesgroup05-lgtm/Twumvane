"""
TWUMVANE - Rwanda Sign Language Avatar Platform
Serves the 3D avatar sign-language translator on http://localhost:5000
"""
import os
import mimetypes

from flask import Flask, render_template, send_from_directory, redirect

# Register GLTF/GLB mimetypes to ensure proper content-type headers across all browsers
mimetypes.add_type('model/gltf-binary', '.glb')
mimetypes.add_type('model/gltf+json', '.gltf')

# ─── Create the main Flask app ───────────────────────────────────────────────
app = Flask(__name__, template_folder='templates')

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
TRSL_FRONTEND = os.path.join(ROOT_DIR, 'TRSL', 'frontend')

# Ensure logo.jpg is also available directly inside TRSL_FRONTEND
try:
    src_logo = os.path.join(ROOT_DIR, 'logo.jpg')
    dst_logo = os.path.join(TRSL_FRONTEND, 'logo.jpg')
    if os.path.exists(src_logo) and not os.path.exists(dst_logo):
        import shutil
        shutil.copy2(src_logo, dst_logo)
except Exception as e:
    pass


# ──────────────────────────────────────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/')
def welcome():
    """Serve the welcome page."""
    return render_template('welcome.html')


@app.route('/logo.jpg')
def root_logo():
    """Serve the platform logo."""
    return send_from_directory(ROOT_DIR, 'logo.jpg', mimetype='image/jpeg')


@app.route('/favicon.ico')
def root_favicon():
    """Serve favicon."""
    return send_from_directory(ROOT_DIR, 'logo.jpg', mimetype='image/jpeg')


@app.route('/trsl')
def trsl_redirect():
    """Redirect /trsl to /trsl/ so relative asset URLs resolve correctly in all browsers."""
    return redirect('/trsl/', code=302)


@app.route('/trsl/')
def trsl_index():
    """Serve the 3D avatar translator."""
    return send_from_directory(TRSL_FRONTEND, 'index.html')


@app.route('/trsl/<path:filename>')
def trsl_static(filename):
    """Serve static assets (avatar.js, models, logo.jpg, etc.)."""
    return send_from_directory(TRSL_FRONTEND, filename)


# Fallback routes in case a browser requests relative paths from root /
@app.route('/avatar.js')
def root_avatar_js():
    return send_from_directory(TRSL_FRONTEND, 'avatar.js')


@app.route('/models/<path:filename>')
def root_models(filename):
    return send_from_directory(os.path.join(TRSL_FRONTEND, 'models'), filename)


# ──────────────────────────────────────────────────────────────────────────────
#  Main entry point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print()
    print("=" * 65)
    print("  ---  TWUMVANE - Rwanda Sign Language Avatar Platform")
    print("=" * 65)
    print()
    print("  Routes:")
    print("    * Welcome page  >>  http://localhost:5000/")
    print("    * 3D Avatar     >>  http://localhost:5000/trsl/")
    print()
    print("=" * 65)
    print("  [STARTED] Starting server on http://localhost:5000")
    print("=" * 65)
    print()

    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)