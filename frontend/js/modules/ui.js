/**
 * ui.js - Responsável por toda a manipulação visual e DOM.
 */
import { Helpers } from '../utils/helpers.js';

export const UI = {
    async renderizarListaChats(chatIdAtivo, callbackAbrir) {
        const lista = document.getElementById('lista-chats');
        if (!lista) return;

        const { Api } = await import('./api.js');
        const chats = await Api.buscarChats();

        lista.innerHTML = '';

        chats.forEach(chat => {
            const item = document.createElement('div');
            const isActive = chat.id === chatIdAtivo;
            
            item.className = `chat-item p-3 mb-2 rounded-lg cursor-pointer flex items-center gap-3 transition-all ${
                isActive ? 'bg-slate-800 border-l-4 border-blue-500 shadow-lg' : 'hover:bg-slate-800/50 text-slate-400'
            }`;

            const iconeUrl = chat.icone ? chat.icone.replace('data/media/', '/media/') : null;

            item.innerHTML = `
                <div class="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-xs overflow-hidden">
                    ${iconeUrl ? `<img src="${iconeUrl}" class="w-full h-full object-cover">` : '<i class="fa-solid fa-message"></i>'}
                </div>
                <div class="flex-1 overflow-hidden">
                    <p class="text-sm font-medium truncate ${isActive ? 'text-white' : ''}">${chat.titulo || 'Nova Conversa'}</p>
                </div>
            `;

            item.onclick = () => callbackAbrir(chat.id);
            lista.appendChild(item);
        });
    },

    atualizarHeader(titulo, icone) {
        const elTitulo = document.getElementById('chat-titulo-header');
        const elIcone = document.getElementById('chat-icon-header');

        if (elTitulo) elTitulo.innerText = titulo || 'Chat';
        if (elIcone) {
            const iconeUrl = icone ? icone.replace('data/media/', '/media/') : null;
            elIcone.innerHTML = iconeUrl 
                ? `<img src="${iconeUrl}" class="w-full h-full rounded-full object-cover">` 
                : '<i class="fa-solid fa-robot text-blue-400"></i>';
        }
    },

    limparAreaMensagens() {
        const area = document.getElementById('area-mensagens');
        if (area) area.innerHTML = '';
    },

    adicionarMensagem(msg, callbackZoom = null) {
        const area = document.getElementById('area-mensagens');
        if (!area) return null;

        const id = msg.id || Helpers.gerarId();
        const isUser = msg.papel === 'user';

        const div = document.createElement('div');
        div.id = `msg-container-${id}`; 
        div.className = `flex w-full mb-8 ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`;

        const imgUrl = msg.caminho_imagem ? msg.caminho_imagem.replace('data/media/', '/media/') : null;

        const userClasses = "bg-blue-600 text-white rounded-2xl rounded-tr-none ml-auto max-w-[85%] sm:max-w-[75%] p-4 shadow-md relative group";
        const assistantClasses = "bg-slate-800 text-slate-100 rounded-2xl rounded-tl-none mr-auto max-w-[85%] sm:max-w-[75%] p-4 border border-slate-700 shadow-sm relative group";

        // Template corrigido: usamos template strings para garantir que o ID passe como número ou string correta
        const botoesAcao = `
            <div class="absolute -bottom-7 ${isUser ? 'right-0' : 'left-0'} flex gap-3 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <button onclick="window.apagarMensagem('${id}')" class="text-slate-500 hover:text-red-500 transition-colors" title="Apagar">
                    <i class="fa-solid fa-trash-can text-xs"></i>
                </button>
                ${!isUser ? `
                <button onclick="window.regerarMensagem('${id}')" class="text-slate-500 hover:text-blue-400 transition-colors" title="Regerar resposta">
                    <i class="fa-solid fa-rotate-right text-xs"></i>
                </button>` : ''}
            </div>
        `;

        div.innerHTML = `
            <div class="${isUser ? userClasses : assistantClasses}">
                ${imgUrl ? `
                    <img src="${imgUrl}" class="mb-3 rounded-lg cursor-zoom-in max-h-64 object-cover" 
                         onclick="window.abrirZoom('${imgUrl}')">
                ` : ''}
                <div class="text-sm leading-relaxed whitespace-pre-wrap">${msg.conteudo}</div>
                ${botoesAcao}
            </div>
        `;

        area.appendChild(div);
        this.rolarParaBaixo();
        
        if (callbackZoom && !window.abrirZoom) window.abrirZoom = callbackZoom;
        return id;
    },

    rolarParaBaixo() {
        const area = document.getElementById('area-mensagens');
        if (area) area.scrollTo({ top: area.scrollHeight, behavior: 'smooth' });
    },

	// --- LÓGICA DO BOTÃO DE SCROLL ---
    initScrollButton() {
        const area = document.getElementById('area-mensagens');
        const btnScroll = document.getElementById('btn-scroll-bottom');

        if (!area || !btnScroll) return;

        // Mostrar o botão quando o utilizador fizer scroll para cima
        area.addEventListener('scroll', () => {
            // Verifica a distância do fundo. Se for maior que 100px, mostra o botão.
            const distParaFundo = area.scrollHeight - area.scrollTop - area.clientHeight;
            
            if (distParaFundo > 100) {
                btnScroll.classList.remove('hidden');
                // Pequena animação para aparecer
                btnScroll.classList.add('animate-fade-in'); 
            } else {
                btnScroll.classList.add('hidden');
            }
        });

        // Evento de clique no botão para rolar para baixo
        btnScroll.addEventListener('click', () => {
            this.rolarParaBaixo();
        });
    }
};
