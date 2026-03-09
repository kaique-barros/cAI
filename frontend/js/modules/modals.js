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
    },

    // --- LÓGICA ESPECÍFICA: INICIALIZAR EVENTOS DOS MODAIS ---
    init() {
        // Inicializa o evento do botão de apagar chat
        const btnApagarChat = document.getElementById('btn-apagar-chat');
        if (btnApagarChat) {
            btnApagarChat.addEventListener('click', async () => {
                // Presumimos que window.currentChatId guarda o ID do chat ativo
                const chatId = window.currentChatId;
                if (!chatId) return;

                // Mostra o popup de confirmação do SweetAlert2
                const resultado = await Swal.fire({
                    title: 'Tem a certeza?',
                    text: "Todo o histórico e imagens desta conversa serão apagados!",
                    icon: 'warning',
                    showCancelButton: true,
                    confirmButtonColor: '#dc2626', // bg-red-600
                    cancelButtonColor: '#475569',  // bg-slate-600
                    confirmButtonText: 'Sim, apagar chat!',
                    cancelButtonText: 'Cancelar',
                    background: '#0f172a', // bg-slate-900 (tema escuro)
                    color: '#f8fafc', // text-slate-50
                    customClass: {
                        popup: 'border border-slate-700 rounded-xl'
                    }
                });

                if (resultado.isConfirmed) {
                    try {
                        const resposta = await fetch(`/api/v1/chats/apagar/${chatId}`, {
                            method: 'DELETE'
                        });

                        if (resposta.ok) {
                            await Swal.fire({
                                title: 'Apagado!',
                                text: 'O chat foi removido com sucesso.',
                                icon: 'success',
                                background: '#0f172a',
                                color: '#f8fafc',
                                timer: 1500,
                                showConfirmButton: false
                            });
                            // Recarrega a página para atualizar a sidebar e limpar o ecrã
                            window.location.reload();
                        } else {
                            throw new Error('Falha no servidor ao apagar chat.');
                        }
                    } catch (erro) {
                        Swal.fire({
                            title: 'Erro!',
                            text: 'Não foi possível apagar o chat.',
                            icon: 'error',
                            background: '#0f172a',
                            color: '#f8fafc'
                        });
                        console.error(erro);
                    }
                }
            });
        }
    }
};

// Não te esqueças de chamar Modals.init() no teu main.js ou UI.js quando a página carregar!
