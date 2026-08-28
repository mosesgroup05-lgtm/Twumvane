// avatar.js
// Kinyarwanda word -> animation clip name inside twumvane.glb.
// Add a new line here every time you animate a new sign in Blender
// and re-export avatar.glb (clip name must match exactly, case-sensitive).
const SIGN_ANIMATIONS = {
    'muraho': 'Muraho neza',
    'amazina': 'Amazina',
    'mama': 'Mama',
    'papa': 'Papa',
    'nitwa': 'Nitwa',
    'ntuye': 'Ntuye',
    'ndagukunda': 'Ndagukunda',
    'nshaka': 'Nshaka',
    'imana': 'Imana'
};

const AvatarPlayer = (function () {
    let scene, camera, renderer, mixer, canvas, clock;
    let currentAction = null;
    let onFinishedCallback = null;
    let ready = false;
    let pendingWord = null;
    let gltfAnimations = [];
    let playbackSpeed = 1;

    function normalize(word) {
        return (word || '').trim().toLowerCase();
    }

    function has(word) {
        return !!SIGN_ANIMATIONS[normalize(word)];
    }

    function init(canvasEl, modelUrl, callbacks = {}) {
        canvas = canvasEl;
        clock = new THREE.Clock();

        scene = new THREE.Scene();

        const initialWidth = canvas.clientWidth || canvas.parentElement?.clientWidth || 300;
        const initialHeight = canvas.clientHeight || canvas.parentElement?.clientHeight || 200;

        camera = new THREE.PerspectiveCamera(
            35,
            initialWidth / (initialHeight || 1),
            0.1,
            100
        );
        camera.position.set(0, 1.4, 2.3);
        camera.lookAt(0, 1.25, 0);

        try {
            renderer = new THREE.WebGLRenderer({
                canvas,
                alpha: true,
                antialias: true,
                powerPreference: 'default',
                failIfMajorPerformanceCaveat: false
            });
        } catch (e1) {
            console.warn('Primary WebGLRenderer creation failed, retrying basic fallback:', e1);
            try {
                renderer = new THREE.WebGLRenderer({
                    canvas,
                    alpha: true,
                    antialias: false,
                    failIfMajorPerformanceCaveat: false
                });
            } catch (e2) {
                console.error('WebGLRenderer initialization failed:', e2);
                if (callbacks.onError) {
                    callbacks.onError(new Error('WebGL is not enabled. In Edge/browser settings, enable "Use graphics acceleration when available" (edge://settings/system).'));
                }
                return;
            }
        }

        if (THREE.sRGBEncoding) {
            renderer.outputEncoding = THREE.sRGBEncoding;
        }
        renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        renderer.setSize(initialWidth, initialHeight, false);

        scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.3));
        const dir = new THREE.DirectionalLight(0xffffff, 0.9);
        dir.position.set(1, 2, 2);
        scene.add(dir);

        const loader = new THREE.GLTFLoader();

        const loadWithFallback = (url, isRetry = false) => {
            loader.load(
                url,
                (gltf) => {
                    scene.add(gltf.scene);
                    gltfAnimations = gltf.animations || [];
                    mixer = new THREE.AnimationMixer(gltf.scene);
                    mixer.addEventListener('finished', () => {
                        if (onFinishedCallback) onFinishedCallback();
                    });
                    ready = true;

                    // Adjust sizing once model is mounted
                    onResize();

                    if (callbacks.onLoad) callbacks.onLoad(gltf);

                    if (pendingWord) {
                        const w = pendingWord;
                        pendingWord = null;
                        playWord(w, onFinishedCallback);
                    }
                },
                (xhr) => {
                    if (callbacks.onProgress) {
                        const percent = xhr.total > 0 ? Math.round((xhr.loaded / xhr.total) * 100) : 0;
                        callbacks.onProgress(percent, xhr.loaded, xhr.total);
                    }
                },
                (err) => {
                    console.warn(`Failed loading model from ${url}:`, err);
                    if (!isRetry && url !== '/trsl/models/twumvane.glb') {
                        console.log('Retrying model load with /trsl/models/twumvane.glb...');
                        loadWithFallback('/trsl/models/twumvane.glb', true);
                    } else {
                        console.error('Avatar failed to load completely:', err);
                        if (callbacks.onError) callbacks.onError(new Error('Could not download 3D avatar model (network error or blocked).'));
                    }
                }
            );
        };

        loadWithFallback(modelUrl);

        window.addEventListener('resize', onResize);
        window.addEventListener('load', onResize);

        if (window.ResizeObserver) {
            const ro = new ResizeObserver(() => onResize());
            ro.observe(canvas);
            if (canvas.parentElement) ro.observe(canvas.parentElement);
        }

        // Trigger onResize at frame intervals to ensure parent CSS flexbox/grid layout is rendered
        requestAnimationFrame(onResize);
        setTimeout(onResize, 100);
        setTimeout(onResize, 500);

        animate();
    }

    function onResize() {
        if (!renderer || !canvas || !camera) return;
        const width = canvas.clientWidth || canvas.parentElement?.clientWidth || 0;
        const height = canvas.clientHeight || canvas.parentElement?.clientHeight || 0;
        if (width === 0 || height === 0) return;

        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
    }

    function animate() {
        requestAnimationFrame(animate);
        const delta = clock ? clock.getDelta() : 0.016;
        if (mixer) mixer.update(delta);
        if (renderer && scene && camera) renderer.render(scene, camera);
    }

    // Returns true if this word has an avatar animation and playback started.
    function playWord(word, onFinished) {
        const clipName = SIGN_ANIMATIONS[normalize(word)];
        if (!clipName) return false;

        onFinishedCallback = onFinished || null;

        if (!ready) {
            pendingWord = word;
            return true; // will play as soon as the model finishes loading
        }

        const clip = THREE.AnimationClip.findByName(gltfAnimations, clipName);
        if (!clip) {
            console.warn('Animation clip not found in GLB:', clipName);
            return false;
        }

        if (currentAction) currentAction.stop();
        currentAction = mixer.clipAction(clip);
        currentAction.reset();
        currentAction.setLoop(THREE.LoopOnce);
        currentAction.clampWhenFinished = true;
        currentAction.timeScale = playbackSpeed;
        currentAction.play();
        return true;
    }

    // Change how fast the avatar animates (1 = normal speed).
    function setSpeed(speed) {
        playbackSpeed = Math.max(0.1, speed || 1);
        if (currentAction) currentAction.timeScale = playbackSpeed;
    }

    function stop() {
        pendingWord = null;
        if (currentAction) currentAction.stop();
    }

    return { init, has, playWord, stop, setSpeed };
})();