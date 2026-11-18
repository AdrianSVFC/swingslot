// Course conditions from the free Open-Meteo API (no API key needed)
const WEATHER_URL = "https://api.open-meteo.com/v1/forecast";

const weatherCodes = {
  0: "Clear sky", 1: "Mostly clear", 2: "Partly cloudy", 3: "Overcast",
  45: "Fog", 48: "Fog", 51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
  61: "Light rain", 63: "Rain", 65: "Heavy rain", 80: "Rain showers",
  81: "Rain showers", 82: "Heavy showers", 95: "Thunderstorm"
};

async function getCourseConditions(lat, lon) {
  const url = `${WEATHER_URL}?latitude=${lat}&longitude=${lon}` +
    "&current=temperature_2m,wind_speed_10m,weather_code" +
    "&temperature_unit=fahrenheit&wind_speed_unit=mph";

  const response = await fetch(url);
  const data = await response.json();

  return {
    temp: Math.round(data.current.temperature_2m),
    wind: Math.round(data.current.wind_speed_10m),
    sky: weatherCodes[data.current.weather_code] || "Unknown"
  };
}

function golfAdvice(conditions) {
  if (conditions.sky.includes("Thunder")) return "Lightning risk: lessons may be moved indoors.";
  if (conditions.wind > 15) return "Windy day: great for practicing low, controlled shots.";
  if (conditions.temp < 45) return "Cold day: bring layers and expect less distance.";
  return "Great conditions for a lesson!";
}

async function showWeather(instructor, box) {
  box.textContent = "Loading course conditions...";
  const c = await getCourseConditions(instructor.lat, instructor.lon);
  box.innerHTML = `
    <strong>Course conditions in ${instructor.location}:</strong>
    ${c.temp}&deg;F, ${c.sky}, wind ${c.wind} mph<br>
    <span class="small">${golfAdvice(c)}</span>`;
}
