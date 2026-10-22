/**
 * @fileoverview Conversion functions between Three.js types and Flexiv PDK protobuf types.
 * This is the TypeScript/JavaScript equivalent of cpp/src/spatial/eigen_conversion.cpp
 * and cpp/include/flexiv/pdk/spatial/eigen_conversion.hpp
 */

import * as THREE from 'three';
import { Vector3, Quaternion, SE3Pose } from '../../generated/flexiv/pdk/spatial/geometry_pb';

/** A position and orientation, as held by THREE.Object3D */
export interface Pose {
  position: THREE.Vector3;
  quaternion: THREE.Quaternion;
}

// --- Protobuf to Three.js (ToThree) ---

// Keep Quaternion before Vector3: a Quaternion also matches the Vector3 signature.
/** Convert a protobuf Quaternion to a Three.js Quaternion */
export function ToThree(q: Quaternion): THREE.Quaternion;
/** Convert a protobuf Vector3 to a Three.js Vector3 */
export function ToThree(v: Vector3): THREE.Vector3;
/** Convert a protobuf SE3Pose to a Three.js Matrix4 */
export function ToThree(p: SE3Pose): THREE.Matrix4;
/** Convert a protobuf RepeatedField (number[]) to a standard number array */
export function ToThree(v: number[]): number[];

export function ToThree(
  arg: Vector3 | Quaternion | SE3Pose | number[]
): THREE.Vector3 | THREE.Quaternion | THREE.Matrix4 | number[] {
  if (arg instanceof Vector3) {
    return new THREE.Vector3(arg.getX(), arg.getY(), arg.getZ());
  }

  if (arg instanceof Quaternion) {
    return new THREE.Quaternion(arg.getX(), arg.getY(), arg.getZ(), arg.getW());
  }

  if (arg instanceof SE3Pose) {
    const matrix = new THREE.Matrix4();
    const position = ToThree(arg.getPosition()!) as THREE.Vector3;
    const rotation = ToThree(arg.getRotation()!) as THREE.Quaternion;
    matrix.compose(position, rotation, new THREE.Vector3(1, 1, 1));
    return matrix;
  }

  if (Array.isArray(arg)) {
    return [...arg];
  }

  throw new Error('Unsupported type for ToThree conversion');
}

// --- Three.js to Protobuf (ToProto) ---

/** Convert a Three.js Vector3 to a protobuf Vector3 */
export function ToProto(v: THREE.Vector3): Vector3;
/** Convert a Three.js Quaternion to a protobuf Quaternion */
export function ToProto(q: THREE.Quaternion): Quaternion;
/** Convert a Three.js Matrix4 to a protobuf SE3Pose */
export function ToProto(m: THREE.Matrix4): SE3Pose;
/** Convert a position and quaternion, such as a THREE.Object3D, to a protobuf SE3Pose */
export function ToProto(pose: Pose): SE3Pose;
/** Convert a number array to a protobuf RepeatedField (number[]) */
export function ToProto(v: number[]): number[];

export function ToProto(
  arg: THREE.Vector3 | THREE.Quaternion | THREE.Matrix4 | Pose | number[]
): Vector3 | Quaternion | SE3Pose | number[] {
  if (arg instanceof THREE.Vector3) {
    const result = new Vector3();
    result.setX(arg.x);
    result.setY(arg.y);
    result.setZ(arg.z);
    return result;
  }

  if (arg instanceof THREE.Quaternion) {
    const result = new Quaternion();
    result.setX(arg.x);
    result.setY(arg.y);
    result.setZ(arg.z);
    result.setW(arg.w);
    return result;
  }

  if (arg instanceof THREE.Matrix4) {
    const result = new SE3Pose();
    const position = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    const scale = new THREE.Vector3();
    arg.decompose(position, quaternion, scale);
    result.setPosition(ToProto(position) as Vector3);
    result.setRotation(ToProto(quaternion) as Quaternion);
    return result;
  }

  if (Array.isArray(arg)) {
    return [...arg];
  }

  if (arg.position instanceof THREE.Vector3 && arg.quaternion instanceof THREE.Quaternion) {
    const result = new SE3Pose();
    result.setPosition(ToProto(arg.position));
    result.setRotation(ToProto(arg.quaternion));
    return result;
  }

  throw new Error('Unsupported type for ToProto conversion');
}

// --- Position and quaternion ---

/** Convert a protobuf SE3Pose to a position and quaternion, to copy into a THREE.Object3D */
export function ToPose(p: SE3Pose): Pose {
  return {
    position: ToThree(p.getPosition()!),
    quaternion: ToThree(p.getRotation()!),
  };
}