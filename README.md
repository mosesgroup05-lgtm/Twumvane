# TWUMVANE — Rwanda Sign Language Avatar Platform

TWUMVANE is a web-based platform for Rwanda Sign Language (RSL) support. It combines a Flask backend with a browser-based 3D avatar that performs sign-language animations from text you type.

## Main Features

- Flask-powered web app
- 3D sign-language avatar rendered with Three.js (GLTF)
- Client-side translation: type a Kinyarwanda word or sentence and the avatar signs each word it knows
- Word chips showing the animated sign sequence
- Recent translation history (stored locally in your browser)

## Technologies Used

- Python
- Flask
- HTML5 / CSS3 / JavaScript
- Three.js (via CDN)
- GLTF 3D avatar model

## Project Structure

```text
TWUMVANE/
├── app.py                  # Main Flask application entry point
├── run_twumvane.bat       # Windows batch launcher
├── run_twumvane.ps1       # PowerShell launcher
├── templates/             # Welcome page template
└── TRSL/
    └── frontend/          # 3D avatar web interface
        ├── index.html     # Avatar translator page
        ├── avatar.js      # Avatar player + sign animation registry
        └── models/        # 3D avatar model (twumvane.glb)
```

## Prerequisites

- Python 3.8 or newer
- pip installed
- Windows PowerShell or Command Prompt

## First-Time Setup

Open a terminal in the project root and follow these steps.

### 1. Create a virtual environment

```powershell
py -m venv .venv
```

### 2. Activate the virtual environment

In PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 3. Install dependencies

```powershell
pip install flask flask-cors Werkzeug python-dotenv
```

## How to Run the Project

### Option 1: Run directly with Python

From the project root:

```powershell
py app.py
```

Then open your browser at:

- http://localhost:5000/ — Welcome page
- http://localhost:5000/trsl — 3D avatar translator

### Option 2: Use the Windows launcher

- Double-click the batch file: run_twumvane.bat
- Or run it from PowerShell: .\run_twumvane.ps1

## Default Application Routes

- / - Welcome page
- /trsl - 3D avatar translator

## Adding New Avatar Signs

The avatar's animated signs are registered in `TRSL/frontend/avatar.js` under the `SIGN_ANIMATIONS` map. Each entry maps a Kinyarwanda word to an animation clip name inside `twumvane.glb` (the clip name must match exactly, case-sensitive):

```js
const SIGN_ANIMATIONS = {
    'muraho': 'Muraho neza',
    'amazina': 'Amazina',
    // add new signs here after re-exporting the model from Blender
};
```

## Notes

- No internet connection is required for the avatar itself; Three.js and fonts load from CDN.
- Translation happens entirely in the browser using the sign registry above.
