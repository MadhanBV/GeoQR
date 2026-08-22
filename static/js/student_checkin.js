/**
 * GeoQR Student Check-in Controller
 * Requests mobile GPS coordinates with high accuracy and handles attendance submission.
 */

const form = document.getElementById('studentCheckinForm');
const inputLat = document.getElementById('student_lat');
const inputLon = document.getElementById('student_lon');
const inputToken = document.getElementById('token');
const inputEventId = document.getElementById('event_id');
const inputStudentName = document.getElementById('student_name');
const inputStudentId = document.getElementById('student_id');

const gpsStatusContainer = document.getElementById('gpsStatusContainer');
const gpsIconBox = document.getElementById('gpsIconBox');
const gpsIcon = document.getElementById('gpsIcon');
const gpsStatusTitle = document.getElementById('gpsStatusTitle');
const gpsStatusSub = document.getElementById('gpsStatusSub');
const btnRetryGps = document.getElementById('btnRetryGps');
const gpsErrorAlert = document.getElementById('gpsErrorAlert');

const btnSubmit = document.getElementById('btnSubmitAttendance');
const btnSubmitText = document.getElementById('btnSubmitText');
const formErrorBanner = document.getElementById('formErrorBanner');
const formErrorMessage = document.getElementById('formErrorMessage');

let gpsAcquired = false;

/**
 * Requests GPS coordinates from the mobile browser with smart tiered fallback.
 * Tier 1: Try High Accuracy (GPS hardware) with 15s timeout and 30s max age.
 * Tier 2: If Tier 1 times out indoors, automatically fall back to balanced Wi-Fi/Cellular positioning.
 */
