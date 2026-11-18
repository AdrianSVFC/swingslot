// SwingSlot - find an instructor and book a golf lesson
const STORAGE_KEY = "swingslot-bookings";
let instructors = [];
let currentInstructor = null;

const instructorList = document.getElementById("instructorList");
const locationFilter = document.getElementById("locationFilter");
const typeFilter = document.getElementById("typeFilter");
const resultCount = document.getElementById("resultCount");
const lessonList = document.getElementById("lessonList");
const slotList = document.getElementById("slotList");
const bookingMessage = document.getElementById("bookingMessage");
const weatherBox = document.getElementById("weatherBox");
const bookingModal = new bootstrap.Modal(document.getElementById("bookingModal"));

// ---------- Load data ----------
async function loadInstructors() {
  const response = await fetch("data/instructors.json");
  instructors = await response.json();
  fillFilterOptions();
  renderInstructors(instructors);
  renderMyLessons();
}

function fillFilterOptions() {
  const locations = [...new Set(instructors.map(i => i.location))];
  const types = [...new Set(instructors.flatMap(i => i.lessonTypes))];
  locations.forEach(loc => locationFilter.add(new Option(loc, loc)));
  types.forEach(type => typeFilter.add(new Option(type, type)));
}

// ---------- Instructor cards ----------
function renderInstructors(list) {
  instructorList.innerHTML = "";
  resultCount.textContent = `${list.length} instructor(s) found`;

  list.forEach(instructor => {
    const col = document.createElement("div");
    col.className = "col-md-6 col-lg-4";
    col.innerHTML = `
      <article class="card instructor-card h-100 shadow-sm">
        <div class="card-body d-flex flex-column">
          <h3 class="h5 card-title">${instructor.name}</h3>
          <p class="text-muted mb-2">${instructor.location}</p>
          <p class="card-text">${instructor.bio}</p>
          <div class="mb-3">
            ${instructor.lessonTypes.map(t => `<span class="badge badge-type me-1">${t}</span>`).join("")}
          </div>
          <p class="fw-bold mt-auto">$${instructor.price} / lesson</p>
          <button class="btn btn-fairway" data-id="${instructor.id}">See open slots</button>
        </div>
      </article>`;
    instructorList.appendChild(col);
  });
}

function applyFilters() {
  const loc = locationFilter.value;
  const type = typeFilter.value;
  const filtered = instructors.filter(i =>
    (loc === "" || i.location === loc) &&
    (type === "" || i.lessonTypes.includes(type))
  );
  renderInstructors(filtered);
}

// ---------- Time slots ----------
function generateSlots(instructor, days = 7) {
  const slots = [];
  const today = new Date();
  for (let d = 1; d <= days; d++) {
    const date = new Date(today);
    date.setDate(today.getDate() + d);
    if (instructor.days.includes(date.getDay())) {
      instructor.hours.forEach(hour => {
        const slot = new Date(date);
        slot.setHours(hour, 0, 0, 0);
        slots.push(slot);
      });
    }
  }
  return slots;
}

function formatSlot(date) {
  return date.toLocaleString("en-US", {
    weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit"
  });
}

function openBooking(instructorId) {
  currentInstructor = instructors.find(i => i.id === instructorId);
  document.getElementById("bookingTitle").textContent = `Book a lesson with ${currentInstructor.name}`;
  bookingMessage.innerHTML = "";
  renderSlots();
  showWeather(currentInstructor, weatherBox);
  bookingModal.show();
}

function renderSlots() {
  const bookings = getBookings();
  slotList.innerHTML = "";
  generateSlots(currentInstructor).forEach(slot => {
    const iso = slot.toISOString();
    const taken = bookings.some(b => b.instructorId === currentInstructor.id && b.slot === iso);
    const btn = document.createElement("button");
    btn.className = "btn btn-sm slot-btn";
    btn.textContent = formatSlot(slot);
    btn.disabled = taken;
    btn.setAttribute("aria-label", `${taken ? "Booked" : "Book"} ${formatSlot(slot)}`);
    btn.addEventListener("click", () => bookSlot(currentInstructor, iso));
    slotList.appendChild(btn);
  });
}

// ---------- Bookings (saved in localStorage) ----------
function getBookings() {
  return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
}

function saveBookings(bookings) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(bookings));
}

function bookSlot(instructor, slotIso) {
  const bookings = getBookings();
  const alreadyBooked = bookings.some(b => b.instructorId === instructor.id && b.slot === slotIso);
  if (alreadyBooked) {
    bookingMessage.innerHTML = `<div class="alert alert-warning">Sorry, that slot was just booked.</div>`;
    return;
  }
  bookings.push({
    id: Date.now(),
    instructorId: instructor.id,
    instructorName: instructor.name,
    location: instructor.location,
    price: instructor.price,
    slot: slotIso
  });
  saveBookings(bookings);
  bookingMessage.innerHTML = `<div class="alert alert-success">Booked! ${formatSlot(new Date(slotIso))} with ${instructor.name}.</div>`;
  renderSlots();
  renderMyLessons();
}

function cancelBooking(bookingId) {
  if (!confirm("Cancel this lesson?")) return;
  const bookings = getBookings().filter(b => b.id !== bookingId);
  saveBookings(bookings);
  renderMyLessons();
}

function renderMyLessons() {
  const bookings = getBookings().sort((a, b) => new Date(a.slot) - new Date(b.slot));
  if (bookings.length === 0) {
    lessonList.innerHTML = `<p class="text-muted">You have no lessons booked yet.</p>`;
    return;
  }
  lessonList.innerHTML = `
    <ul class="list-group">
      ${bookings.map(b => `
        <li class="list-group-item d-flex justify-content-between align-items-center flex-wrap gap-2">
          <span><strong>${formatSlot(new Date(b.slot))}</strong> with ${b.instructorName} (${b.location}) | $${b.price}</span>
          <button class="btn btn-outline-danger btn-sm" data-cancel="${b.id}">Cancel</button>
        </li>`).join("")}
    </ul>`;
}

// ---------- Events ----------
locationFilter.addEventListener("change", applyFilters);
typeFilter.addEventListener("change", applyFilters);

instructorList.addEventListener("click", e => {
  const btn = e.target.closest("button[data-id]");
  if (btn) openBooking(Number(btn.dataset.id));
});

lessonList.addEventListener("click", e => {
  const btn = e.target.closest("button[data-cancel]");
  if (btn) cancelBooking(Number(btn.dataset.cancel));
});

loadInstructors();
