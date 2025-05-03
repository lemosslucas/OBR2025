// parametros valores
document.addEventListener('DOMContentLoaded', () => {
    const sliders = [
        { sliderId: 'slider-threshold', valueId: 'value-threshold' },
        { sliderId: 'slider-kp', valueId: 'value-kp' },
        { sliderId: 'slider-ki', valueId: 'value-ki' },
        { sliderId: 'slider-kd', valueId: 'value-kd' },
    ];

    sliders.forEach(({ sliderId, valueId }) => {
        const slider = document.getElementById(sliderId);
        const valueSpan = document.getElementById(valueId);

        if (slider && valueSpan) {
            slider.addEventListener('input', () => {
                valueSpan.textContent = slider.value;
            });
            console.log(valueSpan)
        } 
    });
});

// status
function updateSystemStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            document.getElementById('cpu').textContent = data.cpu.toFixed(1);
            document.getElementById('memory').textContent = data.memory.toFixed(1);
            document.getElementById('temperature').textContent = data.temperature?.toFixed(1) ?? 'N/A';
        })
        .catch(error => console.error('Erro ao buscar status:', error));
}

// Atualiza a cada 5 segundos
setInterval(updateSystemStatus, 5000);
updateSystemStatus(); // atualiza assim que a página carrega

