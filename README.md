# Job Storage
Rest API and database for job offer storage and applicants' data.

## How to run
```
cd docker/
docker-compose build
docker-compose run
```

- Once running you can:
  - Run Rest API documentation at localhost:2000
    
  - View logs at:
    ```
    tail -f log/syslog
    ```
    
  - Browse database via:
    ```
    docker exec -it postgres-jobs psql -U postgres
    ```