const cameraSelect = document.getElementById('camera-select');
const eventsBody = document.getElementById('events-body');
const stream = document.getElementById('stream');
const eventDetail = document.getElementById('event-detail');
const eventImage = document.getElementById('event-image');

async function loadCameras() {
  const res = await fetch('/cameras');
  const cameras = await res.json();
  cameraSelect.innerHTML = '';
  cameras.forEach((cam) => {
    const opt = document.createElement('option');
    opt.value = cam.id;
    opt.textContent = `${cam.name} (${cam.location || 'Sin ubicación'})`;
    cameraSelect.appendChild(opt);
  });
  if (cameras.length > 0) {
    stream.src = `/monitor/stream/${cameras[0].id}`;
    await loadEvents(cameras[0].id);
  }
}

async function loadEvents(cameraId) {
  const res = await fetch(`/events?camera_id=${cameraId}&limit=50`);
  const events = await res.json();
  eventsBody.innerHTML = '';
  events.forEach((evt) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${evt.id}</td>
      <td>${evt.event_type}</td>
      <td>${evt.severity}</td>
      <td>${evt.confidence}</td>
      <td>${new Date(evt.frame_timestamp).toLocaleString()}</td>
      <td><button data-id="${evt.id}">Ver</button></td>
    `;
    tr.querySelector('button').addEventListener('click', () => loadEventDetail(evt.id));
    eventsBody.appendChild(tr);
  });
}

async function loadEventDetail(eventId) {
  const res = await fetch(`/events/${eventId}`);
  const evt = await res.json();
  eventDetail.textContent = JSON.stringify(evt, null, 2);

  if (evt.snapshot_url) {
    eventImage.src = evt.snapshot_url;
    eventImage.style.display = 'block';
  } else {
    eventImage.style.display = 'none';
  }
}

document.getElementById('refresh').addEventListener('click', async () => {
  const cameraId = cameraSelect.value;
  await loadEvents(cameraId);
});

document.getElementById('detect').addEventListener('click', async () => {
  const cameraId = cameraSelect.value;
  if (!cameraId) return;
  await fetch(`/monitor/run-once/${cameraId}`, { method: 'POST' });
  await loadEvents(cameraId);
});

cameraSelect.addEventListener('change', async () => {
  const cameraId = cameraSelect.value;
  stream.src = `/monitor/stream/${cameraId}`;
  await loadEvents(cameraId);
});

loadCameras();
