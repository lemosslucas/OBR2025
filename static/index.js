document.addEventListener('DOMContentLoaded', () => {
    // Atualiza o texto dos sliders e envia parâmetros ao servidor
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
        }
    });

    // Botões start e stop
    document.getElementById('start_robot').addEventListener('click', () => {
        fetch('/start', { method: 'POST' })
            .then(res => res.json())
            .then(data => console.log('Robô iniciado:', data))
            .catch(err => console.error('Erro ao iniciar robô:', err));
    });

    document.getElementById('stop_robot').addEventListener('click', () => {
        fetch('/stop', { method: 'POST' })
            .then(res => res.json())
            .then(data => console.log('Robô parado:', data))
            .catch(err => console.error('Erro ao parar robô:', err));
    });

    // Atualiza status a cada 5 segundos
    function updateSystemStatus() {
        fetch('/status')
            .then(res => res.json())
            .then(data => {
                document.getElementById('cpu').textContent = data.cpu.toFixed(1);
                document.getElementById('memory').textContent = data.memory.toFixed(1);
                document.getElementById('temperature').textContent = data.temperature?.toFixed(1) ?? 'N/A';
                document.getElementById('voltage_state').textContent = data.voltage_state ?? 'N/A';
            })
            .catch(err => console.error('Erro ao buscar status:', err));
    }
    updateSystemStatus();
    setInterval(updateSystemStatus, 5000);

    // Envia parâmetros para o servidor
    function sendParamsToServer() {
        const kp = document.getElementById('slider-kp').value;
        const ki = document.getElementById('slider-ki').value;
        const kd = document.getElementById('slider-kd').value;
        const threshold = document.getElementById('slider-threshold').value;

        fetch('/update_params', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ kp, ki, kd, threshold })
        })
        .then(res => res.json())
        .then(data => console.log('Parâmetros atualizados:', data))
        .catch(err => console.error('Erro ao enviar parâmetros:', err));
    }

    // Conexão SSE única com reconexão automática
    function connectLogs() {
        const logContainer = document.getElementById('log-container');
        if (!logContainer) {
            console.warn('log-container não encontrado');
            return;
        }

        let eventSource = new EventSource('/logs');

        eventSource.onmessage = (event) => {
            const logText = event.data.trim();
            if (logText) {
                const message = document.createElement('div');
                message.textContent = logText;
                logContainer.appendChild(message);
                logContainer.scrollTop = logContainer.scrollHeight;
                console.log(`[SSE] Logs na div: ${logContainer.children.length}, recebido: "${logText}"`);
            }
        };

        eventSource.onerror = (err) => {
            console.error('Erro SSE:', err);
            eventSource.close();
            // Reconectar após 5 segundos
            setTimeout(connectLogs, 5000);
        };
    }

    connectLogs();
});
