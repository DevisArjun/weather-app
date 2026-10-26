// SkyPulse Weather Web App Client Script

let currentUnits = localStorage.getItem('skypulse_units') || 'metric';
let currentLocation = JSON.parse(localStorage.getItem('skypulse_location')) || {
    lat: 51.5074,
    lon: -0.1278,
    name: 'London, United Kingdom'
};

let hourlyChart = null;
let searchDebounceTimer = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    initUnitToggle();
    initSearch();
    initQuickChips();
    initGeolocation();
    
    // Load initial weather data
    loadWeather(currentLocation.lat, currentLocation.lon, currentLocation.name);
});

// Unit Toggle Handler
function initUnitToggle() {
    const btnC = document.getElementById('unit-c');
    const btnF = document.getElementById('unit-f');

    function updateButtonStyles() {
        if (currentUnits === 'metric') {
            btnC.className = 'px-3 py-1.5 text-xs font-semibold rounded-lg transition-all bg-sky-500 text-white shadow-sm';
            btnF.className = 'px-3 py-1.5 text-xs font-semibold rounded-lg transition-all text-slate-300 hover:text-white';
        } else {
            btnF.className = 'px-3 py-1.5 text-xs font-semibold rounded-lg transition-all bg-sky-500 text-white shadow-sm';
            btnC.className = 'px-3 py-1.5 text-xs font-semibold rounded-lg transition-all text-slate-300 hover:text-white';
        }
    }

    btnC.addEventListener('click', () => {
        if (currentUnits !== 'metric') {
            currentUnits = 'metric';
            localStorage.setItem('skypulse_units', currentUnits);
            updateButtonStyles();
            loadWeather(currentLocation.lat, currentLocation.lon, currentLocation.name);
        }
    });

    btnF.addEventListener('click', () => {
        if (currentUnits !== 'imperial') {
            currentUnits = 'imperial';
            localStorage.setItem('skypulse_units', currentUnits);
            updateButtonStyles();
            loadWeather(currentLocation.lat, currentLocation.lon, currentLocation.name);
        }
    });

    updateButtonStyles();
}

// Search & Autocomplete
function initSearch() {
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');
    const searchResults = document.getElementById('search-results');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        if (query.length > 0) {
            searchClear.classList.remove('hidden');
        } else {
            searchClear.classList.add('hidden');
            searchResults.classList.add('hidden');
            return;
        }

        clearTimeout(searchDebounceTimer);
        searchDebounceTimer = setTimeout(() => {
            fetchLocations(query);
        }, 300);
    });

    searchClear.addEventListener('click', () => {
        searchInput.value = '';
        searchClear.classList.add('hidden');
        searchResults.classList.add('hidden');
        searchInput.focus();
    });

    // Close search dropdown on click outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('hidden');
        }
    });

    // Enter key triggers first result or direct query
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                searchResults.classList.add('hidden');
                loadWeatherByCity(query);
            }
        }
    });
}

async function fetchLocations(query) {
    const searchResults = document.getElementById('search-results');
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const locations = await response.json();

        if (!locations || locations.length === 0) {
            searchResults.innerHTML = `
                <div class="px-4 py-3 text-xs text-slate-400">
                    No locations found. Press enter to search directly.
                </div>
            `;
            searchResults.classList.remove('hidden');
            return;
        }

        searchResults.innerHTML = locations.map(loc => `
            <button class="w-full text-left px-4 py-3 hover:bg-white/10 flex items-center justify-between text-sm transition-colors group"
                onclick="selectLocation(${loc.latitude}, ${loc.longitude}, '${loc.display_name.replace(/'/g, "\\'")}')">
                <span class="flex items-center gap-2 text-slate-200 group-hover:text-white">
                    <i data-lucide="map-pin" class="w-4 h-4 text-sky-400"></i>
                    <span>${loc.display_name}</span>
                </span>
                <span class="text-xs text-slate-400 font-mono">${loc.country_code || ''}</span>
            </button>
        `).join('');

        searchResults.classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    } catch (err) {
        console.error("Error fetching locations:", err);
    }
}

window.selectLocation = function(lat, lon, name) {
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');
    const searchResults = document.getElementById('search-results');

    searchInput.value = '';
    searchClear.classList.add('hidden');
    searchResults.classList.add('hidden');

    currentLocation = { lat, lon, name };
    localStorage.setItem('skypulse_location', JSON.stringify(currentLocation));
    loadWeather(lat, lon, name);
};

// Quick city chips
function initQuickChips() {
    document.querySelectorAll('.quick-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            const cityName = chip.getAttribute('data-city');
            loadWeatherByCity(cityName);
        });
    });
}

