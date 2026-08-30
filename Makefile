.PHONY: export serve

export:
	uv run python -m src.main

serve:
	python -m http.server 8080 --directory src/frontend
