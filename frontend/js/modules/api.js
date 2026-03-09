/**
 * api.js - Centraliza todas as chamadas de rede para o backend local.
 * Atualizado para a versão v1 da API modular.
 */

export const Api = {
    // --- CHATS ---
    async buscarChats() {
        const res = await fetch('/api/v1/chats/');
        return await res.json();
    },

    async criarChat(titulo = "Nova Conversa") {
        const res = await fetch('/api/v1/chats/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ titulo })
        });
        return await res.json();
    },

    async atualizarChat(id, dados) {
        const res = await fetch(`/api/v1/chats/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        return await res.json();
    },

    async eliminarChat(id) {
        const res = await fetch(`/api/v1/chats/${id}`, { method: 'DELETE' });
        return await res.json();
    },

    // --- MENSAGENS ---
    async enviarPergunta(chatId, payload) {
        // Rota de geração de resposta agora centralizada no v1
        return await fetch(`/api/v1/chats/${chatId}/gerar_resposta`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
    },

    async eliminarMensagem(id) {
        const res = await fetch(`/api/v1/mensagens/${id}`, { method: 'DELETE' });
        return await res.json();
    },

    // --- MODELOS ---
    async buscarModelos() {
        const res = await fetch('/api/v1/modelos/');
        return await res.json();
    },

    async sincronizarOllama() {
        const res = await fetch('/api/v1/modelos/sincronizar', { method: 'POST' });
        return await res.json();
    },

    async registarModelo(dados) {
        const res = await fetch('/api/v1/modelos/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        return res;
    },

    async descarregarModelos(listaModelos) {
        const res = await fetch('/api/v1/modelos/baixar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ modelos: listaModelos })
        });
        return await res.json();
    },

    // --- CONFIGURAÇÕES E UPLOADS ---
    async buscarConfiguracoes() {
        const res = await fetch('/api/v1/configuracoes/');
        return await res.json();
    },

    async salvarConfiguracoes(dados) {
        const res = await fetch('/api/v1/configuracoes/', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        return await res.json();
    },

    async uploadFicheiro(arquivo, tipo) {
        const formData = new FormData();
        formData.append('file', arquivo);
        const res = await fetch(`/api/v1/upload/${tipo}`, {
            method: 'POST',
            body: formData
        });
        return await res.json();
    }
};
