/**
 * modals.js - Controla a abertura, fecho e animações de todos os modais.
 */

export const Modals = {
    // Repare que removemos as referências fixas do topo para evitar o erro "null"

    abrir(modalObj) {
        if (modalObj && modalObj.el) {
            modalObj.el.classList.remove('hidden');
        }
    },

    fechar(modalObj) {
        if (modalObj && modalObj.el) {
            modalObj.el.classList.add('hidden');
        }
    },

    // --- LÓGICA ESPECÍFICA: LIGHTBOX (ZOOM DAS IMAGENS) ---
    abrirLightbox(src) {
        const elLightbox = document.getElementById('modal-lightbox');
        const imgLightbox = document.getElementById('img-lightbox');
        
        if (!elLightbox || !imgLightbox) return;

        imgLightbox.src = src;
        elLightbox.classList.remove('hidden');
        
        // Pequeno delay para a animação de escala suave
        setTimeout(() => {
            imgLightbox.classList.remove('scale-95', 'opacity-0');
            imgLightbox.classList.add('scale-100', 'opacity-100');
        }, 10);
    },

    fecharLightbox() {
        const elLightbox = document.getElementById('modal-lightbox');
        const imgLightbox = document.getElementById('img-lightbox');
        
        if (!elLightbox || !imgLightbox) return;

        imgLightbox.classList.remove('scale-100', 'opacity-100');
        imgLightbox.classList.add('scale-95', 'opacity-0');
        
        setTimeout(() => {
            elLightbox.classList.add('hidden');
            imgLightbox.src = '';
        }, 250);
    },

    // --- LÓGICA ESPECÍFICA: GALERIA ---
    renderizarGaleria(mensagensComImagem) {
        const grid = document.getElementById('grid-galeria');
        if (!grid) return;

        grid.innerHTML = '';
        
        if (mensagensComImagem.length === 0) {
            grid.innerHTML = '<p class="text-gray-400 col-span-full text-center py-10">Nenhuma imagem gerada neste chat.</p>';
            return;
        }

        mensagensComImagem.forEach(img => {
            const url = img.caminho_imagem.replace('data/media', '/media');
            const div = document.createElement('div');
            div.className = "group relative rounded-lg overflow-hidden border border-gray-700 aspect-square";
            div.innerHTML = `
                <img src="${url}" class="w-full h-full object-cover transition-transform group-hover:scale-110">
                <a href="${url}" download class="absolute bottom-2 right-2 bg-black bg-opacity-70 text-white p-2 rounded-lg opacity-0 group-hover:opacity-100 hover:text-primary transition-opacity">
                    <i class="fa-solid fa-download"></i>
                </a>
            `;
            grid.appendChild(div);
        });
    }
};
