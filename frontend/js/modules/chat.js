/**
 * chat.js - Gere a lógica de envio, recepção e processamento de mensagens.
 */

import { Api } from './api.js';
import { UI } from './ui.js';

export const Chat = {
    async enviar(chatId, texto, imagemBase64, config) {
        const { modelo, isStream, indicadorId } = config;
        const tipo = modelo === 'stable-diffusion' ? 'imagem' : 'texto';

        try {
            const payload = { 
                prompt: texto || " ", 
                tipo: tipo, 
                modelo: modelo, 
                stream: isStream 
            };
            if (imagemBase64) payload.imagem_base64 = imagemBase64;

            const resposta = await Api.enviarPergunta(chatId, payload);

            if (!resposta.ok) throw new Error("Erro na comunicação com o servidor.");
            
            const loader = document.getElementById(indicadorId);
            if (loader) loader.remove();

            if (tipo === 'imagem' || !isStream) {
                const mensagemIA = await resposta.json();
                UI.adicionarMensagem(mensagemIA, config.callbackZoom);
            } else {
                await this.processarStream(resposta, modelo, chatId, config.callbackZoom);
            }
        } catch (erro) {
            console.error("Erro no Chat:", erro);
            const loader = document.getElementById(indicadorId);
            if (loader) loader.remove();
            UI.adicionarMensagem({ papel: 'assistant', conteudo: "⚠️ Erro de conexão com a IA." });
        }
    },

    async processarStream(resposta, modelo, chatId, callbackZoom) {
        const divIA = this.criarBalaoVazioStream(modelo);
        const conteudoDiv = divIA.querySelector('.conteudo-texto');
        let textoAcumulado = '';

        const reader = resposta.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const linhas = buffer.split('\n');
            buffer = linhas.pop();

            for (const linha of linhas) {
                const linhaLimpa = linha.trim();
                if (!linhaLimpa || !linhaLimpa.startsWith('data: ')) continue;

                try {
                    const dados = JSON.parse(linhaLimpa.substring(6));
                    if (dados.chunk) {
                        textoAcumulado += dados.chunk;
                        conteudoDiv.textContent = textoAcumulado;
                        UI.rolarParaBaixo();
                    } else if (dados.fim) {
                        this.finalizarBalaoStream(divIA, dados.id, textoAcumulado, callbackZoom);
                    }
                } catch (e) {
                    console.error("Erro ao processar chunk:", e);
                }
            }
        }
    },

    // Usa exatamente as mesmas classes visuais do UI.js
    criarBalaoVazioStream(modelo) {
        const div = document.createElement('div');
        div.className = `flex w-full mb-4 justify-start animate-fade-in`;
        div.innerHTML = `
            <div class="bg-slate-800 text-slate-100 rounded-2xl rounded-tl-none mr-auto max-w-[85%] sm:max-w-[75%] p-4 border border-slate-700 shadow-sm w-full relative group">
                <div class="text-[10px] font-bold mb-2 opacity-50 flex items-center justify-between">
                    <span><i class="fa-solid fa-robot mr-1"></i> AI (${modelo})</span>
                    <i class="fa-solid fa-circle-notch fa-spin text-blue-500 ml-2 id-spinner"></i>
                </div>
                <div class="conteudo-texto text-sm leading-relaxed whitespace-pre-wrap"></div>
            </div>
        `;
        const area = document.getElementById('area-mensagens');
        if (area) {
            area.appendChild(div);
            area.scrollTo({ top: area.scrollHeight, behavior: 'smooth' });
        }
        return div;
    },

    finalizarBalaoStream(div, id, textoAcumulado, callbackZoom) {
        const balaoInterno = div.firstElementChild;
        balaoInterno.dataset.id = id;
        balaoInterno.dataset.papel = 'assistant';

        const spinner = div.querySelector('.id-spinner');
        if (spinner) spinner.remove();

        const conteudoDiv = div.querySelector('.conteudo-texto');
        if (conteudoDiv) {
            conteudoDiv.innerHTML = textoAcumulado.replace(/\n/g, '<br>');
        }
    }
};
