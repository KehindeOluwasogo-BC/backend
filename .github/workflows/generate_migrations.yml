name: Generate Migrations

on:
  push:
    paths:
      - '*/models.py'
      - 'backend/settings.py'
    branches: [ main, develop ]
  workflow_dispatch:

jobs:
  migrations:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Generate migrations
        run: |
          python manage.py makemigrations
      
      - name: Setup git credentials
        run: |
          git config --global credential.helper store
          echo "https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com" > ~/.git-credentials
      
      - name: Commit and push migrations
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add .
          git diff --cached --quiet || (git commit -m "Auto-generate migrations" && git push)
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
