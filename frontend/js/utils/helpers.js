/** * helpers.js - Funções de utilidade geral e carregamento de componentes.
 */

export const Helpers = {
    /**
     * Carrega um componente HTML e injeta num container.
     * @param {string} containerId - ID do elemento que receberá o conteúdo.
     * @param {string} fileName - Nome do ficheiro na pasta components.
     */
    async incluirComponente(containerId, fileName) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Elemento com ID "${containerId}" não encontrado.`);
            return false;
        }

        try {
            // O backend serve a pasta 'frontend' na raiz (/), 
            // logo os componentes estão em /components/
            const response = await fetch(`/components/${fileName}`);
            
            if (!response.ok) {
                throw new Error(`Erro ao carregar o componente: ${response.statusText}`);
            }

            const html = await response.text();
            container.innerHTML = html;
            
            return true;
        } catch (error) {
            console.error(`Falha ao incluir componente [${fileName}]:`, error);
            return false;
        }
    },

    /**
     * Gera um ID temporário baseado no timestamp.
     */
    gerarId() {
        return 'temp-' + Date.now();
    },

    /**
     * Configura o comportamento de expansão automática de um textarea.
     */
    configurarAutoResizing(textarea) {
        if (!textarea) return;
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
};
