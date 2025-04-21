# In development
In development the docker-compose file to use is "docker-compose.dev.yml"

# Start the Django server
cd /path/to/your/django/project
docker-compose -f docker-compose.local.yml build
docker-compose -f docker-compose.local.yml up

# Create superuser
docker-compose -f docker-compose.local.yml run app sh -c "python manage.py createsuperuser"


