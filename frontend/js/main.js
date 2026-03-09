/**
 * main.js - Orquestrador da Interface Modular
 */
import { Api } from './modules/api.js';
import { UI } from './modules/ui.js';
import { Chat } from './modules/chat.js';
import { Models } from './modules/models.js';
import { Modals } from './modules/modals.js';
import { Attachments } from './modules/attachments.js';
import { Helpers } from './utils/helpers.js';

let chatIdAtual = null;

// --- FUNÇÃO AUXILIAR PARA LER IMAGENS ---
function lerFicheiroBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

async function carregarInterface() {
    console.log("⏳ Carregando componentes...");
    await Promise.all([
        Helpers.incluirComponente('component-sidebar', 'sidebar.html'),
        Helpers.incluirComponente('component-chat', 'chat-area.html'),
        Helpers.incluirComponente('component-modals', 'modals.html')
    ]);
    console.log("✅ Interface montada.");
}

async function inicializarApp() {
    // --- Referências Seguras ---
    const btnNovoChat = document.getElementById('btn-novo-chat');
    const btnEnviar = document.getElementById('btn-enviar');
    const inputMsg = document.getElementById('input-mensagem');
    const inputAnexo = document.getElementById('input-anexo');
    const btnAnexar = document.getElementById('btn-anexar');
    const btnRemoverAnexo = document.getElementById('btn-remover-anexo');
    
    const btnConfig = document.getElementById('btn-config-global');
    const btnSalvarGlobal = document.getElementById('btn-salvar-global');
    const btnModelos = document.getElementById('btn-gerenciar-modelos');
    const btnSincronizar = document.getElementById('btn-sincronizar-modelos');
    const btnAddModelo = document.getElementById('btn-adicionar-modelo');
    const btnInstalarModelos = document.getElementById('btn-instalar-modelos');

    const btnConfigChat = document.getElementById('btn-config-chat');
    const btnSalvarChat = document.getElementById('btn-salvar-chat');
	Modals.init();
	UI.initScrollButton();

    // EVENTOS CHAT/SIDEBAR
    if (btnNovoChat) {
        btnNovoChat.onclick = async () => {
            const novo = await Api.criarChat("Nova Conversa");
            await abrirChat(novo.id);
        };
    }

    if (btnEnviar) {
        btnEnviar.onclick = () => processarEnvio();
    }

    if (inputMsg) {
        inputMsg.onkeydown = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                processarEnvio();
            }
        };
        Helpers.configurarAutoResizing(inputMsg);
    }

    // EVENTOS ANEXOS
    if (inputAnexo && btnAnexar && btnRemoverAnexo) {
        btnAnexar.onclick = () => inputAnexo.click();
        inputAnexo.onchange = (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (ev) => Attachments.atualizarPrevia(ev.target.result);
                reader.readAsDataURL(file);
            }
        };
        btnRemoverAnexo.onclick = () => Attachments.limpar();
    }

    // EVENTOS MODAIS / CONFIGURAÇÕES
    if (btnConfig) {
        btnConfig.onclick = async () => {
            const config = await Api.buscarConfiguracoes();
            const inputCtx = document.getElementById('input-contexto-global');
            const inputMod = document.getElementById('input-modelo-padrao'); // <-- Adicionado
            const elModal = document.getElementById('modal-global');
            
            // Injeta os valores na interface
            if (inputCtx) inputCtx.value = config.contexto_global || '';
            
            // Força o menu suspenso a ficar no modelo que estava na base de dados
            if (inputMod && config.modelo_padrao) {
                inputMod.value = config.modelo_padrao;
            }
            
            if (elModal) Modals.abrir({ el: elModal });
        };
    }

    if (btnSalvarGlobal) {
        btnSalvarGlobal.onclick = async () => {
            const inputCtx = document.getElementById('input-contexto-global');
            const inputMod = document.getElementById('input-modelo-padrao');
            const elModal = document.getElementById('modal-global');

            await Api.salvarConfiguracoes({
                contexto_global: inputCtx ? inputCtx.value : '',
                modelo_padrao: inputMod ? inputMod.value : ''
            });
            
            if (elModal) Modals.fechar({ el: elModal });
        };
    }

    if (btnModelos) {
        btnModelos.onclick = () => {
            Models.renderizarGerenciador();
            const elModal = document.getElementById('modal-modelos');
            if (elModal) Modals.abrir({ el: elModal });
        };
    }

    if (btnSincronizar) {
        btnSincronizar.onclick = () => Models.sincronizar();
    }

    if (btnAddModelo) {
        btnAddModelo.onclick = async () => {
            const elId = document.getElementById('add-model-id');
            const elTipo = document.getElementById('add-model-tipo');
            const elDesc = document.getElementById('add-model-desc');
            
            const dados = {
                nome_id: elId ? elId.value : '',
                tipo: elTipo ? elTipo.value : 'texto',
                descricao: elDesc ? elDesc.value : ''
            };
            
            if (!dados.nome_id) return alert("O ID do modelo é obrigatório");
            
            const sucesso = await Models.adicionarNovo(dados);
            if (sucesso) {
                if (elId) elId.value = '';
                if (elDesc) elDesc.value = '';
            }
        };
    }

    if (btnInstalarModelos) {
        btnInstalarModelos.onclick = async () => {
            const selecionados = Array.from(document.querySelectorAll('.checkbox-modelo:checked'))
                                      .map(cb => cb.value);
            
            if (selecionados.length === 0) return;
            
            btnInstalarModelos.disabled = true;
            btnInstalarModelos.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Iniciando...';
            
            await Api.descarregarModelos(selecionados);
            alert("Download iniciado no servidor Colab!");
            
            const elModal = document.getElementById('modal-modelos');
            if (elModal) Modals.fechar({ el: elModal });
            
            btnInstalarModelos.disabled = false;
            btnInstalarModelos.innerHTML = '<i class="fa-solid fa-download"></i> Instalar Selecionados';
        };
    }

    // EVENTOS: CONFIGURAÇÕES DA CONVERSA ATUAL
    if (btnConfigChat) {
        btnConfigChat.onclick = async () => {
            if (!chatIdAtual) return;
            const chats = await Api.buscarChats();
            const chat = chats.find(c => c.id === chatIdAtual);
            if (!chat) return;

            const inputTitulo = document.getElementById('input-chat-titulo');
            const inputContexto = document.getElementById('input-chat-contexto');
            
            if (inputTitulo) inputTitulo.value = chat.titulo || '';
            if (inputContexto) inputContexto.value = chat.contexto_inicial || '';

            Modals.abrir({ el: document.getElementById('modal-config-chat') });
        };
    }

    if (btnSalvarChat) {
        btnSalvarChat.onclick = async () => {
            if (!chatIdAtual) return;
            const titulo = document.getElementById('input-chat-titulo').value;
            const contexto = document.getElementById('input-chat-contexto').value;
            const fileIcone = document.getElementById('input-chat-icone').files[0];
            const fileBg = document.getElementById('input-chat-bg').files[0];

            const btnOriginal = btnSalvarChat.innerHTML;
            btnSalvarChat.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> A gravar...';
            btnSalvarChat.disabled = true;

            const dados = { titulo: titulo, contexto_inicial: contexto };
            
            if (fileIcone) dados.icone = await lerFicheiroBase64(fileIcone);
            if (fileBg) dados.background = await lerFicheiroBase64(fileBg);

            await Api.atualizarChat(chatIdAtual, dados);
            
            Modals.fechar({ el: document.getElementById('modal-config-chat') });
            btnSalvarChat.innerHTML = btnOriginal;
            btnSalvarChat.disabled = false;
            
            await UI.renderizarListaChats(chatIdAtual, abrirChat);
            abrirChat(chatIdAtual);
        };
    }

    // --- CARREGAMENTO INICIAL DE DADOS ---
    await Models.atualizarSeletores();
    await UI.renderizarListaChats(chatIdAtual, abrirChat);
}

