// app/static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIGURACIÓN ---
    const WELCOME_CURTAIN_DURATION = 1500; // Duración en milisegundos (reducida)

    // --- Lógica para la Cortina de Bienvenida ---
    const welcomeCurtain = document.getElementById('welcomeCurtain');
    const mainApp = document.getElementById('mainApp');

    console.log('main.js loaded.');
    console.log('welcomeCurtain element:', welcomeCurtain);
    console.log('mainApp element:', mainApp);

    const urlParams = new URLSearchParams(window.location.search);
    const fromLogin = urlParams.get('from_login');
    console.log('from_login parameter:', fromLogin);

    // Global function to start the welcome curtain animation
    window.startWelcomeCurtainAnimation = () => {
        if (welcomeCurtain) {
            welcomeCurtain.style.display = 'flex'; // Asegurarse de que la cortina sea visible para la animación
            document.body.classList.add('curtain-active'); // Prevent scrolling
            const welcomeSubtitle = document.getElementById('welcomeSubtitle');
            const setWelcomeMessage = () => {
                const hour = new Date().getHours();
                let message = "Que tengas un grandioso día, y haya suerte para encontrar los EEM que tal vez se quedaron en tu caja. Suerte amigo!";
                if (hour >= 18) { // Después de las 6 PM
                    message = "Ya es hora de alistar tus cosas para regresar a casa. ¿porque a la ultima hora? Suerte con la búsqueda!";
                } else if (hour >= 13) { // Entre la 1 PM y las 6 PM
                    message = "Despues del almuerzo espero que ahora si trabajes, y puedas encuentrar lo que buscas. Suerte!";
                }
                
                const formatMessage = (msg) => {
                    const commaIndex = msg.indexOf(',');
                    const periodIndex = msg.indexOf('.');
                    let splitIndex = -1;

                    if (commaIndex !== -1 && periodIndex !== -1) {
                        splitIndex = Math.min(commaIndex, periodIndex);
                    } else if (commaIndex !== -1) {
                        splitIndex = commaIndex;
                    } else {
                        splitIndex = periodIndex;
                    }

                    if (splitIndex !== -1) {
                        const firstPart = msg.substring(0, splitIndex + 1);
                        const restPart = msg.substring(splitIndex + 1);
                        return `<strong>${firstPart}</strong>${restPart}`;
                    }
                    return `<strong>${msg}</strong>`;
                };

                if (welcomeSubtitle) welcomeSubtitle.innerHTML = formatMessage(message);
            };

            setWelcomeMessage();

            setTimeout(() => {
                welcomeCurtain.classList.add('hide');
                welcomeCurtain.addEventListener('animationend', () => {
                    welcomeCurtain.style.display = 'none';
                    document.body.style.overflow = 'auto';
                    document.body.classList.remove('curtain-active'); // Re-enable scrolling
                    if (mainApp) mainApp.classList.add('visible');
                }, { once: true });
            }, WELCOME_CURTAIN_DURATION);
        }
    };

    if (fromLogin === 'true') {
        console.log('Coming from login page. Hiding curtain and showing main app.');
        if (welcomeCurtain) {
            welcomeCurtain.style.display = 'none';
            console.log('welcomeCurtain display set to none.');
        }
        if (mainApp) {
            mainApp.classList.add('visible');
            console.log('mainApp class added visible.');
        }
        document.body.style.overflow = 'auto'; // Ensure scroll is enabled
    } else if (welcomeCurtain) {
        window.startWelcomeCurtainAnimation(); // Start animation on non-login pages
    } else {
        if (mainApp) mainApp.classList.add('visible');
    }

    // --- Lógica Principal de la Aplicación ---
    let isDarkMode = true;
    let activeTab = 'internal';
    const body = document.getElementById('body');
    const themeToggle = document.getElementById('themeToggle');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const clearFile = document.getElementById('clearFile');
    const statusText = document.getElementById('statusText');
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const resultsContainer = document.getElementById('resultsContainer');
    const noResults = document.getElementById('noResults');

    // --- Modal de Detalles (Elementos y Eventos) ---
    const detailsModalOverlay = document.getElementById('detailsModalOverlay');
    const modalDataElement = document.getElementById('modalData');
    const modalCloseBtn = detailsModalOverlay.querySelector('.modal-close-btn');

    if (modalCloseBtn) {
        modalCloseBtn.addEventListener('click', () => {
            detailsModalOverlay.style.display = 'none';
        });
    }

    if (detailsModalOverlay) {
        detailsModalOverlay.addEventListener('click', (event) => {
            if (event.target === detailsModalOverlay) {
                detailsModalOverlay.style.display = 'none';
            }
        });
    }

    const showDetailsModal = (data) => {
        if (modalDataElement) modalDataElement.textContent = JSON.stringify(data, null, 2);
        if (detailsModalOverlay) detailsModalOverlay.style.display = 'block';
    };

    const toggleTheme = () => {
        isDarkMode = !isDarkMode;
        if (body) body.className = isDarkMode ? 'dark-mode' : 'light-mode';
        if (themeToggle) themeToggle.innerHTML = isDarkMode ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    };

    const switchTab = (targetTab) => {
        activeTab = targetTab;
        if (tabContents) tabContents.forEach(c => c.classList.remove('active'));
        if (tabButtons) tabButtons.forEach(b => b.classList.remove('active'));
        const targetContent = document.getElementById(targetTab);
        const targetButton = document.querySelector(`[data-tab="${targetTab}"]`);
        if (targetContent) targetContent.classList.add('active');
        if (targetButton) targetButton.classList.add('active');
        updateStatus();
        clearResults();
    };

    const showLoading = (show) => { if (loading) loading.style.display = show ? 'block' : 'none'; };
    const clearResults = () => { 
        if (resultsContainer) resultsContainer.innerHTML = ''; 
        if (noResults) noResults.style.display = 'none'; 
    };
    const updateFileInfo = (filename) => {
        if (fileInfo) {
            if (filename) { 
                if (fileName) fileName.textContent = filename; 
                fileInfo.style.display = 'flex'; 
            } else { 
                fileInfo.style.display = 'none'; 
            }
        }
    };

    const updateStatus = async () => {
        try {
            const response = await fetch('/status');
            const status = await response.json();
            if (activeTab === 'excel') {
                if (statusText) {
                    statusText.textContent = status.has_excel_data
                        ? `${status.records} registros cargados de ${status.filename}`
                        : 'Sube un archivo para buscar en tus datos.';
                }
            }
            updateFileInfo(status.has_excel_data ? status.filename : null);
        } catch (error) {
            console.error('Error al obtener estado:', error);
            if (statusText) statusText.textContent = 'Error al conectar con el servidor.';
        }
    };

    const handleFileUpload = async () => {
        if (!fileInput) return;
        const file = fileInput.files[0];
        if (!file) return;
        const formData = new FormData();
        formData.append('file', file);
        showLoading(true);
        try {
            const response = await fetch('/upload', { method: 'POST', body: formData });
            const result = await response.json();
            if (result.error) throw new Error(result.error);
            if (result.success) switchTab('excel');
        } catch (error) {
            alert(`Error al subir el archivo: ${error.message}`);
        } finally {
            showLoading(false);
            fileInput.value = '';
        }
    };

    const handleClearFile = async () => {
        showLoading(true);
        try {
            await fetch('/clear', { method: 'POST' });
            switchTab('internal');
        } catch (error) { alert('Error al limpiar los datos.'); }
        finally { showLoading(false); }
    };

    const handleSearch = async () => {
        if (!searchInput) return;
        const query = searchInput.value.trim();
        if (!query) { clearResults(); return; }
        clearResults();
        showLoading(true);
        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: query, dataSource: activeTab })
            });
            const data = await response.json();
            if (data.error) throw new Error(data.error);
            displayResults(data);
        } catch (error) {
            console.error('Error en la búsqueda:', error);
            if (noResults) {
                noResults.textContent = `Error en la búsqueda: ${error.message}`;
                noResults.style.display = 'block';
            }
        } finally {
            showLoading(false);
        }
    };

    const createResultCard = (result) => {
        const item = document.createElement('div');
        item.className = 'flip-card';

        const keys = Object.keys(result);

        // Front face data
        const title = result[keys[0]] || 'Documento';
        const subtitle1 = keys.length > 1 ? `${result[keys[1]]}` : '';
        const subtitle2 = keys.length > 4 ? `${result[keys[4]]}` : '';

        // Back face data
        const backData1 = keys[2] ? `{ Exp. BN : ${result[keys[2]]} }` : '';
        const backData2 = keys[6] ? `Oficio/carta : ${result[keys[6]]}` : '';
        const backData3 = keys[8] ? `${result[keys[8]]}` : '';


        item.innerHTML = `
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <h3 class="result-title">${title}</h3>
                    <div class="modern-line"></div>
                    <p class="result-subtitle1">${subtitle1}</p>
                    <p class="result-subtitle2">${subtitle2}</p>
                </div>
                <div class="flip-card-back">
                    <p class="back-data"><strong>${backData1}</strong></p>
                    <p class="back-data">${backData2}</p>
                    <p class="highlighted-back-data">${backData3}</p>
                </div>
            </div>
        `;

        item.addEventListener('click', () => {
            item.classList.toggle('is-flipped');
        });

        return item;
    };

    const displayResults = (data) => {
        if (!resultsContainer || !noResults) return;
        const { results } = data;
        resultsContainer.innerHTML = '';
        if (results.length === 0) {
            noResults.style.display = 'block';
            return;
        }

        noResults.style.display = 'none';
        resultsContainer.className = 'results-grid';

        results.forEach(result => {
            const card = createResultCard(result);
            resultsContainer.appendChild(card);
        });
    };

    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
    if (tabButtons) tabButtons.forEach(b => b.addEventListener('click', () => switchTab(b.dataset.tab)));
    if (fileInput) fileInput.addEventListener('change', handleFileUpload);
    if (clearFile) clearFile.addEventListener('click', handleClearFile);
    if (searchBtn) searchBtn.addEventListener('click', handleSearch);
    if (searchInput) searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSearch(); });

    if (!document.body.classList.contains('login-page')) {
        updateStatus();
    }

    const animationContainer = document.querySelector('.animation-container');
    if (animationContainer) {
        const dots = document.querySelectorAll('.dot');
        const visibleDots = document.querySelectorAll('.dot.lock-visible, .dot.lock-arc');

        anime.set(dots, { scale: 0, opacity: 0 });

        const timeline = anime.timeline({
            loop: false,
            autoplay: true,
            easing: 'easeInOutQuad',
        });

        timeline.add({
            targets: visibleDots,
            scale: [0, 1],
            opacity: [0, 1],
            delay: anime.stagger(50),
            duration: 800
        })
        .add({
            targets: '.dot:not(.lock-arc)',
            scale: [1.1, 1],
            rotate: [0, 360],
            delay: anime.stagger(100, {grid: [15, 15], from: 'center'}),
            duration: 1000,
            easing: 'easeOutElastic(1, .8)'
        }, '-=500')
        .add({
            targets: '.dot.lock-arc',
            scale: [1, 1],
            backgroundColor: [
                'var(--secondary-color)',
                'var(--cyan-color)'
            ],
            delay: anime.stagger(150),
            duration: 500
        }, '-=800');
    }
});