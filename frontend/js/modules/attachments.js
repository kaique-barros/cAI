/**
 * attachments.js - Gere o redimensionamento e a captura de anexos.
 */

export const Attachments = {
    // Estado local do anexo
    imagemBase64: null,

    /**
     * Reduz o tamanho da imagem para evitar sobrecarregar a rede e o processador.
     */
    redimensionar(base64Str, maxWidth = 800, maxHeight = 800) {
        return new Promise((resolve) => {
            const img = new Image();
            img.src = base64Str;
            img.onload = () => {
                const canvas = document.createElement('canvas');
                let width = img.width;
                let height = img.height;

                if (width > height) {
                    if (width > maxWidth) {
                        height *= maxWidth / width;
                        width = maxWidth;
                    }
                } else {
                    if (height > maxHeight) {
                        width *= maxHeight / height;
                        height = maxHeight;
                    }
                }

                canvas.width = width;
                canvas.height = height;
                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, width, height);
                
                // Exporta como JPEG com compressão para ser leve
                resolve(canvas.toDataURL('image/jpeg', 0.7));
            };
        });
    },

    /**
     * Atualiza a interface com a miniatura da imagem selecionada.
     */
    async atualizarPrevia(base64Original) {
        this.imagemBase64 = await this.redimensionar(base64Original);
        
        // Busca os elementos apenas no momento exato em que precisa deles
        const imgPrevia = document.getElementById('img-previa');
        const containerPrevia = document.getElementById('container-previa-imagem');
        
        if (imgPrevia) imgPrevia.src = this.imagemBase64;
        if (containerPrevia) containerPrevia.classList.remove('hidden');
    },

    /**
     * Limpa a pré-visualização e o estado do anexo após o envio.
     */
    limpar() {
        this.imagemBase64 = null;
        
        // Busca os elementos de forma segura
        const inputAnexo = document.getElementById('input-anexo');
        const containerPrevia = document.getElementById('container-previa-imagem');
        const imgPrevia = document.getElementById('img-previa');
        
        if (inputAnexo) inputAnexo.value = '';
        if (imgPrevia) imgPrevia.src = '';
        if (containerPrevia) containerPrevia.classList.add('hidden');
    }
};
