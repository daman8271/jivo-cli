'use strict';
const data = window.DISPATCH_DATA;
const $ = id => document.getElementById(id);
const trips = data.trips;
const totalL = trips.reduce((sum, trip) => sum + trip.litres, 0);
const tonnes = litres => (litres / 1000).toLocaleString('en-IN', { minimumFractionDigits: 3, maximumFractionDigits: 3 });
$('total').innerHTML = `${tonnes(totalL)} <small>T</small>`;
$('trip-count').textContent = trips.length;
$('gap').innerHTML = `${(data.targetPlanningTonnes - totalL / 1000).toFixed(3)} <small>T</small>`;
$('bt').textContent = `${tonnes(data.warehouseLitres['BH-BT'])} T`;
$('pf').textContent = `${tonnes(data.warehouseLitres['BH-PF'])} T`;
let selectedId = trips[trips.length - 1].id;
let redraw = () => {};
$('trucks').innerHTML = trips.map(trip => `<button class="truck" id="trip-${trip.id}" data-id="${trip.id}" aria-pressed="false"><span><span class="trip-icon">TRIP ${trip.id} · ${trip.time} IST</span><small>${trip.warehouses}</small></span><span><strong>${tonnes(trip.litres)} T</strong><small>${trip.litres.toLocaleString('en-IN')} litres</small></span></button>`).join('');
function selectTrip(id) {
  selectedId = id;
  const trip = trips.find(row => row.id === id);
  for (const row of trips) $(`trip-${row.id}`).setAttribute('aria-pressed', String(row.id === id));
  const minute = Number($('replay').value);
  $('detail').innerHTML = `<h3>Trip ${trip.id} · ${trip.entry}</h3><div class="detail-grid"><div><span>Actual gate departure</span>${trip.time} IST · 8 September</div><div><span>Recorded load</span>${tonnes(trip.litres)} T</div><div><span>Warehouse scope</span>${trip.warehouses}</div><div><span>Source verification</span>${trip.documents} documents · ${trip.lines} item lines</div></div><p><small>${trip.minute <= minute ? 'Departed by the selected replay time.' : 'Departure is later than the selected replay time.'} ${trip.warehouses.includes(',') ? 'Per-warehouse load split is not included in this snapshot.' : ''}</small></p>`;
  redraw();
}
$('trucks').addEventListener('click', event => { const row = event.target.closest('[data-id]'); if (row) selectTrip(Number(row.dataset.id)); });
function replay() {
  const minute = Number($('replay').value);
  const departed = trips.filter(trip => trip.minute <= minute);
  const time = minute === 1440 ? '· end of day' : `· ${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')} IST`;
  $('replay-time').textContent = time;
  $('replay-summary').textContent = `${departed.length} of ${trips.length} trips departed · ${tonnes(departed.reduce((sum, trip) => sum + trip.litres, 0))} T released by this point.`;
  for (const trip of trips) $(`trip-${trip.id}`).classList.toggle('dim', trip.minute > minute);
  selectTrip(selectedId);
}
$('replay').addEventListener('input', replay);
$('end-day').addEventListener('click', () => { $('replay').value = 1440; replay(); });
$('scenario').addEventListener('submit', event => event.preventDefault());
$('scenario').addEventListener('input', () => {
  const fields = ['opening', 'production', 'other', 'test-dispatch'].map(id => $(id));
  if (fields.some(input => input.value.trim() === '' || !input.validity.valid || !Number.isFinite(Number(input.value)))) {
    $('scenario-result').textContent = 'Enter valid values in all four fields. Only net other movements can be negative.'; return;
  }
  const [opening, production, other, dispatch] = fields.map(input => Number(input.value));
  const closing = opening + production + other - dispatch;
  $('scenario-result').textContent = closing < 0 ? `This scenario is short by ${(-closing).toFixed(3)} T. The entered dispatch exceeds available stock.` : `What-if closing stock: ${closing.toFixed(3)} T · unconfirmed inputs`;
});
replay();
try {
  const T = window.THREE;
  const host = $('scene');
  const renderer = new T.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0xede3d2, 1);
  host.insertBefore(renderer.domElement, host.firstChild);
  renderer.domElement.setAttribute('aria-label', 'Illustrative three-dimensional yard. Use the truck list for the same information and keyboard selection.');
  const scene = new T.Scene();
  const camera = new T.PerspectiveCamera(34, 1, 0.1, 150);
  camera.position.set(21, 21, 28); camera.lookAt(0, 0, 0);
  scene.add(new T.AmbientLight(0xffffff, 2.3));
  const sun = new T.DirectionalLight(0xfff7df, 3); sun.position.set(10, 25, 15); scene.add(sun);
  function box(parent, x, y, z, w, h, d, color) {
    const mesh = new T.Mesh(new T.BoxGeometry(w, h, d), new T.MeshStandardMaterial({ color, roughness: 0.8 }));
    mesh.position.set(x, y, z); parent.add(mesh); return mesh;
  }
  function label(text, x, y, z, width = 5) {
    const canvas = document.createElement('canvas');canvas.width = 512;canvas.height = 100;
    const ctx = canvas.getContext('2d');ctx.fillStyle = '#392c28';ctx.font = 'bold 32px sans-serif';ctx.textAlign = 'center';ctx.fillText(text, 256, 60);
    const sprite = new T.Sprite(new T.SpriteMaterial({ map: new T.CanvasTexture(canvas), depthTest: false }));sprite.position.set(x,y,z);sprite.scale.set(width,width/5.12,1);scene.add(sprite);return sprite;
  }
  box(scene,0,-0.2,0,27,.3,18,0xdccfbb);
  box(scene,0,.01,3,26,.08,4,0xa99d8c);
  for (let x=-12;x<13;x+=3) box(scene,x,.08,3,1.4,.03,.1,0xf4eadd);
  box(scene,-7,1.8,-5,8,3.6,4,0xc0ad8e);box(scene,5,1.8,-5,8,3.6,4,0xab8c72);
  box(scene,-7,3.65,-5,8.3,.18,4.3,0x8c5145);box(scene,5,3.65,-5,8.3,.18,4.3,0x8c5145);
  for(const x of [-9,-5,3,7]) box(scene,x,1,-2.96,1.7,2,.08,0x685b4e);
  label('BH-BT',-7,5,-5); label('BH-PF',5,5,-5);label('ACTUAL DEPARTURES',0,.3,8,8);
  const truckMeshes = [];
  trips.forEach((trip,index)=>{
    const group = new T.Group(); group.position.set(-10 + index * 5, 0, 3);
    const body=box(group,-.25,1,0,2.6,1.5,1.4,0x942f32);
    box(group,1.5,.8,0,1,1.25,1.35,0xc49b4d);box(group,1.8,1.1,.7,.65,.45,.04,0x466066);
    for(const x of [-1,1.5]) for(const z of [-.77,.77]){const wheel=new T.Mesh(new T.CylinderGeometry(.35,.35,.2,12),new T.MeshStandardMaterial({color:0x403932}));wheel.rotation.x=Math.PI/2;wheel.position.set(x,.35,z);group.add(wheel);}
    group.userData.tripId=trip.id;group.traverse(child=>{child.userData.tripId=trip.id;});scene.add(group);const marker=label(String(trip.id),group.position.x,2.7,3,2.7);truckMeshes.push({group,body,marker,id:trip.id,minute:trip.minute});
  });
  redraw = () => {
    const minute=Number($('replay').value);
    for(const truck of truckMeshes){truck.group.visible=truck.minute<=minute;truck.marker.visible=truck.group.visible;truck.body.material.color.setHex(truck.id===selectedId?0xb88632:0x942f32);}
    renderer.render(scene,camera);
  };
  const resize=()=>{const width=host.clientWidth,height=host.clientHeight;renderer.setSize(width,height,false);camera.aspect=width/height;camera.updateProjectionMatrix();redraw();};
  new ResizeObserver(resize).observe(host);
  const raycaster=new T.Raycaster();const pointer=new T.Vector2();
  renderer.domElement.addEventListener('click',event=>{const rect=renderer.domElement.getBoundingClientRect();pointer.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);const hit=raycaster.intersectObjects(truckMeshes.filter(t=>t.group.visible).map(t=>t.group),true)[0];if(hit)selectTrip(hit.object.userData.tripId);});
  $('fallback').hidden=true;resize();
} catch (error) {
  $('fallback').textContent = '3D is unavailable in this browser. The trip list, historical replay and calculations below remain fully usable.';
  console.info('3D fallback:',error.message);
}
