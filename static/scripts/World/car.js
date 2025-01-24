import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.121.1/examples/jsm/loaders/GLTFLoader.js';

async function loadCar() {
  const loader = new GLTFLoader();

  const [carData] = await Promise.all([
    loader.loadAsync('/static/models/scene.gltf')
  ]);

  const car = carData.scene.children[0];

  return {
    car
  };
}

export { loadCar };