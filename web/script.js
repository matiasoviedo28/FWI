// script.js

// Elementos DOM
const startDateInput = document.getElementById('start-date');
const endDateInput = document.getElementById('end-date');
const applyFiltersButton = document.getElementById('apply-filters');
const idInput = document.getElementById('id-input');
const maxTempElement = document.getElementById('max-temp');
const minTempElement = document.getElementById('min-temp');
const maxPrecipElement = document.getElementById('max-precip');
const minPrecipElement = document.getElementById('min-precip');
const lineChartCanvas = document.getElementById('line-chart');
const mainElement = document.querySelector('main');

// Variables globales
let rawData = [];
let filteredData = [];
let lineChart;

// Cargar CSV
async function loadCSV() {
    try {
        const response = await fetch('CSV/historicos.csv');
        if (!response.ok) {
            throw new Error('No se pudo cargar el archivo CSV.');
        }
        const data = await response.text();
        parseCSV(data);
    } catch (error) {
        displayError('Error al cargar el archivo CSV: ' + error.message);
    }
}

// Parsear CSV
function parseCSV(data) {
    const rows = data.split('\n').slice(1); // Saltar la cabecera
    rawData = rows.map(row => {
        const [Punto_ID, Latitud, Longitud, Fecha, Temperatura, Precipitacion, Viento, Humedad, FFMC, DMC, DC, ISI, BUI, FWI] = row.split(',');
        return {
            Punto_ID,
            Latitud: parseFloat(Latitud),
            Longitud: parseFloat(Longitud),
            Fecha,
            Temperatura: parseFloat(Temperatura),
            Precipitacion: parseFloat(Precipitacion),
            Viento: parseFloat(Viento),
            Humedad: parseFloat(Humedad),
            FFMC: parseFloat(FFMC),
            DMC: parseFloat(DMC),
            DC: parseFloat(DC),
            ISI: parseFloat(ISI),
            BUI: parseFloat(BUI),
            FWI: parseFloat(FWI)
        };
    });
    applyFilters();
}

// Aplicar filtros
function applyFilters() {
    const startDate = startDateInput.value;
    const endDate = endDateInput.value;
    const numericID = idInput.value.trim();

    if (!numericID) {
        displayError('Por favor, ingrese un ID válido.');
        return;
    }

    const Punto_ID = `PUNTO_${numericID}`;

    filteredData = rawData.filter(row => {
        return (
            (!startDate || row.Fecha >= startDate) &&
            (!endDate || row.Fecha <= endDate) &&
            row.Punto_ID === Punto_ID
        );
    });

    if (filteredData.length === 0) {
        displayError('No se encontraron datos para el Punto_ID: ' + Punto_ID);
        return;
    }

    updateStats();
    updateChart();
}

// Mostrar error
function displayError(message) {
    mainElement.innerHTML = `<div class="error-message">${message}</div>`;
}

// Actualizar estadísticas
function updateStats() {
    if (filteredData.length === 0) {
        maxTempElement.textContent = '-';
        minTempElement.textContent = '-';
        maxPrecipElement.textContent = '-';
        minPrecipElement.textContent = '-';
        return;
    }

    const temps = filteredData.map(row => row.Temperatura);
    const precips = filteredData.map(row => row.Precipitacion);

    maxTempElement.textContent = Math.max(...temps).toFixed(2);
    minTempElement.textContent = Math.min(...temps).toFixed(2);
    maxPrecipElement.textContent = Math.max(...precips).toFixed(2);
    minPrecipElement.textContent = Math.min(...precips).toFixed(2);
}

// Actualizar gráfico
function updateChart() {
    const labels = filteredData.map(row => row.Fecha);
    const temps = filteredData.map(row => row.Temperatura);
    const precip = filteredData.map(row => row.Precipitacion);

    if (lineChart) {
        lineChart.destroy();
    }

    lineChart = new Chart(lineChartCanvas, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Temperatura (°C)',
                    data: temps,
                    borderColor: '#ff6f61',
                    fill: false
                },
                {
                    label: 'Precipitación (mm)',
                    data: precip,
                    borderColor: '#ff9085',
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Fecha'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Valor'
                    }
                }
            }
        }
    });
}

// Eventos
applyFiltersButton.addEventListener('click', applyFilters);

// Inicializar
loadCSV();
