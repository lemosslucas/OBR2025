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
            valueSpan.textContent = slider.value;

            slider.addEventListener('input', () => {
                valueSpan.textContent = slider.value;
                sendParamsToServer();
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
            document.getElementById('voltage_state').textContent = data.voltage_state.toFixed(1);
        })
        .catch(error => console.error('Erro ao buscar status:', error));
}

// params
function sendParamsToServer() {
    const kp = document.getElementById('slider-kp').value;
    const ki = document.getElementById('slider-ki').value;
    const kd = document.getElementById('slider-kd').value;
    const threshold = document.getElementById('slider-threshold').value;

    fetch('/update_params', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            kp: kp,
            ki: ki,
            kd: kd,
            threshold: threshold
        })
    })
    .then(response => response.json())
    .then(data => console.log('Parâmetros atualizados:', data))
    .catch(error => console.error('Erro ao enviar parâmetros:', error));
}

// Atualiza a cada 5 segundos
setInterval(updateSystemStatus, 5000);
updateSystemStatus(); // atualiza assim que a página carrega

