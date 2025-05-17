docker-compose -f docker-compose.local.yml build
docker-compose -f docker-compose.local.yml run app sh -c "python manage.py createsuperuser"
docker-compose -f docker-compose.local.yml up