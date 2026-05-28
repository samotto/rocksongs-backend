import pytest

SONG_PAYLOAD = {
    "title": "Stairway to Heaven",
    "artist": "Led Zeppelin",
    "album": "Led Zeppelin IV",
    "year": 1971,
    "genre": "Classic Rock",
    "duration_seconds": 482,
}


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_song(client):
    response = client.post("/songs/", json=SONG_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == SONG_PAYLOAD["title"]
    assert data["artist"] == SONG_PAYLOAD["artist"]
    assert data["album"] == SONG_PAYLOAD["album"]
    assert data["year"] == SONG_PAYLOAD["year"]
    assert data["genre"] == SONG_PAYLOAD["genre"]
    assert data["duration_seconds"] == SONG_PAYLOAD["duration_seconds"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_song_minimal(client):
    response = client.post("/songs/", json={"title": "Bohemian Rhapsody", "artist": "Queen"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Bohemian Rhapsody"
    assert data["artist"] == "Queen"
    assert data["album"] is None
    assert data["year"] is None


def test_create_song_missing_required_fields(client):
    response = client.post("/songs/", json={"title": "Missing Artist"})
    assert response.status_code == 422


def test_list_songs_empty(client):
    response = client.get("/songs/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_songs(client):
    client.post("/songs/", json=SONG_PAYLOAD)
    client.post("/songs/", json={"title": "Bohemian Rhapsody", "artist": "Queen", "genre": "Rock Opera"})
    response = client.get("/songs/")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_songs_filter_by_artist(client):
    client.post("/songs/", json=SONG_PAYLOAD)
    client.post("/songs/", json={"title": "Bohemian Rhapsody", "artist": "Queen"})
    response = client.get("/songs/?artist=Led")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["artist"] == "Led Zeppelin"


def test_list_songs_filter_by_genre(client):
    client.post("/songs/", json=SONG_PAYLOAD)
    client.post("/songs/", json={"title": "Bohemian Rhapsody", "artist": "Queen", "genre": "Rock Opera"})
    response = client.get("/songs/?genre=Classic")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["genre"] == "Classic Rock"


def test_list_songs_pagination(client):
    for i in range(5):
        client.post("/songs/", json={"title": f"Song {i}", "artist": "Artist"})
    response = client.get("/songs/?skip=2&limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_song(client):
    create_resp = client.post("/songs/", json=SONG_PAYLOAD)
    song_id = create_resp.json()["id"]
    response = client.get(f"/songs/{song_id}")
    assert response.status_code == 200
    assert response.json()["id"] == song_id
    assert response.json()["title"] == SONG_PAYLOAD["title"]


def test_get_song_not_found(client):
    response = client.get("/songs/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Song not found"


def test_update_song(client):
    create_resp = client.post("/songs/", json=SONG_PAYLOAD)
    song_id = create_resp.json()["id"]
    response = client.put(f"/songs/{song_id}", json={"title": "Updated Title", "year": 1972})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["year"] == 1972
    assert data["artist"] == SONG_PAYLOAD["artist"]


def test_update_song_not_found(client):
    response = client.put("/songs/9999", json={"title": "New Title"})
    assert response.status_code == 404


def test_delete_song(client):
    create_resp = client.post("/songs/", json=SONG_PAYLOAD)
    song_id = create_resp.json()["id"]
    response = client.delete(f"/songs/{song_id}")
    assert response.status_code == 204
    get_resp = client.get(f"/songs/{song_id}")
    assert get_resp.status_code == 404


def test_delete_song_not_found(client):
    response = client.delete("/songs/9999")
    assert response.status_code == 404
