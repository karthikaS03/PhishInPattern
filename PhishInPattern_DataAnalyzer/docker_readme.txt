sudo docker run -d --network phishpro-network --network-alias container_phishpro_db -v "$(pwd)/sql_script:/docker-entrypoint-initdb.d" -r MYSQL_USER=phishpro_admin -e MYSQL_ROOT_PASSWORD=admin_phishpro -e MYSQL_DATABASE=phishpro_db mysql:latest

