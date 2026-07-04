document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const mainDashboard = document.getElementById('dashboard');
    const refreshBtn = document.getElementById('refresh-btn');
    const repairBtn = document.getElementById('repair-btn');
    const repairText = repairBtn.querySelector('.btn-text');
    const repairLoader = repairBtn.querySelector('.loader-spinner');
    
    // API URL
    const API_BASE = 'http://localhost:5000/api';

    // Circle circumference for progress ring
    const circle = document.getElementById('score-ring');
    const radius = circle.r.baseVal.value;
    const circumference = radius * 2 * Math.PI;
    circle.style.strokeDasharray = `${circumference} ${circumference}`;

    // Initialize Dashboard
    fetchHealthData();

    // Event Listeners
    refreshBtn.addEventListener('click', () => {
        mainDashboard.classList.remove('loaded');
        fetchHealthData();
    });

    repairBtn.addEventListener('click', () => {
        if(confirm("Are you sure you want to run the autonomous remediation workflow? This may restart services or clear temporary files.")) {
            triggerRepair();
        }
    });

    // API Calls
    async function fetchHealthData() {
        try {
            const response = await fetch(`${API_BASE}/health`);
            const data = await response.json();
            
            if (data.status === 'success') {
                updateDashboard(data.diagnostics, data.evaluation);
            } else {
                alert("Error fetching health data: " + data.message);
            }
        } catch (error) {
            console.error("Fetch error:", error);
            document.getElementById('status-msg').textContent = "Failed to connect to agent backend.";
            document.getElementById('status-msg').style.color = "var(--danger)";
        } finally {
            setTimeout(() => {
                mainDashboard.classList.add('loaded');
            }, 500);
        }
    }

    async function triggerRepair() {
        repairText.textContent = "Healing System...";
        repairLoader.classList.remove('hidden');
        repairBtn.disabled = true;

        try {
            const response = await fetch(`${API_BASE}/repair`, { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                updateDashboard(data.diagnostics, data.evaluation);
                alert("Auto-remediation complete! System health updated.");
            } else {
                alert("Repair failed: " + data.message);
            }
        } catch (error) {
            alert("Connection error during repair.");
        } finally {
            repairText.textContent = "Auto-Heal System";
            repairLoader.classList.add('hidden');
            repairBtn.disabled = false;
        }
    }

    // UI Updaters
    function updateDashboard(diag, eval) {
        updateHeroScore(eval.overall, eval.rating);
        
        // CPU
        if (diag.cpu !== undefined) {
            updateBarMetric('cpu', diag.cpu, eval.components.cpu);
        }
        
        // RAM
        if (diag.memory) {
            updateBarMetric('ram', diag.memory.used_percent, eval.components.memory);
            document.getElementById('ram-subtext').textContent = `Free: ${(diag.memory.free_kb / 1024 / 1024).toFixed(2)} GB`;
        }

        // Storage
        if (diag.storage) {
            updateBarMetric('disk', 100 - diag.storage.free_percent, eval.components.storage);
            document.getElementById('disk-subtext').textContent = `Free: ${diag.storage.free_gb.toFixed(1)} GB / ${diag.storage.size_gb.toFixed(1)} GB`;
        }

        // Hardware Drivers
        if (diag.drivers) {
            document.getElementById('drvs-total').textContent = diag.drivers.total_checked || 0;
            document.getElementById('drvs-failed').textContent = diag.drivers.failed_devices?.length || 0;
            document.getElementById('drvs-missing').textContent = diag.drivers.missing_drivers?.length || 0;
            document.getElementById('drvs-conflict').textContent = diag.drivers.conflicting_drivers?.length || 0;
        }

        // System Integrity
        if (diag.smart) {
            const smartEl = document.getElementById('smart-status');
            smartEl.textContent = diag.smart.overall_status;
            smartEl.className = diag.smart.overall_status === 'Healthy' ? 'success-text' : 'danger-text';
        }

        if (diag.services) {
            const stoppedCount = diag.services.stopped_services?.length || 0;
            document.getElementById('services-stopped').textContent = stoppedCount;
            if(stoppedCount > 0) document.getElementById('services-stopped').style.color = "var(--danger)";
        }

        if (diag.updates) {
            document.getElementById('updates-pending').textContent = `${diag.updates.pending_count || 0} Pending`;
        }
    }

    function updateHeroScore(score, rating) {
        const scoreEl = document.getElementById('overall-score');
        const ratingEl = document.getElementById('overall-rating');
        const msgEl = document.getElementById('status-msg');

        // Animate counter
        animateValue(scoreEl, parseInt(scoreEl.textContent), Math.round(score), 1000);
        
        ratingEl.textContent = rating.toUpperCase();
        
        // Set Ring Color and Progress
        const offset = circumference - (score / 100) * circumference;
        circle.style.strokeDashoffset = offset;

        let color = "var(--success)";
        let msg = "System is optimized and running smoothly.";
        
        if (score < 50) {
            color = "var(--danger)";
            msg = "Critical issues detected. Immediate healing required.";
        } else if (score < 80) {
            color = "var(--warning)";
            msg = "System needs attention. Sub-optimal performance.";
        }

        circle.style.stroke = color;
        ratingEl.style.color = color;
        msgEl.textContent = msg;
    }

    function updateBarMetric(prefix, percentValue, componentScore) {
        document.getElementById(`${prefix}-value`).textContent = percentValue.toFixed(1);
        const bar = document.getElementById(`${prefix}-bar`);
        bar.style.width = `${percentValue}%`;

        // Set bar color based on usage percentage (lower is better for usage)
        let color = "var(--success)";
        if (percentValue > 85) color = "var(--danger)";
        else if (percentValue > 70) color = "var(--warning)";
        
        bar.style.backgroundColor = color;

        // Update badge
        const badge = document.getElementById(`${prefix}-score-badge`);
        badge.textContent = `Score: ${Math.round(componentScore)}`;
        badge.className = "badge"; // reset
        if (componentScore >= 80) badge.classList.add("good");
        else if (componentScore >= 50) badge.classList.add("warn");
        else badge.classList.add("critical");
    }

    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }
});
