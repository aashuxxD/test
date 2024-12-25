docker container rm alexa-aio -f > /dev/null
sleep 2
echo "Starting and Deploying Bot as alexa-aio"
docker run -d --restart=unless-stopped --name alexa-aio alexa-aio
