#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER ${APP_DB_USER:-weather_user} WITH PASSWORD '${APP_DB_PASSWORD:-weather_pass}';
    CREATE DATABASE ${APP_DB_NAME:-weather_db};
    GRANT ALL PRIVILEGES ON DATABASE ${APP_DB_NAME:-weather_db} TO ${APP_DB_USER:-weather_user};
    
    ALTER USER ${APP_DB_USER:-weather_user} WITH SUPERUSER;
EOSQL