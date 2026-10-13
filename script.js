const form = document.querySelector("#booking-form");
const status = document.querySelector("#form-status");
document.querySelector("#year").textContent = new Date().getFullYear();

// Use today's date as the earliest selectable booking date.
const dateInput = document.querySelector("#date");
const today = new Date();
dateInput.min = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  status.className = "form-status";
  status.textContent = "Sending your request…";
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    const response = await fetch("/api/bookings", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(data)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Could not submit the booking.");
    status.className = "form-status success";
    status.textContent = "Booking request submitted! Your reference is " + result.id + ".";
    form.reset();
    dateInput.min = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
  } catch (error) {
    status.className = "form-status error";
    status.textContent = error.message.includes("Failed to fetch")
      ? "The API is not connected yet. Follow README.md to configure and deploy the backend."
      : error.message;
  }
});