

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
var eulerAngle;
if (!!window.EventSource) {
  var source = new EventSource('/');
// var ctx = c.getContext("2d");
  // ctx.translate(c.width/2, c.height - 1/10*c.height);

  source.onmessage = function(e){
      eulerAngle = e.data.toString().substring(1,e.data.toString().length-1).trim().split(/\s+/);
      for(var i = 0; i < eulerAngle.length; i++){
        eulerAngle[i] = Number(eulerAngle[i].trim());
      }
  };
  
}
// Canvas
const canvas = document.querySelector("canvas");
const scene = new THREE.Scene();
let renderer;
let camera;
let model;
let controls;
init(); //our setup
render(); //the update loop
var axis;

function init() {
  //setup the camera
  camera = new THREE.PerspectiveCamera(
    45,
    window.innerWidth / window.innerHeight ,
    1,
    1000
  );
  camera.position.set(10, 10, 10);
  axis = new THREE.AxesHelper( 10000 );
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

  model = new THREE.Object3D( );
  // load the model
  const loader = new GLTFLoader();
  loader.load(
    "/static/models/DarwinRender.glb",
    function (gltf) {
      // model = gltf.scene;
      // if (model) model.rotation.x -= Math.PI/2;
      const box = new THREE.Box3( ).setFromObject( gltf.scene );
					// https://threejs.org/docs/index.html#api/en/helpers/Box3Helper
	// const boxHelper = new THREE.Box3Helper( box, 0xffff00 );
	// scene.add( boxHelper ); // see original position of model.gltf, not centered
      const c = box.getCenter( new THREE.Vector3( ) );
      const size = box.getSize( new THREE.Vector3( ) );
      // center the gltf scene - important for modelSqu.rotation.y = t in function animate
      gltf.scene.position.set( 0.0465-c.x, - c.y, -c.z );  // put // in front of this line, try it out 
      var vector = new THREE.Vector3(0, 1, 0);
      var euler = new THREE.Euler();
      const quaternion = new THREE.Quaternion();
      let v = new THREE.Vector3();
      let meshes = []
      model.rotation.set((-0.5*Math.PI),0.0465,0);
      // model.traverse(e=>meshes.push(e));
      // meshes.forEach(mesh=>{
      //   console.log(mesh);
      //   var worldRot = new THREE.Euler();
      //   mesh.getWorldRotation().copy(worldRot);
      //   worldRot.reorder("ZYX");
      //   let g = mesh.geometry;
      //   if(g !== undefined){
      //   console.log(g);
      //   let points = g.attributes.position;
      //   for(let i=0;i<points.count;i++){
      //     v.set(points.getX(i),points.getY(i),points.getZ(i));
      //     mesh.localToWorld(v);
      //     console.log("world space vertex:",v)
      //   }
      // }
      // })
      model.add( gltf.scene ); 
      model.position.set( 0, 0, 0);
      // model.position.y -= 200;
      // model.position.setX(2000);
      // model.position.setY(-20);
      scene.add(model);
      // console.log(model.position);
      
      render(); //render the scene for the first time
    }
  );

  // var loader2 = new THREE.FontLoader();
  // loader2.load( '/static/fonts/helvetiker_regular.typeface.json', function ( font ) {

  //   var textGeometry = new THREE.TextGeometry( "text", {

  //     font: font,

  //     size: 50,
  //     height: 10,
  //     curveSegments: 12,

  //     bevelThickness: 1,
  //     bevelSize: 1,
  //     bevelEnabled: true

  //   });
  //   var  color = new THREE.Color();
  //   color.setRGB(255, 250, 250);
  //   var textMaterial = new THREE.MeshPhongMaterial( 
  //     { color: color}
  //   );
  //   var light = new THREE.DirectionalLight( 0xffffff );
  //   light.position.set( 0, 1, 1 ).normalize();
  //   scene.add(light);
  //   var mesh = new THREE.Mesh( textGeometry, textMaterial );

  //   scene.add( mesh );

  // }); 

  //setup the renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, canvas: canvas });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.toneMapping = THREE.ACESFilmicToneMapping; //added contrast for filmic look
  renderer.toneMappingExposure = 1;
  renderer.outputEncoding = THREE.sRGBEncoding; //extended color space for the hdr

  controls = new OrbitControls(camera, renderer.domElement);
  controls.addEventListener("change", render); // use if there is no animation loop to render after any changes
  controls.minDistance = 10;
  controls.maxDistance = 100;
  controls.target.set(0, 0, 0);
  controls.update();

  // let gridHelper = new THREE.GridHelper(4000, 4000);
  // scene.add(gridHelper);
  scene.add( axis );
  window.addEventListener("resize", onWindowResize);
  animate();
}

function onWindowResize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();

  renderer.setSize(window.innerWidth, window.innerHeight);

  render();
}

//

function render() {
  // var  textGeo = new THREE.TextGeometry('Y', {
  //     size: 5,
  //     height: 2,
  //     curveSegments: 6,
  //     font: "helvetiker",
  //     style: "normal"       
  // });

  // var  color = new THREE.Color();
  // color.setRGB(255, 250, 250);
  // var  textMaterial = new THREE.MeshBasicMaterial({ color: color });
  // var  text = new THREE.Mesh(textGeo , textMaterial);
  // text.position.x = axis.geometry.vertices[1].x;
  // text.position.y = axis.geometry.vertices[1].y;
  // text.position.z = axis.geometry.vertices[1].z;
  // text.rotation = camera.rotation;
  // scene.add(text);
  renderer.render(scene, camera);
}


function animate() {
  // if(model) model.position.y += 10;
  // if(camera) camera.position.y += 10;
  // if(controls) controls.target.y += 10;
  // controls.update();
  if (model && eulerAngle) model.rotation.set((-0.5*Math.PI)+(eulerAngle[0] *Math.PI/360),0.0465+(eulerAngle[1]*Math.PI/360),(eulerAngle[2]*Math.PI/360));
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