// Geolocation
function initGeolocation() {
    const btnGeo = document.getElementById('btn-geolocate');
    btnGeo.addEventListener('click', () => {
        if (!navigator.geolocation) {
            alert("Geolocation is not supported by your browser.");
            return;
        }

        btnGeo.classList.add('opacity-50', 'cursor-not-allowed');
        navigator.geolocation.getCurrentPosition(
            (position) => {
                btnGeo.classList.remove('opacity-50', 'cursor-not-allowed');
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                const name = `Local Coordinates (${lat.toFixed(2)}, ${lon.toFixed(2)})`;
                currentLocation = { lat, lon, name };
                localStorage.setItem('skypulse_location', JSON.stringify(currentLocation));
                loadWeather(lat, lon, name);
            },
            (error) => {
                btnGeo.classList.remove('opacity-50', 'cursor-not-allowed');
                alert(`Unable to get location: ${error.message}`);
            },
            { timeout: 10000, enableHighAccuracy: true }
        );
    });
}

// Load Weather API caller
async function loadWeatherByCity(city) {
    showLoading(true);
    try {
        const response = await fetch(`/api/weather?city=${encodeURIComponent(city)}&units=${currentUnits}`);
        const data = await response.json();
        if (data.error) {
            alert(data.error);
            showLoading(false);
            return;
        }
        currentLocation = {
            lat: data.latitude,
            lon: data.longitude,
            name: data.location_name
        };
        localStorage.setItem('skypulse_location', JSON.stringify(currentLocation));
        renderWeather(data);
    } catch (err) {
        alert("Failed to fetch weather data. Please try again.");
    } finally {
        showLoading(false);
    }
}

async function loadWeather(lat, lon, name) {
    showLoading(true);
    try {
        let url = `/api/weather?lat=${lat}&lon=${lon}&units=${currentUnits}`;
        if (name) url += `&city=${encodeURIComponent(name)}`;
        const response = await fetch(url);
        const data = await response.json();
        if (data.error) {
            alert(data.error);
            return;
        }
        renderWeather(data);
    } catch (err) {
        console.error("Error loading weather:", err);
    } finally {
        showLoading(false);
    }
}

function showLoading(isLoading) {
    const spinner = document.getElementById('loading-spinner');
    const content = document.getElementById('weather-content');
    if (isLoading) {
        spinner.classList.remove('hidden');
        content.classList.add('opacity-40', 'pointer-events-none');
    } else {
        spinner.classList.add('hidden');
        content.classList.remove('opacity-40', 'pointer-events-none');
    }
}

