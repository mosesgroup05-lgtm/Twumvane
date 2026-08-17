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

    function init(canvasEl, modelUrl) {
        canvas = canvasEl;
        clock = new THREE.Clock();

        scene = new THREE.Scene();
        camera = new THREE.PerspectiveCamera(
            35,
            canvas.clientWidth / canvas.clientHeight || 1,
            0.1,
            100
        );
        camera.position.set(0, 1.4, 2.3);
        camera.lookAt(0, 1.25, 0);

        renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: true });
        renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
        renderer.setPixelRatio(window.devicePixelRatio);

        scene.add(new THREE.HemisphereLight(0xffffff, 0x444444, 1.3));
        const dir = new THREE.DirectionalLight(0xffffff, 0.9);
        dir.position.set(1, 2, 2);
        scene.add(dir);

        const loader = new THREE.GLTFLoader();
        loader.load(
            modelUrl,
            (gltf) => {
                scene.add(gltf.scene);
                gltfAnimations = gltf.animations;
                mixer = new THREE.AnimationMixer(gltf.scene);
                mixer.addEventListener('finished', () => {
                    if (onFinishedCallback) onFinishedCallback();
                });
                ready = true;
                if (pendingWord) {
                    const w = pendingWord;
                    pendingWord = null;
                    playWord(w, onFinishedCallback);
                }
            },
            undefined,
            (err) => console.error('Avatar failed to load:', err)
        );

        window.addEventListener('resize', onResize);

        // Watch the canvas itself for size changes — this is what actually
        // fixes the black-screen bug: the canvas starts at 0x0 while its
        // parent has display:none, and a window resize event never fires
        // when the parent later becomes visible. ResizeObserver catches
        // that transition directly.
        if (window.ResizeObserver) {
            const ro = new ResizeObserver(() => onResize());
            ro.observe(canvas);
        }

        animate();
    }

    function onResize() {
        if (!renderer || !canvas || !camera) return;
        if (canvas.clientWidth === 0 || canvas.clientHeight === 0) return;
        renderer.setSize(canvas.clientWidth, canvas.clientHeight, false);
        camera.aspect = canvas.clientWidth / canvas.clientHeight;
        camera.updateProjectionMatrix();
    }

    function animate() {
        requestAnimationFrame(animate);
        const delta = clock.getDelta();
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