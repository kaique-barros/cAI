import logging
import os

# Define a estrutura de diretórios e configura os parâmetros de formatação 
# para os arquivos de log, criando as pastas necessárias caso não existam.
def setup_logger(name, sector=None, log_type="access"):
    log_dir = "logs"
    logger = logging.getLogger(f"{name}_{sector}_{log_type}")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    gen_file = os.path.join(log_dir, f"{log_type}.log")
    gen_handler = logging.FileHandler(gen_file)
    gen_handler.setFormatter(formatter)
    logger.addHandler(gen_handler)

    if sector:
        sec_dir = os.path.join(log_dir, sector)
        if not os.path.exists(sec_dir):
            os.makedirs(sec_dir)
            
        sec_file = os.path.join(sec_dir, f"{log_type}.log")
        sec_handler = logging.FileHandler(sec_file)
        sec_handler.setFormatter(formatter)
        logger.addHandler(sec_handler)

    return logger

# Inicializa o dicionário global de loggers, mapeando os principais setores 
# da aplicação (Persona, Chat e Sistema) para seus respectivos manipuladores.
loggers = {
    "persona": {
        "access": setup_logger("per_acc", "persona", "access"), 
        "db": setup_logger("per_db", "persona", "database")
    },
    "chat": {
        "access": setup_logger("cha_acc", "chat", "access"), 
        "db": setup_logger("cha_db", "chat", "database")
    },
    "system": {
        "access": setup_logger("sys_acc", "system", "access"), 
        "db": setup_logger("sys_db", "system", "database")
    }
}
