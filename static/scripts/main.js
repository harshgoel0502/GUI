

// const scene = new THREE.Scene();
// const camera = new THREE.PerspectiveCamera( 75, window.innerWidth / window.innerHeight, 0.1, 1000 );

// const renderer = new THREE.WebGLRenderer();
// renderer.setSize( window.innerWidth, window.innerHeight );
// renderer.setAnimationLoop( animate );
// document.body.appendChild( renderer.domElement );

// const geometry = new THREE.BoxGeometry( 1, 1, 1 );
// const material = new THREE.MeshBasicMaterial( { color: 0x00ff00 } );
// const cube = new THREE.Mesh( geometry, material );
// scene.add( cube );

// camera.position.z = 5;

// function animate() {

// 	cube.rotation.x += 0.01;
// 	cube.rotation.y += 0.01;

// 	renderer.render( scene, camera );

// }

// import * as THREE from 'https://cdn.skypack.dev/three@0.132.2';
// import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.121.1/examples/jsm/controls/OrbitControls.js';
// // import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
// import { GLTFLoader } from 'https://cdn.jsdelivr.net/npm/three@0.121.1/examples/jsm/loaders/GLTFLoader.js';
// // import Stats from 'https://cdn.jsdelivr.net/npm/three@0.121.1/examples/jsm/libs/stats.module';
// // import Stats from 'three/examples/jsm/libs/stats.module'

// const scene = new THREE.Scene()
// scene.add(new THREE.AxesHelper(5))

// // const light = new THREE.SpotLight(0xffffff, Math.PI * 20)
// // light.position.set(5, 5, 5)
// // scene.add(light);

// const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000)
// camera.position.z = 2

// const renderer = new THREE.WebGLRenderer()
// // Since Three r150, lighting has changed significantly with every version up to three r158
// // keep the threejs defaults, and reduce light watts in blender if using punctual lights
// // if using Threejs lights, then you need to experiment with light intensity.
// // renderer.physicallyCorrectLights = true //deprecated
// // renderer.useLegacyLights = false //deprecated
// renderer.shadowMap.enabled = true
// renderer.setSize(window.innerWidth, window.innerHeight)
// document.body.appendChild(renderer.domElement)

// const controls = new OrbitControls(camera, renderer.domElement)
// controls.enableDamping = true

// const loader = new GLTFLoader()
// loader.load(
//   '/static/models/scene.gltf',
//   function (gltf) {
//     gltf.scene.traverse(function (child) {
//       if (child instanceof THREE.Mesh) {
//         const m = child
//         m.receiveShadow = true
//         m.castShadow = true
//       }
//       if (child instanceof THREE.Light) {
//         const l = child
//         l.castShadow = true
//         l.shadow.bias = -0.003
//         l.shadow.mapSize.width = 2048
//         l.shadow.mapSize.height = 2048
//       }
//     })
//     scene.add(gltf.scene)
//   },
//   (xhr) => {
//     console.log((xhr.loaded / xhr.total) * 100 + '% loaded')
//   },
//   (error) => {
//     console.log(error)
//   }
// )

// window.addEventListener('resize', onWindowResize, false)
// function onWindowResize() {
//   camera.aspect = window.innerWidth / window.innerHeight
//   camera.updateProjectionMatrix()
//   renderer.setSize(window.innerWidth, window.innerHeight)
//   render()
// }


// function render() {
//   renderer.render(scene, camera)
// }

import * as THREE from 'https://cdn.skypack.dev/three@0.132.2';
import { OrbitControls } from 'https://cdn.skypack.dev/three@0.132.2/examples/jsm/controls/OrbitControls.js';
// import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls'
import { GLTFLoader } from 'https://cdn.skypack.dev/three@0.132.2/examples/jsm/loaders/GLTFLoader.js';
import { RGBELoader } from 'https://cdn.skypack.dev/three@0.132.2/examples/jsm/loaders/RGBELoader.js';

// import * as THREE from "three";

// import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
// import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
// import { RGBELoader } from "three/examples/jsm/loaders/RGBELoader.js";

// Canvas
const canvas = document.querySelector("canvas");
const scene = new THREE.Scene();
let renderer;
let camera;
let model;
init(); //our setup
render(); //the update loop

function init() {
  //setup the camera
  camera = new THREE.PerspectiveCamera(
    45,
    window.innerWidth / window.innerHeight,
    10,
    10000
  );
  camera.position.set(108, 200, -307);

  //load and create the environment
  new RGBELoader()
    .setDataType(THREE.UnsignedByteType)
    .load(
      "https://cdn.jsdelivr.net/gh/mrdoob/three.js@master/examples/textures/equirectangular/quarry_01_1k.hdr",
      function (texture) {
        const pmremGenerator = new THREE.PMREMGenerator(renderer);
        pmremGenerator.compileEquirectangularShader();
        const envMap = pmremGenerator.fromEquirectangular(texture).texture;

        // scene.background = envMap; //this loads the envMap for the background
        scene.environment = envMap; //this loads the envMap for reflections and lighting

        texture.dispose(); //we have envMap so we can erase the texture
        pmremGenerator.dispose(); //we processed the image into envMap so we can stop this
      }
    );

  // load the model
  const loader = new GLTFLoader();
  loader.load(
    "/static/models/rocket/scene.gltf",
    function (gltf) {
      model = gltf.scene;
      if (model) model.rotation.x -= Math.PI/2;
      scene.add(model);
      render(); //render the scene for the first time
    }
  );

  //setup the renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, canvas: canvas });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; //added contrast for filmic look
  renderer.toneMappingExposure = 1;
  renderer.outputEncoding = THREE.sRGBEncoding; //extended color space for the hdr

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.addEventListener("change", render); // use if there is no animation loop to render after any changes
  controls.minDistance = 2000;
  controls.maxDistance = 3000;
  controls.target.set(0, 200, -0.2);
  controls.update();

  window.addEventListener("resize", onWindowResize);
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();

  renderer.setSize(window.innerWidth, window.innerHeight);

  render();
}

//

function render() {
  renderer.render(scene, camera);
}

