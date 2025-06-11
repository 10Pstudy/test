function startTimer(remainingTimeMs) {
    const progressBar = document.getElementById('progress-bar');
    const timeRemaining = document.getElementById('time-remaining');
    const startTime = Date.now();
    const initialTime = remainingTimeMs;

    const updateProgress = () => {
        const elapsed = Date.now() - startTime;
        const remaining = Math.max(0, initialTime - elapsed);
        const percentage = (remaining / initialTime) * 100;
        progressBar.style.width = percentage + '%';

        // 残り秒数を表示
        const seconds = Math.ceil(remaining / 1000);
        timeRemaining.textContent = `残り: ${seconds}秒`;

        // 色を変更
        if (percentage > 50) {
            progressBar.style.backgroundColor = '#4caf50';
        } else if (percentage > 20) {
            progressBar.style.backgroundColor = '#ff9800';
        } else {
            progressBar.style.backgroundColor = '#f44336';
        }

        if (remaining <= 0) {
            window.location.href = '/result';
        } else {
            setTimeout(updateProgress, 100);
        }
    };

    updateProgress();
}