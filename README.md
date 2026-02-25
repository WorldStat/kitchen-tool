# 🍳 KitchenTool - Digital Cookbook & Shopping Planner

KitchenTool is a modern, Django-based web application designed to be your ultimate kitchen companion. It allows you to manage your personal cookbook, import recipes from across the web, and generate collaborative shopping lists. With a focus on community and sharing, you can make your creations public and discover what others are cooking.

## ✨ Key Features

-   **Digital Cookbook**: Create, edit, and categorize your personal recipes with a rich, modern interface.
-   **Magic Recipe Importer**: Paste a URL from over 100+ recipe websites, and KitchenTool will automatically parse and fill in the details for you.
-   **Smart Shopping Lists**: 
    -   Generate lists automatically from one or more recipes.
    -   Create and manage lists manually.
    -   **Collaborate in real-time** by inviting other users to view and edit your lists—perfect for households!
-   **Community & Sharing**:
    -   **Public Recipes**: Make any recipe public to share it with anyone via a unique URL.
    -   **Community Cookbook**: Explore a feed of public recipes shared by other users.
    -   **Clone Recipes**: Instantly copy any public recipe to your own cookbook with a single click.
-   **User Dashboard**: A personalized "My Kitchen" dashboard showing your stats, including total recipes, shared recipes, and shopping lists.
-   **Cloud-Ready**: Seamlessly integrates with AWS S3 for scalable, cloud-based image storage.

## 🛠️ Technology Stack

-   **Backend**: Django, Python
-   **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
-   **Database**: SQLite (for local development), easily configurable for PostgreSQL in production.
-   **Deployment**: Designed for deployment on AWS EC2 with media files served from S3.
-   **Web Scraping**: `recipe-scrapers` library.

## 🏗️ Project Architecture

The project follows a standard Django architecture, with functionality organized into distinct apps:

-   `recipe_project/`: The main Django project directory.
    -   `config/`: Contains the main `settings.py` and root `urls.py`.
    -   `recipes/`: Handles all logic related to recipe creation, viewing, and the web scraper.
    -   `shopping/`: Manages shopping lists, items, and collaborator logic.
    -   `users/`: Implements a `CustomUser` model, authentication views, and the user dashboard.
    -   `templates/`: Contains the base template and other global HTML files. App-specific templates are nested within each app's `templates/` folder.
    -   `static/`: For global static assets like CSS and JavaScript.

## 🚀 Local Installation Guide

Get KitchenTool running on your local machine in a few simple steps.

### 1. Prerequisites
-   Python 3.10+
-   `git`

### 2. Clone & Setup
```bash
# Clone the repository
git clone https://github.com/your-username/kitchen-tool.git
cd kitchen-tool/recipe_project

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Install all required packages
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the `recipe_project/` directory. You can copy the example file to get started:

```bash
cp .env.example .env
```

Now, open the `.env` file and fill in the required values. For local development, you only need to set `SECRET_KEY`.

### 5. Initialize Database
```bash
# Apply database migrations
python3 manage.py migrate

# Create a superuser to access the admin panel
python3 manage.py createsuperuser
```

### 6. Run the Server
```bash
# Start the Django development server
python3 manage.py runserver
```
Your local instance of KitchenTool will be available at `http://127.0.0.1:8000/`.

## ☁️ Deployment Notes (AWS)

The project is configured for deployment on AWS EC2 with S3 for media storage.

-   **`.env` for Production**: To enable S3, set `USE_S3=True` in your `.env` file on the EC2 instance and provide your `AWS_STORAGE_BUCKET_NAME` and `AWS_S3_REGION_NAME`.
-   **IAM Role**: Your EC2 instance **must** have an IAM Role attached with permissions to `PutObject`, `GetObject`, `DeleteObject`, and `ListBucket` for your S3 bucket.
-   **S3 Bucket Policy**: Ensure your bucket policy allows public reads (`s3:GetObject`) for the `recipe_photos/*` directory if you want images to be publicly visible.
-   **CORS Configuration**: Your S3 bucket needs a CORS policy to allow your web domain to request images.

---
*This README was generated with assistance from an AI pair programmer.*
