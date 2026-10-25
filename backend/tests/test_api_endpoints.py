import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "ollama_connected" in data

def test_health_ollama_endpoint():
    response = client.get("/api/health/ollama")
    assert response.status_code == 200
    data = response.json()
    assert "configured_model" in data
    assert "connected" in data

def test_get_sources():
    response = client.get("/api/sources")
    assert response.status_code == 200
    sources = response.json()
    assert isinstance(sources, list)
    assert len(sources) >= 1

def test_create_and_delete_source():
    payload = {
        "name": "Test Lab Blog",
        "url": "https://test-ai-lab.org/feed.xml",
        "category": "official_ai",
        "is_official": True,
        "feed_type": "rss"
    }
    create_resp = client.post("/api/sources", json=payload)
    assert create_resp.status_code == 201
    source_id = create_resp.json()["id"]

    # Delete
    del_resp = client.delete(f"/api/sources/{source_id}")
    assert del_resp.status_code == 204

def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_articles" in data
    assert "total_stories" in data
    assert "corroborated_stories" in data

def test_get_news_pagination():
    response = client.get("/api/news?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "total_pages" in data

def test_get_settings_and_patch():
    get_resp = client.get("/api/settings")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert "ollama" in data
    assert "telegram" in data

    # Patch a setting
    patch_resp = client.patch("/api/settings?key=OLLAMA_MODEL", json={"value": "qwen2.5:3b"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["value"] == "qwen2.5:3b"
