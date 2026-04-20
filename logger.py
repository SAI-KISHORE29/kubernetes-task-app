import logging
import logging_loki
import requests

# 1. Set up a custom session to pass the multi-tenancy header Loki expects
session = requests.Session()
session.headers.update({"X-Scope-OrgID": "tenant1"})

# 2. Configure the Loki Transport
loki_handler = logging_loki.LokiHandler(
    url="http://loki-gateway.loki.svc.cluster.local/loki/api/v1/push",
    tags={"env": "development", "service": "order-services"},
    version="1",
    session=session
)

# 3. Create the Logger
logger = logging.getLogger("order-service")
logger.setLevel(logging.INFO)
logger.addHandler(loki_handler)

# Optional: Also print to console so you can see it locally
console_handler = logging.StreamHandler()
logger.addHandler(console_handler)

# Fallback error handling if Loki is unreachable
def handle_loki_error(error):
    print(f"🚨 Python Loki Transport Error: {error}")
    
loki_handler.emitter.on_error = handle_loki_error