async function abrirChat(id) {
    chatIdAtual = id;
	window.currentChatId = id;
    const chats = await Api.buscarChats();
    const chat = chats.find(c => c.id === id);
    
    if (!chat) return;

    const telaIni = document.getElementById('tela-inicial');
    const telaChat = document.getElementById('tela-chat');
    
    if (telaIni) telaIni.classList.add('hidden');
    if (telaChat) {
        telaChat.classList.remove('hidden');
        telaChat.classList.add('flex');
    }
    
    UI.atualizarHeader(chat.titulo, chat.icone);
    UI.limparAreaMensagens();

    // Aplica a imagem de fundo personalizada se existir
    const areaMensagens = document.getElementById('area-mensagens');
    if (areaMensagens) {
        if (chat.background) {
            const bgUrl = chat.background.replace('data/media/', '/media/');
            areaMensagens.style.backgroundImage = `url('${bgUrl}')`;
            areaMensagens.style.backgroundSize = 'cover';
            areaMensagens.style.backgroundPosition = 'center';
            areaMensagens.style.backgroundAttachment = 'fixed';
            areaMensagens.style.boxShadow = 'inset 0 0 0 2000px rgba(15, 23, 42, 0.85)';
        } else {
            areaMensagens.style.backgroundImage = 'none';
            areaMensagens.style.boxShadow = 'none';
        }
    }
    
    if (chat.mensagens) {
        chat.mensagens.forEach(msg => {
            UI.adicionarMensagem(msg, (src) => Modals.abrirLightbox(src));
        });
    }
    
    UI.renderizarListaChats(chatIdAtual, abrirChat);
    UI.rolarParaBaixo();
}

