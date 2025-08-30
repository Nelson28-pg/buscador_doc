// app/static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    // --- CONFIGURACIÓN ---
    const WELCOME_CURTAIN_DURATION = 10000; // Duración en milisegundos

    // --- Lógica para la Cortina de Bienvenida ---
    const welcomeCurtain = document.getElementById('welcomeCurtain');
    const mainApp = document.getElementById('mainApp');
    
    if (welcomeCurtain) {
        const welcomeSubtitle = document.getElementById('welcomeSubtitle');
        const setWelcomeMessage = () => {
            const hour = new Date().getHours();
            let message = "Que tengas un grandioso día, suerte para encontrar los EEM que tal vez se quedaron en tu caja. Trabaja!";
            if (hour >= 18) { // Después de las 6 PM
                message = "Ya es hora de que alistes tus cosas para regresar a casa, porque a la última hora. Suerte con la búsqueda!";
            } else if (hour >= 13) { // Entre la 1 PM y las 6 PM
                message = "Despues del refrigerio espero que ahora si trabajes, y encuentres lo que buscas. Suerte!";
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

    const displayResults = (data) => {
        const { results } = data;
        if (results.length === 0) { 
            noResults.style.display = 'block'; 
            return; 
        }

        results.forEach(result => {
            const keys = Object.keys(result);
            const title = result[keys[0]] || 'Documento';
            const details = keys.slice(1).map(key => `${key}: ${result[key]}`).join(' | ');
            const item = document.createElement('div');
            item.className = 'result-item';
            item.innerHTML = `<h3 class="result-title">${title}</h3><p class="result-details">${details}</p>`;
            resultsContainer.appendChild(item);
        });
    };

    // Asignación de eventos
    themeToggle.addEventListener('click', toggleTheme);
    tabButtons.forEach(b => b.addEventListener('click', () => switchTab(b.dataset.tab)));
    fileInput.addEventListener('change', handleFileUpload);
    clearFile.addEventListener('click', handleClearFile);
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') handleSearch(); });

    // Estado inicial
    updateStatus();
});