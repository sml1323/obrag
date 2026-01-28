import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager

# Import actual modules to test wiring
from api.main import app, lifespan
from api.deps import get_app_state, get_chroma_store, get_rag_chain, get_syncer
from config.models import OpenAILLMConfig, OpenAIEmbeddingConfig

@pytest.fixture
def mock_deps():
    """
    Mock external dependencies to verify wiring without actual initialization.
    """
    with patch("api.deps.EmbedderFactory") as mock_embed, \
         patch("api.deps.ChromaStore") as mock_store, \
         patch("api.deps.LLMFactory") as mock_llm, \
         patch("api.deps.Retriever") as mock_retriever, \
         patch("api.deps.RAGChain") as mock_rag, \
         patch("api.deps.create_syncer") as mock_syncer, \
         patch("os.getenv") as mock_getenv:
        
        # Setup specific mocks
        mock_embedding_instance = MagicMock()
        mock_embed.create.return_value = mock_embedding_instance
        
        mock_store_instance = MagicMock()
        mock_store.return_value = mock_store_instance
        
        mock_llm_instance = MagicMock()
        mock_llm.create.return_value = mock_llm_instance
        
        mock_retriever_instance = MagicMock()
        mock_retriever.return_value = mock_retriever_instance
        
        mock_rag_instance = MagicMock()
        mock_rag.return_value = mock_rag_instance
        
        mock_syncer_instance = MagicMock()
        mock_syncer.return_value = mock_syncer_instance
        
        # Default env vars
        def getenv_side_effect(key, default=None):
            if key == "EMBEDDING_MODEL": return "text-embedding-3-small"
            if key == "LLM_MODEL": return "gpt-4o-mini"
            if key == "OBSIDIAN_PATH": return "/tmp/test/notes"
            return default
        mock_getenv.side_effect = getenv_side_effect

        yield {
            "embed": mock_embed,
            "store": mock_store,
            "llm": mock_llm,
            "retriever": mock_retriever,
            "rag": mock_rag,
            "syncer": mock_syncer,
            "instances": {
                "store": mock_store_instance,
                "rag": mock_rag_instance,
                "syncer": mock_syncer_instance
            }
        }

def test_lifespan_initializes_app_state(mock_deps):
    """
    Verify that lifespan initializes AppState with correct factories and configurations.
    """
    # Use Client with app to trigger lifespan
    with TestClient(app) as client:
        # Check if deps are initialized in app.state
        assert hasattr(app.state, "deps")
        deps = app.state.deps
        
        # Verify EmbedderFactory call
        mock_deps["embed"].create.assert_called_once()
        config_call = mock_deps["embed"].create.call_args[0][0]
        assert isinstance(config_call, OpenAIEmbeddingConfig)
        assert config_call.model_name == "text-embedding-3-small"
        
        # Verify ChromaStore call
        mock_deps["store"].assert_called_once_with(
            persist_path="./chroma_db",
            collection_name="obsidian_notes",
            embedder=mock_deps["embed"].create.return_value
        )
        
        # Verify LLMFactory call
        mock_deps["llm"].create.assert_called_once()
        config_call = mock_deps["llm"].create.call_args[0][0]
        assert isinstance(config_call, OpenAILLMConfig)
        assert config_call.model_name == "gpt-4o-mini"
        
        # Verify Retriever & RAGChain wiring
        mock_deps["retriever"].assert_called_once_with(mock_deps["instances"]["store"])
        mock_deps["rag"].assert_called_once_with(
            retriever=mock_deps["retriever"].return_value, 
            llm=mock_deps["llm"].create.return_value
        )
        
        # Verify Syncer wiring
        mock_deps["syncer"].assert_called_once_with(
            root_path="/tmp/test/notes",
            chroma_store=mock_deps["instances"]["store"]
        )

        # Check AppState Integrity
        assert deps.chroma_store == mock_deps["instances"]["store"]
        assert deps.rag_chain == mock_deps["instances"]["rag"]
        assert deps.syncer == mock_deps["instances"]["syncer"]

    # Ensure cleanup happened (though our lifespan is simple yield)
    assert app.state.deps is None

def test_app_dependency_injection_chain(mock_deps):
    """
    Verify that FastAPI dependency functions (get_*) return the initialized objects from AppState.
    """
    # We can invoke dependencies directly if we simulate a request with state
    
    # 1. Start App
    with TestClient(app) as client:
        # 2. Mock Request object
        mock_request = MagicMock()
        mock_request.app.state.deps = app.state.deps
        
        # 3. Test Dependencies
        deps = get_app_state(mock_request)
        assert deps == app.state.deps
        
        store = get_chroma_store(mock_request)
        assert store == mock_deps["instances"]["store"]
        
        rag = get_rag_chain(mock_request)
        assert rag == mock_deps["instances"]["rag"]
        
        syncer = get_syncer(mock_request)
        assert syncer == mock_deps["instances"]["syncer"]
