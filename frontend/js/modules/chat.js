/**
 * chat.js - Lida exclusivamente com a lógica de envio de mensagens e streaming (SSE).
 */
import { UI } from './ui.js';

export const Chat = {
    async enviar(chatId, texto, imagemBase64, opcoes = { modelo: 'llama3', isStream: true, indicadorId: null, callbackZoom: null }) {
        
        // 1. Prepara o payload base
        const payload = {
            prompt: texto,
            modelo: opcoes.modelo,
            stream: opcoes.isStream
        };

        // 2. Lógica de Roteamento Inteligente
        let endpoint = `/api/v1/chats/${chatId}/send_message/text`;

        if (imagemBase64) {
            payload.imagem_base64 = imagemBase64;
            endpoint = `/api/v1/chats/${chatId}/send_message/image/interpret`;
            console.log("📷 Imagem detetada! Roteando para interpretação de visão.");
        } else {
            console.log("📝 Roteando para endpoint de texto padrão.");
        }

        try {
            // 3. Faz a requisição para o endpoint selecionado
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const erro = await response.text();
                throw new Error(`Erro do servidor: ${erro}`);
            }

            const divIA = document.getElementById(`msg-container-${opcoes.indicadorId}`);
            if (!divIA) return;

            // Encontra a div interna onde o texto realmente fica
            const conteudoIA = divIA.querySelector('.text-sm');
            if (!conteudoIA) return;

            conteudoIA.innerHTML = ''; // Limpa o "..." inicial

            if (opcoes.isStream) {
                // LÓGICA DE STREAMING (Efeito máquina de escrever)
                const reader = response.body.getReader();
                const decoder = new TextDecoder("utf-8");

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    const linhas = chunk.split('\n');

                    for (const linha of linhas) {
                        if (linha.startsWith('data: ')) {
                            try {
                                const dados = JSON.parse(linha.substring(6));
                                
                                if (dados.fim) {
                                    // A IA terminou de responder. Atualizamos o ID temporário para o ID real do banco.
                                    divIA.id = `msg-container-${dados.id}`;
                                    
                                    // Atualizamos também os botões de ação (Apagar/Regerar) com o ID real
                                    const btnApagar = divIA.querySelector('button[title="Apagar"]');
                                    const btnRegerar = divIA.querySelector('button[title="Regerar resposta"]');
                                    
                                    if (btnApagar) btnApagar.setAttribute('onclick', `window.apagarMensagem('${dados.id}')`);
                                    if (btnRegerar) btnRegerar.setAttribute('onclick', `window.regerarMensagem('${dados.id}')`);
                                    break;
                                }

                                if (dados.chunk) {
                                    // Anexa o novo texto gerado
                                    conteudoIA.innerHTML += dados.chunk;
                                    UI.rolarParaBaixo();
                                }
                            } catch (e) {
                                console.warn("Erro ao fazer parse do chunk SSE:", e, linha);
                            }
                        }
                    }
                }
            } else {
                // LÓGICA SEM STREAM (Aguarda a resposta completa)
                // (Atualmente o backend força stream, mas mantemos por segurança)
                const data = await response.json();
                if (data.conteudo) {
                    conteudoIA.innerHTML = data.conteudo;
                }
            }

        } catch (error) {
            console.error("Falha ao enviar mensagem:", error);
            const divIA = document.getElementById(`msg-container-${opcoes.indicadorId}`);
            if (divIA) {
                const conteudoIA = divIA.querySelector('.text-sm');
                if (conteudoIA) {
                    conteudoIA.innerHTML = `<span class="text-red-400"><i class="fa-solid fa-triangle-exclamation"></i> Falha na comunicação com a IA. Tente novamente.</span>`;
                }
            }
        }
    }
};
