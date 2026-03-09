/**
 * models.js - Gere a lógica do Gestor de Modelos e sincronização.
 */
import { Api } from './api.js';

export const Models = {
    /**
     * Atualiza os dropdowns (selects) da interface com os modelos ativos.
     */
    async atualizarSeletores() {
        const seletorChat = document.getElementById('seletor-modelo');
        const seletorGlobal = document.getElementById('input-modelo-padrao');

        // Verificação de segurança: os elementos podem ainda não estar no DOM
        if (!seletorChat) return;

        try {
            const modelos = await Api.buscarModelos();
            seletorChat.innerHTML = ''; 
            if (seletorGlobal) seletorGlobal.innerHTML = '';

            const ativos = modelos.filter(m => m.is_ativo);

            if (ativos.length === 0) {
                seletorChat.innerHTML = '<option value="">Nenhum modelo ativo</option>';
            } else {
                ativos.forEach(m => {
                    const icone = m.tipo === 'imagem' ? '🎨' : '🤖';
                    const tag = m.tipo === 'imagem' ? '(Imagem)' : '(Texto)';
                    const opcao = `<option value="${m.nome_id}">${icone} ${m.nome_id} ${tag}</option>`;
                    
                    seletorChat.innerHTML += opcao;
                    if (m.tipo === 'texto' && seletorGlobal) {
                        seletorGlobal.innerHTML += opcao;
                    }
                });
            }
        } catch (e) {
            console.error("Erro ao atualizar seletores de modelos:", e);
        }
    },

    /**
     * Renderiza a lista detalhada dentro do Modal do Gestor e controla os botões de download.
     */
    async renderizarGerenciador() {
        const lista = document.getElementById('lista-gerenciador-modelos');
        const controles = document.getElementById('controles-download');
        
        if (!lista) return;

        const modelos = await Api.buscarModelos();
        lista.innerHTML = '';
        let temInativos = false;

        if (modelos.length === 0) {
            lista.innerHTML = '<p class="text-gray-500 text-center py-4">Nenhum modelo registado.</p>';
            if (controles) controles.style.display = 'none';
            return;
        }

        modelos.forEach(m => {
            const isAtivo = m.is_ativo;
            const statusDot = isAtivo ? 'bg-green-500' : 'bg-gray-600';
            const statusText = isAtivo ? 'Instalado & Pronto' : 'Falta Instalar';
            
            // Define se exibe ícone de check ou checkbox para download
            let acaoHtml = isAtivo 
                ? `<i class="fa-solid fa-circle-check text-green-500 text-xl mt-1"></i>`
                : `<input type="checkbox" value="${m.nome_id}" class="checkbox-modelo w-5 h-5 text-primary bg-gray-900 border-gray-600 rounded cursor-pointer mt-1">`;

            if (!isAtivo && m.tipo === 'texto') temInativos = true;

            lista.innerHTML += `
                <div class="bg-slate-800 border border-slate-700 rounded-xl p-4 flex items-start space-x-4 hover:border-blue-500 transition-all mb-3">
                    <div class="pt-1">${acaoHtml}</div>
                    <div class="flex-1 flex justify-between items-center">
                        <div>
                            <div class="flex items-center space-x-2 mb-1">
                                <span class="w-2 h-2 rounded-full ${statusDot}"></span>
                                <h5 class="text-lg font-bold text-white">${m.nome_id}</h5>
                                <span class="text-xs text-gray-400 uppercase bg-gray-900 px-2 py-0.5 rounded border border-slate-700">${m.tipo}</span>
                            </div>
                            <p class="text-sm text-gray-400">${m.descricao || 'Sem descrição.'}</p>
                        </div>
                        <div class="text-sm font-semibold ${isAtivo ? 'text-green-400' : 'text-gray-500'}">${statusText}</div>
                    </div>
                </div>`;
        });

        // Mostra o botão de instalar se houver modelos para baixar
        if (controles) {
            controles.classList.toggle('hidden', !temInativos);
        }
    },

    /**
     * Sincroniza os modelos com o servidor Ollama.
     */
    async sincronizar() {
        const btn = document.getElementById('btn-sincronizar-modelos');
        if (!btn) return;

        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i> Sincronizando...';
        btn.disabled = true;

        try {
            await Api.sincronizarOllama();
            await this.renderizarGerenciador();
            await this.atualizarSeletores();
        } catch (e) {
            console.error("Erro na sincronização:", e);
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },

    /**
     * Regista um novo modelo no banco de dados.
     */
    async adicionarNovo(dados) {
        try {
            const res = await Api.registarModelo(dados);
            if (res.ok) {
                await Api.sincronizarOllama();
                await this.renderizarGerenciador();
                await this.atualizarSeletores();
                return true;
            }
            const erro = await res.json();
            alert(erro.detail || "Erro ao registar modelo.");
            return false;
        } catch (e) {
            console.error("Erro ao adicionar modelo:", e);
            return false;
        }
    }
};
