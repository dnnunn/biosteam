.PHONY: dev api ui cli test

python := python3.11

dev: ## install dev deps
	cd app/api && $(python) -m pip install -e .
	cd app/cli && $(python) -m pip install -e .

api:
	uvicorn app.api.main:app --reload --port 8000

ui:
	cd app/ui && npm i && npm run dev

test:
	cd app/api && pytest -q
