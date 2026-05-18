.PHONY: help validate up ps register-connector create-topics health processor dashboard demo quality down

help:
	@printf "Real-Time Order & Inventory CDC Platform helpers\n"
	@printf "\n"
	@printf "  make validate            Static checks; safe before every commit\n"
	@printf "  make up                  Start local compose services\n"
	@printf "  make ps                  Show compose service status\n"
	@printf "  make register-connector  Register/update Debezium connector\n"
	@printf "  make create-topics       Ensure expected Redpanda topics exist\n"
	@printf "  make health              Check live demo service health\n"
	@printf "  make processor           Start Python CDC processor\n"
	@printf "  make dashboard           Start Streamlit dashboard\n"
	@printf "  make demo                Run flash-sale demo sequence\n"
	@printf "  make quality             Run data quality checks\n"
	@printf "  make down                Stop compose services\n"

validate:
	./scripts/validate_project.sh

up:
	podman compose -f compose.yml up -d

ps:
	podman compose -f compose.yml ps

register-connector:
	./scripts/register_connector.sh

create-topics:
	./scripts/create_topics.sh

health:
	./scripts/check_demo_health.sh

processor:
	cd stream_processor && uv run python -m src.main

dashboard:
	cd dashboard && uv run streamlit run app.py

demo:
	./scripts/run_demo_sequence.sh

quality:
	cd stream_processor && uv run python -m src.quality.run_checks

down:
	podman compose -f compose.yml down
