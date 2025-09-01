// app/static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIGURACIÓN ---
    const WELCOME_CURTAIN_DURATION = 9000; // Duración en milisegundos

    // --- Lógica para la Cortina de Bienvenida ---
    const welcomeCurtain = document.getElementById('welcomeCurtain');
    const mainApp = document.getElementById('mainApp');
    
    // Check if it's the login page
    if (document.body.classList.contains('login-page')) {
        mainApp.classList.add('visible');
        if (welcomeCurtain) {
            welcomeCurtain.style.display = 'none'; // Hide welcome curtain immediately
        }
        document.body.style.overflow = 'auto'; // Ensure scroll is enabled
    } else if (welcomeCurtain) {
        const welcomeSubtitle = document.getElementById('welcomeSubtitle');
        const setWelcomeMessage = () => {
            const hour = new Date().getHours();
            let message = "Que tengas un grandioso día, y haya suerte para encontrar los EEM que tal vez se quedaron en tu caja. Suerte amigo!";
            if (hour >= 18) { // Después de las 6 PM
                message = "Ya es hora de alistar tus cosas para regresar a casa. ¿porque a la ultima hora? Suerte con la búsqueda!";
            } else if (hour >= 13) { // Entre la 1 PM y las 6 PM
                message = "Despues del almuerzo espero que ahora si trabajes, y puedas encuentrar lo que buscas. Suerte!";
            }
            
            // Formatea el mensaje para poner la primera parte en negrita
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

            welcomeSubtitle.innerHTML = formatMessage(message);
        };

        setWelcomeMessage();

        setTimeout(() => {
            welcomeCurtain.classList.add('hide');
            welcomeCurtain.addEventListener('animationend', () => {
                welcomeCurtain.style.display = 'none';
                document.body.style.overflow = 'auto';
                mainApp.classList.add('visible');
            });
        }, WELCOME_CURTAIN_DURATION);
    } else {
        mainApp.classList.add('visible');
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

    modalCloseBtn.addEventListener('click', () => {
        detailsModalOverlay.style.display = 'none';
    });

    detailsModalOverlay.addEventListener('click', (event) => {
        if (event.target === detailsModalOverlay) {
            detailsModalOverlay.style.display = 'none';
        }
    });

    const showDetailsModal = (data) => {
        modalDataElement.textContent = JSON.stringify(data, null, 2); // Formato JSON legible
        detailsModalOverlay.style.display = 'block';
    };

    const toggleTheme = () => {
        isDarkMode = !isDarkMode;
        body.className = isDarkMode ? 'dark-mode' : 'light-mode';
        themeToggle.innerHTML = isDarkMode ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
    };

    const switchTab = (targetTab) => {
        activeTab = targetTab;
        tabContents.forEach(c => c.classList.remove('active'));
        tabButtons.forEach(b => b.classList.remove('active'));
        document.getElementById(targetTab).classList.add('active');
        document.querySelector(`[data-tab="${targetTab}"]`).classList.add('active');
        updateStatus();
        clearResults();
    };

    const showLoading = (show) => { loading.style.display = show ? 'block' : 'none'; };
    const clearResults = () => { resultsContainer.innerHTML = ''; noResults.style.display = 'none'; };
    const updateFileInfo = (filename) => {
        if (filename) { fileName.textContent = filename; fileInfo.style.display = 'flex'; }
        else { fileInfo.style.display = 'none'; }
    };

    const updateStatus = async () => {
        try {
            const response = await fetch('/status');
            const status = await response.json();
            if (activeTab === 'excel') {
                statusText.textContent = status.has_excel_data
                    ? `${status.records} registros cargados de ${status.filename}`
                    : 'Sube un archivo para buscar en tus datos.';
            }
            updateFileInfo(status.has_excel_data ? status.filename : null);
        } catch (error) {
            console.error('Error al obtener estado:', error);
            statusText.textContent = 'Error al conectar con el servidor.';
        }
    };

    const handleFileUpload = async () => {
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
            noResults.textContent = `Error en la búsqueda: ${error.message}`;
            noResults.style.display = 'block';
        } finally {
            showLoading(false);
        }
    };

    // Nueva función para crear una tarjeta de resultado giratoria
    const createResultCard = (result) => {
        const item = document.createElement('div');
        item.className = 'flip-card';

        const keys = Object.keys(result);

        // Obtener los valores para el reverso de la tarjeta (indices [4], [7], [5])
        const backData1 = keys[4] ? `${keys[2]}: ${result[keys[2]]}` : '';
        const backData2 = keys[7] ? `${keys[5]}: ${result[keys[5]]}` : '';
        const backData3 = keys[5] ? `${keys[8]}: ${result[keys[8]]}` : ''; // This is the one to highlight

        // Contenido del frente de la tarjeta
        const title = result[keys[0]] || 'Documento';
        const subtitle1 = keys.length > 1 ? `${keys[1]}: ${result[keys[1]]}` : '';
        const subtitle2 = keys.length > 4 ? `${result[keys[4]]}` : ''; // Only value, no field name

        item.innerHTML = `
            <div class="flip-card-inner">
                <div class="flip-card-front">
                    <h3 class="result-title">${title}</h3>
                    <div class="modern-line"></div> <!-- New line element -->
                    <p class="result-subtitle1">${subtitle1}</p>
                    <p class="result-subtitle2">${subtitle2}</p>
                </div>
                <div class="flip-card-back">
                    <p>${backData1}</p>
                    <p>${backData2}</p>
                    <p class="highlighted-back-data">${backData3}</p>
                </div>
            </div>
        `;

        // Añadir evento de clic para girar la tarjeta
        item.addEventListener('click', () => {
            item.classList.toggle('is-flipped');
        });

        return item;
    };

    const displayResults = (data) => {
        const { results } = data;
        resultsContainer.innerHTML = ''; // Limpiar resultados anteriores
        if (results.length === 0) {
            noResults.style.display = 'block';
            return;
        }

        // Ocultar mensaje de no resultados si hay resultados
        noResults.style.display = 'none';

        // Configurar resultsContainer para mostrar dos tarjetas por fila
        resultsContainer.style.display = 'grid';
        resultsContainer.style.gridTemplateColumns = 'repeat(auto-fit, minmax(300px, 1fr))'; // Ajuste para 2 columnas
        resultsContainer.style.gap = '20px'; // Espacio entre tarjetas

        results.forEach(result => {
            const card = createResultCard(result);
            resultsContainer.appendChild(card);
        });
    };

    // Asignación de eventos
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    if (tabButtons) {
        tabButtons.forEach(b => b.addEventListener('click', () => switchTab(b.dataset.tab)));
    }
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }
    if (clearFile) {
        clearFile.addEventListener('click', handleClearFile);
    }
    if (searchBtn) {
        searchBtn.addEventListener('click', handleSearch);
    }
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSearch(); });
    }

    // Estado inicial
    if (!document.body.classList.contains('login-page')) {
        updateStatus();
    }

    // Anime.js animation for login page
    const animationContainer = document.querySelector('.animation-container');
    if (animationContainer) {
        const dots = document.querySelectorAll('.dot');
        const visibleDots = document.querySelectorAll('.dot.lock-visible, .dot.lock-arc');

        // Oculta todos los puntos al inicio
        anime.set(dots, { scale: 0, opacity: 0 });

        // Define la secuencia de la animación
        const timeline = anime.timeline({
            // La animación se ejecuta una vez al cargar la página
            loop: false,
            autoplay: true,
            easing: 'easeInOutQuad',
        });

        // Animación #1: Los puntos que formarán el candado aparecen
        timeline.add({
            targets: visibleDots,
            scale: [0, 1],
            opacity: [0, 1],
            delay: anime.stagger(50), // Pequeño retraso para un efecto de "revelación"
            duration: 800
        })
        // Animación #2: El cuerpo del candado se "construye"
        .add({
            targets: '.dot:not(.lock-arc)',
            scale: [1.1, 1], // Un pequeño rebote
            rotate: [0, 360],
            delay: anime.stagger(100, {grid: [15, 15], from: 'center'}),
            duration: 1000,
            easing: 'easeOutElastic(1, .8)'
        }, '-=500') // Comienza 500ms antes de que termine la animación anterior
        // Animación #3: El arco del candado se "cierra" con un color diferente
        .add({
            targets: '.dot.lock-arc',
            scale: [1, 1],
            backgroundColor: [
                'var(--secondary-color)',
                'var(--cyan-color)'
            ],
            delay: anime.stagger(150),
            duration: 500
        }, '-=800'); // Comienza 800ms antes de que termine la animación anterior
    }
});