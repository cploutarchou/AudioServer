#!/bin/bash
echo "Waiting mongo db initialization..."
sleep 20
echo "Stating process config mongodb servers"
docker-compose exec configsvr01 sh -c -i "mongo < /scripts/init-configserver.js"
echo "Stating process config mongodb Sharding"
docker-compose exec shard01-a sh -c -i "mongo < /scripts/init-shard01.js"
docker-compose exec shard02-a sh -c -i "mongo < /scripts/init-shard02.js"
docker-compose exec shard03-a sh -c -i "mongo < /scripts/init-shard03.js"
sleep 20
echo "Stating process config mongodb routers"
docker-compose exec router01 sh -c -i "mongo < /scripts/init-router.js"
echo "Stating process enable mongo db and collections"
docker-compose exec router01 sh -c -i "mongo < /scripts/enable.js"
