MODEL ?= tinyllama
d:
	docker compose down

b:
	docker compose up --build

re:
	docker compose down
	docker compose up --build

po:
	docker compose up -d ollama
	@echo "Waiting for Ollama to start..."
	@sleep 5
	docker exec ollama ollama pull $(MODEL)

vo:
	docker exec ollama ollama list
	curl http://localhost:11434/api/tags

ro:
	docker exec -it ollama ollama run $(MODEL)

remove-model:
	docker compose stop ollama || true
	docker exec ollama bash -lc 'rm -rf /root/.ollama/models/$(MODEL)'
	docker compose start ollama || true

ra:
	docker compose up -d ollama
	docker compose up -d app
	curl http://localhost:11434/api/tags