// Weather Harvester Web Application JavaScript

const API_BASE_URL = '/api';

// DOM Elements
const cityInput = document.getElementById('cityInput');
const searchBtn = document.getElementById('searchBtn');
const clearCacheBtn = document.getElementById('clearCacheBtn');
const cacheInfoBtn = document.getElementById('cacheInfoBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMessage = document.getElementById('errorMessage');
const weatherCard = document.getElementById('weatherCard');
const alertsContainer = document.getElementById('alertsContainer');

// Event Listeners
searchBtn.addEventListener('click', handleSearch);
cityInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSearch();
    }
});
clearCacheBtn.addEventListener('click', handleClearCache);
cacheInfoBtn.addEventListener('click', handleCacheInfo);

/**
 * Handle weather search
 */
async function handleSearch() {
    const city = cityInput.value.trim();
    
    if (!city) {
        showError('Please enter a city name');
        return;
    }
    
    // Hide previous results
    hideError();
    hideWeatherCard();
    hideAlerts();
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/weather?city=${encodeURIComponent(city)}&use_cache=true`);
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            displayWeather(data);
            if (data.alerts && data.alerts.length > 0) {
                displayAlerts(data.alerts);
            }
        } else {
            showError(data.error || 'Failed to fetch weather data');
        }
    } catch (error) {
        hideLoading();
        showError('Network error. Please check your connection and try again.');
        console.error('Error:', error);
    }
}

/**
 * Display weather data
 */
function displayWeather(data) {
    const weather = data.data;
    
    // Update header
    document.getElementById('cityName').textContent = weather.city;
    document.getElementById('countryName').textContent = weather.country;
    document.getElementById('weatherIcon').src = data.icon_url;
    document.getElementById('weatherIcon').alt = weather.description;
    
    // Update temperature
    document.getElementById('temperature').textContent = weather.temperature;
    document.getElementById('feelsLike').textContent = `Feels like ${weather.feels_like}°C`;
    document.getElementById('description').textContent = weather.description;
    
    // Update details
    document.getElementById('windSpeed').textContent = `${weather.wind_speed} km/h`;
    document.getElementById('windDirection').textContent = data.wind_direction || 'N/A';
    document.getElementById('humidity').textContent = `${weather.humidity}%`;
    document.getElementById('pressure').textContent = `${weather.pressure} hPa`;
    document.getElementById('clouds').textContent = `${weather.clouds}%`;
    document.getElementById('visibility').textContent = weather.visibility ? `${weather.visibility} km` : 'N/A';
    
    // Show cache badge if data is cached
    const cacheBadge = document.getElementById('cacheBadge');
    if (data.cached) {
        cacheBadge.classList.remove('hidden');
    } else {
        cacheBadge.classList.add('hidden');
    }
    
    // Show weather card
    weatherCard.classList.remove('hidden');
    
    // Scroll to weather card
    weatherCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Display weather alerts
 */
function displayAlerts(alerts) {
    alertsContainer.innerHTML = '';
    
    alerts.forEach(alert => {
        const alertElement = document.createElement('div');
        alertElement.className = `alert ${alert.severity}`;
        
        alertElement.innerHTML = `
            <span class="alert-icon">${alert.icon}</span>
            <span class="alert-message">${alert.message}</span>
        `;
        
        alertsContainer.appendChild(alertElement);
    });
    
    alertsContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Handle clear cache
 */
async function handleClearCache() {
    if (!confirm('Are you sure you want to clear all cached weather data?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/cache/clear`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.success) {
            alert('Cache cleared successfully!');
        } else {
            alert('Failed to clear cache: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error clearing cache. Please try again.');
        console.error('Error:', error);
    }
}

/**
 * Handle cache info
 */
async function handleCacheInfo() {
    try {
        const response = await fetch(`${API_BASE_URL}/cache/info`);
        const data = await response.json();
        
        if (data.success) {
            const info = data.data;
            let message = `Total cached cities: ${info.total_cached}\n\n`;
            
            if (info.cities.length > 0) {
                message += 'Cached cities:\n';
                info.cities.forEach(city => {
                    const expiresIn = city.expires_in > 0
                        ? `${Math.floor(city.expires_in / 60)}m ${city.expires_in % 60}s`
                        : 'Expired';
                    message += `• ${city.city} (expires in: ${expiresIn})\n`;
                });
            } else {
                message += 'No cities currently cached.';
            }
            
            alert(message);
        } else {
            alert('Failed to get cache info: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        alert('Error getting cache info. Please try again.');
        console.error('Error:', error);
    }
}

/**
 * Show loading indicator
 */
function showLoading() {
    loadingIndicator.classList.remove('hidden');
}

/**
 * Hide loading indicator
 */
function hideLoading() {
    loadingIndicator.classList.add('hidden');
}

/**
 * Show error message
 */
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
}

/**
 * Hide error message
 */
function hideError() {
    errorMessage.classList.add('hidden');
}

/**
 * Show weather card
 */
function showWeatherCard() {
    weatherCard.classList.remove('hidden');
}

/**
 * Hide weather card
 */
function hideWeatherCard() {
    weatherCard.classList.add('hidden');
}

/**
 * Hide alerts
 */
function hideAlerts() {
    alertsContainer.innerHTML = '';
}

// Focus on input when page loads
window.addEventListener('load', () => {
    cityInput.focus();
});
