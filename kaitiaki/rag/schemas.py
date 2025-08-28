# kaitiaki/rag/schemas.py
from pydantic import BaseModel, Field


from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel

# Schéma pour une citation individuelle
class Citation(BaseModel):
    document_id: str = Field(..., description="ID unique du document source.")
    content: str = Field(..., description="Contenu textuel du chunk cité.")
    page_number: int = Field(..., description="Numéro de la page d'où provient le chunk.")
    source: str = Field(..., description="Nom du fichier ou URL de la source.")
    
    class Config:
        alias_generator = to_camel
        populate_by_name = True
        
# Schéma pour le détail de la latence
class Latency(BaseModel):
    total_ms: int = Field(..., description="Latence totale du traitement de la requête en millisecondes.")
    retrieval_ms: int = Field(..., description="Temps de récupération des documents en millisecondes.")
    llm_ms: int = Field(..., description="Temps de génération de la réponse par le LLM en millisecondes.")

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# Schéma pour la réponse finale de l'API
class Answer(BaseModel):
    answer: str = Field(..., description="Réponse textuelle générée par le modèle.")
    citations: list[Citation] = Field(default_factory=list, description="Liste des chunks de documents utilisés pour générer la réponse.")
    latency: Latency | None = Field(None, description="Détail de la latence du traitement.")

    class Config:
        alias_generator = to_camel
        populate_by_name = True

# Schéma pour une question posée à l'API
class Query(BaseModel):
    question: str = Field(..., description="Question de l'utilisateur.")

