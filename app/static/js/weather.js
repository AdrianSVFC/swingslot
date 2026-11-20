// Shows today's weather at the instructor's location using the free Open-Meteo API.
(function () {
  const box = document.getElementById("weatherBox");
  if (!box) return;

  const lat = box.dataset.lat;
  const lon = box.dataset.lon;
  const url = "https://api.open-meteo.com/v1/forecast?latitude=" + lat + "&longitude=" + lon +
    "&current=temperature_2m,wind_speed_10m,weather_code" +
    "&temperature_unit=fahrenheit&wind_speed_unit=mph&timezone=auto";

  // WMO weather codes -> short description
  function describe(code) {
    if (code === 0) return "Clear sky";
    if (code <= 3) return "Partly cloudy";
    if (code <= 48) return "Fog";
    if (code <= 67) return "Rain";
    if (code <= 77) return "Snow";
    if (code <= 82) return "Showers";
    return "Thunderstorm";
  }

  fetch(url)
    .then(function (response) {
      if (!response.ok) throw new Error("HTTP " + response.status);
      return response.json();
    })
    .then(function (data) {
      const c = data.current;
      box.textContent = "Course weather now: " + Math.round(c.temperature_2m) + "°F, " +
        describe(c.weather_code) + ", wind " + Math.round(c.wind_speed_10m) + " mph";
    })
    .catch(function () {
      box.textContent = "Course weather is not available right now.";
    });
})();