async function processarEnvio() {
    const input = document.getElementById('input-mensagem');
    const seletor = document.getElementById('seletor-modelo');
    
    if (!input) return;
    
    const texto = input.value.trim();
    const imagem = Attachments.imagemBase64;

    if ((!texto && !imagem) || !chatIdAtual) return;

    // A declaração da variável "idTemp" está agora de forma segura ANTES de ser usada
    UI.adicionarMensagem({ papel: 'user', conteudo: texto, caminho_imagem: imagem });
    const idTemp = UI.adicionarMensagem({ papel: 'assistant', conteudo: '...' });
    
    input.value = '';
    input.style.height = 'auto';
    Attachments.limpar();

    const switchStream = document.getElementById('switch-stream-chat');
    const isStreamLigado = switchStream ? switchStream.checked : true;

    try {
        await Chat.enviar(chatIdAtual, texto, imagem, {
            modelo: seletor ? seletor.value : 'llama3',
            isStream: isStreamLigado,
            indicadorId: idTemp,
            callbackZoom: (src) => Modals.abrirLightbox(src)
        });
    } catch (err) {
        console.error("Erro no envio:", err);
    }
}

document.addEventListener('DOMContentLoaded', async () => {
    try {
        await carregarInterface(); 
        await inicializarApp();    
    } catch (err) {
        console.error("Falha crítica na inicialização:", err);
    }
});

// Funções Globais para os botões do UI.js
window.apagarMensagem = async (id) => {
    if (!confirm("Deseja apagar esta mensagem?")) return;
    
    try {
        const res = await Api.eliminarMensagem(id);
        if (res.status === "sucesso") {
            // Recarrega apenas a área de chat chamando a função que já existe no seu main.js
            if (typeof abrirChat === 'function' && chatIdAtual) {
                await abrirChat(chatIdAtual);
            } else {
                location.reload(); 
            }
        }
    } catch (err) {
        console.error("Erro ao apagar:", err);
    }
};

window.regerarMensagem = async (idIA) => {
    const chats = await Api.buscarChats();
    // chatIdAtual vem do escopo do main.js
    const chat = chats.find(c => c.id === chatIdAtual);
    if (!chat) return;

    const mensagens = chat.mensagens;
    const indexIA = mensagens.findIndex(m => m.id == idIA);
    const msgUser = mensagens.slice(0, indexIA).reverse().find(m => m.papel === "user");

    if (msgUser) {
        await Api.eliminarMensagem(idIA);
        const inputMsg = document.getElementById('input-mensagem');
        if (inputMsg) {
            inputMsg.value = msgUser.conteudo;
            // processarEnvio é a função do main.js que lida com o envio
            window.scrollTo(0, document.body.scrollHeight);
            document.getElementById('btn-enviar').click();
        }
    }
};

document.addEventListener('paste', async (e) => {
    const itens = e.clipboardData.items;
    for (let item of itens) {
        if (item.type.indexOf("image") !== -1) {
            const blob = item.getAsFile();
            const reader = new FileReader();
            reader.onload = (ev) => {
                import('./modules/attachments.js').then(m => {
                    m.Attachments.atualizarPrevia(ev.target.result);
                });
            };
            reader.readAsDataURL(blob);
        }
    }
});
