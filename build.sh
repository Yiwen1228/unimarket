#!/usr/bin/env bash
# Render build script — runs on every deploy
set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Seed default categories if empty
python manage.py shell -c "
from market.models import Category
if not Category.objects.exists():
    for name in ['General','Dairy','Bakery','Beverages','Snacks','Fruits','Vegetables','Frozen','Stationery','Other']:
        Category.objects.get_or_create(name=name)
    print('Categories seeded.')
else:
    print('Categories already exist, skipping.')
"

# Create default staff account if none exists
python manage.py shell -c "
from market.models import Staff
if not Staff.objects.exists():
    from django.contrib.auth.hashers import make_password
    Staff.objects.create(username='admin', email='admin@uni.ac.uk', password=make_password('Staff2025!'))
    print('Default staff account created.')
else:
    print('Staff accounts exist, skipping.')
"