function acquireGpsLocation() {
    if (!navigator.geolocation) {
        showGpsError("Geolocation is not supported by your browser.");
        return;
    }

    gpsStatusContainer.className = "mb-5 p-3.5 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-between";
    gpsIconBox.className = "w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center text-sm shadow-sm";
    gpsIcon.className = "fa-solid fa-satellite-dish fa-spin";
    gpsStatusTitle.textContent = "Acquiring GPS Signal...";
    gpsStatusSub.textContent = "Locking device location...";
    btnRetryGps.classList.add('hidden');
    gpsErrorAlert.classList.add('hidden');

    btnSubmit.disabled = true;
    btnSubmit.className = "w-full py-3.5 px-4 rounded-xl bg-slate-300 text-slate-500 font-bold text-sm flex items-center justify-center space-x-2 cursor-not-allowed";
    btnSubmitText.textContent = "Waiting for GPS...";

    function onGpsSuccess(position) {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        const accuracy = Math.round(position.coords.accuracy);

        inputLat.value = lat;
        inputLon.value = lon;
        gpsAcquired = true;

        // Update UI to Success State
        gpsStatusContainer.className = "mb-5 p-3.5 rounded-xl bg-green-50 border border-green-200 flex items-center justify-between";
        gpsIconBox.className = "w-8 h-8 rounded-lg bg-green-600 text-white flex items-center justify-center text-sm shadow-sm";
        gpsIcon.className = "fa-solid fa-check";
        gpsStatusTitle.textContent = "GPS Location Locked";
        gpsStatusSub.textContent = `Accuracy: \u00B1${accuracy}m (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
        btnRetryGps.classList.remove('hidden');
        btnRetryGps.textContent = "Re-check";

        // Enable Submit Button
        btnSubmit.disabled = false;
        btnSubmit.className = "w-full py-3.5 px-4 rounded-xl bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white font-bold text-sm flex items-center justify-center space-x-2 shadow-md shadow-blue-500/20 transition-all duration-200 cursor-pointer";
        btnSubmitText.textContent = "Submit Attendance";
    }

    function onGpsErrorTier1(error) {
        if (error.code === error.PERMISSION_DENIED) {
            gpsAcquired = false;
            gpsErrorAlert.classList.remove('hidden');
            showGpsError("Location permission was denied.");
            return;
        }

        // If high accuracy times out (common indoors), seamlessly fall back to balanced network location
        gpsStatusSub.textContent = "Calibrating indoor position...";
        navigator.geolocation.getCurrentPosition(
            onGpsSuccess,
            (finalError) => {
                gpsAcquired = false;
                let message = "Unable to retrieve your location.";
                if (finalError.code === finalError.PERMISSION_DENIED) {
                    message = "Location permission was denied.";
                    gpsErrorAlert.classList.remove('hidden');
                } else if (finalError.code === finalError.POSITION_UNAVAILABLE) {
                    message = "GPS signal unavailable. Please ensure Device Location is turned ON.";
                } else if (finalError.code === finalError.TIMEOUT) {
                    message = "Location timed out. Please tap 'Retry GPS'.";
                }
                showGpsError(message);
            },
            {
                enableHighAccuracy: false, // Balanced mode (Wi-Fi / Cell positioning)
                timeout: 15000,
                maximumAge: 60000 // Accept recent position up to 1 minute old
            }
        );
    }

    // Tier 1: Try High Accuracy first
    navigator.geolocation.getCurrentPosition(
        onGpsSuccess,
        onGpsErrorTier1,
        {
            enableHighAccuracy: true,
            timeout: 12000,
            maximumAge: 30000 // Accept recent position up to 30 seconds old
        }
    );
}

function showGpsError(message) {
    gpsStatusContainer.className = "mb-5 p-3.5 rounded-xl bg-red-50 border border-red-200 flex items-center justify-between";
    gpsIconBox.className = "w-8 h-8 rounded-lg bg-red-500 text-white flex items-center justify-center text-sm shadow-sm";
    gpsIcon.className = "fa-solid fa-triangle-exclamation";
    gpsStatusTitle.textContent = "GPS Access Required";
    gpsStatusSub.textContent = message;
    btnRetryGps.classList.remove('hidden');
    btnRetryGps.textContent = "Retry GPS";

    btnSubmit.disabled = true;
    btnSubmit.className = "w-full py-3.5 px-4 rounded-xl bg-slate-300 text-slate-500 font-bold text-sm flex items-center justify-center space-x-2 cursor-not-allowed";
    btnSubmitText.textContent = "GPS Location Required";
}

// Handle Form Submission
if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Hide prior errors
        formErrorBanner.classList.add('hidden');

        if (!gpsAcquired || !inputLat.value || !inputLon.value) {
            formErrorMessage.textContent = "Please allow GPS location access before submitting.";
            formErrorBanner.classList.remove('hidden');
            return;
        }

        const payload = {
            event_id: inputEventId.value,
            token: inputToken.value,
            student_name: inputStudentName.value.trim(),
            student_id: inputStudentId.value.trim(),
            student_lat: parseFloat(inputLat.value),
            student_lon: parseFloat(inputLon.value)
        };

        // Loading State
        btnSubmit.disabled = true;
        btnSubmitText.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Verifying Attendance...';

        try {
            const response = await fetch('/api/attendance/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const result = await response.json();

            if (result.redirect_url) {
                // Navigate to the status result page
                window.location.href = result.redirect_url;
            } else if (!result.success) {
                formErrorMessage.textContent = result.message || "Attendance verification failed.";
                formErrorBanner.classList.remove('hidden');
                btnSubmit.disabled = false;
                btnSubmitText.textContent = "Retry Submission";
            }
        } catch (err) {
            console.error("Submission failed:", err);
            formErrorMessage.textContent = "Network error while submitting. Please check your connection and retry.";
            formErrorBanner.classList.remove('hidden');
            btnSubmit.disabled = false;
            btnSubmitText.textContent = "Retry Submission";
        }
    });
}

// Auto-trigger GPS capture immediately when the page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', acquireGpsLocation);
} else {
    acquireGpsLocation();
}
