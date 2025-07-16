// Aplica as máscaras de input
document.addEventListener('DOMContentLoaded', (event) => {
    const cpfElement = document.getElementById('cpf');
    const telefoneElement = document.getElementById('telefone');

    const cpfMaskOptions = {
        mask: '000.000.000-00'
    };
    const telefoneMaskOptions = {
        mask: '(00) 00000-0000'
    };

    IMask(cpfElement, cpfMaskOptions);
    IMask(telefoneElement, telefoneMaskOptions);
});

document.getElementById('upload-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    const messageDiv = document.getElementById('message');
    const curriculoInput = document.getElementById('curriculo');
    
    // Validação do tipo de arquivo no frontend
    const allowedExtensions = ['pdf', 'doc', 'docx'];
    const fileName = curriculoInput.value;
    const fileExtension = fileName.split('.').pop().toLowerCase();

    if (fileName && !allowedExtensions.includes(fileExtension)) {
        messageDiv.textContent = 'Erro: Tipo de arquivo inválido. Por favor, selecione um arquivo PDF, DOC ou DOCX.';
        messageDiv.className = 'error';
        messageDiv.style.display = 'block'; // Garante que a mensagem seja exibida
        return; // Impede o envio do formulário
    }

    // Limpa mensagens anteriores
    messageDiv.textContent = '';
    messageDiv.className = '';

    fetch('https://phdbrazil.pythonanywhere.com/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json().then(data => ({ status: response.status, body: data })))
    .then(({ status, body }) => {
        if (status === 200 || status === 201) {
            messageDiv.textContent = body.message;
            messageDiv.classList.add('success');
            form.reset(); // Limpa o formulário
        } else {
            messageDiv.textContent = 'Erro: ' + (body.error || JSON.stringify(body));
            messageDiv.classList.add('error');
        }
    })
    .catch(error => {
        console.error('Erro na requisição:', error);
        messageDiv.textContent = 'Ocorreu um erro ao enviar o formulário. Verifique o console para mais detalhes.';
        messageDiv.classList.add('error');
    });
}); 