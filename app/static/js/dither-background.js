class DitherBackground {
    constructor(container, options = {}) {
        this.container = container;

        // Default options matching original Dither implementation
        this.options = {
            pixelSize: 8.0,              // Medium-sized pixels for clear dithering
            colorNum: 4,                 // Perfect balance of contrast and smoothness
            waveSpeed: 1.2,              // Slightly faster for more visible movement
            waveFrequency: 1.5,          // More detailed patterns
            waveAmplitude: 2.8,          // Much stronger base animation
            waveColor: [0, 0, 0],
            enableMouseInteraction: true,
            mouseRadius: 0.5,            // Large interactive area
            disableAnimation: false,
            ...options
        };

        this.mouse = new THREE.Vector2(0, 0);
        this.animationFrame = null;
        this.eventListeners = {};

        this.init();
    }

    init() {
        // Scene setup
        this.scene = new THREE.Scene();
        this.camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

        // Renderer with better settings for crisp rendering
        this.renderer = new THREE.WebGLRenderer({
            antialias: false,
            alpha: false,
            powerPreference: "high-performance"
        });
        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(1);

        // Ensure renderer fills viewport completely
        this.renderer.domElement.style.position = 'fixed';
        this.renderer.domElement.style.top = '0';
        this.renderer.domElement.style.left = '0';
        this.renderer.domElement.style.width = '100vw';
        this.renderer.domElement.style.height = '100vh';
        this.renderer.domElement.style.zIndex = '-1';
        this.renderer.domElement.style.pointerEvents = 'none';

        this.container.appendChild(this.renderer.domElement);

        // Create authentic dither shader material
        this.createShaderMaterial();

        // Create full-screen quad
        const geometry = new THREE.PlaneGeometry(2, 2);
        this.mesh = new THREE.Mesh(geometry, this.material);
        this.scene.add(this.mesh);

        this.camera.position.z = 1;

        // Event listeners
        this.setupEventListeners();

        // Start animation
        this.animate();
    }

    createShaderMaterial() {
        const vertexShader = `
      varying vec2 vUv;
      void main() {
        vUv = uv;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;

        const fragmentShader = `
      precision highp float;
      uniform vec2 u_resolution;
      uniform float u_time;
      uniform vec2 u_mouse;
      uniform float u_pixelSize;
      uniform float u_colorNum;
      uniform float u_waveSpeed;
      uniform float u_waveFrequency;
      uniform float u_waveAmplitude;
      uniform int u_enableMouseInteraction;
      uniform float u_mouseRadius;
      varying vec2 vUv;
      
      vec3 mod289(vec3 x) {
        return x - floor(x * (1.0 / 289.0)) * 289.0;
      }
      
      vec2 mod289(vec2 x) {
        return x - floor(x * (1.0 / 289.0)) * 289.0;
      }
      
      vec3 permute(vec3 x) {
        return mod289(((x*34.0)+1.0)*x);
      }
      
      float snoise(vec2 v) {
        const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
        vec2 i  = floor(v + dot(v, C.yy) );
        vec2 x0 = v -   i + dot(i, C.xx);
        vec2 i1;
        i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
        vec4 x12 = x0.xyxy + C.xxzz;
        x12.xy -= i1;
        i = mod289(i);
        vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 )) + i.x + vec3(0.0, i1.x, 1.0 ));
        vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy), dot(x12.zw,x12.zw)), 0.0);
        m = m*m;
        m = m*m;
        vec3 x = 2.0 * fract(p * C.www) - 1.0;
        vec3 h = abs(x) - 0.5;
        vec3 ox = floor(x + 0.5);
        vec3 a0 = x - ox;
        m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
        vec3 g;
        g.x  = a0.x  * x0.x  + h.x  * x0.y;
        g.yz = a0.yz * x12.xz + h.yz * x12.yw;
        return 130.0 * dot(m, g);
      }
      
      float fbm(vec2 p) {
        float value = 0.0;
        float amplitude = 0.5;
        float frequency = 1.0;
        
        for(int i = 0; i < 4; i++) {
          value += amplitude * snoise(p * frequency);
          amplitude *= 0.5;
          frequency *= 2.0;
        }
        
        return value;
      }
      
      float getBayerValue(ivec2 pos) {
        int bayerMatrix[64] = int[64](
          0, 32, 8, 40, 2, 34, 10, 42,
          48, 16, 56, 24, 50, 18, 58, 26,
          12, 44, 4, 36, 14, 46, 6, 38,
          60, 28, 52, 20, 62, 30, 54, 22,
          3, 35, 11, 43, 1, 33, 9, 41,
          51, 19, 59, 27, 49, 17, 57, 25,
          15, 47, 7, 39, 13, 45, 5, 37,
          63, 31, 55, 23, 61, 29, 53, 21
        );
        
        int x = pos.x % 8;
        int y = pos.y % 8;
        return float(bayerMatrix[y * 8 + x]) / 64.0;
      }
      
      vec3 orderedDither(vec2 screenPos, vec3 color) {
        ivec2 pixelPos = ivec2(floor(screenPos / u_pixelSize));
        float threshold = getBayerValue(pixelPos);
        
        float levels = u_colorNum - 1.0;
        vec3 quantized = floor(color * levels + threshold) / levels;
        
        return clamp(quantized, 0.0, 1.0);
      }
      
      void main() {
        vec2 screenCoord = gl_FragCoord.xy;
        vec2 uv = vUv;
        
        // Enhanced base noise with multiple layers
        vec2 noiseCoord = uv * u_waveFrequency + u_time * u_waveSpeed * 0.15;
        float noise = fbm(noiseCoord);
        
        // Add multiple animated sine/cosine waves for dynamic patterns
        noise += 0.6 * sin(u_time * 0.8 + uv.x * 12.0 + uv.y * 6.0);
        noise += 0.4 * cos(u_time * 0.6 + uv.y * 15.0 - uv.x * 8.0);
        noise += 0.3 * sin(u_time * 1.2 + length(uv - 0.5) * 20.0);
        
        // Add rotating spiral pattern
        float angle = atan(uv.y - 0.5, uv.x - 0.5);
        float radius = length(uv - 0.5);
        noise += 0.4 * sin(angle * 4.0 + u_time * 2.0 + radius * 10.0);
        
        // Add breathing effect
        noise += 0.3 * sin(u_time * 1.5) * (1.0 - radius * 2.0);
        
        if (u_enableMouseInteraction == 1) {
          vec2 mouseUv = u_mouse / u_resolution;
          mouseUv.y = 1.0 - mouseUv.y;
          float mouseDist = distance(uv, mouseUv);
          float mouseInfluence = smoothstep(u_mouseRadius, 0.0, mouseDist);
          noise += mouseInfluence * 2.0;
        }
        
        // Apply amplitude with stronger base intensity
        noise = noise * u_waveAmplitude * 0.35 + 0.6;
        
        // More dramatic gradients
        float verticalGradient = 1.0 - uv.y * 0.2;
        float radialGradient = 1.0 - length(uv - 0.5) * 0.3;
        
        float intensity = noise * verticalGradient * radialGradient;
        intensity = clamp(intensity, 0.0, 1.0);
        
        vec3 color = vec3(intensity);
        color = orderedDither(screenCoord, color);
        
        float luminance = dot(color, vec3(0.299, 0.587, 0.114));
        color = vec3(step(0.5, luminance));
        
        gl_FragColor = vec4(color, 1.0);
      }
    `;

        this.material = new THREE.ShaderMaterial({
            vertexShader: vertexShader,
            fragmentShader: fragmentShader,
            uniforms: {
                u_time: { value: 0 },
                u_resolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
                u_mouse: { value: new THREE.Vector2(0, 0) },
                u_pixelSize: { value: this.options.pixelSize },
                u_colorNum: { value: this.options.colorNum },
                u_waveSpeed: { value: this.options.waveSpeed },
                u_waveFrequency: { value: this.options.waveFrequency },
                u_waveAmplitude: { value: this.options.waveAmplitude },
                u_enableMouseInteraction: { value: this.options.enableMouseInteraction ? 1 : 0 },
                u_mouseRadius: { value: this.options.mouseRadius }
            },
            transparent: false
        });
    }

    setupEventListeners() {
        const onMouseMove = (event) => {
            if (!this.options.enableMouseInteraction) return;

            this.mouse.x = event.clientX;
            this.mouse.y = event.clientY;
            this.material.uniforms.u_mouse.value.copy(this.mouse);
        };

        const onWindowResize = () => {
            const width = window.innerWidth;
            const height = window.innerHeight;

            this.renderer.setSize(width, height);
            this.material.uniforms.u_resolution.value.set(width, height);

            this.renderer.domElement.style.width = '100vw';
            this.renderer.domElement.style.height = '100vh';
        };

        window.addEventListener('mousemove', onMouseMove, false);
        window.addEventListener('resize', onWindowResize, false);

        this.eventListeners = {
            mousemove: onMouseMove,
            resize: onWindowResize
        };
    }

    animate() {
        if (!this.options.disableAnimation) {
            this.material.uniforms.u_time.value += 0.016;
        }

        this.renderer.render(this.scene, this.camera);
        this.animationFrame = requestAnimationFrame(() => this.animate());
    }

    updateOptions(newOptions) {
        Object.assign(this.options, newOptions);

        if (this.material) {
            this.material.uniforms.u_pixelSize.value = this.options.pixelSize;
            this.material.uniforms.u_colorNum.value = this.options.colorNum;
            this.material.uniforms.u_waveSpeed.value = this.options.waveSpeed;
            this.material.uniforms.u_waveFrequency.value = this.options.waveFrequency;
            this.material.uniforms.u_waveAmplitude.value = this.options.waveAmplitude;
            this.material.uniforms.u_enableMouseInteraction.value = this.options.enableMouseInteraction ? 1 : 0;
            this.material.uniforms.u_mouseRadius.value = this.options.mouseRadius;
        }
    }

    destroy() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
        }

        Object.entries(this.eventListeners).forEach(([event, handler]) => {
            window.removeEventListener(event, handler);
        });

        if (this.material) this.material.dispose();
        if (this.mesh) {
            this.mesh.geometry.dispose();
            this.scene.remove(this.mesh);
        }
        if (this.renderer) {
            this.container.removeChild(this.renderer.domElement);
            this.renderer.dispose();
        }
    }
}

window.DitherBackground = DitherBackground;
