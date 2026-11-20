import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { useTheme } from '../theme/useTheme';
import { Shield } from 'lucide-react';

interface CyberShield3DProps {
  interactive?: boolean;
  intensity?: number;
  isScanning?: boolean;
}

export const CyberShield3D: React.FC<CyberShield3DProps> = ({
  interactive = true,
  intensity = 1.0,
  isScanning = false
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const [webglSupported, setWebglSupported] = useState(true);
  const [isHovered, setIsHovered] = useState(false);
  const { palette, colorRatio } = useTheme();

  // References for live update on theme change without tearing down the WebGL context
  const lightsRef = useRef<{
    ambient?: THREE.AmbientLight;
    accentKey?: THREE.PointLight;
    secondaryRim?: THREE.PointLight;
    coreLight?: THREE.PointLight;
  }>({});

  const materialsRef = useRef<{
    shieldMat?: THREE.MeshPhysicalMaterial;
    glassMat?: THREE.MeshPhysicalMaterial;
    coreMat?: THREE.MeshBasicMaterial;
    solidCoreMat?: THREE.MeshStandardMaterial;
    ring1Mat?: THREE.MeshBasicMaterial;
    ring2Mat?: THREE.MeshBasicMaterial;
    particlesMat?: THREE.PointsMaterial;
    nodesMat?: THREE.PointsMaterial;
  }>({});

  const stateRef = useRef({
    isHovered: false,
    isScanning: false,
    scrollOffset: 0
  });

  stateRef.current.isHovered = isHovered;
  stateRef.current.isScanning = isScanning;

  // 1. Initial Scene Setup
  useEffect(() => {
    // Check WebGL availability
    const testCanvas = document.createElement('canvas');
    const gl = testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl');
    if (!gl) {
      setWebglSupported(false);
      return;
    }

    const currentMount = mountRef.current;
    if (!currentMount) return;

    const width = currentMount.clientWidth || 500;
    const height = currentMount.clientHeight || 500;

    // Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100);
    camera.position.z = 7.6;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    currentMount.appendChild(renderer.domElement);

    // Initial Colors from Palette
    const primaryColor = new THREE.Color(palette.primary.hex);
    const secondaryColor = new THREE.Color(palette.secondary.hex);
    const accentColor = new THREE.Color(palette.accent.hex);

    // Lights
    const ambientLight = new THREE.AmbientLight(primaryColor.getHex(), 2.8);
    scene.add(ambientLight);
    lightsRef.current.ambient = ambientLight;

    const accentLight = new THREE.PointLight(accentColor.getHex(), 4.0 * intensity, 22);
    accentLight.position.set(3.2, 3.2, 4.2);
    scene.add(accentLight);
    lightsRef.current.accentKey = accentLight;

    const secondaryRimLight = new THREE.PointLight(secondaryColor.getHex(), 3.5 * intensity, 22);
    secondaryRimLight.position.set(-3.2, -2.5, 3.2);
    scene.add(secondaryRimLight);
    lightsRef.current.secondaryRim = secondaryRimLight;

    const coreLight = new THREE.PointLight(accentColor.getHex(), 2.5, 9);
    coreLight.position.set(0, 0, 0.2);
    scene.add(coreLight);
    lightsRef.current.coreLight = coreLight;

    // Root Group for Shield & Effects
    const rootGroup = new THREE.Group();
    scene.add(rootGroup);

    const shieldGroup = new THREE.Group();
    rootGroup.add(shieldGroup);

    // --- Shield Shape Path ---
    const shape = new THREE.Shape();
    shape.moveTo(0, 2.0);
    shape.quadraticCurveTo(1.45, 1.9, 1.55, 0.85);
    shape.quadraticCurveTo(1.55, -0.65, 0, -2.0);
    shape.quadraticCurveTo(-1.55, -0.65, -1.55, 0.85);
    shape.quadraticCurveTo(-1.45, 1.9, 0, 2.0);

    const extrudeSettings = {
      depth: 0.32,
      bevelEnabled: true,
      bevelSegments: 8,
      steps: 2,
      bevelSize: 0.1,
      bevelThickness: 0.11
    };

    const shieldGeo = new THREE.ExtrudeGeometry(shape, extrudeSettings);
    shieldGeo.center();

    // Metallic Outer Rim Material
    const shieldMat = new THREE.MeshPhysicalMaterial({
      color: primaryColor.clone().offsetHSL(0, 0, 0.08),
      metalness: 0.92,
      roughness: 0.2,
      clearcoat: 0.85,
      clearcoatRoughness: 0.12,
      reflectivity: 0.95
    });
    materialsRef.current.shieldMat = shieldMat;

    const shieldMesh = new THREE.Mesh(shieldGeo, shieldMat);
    shieldGroup.add(shieldMesh);

    // Translucent Inner Crystal Face
    const innerShape = new THREE.Shape();
    innerShape.moveTo(0, 1.72);
    innerShape.quadraticCurveTo(1.25, 1.62, 1.35, 0.75);
    innerShape.quadraticCurveTo(1.35, -0.55, 0, -1.72);
    innerShape.quadraticCurveTo(-1.35, -0.55, -1.35, 0.75);
    innerShape.quadraticCurveTo(-1.25, 1.62, 0, 1.72);

    const innerGeo = new THREE.ShapeGeometry(innerShape);
    innerGeo.center();
    const glassMat = new THREE.MeshPhysicalMaterial({
      color: accentColor,
      transparent: true,
      opacity: 0.32,
      roughness: 0.1,
      metalness: 0.15,
      transmission: 0.65,
      ior: 1.52,
      side: THREE.DoubleSide
    });
    materialsRef.current.glassMat = glassMat;

    const glassMesh = new THREE.Mesh(innerGeo, glassMat);
    glassMesh.position.z = 0.24;
    shieldGroup.add(glassMesh);

    // Luminous Energy Diamond Core (Wireframe + Solid)
    const coreGeo = new THREE.OctahedronGeometry(0.58, 1);
    const coreMat = new THREE.MeshBasicMaterial({
      color: accentColor,
      wireframe: true,
      transparent: true,
      opacity: 0.9
    });
    materialsRef.current.coreMat = coreMat;

    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreMesh.position.z = 0.32;
    shieldGroup.add(coreMesh);

    const solidCoreGeo = new THREE.OctahedronGeometry(0.38, 0);
    const solidCoreMat = new THREE.MeshStandardMaterial({
      color: secondaryColor,
      emissive: accentColor,
      emissiveIntensity: 1.8,
      roughness: 0.15,
      metalness: 0.85
    });
    materialsRef.current.solidCoreMat = solidCoreMat;

    const solidCoreMesh = new THREE.Mesh(solidCoreGeo, solidCoreMat);
    solidCoreMesh.position.z = 0.32;
    shieldGroup.add(solidCoreMesh);

    // Multiple Rotating Orbital Rings
    const ring1Geo = new THREE.TorusGeometry(2.35, 0.024, 16, 100);
    const ring1Mat = new THREE.MeshBasicMaterial({
      color: secondaryColor,
      transparent: true,
      opacity: 0.55
    });
    materialsRef.current.ring1Mat = ring1Mat;
    const ring1Mesh = new THREE.Mesh(ring1Geo, ring1Mat);
    ring1Mesh.rotation.x = Math.PI / 3;
    rootGroup.add(ring1Mesh);

    const ring2Geo = new THREE.TorusGeometry(2.65, 0.018, 16, 100);
    const ring2Mat = new THREE.MeshBasicMaterial({
      color: accentColor,
      transparent: true,
      opacity: 0.65
    });
    materialsRef.current.ring2Mat = ring2Mat;
    const ring2Mesh = new THREE.Mesh(ring2Geo, ring2Mat);
    ring2Mesh.rotation.y = Math.PI / 4;
    ring2Mesh.rotation.x = -Math.PI / 6;
    rootGroup.add(ring2Mesh);

    // Ambient Particle Network Field
    const particleCount = 260;
    const particleGeo = new THREE.BufferGeometry();
    const particlePos = new Float32Array(particleCount * 3);
    for (let i = 0; i < particleCount * 3; i += 3) {
      particlePos[i] = (Math.random() - 0.5) * 8.5;
      particlePos[i + 1] = (Math.random() - 0.5) * 8.5;
      particlePos[i + 2] = (Math.random() - 0.5) * 6.0;
    }
    particleGeo.setAttribute('position', new THREE.BufferAttribute(particlePos, 3));

    const particlesMat = new THREE.PointsMaterial({
      color: accentColor,
      size: 0.045,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending
    });
    materialsRef.current.particlesMat = particlesMat;
    const particleSystem = new THREE.Points(particleGeo, particlesMat);
    rootGroup.add(particleSystem);

    // Floating Network Nodes along Orbital Ring
    const nodeCount = 36;
    const nodePos = new Float32Array(nodeCount * 3);
    for (let i = 0; i < nodeCount; i++) {
      const angle = (i / nodeCount) * Math.PI * 2;
      const radius = 2.45 + (Math.random() - 0.5) * 0.3;
      nodePos[i * 3] = Math.cos(angle) * radius;
      nodePos[i * 3 + 1] = Math.sin(angle) * radius;
      nodePos[i * 3 + 2] = (Math.random() - 0.5) * 0.4;
    }
    const nodeGeo = new THREE.BufferGeometry();
    nodeGeo.setAttribute('position', new THREE.BufferAttribute(nodePos, 3));
    const nodesMat = new THREE.PointsMaterial({
      color: secondaryColor,
      size: 0.08,
      transparent: true,
      opacity: 0.85
    });
    materialsRef.current.nodesMat = nodesMat;
    const nodesMesh = new THREE.Points(nodeGeo, nodesMat);
    rootGroup.add(nodesMesh);

    // Mouse Parallax
    const mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    const handleMouseMove = (event: MouseEvent) => {
      const rect = currentMount.getBoundingClientRect();
      const x = (event.clientX - rect.left) / width - 0.5;
      const y = (event.clientY - rect.top) / height - 0.5;
      mouse.targetX = x * 0.65;
      mouse.targetY = y * 0.65;
    };

    if (interactive) {
      window.addEventListener('mousemove', handleMouseMove);
    }

    // Scroll Handler
    const handleScroll = () => {
      stateRef.current.scrollOffset = window.scrollY || window.pageYOffset;
    };
    window.addEventListener('scroll', handleScroll, { passive: true });

    // Resize Handler
    const handleResize = () => {
      if (!currentMount) return;
      const newWidth = currentMount.clientWidth;
      const newHeight = currentMount.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Smooth mouse lerp
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      // Scroll reaction
      const scrollRotation = stateRef.current.scrollOffset * 0.0006;

      // Idle Rotation & Breathing
      const hoverSpeed = stateRef.current.isHovered ? 1.6 : 1.0;
      const baseRotationY = Math.sin(elapsedTime * 0.6 * hoverSpeed) * 0.22;
      const baseRotationX = Math.cos(elapsedTime * 0.45 * hoverSpeed) * 0.12;

      shieldGroup.rotation.y = baseRotationY + mouse.x + scrollRotation * 0.5;
      shieldGroup.rotation.x = baseRotationX - mouse.y;

      // Diamond Core Pulse
      const coreScale = 1.0 + Math.sin(elapsedTime * 2.5 * hoverSpeed) * 0.08;
      coreMesh.scale.set(coreScale, coreScale, coreScale);
      coreMesh.rotation.y += 0.02 * hoverSpeed;
      coreMesh.rotation.x += 0.015 * hoverSpeed;

      solidCoreMesh.rotation.y -= 0.018 * hoverSpeed;
      solidCoreMesh.rotation.z += 0.012 * hoverSpeed;

      // Orbital Rings Rotation
      ring1Mesh.rotation.z += 0.006 * hoverSpeed;
      ring2Mesh.rotation.z -= 0.008 * hoverSpeed;
      nodesMesh.rotation.z += 0.004 * hoverSpeed;

      // Particle Drift
      particleSystem.rotation.y = elapsedTime * 0.025;

      // Scanning effect: periodic intense glow sweep
      if (stateRef.current.isScanning) {
        accentLight.intensity = 5.5 + Math.sin(elapsedTime * 8.0) * 2.5;
        coreLight.intensity = 4.0 + Math.sin(elapsedTime * 8.0) * 2.0;
      }

      renderer.render(scene, camera);
    };

    animate();

    // Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      if (interactive) {
        window.removeEventListener('mousemove', handleMouseMove);
      }
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleResize);
      if (currentMount && renderer.domElement) {
        currentMount.removeChild(renderer.domElement);
      }
      renderer.dispose();
      shieldGeo.dispose();
      innerGeo.dispose();
      coreGeo.dispose();
      solidCoreGeo.dispose();
      ring1Geo.dispose();
      ring2Geo.dispose();
      particleGeo.dispose();
      nodeGeo.dispose();
    };
  }, [interactive, intensity]);

  // 2. React smoothly to dynamic theme changes (Colors lerp in real-time)
  useEffect(() => {
    const primaryColor = new THREE.Color(palette.primary.hex);
    const secondaryColor = new THREE.Color(palette.secondary.hex);
    const accentColor = new THREE.Color(palette.accent.hex);

    // Proportional intensity modifier from 60/30/10 ratio
    const accentFactor = colorRatio.accent / 10;

    // Update lights
    if (lightsRef.current.ambient) {
      lightsRef.current.ambient.color = primaryColor;
    }
    if (lightsRef.current.accentKey) {
      lightsRef.current.accentKey.color = accentColor;
      lightsRef.current.accentKey.intensity = 3.8 * intensity * accentFactor;
    }
    if (lightsRef.current.secondaryRim) {
      lightsRef.current.secondaryRim.color = secondaryColor;
    }
    if (lightsRef.current.coreLight) {
      lightsRef.current.coreLight.color = accentColor;
      lightsRef.current.coreLight.intensity = 2.4 * accentFactor;
    }

    // Update Materials
    const mats = materialsRef.current;
    if (mats.shieldMat) {
      mats.shieldMat.color = primaryColor.clone().offsetHSL(0, 0, 0.08);
    }
    if (mats.glassMat) {
      mats.glassMat.color = accentColor;
    }
    if (mats.coreMat) {
      mats.coreMat.color = accentColor;
    }
    if (mats.solidCoreMat) {
      mats.solidCoreMat.color = secondaryColor;
      mats.solidCoreMat.emissive = accentColor;
      mats.solidCoreMat.emissiveIntensity = 1.6 * accentFactor;
    }
    if (mats.ring1Mat) {
      mats.ring1Mat.color = secondaryColor;
    }
    if (mats.ring2Mat) {
      mats.ring2Mat.color = accentColor;
    }
    if (mats.particlesMat) {
      mats.particlesMat.color = accentColor;
    }
    if (mats.nodesMat) {
      mats.nodesMat.color = secondaryColor;
    }
  }, [palette, colorRatio, intensity]);

  // WebGL Fallback
  if (!webglSupported) {
    return (
      <div className="w-full h-full min-h-[420px] flex flex-col items-center justify-center p-8 text-center rounded-2xl glass-panel border border-[var(--theme-accent)]/30">
        <div className="w-24 h-24 rounded-2xl bg-[var(--theme-accent)]/15 border border-[var(--theme-accent)]/40 flex items-center justify-center mb-4 shadow-[0_0_30px_rgba(var(--theme-accent-rgb),0.35)]">
          <Shield className="w-12 h-12 text-[var(--theme-accent)]" />
        </div>
        <h3 className="text-lg font-bold text-white mb-2">BHASHASHIELD SECURE CORE</h3>
        <p className="text-xs text-white/60 max-w-xs font-mono">
          WebGL acceleration disabled or unsupported. Multilingual defense engine active.
        </p>
      </div>
    );
  }

  return (
    <div
      ref={mountRef}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="w-full h-full min-h-[460px] lg:min-h-[580px] relative cursor-grab active:cursor-grabbing select-none"
      title="Interactive 3D BhashaShield Cyber Core (Drag to rotate)"
    />
  );
};
