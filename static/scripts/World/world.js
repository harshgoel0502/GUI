import { loadCar } from './car.js';
import { createCamera } from './camera.js';
import { createScene } from './scene.js';
import { createRenderer } from './renderer.js';

let camera;
let renderer;
let scene;

class World {
  constructor(container) {
    camera = createCamera();
    renderer = createRenderer();
    scene = createScene();
    container.append(renderer.domElement);
  }

  async init() {
    const { car } = await loadCar();
    scene.add(car);
  }

  render() {
    renderer.render(scene, camera);
  }
}

export { World };