import logging
import logging_loki
import requests

# 1. Configure the Loki Transport without the session argument first
loki_handler = logging_loki.LokiHandler(
    url="http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push",
    tags={"env": "development", "service": "order-services"},
    version="1",
)

# 2. Inject the header into the underlying emitter's session
# This is where the magic happens for multi-tenancy
loki_handler.emitter.session.headers.update({"X-Scope-OrgID": "tenant1"})

# 3. Create the Logger
logger = logging.getLogger("order-service")
logger.setLevel(logging.INFO)
logger.addHandler(loki_handler)

# Always print to console so you can see it locally
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

# Fallback error handling
def handle_loki_error(error):
    print(f"🚨 Python Loki Transport Error: {error}")
    
loki_handler.emitter.on_error = handle_loki_error