// Render Weather to UI
function renderWeather(data) {
    const cur = data.current;
    const tempUnit = cur.units.temp;
    const windUnit = cur.units.wind;

    // Set Atmospheric Theme
    const bodyContainer = document.getElementById('body-container');
    bodyContainer.className = `min-h-full font-sans antialiased text-slate-100 transition-colors duration-700 theme-${cur.theme}`;

    // Location & Hero
    document.getElementById('location-name').textContent = data.location_name;
    document.getElementById('local-time').textContent = `Local Time: ${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
    document.getElementById('current-temp').textContent = `${cur.temperature}${tempUnit}`;
    document.getElementById('current-desc').textContent = cur.description;
    document.getElementById('feels-like').textContent = `${cur.apparent_temperature}${tempUnit}`;

    if (data.daily && data.daily.length > 0) {
        document.getElementById('day-high').textContent = `${data.daily[0].max_temp}${tempUnit}`;
        document.getElementById('day-low').textContent = `${data.daily[0].min_temp}${tempUnit}`;
    }

    // Hero Icon
    const heroIcon = document.getElementById('hero-icon');
    heroIcon.setAttribute('data-lucide', cur.icon);

    // Detailed Metrics
    document.getElementById('metric-humidity').textContent = `${cur.humidity}%`;
    document.getElementById('bar-humidity').style.width = `${Math.min(cur.humidity, 100)}%`;

    document.getElementById('metric-wind').textContent = `${cur.wind_speed} ${windUnit}`;
    document.getElementById('metric-wind-dir').textContent = `${cur.wind_compass} (${cur.wind_direction}°)`;

    const uv = cur.uv_index || 0;
    document.getElementById('metric-uv').textContent = uv;
    let uvText = 'Low';
    let uvColor = 'text-emerald-400';
    if (uv > 2 && uv <= 5) { uvText = 'Moderate'; uvColor = 'text-amber-400'; }
    else if (uv > 5 && uv <= 7) { uvText = 'High'; uvColor = 'text-orange-400'; }
    else if (uv > 7) { uvText = 'Very High'; uvColor = 'text-rose-400'; }
    const uvElem = document.getElementById('metric-uv-level');
    uvElem.textContent = uvText;
    uvElem.className = `text-xs mt-1 font-medium ${uvColor}`;

    document.getElementById('metric-pressure').textContent = `${cur.pressure} hPa`;
    document.getElementById('metric-cloud').textContent = `${cur.cloud_cover}%`;
    document.getElementById('bar-cloud').style.width = `${Math.min(cur.cloud_cover, 100)}%`;

    document.getElementById('metric-sunrise').textContent = cur.sunrise || '--:--';
    document.getElementById('metric-sunset').textContent = cur.sunset || '--:--';

    // Render Hourly Carousel & Chart
    renderHourly(data.hourly || [], tempUnit);

    // Render 7-day Forecast
    renderDaily(data.daily || [], tempUnit);

    // Re-initialize Lucide Icons
    if (window.lucide) {
        lucide.createIcons();
    }
}

function renderHourly(hourlyData, tempUnit) {
    const hourlyContainer = document.getElementById('hourly-cards');
    hourlyContainer.innerHTML = hourlyData.slice(0, 24).map(h => `
        <div class="flex-shrink-0 flex flex-col items-center justify-between p-3.5 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/15 min-w-[76px] transition-all">
            <span class="text-xs text-slate-300 font-medium">${h.hour_label}</span>
            <div class="my-2 text-sky-300">
                <i data-lucide="${h.icon}" class="w-6 h-6"></i>
            </div>
            <span class="text-sm font-bold text-white">${h.temperature}${tempUnit}</span>
            <div class="flex items-center gap-1 text-[11px] text-sky-400 mt-1 font-medium">
                <i data-lucide="droplets" class="w-3 h-3"></i>
                <span>${h.pop}%</span>
            </div>
        </div>
    `).join('');

    // Update Chart.js
    const ctx = document.getElementById('hourly-chart').getContext('2d');
    const labels = hourlyData.slice(0, 24).map(h => h.hour_label);
    const temps = hourlyData.slice(0, 24).map(h => h.temperature);
    const pops = hourlyData.slice(0, 24).map(h => h.pop);

    if (hourlyChart) {
        hourlyChart.destroy();
    }

    const gradient = ctx.createLinearGradient(0, 0, 0, 180);
    gradient.addColorStop(0, 'rgba(56, 189, 248, 0.35)');
    gradient.addColorStop(1, 'rgba(56, 189, 248, 0.0)');

    hourlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: `Temperature (${tempUnit})`,
                    data: temps,
                    borderColor: '#38bdf8',
                    borderWidth: 2.5,
                    backgroundColor: gradient,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBackgroundColor: '#38bdf8',
                    yAxisID: 'y'
                },
                {
                    label: 'Rain Chance (%)',
                    data: pops,
                    type: 'bar',
                    backgroundColor: 'rgba(96, 165, 250, 0.25)',
                    hoverBackgroundColor: 'rgba(96, 165, 250, 0.5)',
                    borderRadius: 4,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#cbd5e1', font: { size: 11 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.85)',
                    titleColor: '#f8fafc',
                    bodyColor: '#cbd5e1',
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 1,
                    padding: 10,
                    cornerRadius: 8
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#94a3b8', font: { size: 11 }, maxRotation: 0 }
                },
                y: {
                    position: 'left',
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#94a3b8',
                        font: { size: 11 },
                        callback: function(value) { return value + tempUnit; }
                    }
                },
                y1: {
                    position: 'right',
                    min: 0,
                    max: 100,
                    grid: { display: false },
                    ticks: {
                        color: '#60a5fa',
                        font: { size: 10 },
                        callback: function(value) { return value + '%'; }
                    }
                }
            }
        }
    });
}

function renderDaily(dailyData, tempUnit) {
    const dailyContainer = document.getElementById('daily-forecast-list');
    
    // Calculate global min & max to render comparative temperature bars
    let minAll = Math.min(...dailyData.map(d => d.min_temp));
    let maxAll = Math.max(...dailyData.map(d => d.max_temp));
    if (minAll === maxAll) { maxAll += 1; }

    dailyContainer.innerHTML = dailyData.map(d => {
        const leftPercent = Math.max(0, Math.min(100, ((d.min_temp - minAll) / (maxAll - minAll)) * 100));
        const rightPercent = Math.max(0, Math.min(100, ((d.max_temp - minAll) / (maxAll - minAll)) * 100));
        const widthPercent = Math.max(8, rightPercent - leftPercent);

        return `
            <div class="pt-3 pb-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-sm hover:bg-white/5 px-2 rounded-xl transition-colors">
                <div class="flex items-center gap-3 w-40">
                    <span class="font-semibold text-white w-20">${d.day_name}</span>
                    <div class="flex items-center gap-1.5 text-xs text-sky-400">
                        <i data-lucide="droplets" class="w-3.5 h-3.5"></i>
                        <span>${d.pop}%</span>
                    </div>
                </div>

                <div class="flex items-center gap-3 flex-1">
                    <div class="w-7 h-7 flex items-center justify-center text-sky-300">
                        <i data-lucide="${d.icon}" class="w-5 h-5"></i>
                    </div>
                    <span class="text-xs text-slate-300 w-36 truncate">${d.description}</span>

                    <!-- Temperature range visualization -->
                    <div class="flex items-center gap-3 flex-1 max-w-xs ml-auto">
                        <span class="text-xs text-slate-400 font-mono w-9 text-right">${d.min_temp}${tempUnit}</span>
                        <div class="flex-1 bg-white/10 h-2 rounded-full relative overflow-hidden">
                            <div class="absolute h-full bg-gradient-to-r from-sky-400 via-amber-300 to-rose-400 rounded-full"
                                style="left: ${leftPercent}%; width: ${widthPercent}%;"></div>
                        </div>
                        <span class="text-xs text-white font-bold font-mono w-9">${d.max_temp}${tempUnit}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}
