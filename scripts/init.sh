#!/bin/bash
echo "Waiting mongo db initialization..."
sleep 20
echo "Stating process config mongodb servers"
docker-compose exec -T configsvr01 sh -c "mongo < /scripts/init-configserver.js"
echo "Stating process config mongodb Sharding"
docker-compose exec -T shard01-a sh -c "mongo < /scripts/init-shard01.js"
docker-compose exec -T shard02-a sh -c "mongo < /scripts/init-shard02.js"
docker-compose exec -T shard03-a sh -c "mongo < /scripts/init-shard03.js"
sleep 60
echo "Stating process config mongodb routers"
docker-compose exec -T router01 sh -c "mongo < /scripts/init-router.js"
echo "Stating process enable mongo db and collections"
docker-compose exec -T router01 sh -c "mongo < /scripts/enable.js"


docker exec -it shard-01-node-a bash -c "echo 'rs.status()' | mongo --port 27017"
docker exec -it shard-02-node-a bash -c "echo 'rs.status()' | mongo --port 27017"
docker exec -it shard-03-node-a bash -c "echo 'rs.status()' | mongo --port 27017"
