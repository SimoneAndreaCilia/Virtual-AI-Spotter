from typing import List, Tuple, Callable, Any, Dict

class FeedbackSystem:
    """
    Sistema centralizzato per la gestione dei feedback correttivi.
    Permette di registrare regole e ottenere il messaggio a più alta priorità.
    """
    def __init__(self):
        # Lista di tuple: (priority, condition_func, message_key)
        # Priority più alta vince (es. 10 > 1)
        self.rules: List[Tuple[int, Callable[[Dict[str, Any]], bool], str]] = []

    def add_rule(self, 
                 condition: Callable[[Dict[str, Any]], bool], 
                 message_key: str, 
                 priority: int = 1):
        """
        Aggiunge una regola di feedback.
        
        Args:
            condition: Funzione che accetta un 'context' (dict) e ritorna True se c'è un errore.
            message_key: Chiave del messaggio da mostrare se la condizione è vera.
            priority: Importanza dell'errore (10=critico, 1=info).
        """
        self.rules.append((priority, condition, message_key))
        # Ordina per priorità decrescente
        self.rules.sort(key=lambda x: x[0], reverse=True)

    def check(self, context: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Verifica tutte le regole contro il contesto fornito.
        
        Returns:
            Tuple[str, bool]: (message_key, is_valid_form)
            is_valid_form è False se almeno una regola con priorità > 0 scatta.
        """
        for priority, condition, msg_key in self.rules:
            if condition(context):
                # Se la condizione è vera (c'è un problema/stato da segnalare)
                # Ritorniamo subito il messaggio a più alta priorità
                # Se priority > 0 consideriamo la form non valida (o warning)
                is_valid = False # Assumiamo che se c'è un feedback, c'è qualcosa da dire
                
                # Eccezione: Messaggi "Positivi" (es. Perfect Form) potrebbero avere priorità bassa
                # Ma qui assumiamo che add_rule sia usato per ERRORI o WARNINGS.
                # Per messaggi di stato "Good", usiamo un default se loop finisce.
                
                return msg_key, False
        
        # Nessuna regola scattata -> Feedback positivo di default
        return "feedback_perfect", True
        
    def reset(self):
        pass # Stateless per ora
