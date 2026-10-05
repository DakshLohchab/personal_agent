"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { Component, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { SphereGeometry, Vector3, type Mesh } from "three";
import type { SimulationOutput } from "@/lib/types";

class WebGLBoundary extends Component<{ children: ReactNode; fallback: ReactNode }, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: unknown) {
    if (error instanceof Error) {
      console.error("Future paths 3D preview failed:", error.message);
    } else {
      console.error("Future paths 3D preview failed:", String(error));
    }
  }

  render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

function PathMarker({
  index,
  selected,
  onSelect,
}: {
  index: number;
  selected: boolean;
  onSelect: () => void;
}) {
  const mesh = useRef<Mesh>(null);
  const targetScale = selected ? 1.35 : 1;

  useFrame((_, delta) => {
    if (mesh.current) {
      mesh.current.scale.x += (targetScale - mesh.current.scale.x) * Math.min(delta * 8, 1);
      mesh.current.scale.y = mesh.current.scale.x;
      mesh.current.scale.z = mesh.current.scale.x;
      if (selected) mesh.current.rotation.y += delta * 0.35;
    }
  });

  const x = (index - (index + 1) / 2) * 2.4;
  return (
    <mesh ref={mesh} position={[x, 0, 0]} onClick={onSelect} onPointerDown={onSelect}>
      <sphereGeometry args={[0.48, 24, 16]} />
      <meshStandardMaterial color={selected ? "#d88b61" : "#426454"} roughness={0.35} />
      <lineSegments>
        <edgesGeometry args={[new SphereGeometry(0.5, 12, 8)]} />
        <lineBasicMaterial color="#f4f1e8" />
      </lineSegments>
    </mesh>
  );
}

function FutureScene({
  outputs,
  selected,
  onSelect,
  reducedMotion,
}: {
  outputs: SimulationOutput[];
  selected: string | null;
  onSelect: (option: string) => void;
  reducedMotion: boolean;
}) {
  const positions = useMemo(
    () => outputs.map((_, index) => [(index - (outputs.length - 1) / 2) * 2.4, 0, 0] as [number, number, number]),
    [outputs],
  );
  return (
    <>
      <ambientLight intensity={1.8} />
      <directionalLight position={[2, 4, 3]} intensity={2} />
      <group rotation={reducedMotion ? [0, 0, 0] : [0.12, 0, 0]}>
        {outputs.map((output, index) => (
          <PathMarker
            key={output.option_name}
            index={index}
            selected={selected === output.option_name}
            onSelect={() => onSelect(output.option_name)}
          />
        ))}
        {positions.map((position, index) =>
          index === 0 ? null : (
            <line key={`path-${outputs[index].option_name}`}>
              <bufferGeometry
                attach="geometry"
                onUpdate={(geometry) => {
                  geometry.setFromPoints([
                    new Vector3(...positions[index - 1]),
                    new Vector3(...position),
                  ]);
                }}
              />
              <lineBasicMaterial color="#b8c5b8" />
            </line>
          ),
        )}
      </group>
    </>
  );
}

export function FuturePaths({
  outputs,
  selected,
  onSelect,
}: {
  outputs: SimulationOutput[];
  selected: string | null;
  onSelect: (option: string) => void;
}) {
  const [webgl, setWebgl] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    try {
      const canvas = document.createElement("canvas");
      setWebgl(Boolean(canvas.getContext("webgl2") || canvas.getContext("webgl")));
    } catch {
      setWebgl(false);
    }
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updateMotion = () => setReducedMotion(media.matches);
    updateMotion();
    media.addEventListener("change", updateMotion);
    return () => media.removeEventListener("change", updateMotion);
  }, []);

  return (
    <div aria-label="Interactive overview of possible futures" className="future-paths">
      <div className="future-paths__canvas" aria-hidden="true">
        <WebGLBoundary
          fallback={
            <p className="future-paths__fallback">
              3D preview is unavailable. Use the path buttons or detailed graph below.
            </p>
          }
        >
          {webgl ? (
            <Canvas
              camera={{ position: [0, 2.4, 7], fov: 42 }}
              dpr={[1, 1.5]}
              fallback={
                <p className="future-paths__fallback">
                  3D preview is unavailable. Use the path buttons or detailed graph below.
                </p>
              }
            >
              <FutureScene
                outputs={outputs}
                selected={selected}
                onSelect={onSelect}
                reducedMotion={reducedMotion}
              />
            </Canvas>
          ) : (
            <p className="future-paths__fallback">
              3D preview is unavailable. Use the path buttons or detailed graph below.
            </p>
          )}
        </WebGLBoundary>
      </div>
      <div className="future-paths__legend" aria-label="Future path selection">
        {outputs.map((output) => (
          <button
            className={selected === output.option_name ? "future-paths__button is-selected" : "future-paths__button"}
            key={output.option_name}
            onClick={() => onSelect(output.option_name)}
            type="button"
          >
            <span>{output.option_name}</span>
            <span className="future-paths__value">₹{output.result.metrics.ending_cash}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
