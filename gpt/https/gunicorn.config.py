bind = "0.0.0.0:8081"

workers = 4
worker_class = "uvicorn.workers.UvicornWorker"

accesslog = "-"
errorlog = "-"

loglevel = "info"
timeout = 30
keepalive = 5

graceful_timeout = 30
