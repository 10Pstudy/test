function startTimer(remainingTimeMs) {
    const progressBar = document.getElementById('progress-bar');
    const startTime = Date.now();
    const initialTime = remainingTimeMs;

    const updateProgress = () => {
        const elapsed = Date.now() - startTime;
        const remaining = Math.max(0, initialTime - elapsed);
        const percentage = (remaining / initialTime) * 100;
        progressBar.style.width = percentage + '%';

        // 色を変更（残り時間が少ないほど赤に近づく）
        if (percentage > 50) {
            progressBar.style.backgroundColor = '#4caf50'; // 緑
        } else if (percentage > 20) {
            progressBar.style.backgroundColor = '#ff9800'; // オレンジ
        } else {
            progressBar.style.backgroundColor = '#f44336'; // 赤
        }

        if (remaining <= 0) {
            // 時間切れで結果ページへ
            window.location.href = '/result';
        } else {
            setTimeout(updateProgress, 100);
        }
    };

    updateProgress();
}