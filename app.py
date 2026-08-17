"""
TWUMVANE - Rwanda Sign Language Avatar Platform
Serves the 3D avatar sign-language translator on http://localhost:5000
"""
import os

from flask import Flask, render_template, send_from_directory

# ─── Create the main Flask app ───────────────────────────────────────────────
app = Flask(__name__, template_folder='templates')

TRSL_FRONTEND = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TRSL', 'frontend')


# ──────────────────────────────────────────────────────────────────────────────
#  Routes
# ──────────────────────────────────────────────────────────────────────────────
@app.route('/')
def welcome():
    """Serve the welcome page."""
    return render_template('welcome.html')


@app.route('/trsl')
@app.route('/trsl/')
def trsl_index():
    """Serve the 3D avatar translator."""
    return send_from_directory(TRSL_FRONTEND, 'index.html')


@app.route('/trsl/<path:filename>')
def trsl_static(filename):
    """Serve static assets (avatar.js, models, etc.)."""
    return send_from_directory(TRSL_FRONTEND, filename)


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
    print("    * 3D Avatar     >>  http://localhost:5000/trsl")
    print()
    print("=" * 65)
    print("  [STARTED] Starting server on http://localhost:5000")
    print("=" * 65)
    print()

    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)