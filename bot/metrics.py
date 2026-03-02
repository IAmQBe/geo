from prometheus_client import Counter, Histogram

BOT_REQUESTS_TOTAL = Counter("bot_requests_total", "Total bot updates processed", ["update_type"])
BOT_ERRORS_TOTAL = Counter("bot_errors_total", "Total bot errors")
BOT_HANDLER_DURATION = Histogram("bot_handler_duration_seconds", "Bot handler execution duration")
PARSER_PLACES_PROCESSED_TOTAL = Counter("parser_places_processed_total", "Total parsed places")
