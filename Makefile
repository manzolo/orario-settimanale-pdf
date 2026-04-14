.DEFAULT_GOAL := generate

IMAGE_NAME  := pdf-generator
CONTAINER   := pdf-generator
OUTPUT_PDF  := orario.pdf

.PHONY: help build run generate clean rebuild

help: ## Mostra questo messaggio di aiuto
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso: make \033[36m<target>\033[0m\n\nTarget disponibili:\n\n"} \
	      /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""

build: ## Costruisce l'immagine Docker
	docker compose build

run: ## Avvia il container e genera il PDF (richiede build)
	docker compose up --remove-orphans
	@echo ""
	@if [ -f $(OUTPUT_PDF) ]; then \
	    echo "  PDF generato: $(OUTPUT_PDF) ($$(du -h $(OUTPUT_PDF) | cut -f1))"; \
	else \
	    echo "  ATTENZIONE: $(OUTPUT_PDF) non trovato"; \
	fi

generate: build run ## Esegue build + generazione PDF in un solo comando

rebuild: clean build run ## Rimuove tutto, ricostruisce e rigenera il PDF

clean: ## Rimuove il PDF generato e l'immagine Docker
	@rm -f $(OUTPUT_PDF) && echo "  Rimosso $(OUTPUT_PDF)" || true
	@docker rmi $(IMAGE_NAME) 2>/dev/null && echo "  Rimossa immagine $(IMAGE_NAME)" || echo "  Immagine $(IMAGE_NAME) non presente"
