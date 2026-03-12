import sqlite3
import os
from core.logger import loggers

class FlashMemory:
    """
    Gerenciador de histórico cronológico baseado em SQLite.
    Focado em fornecer o contexto imediato (últimas mensagens) para os modelos.
    """

    # Configura o caminho do banco de dados utilizando o UUID da persona 
    # e dispara a criação das tabelas fundamentais.
    def __init__(self, persona_id: str):
        self.persona_id = persona_id
        self.db_path = f"data/sqlite/{self.persona_id}.db"
        self.log = loggers["chat"]["db"]
        
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_sqlite()

    # Cria a estrutura de tabelas necessária para armazenar mensagens, 
    # garantindo que o banco esteja pronto para operações de escrita.
    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT, 
                    content TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'processed' 
                )
            ''')
            conn.commit()

    # Insere uma nova mensagem no banco de dados e retorna o ID gerado, 
    # registrando quem enviou (usuário ou IA) e o conteúdo textual.
    def save(self, role: str, content: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (role, content) VALUES (?, ?)", 
                (role, content)
            )
            msg_id = cursor.lastrowid
            conn.commit()
            
        self.log.info(f"ID:{self.persona_id} | Flash: Mensagem {msg_id} salva.")
        return msg_id

    # Recupera as mensagens mais recentes do histórico, invertendo a ordem 
    # para que fiquem em sequência cronológica correta para o prompt.
    def get_context(self, limit: int = 10):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content FROM messages ORDER BY timestamp DESC LIMIT ?", 
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in reversed(rows)]

    # Localiza uma mensagem específica pelo ID e atualiza seu conteúdo, 
    # útil para correções manuais ou edições via interface.
    def update(self, msg_id: int, new_content: str):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE messages SET content = ? WHERE id = ?", 
                (new_content, msg_id)
            )
            conn.commit()
            
        self.log.info(f"ID:{self.persona_id} | Flash: Mensagem {msg_id} editada.")

    # Remove permanentemente todos os registros de mensagens vinculados 
    # a esta persona, reiniciando o histórico de conversas.
    def clear_history(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            conn.commit()
            
        self.log.info(f"ID:{self.persona_id} | Flash: Histórico limpo.")
