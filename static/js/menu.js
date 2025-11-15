// UI interactions
document.addEventListener('DOMContentLoaded', () => {
	const newBtn = document.getElementById('new-game');
	const settingsBtn = document.getElementById('settings');
	const creditsBtn = document.getElementById('credits');
    const startBtn = document.getElementById('start-button');
    const backBtn = document.getElementById('back-button');

	if (newBtn) {
		newBtn.addEventListener('click', () => {
			// navigate to ingame page (adjust path if your server routes differ)
			window.location.href = 'tutorial.html';
		});
	}

	if (settingsBtn) {
		settingsBtn.addEventListener('click', () => {
			window.location.href = 'settings.html';
		});
	}

	if (creditsBtn) {
		creditsBtn.addEventListener('click', () => {
			window.location.href = 'credits.html';
		});
	}

	// Start button on tutorial -> go to game
	if (startBtn) {
		startBtn.addEventListener('click', () => {
			window.location.href = 'game.html';
		});
	}

    if (backBtn) {
        backBtn.addEventListener('click', function () {
            // Navigate to the index page
            window.location.href = 'index.html';
        });
    }

	// Theme toggle: switch between day and night backgrounds
	const themeToggle = document.getElementById('theme-toggle');

	function applyTheme(theme){
		const isNight = theme === 'night';
		document.body.classList.toggle('night-mode', isNight);
		if(themeToggle){
			themeToggle.setAttribute('aria-pressed', String(isNight));
			themeToggle.textContent = isNight ? '☀️ Toggle Day' : '🌙 Toggle Night';
		}
	}

	// initialise from localStorage
	const saved = localStorage.getItem('theme') || 'day';
	applyTheme(saved);

	if(themeToggle){
		themeToggle.addEventListener('click', () => {
			const now = document.body.classList.contains('night-mode') ? 'day' : 'night';
			localStorage.setItem('theme', now);
			applyTheme(now);
		});
	}

});
