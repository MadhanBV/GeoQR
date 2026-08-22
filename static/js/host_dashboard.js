/**
 * GeoQR Host Live Dashboard Controller
 * Manages 25-second rolling QR code token rotation and real-time attendee polling.
 */

let totalDurationMs = (typeof QR_REFRESH_INTERVAL_SECONDS !== 'undefined' ? QR_REFRESH_INTERVAL_SECONDS : 50) * 1000;
let remainingMs = totalDurationMs;
let timerInterval = null;
let attendeePollInterval = null;
let isFetchingToken = false;

// DOM Elements
const qrImage = document.getElementById('qrImage');
const qrLoadingOverlay = document.getElementById('qrLoadingOverlay');
const countdownProgressBar = document.getElementById('countdownProgressBar');
const countdownText = document.getElementById('countdownText');
const directCheckinUrl = document.getElementById('directCheckinUrl');
const attendeeCountBadge = document.getElementById('attendeeCountBadge');
const attendeeTableBody = document.getElementById('attendeeTableBody');
const noAttendeesState = document.getElementById('noAttendeesState');
const lastUpdatedText = document.getElementById('lastUpdatedText');
const btnFullscreen = document.getElementById('btnFullscreen');

/**
 * Fetches a newly signed dynamic QR token from the backend.
 */
async function fetchNextQrToken() {
    if (isFetchingToken) return;
    isFetchingToken = true;

    try {
        if (qrLoadingOverlay) qrLoadingOverlay.classList.remove('hidden');

        const response = await fetch(`/api/event/${EVENT_ID}/qr-token`);
        if (!response.ok) {
            throw new Error(`Server returned ${response.status}`);
        }

        const data = await response.json();
        if (data.success && data.qr_image) {
            qrImage.src = data.qr_image;
            if (directCheckinUrl) {
                directCheckinUrl.value = data.checkin_url || '';
            }

            // Reset countdown to backend configured expiration
            if (data.expires_in) {
                totalDurationMs = data.expires_in * 1000;
            }
            remainingMs = totalDurationMs;
            updateCountdownUI();
        }
    } catch (err) {
        console.error("Failed to refresh QR token:", err);
    } finally {
        isFetchingToken = false;
        if (qrLoadingOverlay) qrLoadingOverlay.classList.add('hidden');
    }
}

/**
 * Updates the visual timer bar and digital countdown text.
 */
function updateCountdownUI() {
    const secondsLeft = Math.max(0, Math.ceil(remainingMs / 1000));
    countdownText.textContent = `${secondsLeft}s`;

    const percentage = Math.max(0, Math.min(100, (remainingMs / totalDurationMs) * 100));
    countdownProgressBar.style.width = `${percentage}%`;

    // Dynamic color shifting as expiry nears
    if (secondsLeft <= 5) {
        countdownProgressBar.className = "bg-red-500 h-full rounded-full transition-all duration-100 ease-linear";
        countdownText.className = "font-bold text-red-600 font-mono text-sm bg-red-50 px-2 py-0.5 rounded";
    } else if (secondsLeft <= 10) {
        countdownProgressBar.className = "bg-amber-500 h-full rounded-full transition-all duration-100 ease-linear";
        countdownText.className = "font-bold text-amber-700 font-mono text-sm bg-amber-50 px-2 py-0.5 rounded";
    } else {
        countdownProgressBar.className = "bg-blue-600 h-full rounded-full transition-all duration-100 ease-linear";
        countdownText.className = "font-bold text-slate-900 font-mono text-sm bg-slate-100 px-2 py-0.5 rounded";
    }
}

/**
 * Starts the high-resolution 100ms countdown timer.
 */
function startCountdown() {
    if (timerInterval) clearInterval(timerInterval);

    timerInterval = setInterval(() => {
        remainingMs -= 100;

        if (remainingMs <= 0) {
            remainingMs = 0;
            updateCountdownUI();
            fetchNextQrToken();
        } else {
            updateCountdownUI();
        }
    }, 100);
}

/**
 * Polls the backend for verified attendees list.
 */
async function pollAttendees() {
    try {
        const response = await fetch(`/api/event/${EVENT_ID}/attendees`);
        if (!response.ok) return;

        const data = await response.json();
        if (data.success) {
            const attendees = data.attendees || [];
            attendeeCountBadge.textContent = attendees.length;

            if (attendees.length === 0) {
                noAttendeesState.classList.remove('hidden');
                attendeeTableBody.innerHTML = '';
            } else {
                noAttendeesState.classList.add('hidden');
                renderAttendeesTable(attendees);
            }

            const now = new Date();
            lastUpdatedText.textContent = `Synced ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`;
        }
    } catch (err) {
        console.error("Attendee polling error:", err);
    }
}

/**
 * Formats and renders attendee rows in the live feed table.
 */
function renderAttendeesTable(attendees) {
    attendeeTableBody.innerHTML = attendees.map((att) => {
        const timeFormatted = new Date(att.timestamp * 1000).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        return `
            <tr class="hover:bg-slate-50 transition-colors">
                <td class="py-3 px-3">
                    <div class="font-bold text-slate-900">${escapeHtml(att.student_name)}</div>
                </td>
                <td class="py-3 px-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                        ${escapeHtml(att.student_id)}
                    </span>
                </td>
                <td class="py-3 px-3">
                    <span class="inline-flex items-center text-xs font-semibold text-emerald-600 font-mono">
                        <i class="fa-solid fa-location-dot text-[10px] mr-1 text-emerald-500"></i> ${att.distance_meters}m
                    </span>
                </td>
                <td class="py-3 px-3 text-right text-slate-400 font-mono text-[11px]">
                    ${timeFormatted}
                </td>
            </tr>
        `;
    }).join('');
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

/**
 * Copies the active check-in link to clipboard.
 */
function copyCheckinLink() {
    if (!directCheckinUrl.value) return;
    navigator.clipboard.writeText(directCheckinUrl.value).then(() => {
        const btn = document.getElementById('btnCopyLink');
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-check text-green-600 mr-1"></i> Copied!';
        setTimeout(() => {
            btn.innerHTML = originalHtml;
        }, 2000);
    });
}

// Fullscreen Toggle for Auditorium Projectors
if (btnFullscreen) {
    btnFullscreen.addEventListener('click', () => {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.warn(`Error attempting fullscreen: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    });
}

// Initialize on page load
function initDashboard() {
    startCountdown();
    pollAttendees();
    if (attendeePollInterval) clearInterval(attendeePollInterval);
    attendeePollInterval = setInterval(pollAttendees, 3500);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}

// Clean up intervals on page unload
window.addEventListener('beforeunload', () => {
    if (timerInterval) clearInterval(timerInterval);
    if (attendeePollInterval) clearInterval(attendeePollInterval);
});
