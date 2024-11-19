FROM ankane/pgvector

COPY ../init_db.sh /docker-entrypoint-initdb.d/init_db.sh

RUN chmod +x /docker-entrypoint-initdb.d/init_db.sh

COPY db_docker/entrypoint.sh /docker-entrypoint-initdb.d/entrypoint.sh
RUN chmod +x /docker-entrypoint-initdb.d/entrypoint.sh